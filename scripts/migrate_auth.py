"""
Database migration script to create user authentication tables.

Run this script to set up the authentication system in the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import text
from cmp.db import engine, init_db
from cmp.models import User, UserRole
from cmp.auth import create_user
from cmp.logging_config import get_logger
from sqlalchemy.orm import Session

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import text
from cmp.db import engine, init_db
from cmp.models import User, UserRole
from cmp.auth import create_user
from cmp.logging_config import get_logger
from sqlalchemy.orm import Session

logger = get_logger("migration")


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    init_db()
    logger.info("Database tables created successfully")


def create_admin_user():
    """Create default admin user"""
    logger.info("Creating default admin user...")
    
    with Session(engine) as db:
        try:
            # Check if admin already exists
            admin_email = "admin@cmp.local"
            existing_admin = db.execute(
                text("SELECT id FROM users WHERE email = :email"), 
                {"email": admin_email}
            ).fetchone()
            
            if existing_admin:
                logger.info("Admin user already exists")
                return
            
            # Create admin user
            admin_user = User(
                email=admin_email,
                hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "admin123"
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            
            db.add(admin_user)
            db.commit()
            
            logger.info(f"Created admin user: {admin_email}")
            logger.info("Default password: admin123 (change immediately!)")
            
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            db.rollback()
            raise


def main():
    """Run migration"""
    try:
        logger.info("Starting database migration for authentication system...")
        
        # Create tables
        create_tables()
        
        # Create default admin user
        create_admin_user()
        
        logger.info("Migration completed successfully!")
        logger.info("You can now log in with:")
        logger.info("  Email: admin@cmp.local")
        logger.info("  Password: admin123")
        logger.info("  IMPORTANT: Change the default password immediately!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()
