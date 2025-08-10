# app/error_handlers.py

from flask import request, jsonify, render_template


def register_error_handlers(app):
    """
    Đăng ký các error handlers cho ứng dụng Flask.
    """
    
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found', 'status': 404}), 404
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def handle_500(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error', 'status': 500}), 500
        return render_template('index.html'), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Chỉ log lỗi, không expose chi tiết cho client
        app.logger.error(f'Unhandled exception: {e}', exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({'error': 'An unexpected error occurred', 'status': 500}), 500
        return render_template('index.html'), 500
