"""Authentication and authorization framework for metadata runtime."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

import streamlit as st

from metadata_runtime.models import MetadataConfig

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User information and permissions."""
    user_id: str
    username: str
    email: str
    roles: List[str]
    groups: List[str]
    attributes: Dict[str, Any]
    is_active: bool = True
    last_login: Optional[float] = None

    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return role in self.roles

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)

    def has_group(self, group: str) -> bool:
        """Check if user belongs to specific group."""
        return group in self.groups

    def has_any_group(self, groups: List[str]) -> bool:
        """Check if user belongs to any of the specified groups."""
        return any(group in self.groups for group in groups)


@dataclass
class Permission:
    """Permission definition."""
    resource: str
    action: str
    conditions: Optional[Dict[str, Any]] = None

    def matches(self, requested_resource: str, requested_action: str) -> bool:
        """Check if this permission matches the requested resource and action."""
        return self.resource == requested_resource and self.action == requested_action


class RoleBasedAccessControl:
    """Role-based access control system."""

    def __init__(self, config: MetadataConfig):
        self.config = config
        self.roles: Dict[str, List[Permission]] = {}
        self.role_hierarchy: Dict[str, List[str]] = {}
        self._load_roles()

    def _load_roles(self):
        """Load roles and permissions from metadata config."""
        if not hasattr(self.config, 'security') or not self.config.security:
            logger.warning("No security configuration found in metadata")
            return

        security = self.config.security

        # Load role definitions
        if 'roles' in security:
            for role_name, role_config in security['roles'].items():
                permissions = []

                # Parse permissions
                if 'permissions' in role_config:
                    for perm_config in role_config['permissions']:
                        if isinstance(perm_config, dict):
                            permission = Permission(
                                resource=perm_config.get('resource', ''),
                                action=perm_config.get('action', ''),
                                conditions=perm_config.get('conditions')
                            )
                            permissions.append(permission)

                self.roles[role_name] = permissions

        # Load role hierarchy
        if 'role_hierarchy' in security:
            self.role_hierarchy = security['role_hierarchy']

    def get_user_permissions(self, user: User) -> List[Permission]:
        """Get all permissions for a user based on their roles."""
        permissions = []

        for role in user.roles:
            if role in self.roles:
                permissions.extend(self.roles[role])

            # Add permissions from parent roles
            if role in self.role_hierarchy:
                for parent_role in self.role_hierarchy[role]:
                    if parent_role in self.roles:
                        permissions.extend(self.roles[parent_role])

        return permissions

    def has_permission(self, user: User, resource: str, action: str) -> bool:
        """Check if user has permission for specific resource and action."""
        permissions = self.get_user_permissions(user)

        for permission in permissions:
            if permission.matches(resource, action):
                # Check conditions if any
                if permission.conditions:
                    if not self._check_conditions(user, permission.conditions):
                        continue
                return True

        return False

    def _check_conditions(self, user: User, conditions: Dict[str, Any]) -> bool:
        """Check if user meets permission conditions."""
        for condition_key, condition_value in conditions.items():
            if condition_key == 'user_attribute':
                attr_name = condition_value.get('name')
                attr_value = condition_value.get('value')
                if attr_name and user.attributes.get(attr_name) != attr_value:
                    return False
            elif condition_key == 'group_membership':
                required_groups = condition_value.get('groups', [])
                if not user.has_any_group(required_groups):
                    return False
            elif condition_key == 'time_restriction':
                # Implement time-based restrictions
                pass

        return True

    def filter_accessible_resources(self, user: User, resources: List[str], action: str) -> List[str]:
        """Filter list of resources user can access."""
        accessible = []

        for resource in resources:
            if self.has_permission(user, resource, action):
                accessible.append(resource)

        return accessible


class JWTTokenManager:
    """JWT token management for authentication."""

    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "default-secret-key")
        self.algorithm = algorithm

    def create_token(self, user: User, expires_in: int = 3600) -> str:
        """Create JWT token for user."""
        import jwt

        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles,
            "groups": user.groups,
            "iat": int(time.time()),
            "exp": int(time.time()) + expires_in
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user."""
        import jwt

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check expiration
            if payload.get('exp', 0) < time.time():
                return None

            user = User(
                user_id=payload['user_id'],
                username=payload['username'],
                email=payload['email'],
                roles=payload.get('roles', []),
                groups=payload.get('groups', []),
                attributes={}
            )

            return user

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh JWT token."""
        user = self.verify_token(token)
        if user:
            return self.create_token(user)
        return None


