from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bcrypt
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

app = Flask(__name__)

# Configure CORS
CORS(app, origins=[
    'http://localhost:3000',
    'https://*.vercel.app'
], supports_credentials=True)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://"
)

# Supabase Configuration - مع تنظيف المسافات
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip()  # تنظيف المسافات
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '').strip()  # تنظيف المسافات
JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback-secret-key').strip()

print("🌿 Flora Auth API Starting...")
print(f"SUPABASE_URL: '{SUPABASE_URL}'")
print(f"SUPABASE_URL length: {len(SUPABASE_URL)}")
print(f"SUPABASE_KEY loaded: {bool(SUPABASE_KEY)}")

def hash_password(password):
    """Hash password"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id, email):
    """Create JWT token"""
    payload = {
        'user_id': str(user_id),
        'email': email,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

# Supabase REST API Helper Functions
def supabase_request(endpoint, method='GET', data=None):
    """Make request to Supabase REST API"""
    # تنظيف الـ URL من أي مسافات
    base_url = SUPABASE_URL.strip()
    if not base_url:
        print("❌ SUPABASE_URL is empty!")
        return None
        
    url = f"{base_url}/rest/v1/{endpoint}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    print(f"🔧 Making {method} request to: {url}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        
        print(f"🔧 Response status: {response.status_code}")
        
        if response.status_code >= 400:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return None
        
        # Handle empty response
        if response.status_code == 204 or not response.text.strip():
            return []
            
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None

def get_user_by_email(email):
    """Get user by email"""
    endpoint = f"users?email=eq.{email}"
    return supabase_request(endpoint)

def create_user(email, password_hash, full_name):
    """Create new user"""
    endpoint = "users"
    data = {
        'email': email,
        'password_hash': password_hash,
        'full_name': full_name
    }
    return supabase_request(endpoint, 'POST', data)

def update_last_login(user_id):
    """Update user's last login"""
    endpoint = f"users?id=eq.{user_id}"
    data = {'last_login': datetime.utcnow().isoformat()}
    return supabase_request(endpoint, 'PATCH', data)

# Root endpoint
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Flora Authentication API 🌿',
        'version': '1.0.0',
        'status': 'running',
        'config': {
            'supabase_url_configured': bool(SUPABASE_URL),
            'supabase_key_configured': bool(SUPABASE_KEY)
        }
    })

# Health check
@app.route('/health', methods=['GET'])
def health():
    try:
        # Test basic Supabase connection
        test_url = f"{SUPABASE_URL.strip()}/rest/v1/"
        headers = {'apikey': SUPABASE_KEY}
        response = requests.get(test_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            db_status = 'connected'
        else:
            db_status = f'error: {response.status_code}'
            
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'service': 'Flora Auth',
        'database': db_status,
        'supabase_url_clean': SUPABASE_URL.strip() == 'https://onnbpuqxtmdddbksfgrt.supabase.co'
    })

# Register endpoint
@app.route('/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    try:
        data = request.json
        print(f"📥 Register request: {data}")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user exists
        existing_users = get_user_by_email(email)
        print(f"🔍 Existing users check: {existing_users}")
        
        if existing_users and len(existing_users) > 0:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        password_hash = hash_password(password)
        new_user = create_user(email, password_hash, full_name)
        print(f"🔧 Create user result: {new_user}")
        
        if not new_user or len(new_user) == 0:
            return jsonify({'error': 'Failed to create user. Please check RLS policies.'}), 500
        
        user = new_user[0]
        
        # Create token
        token = create_token(user['id'], user['email'])
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': str(user['id']),
                'email': user['email'],
                'full_name': user['full_name']
            }
        }), 201
    
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

# Login endpoint
@app.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        # Get user
        users = get_user_by_email(email)
        if not users or len(users) == 0:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user = users[0]
        
        if not verify_password(password, user['password_hash']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Update last login
        update_last_login(user['id'])
        
        # Create token
        token = create_token(user['id'], user['email'])
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': str(user['id']),
                'email': user['email'],
                'full_name': user['full_name']
            }
        })
    
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

# Test endpoint جديد
@app.route('/test-config', methods=['GET'])
def test_config():
    """Test configuration details"""
    return jsonify({
        'supabase_url_raw': SUPABASE_URL,
        'supabase_url_clean': SUPABASE_URL.strip(),
        'supabase_url_length': len(SUPABASE_URL),
        'supabase_key_exists': bool(SUPABASE_KEY),
        'expected_url': 'https://onnbpuqxtmdddbksfgrt.supabase.co',
        'urls_match': SUPABASE_URL.strip() == 'https://onnbpuqxtmdddbksfgrt.supabase.co'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    app.run(host='0.0.0.0', port=port, debug=False)