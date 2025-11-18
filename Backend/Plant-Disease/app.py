from flask import Flask, request, jsonify
import io
import base64
from PIL import Image
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

# Add current directory to path to import score
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your model scoring
from score import PlantDiseaseModel

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes 
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

print("🌿 Plant Disease Detection API Starting...")
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY loaded: {bool(SUPABASE_KEY)}")

# Initialize model
model = PlantDiseaseModel()
init_success = model.init()

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
        logger.info(f"Request data: {data}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Response text: {response.text}")
        
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

def save_disease_prediction(user_id, image_url, result):
    """Save disease prediction to Supabase"""
    try:
        endpoint = "disease_predictions"
        
        # Determine if plant is healthy based on your model's output
        is_healthy = result.get('status', '').lower() == 'healthy'
        confidence = result.get('overall_confidence', 0.0)
        disease_detected = "Healthy" if is_healthy else "Disease Detected"
        
        data = {
            'user_id': user_id,
            'image_url': image_url,
            'image_path': f"disease_images/{user_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg",
            'is_healthy': is_healthy,
            'confidence': confidence,
            'disease_detected': disease_detected,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Add detailed diagnosis if available
        if 'treatment' in result:
            data['treatment_recommendation'] = result['treatment']
        if 'prevention' in result:
            data['prevention_tips'] = result['prevention']
        
        logger.info(f"Attempting to save disease prediction for user {user_id}")
        logger.info(f"Data being sent: {data}")
        
        response = supabase_request(endpoint, 'POST', data)
        
        logger.info(f"Supabase API response: {response}")
        
        if response:
            logger.info(f"Successfully saved disease prediction: {response}")
            return True
        else:
            logger.error("❌ Failed to save disease prediction - API returned None")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error saving disease prediction: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def upload_plant_image(image_file, user_id):
    """Upload plant image to Supabase Storage"""
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = image_file.filename.split('.')[-1].lower()
        unique_filename = f"{user_id}/{timestamp}.{file_extension}"
        
        # Upload to Supabase Storage using the correct endpoint
        endpoint = f"storage/v1/object/plant-images/{unique_filename}"
        url = f"{SUPABASE_URL}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': image_file.content_type
        }
        
        # Reset file pointer and read data
        image_file.seek(0)
        file_data = image_file.read()
        
        response = requests.post(
            url,
            headers=headers,
            data=file_data,
            timeout=30
        )
        
        if response.status_code == 200:
            # Get public URL
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/plant-images/{unique_filename}"
            logger.info(f"Image uploaded successfully: {public_url}")
            return {
                'success': True,
                'path': unique_filename,
                'url': public_url
            }
        else:
            logger.error(f"❌ Image upload failed: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f"Upload failed: {response.status_code}",
                'details': response.text
            }
    
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        return {
            'success': False,
            'error': str(e)
        }

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

def enhance_prediction_result(base_result):
    """Add treatment and prevention advice based on prediction"""
    status = base_result.get('status', '')
    confidence = base_result.get('overall_confidence', 0)
    
    enhanced_result = base_result.copy()
    
    if status.lower() == 'healthy':
        enhanced_result.update({
            'disease': 'No Disease',
            'is_healthy': True,
            'treatment': 'No treatment needed. Your plant is healthy!',
            'prevention': 'Continue with current care routine. Monitor regularly.',
            'advice': 'Maintain proper watering, sunlight, and nutrient levels.'
        })
    else:
        enhanced_result.update({
            'disease': 'Plant Disease Detected',
            'is_healthy': False,
            'treatment': 'Apply appropriate fungicide or pesticide. Isolate plant if contagious. Remove affected leaves.',
            'prevention': 'Improve air circulation. Avoid overwatering. Ensure proper spacing between plants.',
            'advice': 'Consult with agricultural expert for specific treatment.'
        })
    
    # Add confidence level description
    if confidence > 0.8:
        confidence_level = "High"
    elif confidence > 0.6:
        confidence_level = "Medium"
    else:
        confidence_level = "Low"
    
    enhanced_result['confidence_level'] = confidence_level
    enhanced_result['suitability'] = f"{confidence:.1%}"
    
    return enhanced_result

