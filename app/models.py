# app/models.py

from .extensions import db
from datetime import datetime, timezone

class Report(db.Model):
    """
    Model để lưu trữ nội dung báo cáo được tạo ra bởi AI.
    """
    id = db.Column(db.Integer, primary_key=True)
    html_content = db.Column(db.Text, nullable=False)
    css_content = db.Column(db.Text, nullable=True)
    js_content = db.Column(db.Text, nullable=True)
    html_content_en = db.Column(db.Text, nullable=True)  # Nội dung HTML đã dịch sang tiếng Anh
    js_content_en = db.Column(db.Text, nullable=True)    # Nội dung JS đã dịch sang tiếng Anh
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Report {self.id}>'