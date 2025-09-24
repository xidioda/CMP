#!/usr/bin/env python3
"""
Reset admin password for CMP platform
"""

import sys
import os
sys.path.append('/Users/xidioda/Projects/CMP')

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from cmp.models import User, UserRole
from cmp.config import Settings
from cmp.auth import hash_password, authenticate_user

def reset_admin_password():
    """Reset admin password to 'admin123'"""
    # Unset DEBUG environment variable
    if 'DEBUG' in os.environ:
        del os.environ['DEBUG']
    
    settings = Settings()
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # Find admin users
        admin_users = db.query(User).filter(
            User.email.in_(['admin@cmp.com', 'admin@cmp.local'])
        ).all()
        
        if not admin_users:
            print("❌ No admin users found. Creating new admin user...")
            # Create new admin user
            hashed_password = hash_password("admin123")
            new_admin = User(
                email="admin@cmp.com",
                hashed_password=hashed_password,
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(new_admin)
            db.commit()
            print("✅ Created new admin user: admin@cmp.com / admin123")
        else:
            # Reset password for existing admin users
            new_password = "admin123"
            hashed_password = hash_password(new_password)
            
            for user in admin_users:
                user.hashed_password = hashed_password
                print(f"✅ Reset password for {user.email}")
            
            db.commit()
            print(f"\n✅ Password reset complete for {len(admin_users)} admin users")
            print("New credentials: admin123")
        
        # Test authentication
        print("\n🧪 Testing authentication:")
        for email in ['admin@cmp.com', 'admin@cmp.local']:
            user = authenticate_user(db, email, "admin123")
            if user:
                print(f"✅ {email} / admin123 - Authentication successful")
            else:
                print(f"❌ {email} / admin123 - Authentication failed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()