class SessionManager:
    """Session management for Streamlit applications."""

    def __init__(self, token_manager: JWTTokenManager):
        self.token_manager = token_manager
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour default

    def login_user(self, user: User) -> str:
        """Log in user and create session token."""
        token = self.token_manager.create_token(user)

        # Store in Streamlit session state
        st.session_state.auth_token = token
        st.session_state.user = user
        st.session_state.login_time = time.time()

        logger.info(f"User {user.username} logged in successfully")
        return token

    def logout_user(self):
        """Log out current user."""
        if 'user' in st.session_state:
            user = st.session_state.user
            logger.info(f"User {user.username} logged out")

        # Clear session state
        for key in ['auth_token', 'user', 'login_time']:
            if key in st.session_state:
                del st.session_state[key]

    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user."""
        if 'auth_token' not in st.session_state:
            return None

        token = st.session_state.auth_token
        user = self.token_manager.verify_token(token)

        if user:
            # Check session timeout
            login_time = st.session_state.get('login_time', 0)
            if time.time() - login_time > self.session_timeout:
                self.logout_user()
                return None

            # Update last activity
            st.session_state.last_activity = time.time()
            return user

        # Invalid token, clear session
        self.logout_user()
        return None

    def require_authentication(self, redirect_to: str = "/login"):
        """Require authentication for page access."""
        user = self.get_current_user()
        if not user:
            st.error("Authentication required")
            st.stop()
        return user

    def require_permission(self, resource: str, action: str, rbac: RoleBasedAccessControl):
        """Require specific permission for page access."""
        user = self.require_authentication()
        if not rbac.has_permission(user, resource, action):
            st.error(f"Access denied: insufficient permissions for {resource}:{action}")
            st.stop()
        return user


class AuthProvider:
    """Authentication provider interface."""

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password."""
        raise NotImplementedError

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        raise NotImplementedError


class LocalAuthProvider(AuthProvider):
    """Local authentication provider using environment/config."""

    def __init__(self, users_file: Optional[Path] = None):
        self.users_file = users_file or Path("config/users.json")
        self.users: Dict[str, User] = {}
        self._load_users()

    def _load_users(self):
        """Load users from configuration file."""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)

                for user_data in users_data.get('users', []):
                    user = User(
                        user_id=user_data['user_id'],
                        username=user_data['username'],
                        email=user_data['email'],
                        roles=user_data.get('roles', []),
                        groups=user_data.get('groups', []),
                        attributes=user_data.get('attributes', {}),
                        is_active=user_data.get('is_active', True)
                    )
                    self.users[user.user_id] = user
                    self.users[user.username] = user  # Allow lookup by username

            except Exception as e:
                logger.error(f"Failed to load users from {self.users_file}: {e}")

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Simple authentication (for demo - use proper auth in production)."""
        user = self.users.get(username)
        if user and user.is_active:
            # In production, verify password hash
            # For demo, accept any password for active users
            return user
        return None

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID or username."""
        return self.users.get(user_id)


# Streamlit authentication components
def create_login_form(auth_provider: AuthProvider, session_manager: SessionManager):
    """Create Streamlit login form."""
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password")
                return

            user = auth_provider.authenticate(username, password)
            if user:
                session_manager.login_user(user)
                st.success(f"Welcome, {user.username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")


def create_logout_button(session_manager: SessionManager):
    """Create logout button."""
    if st.sidebar.button("Logout"):
        session_manager.logout_user()
        st.rerun()


def display_user_info(user: User):
    """Display current user information."""
    with st.sidebar.expander("👤 User Info"):
        st.write(f"**Username:** {user.username}")
        st.write(f"**Email:** {user.email}")
        st.write(f"**Roles:** {', '.join(user.roles)}")
        st.write(f"**Groups:** {', '.join(user.groups)}")


# Initialize authentication system
def init_auth_system(config: MetadataConfig) -> tuple[AuthProvider, SessionManager, RoleBasedAccessControl]:
    """Initialize complete authentication system."""
    # Initialize components
    auth_provider = LocalAuthProvider()
    token_manager = JWTTokenManager()
    session_manager = SessionManager(token_manager)
    rbac = RoleBasedAccessControl(config)

    return auth_provider, session_manager, rbac


__all__ = [
    "User",
    "Permission",
    "RoleBasedAccessControl",
    "JWTTokenManager",
    "SessionManager",
    "AuthProvider",
    "LocalAuthProvider",
    "create_login_form",
    "create_logout_button",
    "display_user_info",
    "init_auth_system"
]