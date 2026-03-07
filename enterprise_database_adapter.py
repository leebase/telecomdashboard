"""
Enterprise Database Adapter for Telecom Dashboard
Phase 3: Data Migration & Integration

This module provides a flexible database adapter that supports multiple enterprise databases
while maintaining compatibility with the existing SQLite-based development setup.
"""

import os
import pandas as pd
import sqlite3
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, Union, Tuple, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from functools import lru_cache
from urllib.parse import urlparse
from __version__ import APP_VERSION
from queue import Queue, Empty

from config_manager import get_config, DatabaseConfig
from logging_config import get_logger

logger = get_logger('enterprise_db')

class ConnectionPool:
    """
    Thread-safe connection pool for database connections.
    
    Manages a pool of database connections to prevent connection exhaustion
    and improve performance by reusing connections.
    """
    
    def __init__(self, create_connection_func, min_connections: int = 2, max_connections: int = 10):
        """
        Initialize connection pool.
        
        Args:
            create_connection_func: Function that creates a new database connection
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections allowed
        """
        self.create_connection = create_connection_func
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        self._pool = Queue(maxsize=max_connections)
        self._active_connections = 0
        # Pool expansion can happen from code paths that already hold the lock.
        self._lock = threading.RLock()
        
        # Pre-populate with minimum connections
        for _ in range(min_connections):
            try:
                conn = self.create_connection()
                self._pool.put(conn)
                self._active_connections += 1
            except Exception as e:
                logger.warning(f"Failed to create initial connection: {e}")
    
    def get_connection(self, timeout: float = 30.0):
        """
        Get a connection from the pool.
        
        Args:
            timeout: Maximum time to wait for a connection
            
        Returns:
            Database connection
            
        Raises:
            Exception: If no connection is available within timeout
        """
        try:
            # Try to get existing connection from pool
            conn = self._pool.get(timeout=timeout)
            
            # Test connection validity (simple ping)
            if self._is_connection_valid(conn):
                return conn
            else:
                logger.debug("Connection invalid, creating new one")
                self._active_connections -= 1
                # Create new connection if old one is invalid
                return self._create_new_connection()
                
        except Empty:
            # No connection available in pool, try to create new one
            with self._lock:
                if self._active_connections < self.max_connections:
                    return self._create_new_connection()
                else:
                    raise Exception(f"Connection pool exhausted (max: {self.max_connections})")
    
    def return_connection(self, conn):
        """
        Return a connection to the pool.
        
        Args:
            conn: Database connection to return
        """
        if self._is_connection_valid(conn):
            try:
                self._pool.put_nowait(conn)
            except:
                # Pool is full, close the connection
                self._close_connection(conn)
                with self._lock:
                    self._active_connections -= 1
        else:
            # Invalid connection, close it
            self._close_connection(conn)
            with self._lock:
                self._active_connections -= 1
    
    def _create_new_connection(self):
        """Create a new database connection."""
        try:
            conn = self.create_connection()
            with self._lock:
                self._active_connections += 1
            return conn
        except Exception as e:
            logger.error(f"Failed to create new connection: {e}")
            raise
    
    def _is_connection_valid(self, conn) -> bool:
        """
        Test if a connection is still valid.
        
        Args:
            conn: Database connection to test
            
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Simple test query - works for most databases
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except:
            return False
    
    def _close_connection(self, conn):
        """Close a database connection safely."""
        try:
            conn.close()
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                self._close_connection(conn)
            except Empty:
                break
        
        with self._lock:
            self._active_connections = 0

@dataclass
class DatabaseCredentials:
    """Database connection credentials"""
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: str = ""
    password: str = ""
    schema: Optional[str] = None
    warehouse: Optional[str] = None  # For Snowflake
    account: Optional[str] = None    # For Snowflake

class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""
    
    @abstractmethod
    def get_connection(self):
        """Get database connection"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Test database connection"""
        pass
    
    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """Get database metadata and version info"""
        pass

