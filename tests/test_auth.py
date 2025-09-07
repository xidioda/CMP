"""
Tests for authentication system including JWT tokens, user management, and access control.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
import datetime as dt

from cmp.main import app
from cmp.db import get_db, Base
from cmp.models import User, UserRole
from cmp.auth import hash_password, verify_password, create_access_token, verify_token

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def admin_user(db):
    """Create admin user for testing"""
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def orchestrator_user(db):
    """Create orchestrator user for testing"""
    user = User(
        email="orchestrator@test.com",
        hashed_password=hash_password("orch123"),
        full_name="Test Orchestrator",
        role=UserRole.ORCHESTRATOR,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def viewer_user(db):
    """Create viewer user for testing"""
    user = User(
        email="viewer@test.com",
        hashed_password=hash_password("view123"),
        full_name="Test Viewer",
        role=UserRole.VIEWER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def admin_token(admin_user):
    """Create admin access token"""
    return create_access_token({"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role.value})

@pytest.fixture
def orchestrator_token(orchestrator_user):
    """Create orchestrator access token"""
    return create_access_token({"sub": str(orchestrator_user.id), "email": orchestrator_user.email, "role": orchestrator_user.role.value})

@pytest.fixture
def viewer_token(viewer_user):
    """Create viewer access token"""
    return create_access_token({"sub": str(viewer_user.id), "email": viewer_user.email, "role": viewer_user.role.value})


class TestPasswordHashing:
    """Test password hashing functions"""
    
    def test_hash_password(self):
        password = "test123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
    
    def test_verify_password(self):
        password = "test123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification"""
    
    def test_create_access_token(self):
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_token(self):
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)
        payload = verify_token(token)
        
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_expired_token(self):
        data = {"sub": "123", "email": "test@example.com"}
        expired_delta = dt.timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expired_delta)
        
        from cmp.auth import AuthenticationError
        with pytest.raises(AuthenticationError, match="Invalid token"):
            verify_token(token)


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_permissions(self, db):
        admin = User(role=UserRole.ADMIN)
        orchestrator = User(role=UserRole.ORCHESTRATOR)
        viewer = User(role=UserRole.VIEWER)
        
        # Admin has all permissions
        assert admin.has_permission(UserRole.ADMIN) is True
        assert admin.has_permission(UserRole.ORCHESTRATOR) is True
        assert admin.has_permission(UserRole.VIEWER) is True
        
        # Orchestrator has orchestrator and viewer permissions
        assert orchestrator.has_permission(UserRole.ADMIN) is False
        assert orchestrator.has_permission(UserRole.ORCHESTRATOR) is True
        assert orchestrator.has_permission(UserRole.VIEWER) is True
        
        # Viewer has only viewer permissions
        assert viewer.has_permission(UserRole.ADMIN) is False
        assert viewer.has_permission(UserRole.ORCHESTRATOR) is False
        assert viewer.has_permission(UserRole.VIEWER) is True


class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""
    
    def test_login_success(self, client, admin_user):
        response = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@test.com"
    
    def test_login_invalid_credentials(self, client, admin_user):
        response = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        response = client.post("/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "password"
        })
        
        assert response.status_code == 401
    
    def test_get_current_user(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"
    
    def test_get_current_user_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_register_user_admin_only(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/auth/register", 
            headers=headers,
            json={
                "email": "newuser@test.com",
                "password": "newpass123",
                "full_name": "New User",
                "role": "viewer"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "viewer"
    
    def test_register_user_non_admin(self, client, viewer_token):
        headers = {"Authorization": f"Bearer {viewer_token}"}
        response = client.post("/auth/register", 
            headers=headers,
            json={
                "email": "newuser@test.com",
                "password": "newpass123",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    def test_list_users_admin_only(self, client, admin_token, viewer_token):
        # Admin can list users
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/auth/users", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Viewer cannot list users
        headers = {"Authorization": f"Bearer {viewer_token}"}
        response = client.get("/auth/users", headers=headers)
        assert response.status_code == 403


class TestDashboardAccess:
    """Test dashboard access control"""
    
    def test_dashboard_requires_auth(self, client):
        response = client.get("/dashboard")
        # Should return 401 if no auth header, 403 if auth header but invalid
        assert response.status_code in [401, 403]
    
    def test_dashboard_with_auth(self, client, viewer_token):
        headers = {"Authorization": f"Bearer {viewer_token}"}
        response = client.get("/dashboard", headers=headers)
        assert response.status_code == 200
    
    def test_agent_status_requires_viewer(self, client, viewer_token):
        headers = {"Authorization": f"Bearer {viewer_token}"}
        response = client.get("/dashboard/agent-status", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        assert "accountant" in data["agents"]
    
    def test_agent_status_no_auth(self, client):
        response = client.get("/dashboard/agent-status")
        # Should return 401 if no auth header, 403 if auth header but invalid
        assert response.status_code in [401, 403]


class TestRoleBasedAccess:
    """Test role-based access control for different endpoints"""
    
    def test_orchestrator_can_upload_invoice(self, client, orchestrator_token):
        headers = {"Authorization": f"Bearer {orchestrator_token}"}
        
        # Create a mock file upload
        files = {"file": ("test.png", b"fake image data", "image/png")}
        
        # Note: This would require more setup for actual file processing
        # For now, we're testing the authentication part
        response = client.post("/dashboard/upload-invoice", 
                             headers=headers, 
                             files=files)
        
        # We expect either success or a file processing error, not auth error
        assert response.status_code != 401
        assert response.status_code != 403
    
    def test_viewer_cannot_upload_invoice(self, client, viewer_token):
        headers = {"Authorization": f"Bearer {viewer_token}"}
        
        files = {"file": ("test.png", b"fake image data", "image/png")}
        response = client.post("/dashboard/upload-invoice", 
                             headers=headers, 
                             files=files)
        
        assert response.status_code == 403
        assert "Orchestrator access required" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
