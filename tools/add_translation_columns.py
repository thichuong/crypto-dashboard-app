#!/usr/bin/env python3
"""
Migration script để thêm cột html_content_en và js_content_en vào bảng Report
"""

import os
import sys

# Thêm đường dẫn để import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text


def add_translation_columns():
    """Thêm cột dịch vào bảng Report"""
    app = create_app()
    
    with app.app_context():
        try:
            # Kiểm tra xem cột đã tồn tại chưa
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='crypto_report' AND column_name IN ('html_content_en', 'js_content_en')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Thêm cột html_content_en nếu chưa có
            if 'html_content_en' not in existing_columns:
                print("Thêm cột html_content_en...")
                db.session.execute(text("""
                    ALTER TABLE crypto_report ADD COLUMN html_content_en TEXT
                """))
                print("✓ Đã thêm cột html_content_en")
            else:
                print("✓ Cột html_content_en đã tồn tại")
            
            # Thêm cột js_content_en nếu chưa có
            if 'js_content_en' not in existing_columns:
                print("Thêm cột js_content_en...")
                db.session.execute(text("""
                    ALTER TABLE crypto_report ADD COLUMN js_content_en TEXT
                """))
                print("✓ Đã thêm cột js_content_en")
            else:
                print("✓ Cột js_content_en đã tồn tại")
            
            db.session.commit()
            print("✅ Migration hoàn thành thành công!")
            
        except Exception as e:
            print(f"❌ Lỗi migration: {e}")
            db.session.rollback()
            sys.exit(1)


if __name__ == "__main__":
    add_translation_columns()
