#!/usr/bin/env python3
"""
Database migration và setup script cho Railway deployment
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Report


def setup_database():
    """Setup database tables"""
    print("🔧 Setting up database...")
    
    try:
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Test basic operations
        print("🧪 Testing basic operations...")
        
        # Test insert
        test_report = Report(
            html_content="<div>Setup Test</div>",
            css_content="/* setup test */", 
            js_content="// setup test"
        )
        db.session.add(test_report)
        db.session.commit()
        
        # Test query
        found = Report.query.get(test_report.id)
        if found:
            print(f"✅ Test report created with ID: {found.id}")
            
            # Cleanup test data
            db.session.delete(found)
            db.session.commit()
            print("✅ Test data cleaned up")
        else:
            print("❌ Test report not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False


def check_existing_data():
    """Check existing data in database"""
    print("📊 Checking existing data...")
    
    try:
        report_count = Report.query.count()
        print(f"📈 Found {report_count} existing reports")
        
        if report_count > 0:
            latest = Report.query.order_by(Report.created_at.desc()).first()
            print(f"📅 Latest report: {latest.created_at}")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to check existing data: {e}")
        return False


def main():
    """Main migration function"""
    print("🚀 Starting Database Migration...")
    
    try:
        # Create Flask app
        app = create_app()
        
        with app.app_context():
            # Check existing data first
            if not check_existing_data():
                print("⚠️ Warning: Could not check existing data")
            
            # Setup database
            if setup_database():
                print("\n✅ Database migration completed successfully")
                return 0
            else:
                print("\n❌ Database migration failed")
                return 1
                
    except Exception as e:
        print(f"\n💥 Critical Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
