# run.py
from app import create_app
from app.websocket.manager import websocket_manager
import os

# Gọi hàm create_app để tạo một instance của ứng dụng Flask
app = create_app()

if __name__ == '__main__':
    # Railway configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8080))
    
    # Enable debug mode only for local development
    debug_mode = os.environ.get('RAILWAY_ENVIRONMENT') != 'production'
    
    # Chạy ứng dụng với SocketIO support
    # Disable the Flask reloader when using SocketIO; the reloader can cause
    # Werkzeug to attempt writes before start_response which raises
    # "write() before start_response" in some setups.
    websocket_manager.socketio.run(
        app,
        host=host,
        port=port,
        debug=debug_mode,
        use_reloader=False
    )