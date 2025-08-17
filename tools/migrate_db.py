#!/usr/bin/env python3
import sys
import os
from datetime import datetime, timezone

# Ensure app package is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import CryptoReport as Report


def setup_database():
    #!/usr/bin/env python3
    """Database migration and setup script for Railway deployment.

    This script creates tables (using SQLAlchemy's create_all) and performs a
    small test insert to verify connectivity. It sets the test report's
    `created_at` explicitly to UTC to match the updated model.
    """
    import sys
    import os
    from datetime import datetime, timezone

    # Ensure app package is importable
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from app import create_app
    from app.extensions import db
    from app.models import CryptoReport as Report


    def setup_database():
        """Create tables and run a quick test insert/delete."""
        print("🔧 Setting up database...")

        try:
            # Create all tables defined by SQLAlchemy models
            db.create_all()
            print("✅ Database tables created successfully")

            # Test basic operations
            print("🧪 Testing basic operations...")

            # Create a test report with timezone-aware created_at
            test_report = Report(
                html_content="<div>Setup Test</div>",
                css_content="/* setup test */",
                js_content="// setup test",
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(test_report)
            db.session.commit()

            # Verify it exists
            found = Report.query.get(test_report.id)
            if found:
                print(f"✅ Test report created with ID: {found.id}")

                # Cleanup the test data
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
            except Exception:
                pass
            return False


    def check_existing_data():
        """Report basic stats about existing data."""
        print("📊 Checking existing data...")

        try:
            report_count = Report.query.count()
            print(f"📈 Found {report_count} existing reports")

            if report_count > 0:
                latest = Report.query.order_by(Report.created_at.desc()).first()
                tzinfo = getattr(latest.created_at, "tzinfo", None)
                print(f"📅 Latest report: {latest.created_at} (tzinfo={tzinfo})")

            return True

        except Exception as e:
            print(f"❌ Failed to check existing data: {e}")
            return False


    def main():
        """Main entrypoint for the migration script."""
        print("🚀 Starting Database Migration...")

        try:
            app = create_app()

            with app.app_context():
                if not check_existing_data():
                    print("⚠️ Warning: Could not check existing data")

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

