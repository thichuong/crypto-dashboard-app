#!/usr/bin/env python3
"""
Railway Database Connection Checker
Debug tool để kiểm tra kết nối database trên Railway
"""

import os
import sys
import urllib.parse

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_environment_variables():
    """Kiểm tra các biến môi trường"""
    print("🔍 Environment Variables Check:")
    print("=" * 40)
    
    env_vars = [
        'RAILWAY_ENVIRONMENT',
        'DATABASE_URL', 
        'POSTGRES_URL',
        'PORT',
        'FLASK_ENV'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'URL' in var and 'postgres' in value:
                # Hide password for security, show structure
                try:
                    parsed = urllib.parse.urlparse(value)
                    safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port}{parsed.path}"
                    print(f"   {var}: {safe_url}")
                except:
                    print(f"   {var}: [PROTECTED URL]")
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: ❌ NOT SET")
    
    print()

def test_database_connection():
    """Test kết nối database"""
    print("🔌 Database Connection Test:")
    print("=" * 40)
    
    try:
        # Import Flask app
        from app import create_app
        from app.extensions import db
        
        print("📱 Creating Flask app...")
        app = create_app()
        
        with app.app_context():
            print("✅ Flask app created successfully")
            
            # Get database info
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
            print(f"📊 Database URI configured: {'✅ Yes' if db_uri != 'Not configured' else '❌ No'}")
            
            if 'sqlite' in db_uri.lower():
                print("💾 Database type: SQLite (Local)")
            elif 'postgresql' in db_uri.lower():
                print("🐘 Database type: PostgreSQL (Production)")
                
                # Show connection details safely
                try:
                    parsed = urllib.parse.urlparse(db_uri)
                    print(f"🌐 Host: {parsed.hostname}")
                    print(f"🚪 Port: {parsed.port}")
                    print(f"🗄️  Database: {parsed.path.lstrip('/')}")
                except Exception as e:
                    print(f"⚠️  Could not parse DB URI: {e}")
            
            # Test actual connection
            print("\n🧪 Testing database connection...")
            try:
                # Try to execute a simple query
                result = db.session.execute(db.text("SELECT 1 as test"))
                test_value = result.scalar()
                if test_value == 1:
                    print("✅ Database connection successful!")
                else:
                    print("❌ Database connection failed - unexpected result")
                    return False
                    
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                print("\n🔧 Troubleshooting suggestions:")
                
                error_str = str(e).lower()
                if 'could not translate host name' in error_str:
                    print("   • DNS resolution error - check if running in correct environment")
                    print("   • Railway internal hostnames only work within Railway network")
                    print("   • For local testing, use SQLite or Railway CLI proxy")
                elif 'ssl' in error_str:
                    print("   • SSL connection issue - check SSL configuration")
                elif 'timeout' in error_str:
                    print("   • Connection timeout - check network connectivity")
                elif 'authentication' in error_str or 'password' in error_str:
                    print("   • Authentication failed - check credentials")
                else:
                    print(f"   • General database error: {e}")
                
                return False
            
            # Test tables if connection works
            print("\n📋 Checking database tables...")
            try:
                from app.models import Report
                
                # Check if Report table exists and get count
                report_count = Report.query.count()
                print(f"📊 Reports in database: {report_count}")
                
                # Check table structure
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"🗃️  Tables found: {', '.join(tables)}")
                
                if 'report' in tables:
                    columns = inspector.get_columns('report')
                    column_names = [col['name'] for col in columns]
                    print(f"📝 Report table columns: {', '.join(column_names)}")
                    
                    # Check for translation columns
                    if 'html_content_en' in column_names:
                        print("✅ Translation columns found")
                    else:
                        print("⚠️  Translation columns missing - migration needed")
                
            except Exception as e:
                print(f"⚠️  Could not check tables: {e}")
        
        return True
        
    except Exception as e:
        print(f"💥 Failed to create Flask app: {e}")
        return False

def main():
    """Main function"""
    print("🏥 Railway Database Health Check")
    print("=" * 50)
    
    # Check environment
    check_environment_variables()
    
    # Test database
    success = test_database_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Health check completed successfully!")
        return 0
    else:
        print("❌ Health check failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