class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter (current implementation)"""
    
    def __init__(self, db_path: str = "data/telecom_db.sqlite"):
        self.db_path = db_path
    
    def get_connection(self):
        """Get SQLite connection"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        return conn
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        with self.get_connection() as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            else:
                return pd.read_sql_query(query, conn)
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test SQLite connection"""
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")
                return True, "SQLite connection successful"
        except Exception as e:
            return False, f"SQLite connection failed: {str(e)}"
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get SQLite database info"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            return {
                "type": "SQLite",
                "version": version,
                "database": self.db_path,
                "tables": tables,
                "schema": "main"
            }

class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter for medium enterprise deployment"""
    
    def __init__(self, credentials: DatabaseCredentials, use_pooling: bool = True):
        self.credentials = credentials
        self._connection_string = self._build_connection_string()
        self.use_pooling = use_pooling
        
        if use_pooling:
            self._pool = ConnectionPool(
                create_connection_func=self._create_raw_connection,
                min_connections=2,
                max_connections=10
            )
    
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        return (f"postgresql://{self.credentials.username}:{self.credentials.password}@"
                f"{self.credentials.host}:{self.credentials.port or 5432}/"
                f"{self.credentials.database}")
    
    def _create_raw_connection(self):
        """Create a raw PostgreSQL connection"""
        try:
            import psycopg2
            return psycopg2.connect(
                host=self.credentials.host,
                port=self.credentials.port or 5432,
                database=self.credentials.database,
                user=self.credentials.username,
                password=self.credentials.password
            )
        except ImportError:
            raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")
    
    def get_connection(self):
        """Get PostgreSQL connection (pooled or direct)"""
        if self.use_pooling:
            return self._pool.get_connection()
        else:
            return self._create_raw_connection()
    
    def return_connection(self, conn):
        """Return connection to pool if pooling is enabled"""
        if self.use_pooling:
            self._pool.return_connection(conn)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute PostgreSQL query and return DataFrame"""
        if self.use_pooling:
            conn = self.get_connection()
            try:
                result = pd.read_sql_query(query, conn, params=params)
                return result
            finally:
                self.return_connection(conn)
        else:
            # Fall back to SQLAlchemy engine for non-pooled connections
            try:
                import sqlalchemy
                engine = sqlalchemy.create_engine(self._connection_string)
                return pd.read_sql_query(query, engine, params=params)
            except ImportError:
                raise ImportError("sqlalchemy not installed. Run: pip install sqlalchemy")
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test PostgreSQL connection"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    return True, f"PostgreSQL connection successful: {version}"
        except Exception as e:
            return False, f"PostgreSQL connection failed: {str(e)}"
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get PostgreSQL database info"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = %s
                """, (self.credentials.schema or 'public',))
                tables = [row[0] for row in cursor.fetchall()]
                
                return {
                    "type": "PostgreSQL",
                    "version": version,
                    "host": self.credentials.host,
                    "port": self.credentials.port,
                    "database": self.credentials.database,
                    "schema": self.credentials.schema or 'public',
                    "tables": tables
                }

