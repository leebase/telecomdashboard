"""Tests for authentication and authorization system."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.security.auth_manager import (
    User, Permission, RoleBasedAccessControl, JWTTokenManager,
    SessionManager, LocalAuthProvider, AuthProvider
)
from metadata_runtime.models import MetadataConfig


class TestUser:
    """Test User class functionality."""

    def test_user_creation(self):
        """Test user object creation."""
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst", "viewer"],
            groups=["data_team"],
            attributes={"department": "engineering"}
        )

        assert user.user_id == "user123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.has_role("analyst")
        assert not user.has_role("admin")
        assert user.has_any_role(["analyst", "admin"])
        assert user.has_group("data_team")
        assert user.has_any_group(["data_team", "admin_team"])

    def test_user_defaults(self):
        """Test user default values."""
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=[],
            groups=[]
        )

        assert user.is_active is True
        assert user.last_login is None


class TestPermission:
    """Test Permission class functionality."""

    def test_permission_creation(self):
        """Test permission object creation."""
        permission = Permission(
            resource="dashboard",
            action="view",
            conditions={"department": "engineering"}
        )

        assert permission.resource == "dashboard"
        assert permission.action == "view"
        assert permission.conditions == {"department": "engineering"}

    def test_permission_matching(self):
        """Test permission matching."""
        permission = Permission(resource="dashboard", action="view")

        assert permission.matches("dashboard", "view")
        assert not permission.matches("dashboard", "edit")
        assert not permission.matches("reports", "view")


class TestRoleBasedAccessControl:
    """Test RBAC functionality."""

    def test_rbac_initialization(self):
        """Test RBAC initialization with config."""
        config = MetadataConfig(
            schema_version="1.0",
            app_version="0.9.0",
            pack_id="test",
            label="Test Pack",
            globals={},
            dialects={},
            data_sources={},
            filters={},
            subject_areas=[],
            kpis=[],
            security={
                "roles": {
                    "analyst": {
                        "permissions": [
                            {"resource": "dashboard", "action": "view"},
                            {"resource": "reports", "action": "read"}
                        ]
                    }
                },
                "role_hierarchy": {
                    "admin": ["analyst"]
                }
            }
        )

        rbac = RoleBasedAccessControl(config)

        assert "analyst" in rbac.roles
        assert len(rbac.roles["analyst"]) == 2
        assert rbac.role_hierarchy["admin"] == ["analyst"]

    def test_get_user_permissions(self):
        """Test getting user permissions."""
        config = MetadataConfig(
            schema_version="1.0",
            app_version="0.9.0",
            pack_id="test",
            label="Test Pack",
            globals={},
            dialects={},
            data_sources={},
            filters={},
            subject_areas=[],
            kpis=[],
            security={
                "roles": {
                    "analyst": {
                        "permissions": [
                            {"resource": "dashboard", "action": "view"}
                        ]
                    },
                    "viewer": {
                        "permissions": [
                            {"resource": "reports", "action": "read"}
                        ]
                    }
                },
                "role_hierarchy": {
                    "admin": ["analyst", "viewer"]
                }
            }
        )

        rbac = RoleBasedAccessControl(config)
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst"],
            groups=[]
        )

        permissions = rbac.get_user_permissions(user)

        assert len(permissions) == 1
        assert permissions[0].resource == "dashboard"
        assert permissions[0].action == "view"

    def test_has_permission(self):
        """Test permission checking."""
        config = MetadataConfig(
            schema_version="1.0",
            app_version="0.9.0",
            pack_id="test",
            label="Test Pack",
            globals={},
            dialects={},
            data_sources={},
            filters={},
            subject_areas=[],
            kpis=[],
            security={
                "roles": {
                    "analyst": {
                        "permissions": [
                            {"resource": "dashboard", "action": "view"}
                        ]
                    }
                }
            }
        )

        rbac = RoleBasedAccessControl(config)
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst"],
            groups=[]
        )

        assert rbac.has_permission(user, "dashboard", "view")
        assert not rbac.has_permission(user, "dashboard", "edit")
        assert not rbac.has_permission(user, "reports", "view")

    def test_filter_accessible_resources(self):
        """Test filtering accessible resources."""
        config = MetadataConfig(
            schema_version="1.0",
            app_version="0.9.0",
            pack_id="test",
            label="Test Pack",
            globals={},
            dialects={},
            data_sources={},
            filters={},
            subject_areas=[],
            kpis=[],
            security={
                "roles": {
                    "analyst": {
                        "permissions": [
                            {"resource": "dashboard", "action": "view"}
                        ]
                    }
                }
            }
        )

        rbac = RoleBasedAccessControl(config)
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst"],
            groups=[]
        )

        resources = ["dashboard", "reports", "admin"]
        accessible = rbac.filter_accessible_resources(user, resources, "view")

        assert accessible == ["dashboard"]


class TestJWTTokenManager:
    """Test JWT token management."""

    def test_create_token(self):
        """Test JWT token creation."""
        manager = JWTTokenManager(secret_key="test-secret")
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst"],
            groups=[]
        )

        token = manager.create_token(user, expires_in=3600)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token(self):
        """Test JWT token verification."""
        manager = JWTTokenManager(secret_key="test-secret")
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst"],
            groups=[]
        )

        token = manager.create_token(user)
        verified_user = manager.verify_token(token)

        assert verified_user is not None
        assert verified_user.user_id == user.user_id
        assert verified_user.username == user.username
        assert verified_user.roles == user.roles

    def test_verify_expired_token(self):
        """Test expired token verification."""
        manager = JWTTokenManager(secret_key="test-secret")
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst"],
            groups=[]
        )

        # Create token that expires immediately
        token = manager.create_token(user, expires_in=-1)
        verified_user = manager.verify_token(token)

        assert verified_user is None

    def test_verify_invalid_token(self):
        """Test invalid token verification."""
        manager = JWTTokenManager(secret_key="test-secret")

        verified_user = manager.verify_token("invalid-token")

        assert verified_user is None


class TestSessionManager:
    """Test session management."""

    @patch('streamlit.session_state')
    def test_login_user(self, mock_session_state):
        """Test user login."""
        token_manager = JWTTokenManager(secret_key="test-secret")
        session_manager = SessionManager(token_manager)

        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst"],
            groups=[]
        )

        token = session_manager.login_user(user)

        assert isinstance(token, str)
        assert mock_session_state.auth_token == token
        assert mock_session_state.user == user
        assert 'login_time' in mock_session_state

    @patch('streamlit.session_state')
    def test_logout_user(self, mock_session_state):
        """Test user logout."""
        token_manager = JWTTokenManager(secret_key="test-secret")
        session_manager = SessionManager(token_manager)

        # Set up session state
        mock_session_state.auth_token = "test-token"
        mock_session_state.user = Mock()
        mock_session_state.login_time = 1234567890

        session_manager.logout_user()

        assert 'auth_token' not in mock_session_state
        assert 'user' not in mock_session_state
        assert 'login_time' not in mock_session_state

    @patch('streamlit.session_state')
    def test_get_current_user_valid(self, mock_session_state):
        """Test getting current user with valid token."""
        token_manager = JWTTokenManager(secret_key="test-secret")
        session_manager = SessionManager(token_manager)

        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst"],
            groups=[]
        )

        token = token_manager.create_token(user)
        mock_session_state.auth_token = token
        mock_session_state.login_time = time.time()

        current_user = session_manager.get_current_user()

        assert current_user is not None
        assert current_user.user_id == user.user_id

    @patch('streamlit.session_state')
    def test_get_current_user_expired_session(self, mock_session_state):
        """Test getting current user with expired session."""
        token_manager = JWTTokenManager(secret_key="test-secret")
        session_manager = SessionManager(token_manager)

        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst"],
            groups=[]
        )

        token = token_manager.create_token(user)
        mock_session_state.auth_token = token
        mock_session_state.login_time = time.time() - 7200  # 2 hours ago

        current_user = session_manager.get_current_user()

        assert current_user is None


class TestLocalAuthProvider:
    """Test local authentication provider."""

    def test_load_users_from_file(self):
        """Test loading users from JSON file."""
        users_data = {
            "users": [
                {
                    "user_id": "user123",
                    "username": "testuser",
                    "email": "test@example.com",
                    "roles": ["analyst"],
                    "groups": ["data_team"],
                    "attributes": {"department": "engineering"},
                    "is_active": True
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(users_data, f)
            users_file = Path(f.name)

        try:
            provider = LocalAuthProvider(users_file)

            # Test user lookup by username
            user = provider.get_user("testuser")
            assert user is not None
            assert user.user_id == "user123"
            assert user.has_role("analyst")

            # Test authentication
            authenticated_user = provider.authenticate("testuser", "password")
            assert authenticated_user is not None
            assert authenticated_user.username == "testuser"

        finally:
            users_file.unlink()

    def test_authenticate_inactive_user(self):
        """Test authentication of inactive user."""
        users_data = {
            "users": [
                {
                    "user_id": "user123",
                    "username": "testuser",
                    "email": "test@example.com",
                    "roles": ["analyst"],
                    "groups": ["data_team"],
                    "is_active": False
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(users_data, f)
            users_file = Path(f.name)

        try:
            provider = LocalAuthProvider(users_file)

            authenticated_user = provider.authenticate("testuser", "password")
            assert authenticated_user is None

        finally:
            users_file.unlink()

    def test_authenticate_nonexistent_user(self):
        """Test authentication of nonexistent user."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"users": []}, f)
            users_file = Path(f.name)

        try:
            provider = LocalAuthProvider(users_file)

            authenticated_user = provider.authenticate("nonexistent", "password")
            assert authenticated_user is None

        finally:
            users_file.unlink()


