# Flask application entry point
# ContractIQ Backend - Main Application File
# This is the core Flask application that handles all API routes and business logic

# =============================================================================
# IMPORTS
# =============================================================================

# Flask core imports
# - Flask: The main application class
# - request: Access incoming request data (JSON, form data, files)
# - jsonify: Convert Python dicts to JSON responses
# - session: Server-side session management for user authentication
from flask import Flask, request, jsonify, session

# Flask-CORS: Enable Cross-Origin Resource Sharing
# Required for frontend (React/Vue/etc.) to communicate with this backend
# Without CORS, browsers block requests from different origins
from flask_cors import CORS

# Werkzeug security utilities
# - generate_password_hash: Securely hash passwords (never store plain text!)
# - check_password_hash: Verify password against stored hash
# - secure_filename: Sanitize uploaded filenames to prevent directory traversal attacks
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Standard library imports
import os                   # File system operations (paths, directories)
from datetime import datetime, timedelta  # Timestamps for unique filenames and JWT expiration
import uuid                 # Generate unique identifiers

# JWT for access token authentication
import jwt

# =============================================================================
# IMPORT LOCAL MODULES
# =============================================================================

# Database operations (user management, document storage)
from database import (
    init_db,
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    save_document,
    get_user_documents,
    get_document_by_id,
    delete_document,
    get_dashboard_stats,
    user_exists
)

# PDF text extraction
from pdf_processor import (
    extract_text_from_pdf,
    get_pdf_info
)

# Contract clause extraction
from clause_extractor import (
    extract_clauses,
    get_clause_summary,
    get_available_categories
)


# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

# Create the Flask application instance
# __name__ tells Flask where to look for resources (templates, static files)
app = Flask(__name__)

# -----------------------------------------------------------------------------
# SECRET KEY CONFIGURATION
# -----------------------------------------------------------------------------
# The secret key is used for:
# - Signing session cookies (prevents tampering)
# - CSRF protection
# - Any cryptographic operations
#
# IMPORTANT: In production, use a strong random key stored in environment variables!
# Never hardcode the secret key in production code
#
# Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-abc123')

# -----------------------------------------------------------------------------
# FILE UPLOAD CONFIGURATION
# -----------------------------------------------------------------------------
# Define where uploaded PDF files will be stored
# os.path.dirname(__file__) gets the directory containing this script
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Maximum allowed file size: 10 MB (in bytes)
# This prevents users from uploading extremely large files that could
# consume server resources or cause denial of service
# 10 MB = 10 * 1024 * 1024 bytes = 10,485,760 bytes
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

# Allowed file extensions
# We only accept PDF files for contract analysis
# Stored as a set for O(1) lookup performance
ALLOWED_EXTENSIONS = {'pdf'}

# -----------------------------------------------------------------------------
# SESSION CONFIGURATION
# -----------------------------------------------------------------------------
# Configure session behavior
app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions on disk
app.config['SESSION_PERMANENT'] = False    # Session expires when browser closes
app.config['SESSION_USE_SIGNER'] = True    # Sign session cookies for security

# -----------------------------------------------------------------------------
# CORS CONFIGURATION
# -----------------------------------------------------------------------------
# Enable CORS (Cross-Origin Resource Sharing) for all routes
# This allows the frontend application (running on a different port/domain)
# to make requests to this API
#
# Configuration options:
# - supports_credentials=True: Allow cookies/sessions in cross-origin requests
# - origins: Specify allowed origins (use specific domains in production)
#
# SECURITY NOTE: In production, restrict origins to your frontend domain only
# Example: origins=["https://yourdomain.com", "https://www.yourdomain.com"]
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://127.0.0.1:3000"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    This function validates that the uploaded file is a PDF by checking
    its extension. This is a basic validation - for production, you should
    also verify the file's MIME type and magic bytes.
    
    Security Note:
    - File extension checking is just the first line of defense
    - Malicious users could rename files to bypass this check
    - Additional validation happens during PDF processing
    
    Args:
        filename (str): The name of the uploaded file
    
    Returns:
        bool: True if file has .pdf extension, False otherwise
    
    Example:
        allowed_file("contract.pdf")  # Returns True
        allowed_file("document.docx") # Returns False
        allowed_file("malware.exe")   # Returns False
    """
    # Check if filename contains a dot (has extension)
    # and if the extension (after the last dot) is in allowed set
    # The rsplit('.', 1) splits from the right, once, to get the extension
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename):
    """
    Generate a unique filename for storing uploaded files.
    
    This function creates a unique filename by combining:
    - A UUID (Universally Unique Identifier)
    - A timestamp
    - The original file extension
    
    Why unique filenames?
    - Prevents filename collisions (two users upload "contract.pdf")
    - Prevents overwriting existing files
    - Adds security by obscuring original filenames
    - Makes files harder to guess/access without authorization
    
    Args:
        original_filename (str): The original name of the uploaded file
    
    Returns:
        str: A unique filename in format: uuid_timestamp.extension
    
    Example:
        generate_unique_filename("my_contract.pdf")
        # Returns: "a1b2c3d4-e5f6-7890-abcd-ef1234567890_20250206_143052.pdf"
    """
    # Extract the file extension from the original filename
    # secure_filename sanitizes the filename first to prevent path traversal
    secure_name = secure_filename(original_filename)
    
    # Get the extension (e.g., "pdf")
    extension = secure_name.rsplit('.', 1)[1].lower() if '.' in secure_name else 'pdf'
    
    # Generate unique components
    unique_id = str(uuid.uuid4())  # Random UUID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Current timestamp
    
    # Combine into unique filename
    unique_filename = f"{unique_id}_{timestamp}.{extension}"
    
    return unique_filename


# =============================================================================
# JWT TOKEN CONFIGURATION
# =============================================================================

# JWT token expiration time (24 hours)
JWT_EXPIRATION_HOURS = 24

# JWT algorithm
JWT_ALGORITHM = 'HS256'


def generate_access_token(user_id, username, role):
    """
    Generate a JWT access token for the user.
    
    The token contains user information and has an expiration time.
    
    Args:
        user_id (int): The user's database ID
        username (str): The user's username
        role (str): The user's role
    
    Returns:
        str: The encoded JWT token
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()  # Issued at time
    }
    
    token = jwt.encode(
        payload,
        app.config['SECRET_KEY'],
        algorithm=JWT_ALGORITHM
    )
    
    return token


