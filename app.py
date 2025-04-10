from flask import Flask, render_template, request, jsonify, make_response
import pymongo
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import time
import urllib.parse
import jinja2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app with explicit template folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)

# Database configuration
username = "mdsaif123"
password = "22494008"
cluster = "iotusingrelay.vfu72n2.mongodb.net"
encoded_username = urllib.parse.quote_plus(username)
encoded_password = urllib.parse.quote_plus(password)

# Construct MongoDB URI with explicit options
MONGO_URI = f"mongodb+srv://{encoded_username}:{encoded_password}@{cluster}/?retryWrites=true&w=majority&ssl=true&tlsAllowInvalidCertificates=true"
DB_NAME = "test"
COLLECTION_NAME = "devices"

logger.info(f"Connecting to database: {DB_NAME}, collection: {COLLECTION_NAME}")

# Define the LED configuration
LED_CONFIG = [
    {"name": "LED 1", "pin": 17, "device_type": "led 1"},
    {"name": "LED 2", "pin": 27, "device_type": "led 2"},
    {"name": "LED 3", "pin": 22, "device_type": "led 3"},
    {"name": "LED 4", "pin": 18, "device_type": "led 4"}
]

def get_db():
    """Get database connection with retry mechanism"""
    for attempt in range(3):
        try:
            logger.info(f"Attempting to connect to MongoDB (attempt {attempt + 1}/3)...")
            # Create MongoDB client with options
            mongo_client = pymongo.MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=1,
                retryWrites=True,
                retryReads=True
            )
            
            # Test the connection explicitly
            mongo_client.admin.command('ping')
            logger.info("MongoDB ping successful!")
            
            database = mongo_client[DB_NAME]
            collection = database[COLLECTION_NAME]
            
            # Test collection access
            collection.find_one()
            logger.info("Successfully connected to collection!")
            
            return collection
            
        except Exception as e:
            logger.error(f"MongoDB connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < 2:  # Only sleep if we're going to retry
                time.sleep(1)
    
    logger.error("All MongoDB connection attempts failed")
    return None

def render_template_safe(*args, **kwargs):
    """Safely render template with error handling"""
    try:
        return render_template(*args, **kwargs)
    except jinja2.TemplateNotFound:
        logger.error(f"Template not found: {args[0]}")
        return f"Error: Template {args[0]} not found", 500
    except Exception as e:
        logger.error(f"Template rendering error: {str(e)}")
        return "Internal server error", 500

@app.route('/')
def index():
    """Render the main control page"""
    try:
        device_collection = get_db()
        if device_collection is None:
            error_msg = "Database connection failed. Please check MongoDB connection and try again."
            logger.error(error_msg)
            return render_template_safe('index.html', 
                                     devices=[], 
                                     error=error_msg)
        
        devices = list(device_collection.find())
        logger.info(f"Successfully retrieved {len(devices)} devices")
        
        response = make_response(render_template_safe('index.html', 
                                                    devices=devices,
                                                    error=None))
        response.headers.update({
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block'
        })
        return response
        
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        logger.error(error_msg)
        return render_template_safe('index.html', 
                                 devices=[], 
                                 error=error_msg)

@app.after_request
def add_header(response):
    # Add caching headers for static content
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    else:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """API endpoint to get all devices"""
    try:
        device_collection = get_db()
        if device_collection is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        devices = list(device_collection.find())
        # Convert ObjectId to string for JSON serialization
        for device in devices:
            device['_id'] = str(device['_id'])
        return jsonify(devices)
    except Exception as e:
        logger.error(f"Error in get_devices: {str(e)}")
        return jsonify({"error": "Failed to retrieve devices"}), 500

@app.route('/api/toggle/<device_id>', methods=['POST'])
def toggle_device(device_id):
    """Toggle the state of an LED"""
    try:
        device_collection = get_db()
        if device_collection is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Find the device
        device = device_collection.find_one({"_id": ObjectId(device_id)})
        if not device:
            return jsonify({"error": "Device not found"}), 404
            
        # Toggle the state
        current_state = device.get("state", False)
        new_state = not current_state
        
        # Update the database
        device_collection.update_one(
            {"_id": ObjectId(device_id)},
            {"$set": {"state": new_state}}
        )
        
        return jsonify({"success": True, "device_id": device_id, "state": new_state})
    except Exception as e:
        logger.error(f"Error in toggle_device: {str(e)}")
        return jsonify({"error": "Failed to toggle device"}), 500

@app.route('/api/update/<device_id>', methods=['POST'])
def update_device(device_id):
    """Update the state of an LED to a specific value"""
    try:
        device_collection = get_db()
        if device_collection is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        data = request.json
        new_state = data.get('state', False)
        
        # Update the database
        device_collection.update_one(
            {"_id": ObjectId(device_id)},
            {"$set": {"state": new_state}}
        )
        
        return jsonify({"success": True, "device_id": device_id, "state": new_state})
    except Exception as e:
        logger.error(f"Error in update_device: {str(e)}")
        return jsonify({"error": "Failed to update device"}), 500

@app.route('/api/update-all-names', methods=['GET'])
def update_all_names():
    """Update all device names to ensure they are LED 1, LED 2, etc."""
    try:
        device_collection = get_db()
        if device_collection is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Get all devices
        devices = list(device_collection.find())
        
        # Match devices with LED_CONFIG by pin number and update names
        updated_count = 0
        for device in devices:
            pin = device.get('pin')
            for led_config in LED_CONFIG:
                if led_config['pin'] == pin:
                    # Update name and device_type if needed
                    if device.get('name') != led_config['name'] or device.get('device_type') != led_config['device_type']:
                        device_collection.update_one(
                            {"_id": device['_id']},
                            {"$set": {
                                "name": led_config['name'],
                                "device_type": led_config['device_type']
                            }}
                        )
                        updated_count += 1
                    break
        
        return jsonify({"success": True, "updated_count": updated_count})
    except Exception as e:
        logger.error(f"Error in update_all_names: {str(e)}")
        return jsonify({"error": "Failed to update device names"}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        device_collection = get_db()
        if device_collection is None:
            return jsonify({
                "status": "error",
                "message": "Database connection failed",
                "mongo_uri": MONGO_URI.replace(MONGO_URI.split('@')[0], '***')  # Hide credentials
            }), 500
        
        # Test database operations
        count = device_collection.count_documents({})
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "device_count": count,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# This is required for Vercel
app = app

if __name__ == '__main__':
    # Only attempt to initialize database if connection was successful
    device_collection = get_db()
    if device_collection is not None:
        # Check if devices exist in the collection, create them if not
        if device_collection.count_documents({}) == 0:
            # Create the 4 LED devices
            for led in LED_CONFIG:
                device_collection.insert_one({
                    "name": led["name"],
                    "pin": led["pin"],
                    "device_type": led["device_type"],
                    "state": False
                })
            print("Created LED devices in database")
        else:
            # Verify all devices have correct names and update if necessary
            devices = list(device_collection.find())
            update_needed = False
            
            # Check if we have exactly 4 devices with correct names
            if len(devices) != 4:
                update_needed = True
            else:
                # Check device names and types
                device_pins = [device.get('pin') for device in devices]
                for led in LED_CONFIG:
                    if led['pin'] not in device_pins:
                        update_needed = True
                        break
                        
                    # Verify correct names
                    for device in devices:
                        if device.get('pin') == led['pin'] and (device.get('name') != led['name'] or device.get('device_type') != led['device_type']):
                            update_needed = True
                            break
            
            if update_needed:
                # Clear and recreate all devices
                device_collection.delete_many({})
                for led in LED_CONFIG:
                    device_collection.insert_one({
                        "name": led["name"],
                        "pin": led["pin"],
                        "device_type": led["device_type"],
                        "state": False
                    })
                print("Reset LED devices in database")
            else:
                print("LED devices already exist with correct configuration")
        
        # Update any devices with old names on startup
        devices = list(device_collection.find())
        updated = 0
        for device in devices:
            pin = device.get('pin')
            for led_config in LED_CONFIG:
                if led_config['pin'] == pin and (device.get('name') != led_config['name'] or device.get('device_type') != led_config['device_type']):
                    device_collection.update_one(
                        {"_id": device['_id']},
                        {"$set": {
                            "name": led_config['name'],
                            "device_type": led_config['device_type']
                        }}
                    )
                    updated += 1
                    break
        
        if updated > 0:
            print(f"Updated {updated} device names to LED format")
    else:
        print("WARNING: Starting app without database connection. App will run in limited mode.")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 