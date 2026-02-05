# ContractIQ API Documentation

**Base URL:** `http://localhost:5000`

---

## Authentication

The API supports two authentication methods (use either one):

1. **Session Cookie** - Automatically set after login (for web browsers)
2. **Access Token** - Pass in header: `Authorization: Bearer <token>`

---

## Endpoints

### 1. Register User

```
POST /api/register
Content-Type: application/json
```

**Request:**
```json
{
    "username": "string",     // Required: 3-50 chars, alphanumeric + underscore
    "email": "string",        // Required: valid email
    "password": "string",     // Required: min 6 chars
    "role": "string"          // Optional: "admin" | "lawyer" | "client" (default: "client")
}
```

**Response (201):**
```json
{
    "success": true,
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "john_doe",
        "role": "client"
    }
}
```

**Errors:**
- `400` - Validation error (missing/invalid fields)
- `409` - Username or email already exists

---

### 2. Login

```
POST /api/login
Content-Type: application/json
```

**Request:**
```json
{
    "email": "string",        // Required
    "password": "string"      // Required
}
```

**Response (200):**
```json
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
```

**Errors:**
- `400` - Missing email or password
- `401` - Invalid email or password

> **Note:** Save `access_token` for authenticated requests. Token expires in 24 hours.

---

### 3. Logout

```
POST /api/logout
```

**Response (200):**
```json
{
    "success": true,
    "message": "Logged out successfully"
}
```

---

### 4. Get Profile

```
GET /api/profile
Authorization: Bearer <token>
```

**Response (200):**
```json
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
```

---

### 5. Get Dashboard

```
GET /api/dashboard
Authorization: Bearer <token>
```

**Response (200):**
```json
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
        "total_clauses_extracted": 15,
        "recent_documents": [
            {
                "id": 5,
                "original_filename": "contract.pdf",
                "upload_date": "2025-02-06 14:30:00"
            }
        ],
        "account_created": "2025-02-01 10:00:00"
    }
}
```

---

### 6. Upload Document

```
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request:**
- `file`: PDF file (max 10 MB)

**Response (200):**
```json
{
    "success": true,
    "message": "Document uploaded and processed successfully",
    "document": {
        "id": 1,
        "filename": "uuid_timestamp.pdf",
        "original_filename": "contract.pdf",
        "upload_date": "2025-02-06 14:30:52",
        "clauses": {
            "Termination": ["clause text 1", "clause text 2"],
            "Payment": ["clause text"],
            "Confidentiality": [],
            "Liability": ["clause text"],
            "Intellectual Property": []
        },
        "clauses_summary": {
            "total_clauses": 4,
            "categories": {
                "Termination": 2,
                "Payment": 1,
                "Liability": 1
            }
        },
        "text_preview": "First 500 characters...",
        "text_length": 5432
    }
}
```

**Errors:**
- `400` - No file / invalid file type (only PDF allowed)
- `401` - Not authenticated
- `413` - File too large (max 10 MB)

---

### 7. Get All Documents

```
GET /api/documents
Authorization: Bearer <token>
```

**Response (200):**
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
                    "Termination": 2,
                    "Payment": 1
                }
            },
            "has_extracted_text": true
        }
    ],
    "total_count": 1
}
```

---

### 8. Get Document Details

```
GET /api/document/{id}
Authorization: Bearer <token>
```

**Response (200):**
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
            "Payment": ["clause 3"],
            "Confidentiality": [],
            "Liability": [],
            "Intellectual Property": []
        },
        "clauses_summary": {
            "total_clauses": 3,
            "categories": {
                "Termination": 2,
                "Payment": 1
            }
        }
    }
}
```

**Errors:**
- `401` - Not authenticated
- `404` - Document not found or no access

---

### 9. Delete Document

```
DELETE /api/document/{id}
Authorization: Bearer <token>
```

**Response (200):**
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

**Errors:**
- `401` - Not authenticated
- `403` - No permission (not document owner)
- `404` - Document not found

---

## Error Response Format

All errors follow this format:

```json
{
    "success": false,
    "error": "Error message here"
}
```

---

## Clause Categories

Documents are analyzed for these 5 clause types:
- **Termination** - Contract ending conditions
- **Payment** - Financial terms
- **Confidentiality** - Information protection
- **Liability** - Responsibility terms
- **Intellectual Property** - IP ownership

---

## Quick Reference

| Endpoint | Method | Auth Required |
|----------|--------|---------------|
| `/api/register` | POST | No |
| `/api/login` | POST | No |
| `/api/logout` | POST | No |
| `/api/profile` | GET | Yes |
| `/api/dashboard` | GET | Yes |
| `/api/upload` | POST | Yes |
| `/api/documents` | GET | Yes |
| `/api/document/{id}` | GET | Yes |
| `/api/document/{id}` | DELETE | Yes |
| `/health` | GET | No |