class SnowflakeAdapter(DatabaseAdapter):
    """Snowflake database adapter for large enterprise deployment"""
    
    def __init__(self, credentials: DatabaseCredentials, use_pooling: bool = True):
        self.credentials = credentials
        self.use_pooling = use_pooling
        
        if use_pooling:
            self._pool = ConnectionPool(
                create_connection_func=self._create_raw_connection,
                min_connections=2,
                max_connections=10
            )
    
    def _create_raw_connection(self):
        """Create a raw Snowflake connection"""
        try:
            import snowflake.connector
            return snowflake.connector.connect(
                user=self.credentials.username,
                password=self.credentials.password,
                account=self.credentials.account,
                warehouse=self.credentials.warehouse,
                database=self.credentials.database,
                schema=self.credentials.schema or 'PUBLIC'
            )
        except ImportError:
            raise ImportError("snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
    
    def get_connection(self):
        """Get Snowflake connection (pooled or direct)"""
        if self.use_pooling:
            return self._pool.get_connection()
        else:
            return self._create_raw_connection()
    
    def return_connection(self, conn):
        """Return connection to pool if pooling is enabled"""
        if self.use_pooling:
            self._pool.return_connection(conn)
    
    def execute_query(self, query: str, params: Optional[tuple] = None, user_context: Optional[str] = None) -> pd.DataFrame:
        """
        Execute Snowflake query with audit tagging and return DataFrame
        
        Args:
            query: SQL query to execute
            params: Query parameters
            user_context: Optional user context for audit trails
            
        Returns:
            DataFrame with query results
        """
        try:
            import snowflake.connector.pandas_tools as pd_tools
            conn = self.get_connection()
            try:
                # Set query tag for SOC 2 compliance and audit trails
                query_tag = self._generate_query_tag(user_context)
                cursor = conn.cursor()
                
                # Apply query tag for audit tracking
                cursor.execute(f"ALTER SESSION SET QUERY_TAG = '{query_tag}'")
                logger.info(f"Snowflake query tagged: {query_tag}")
                
                # Execute through the Snowflake cursor API directly so the
                # connector remains the source of truth for DataFrame fetches.
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                result = cursor.fetch_pandas_all()
                
                # Log query execution for audit
                logger.info(f"Snowflake query executed successfully, returned {len(result)} rows")
                
                return result
            finally:
                if self.use_pooling:
                    self.return_connection(conn)
                else:
                    conn.close()
        except ImportError:
            raise ImportError("snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
    
    def _generate_query_tag(self, user_context: Optional[str] = None) -> str:
        """
        Generate comprehensive query tag for audit compliance
        
        Args:
            user_context: Optional user context information
            
        Returns:
            Formatted query tag string
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Build comprehensive tag with compliance information
        tag_components = [
            "telecom_dashboard",
            timestamp,
            f"app_v{APP_VERSION}",  # Version for tracking
            "prod_env" if os.getenv('ENVIRONMENT') == 'production' else "dev_env"
        ]
        
        # Add user context if provided
        if user_context:
            # Sanitize user context for tag
            safe_context = user_context.replace("'", "").replace('"', "").replace(";", "")[:50]
            tag_components.append(f"user_{safe_context}")
        
        # Add compliance markers
        tag_components.extend([
            "soc2_audit",
            "gdpr_compliant"
        ])
        
        return "_".join(tag_components)
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test Snowflake connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT current_version()")
                version = cursor.fetchone()[0]
                return True, f"Snowflake connection successful: {version}"
        except Exception as e:
            return False, f"Snowflake connection failed: {str(e)}"
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get Snowflake database info"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT current_version()")
            version = cursor.fetchone()[0]
            
            cursor.execute(f"""
                SHOW TABLES IN SCHEMA {self.credentials.database}.{self.credentials.schema or 'PUBLIC'}
            """)
            tables = [row[1] for row in cursor.fetchall()]  # Table name is in second column
            
            return {
                "type": "Snowflake",
                "version": version,
                "account": self.credentials.account,
                "warehouse": self.credentials.warehouse,
                "database": self.credentials.database,
                "schema": self.credentials.schema or 'PUBLIC',
                "tables": tables
            }

class AzureSQLAdapter(DatabaseAdapter):
    """Azure SQL database adapter for Microsoft enterprise deployment"""
    
    def __init__(self, credentials: DatabaseCredentials):
        self.credentials = credentials
        self._connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Build Azure SQL connection string"""
        return (f"mssql+pyodbc://{self.credentials.username}:{self.credentials.password}@"
                f"{self.credentials.host}:{self.credentials.port or 1433}/"
                f"{self.credentials.database}?driver=ODBC+Driver+17+for+SQL+Server")
    
    def get_connection(self):
        """Get Azure SQL connection"""
        try:
            import pyodbc
            return pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.credentials.host},{self.credentials.port or 1433};"
                f"DATABASE={self.credentials.database};"
                f"UID={self.credentials.username};"
                f"PWD={self.credentials.password};"
                f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
            )
        except ImportError:
            raise ImportError("pyodbc not installed. Run: pip install pyodbc")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute Azure SQL query and return DataFrame"""
        try:
            import sqlalchemy
            engine = sqlalchemy.create_engine(self._connection_string)
            return pd.read_sql_query(query, engine, params=params)
        except ImportError:
            raise ImportError("sqlalchemy not installed. Run: pip install sqlalchemy")
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test Azure SQL connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]
                return True, f"Azure SQL connection successful: {version[:50]}..."
        except Exception as e:
            return False, f"Azure SQL connection failed: {str(e)}"
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get Azure SQL database info"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA = ?
            """, (self.credentials.schema or 'dbo',))
            tables = [row[0] for row in cursor.fetchall()]
            
            return {
                "type": "Azure SQL",
                "version": version[:100] + "..." if len(version) > 100 else version,
                "server": self.credentials.host,
                "database": self.credentials.database,
                "schema": self.credentials.schema or 'dbo',
                "tables": tables
            }

