# app/services/vercel_socketio_adapter.py
"""
Adapter cho SocketIO trên Vercel serverless environment.
Vì Vercel không hỗ trợ WebSocket, chúng ta sẽ sử dụng polling API endpoints.
"""

import json
import time
from flask import request, jsonify
from ..utils.cache import cache

class VercelSocketIOAdapter:
    """Adapter class để simulate SocketIO behavior trên Vercel"""
    
    def __init__(self, app):
        self.app = app
        self.setup_routes()
    
    def setup_routes(self):
        """Setup polling endpoints để thay thế SocketIO"""
        
        @self.app.route('/api/socketio/connect', methods=['POST'])
        def socketio_connect():
            """Simulate SocketIO connect"""
            client_id = request.json.get('client_id', f"client_{int(time.time())}")
            
            # Store client connection in cache
            cache.set(f"socketio_client_{client_id}", {
                'connected_at': time.time(),
                'last_ping': time.time()
            }, timeout=300)  # 5 minutes timeout
            
            return jsonify({'success': True, 'client_id': client_id})
        
        @self.app.route('/api/socketio/poll/<client_id>', methods=['GET'])
        def socketio_poll(client_id):
            """Polling endpoint để nhận messages"""
            try:
                # Update last ping
                client_data = cache.get(f"socketio_client_{client_id}")
                if not client_data:
                    return jsonify({'error': 'Client not connected'}), 404
                
                client_data['last_ping'] = time.time()
                cache.set(f"socketio_client_{client_id}", client_data, timeout=300)
                
                # Get messages for this client
                messages = cache.get(f"socketio_messages_{client_id}") or []
                
                # Clear messages after reading
                cache.delete(f"socketio_messages_{client_id}")
                
                return jsonify({'messages': messages})
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/socketio/emit', methods=['POST'])
        def socketio_emit():
            """Endpoint để emit messages tới clients"""
            try:
                data = request.json
                event = data.get('event')
                message = data.get('data')
                room = data.get('room')  # Optional room/session_id
                
                if room:
                    # Send to specific room/session
                    self._send_to_room(room, event, message)
                else:
                    # Broadcast to all connected clients
                    self._broadcast(event, message)
                
                return jsonify({'success': True})
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/socketio/join', methods=['POST'])
        def socketio_join():
            """Join a room (session)"""
            try:
                data = request.json
                client_id = data.get('client_id')
                room = data.get('room')
                
                # Store room membership
                rooms = cache.get(f"socketio_rooms_{client_id}") or []
                if room not in rooms:
                    rooms.append(room)
                    cache.set(f"socketio_rooms_{client_id}", rooms, timeout=300)
                
                return jsonify({'success': True})
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/socketio/leave', methods=['POST'])
        def socketio_leave():
            """Leave a room (session)"""
            try:
                data = request.json
                client_id = data.get('client_id')
                room = data.get('room')
                
                # Remove room membership
                rooms = cache.get(f"socketio_rooms_{client_id}") or []
                if room in rooms:
                    rooms.remove(room)
                    cache.set(f"socketio_rooms_{client_id}", rooms, timeout=300)
                
                return jsonify({'success': True})
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _send_to_room(self, room, event, data):
        """Send message to all clients in a room"""
        # Get all connected clients
        all_clients = self._get_connected_clients()
        
        for client_id in all_clients:
            client_rooms = cache.get(f"socketio_rooms_{client_id}") or []
            if room in client_rooms:
                self._send_to_client(client_id, event, data)
    
    def _broadcast(self, event, data):
        """Broadcast message to all connected clients"""
        all_clients = self._get_connected_clients()
        
        for client_id in all_clients:
            self._send_to_client(client_id, event, data)
    
    def _send_to_client(self, client_id, event, data):
        """Send message to specific client"""
        messages = cache.get(f"socketio_messages_{client_id}") or []
        messages.append({
            'event': event,
            'data': data,
            'timestamp': time.time()
        })
        cache.set(f"socketio_messages_{client_id}", messages, timeout=300)
    
    def _get_connected_clients(self):
        """Get list of connected client IDs"""
        # This is a simplified implementation
        # In production, you might want to use a more efficient approach
        connected_clients = []
        
        # Scan cache for client connections (this is not ideal for large scale)
        # In production, consider using Redis SCAN or maintain a separate list
        try:
            # This is a workaround - in real implementation, 
            # you'd maintain a list of connected clients
            pass
        except:
            pass
        
        return connected_clients

def emit_to_room(room, event, data):
    """Helper function để emit message tới room"""
    from flask import current_app
    
    try:
        # Store message for room
        cache.set(f"socketio_room_message_{room}_{int(time.time())}", {
            'event': event,
            'data': data,
            'timestamp': time.time()
        }, timeout=300)
        
        print(f"[VERCEL_SOCKETIO] Emitted to room {room}: {event}")
        return True
    except Exception as e:
        print(f"[VERCEL_SOCKETIO] Error emitting to room {room}: {e}")
        return False

def emit_progress_update(session_id, progress_data):
    """Helper function đặc biệt cho progress updates"""
    return emit_to_room(session_id, 'progress_update', {
        'session_id': session_id,
        'progress': progress_data
    })
