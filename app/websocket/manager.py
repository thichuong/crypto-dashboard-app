"""
WebSocket Server for Real-time Updates
Handles all real-time communication between server and clients
"""
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import uuid
import json
import threading
import time
from datetime import datetime

class WebSocketManager:
    def __init__(self, app=None, redis_client=None):
        self.socketio = None
        self.app = app
        self.redis_client = redis_client
        self.active_connections = {}
        self.room_subscribers = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize SocketIO with Flask app"""
        self.app = app
        self.socketio = SocketIO(
            app, 
            cors_allowed_origins="*",
            async_mode='threading',
            logger=True,
            engineio_logger=True
        )
        
        # Register event handlers
        self.register_handlers()
        
        # Start background tasks
        self.start_background_tasks()
    
    def register_handlers(self):
        """Register all WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            client_id = str(uuid.uuid4())
            session_id = request.sid
            
            # Store connection info
            self.active_connections[session_id] = {
                'client_id': client_id,
                'connected_at': datetime.now(),
                'last_ping': datetime.now(),
                'subscriptions': set()
            }
            
            print(f"[WebSocket] Client connected: {client_id} (Session: {session_id})")
            
            # Send welcome message
            emit('connected', {
                'client_id': client_id,
                'server_time': datetime.now().isoformat(),
                'message': 'Connected to Crypto Dashboard WebSocket'
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            session_id = request.sid
            if session_id in self.active_connections:
                client_info = self.active_connections[session_id]
                print(f"[WebSocket] Client disconnected: {client_info['client_id']}")
                
                # Leave all rooms
                for subscription in client_info['subscriptions']:
                    leave_room(subscription)
                    if subscription in self.room_subscribers:
                        self.room_subscribers[subscription].discard(session_id)
                
                # Remove from active connections
                del self.active_connections[session_id]
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Subscribe to specific data channels"""
            session_id = request.sid
            channel = data.get('channel')
            
            if not channel:
                emit('error', {'message': 'Channel is required'})
                return
            
            # Join room
            join_room(channel)
            
            # Track subscription
            if session_id in self.active_connections:
                self.active_connections[session_id]['subscriptions'].add(channel)
            
            if channel not in self.room_subscribers:
                self.room_subscribers[channel] = set()
            self.room_subscribers[channel].add(session_id)
            
            print(f"[WebSocket] Client {session_id} subscribed to {channel}")
            
            emit('subscribed', {
                'channel': channel,
                'message': f'Successfully subscribed to {channel}'
            })
        
        @self.socketio.on('unsubscribe')
        def handle_unsubscribe(data):
            """Unsubscribe from specific data channels"""
            session_id = request.sid
            channel = data.get('channel')
            
            if not channel:
                emit('error', {'message': 'Channel is required'})
                return
            
            # Leave room
            leave_room(channel)
            
            # Remove subscription tracking
            if session_id in self.active_connections:
                self.active_connections[session_id]['subscriptions'].discard(channel)
            
            if channel in self.room_subscribers:
                self.room_subscribers[channel].discard(session_id)
            
            print(f"[WebSocket] Client {session_id} unsubscribed from {channel}")
            
            emit('unsubscribed', {
                'channel': channel,
                'message': f'Successfully unsubscribed from {channel}'
            })
        
        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping for connection keepalive"""
            session_id = request.sid
            if session_id in self.active_connections:
                self.active_connections[session_id]['last_ping'] = datetime.now()
            
            emit('pong', {'timestamp': datetime.now().isoformat()})
    
    def broadcast_to_channel(self, channel, event_type, data):
        """Broadcast data to all subscribers of a channel"""
        if channel in self.room_subscribers and self.room_subscribers[channel]:
            self.socketio.emit(event_type, data, room=channel)
            print(f"[WebSocket] Broadcasted {event_type} to {channel} ({len(self.room_subscribers[channel])} clients)")
    
    def broadcast_status_update(self, status_data):
        """Broadcast system status updates"""
        self.broadcast_to_channel('system_status', 'status_update', {
            'timestamp': datetime.now().isoformat(),
            'data': status_data
        })
    
    def broadcast_progress_update(self, session_id, progress_data):
        """Broadcast progress updates for specific session"""
        self.broadcast_to_channel(f'progress_{session_id}', 'progress_update', {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'data': progress_data
        })
    
    def broadcast_report_completed(self, report_data):
        """Broadcast when new report is completed"""
        self.broadcast_to_channel('reports', 'report_completed', {
            'timestamp': datetime.now().isoformat(),
            'data': report_data
        })
    
    def start_background_tasks(self):
        """Start background tasks for cleanup and heartbeat"""
        def cleanup_stale_connections():
            """Remove stale connections every 60 seconds"""
            while True:
                time.sleep(60)
                current_time = datetime.now()
                stale_connections = []
                
                for session_id, conn_info in self.active_connections.items():
                    time_diff = (current_time - conn_info['last_ping']).total_seconds()
                    if time_diff > 120:  # 2 minutes timeout
                        stale_connections.append(session_id)
                
                for session_id in stale_connections:
                    if session_id in self.active_connections:
                        print(f"[WebSocket] Removing stale connection: {session_id}")
                        del self.active_connections[session_id]
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=cleanup_stale_connections, daemon=True)
        cleanup_thread.start()
    
    def get_connection_stats(self):
        """Get current connection statistics"""
        return {
            'total_connections': len(self.active_connections),
            'channels': {
                channel: len(subscribers) 
                for channel, subscribers in self.room_subscribers.items()
            },
            'connections': [
                {
                    'session_id': session_id,
                    'client_id': info['client_id'],
                    'connected_at': info['connected_at'].isoformat(),
                    'subscriptions': list(info['subscriptions'])
                }
                for session_id, info in self.active_connections.items()
            ]
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