def verify_access_token(token):
    """
    Verify and decode a JWT access token.
    
    Args:
        token (str): The JWT token to verify
    
    Returns:
        dict: The decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        print("✗ Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"✗ Invalid token: {e}")
        return None


def get_current_user():
    """
    Get the currently logged-in user from the session or access token.
    
    This helper function first checks for an access token in the Authorization header,
    then falls back to checking the session cookie.
    
    Returns:
        dict: User data if logged in, None otherwise
    
    Usage:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
    """
    # First, try to get user from access token (Authorization header)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        payload = verify_access_token(token)
        if payload:
            return get_user_by_id(payload['user_id'])
    
    # Fall back to session-based authentication
    user_id = session.get('user_id')
    if not user_id:
        return None
    return get_user_by_id(user_id)


def get_current_user_id():
    """
    Get the current user's ID from session or access token.
    
    Returns:
        int: User ID if authenticated, None otherwise
    """
    # First, try to get user_id from access token (Authorization header)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        payload = verify_access_token(token)
        if payload:
            return payload['user_id']
    
    # Fall back to session-based authentication
    return session.get('user_id')


def login_required(f):
    """
    Decorator to protect routes that require authentication.
    
    This decorator checks for authentication via:
    1. JWT access token in Authorization header (Bearer token)
    2. Session cookie (user_id in session)
    
    If neither is present or valid, returns 401 Unauthorized.
    
    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return jsonify({'message': 'You are logged in!'})
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try access token first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            payload = verify_access_token(token)
            if payload:
                # Token is valid, allow access
                return f(*args, **kwargs)
        
        # Fall back to session-based authentication
        if 'user_id' in session:
            return f(*args, **kwargs)
        
        # Neither token nor session is valid
        return jsonify({
            'success': False,
            'error': 'Authentication required. Please log in or provide a valid access token.'
        }), 401
    
    return decorated_function


# =============================================================================
# ENSURE REQUIRED DIRECTORIES EXIST
# =============================================================================

def ensure_directories():
    """
    Create required directories if they don't exist.
    
    This function ensures that the uploads folder and instance folder
    (for SQLite database) exist before the application starts.
    """
    # Create uploads directory
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        print(f"✓ Created uploads directory: {UPLOAD_FOLDER}")
    
    # Create instance directory (for SQLite database)
    instance_folder = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_folder):
        os.makedirs(instance_folder)
        print(f"✓ Created instance directory: {instance_folder}")


# =============================================================================
# APPLICATION INITIALIZATION
# =============================================================================

# Ensure directories exist
ensure_directories()

# Initialize the database (create tables if they don't exist)
# This is called when the module is imported or when the app starts
print("\n" + "=" * 50)
print("ContractIQ Backend Starting...")
print("=" * 50)
init_db()
print("=" * 50 + "\n")


# =============================================================================
# API ROUTES PLACEHOLDER
# =============================================================================
# Routes will be added in the next steps:
# - Authentication routes (register, login, logout)
# - Document routes (upload, list, delete)
# - Analysis routes (extract clauses, get summary)
# - Dashboard routes (stats, recent documents)

@app.route('/')
def index():
    """
    Root endpoint - API health check.
    
    Returns basic information about the API and its status.
    Useful for monitoring and debugging.
    """
    return jsonify({
        'name': 'ContractIQ API',
        'version': '1.0.0',
        'status': 'running',
        'message': 'Welcome to ContractIQ - Contract Analysis API',
        'endpoints': {
            'health': 'GET /',
            'auth': {
                'register': 'POST /api/auth/register',
                'login': 'POST /api/auth/login',
                'logout': 'POST /api/auth/logout',
                'profile': 'GET /api/auth/profile'
            },
            'documents': {
                'upload': 'POST /api/documents/upload',
                'list': 'GET /api/documents',
                'get': 'GET /api/documents/<id>',
                'delete': 'DELETE /api/documents/<id>'
            },
            'dashboard': 'GET /api/dashboard'
        }
    })


