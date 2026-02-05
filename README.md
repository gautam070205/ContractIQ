# 📄 ContractIQ Backend

> **Smart Contract Analysis API** - Upload PDF contracts and automatically extract key clauses using AI-powered text analysis.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Technology Stack](#-technology-stack)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Future Enhancements](#-future-enhancements)

---

## 🎯 Project Overview

**ContractIQ** is a Flask-based REST API that helps legal professionals, businesses, and individuals analyze contract documents automatically. 

### What does it do?

1. **📤 Upload PDF Contracts** - Securely upload contract documents in PDF format
2. **📝 Extract Text** - Automatically extract text content from PDFs using PyPDF2
3. **🔍 Identify Clauses** - Use keyword matching to identify and categorize important contract clauses
4. **📊 Organize Results** - Categorize clauses into 5 key categories:
   - ⚖️ **Termination** - How and when the contract can be ended
   - 💰 **Payment** - Financial terms and obligations
   - 🔒 **Confidentiality** - Information protection requirements
   - ⚠️ **Liability** - Responsibility and indemnification terms
   - 💡 **Intellectual Property** - IP ownership and rights

### Who is it for?

- 👨‍⚖️ **Lawyers** - Quickly review contracts and identify key terms
- 🏢 **Businesses** - Analyze vendor contracts and agreements
- 👨‍💼 **Freelancers** - Understand client contracts before signing
- 📚 **Students** - Learn about contract structure and key clauses

---

## 🛠 Technology Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Programming Language | 3.8+ |
| **Flask** | Web Framework | 3.0.0 |
| **Flask-CORS** | Cross-Origin Resource Sharing | 4.0.0 |
| **SQLite** | Database | Built-in |
| **PyPDF2** | PDF Text Extraction | 3.0.1 |
| **Werkzeug** | Password Hashing & Security | 3.0.1 || **PyJWT** | JWT Access Token Authentication | 2.8.0 |
### Why these technologies?

- **Flask** - Lightweight, easy to learn, perfect for REST APIs
- **SQLite** - No separate database server needed, portable
- **PyPDF2** - Reliable PDF processing in pure Python
- **Werkzeug** - Industry-standard password hashing (PBKDF2)

---

## ✨ Features

### 🔐 Authentication System
- User registration with role-based access (admin/lawyer/client)
- Secure login with **email and password**
- **Dual authentication support:**
  - Session-based (cookies) for web browsers
  - JWT access tokens for API/mobile apps
- Profile management

### 📄 Document Management
- PDF upload with automatic text extraction
- Clause identification and categorization
- Document storage and retrieval
- Secure document deletion (ownership verified)

### 📊 Dashboard & Analytics
- Document statistics
- Recent uploads tracking
- Clause extraction summaries

---

## 📌 Prerequisites

Before you begin, ensure you have the following installed:

### Required

| Software | Minimum Version | Check Command |
|----------|-----------------|---------------|
| Python | 3.8+ | `python --version` |
| pip | Latest | `pip --version` |

### Optional (Recommended)

| Software | Purpose |
|----------|---------|
| VS Code | Code editor |
| Postman | API testing |
| Git | Version control |

---

## 🚀 Installation

### Step 1: Get the Project

**Option A: Clone from Git (if using version control)**
```bash
git clone https://github.com/yourusername/contractiq-backend.git
cd contractiq-backend
```

**Option B: Download and Extract**
```bash
# Download the project folder and navigate to it
cd path/to/contractiq-backend
```

### Step 2: Create Virtual Environment

A virtual environment keeps project dependencies isolated from other Python projects.

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> 💡 **Tip:** You'll know it's activated when you see `(venv)` at the start of your terminal prompt.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- Flask-CORS (cross-origin support)
- PyPDF2 (PDF processing)
- Werkzeug (security utilities)

### Step 4: Run the Application

```bash
python app.py
```

You should see:
```
============================================================
  ContractIQ Backend - Startup
============================================================
✓ Uploads directory exists: .../uploads
✓ Instance directory exists: .../instance

→ Initializing database...
✓ Database initialized successfully

============================================================
  Starting Development Server
============================================================
  • API URL:        http://localhost:5000
  • Health Check:   http://localhost:5000/health
  • Debug Mode:     ON (auto-reload enabled)
============================================================

  Press Ctrl+C to stop the server
```

### Step 5: Verify Installation

Open your browser and visit:
- **http://localhost:5000** - Should show API info
- **http://localhost:5000/health** - Should show `{"status": "healthy"}`

🎉 **Congratulations!** Your ContractIQ backend is running!

---

## 📚 API Documentation

### Base URL
```
http://localhost:5000
```

### Authentication Endpoints

#### 1️⃣ Register User

**Endpoint:** `POST /api/register`

**Description:** Create a new user account

**Request Body:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123",
    "role": "lawyer"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | 3-50 chars, alphanumeric + underscore |
| email | string | Yes | Valid email address |
| password | string | Yes | Minimum 6 characters |
| role | string | No | `admin`, `lawyer`, or `client` (default: `client`) |

**Success Response (201):**
```json
{
    "success": true,
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "john_doe",
        "role": "lawyer"
    }
}
```

**Error Response (409):**
```json
{
    "success": false,
    "error": "Username already exists. Please choose a different username."
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","email":"john@example.com","password":"secret123","role":"lawyer"}'
```

---

#### 2️⃣ Login

**Endpoint:** `POST /api/login`

**Description:** Authenticate with email and get session cookie + JWT access token

**Request Body:**
```json
{
    "email": "john@example.com",
    "password": "securepassword123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's registered email address |
| password | string | Yes | User's password |

**Success Response (200):**
```json
{
    "success": true,
    "message": "Login successful",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "lawyer"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Response (401):**
```json
{
    "success": false,
    "error": "Invalid email or password"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"secret123"}' \
  -c cookies.txt
```

> 💡 **Note:** The response includes both:
> - **Session cookie** - Automatically saved with `-c cookies.txt` for browser-like requests
> - **Access token** - Use in `Authorization: Bearer <token>` header for API/mobile requests

---

### 🔑 Using Access Tokens

After login, you can authenticate requests using either method:

**Method 1: Session Cookie (Web Browsers)**
```bash
curl -X GET http://localhost:5000/api/documents -b cookies.txt
```

**Method 2: Access Token (API/Mobile Apps)**
```bash
curl -X GET http://localhost:5000/api/documents \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

> ⏰ **Token Expiration:** Access tokens expire after 24 hours. Re-login to get a new token.

---

#### 3️⃣ Logout

**Endpoint:** `POST /api/logout`

**Description:** End the current session

**Success Response (200):**
```json
{
    "success": true,
    "message": "Logged out successfully"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/logout \
  -b cookies.txt
```

---

### Document Endpoints

#### 4️⃣ Upload Document

**Endpoint:** `POST /api/upload`

**Description:** Upload a PDF contract for analysis

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | PDF file (max 10 MB) |

**Success Response (200):**
```json
{
    "success": true,
    "message": "Document uploaded and processed successfully",
    "document": {
        "id": 1,
        "filename": "uuid_20250206_143052.pdf",
        "original_filename": "contract.pdf",
        "upload_date": "2025-02-06 14:30:52",
        "clauses": {
            "Termination": ["Either party may terminate with 30 days notice."],
            "Payment": ["Payment is due within 30 days of invoice."],
            "Confidentiality": ["All information shared is confidential."],
            "Liability": ["Liability is limited to the contract value."],
            "Intellectual Property": []
        },
        "clauses_summary": {
            "total_clauses": 4,
            "categories": {
                "Termination": 1,
                "Payment": 1,
                "Confidentiality": 1,
                "Liability": 1
            }
        },
        "text_preview": "This agreement is entered into...",
        "text_length": 5432
    }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -b cookies.txt \
  -F "file=@/path/to/contract.pdf"
```

**PowerShell Example:**
```powershell
$form = @{
    file = Get-Item -Path "C:\path\to\contract.pdf"
}
Invoke-RestMethod -Uri "http://localhost:5000/api/upload" `
    -Method Post `
    -Form $form `
    -WebSession $session
```

---

#### 5️⃣ Get All Documents

**Endpoint:** `GET /api/documents`

**Description:** List all documents for the logged-in user

**Success Response (200):**
```json
{
    "success": true,
    "documents": [
        {
            "id": 1,
            "filename": "uuid_timestamp.pdf",
            "original_filename": "contract.pdf",
            "upload_date": "2025-02-06 14:30:52",
            "clauses_summary": {
                "total_clauses": 4,
                "categories": {
                    "Termination": 1,
                    "Payment": 1
                }
            },
            "has_extracted_text": true
        }
    ],
    "total_count": 1
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:5000/api/documents \
  -b cookies.txt
```

---

#### 6️⃣ Get Document Details

**Endpoint:** `GET /api/document/<id>`

**Description:** Get full details of a specific document

**Success Response (200):**
```json
{
    "success": true,
    "document": {
        "id": 1,
        "filename": "uuid_timestamp.pdf",
        "original_filename": "contract.pdf",
        "upload_date": "2025-02-06 14:30:52",
        "extracted_text": "Full text content of the document...",
        "clauses": {
            "Termination": ["clause 1", "clause 2"],
            "Payment": ["clause 3"]
        },
        "clauses_summary": {
            "total_clauses": 3,
            "categories": {}
        }
    }
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:5000/api/document/1 \
  -b cookies.txt
```

---

#### 7️⃣ Delete Document

**Endpoint:** `DELETE /api/document/<id>`

**Description:** Delete a document (must be owner)

**Success Response (200):**
```json
{
    "success": true,
    "message": "Document deleted successfully",
    "details": {
        "document_id": 1,
        "file_deleted": true
    }
}
```

**Error Response (403):**
```json
{
    "success": false,
    "error": "You don't have permission to delete this document."
}
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:5000/api/document/1 \
  -b cookies.txt
```

---

### Dashboard Endpoint

#### 8️⃣ Get Dashboard

**Endpoint:** `GET /api/dashboard`

**Description:** Get user stats and recent activity

**Success Response (200):**
```json
{
    "success": true,
    "user": {
        "username": "john_doe",
        "email": "john@example.com",
        "role": "lawyer"
    },
    "stats": {
        "total_documents": 5,
        "recent_uploads": 2,
        "total_clauses_extracted": 4,
        "recent_documents": [
            {"id": 5, "original_filename": "latest.pdf", "upload_date": "2025-02-06"}
        ],
        "account_created": "2025-02-01 10:00:00"
    }
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:5000/api/dashboard \
  -b cookies.txt
```

---

## 📁 Project Structure

```
contractiq-backend/
│
├── 📄 app.py                 # Main Flask application
│                              # - Route definitions
│                              # - Configuration
│                              # - Error handlers
│
├── 📄 database.py            # Database operations
│                              # - SQLite connection
│                              # - User CRUD operations
│                              # - Document CRUD operations
│
├── 📄 pdf_processor.py       # PDF text extraction
│                              # - Extract text from PDFs
│                              # - Handle errors (corrupted, encrypted)
│                              # - Clean extracted text
│
├── 📄 clause_extractor.py    # Clause identification
│                              # - Keyword matching
│                              # - Sentence splitting
│                              # - Clause categorization
│
├── 📄 requirements.txt       # Python dependencies
│
├── 📄 README.md              # This file!
│
├── 📄 .gitignore             # Git ignore rules
│
├── 📁 uploads/               # Uploaded PDF storage
│   └── .gitkeep
│
└── 📁 instance/              # SQLite database location
    └── contractiq.db         # Database file (created on first run)
```

### File Descriptions

| File | Purpose |
|------|---------|
| `app.py` | Main application file. Contains all API routes, configuration, and the Flask app instance. |
| `database.py` | Handles all database operations using SQLite. Creates tables, manages users and documents. |
| `pdf_processor.py` | Extracts text from PDF files using PyPDF2. Handles errors gracefully. |
| `clause_extractor.py` | Analyzes text to identify contract clauses using keyword matching. |
| `requirements.txt` | Lists all Python packages needed to run the project. |

---

## 🧪 Testing

### Using Postman (Recommended for Beginners)

1. **Download Postman:** https://www.postman.com/downloads/
2. **Import the collection** or create requests manually
3. **Set up environment variables** for `base_url = http://localhost:5000`

#### Testing Flow:

```
1. Register → 2. Login → 3. Upload PDF → 4. View Documents → 5. Delete → 6. Logout
```

### Using cURL

**Complete Testing Script (PowerShell):**

```powershell
# 1. Register a new user
curl -X POST http://localhost:5000/api/register `
  -H "Content-Type: application/json" `
  -d '{"username":"testuser","email":"test@example.com","password":"test123"}'

# 2. Login with email (save session cookie)
# Response includes access_token for API/mobile use
curl -X POST http://localhost:5000/api/login `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","password":"test123"}' `
  -c cookies.txt

# 3. Check dashboard (using cookie)
curl -X GET http://localhost:5000/api/dashboard -b cookies.txt

# 3b. Or use access token instead of cookie
# curl -X GET http://localhost:5000/api/dashboard -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 4. Upload a PDF (replace path)
curl -X POST http://localhost:5000/api/upload `
  -b cookies.txt `
  -F "file=@C:\path\to\test.pdf"

# 5. Get all documents
curl -X GET http://localhost:5000/api/documents -b cookies.txt

# 6. Get specific document (replace ID)
curl -X GET http://localhost:5000/api/document/1 -b cookies.txt

# 7. Delete document
curl -X DELETE http://localhost:5000/api/document/1 -b cookies.txt

# 8. Logout
curl -X POST http://localhost:5000/api/logout -b cookies.txt
```

### Using Python requests

```python
import requests

base_url = "http://localhost:5000"
session = requests.Session()

# Register
response = session.post(f"{base_url}/api/register", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "test123"
})
print("Register:", response.json())

# Login with email (session-based)
response = session.post(f"{base_url}/api/login", json={
    "email": "test@example.com",
    "password": "test123"
})
login_data = response.json()
print("Login:", login_data)

# Get the access token for API/mobile use
access_token = login_data.get("access_token")
print("Access Token:", access_token)

# Upload PDF (using session cookie)
with open("contract.pdf", "rb") as f:
    response = session.post(f"{base_url}/api/upload", files={"file": f})
print("Upload:", response.json())

# Get documents (using session cookie)
response = session.get(f"{base_url}/api/documents")
print("Documents:", response.json())

# Alternative: Use access token instead of session
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{base_url}/api/documents", headers=headers)
print("Documents (via token):", response.json())
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### ❌ "Module not found" error

**Problem:** `ModuleNotFoundError: No module named 'flask'`

**Solution:** 
```bash
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

---

#### ❌ Port 5000 already in use

**Problem:** `OSError: [Errno 98] Address already in use`

**Solution:**
```python
# In app.py, change the port:
app.run(debug=True, host='0.0.0.0', port=5001)  # Use port 5001 instead
```

Or kill the process using port 5000:
```powershell
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

---

#### ❌ CORS errors in browser

**Problem:** `Access to fetch blocked by CORS policy`

**Solution:** The backend already has CORS configured. Make sure your frontend is running on `http://localhost:3000`. If using a different port, update `app.py`:

```python
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://localhost:YOUR_PORT"])
```

---

#### ❌ PDF text extraction returns empty

**Problem:** Uploaded PDF shows no extracted text

**Possible Causes:**
1. **Scanned PDF** - The PDF is an image, not text. PyPDF2 cannot extract text from images.
2. **Encrypted PDF** - The PDF is password-protected.
3. **Corrupted PDF** - The file is damaged.

**Solution:** Use PDFs with actual text content, not scanned documents.

---

#### ❌ Database errors

**Problem:** `sqlite3.OperationalError: no such table: users`

**Solution:** Delete the database and restart:
```bash
# Delete the database file
rm instance/contractiq.db  # macOS/Linux
del instance\contractiq.db  # Windows

# Restart the app (tables will be created)
python app.py
```

---

#### ❌ Session not persisting

**Problem:** Login works but subsequent requests say "Not authenticated"

**Solution 1: Use cookies properly**
```bash
# Save cookies on login
curl -X POST http://localhost:5000/api/login ... -c cookies.txt

# Include cookies in subsequent requests
curl -X GET http://localhost:5000/api/dashboard -b cookies.txt
```

**Solution 2: Use access token instead**
```bash
# Login and save the access_token from the response
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Use the token in subsequent requests
curl -X GET http://localhost:5000/api/dashboard \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

For Postman: Enable "Send cookies" in settings, or use the Authorization tab with Bearer Token.

---

## 🚀 Future Enhancements

Here are planned features for future versions:

### Version 2.0

- [ ] 🤖 **AI-Powered Analysis** - Use OpenAI/Claude for smarter clause extraction
- [ ] 📧 **Email Verification** - Verify user emails on registration
- [x] 🔑 **JWT Authentication** - ✅ Token-based auth for mobile apps (COMPLETED!)
- [ ] 📱 **React Frontend** - Modern web interface

### Version 3.0

- [ ] 📊 **Advanced Analytics** - Charts and visualizations
- [ ] 🔔 **Notifications** - Alert users about contract deadlines
- [ ] 👥 **Team Sharing** - Share documents with team members
- [ ] 📝 **Document Comparison** - Compare two contracts side by side

### Version 4.0

- [ ] 🌍 **Multi-language Support** - Analyze contracts in multiple languages
- [ ] 📄 **Word/DOCX Support** - Support more document formats
- [ ] 🔗 **API Integrations** - Connect with DocuSign, Dropbox, etc.
- [ ] ☁️ **Cloud Deployment** - Deploy to AWS/Azure/GCP

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Support

If you have any questions or run into issues:

1. 📖 Check this README first
2. 🔍 Search existing issues
3. 🆕 Create a new issue with details

---

**Made with ❤️ for the legal tech community**
