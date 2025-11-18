from flask import Flask, request, jsonify
import logging
import sys
import os
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import jwt
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from score_crop import CropRecommendationModel

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://"
)

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip()
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '').strip()
JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback-secret-key').strip()

print("🌾 Crop Recommendation API Starting...")
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY loaded: {bool(SUPABASE_KEY)}")

# Initialize crop model
crop_model = CropRecommendationModel()
init_success = crop_model.init()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase Helper Functions
def supabase_request(endpoint, method='GET', data=None):
    """Make request to Supabase REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    logger.info(f"Making {method} request to: {url}")
    if data:
        logger.info(f" Request data: {data}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code >= 400:
            logger.error(f"❌ API Error {response.status_code}: {response.text}")
            return None
        
        # Handle empty response
        if response.status_code == 204 or not response.text.strip():
            logger.info("Empty response (204 No Content)")
            return []
            
        result = response.json()
        logger.info(f"Response data: {result}")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request error: {e}")
        return None


def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except:
        return None

def save_crop_recommendation(user_id, input_data, result):
    """Save crop recommendation to Supabase"""
    try:
        endpoint = "crop_recommendations"
        data = {
            'user_id': user_id,
            'nitrogen': input_data['nitrogen'],
            'phosphorus': input_data['phosphorus'],
            'potassium': input_data['potassium'],
            'temperature': input_data['temperature'],
            'humidity': input_data['humidity'],
            'ph_level': input_data['ph'],
            'rainfall': input_data['rainfall'],
            'recommended_crop': result['crop'],
            'suitability_level': result['suitability'],
            'match_percentage': result['confidence'] * 100,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f" Attempting to save crop recommendation for user {user_id}")
        logger.info(f" Data to save: {data}")
        
        response = supabase_request(endpoint, 'POST', data)
        
        if response:
            logger.info(f"Successfully saved crop recommendation: {response}")
            return True
        else:
            logger.error("❌ Failed to save crop recommendation - API returned None")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error saving crop recommendation: {e}")
        return False

def require_auth(f):
    """Decorator to protect routes with JWT authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization token provided'}), 401
        
        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = verify_token(token)
            
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            request.user_id = payload['user_id']
            request.user_email = payload['email']
            
        except Exception as e:
            return jsonify({'error': 'Invalid authorization header'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/')
def home():
    return jsonify({
        "message": "Crop Recommendation API 🌾",
        "status": "running",
        "model_loaded": init_success,
        "supabase_connected": bool(SUPABASE_URL and SUPABASE_KEY)
    })

@app.route('/health', methods=['GET'])
def health_check():
    # Test Supabase connection
    supabase_status = False
    try:
        test_response = supabase_request("crop_recommendations?select=count&limit=1")
        supabase_status = test_response is not None
    except:
        pass
    
    return jsonify({
        "status": "healthy",
        "model_initialized": init_success,
        "supabase_connected": supabase_status
    })

@app.route('/recommend', methods=['POST'])
@require_auth
@limiter.limit("30 per hour")
def recommend_crop():
    try:
        if not init_success:
            return jsonify({"error": "Crop model not initialized"}), 500
        
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Required parameters 
        required_params = [
            'nitrogen', 'phosphorus', 'potassium', 
            'temperature', 'humidity', 'ph', 'rainfall'
        ]
        
        # Check if all required parameters are present
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"Missing parameter: {param}"}), 400
        
        # Prepare input data
        input_data = {
            'nitrogen': float(data['nitrogen']),
            'phosphorus': float(data['phosphorus']),
            'potassium': float(data['potassium']),
            'temperature': float(data['temperature']),
            'humidity': float(data['humidity']),
            'ph': float(data['ph']),
            'rainfall': float(data['rainfall'])
        }
        
        # Validate ranges
        if not (0 <= input_data['humidity'] <= 100):
            return jsonify({"error": "Humidity must be between 0 and 100"}), 400
        
        if not (0 <= input_data['ph'] <= 14):
            return jsonify({"error": "pH must be between 0 and 14"}), 400
        
        logger.info(f"Received input from user {request.user_id}: {input_data}")
        
        # Get prediction
        result = crop_model.run(input_data)
        
        # Save to Supabase
        save_result = save_crop_recommendation(request.user_id, input_data, result)
        
        if save_result:
            logger.info(f" Crop recommendation saved to Supabase for user {request.user_id}")
            result['saved_to_database'] = True
        else:
            logger.warning(f"⚠️ Failed to save crop recommendation to Supabase for user {request.user_id}")
            result['saved_to_database'] = False
        
        logger.info(f"Prediction for user {request.user_id}: {result['crop']} ({result['suitability']})")
        
        return jsonify(result)
        
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        return jsonify({"error": f"Invalid parameter type: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@app.route('/history', methods=['GET'])
@require_auth
def get_recommendation_history():
    """Get user's crop recommendation history"""
    try:
        endpoint = f"crop_recommendations?user_id=eq.{request.user_id}&order=created_at.desc&limit=20"
        history = supabase_request(endpoint)
        
        if history is None:
            return jsonify({"error": "Failed to fetch history"}), 500
        
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history)
        })
        
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return jsonify({"error": "Failed to fetch recommendation history"}), 500

@app.route('/test-supabase', methods=['GET'])
def test_supabase():
    """Test Supabase connection"""
    try:
        # Test basic connectivity
        endpoint = "crop_recommendations?select=count&limit=1"
        response = supabase_request(endpoint)
        
        return jsonify({
            "success": True,
            "supabase_connected": response is not None,
            "supabase_url": SUPABASE_URL,
            "message": "Supabase connection test completed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860)) 
    app.run(host='0.0.0.0', port=port, debug=False)
