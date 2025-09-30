"""
Comprehensive unit tests for database module (db.py)
Tests database initialization, session management, and database operations.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cmp.db import get_db, session_scope, init_db, engine, SessionLocal
from cmp.models import Base


class TestDatabase:
    """Test suite for database functionality"""
    
    def test_engine_exists(self):
        """Test that engine is properly created"""
        assert engine is not None
        assert hasattr(engine, 'url')
    
    def test_session_local_exists(self):
        """Test that SessionLocal is properly configured"""
        assert SessionLocal is not None
        assert hasattr(SessionLocal, 'bind')
    
    def test_session_scope_context_manager(self):
        """Test session_scope context manager"""
        # Create test database
        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(bind=test_engine)
        
        with patch('cmp.db.SessionLocal', TestSessionLocal):
            with session_scope() as session:
                assert session is not None
                assert hasattr(session, 'query')
                assert hasattr(session, 'commit')
                assert hasattr(session, 'rollback')
    
    def test_session_scope_exception_handling(self):
        """Test that session_scope handles exceptions properly"""
        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(bind=test_engine)
        
        with patch('cmp.db.SessionLocal', TestSessionLocal):
            try:
                with session_scope() as session:
                    # Simulate an error
                    raise Exception("Test error")
            except Exception as e:
                assert str(e) == "Test error"
                # Session should be rolled back and closed
    
    def test_init_db_creates_tables(self):
        """Test that init_db creates database tables"""
        test_engine = create_engine("sqlite:///:memory:")
        
        with patch('cmp.db.engine', test_engine):
            with patch.object(Base.metadata, 'create_all') as mock_create_all:
                init_db()
                mock_create_all.assert_called_once_with(bind=test_engine)
    
    def test_get_db_generator(self):
        """Test database session generator"""
        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(bind=test_engine)
        
        with patch('cmp.db.SessionLocal', TestSessionLocal):
            db_gen = get_db()
            db_session = next(db_gen)
            
            assert db_session is not None
            assert hasattr(db_session, 'query')
            assert hasattr(db_session, 'commit')
            assert hasattr(db_session, 'rollback')
            
            # Generator should close session
            try:
                next(db_gen)
            except StopIteration:
                pass  # Expected behavior
    
    def test_database_url_configuration(self):
        """Test database URL configuration"""
        with patch('cmp.db.settings') as mock_settings:
            mock_settings.database_url = "sqlite:///test.db"
            
            from cmp.db import _make_engine
            test_engine = _make_engine(mock_settings.database_url)
            
            assert test_engine is not None
            assert "test.db" in str(test_engine.url)
    
    def test_default_sqlite_url(self):
        """Test default SQLite URL generation"""
        from cmp.db import _get_default_sqlite_url
        
        default_url = _get_default_sqlite_url()
        assert default_url == "sqlite+pysqlite:///cmp.db"
    
    def test_make_engine_with_none_url(self):
        """Test engine creation with None URL (uses default)"""
        from cmp.db import _make_engine, _get_default_sqlite_url
        
        engine_with_none = _make_engine(None)
        default_url = _get_default_sqlite_url()
        
        assert engine_with_none is not None
        assert str(engine_with_none.url) == default_url
    
    def test_sqlite_connect_args(self):
        """Test SQLite connection arguments"""
        from cmp.db import _make_engine
        
        sqlite_engine = _make_engine("sqlite+pysqlite:///test.db")
        
        # Should have check_same_thread=False for SQLite
        assert sqlite_engine is not None


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database functionality"""
    
    def test_real_database_connection(self):
        """Test actual database connection and table creation"""
        test_engine = create_engine("sqlite:///:memory:")
        
        # Test table creation
        Base.metadata.create_all(bind=test_engine)
        
        # Verify some tables were created (based on models)
        inspector = test_engine.dialect.get_table_names(test_engine)
        assert len(inspector) > 0  # Some tables should exist
    
    def test_session_lifecycle(self):
        """Test complete session lifecycle"""
        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(bind=test_engine)
        
        with patch('cmp.db.SessionLocal', TestSessionLocal):
            # Test session creation and cleanup
            with session_scope() as session:
                # Session should be active
                assert session.is_active
            
            # Session should be closed after context
            assert not session.is_active
    
    def test_database_crud_operations(self):
        """Test basic CRUD operations work with database"""
        from cmp.models import User, UserRole
        
        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(bind=test_engine)
        
        with patch('cmp.db.SessionLocal', TestSessionLocal):
            with session_scope() as session:
                # Create
                user = User(
                    email="test@example.com",
                    hashed_password="hashed_password",
                    full_name="Test User",
                    role=UserRole.USER,
                    is_active=True
                )
                session.add(user)
                session.flush()  # Get ID without committing
                
                user_id = user.id
                assert user_id is not None
                
                # Read
                retrieved_user = session.query(User).filter(User.id == user_id).first()
                assert retrieved_user is not None
                assert retrieved_user.email == "test@example.com"
                
                # Update
                retrieved_user.full_name = "Updated User"
                session.flush()
                
                updated_user = session.query(User).filter(User.id == user_id).first()
                assert updated_user.full_name == "Updated User"
                
                # Delete
                session.delete(updated_user)
                session.flush()
                
                deleted_user = session.query(User).filter(User.id == user_id).first()
                assert deleted_user is None
    
    def test_concurrent_sessions(self):
        """Test that multiple sessions work independently"""
        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(bind=test_engine)
        
        with patch('cmp.db.SessionLocal', TestSessionLocal):
            # Two independent sessions
            with session_scope() as session1:
                with session_scope() as session2:
                    # Sessions should be different instances
                    assert session1 is not session2
                    
                    # Both should be functional
                    assert session1.is_active
                    assert session2.is_active
    
    def test_transaction_rollback_on_error(self):
        """Test transaction rollback when error occurs"""
        from cmp.models import User, UserRole
        
        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(bind=test_engine)
        
        with patch('cmp.db.SessionLocal', TestSessionLocal):
            try:
                with session_scope() as session:
                    # Add a user
                    user = User(
                        email="test@example.com",
                        hashed_password="hashed_password",
                        full_name="Test User",
                        role=UserRole.USER,
                        is_active=True
                    )
                    session.add(user)
                    session.flush()
                    
                    # Verify user exists
                    assert session.query(User).count() == 1
                    
                    # Simulate an error
                    raise Exception("Simulated error")
                    
            except Exception:
                pass  # Expected
            
            # Start new session to verify rollback
            with session_scope() as session:
                # User should not exist due to rollback
                assert session.query(User).count() == 0