#!/usr/bin/env python3
"""
Add OTP columns to User model
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

def add_otp_columns():
    """Add OTP columns to users table"""
    app = create_app()
    
    with app.app_context():
        print("🔐 Adding OTP columns to User model...")
        
        try:
            # For SQLite, we'll try to add columns directly and handle errors
            with db.engine.connect() as conn:
                try:
                    conn.execute(db.text("ALTER TABLE users ADD COLUMN reset_otp VARCHAR(64)"))
                    conn.commit()
                    print("✅ Added reset_otp column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("ℹ️  reset_otp column already exists")
                    else:
                        print(f"⚠️  Error adding reset_otp: {e}")
                
                try:
                    conn.execute(db.text("ALTER TABLE users ADD COLUMN reset_otp_expiry TIMESTAMP"))
                    conn.commit()
                    print("✅ Added reset_otp_expiry column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("ℹ️  reset_otp_expiry column already exists")
                    else:
                        print(f"⚠️  Error adding reset_otp_expiry: {e}")
                        
        except Exception as e:
            print(f"❌ Error: {e}")
            
        # Test the User model
        try:
            user = User.query.first()
            if user:
                print(f"✅ User model works: {user}")
                print(f"   - Has reset_otp: {hasattr(user, 'reset_otp')}")
                print(f"   - Has reset_otp_expiry: {hasattr(user, 'reset_otp_expiry')}")
            else:
                print("⚠️  No users in database to test")
        except Exception as e:
            print(f"❌ Error testing User model: {e}")
        
        print("\n🎉 OTP columns are ready for testing!")

if __name__ == "__main__":
    add_otp_columns()
