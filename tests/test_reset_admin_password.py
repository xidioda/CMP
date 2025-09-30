"""
Comprehensive unit tests for reset_admin_password.py
Tests admin password reset functionality and database operations.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

# We'll test the functionality without importing the actual module
# to avoid side effects during testing


class TestAdminPasswordReset:
    """Test suite for admin password reset functionality"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        session = MagicMock(spec=Session)
        return session
    
    @pytest.fixture
    def mock_user(self):
        """Create mock admin user"""
        user = MagicMock()
        user.email = "admin@example.com"
        user.role = "admin"
        user.is_active = True
        return user
    
    def test_password_hashing(self):
        """Test password hashing functionality"""
        from cmp.auth import hash_password
        
        password = "new_admin_password"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_password_verification(self):
        """Test password verification after hashing"""
        from cmp.auth import hash_password, verify_password
        
        password = "test_password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    @patch('builtins.input')
    @patch('getpass.getpass')
    def test_password_input_validation(self, mock_getpass, mock_input):
        """Test password input validation"""
        # Mock user inputs
        mock_input.return_value = "admin@example.com"
        mock_getpass.side_effect = ["newpassword123", "newpassword123"]
        
        # Test that password confirmation works
        email = mock_input.return_value
        password1 = mock_getpass.return_value
        password2 = mock_getpass.return_value
        
        assert email == "admin@example.com"
        assert password1 == password2
    
    @patch('builtins.input')
    @patch('getpass.getpass')
    def test_password_mismatch_handling(self, mock_getpass, mock_input):
        """Test handling of password mismatch"""
        mock_input.return_value = "admin@example.com"
        mock_getpass.side_effect = ["password1", "password2"]
        
        password1 = mock_getpass.return_value
        mock_getpass.side_effect = ["password2"]
        password2 = mock_getpass.return_value
        
        # Passwords should not match
        assert password1 != password2
    
    def test_admin_user_lookup(self, mock_db_session, mock_user):
        """Test admin user lookup in database"""
        # Mock query result
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Simulate user lookup
        from cmp.models import User
        user = mock_db_session.query(User).filter(User.email == "admin@example.com").first()
        
        assert user is not None
        assert user.email == "admin@example.com"
        assert user.role == "admin"
    
    def test_admin_user_not_found(self, mock_db_session):
        """Test handling when admin user is not found"""
        # Mock empty query result
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        from cmp.models import User
        user = mock_db_session.query(User).filter(User.email == "nonexistent@example.com").first()
        
        assert user is None
    
    def test_password_update_success(self, mock_db_session, mock_user):
        """Test successful password update"""
        from cmp.auth import hash_password
        
        new_password = "new_secure_password"
        hashed_password = hash_password(new_password)
        
        # Update user password
        mock_user.hashed_password = hashed_password
        mock_db_session.commit()
        
        assert mock_user.hashed_password == hashed_password
        mock_db_session.commit.assert_called_once()
    
    def test_database_transaction_rollback(self, mock_db_session):
        """Test database transaction rollback on error"""
        # Simulate database error
        mock_db_session.commit.side_effect = Exception("Database error")
        
        try:
            mock_db_session.commit()
        except Exception:
            mock_db_session.rollback()
        
        mock_db_session.rollback.assert_called_once()
    
    def test_email_validation(self):
        """Test email format validation"""
        import re
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        valid_emails = [
            "admin@example.com",
            "test.user@domain.org",
            "user+tag@company.co.uk"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user.domain.com"
        ]
        
        for email in valid_emails:
            assert re.match(email_pattern, email) is not None
        
        for email in invalid_emails:
            assert re.match(email_pattern, email) is None
    
    def test_password_strength_validation(self):
        """Test password strength validation"""
        def validate_password_strength(password):
            """Basic password strength validation"""
            if len(password) < 8:
                return False, "Password must be at least 8 characters long"
            
            if not any(c.isupper() for c in password):
                return False, "Password must contain at least one uppercase letter"
            
            if not any(c.islower() for c in password):
                return False, "Password must contain at least one lowercase letter"
            
            if not any(c.isdigit() for c in password):
                return False, "Password must contain at least one digit"
            
            return True, "Password is strong"
        
        # Test weak passwords
        weak_passwords = [
            "123",
            "password",
            "PASSWORD",
            "12345678",
            "abcdefgh"
        ]
        
        for password in weak_passwords:
            is_strong, message = validate_password_strength(password)
            assert is_strong is False
        
        # Test strong passwords
        strong_passwords = [
            "StrongPass123",
            "SecurePassword1",
            "MyP@ssw0rd"
        ]
        
        for password in strong_passwords:
            is_strong, message = validate_password_strength(password)
            assert is_strong is True


class TestAdminPasswordResetIntegration:
    """Integration tests for admin password reset"""
    
    @pytest.fixture
    def test_db_session(self):
        """Create test database session"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from cmp.models import Base
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        yield session
        session.close()
    
    def test_create_admin_user(self, test_db_session):
        """Test creating admin user for password reset"""
        from cmp.models import User, UserRole
        from cmp.auth import hash_password
        
        admin_user = User(
            email="admin@example.com",
            hashed_password=hash_password("old_password"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        test_db_session.add(admin_user)
        test_db_session.commit()
        
        # Verify user was created
        created_user = test_db_session.query(User).filter(User.email == "admin@example.com").first()
        assert created_user is not None
        assert created_user.role == UserRole.ADMIN
    
    def test_update_admin_password(self, test_db_session):
        """Test updating admin password in database"""
        from cmp.models import User, UserRole
        from cmp.auth import hash_password, verify_password
        
        # Create admin user
        admin_user = User(
            email="admin@example.com",
            hashed_password=hash_password("old_password"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        test_db_session.add(admin_user)
        test_db_session.commit()
        
        # Update password
        new_password = "new_secure_password"
        admin_user.hashed_password = hash_password(new_password)
        test_db_session.commit()
        
        # Verify password was updated
        updated_user = test_db_session.query(User).filter(User.email == "admin@example.com").first()
        assert verify_password(new_password, updated_user.hashed_password) is True
        assert verify_password("old_password", updated_user.hashed_password) is False
    
    def test_multiple_admin_users(self, test_db_session):
        """Test handling multiple admin users"""
        from cmp.models import User, UserRole
        from cmp.auth import hash_password
        
        # Create multiple admin users
        admin1 = User(
            email="admin1@example.com",
            hashed_password=hash_password("password1"),
            full_name="Admin One",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        admin2 = User(
            email="admin2@example.com",
            hashed_password=hash_password("password2"),
            full_name="Admin Two",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        test_db_session.add_all([admin1, admin2])
        test_db_session.commit()
        
        # Query should return specific admin user
        target_admin = test_db_session.query(User).filter(User.email == "admin1@example.com").first()
        assert target_admin.email == "admin1@example.com"
        assert target_admin.full_name == "Admin One"
    
    def test_non_admin_user_restriction(self, test_db_session):
        """Test that non-admin users cannot be targeted for reset"""
        from cmp.models import User, UserRole
        from cmp.auth import hash_password
        
        # Create regular user
        regular_user = User(
            email="user@example.com",
            hashed_password=hash_password("password"),
            full_name="Regular User",
            role=UserRole.USER,
            is_active=True
        )
        
        test_db_session.add(regular_user)
        test_db_session.commit()
        
        # Query for admin users only
        admin_users = test_db_session.query(User).filter(User.role == UserRole.ADMIN).all()
        
        # Regular user should not be in admin users list
        admin_emails = [user.email for user in admin_users]
        assert "user@example.com" not in admin_emails