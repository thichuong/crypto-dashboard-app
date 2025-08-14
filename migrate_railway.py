#!/usr/bin/env python3
"""
Simple migration script for Railway - Add translation columns
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_database():
    """Add translation columns to Report table"""
    
    try:
        # Import Flask app
        from app import create_app
        from app.extensions import db
        
        print("Creating Flask app context...")
        app = create_app()
        
        with app.app_context():
            print("Connected to database successfully")
            
            # Try to add columns using raw SQL
            try:
                print("Adding html_content_en column...")
                db.session.execute(db.text("ALTER TABLE report ADD COLUMN html_content_en TEXT"))
                db.session.commit()
                print("✓ Added html_content_en column")
            except Exception as e:
                error_str = str(e).lower()
                if "duplicate column" in error_str or "already exists" in error_str or "duplicate" in error_str:
                    print("✓ html_content_en column already exists")
                else:
                    print(f"Error adding html_content_en: {e}")
            
            try:
                print("Adding js_content_en column...")
                db.session.execute(db.text("ALTER TABLE report ADD COLUMN js_content_en TEXT"))
                db.session.commit()
                print("✓ Added js_content_en column")
            except Exception as e:
                error_str = str(e).lower()
                if "duplicate column" in error_str or "already exists" in error_str or "duplicate" in error_str:
                    print("✓ js_content_en column already exists")
                else:
                    print(f"Error adding js_content_en: {e}")
        
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
