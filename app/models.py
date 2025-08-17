# app/models.py

from .extensions import db
from datetime import datetime, timezone

class CryptoReport(db.Model):
    """
    Model để lưu trữ nội dung báo cáo được tạo ra bởi AI.
    Renamed from `Report` to `CryptoReport` but keep the original
    table name (`report`) via __tablename__ to avoid migrating DB tables.
    """
    __tablename__ = 'crypto_report'
    id = db.Column(db.Integer, primary_key=True)
    html_content = db.Column(db.Text, nullable=False)
    css_content = db.Column(db.Text, nullable=True)
    js_content = db.Column(db.Text, nullable=True)
    html_content_en = db.Column(db.Text, nullable=True)  # Nội dung HTML đã dịch sang tiếng Anh
    js_content_en = db.Column(db.Text, nullable=True)    # Nội dung JS đã dịch sang tiếng Anh
    # store timezone-aware UTC timestamps (maps to TIMESTAMPTZ in Postgres)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<CryptoReport {self.id}>'