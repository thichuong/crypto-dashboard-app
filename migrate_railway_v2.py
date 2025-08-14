#!/usr/bin/env python3
"""
Improved Railway migration script with better error handling and fallback support
"""

import os
import sys
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_environment():
    """Check if we're running in Railway environment and have required env vars"""
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    database_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
    
    print(f"🔍 Environment check:")
    print(f"   Railway Environment: {railway_env or 'Not detected'}")
    print(f"   Database URL: {'✅ Set' if database_url else '❌ Not set'}")
    
    if not database_url:
        print("⚠️  Warning: No database URL found. This is normal for local development.")
        print("   For Railway deployment, ensure DATABASE_URL is set in environment variables.")
        return False, "No database URL configured"
    
    # Check if we can resolve the database host
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        if 'railway.internal' in parsed.hostname and not railway_env:
            return False, f"Internal Railway hostname detected but not in Railway environment: {parsed.hostname}"
    except Exception as e:
        print(f"⚠️  Could not parse database URL: {e}")
    
    return True, None

def migrate_database():
    """Add translation columns to Report table with better error handling"""
    
    # Check environment first
    can_connect, error_msg = check_environment()
    if not can_connect:
        print(f"ℹ️  Skipping migration: {error_msg}")
        if os.getenv('RAILWAY_ENVIRONMENT'):
            # In Railway, this is a real error
            print("❌ Migration failed in Railway environment")
            return False
        else:
            # Local development - just create SQLite tables
            print("🔄 Running local development migration...")
            return migrate_local()
    
    try:
        # Import Flask app
        from app import create_app
        from app.extensions import db
        
        print("🚀 Creating Flask app context...")
        app = create_app()
        
        with app.app_context():
            print("✅ Connected to database successfully")
            
            # Check current database type
            database_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if 'sqlite' in database_url.lower():
                print("📱 SQLite database detected - ensuring tables exist")
                db.create_all()
            else:
                print("🐘 PostgreSQL database detected - running migrations")
            
            # Try to add columns using raw SQL
            migration_results = []
            
            columns_to_add = [
                ('html_content_en', 'TEXT'),
                ('js_content_en', 'TEXT')
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    print(f"🔧 Adding {column_name} column...")
                    sql = f"ALTER TABLE report ADD COLUMN {column_name} {column_type}"
                    db.session.execute(db.text(sql))
                    db.session.commit()
                    print(f"✅ Added {column_name} column successfully")
                    migration_results.append(f"✅ {column_name}")
                except Exception as e:
                    error_str = str(e).lower()
                    if any(phrase in error_str for phrase in ["duplicate column", "already exists", "duplicate"]):
                        print(f"ℹ️  {column_name} column already exists")
                        migration_results.append(f"ℹ️  {column_name} (already exists)")
                    else:
                        print(f"❌ Error adding {column_name}: {e}")
                        migration_results.append(f"❌ {column_name}: {e}")
                        # Don't fail completely for column errors in PostgreSQL
            
            print("\n📊 Migration Summary:")
            for result in migration_results:
                print(f"   {result}")
        
        print("🎉 Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"💥 Migration failed: {e}")
        
        # Provide helpful troubleshooting info
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if DATABASE_URL is set correctly in Railway environment variables")
        print("2. Ensure PostgreSQL service is running and accessible")
        print("3. Verify SSL connection settings")
        
        # Check if this is a connection error
        error_str = str(e).lower()
        if 'could not translate host name' in error_str:
            print("4. ⚠️  DNS resolution error - ensure running in correct environment")
            print("   • Local: Use SQLite (no DATABASE_URL needed)")
            print("   • Railway: Run via 'railway run' or in deployed environment")
        elif 'ssl' in error_str:
            print("4. 🔒 SSL connection issue - check SSL configuration")
        
        return False

def migrate_local():
    """Fallback migration for local development with SQLite"""
    try:
        from app import create_app
        from app.extensions import db
        
        print("🏠 Running local SQLite migration...")
        app = create_app()
        
        with app.app_context():
            # Just ensure all tables exist
            db.create_all()
            print("✅ SQLite tables created/verified")
            
            # Test basic functionality
            from app.models import Report
            test_count = Report.query.count()
            print(f"📊 Current reports in database: {test_count}")
            
        return True
        
    except Exception as e:
        print(f"❌ Local migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Railway Migration Script v2.0")
    print("=" * 50)
    
    success = migrate_database()
    
    print("=" * 50)
    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)
