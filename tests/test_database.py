#!/usr/bin/env python3
"""
Test to verify database Report model and translation columns.

This test creates an in-memory SQLite database, ensures the `Report` model
contains `html_content_en` and `js_content_en`, inserts a sample record,
reads it back, and then cleans up.
"""
import sys
import os

# Ensure project root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from app.extensions import db
from app.models import CryptoReport as Report


def test_database_report_model():
    print("🧪 Testing database Report model and translation columns")

    app = Flask(__name__)
    # Use in-memory SQLite so test is isolated and does not touch local_dev.db
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize db with the test app
    db.init_app(app)

    with app.app_context():
        # Create tables
        db.create_all()

        # Model should expose the translation columns
        assert hasattr(Report, 'html_content_en'), "Report model missing html_content_en"
        assert hasattr(Report, 'js_content_en'), "Report model missing js_content_en"

        # Insert a sample report
        sample = Report(
            html_content='<p>Tiếng Việt</p>',
            js_content="console.log('vi');",
            html_content_en='<p>English</p>',
            js_content_en="console.log('en');",
        )
        db.session.add(sample)
        db.session.commit()

    print(f"Inserted Report id={sample.id}")

    # Fetch and validate using latest report query
    latest_report = Report.query.order_by(Report.created_at.desc()).first()
    assert latest_report is not None, "Failed to fetch latest Report"
    assert latest_report.html_content_en == '<p>English</p>'
    assert latest_report.js_content_en == "console.log('en');"

    # Cleanup
    db.session.delete(latest_report)
    db.session.commit()

    print("✅ Database Report model test passed")
    return True


if __name__ == '__main__':
    ok = test_database_report_model()
    sys.exit(0 if ok else 1)