class EnterpriseDatabaseManager:
    """Main database manager with enterprise support"""
    
    def __init__(self, config_file: str = "config/database.yaml"):
        self.config_file = config_file
        self._adapter: Optional[DatabaseAdapter] = None
        self._config = self._load_database_config()
    
    def _load_database_config(self) -> Dict[str, Any]:
        """Load database configuration"""
        import yaml
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.info(f"Database config file {self.config_file} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default database configuration"""
        return {
            "type": "sqlite",
            "sqlite": {
                "path": "data/telecom_db.sqlite"
            }
        }
    
    def get_adapter(self) -> DatabaseAdapter:
        """Get database adapter based on configuration"""
        if self._adapter is None:
            self._adapter = self._create_adapter()
        return self._adapter
    
    def _create_adapter(self) -> DatabaseAdapter:
        """Create database adapter based on configuration"""
        db_type = self._config.get("type", "sqlite").lower()
        
        if db_type == "sqlite":
            sqlite_config = self._config.get("sqlite", {})
            return SQLiteAdapter(sqlite_config.get("path", "data/telecom_db.sqlite"))
        
        elif db_type == "postgresql":
            pg_config = self._config.get("postgresql", {})
            credentials = DatabaseCredentials(
                host=pg_config.get("host"),
                port=pg_config.get("port"),
                database=pg_config.get("database"),
                username=pg_config.get("username"),
                password=pg_config.get("password"),
                schema=pg_config.get("schema")
            )
            return PostgreSQLAdapter(credentials)
        
        elif db_type == "snowflake":
            sf_config = self._config.get("snowflake", {})
            credentials = DatabaseCredentials(
                account=sf_config.get("account"),
                warehouse=sf_config.get("warehouse"),
                database=sf_config.get("database"),
                username=sf_config.get("username"),
                password=sf_config.get("password"),
                schema=sf_config.get("schema")
            )
            return SnowflakeAdapter(credentials)
        
        elif db_type in ["azuresql", "azure_sql"]:
            azure_config = self._config.get("azuresql", {})
            credentials = DatabaseCredentials(
                host=azure_config.get("server"),
                port=azure_config.get("port"),
                database=azure_config.get("database"),
                username=azure_config.get("username"),
                password=azure_config.get("password"),
                schema=azure_config.get("schema")
            )
            return AzureSQLAdapter(credentials)
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test database connection"""
        try:
            adapter = self.get_adapter()
            return adapter.test_connection()
        except Exception as e:
            return False, f"Failed to create adapter: {str(e)}"
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        adapter = self.get_adapter()
        return adapter.get_database_info()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute query using current adapter"""
        adapter = self.get_adapter()
        return adapter.execute_query(query, params)
    
    def migrate_from_sqlite(self, source_db_path: str = "data/telecom_db.sqlite") -> bool:
        """Migrate data from SQLite to target enterprise database"""
        try:
            # Create source SQLite adapter
            source_adapter = SQLiteAdapter(source_db_path)
            target_adapter = self.get_adapter()
            
            # Get list of tables to migrate
            source_info = source_adapter.get_database_info()
            tables = source_info.get("tables", [])
            
            logger.info(f"Starting migration of {len(tables)} tables from SQLite to {type(target_adapter).__name__}")
            
            for table in tables:
                if table.startswith('sqlite_'):  # Skip SQLite system tables
                    continue
                
                logger.info(f"Migrating table: {table}")
                
                # Read data from source
                df = source_adapter.execute_query(f"SELECT * FROM {table}")
                
                # Write to target (implementation depends on target database)
                self._write_table_to_target(target_adapter, table, df)
            
            logger.info("Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return False
    
    def _write_table_to_target(self, target_adapter: DatabaseAdapter, table_name: str, df: pd.DataFrame):
        """Write DataFrame to target database table"""
        # This is a simplified implementation
        # In production, you'd want more sophisticated table creation and data type mapping
        if isinstance(target_adapter, SQLiteAdapter):
            with target_adapter.get_connection() as conn:
                df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        elif isinstance(target_adapter, PostgreSQLAdapter):
            import sqlalchemy
            engine = sqlalchemy.create_engine(target_adapter._connection_string)
            df.to_sql(table_name, engine, if_exists='replace', index=False)
        
        elif isinstance(target_adapter, SnowflakeAdapter):
            # Snowflake requires special handling
            with target_adapter.get_connection() as conn:
                # Use Snowflake's pandas write utilities
                import snowflake.connector.pandas_tools as pd_tools
                success, nchunks, nrows, _ = pd_tools.write_pandas(
                    conn, df, table_name, auto_create_table=True
                )
                logger.info(f"Wrote {nrows} rows to {table_name} in {nchunks} chunks")
        
        elif isinstance(target_adapter, AzureSQLAdapter):
            import sqlalchemy
            engine = sqlalchemy.create_engine(target_adapter._connection_string)
            df.to_sql(table_name, engine, if_exists='replace', index=False)

# Global enterprise database manager instance
enterprise_db_manager = EnterpriseDatabaseManager()

def get_enterprise_db() -> EnterpriseDatabaseManager:
    """Get global enterprise database manager"""
    return enterprise_db_manager