@pytest.mark.integration
class TestAuthIntegration:
    """Integration tests for authentication system."""

    def test_complete_auth_flow(self):
        """Test complete authentication flow."""
        # Create test user
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["analyst"],
            groups=["data_team"]
        )

        # Initialize components
        config = MetadataConfig(
            schema_version="1.0",
            app_version="0.9.0",
            pack_id="test",
            label="Test Pack",
            globals={},
            dialects={},
            data_sources={},
            filters={},
            subject_areas=[],
            kpis=[],
            security={
                "roles": {
                    "analyst": {
                        "permissions": [
                            {"resource": "dashboard", "action": "view"}
                        ]
                    }
                }
            }
        )

        token_manager = JWTTokenManager(secret_key="test-secret")
        session_manager = SessionManager(token_manager)
        rbac = RoleBasedAccessControl(config)

        # Test token creation and verification
        token = token_manager.create_token(user)
        verified_user = token_manager.verify_token(token)

        assert verified_user is not None
        assert verified_user.user_id == user.user_id

        # Test RBAC
        assert rbac.has_permission(verified_user, "dashboard", "view")
        assert not rbac.has_permission(verified_user, "admin", "manage")

        # Test resource filtering
        resources = ["dashboard", "admin", "reports"]
        accessible = rbac.filter_accessible_resources(verified_user, resources, "view")
        assert accessible == ["dashboard"]