@app.route('/')
def home():
    return jsonify({
        "message": "Plant Disease Detection API 🌿",
        "status": "running",
        "model_loaded": init_success,
        "supabase_connected": bool(SUPABASE_URL and SUPABASE_KEY),
        "endpoints": {
            "health": "/health (GET)",
            "predict": "/predict (POST) - requires auth",
            "history": "/history (GET) - requires auth",
            "test": "/test-supabase (GET)"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    # Test Supabase connection
    supabase_status = False
    try:
        test_response = supabase_request("disease_predictions?select=count&limit=1")
        supabase_status = test_response is not None
    except:
        pass
    
    return jsonify({
        "status": "healthy",
        "model_initialized": init_success,
        "supabase_connected": supabase_status,
        "device": str(model.device) if init_success else "unknown"
    })

@app.route('/predict', methods=['POST'])
@require_auth
@limiter.limit("20 per hour")
def predict():
    try:
        if not init_success:
            return jsonify({"error": "Model not initialized"}), 500
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return jsonify({"error": "Invalid file type. Use PNG, JPG, or WEBP"}), 400
        
        if not file.content_type.startswith('image/'):
            return jsonify({"error": "File must be an image"}), 400
        
        logger.info(f"📸 Processing image from user {request.user_id} - {file.filename}")
        
        # Upload image to Supabase Storage
        upload_result = upload_plant_image(file, request.user_id)
        
        image_url = None
        if upload_result.get('success'):
            image_url = upload_result['url']
            logger.info(f"✅ Image uploaded to: {image_url}")
        else:
            logger.warning(f"⚠️ Image upload failed: {upload_result.get('error')}")
            # Continue without saving image URL for now
        
        # Read file again for prediction (reset file pointer)
        file.seek(0)
        image_data = file.read()
        
        # Get prediction from model
        base_result = model.run(image_data)
        
        # Enhance result with additional information
        enhanced_result = enhance_prediction_result(base_result)
        
        # Save prediction to Supabase
        if image_url:  # Only save if image upload was successful
            save_result = save_disease_prediction(request.user_id, image_url, enhanced_result)
            enhanced_result['saved_to_database'] = save_result
            enhanced_result['image_url'] = image_url
        else:
            enhanced_result['saved_to_database'] = False
            enhanced_result['image_url'] = None
            enhanced_result['upload_error'] = upload_result.get('error', 'Unknown upload error')
        
        logger.info(f"🔍 Prediction completed for user {request.user_id}: {enhanced_result.get('status', 'Unknown')}")
        
        return jsonify(enhanced_result)
        
    except Exception as e:
        logger.error(f"❌ Prediction error: {str(e)}")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@app.route('/history', methods=['GET'])
@require_auth
def get_prediction_history():
    """Get user's disease prediction history"""
    try:
        endpoint = f"disease_predictions?user_id=eq.{request.user_id}&order=created_at.desc&limit=20"
        history = supabase_request(endpoint)
        
        if history is None:
            return jsonify({"error": "Failed to fetch history"}), 500
        
        # Format the response
        formatted_history = []
        for item in history:
            formatted_history.append({
                "id": item.get('id'),
                "image_url": item.get('image_url'),
                "disease_detected": item.get('disease_detected'),
                "is_healthy": item.get('is_healthy'),
                "confidence": item.get('confidence'),
                "created_at": item.get('created_at'),
                "treatment": item.get('treatment_recommendation'),
                "prevention": item.get('prevention_tips')
            })
        
        return jsonify({
            "success": True,
            "history": formatted_history,
            "count": len(history)
        })
        
    except Exception as e:
        logger.error(f"Error fetching disease history: {e}")
        return jsonify({"error": "Failed to fetch prediction history"}), 500

@app.route('/test-supabase', methods=['GET'])
def test_supabase():
    """Test Supabase connection"""
    try:
        # Test basic connectivity
        endpoint = "disease_predictions?select=count&limit=1"
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

@app.route('/test-auth', methods=['GET'])
@require_auth
def test_auth():
    """Test authentication endpoint"""
    return jsonify({
        "success": True,
        "message": "Authentication successful",
        "user_id": request.user_id,
        "user_email": request.user_email
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860)) 
    app.run(host='0.0.0.0', port=port, debug=False)