@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns a simple status indicating the API is running.
    Used by load balancers, monitoring tools, and container orchestration.
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route('/api/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    This endpoint creates a new user in the system with the provided
    credentials. The password is securely hashed before storage.
    
    Request Body (JSON):
        {
            "username": "string",    # Required: Unique username (3-50 chars)
            "email": "string",       # Required: Valid email address
            "password": "string",    # Required: Password (min 6 chars)
            "role": "string"         # Optional: 'admin', 'lawyer', or 'client' (default: 'client')
        }
    
    Returns:
        Success (201):
            {
                "success": true,
                "message": "User registered successfully",
                "user": {"id": 1, "username": "john_doe", "role": "client"}
            }
        
        Error (400): Invalid input data
            {"success": false, "error": "Error description"}
        
        Error (409): Username/email already exists
            {"success": false, "error": "Username already exists"}
    
    Security Notes:
        - Passwords are hashed using Werkzeug's generate_password_hash
        - The hash uses PBKDF2 with SHA-256 by default
        - Never log or return the password or hash
    """
    
    # -------------------------------------------------------------------------
    # Step 1: Parse and validate request data
    # -------------------------------------------------------------------------
    
    # Ensure request contains JSON data
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Request must be JSON. Set Content-Type: application/json'
        }), 400
    
    # Get JSON data from request body
    data = request.get_json()
    
    # Extract fields from request
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()  # Normalize email to lowercase
    password = data.get('password', '')
    role = data.get('role', 'client').strip().lower()  # Default role is 'client'
    
    # -------------------------------------------------------------------------
    # Step 2: Validate required fields
    # -------------------------------------------------------------------------
    
    # Check that all required fields are present and not empty
    if not username:
        return jsonify({
            'success': False,
            'error': 'Username is required'
        }), 400
    
    if not email:
        return jsonify({
            'success': False,
            'error': 'Email is required'
        }), 400
    
    if not password:
        return jsonify({
            'success': False,
            'error': 'Password is required'
        }), 400
    
    # -------------------------------------------------------------------------
    # Step 3: Validate field formats and constraints
    # -------------------------------------------------------------------------
    
    # Username validation: 3-50 characters, alphanumeric and underscores only
    if len(username) < 3 or len(username) > 50:
        return jsonify({
            'success': False,
            'error': 'Username must be between 3 and 50 characters'
        }), 400
    
    if not username.replace('_', '').isalnum():
        return jsonify({
            'success': False,
            'error': 'Username can only contain letters, numbers, and underscores'
        }), 400
    
    # Email validation: Basic format check (contains @ and .)
    if '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({
            'success': False,
            'error': 'Please provide a valid email address'
        }), 400
    
    # Password validation: Minimum 6 characters
    if len(password) < 6:
        return jsonify({
            'success': False,
            'error': 'Password must be at least 6 characters long'
        }), 400
    
    # Role validation: Must be one of the allowed values
    allowed_roles = ['admin', 'lawyer', 'client']
    if role not in allowed_roles:
        return jsonify({
            'success': False,
            'error': f'Invalid role. Must be one of: {", ".join(allowed_roles)}'
        }), 400
    
    # -------------------------------------------------------------------------
    # Step 4: Check if username or email already exists
    # -------------------------------------------------------------------------
    
    if user_exists(username=username):
        return jsonify({
            'success': False,
            'error': 'Username already exists. Please choose a different username.'
        }), 409  # 409 Conflict
    
    if user_exists(email=email):
        return jsonify({
            'success': False,
            'error': 'Email already registered. Please use a different email or login.'
        }), 409
    
    # -------------------------------------------------------------------------
    # Step 5: Hash password and create user
    # -------------------------------------------------------------------------
    
    # Generate secure password hash
    # The method 'pbkdf2:sha256' is secure and widely recommended
    # The hash includes the salt, so we don't need to store it separately
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    # Create the user in the database
    user_id = create_user(
        username=username,
        email=email,
        password_hash=password_hash,
        role=role
    )
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Failed to create user. Please try again.'
        }), 500
    
    # -------------------------------------------------------------------------
    # Step 6: Return success response
    # -------------------------------------------------------------------------
    
    print(f"✓ New user registered: {username} (ID: {user_id}, Role: {role})")
    
    return jsonify({
        'success': True,
        'message': 'User registered successfully',
        'user': {
            'id': user_id,
            'username': username,
            'role': role
        }
    }), 201  # 201 Created


@app.route('/api/login', methods=['POST'])
def login():
    """
    Authenticate a user with email and create a session + access token.
    
    This endpoint verifies user credentials and establishes both:
    - A session cookie for web browser clients
    - A JWT access token for API/mobile clients
    
    Request Body (JSON):
        {
            "email": "string",       # Required: User's email address
            "password": "string"     # Required: User's password
        }
    
    Returns:
        Success (200):
            {
                "success": true,
                "message": "Login successful",
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john@example.com",
                    "role": "client"
                },
                "access_token": "eyJhbGciOiJIUzI1NiIs..."
            }
        
        Error (400): Missing credentials
            {"success": false, "error": "Email and password are required"}
        
        Error (401): Invalid credentials
            {"success": false, "error": "Invalid email or password"}
    
    Session:
        On successful login, the following are stored in the session:
        - user_id: The user's database ID
        - username: The user's username
        - role: The user's role
    
    Access Token:
        A JWT token is returned that can be used in the Authorization header:
        Authorization: Bearer <access_token>
    
    Security Notes:
        - Failed login attempts don't reveal whether email exists
        - Same error message for wrong email and wrong password
        - Password comparison uses constant-time comparison (via check_password_hash)
    """
    
    # -------------------------------------------------------------------------
    # Step 1: Parse and validate request data
    # -------------------------------------------------------------------------
    
    # Ensure request contains JSON data
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Request must be JSON. Set Content-Type: application/json'
        }), 400
    
    # Get JSON data from request body
    data = request.get_json()
    
    # Extract credentials - now using email instead of username
    email = data.get('email', '').strip().lower()  # Normalize email to lowercase
    password = data.get('password', '')
    
    # Validate that both fields are provided
    if not email or not password:
        return jsonify({
            'success': False,
            'error': 'Email and password are required'
        }), 400
    
    # -------------------------------------------------------------------------
    # Step 2: Fetch user from database by email
    # -------------------------------------------------------------------------
    
    user = get_user_by_email(email)
    
    # -------------------------------------------------------------------------
    # Step 3: Verify credentials
    # -------------------------------------------------------------------------
    
    # Check if user exists and password is correct
    # IMPORTANT: We use the same error message for both cases to prevent
    # email enumeration attacks (attacker can't tell if email exists)
    if not user:
        # User doesn't exist - but don't reveal this
        print(f"✗ Login failed: Email not found - {email}")
        return jsonify({
            'success': False,
            'error': 'Invalid email or password'
        }), 401
    
    # Verify password against stored hash
    # check_password_hash uses constant-time comparison to prevent timing attacks
    if not check_password_hash(user['password_hash'], password):
        # Password doesn't match
        print(f"✗ Login failed: Wrong password for email - {email}")
        return jsonify({
            'success': False,
            'error': 'Invalid email or password'
        }), 401
    
    # -------------------------------------------------------------------------
    # Step 4: Create session (for cookie-based auth)
    # -------------------------------------------------------------------------
    
    # Clear any existing session data
    session.clear()
    
    # Store user information in session
    # This creates a signed cookie that the client will send with future requests
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    
    # Mark session as modified to ensure it's saved
    session.modified = True
    
    # -------------------------------------------------------------------------
    # Step 5: Generate JWT access token
    # -------------------------------------------------------------------------
    
    access_token = generate_access_token(
        user_id=user['id'],
        username=user['username'],
        role=user['role']
    )
    
    # -------------------------------------------------------------------------
    # Step 6: Return success response with access token
    # -------------------------------------------------------------------------
    
    print(f"✓ User logged in: {user['username']} (ID: {user['id']}) via email: {email}")
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role']
        },
        'access_token': access_token
    }), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    """
    Log out the current user and destroy their session.
    
    This endpoint clears all session data, effectively logging out the user.
    The client should also clear any locally stored user information.
    
    Request:
        No body required. Session cookie is used for identification.
    
    Returns:
        Success (200):
            {
                "success": true,
                "message": "Logged out successfully"
            }
    
    Notes:
        - This endpoint always returns success, even if no user was logged in
        - The session cookie is invalidated
        - Client should redirect to login page after calling this
    """
    
    # Get username before clearing session (for logging)
    username = session.get('username', 'Unknown')
    
    # Clear all session data
    # This removes user_id, username, role, and any other session variables
    session.clear()
    
    print(f"✓ User logged out: {username}")
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    """
    Get the current user's profile information.
    
    This endpoint returns the profile of the currently logged-in user.
    Requires authentication (session must contain valid user_id).
    
    Returns:
        Success (200):
            {
                "success": true,
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john@example.com",
                    "role": "client",
                    "created_at": "2025-02-06 10:30:00"
                }
            }
        
        Error (401): Not authenticated
            {"success": false, "error": "Authentication required. Please log in."}
    """
    
    # Get current user from session
    user = get_current_user()
    
    if not user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'created_at': user['created_at']
        }
    }), 200


# =============================================================================
# DASHBOARD ROUTE
# =============================================================================

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    """
    Get dashboard data for the current user.
    
    This endpoint provides an overview of the user's account including
    profile information and document statistics. It demonstrates session
    management in Flask.
    
    Session Management Explanation:
    ------------------------------
    Flask sessions work as follows:
    
    1. When a user logs in, we store their user_id in the session:
       session['user_id'] = user['id']
    
    2. Flask serializes the session data, signs it with SECRET_KEY,
       and sends it as a cookie to the client's browser.
    
    3. On subsequent requests, the browser automatically sends this cookie.
    
    4. Flask verifies the signature (prevents tampering) and deserializes
       the session data, making it available via the `session` object.
    
    5. We can then check session['user_id'] to identify the logged-in user.
    
    This approach is stateless on the server side - all session data is
    stored in the signed cookie. For larger session data or better security,
    consider server-side sessions (Redis, database, etc.).
    
    Returns:
        Success (200):
            {
                "success": true,
                "user": {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "role": "client"
                },
                "stats": {
                    "total_documents": 5,
                    "recent_uploads": 2,
                    "total_clauses_extracted": 4,
                    "recent_documents": [...]
                }
            }
        
        Error (401): Not authenticated
            {
                "success": false,
                "error": "Not authenticated. Please log in."
            }
    
    Notes:
        - The session cookie is HTTP-only (not accessible via JavaScript)
        - The cookie is signed to prevent tampering
        - Session expires when browser closes (SESSION_PERMANENT = False)
    """
    
    # -------------------------------------------------------------------------
    # Step 1: Check if user is authenticated
    # -------------------------------------------------------------------------
    # 
    # We support dual authentication:
    # 1. JWT access token in Authorization header (Bearer token)
    # 2. Session cookie (user_id in session)
    #
    # get_current_user_id() checks both methods and returns the user_id.
    
    user_id = get_current_user_id()
    
    # If user_id is not found via token or session, the user is not logged in
    if not user_id:
        # Return 401 Unauthorized status code
        # This tells the client they need to authenticate first
        return jsonify({
            'success': False,
            'error': 'Not authenticated. Please log in or provide a valid access token.'
        }), 401
    
    # -------------------------------------------------------------------------
    # Step 2: Fetch user information from database
    # -------------------------------------------------------------------------
    #
    # Even though we have user_id in the session, we fetch fresh user data
    # from the database. This ensures:
    # - User still exists (wasn't deleted)
    # - We have the latest user information (role might have changed)
    # - We don't expose sensitive data stored only in session
    
    user = get_user_by_id(user_id)
    
    # Handle case where user was deleted after login
    if not user:
        # Clear the invalid session
        session.clear()
        return jsonify({
            'success': False,
            'error': 'User account not found. Please log in again.'
        }), 401
    
    # -------------------------------------------------------------------------
    # Step 3: Get dashboard statistics
    # -------------------------------------------------------------------------
    #
    # Fetch aggregated statistics about the user's documents.
    # This provides a quick overview without loading all document data.
    
    stats = get_dashboard_stats(user_id)
    
    # -------------------------------------------------------------------------
    # Step 4: Return dashboard data
    # -------------------------------------------------------------------------
    
    print(f"→ Dashboard accessed by: {user['username']} (ID: {user_id})")
    
    return jsonify({
        'success': True,
        'user': {
            'username': user['username'],
            'email': user['email'],
            'role': user['role']
        },
        'stats': {
            'total_documents': stats.get('total_documents', 0),
            'recent_uploads': len(stats.get('recent_documents', [])),
            'total_clauses_extracted': stats.get('total_clauses_extracted', 0),
            'recent_documents': stats.get('recent_documents', []),
            'account_created': stats.get('account_created')
        }
    }), 200


# =============================================================================
# PDF UPLOAD ROUTE
# =============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """
    Upload a PDF document for analysis.
    
    This endpoint handles the complete document upload and processing pipeline:
    1. Receive the PDF file from the client
    2. Validate the file (type, size)
    3. Save the file with a unique name
    4. Extract text content from the PDF
    5. Analyze text and extract contract clauses
    6. Store everything in the database
    7. Return the results to the client
    
    Authentication:
        Requires user to be logged in (user_id in session).
    
    Request:
        Content-Type: multipart/form-data
        Body: 
            - file: The PDF file to upload (required)
    
    Returns:
        Success (200):
            {
                "success": true,
                "message": "Document uploaded and processed successfully",
                "document": {
                    "id": 1,
                    "filename": "uuid_timestamp.pdf",
                    "original_filename": "contract.pdf",
                    "upload_date": "2025-02-06 10:30:00",
                    "clauses": {
                        "Termination": ["clause 1", "clause 2"],
                        "Payment": ["clause 3"],
                        ...
                    },
                    "clauses_summary": {
                        "total_clauses": 10,
                        "categories": {...}
                    },
                    "text_preview": "First 500 characters of extracted text..."
                }
            }
        
        Error (400): Bad request (no file, invalid file type)
            {"success": false, "error": "Error description"}
        
        Error (401): Not authenticated
            {"success": false, "error": "Not authenticated. Please log in."}
        
        Error (413): File too large (handled by Flask error handler)
            {"success": false, "error": "File too large. Maximum size is 10 MB."}
        
        Error (500): Processing error
            {"success": false, "error": "Failed to process document"}
    
    File Processing Pipeline:
        1. Validation → Check file exists and is PDF
        2. Storage → Save to uploads/ with unique filename
        3. Extraction → Use PyPDF2 to extract text
        4. Analysis → Use keyword matching to identify clauses
        5. Database → Store metadata, text, and clauses
        6. Response → Return processed document info
    
    Security Notes:
        - Filenames are sanitized using werkzeug.secure_filename
        - Unique filenames prevent overwriting
        - File type is validated before processing
        - Maximum file size is enforced by Flask
    """
    
    # -------------------------------------------------------------------------
    # Step 1: Verify user is authenticated
    # -------------------------------------------------------------------------
    # Users must be logged in to upload documents
    # This ensures documents are associated with a user account
    # Supports both cookie session and JWT access token authentication
    
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not authenticated. Please log in or provide a valid access token.'
        }), 401
    
    # -------------------------------------------------------------------------
    # Step 2: Check if file is present in request
    # -------------------------------------------------------------------------
    # For file uploads, the file comes in request.files, not request.json
    # The key 'file' is the field name expected from the client form
    
    # Check if the 'file' key exists in the request
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided. Please select a PDF file to upload.'
        }), 400
    
    # Get the file object from the request
    file = request.files['file']
    
    # Check if a file was actually selected (empty filename means no selection)
    # This can happen if user submits form without selecting a file
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected. Please choose a PDF file.'
        }), 400
    
    # -------------------------------------------------------------------------
    # Step 3: Validate file type
    # -------------------------------------------------------------------------
    # Only PDF files are allowed for contract analysis
    # We check the file extension using our allowed_file() helper
    
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Only PDF files are allowed.'
        }), 400
    
    # -------------------------------------------------------------------------
    # Step 4: Generate unique filename and save file
    # -------------------------------------------------------------------------
    # We generate a unique filename to:
    # - Prevent filename collisions (multiple users uploading "contract.pdf")
    # - Prevent overwriting existing files
    # - Add security by not using user-provided filenames directly
    
    # Store the original filename for display purposes
    original_filename = secure_filename(file.filename)
    
    # Generate a unique filename using UUID and timestamp
    unique_filename = generate_unique_filename(original_filename)
    
    # Create the full file path in the uploads directory
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    try:
        # Save the uploaded file to disk
        # Flask's FileStorage.save() handles the file writing
        file.save(file_path)
        print(f"✓ File saved: {file_path}")
        
    except Exception as e:
        print(f"✗ Error saving file: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save the uploaded file. Please try again.'
        }), 500
    
    # -------------------------------------------------------------------------
    # Step 5: Extract text from PDF
    # -------------------------------------------------------------------------
    # Use our pdf_processor module to extract text content from the PDF
    # This uses PyPDF2 to read the PDF and extract all text
    
    print(f"→ Extracting text from: {original_filename}")
    
    extracted_text = extract_text_from_pdf(file_path)
    
    # Check if text extraction was successful
    if extracted_text is None:
        # Text extraction failed - this could be due to:
        # - Corrupted PDF
        # - Scanned document (image-based PDF)
        # - Password-protected PDF
        # - Empty PDF
        
        # We still save the document but with a warning
        print(f"⚠ Could not extract text from: {original_filename}")
        extracted_text = ""  # Store empty string instead of None
        extraction_warning = "Could not extract text from this PDF. It may be scanned, encrypted, or empty."
    else:
        extraction_warning = None
        print(f"✓ Extracted {len(extracted_text)} characters")
    
    # -------------------------------------------------------------------------
    # Step 6: Extract clauses from text
    # -------------------------------------------------------------------------
    # Use our clause_extractor module to identify and categorize clauses
    # This uses keyword matching to find relevant contract terms
    
    print(f"→ Analyzing document for clauses...")
    
    if extracted_text:
        # Extract clauses using keyword matching
        clauses = extract_clauses(extracted_text)
        
        # Create a summary for the response
        clauses_summary = create_clauses_summary(clauses)
        
        print(f"✓ Found {clauses_summary['total_clauses']} clauses across {len(clauses_summary['categories'])} categories")
    else:
        # No text to analyze
        clauses = {
            "Termination": [],
            "Liability": [],
            "Payment": [],
            "Confidentiality": [],
            "Intellectual Property": []
        }
        clauses_summary = {'total_clauses': 0, 'categories': {}}
    
    # -------------------------------------------------------------------------
    # Step 7: Save document to database
    # -------------------------------------------------------------------------
    # Store all document information in the database:
    # - User association (who uploaded it)
    # - File information (names, path)
    # - Extracted content (text and clauses)
    
    print(f"→ Saving to database...")
    
    document_id = save_document(
        user_id=user_id,
        filename=unique_filename,
        original_filename=original_filename,
        file_path=file_path,
        extracted_text=extracted_text,
        clauses=clauses  # This will be JSON-serialized by the database module
    )
    
    if not document_id:
        # Database save failed - clean up the uploaded file
        try:
            os.remove(file_path)
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': 'Failed to save document information. Please try again.'
        }), 500
    
    # -------------------------------------------------------------------------
    # Step 8: Prepare and return response
    # -------------------------------------------------------------------------
    # Return the processed document information to the client
    # Include a text preview (first 500 chars) instead of full text
    
    print(f"✓ Document processed successfully: ID={document_id}")
    
    # Create text preview (first 500 characters)
    text_preview = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
    
    # Build response
    response_data = {
        'success': True,
        'message': 'Document uploaded and processed successfully',
        'document': {
            'id': document_id,
            'filename': unique_filename,
            'original_filename': original_filename,
            'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'clauses': clauses,
            'clauses_summary': clauses_summary,
            'text_preview': text_preview,
            'text_length': len(extracted_text)
        }
    }
    
    # Add warning if text extraction had issues
    if extraction_warning:
        response_data['warning'] = extraction_warning
    
    return jsonify(response_data), 200


# =============================================================================
# DOCUMENT MANAGEMENT ROUTES
# =============================================================================

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """
    Get all documents for the currently logged-in user.
    
    This endpoint retrieves a list of all PDF documents uploaded by the
    authenticated user, including metadata and clause extraction summaries.
    
    Authentication:
        Requires user to be logged in (user_id in session).
    
    Returns:
        Success (200):
            {
                "success": true,
                "documents": [
                    {
                        "id": 1,
                        "filename": "contract_2025.pdf",
                        "original_filename": "My Contract.pdf",
                        "upload_date": "2025-02-06 10:30:00",
                        "clauses_summary": {
                            "total_clauses": 12,
                            "categories": {
                                "Termination": 3,
                                "Liability": 2,
                                "Payment": 4,
                                "Confidentiality": 2,
                                "Intellectual Property": 1
                            }
                        }
                    },
                    ...
                ],
                "total_count": 5
            }
        
        Error (401): Not authenticated
            {"success": false, "error": "Not authenticated. Please log in."}
    
    Notes:
        - Documents are sorted by upload date (newest first)
        - clauses_summary provides a count of clauses by category
        - The full extracted text is NOT included to reduce payload size
    """
    
    # -------------------------------------------------------------------------
    # Step 1: Verify user is authenticated
    # -------------------------------------------------------------------------
    # Check if user is authenticated via session cookie or access token
    
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not authenticated. Please log in or provide a valid access token.'
        }), 401
    
    # -------------------------------------------------------------------------
    # Step 2: Fetch documents from database
    # -------------------------------------------------------------------------
    # get_user_documents returns all documents belonging to this user,
    # sorted by upload_date in descending order (newest first)
    
    documents = get_user_documents(user_id)
    
    # -------------------------------------------------------------------------
    # Step 3: Process documents and create response
    # -------------------------------------------------------------------------
    # Transform the database records into a client-friendly format
    # We don't send the full extracted_text to reduce response size
    
    documents_list = []
    
    for doc in documents:
        # Create clauses summary from the stored clauses data
        clauses_summary = create_clauses_summary(doc.get('clauses'))
        
        # Build document object for response
        doc_info = {
            'id': doc['id'],
            'filename': doc['filename'],
            'original_filename': doc['original_filename'],
            'upload_date': doc['upload_date'],
            'clauses_summary': clauses_summary,
            # Include a flag indicating if text was extracted
            'has_extracted_text': bool(doc.get('extracted_text'))
        }
        
        documents_list.append(doc_info)
    
    # -------------------------------------------------------------------------
    # Step 4: Return response
    # -------------------------------------------------------------------------
    
    print(f"→ Documents retrieved for user {user_id}: {len(documents_list)} document(s)")
    
    return jsonify({
        'success': True,
        'documents': documents_list,
        'total_count': len(documents_list)
    }), 200


def create_clauses_summary(clauses):
    """
    Create a summary of extracted clauses for display.
    
    This helper function transforms the full clauses dictionary into
    a summary showing the count of clauses in each category.
    
    Args:
        clauses (dict): The full clauses dictionary from the database
                       Format: {"Category": ["clause1", "clause2"], ...}
    
    Returns:
        dict: Summary with structure:
              {
                  "total_clauses": 10,
                  "categories": {
                      "Termination": 3,
                      "Liability": 2,
                      ...
                  }
              }
    
    Example:
        clauses = {"Termination": ["...", "..."], "Payment": ["..."]}
        summary = create_clauses_summary(clauses)
        # Result: {"total_clauses": 3, "categories": {"Termination": 2, "Payment": 1}}
    """
    
    # Handle None or empty clauses
    if not clauses:
        return {
            'total_clauses': 0,
            'categories': {}
        }
    
    # Count clauses in each category
    categories = {}
    total = 0
    
    for category, clause_list in clauses.items():
        if isinstance(clause_list, list):
            count = len(clause_list)
            categories[category] = count
            total += count
    
    return {
        'total_clauses': total,
        'categories': categories
    }


@app.route('/api/document/<int:document_id>', methods=['DELETE'])
def delete_document_route(document_id):
    """
    Delete a document by its ID.
    
    This endpoint deletes both the database record and the physical PDF file
    from the uploads folder. It verifies that the document belongs to the
    logged-in user before deletion.
    
    Authentication:
        Requires user to be logged in (user_id in session).
    
    Authorization:
        User can only delete their own documents.
    
    URL Parameters:
        document_id (int): The ID of the document to delete
    
    Returns:
        Success (200):
            {
                "success": true,
                "message": "Document deleted successfully"
            }
        
        Error (401): Not authenticated
            {"success": false, "error": "Not authenticated. Please log in."}
        
        Error (403): Forbidden (document belongs to another user)
            {"success": false, "error": "You don't have permission to delete this document."}
        
        Error (404): Document not found
            {"success": false, "error": "Document not found."}
    
    Process:
        1. Verify user is authenticated
        2. Fetch document from database
        3. Verify document belongs to the user (authorization)
        4. Delete the physical file from uploads folder
        5. Delete the database record
        6. Return success response
    
    Notes:
        - Physical file deletion happens before database deletion
        - If file deletion fails, the database record is still deleted
          (file might have been manually deleted)
        - Uses transactions implicitly via the database module
    """
    
    # -------------------------------------------------------------------------
    # Step 1: Verify user is authenticated
    # -------------------------------------------------------------------------
    # Supports both cookie session and JWT access token authentication
    
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not authenticated. Please log in or provide a valid access token.'
        }), 401
    
    # -------------------------------------------------------------------------
    # Step 2: Fetch document from database
    # -------------------------------------------------------------------------
    # We need to verify the document exists and get its file path
    # before we can delete it
    
    document = get_document_by_id(document_id)
    
    if not document:
        return jsonify({
            'success': False,
            'error': 'Document not found.'
        }), 404
    
    # -------------------------------------------------------------------------
    # Step 3: Verify ownership (authorization)
    # -------------------------------------------------------------------------
    # A user should only be able to delete their own documents
    # This is a critical security check to prevent unauthorized deletion
    
    if document['user_id'] != user_id:
        # Log this attempt - could indicate malicious activity
        print(f"⚠ Unauthorized delete attempt: User {user_id} tried to delete document {document_id} owned by user {document['user_id']}")
        
        return jsonify({
            'success': False,
            'error': "You don't have permission to delete this document."
        }), 403  # 403 Forbidden
    
    # -------------------------------------------------------------------------
    # Step 4: Delete the physical file
    # -------------------------------------------------------------------------
    # Get the file path and attempt to delete the file
    # We proceed with database deletion even if file deletion fails
    # (the file might have been manually deleted or moved)
    
    file_path = document.get('file_path')
    file_deleted = False
    
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            file_deleted = True
            print(f"✓ Deleted file: {file_path}")
        except OSError as e:
            # Log the error but continue with database deletion
            print(f"⚠ Could not delete file {file_path}: {e}")
    else:
        print(f"→ File not found on disk (may have been deleted): {file_path}")
    
    # -------------------------------------------------------------------------
    # Step 5: Delete the database record
    # -------------------------------------------------------------------------
    # The delete_document function in database.py also verifies ownership
    # as an additional security measure
    
    deleted = delete_document(document_id, user_id)
    
    if not deleted:
        return jsonify({
            'success': False,
            'error': 'Failed to delete document from database.'
        }), 500
    
    # -------------------------------------------------------------------------
    # Step 6: Return success response
    # -------------------------------------------------------------------------
    
    print(f"✓ Document deleted: ID={document_id}, User={user_id}, File deleted={file_deleted}")
    
    return jsonify({
        'success': True,
        'message': 'Document deleted successfully',
        'details': {
            'document_id': document_id,
            'file_deleted': file_deleted
        }
    }), 200


@app.route('/api/document/<int:document_id>', methods=['GET'])
def get_document_detail(document_id):
    """
    Get detailed information about a specific document.
    
    This endpoint retrieves full details of a document including
    the extracted text and all identified clauses.
    
    Authentication:
        Requires user to be logged in (user_id in session).
    
    Authorization:
        User can only view their own documents.
    
    URL Parameters:
        document_id (int): The ID of the document to retrieve
    
    Returns:
        Success (200):
            {
                "success": true,
                "document": {
                    "id": 1,
                    "filename": "contract.pdf",
                    "original_filename": "My Contract.pdf",
                    "upload_date": "2025-02-06 10:30:00",
                    "extracted_text": "Full text content...",
                    "clauses": {
                        "Termination": ["clause 1", "clause 2"],
                        "Payment": ["clause 3"],
                        ...
                    },
                    "clauses_summary": {...}
                }
            }
        
        Error (401): Not authenticated
        Error (403): Forbidden
        Error (404): Document not found
    """
    
    # Verify authentication (supports both cookie session and JWT access token)
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not authenticated. Please log in or provide a valid access token.'
        }), 401
    
    # Fetch document with ownership check
    document = get_document_by_id(document_id, user_id)
    
    if not document:
        return jsonify({
            'success': False,
            'error': 'Document not found or you do not have access.'
        }), 404
    
    # Create clauses summary
    clauses_summary = create_clauses_summary(document.get('clauses'))
    
    print(f"→ Document detail retrieved: ID={document_id}, User={user_id}")
    
    return jsonify({
        'success': True,
        'document': {
            'id': document['id'],
            'filename': document['filename'],
            'original_filename': document['original_filename'],
            'upload_date': document['upload_date'],
            'extracted_text': document.get('extracted_text', ''),
            'clauses': document.get('clauses', {}),
            'clauses_summary': clauses_summary
        }
    }), 200


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(413)
def file_too_large(error):
    """
    Handle file size limit exceeded error.
    
    This is triggered when an uploaded file exceeds MAX_CONTENT_LENGTH.
    Returns a user-friendly error message.
    """
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 10 MB.'
    }), 413


@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 Not Found errors.
    
    Returns a JSON response instead of HTML for API consistency.
    """
    return jsonify({
        'success': False,
        'error': 'Resource not found.'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle internal server errors.
    
    Logs the error and returns a generic message to the user.
    Never expose internal error details to users in production.
    """
    print(f"✗ Internal Server Error: {error}")
    return jsonify({
        'success': False,
        'error': 'An internal error occurred. Please try again later.'
    }), 500


# =============================================================================
# RUN THE APPLICATION
# =============================================================================

if __name__ == '__main__':
    """
    Main entry point for the ContractIQ Backend application.
    
    This block only executes when the script is run directly:
        python app.py
    
    It does NOT execute when the module is imported by another script
    or when using a WSGI server (like Gunicorn or uWSGI).
    
    Startup Process:
    1. Create required directories (uploads/, instance/)
    2. Initialize the database (create tables if needed)
    3. Start the Flask development server
    """
    
    # -------------------------------------------------------------------------
    # Step 1: Create required directories
    # -------------------------------------------------------------------------
    # Ensure the uploads folder exists for storing PDF files
    # Ensure the instance folder exists for the SQLite database
    
    print("\n" + "=" * 60)
    print("  ContractIQ Backend - Startup")
    print("=" * 60)
    
    # Create uploads directory if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        print(f"✓ Created uploads directory: {UPLOAD_FOLDER}")
    else:
        print(f"✓ Uploads directory exists: {UPLOAD_FOLDER}")
    
    # Create instance directory for SQLite database
    instance_folder = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_folder):
        os.makedirs(instance_folder)
        print(f"✓ Created instance directory: {instance_folder}")
    else:
        print(f"✓ Instance directory exists: {instance_folder}")
    
    # -------------------------------------------------------------------------
    # Step 2: Initialize the database
    # -------------------------------------------------------------------------
    # Create database tables if they don't exist
    # This is safe to call multiple times (uses IF NOT EXISTS)
    
    print("\n→ Initializing database...")
    init_db()
    
    # -------------------------------------------------------------------------
    # Step 3: Start the Flask development server
    # -------------------------------------------------------------------------
    # 
    # ABOUT DEBUG MODE:
    # -----------------
    # debug=True enables several development features:
    # 
    # 1. AUTO-RELOADER: 
    #    - Automatically restarts the server when code changes
    #    - No need to manually restart after editing files
    #    - Great for rapid development iteration
    # 
    # 2. INTERACTIVE DEBUGGER:
    #    - When an error occurs, shows an interactive debugger in the browser
    #    - Allows inspecting variables, running code at the error point
    #    - Shows full stack traces with code context
    # 
    # 3. DETAILED ERROR PAGES:
    #    - Shows detailed error information instead of generic "500 Error"
    #    - Includes the exact line of code that caused the error
    # 
    # ⚠️  SECURITY WARNING:
    #    - NEVER use debug=True in production!
    #    - The debugger allows executing arbitrary Python code
    #    - Exposes sensitive application internals
    #    - For production, use: app.run(debug=False) or a WSGI server
    # 
    # HOST CONFIGURATION:
    # -------------------
    # - host='127.0.0.1' (default): Only accept local connections
    # - host='0.0.0.0': Accept connections from any IP address
    #   This is needed if you want to access the API from:
    #   - Other devices on your network
    #   - A frontend running on a different port
    #   - Docker containers or VMs
    # 
    # PORT CONFIGURATION:
    # -------------------
    # - port=5000: The default Flask port
    # - Change if port 5000 is already in use
    # - Common alternatives: 5001, 8000, 8080
    #
    
    print("\n" + "=" * 60)
    print("  Starting Development Server")
    print("=" * 60)
    print(f"  • API URL:        http://localhost:5000")
    print(f"  • Health Check:   http://localhost:5000/health")
    print(f"  • Upload Folder:  {UPLOAD_FOLDER}")
    print(f"  • Database:       {instance_folder}/contractiq.db")
    print(f"  • Max File Size:  10 MB")
    print(f"  • Debug Mode:     ON (auto-reload enabled)")
    print("=" * 60)
    print("\n  Press Ctrl+C to stop the server\n")
    
    # Start the Flask development server
    app.run(
        debug=True,      # Enable debug mode (auto-reload + debugger)
        host='0.0.0.0',  # Accept connections from any IP
        port=5000        # Run on port 5000
    )

