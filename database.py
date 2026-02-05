# Database configuration and models
# This module handles all SQLite database operations for ContractIQ
# Uses Python's built-in sqlite3 module for database connectivity

import sqlite3
import os
import json
from datetime import datetime

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Database file path - stored in the instance folder for Flask convention
# The instance folder is typically used for deployment-specific files
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'contractiq.db')


def get_db_connection():
    """
    Create and return a database connection.
    
    This function establishes a connection to the SQLite database.
    - Row factory is set to sqlite3.Row to enable column access by name
    - This allows us to access results like dictionaries (row['column_name'])
    
    Returns:
        sqlite3.Connection: A connection object to the database
    
    Example:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM users")
        conn.close()
    """
    # Ensure the instance directory exists before connecting
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Create connection with row factory for dict-like access
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    # Enable foreign key support (disabled by default in SQLite)
    conn.execute("PRAGMA foreign_keys = ON")
    
    return conn


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_db():
    """
    Initialize the database by creating all required tables.
    
    This function should be called when the application starts.
    It creates the following tables if they don't already exist:
    - users: Stores user account information
    - documents: Stores uploaded contract documents and extracted data
    
    The function uses 'IF NOT EXISTS' to prevent errors if tables already exist.
    This makes it safe to call multiple times (idempotent).
    
    Returns:
        bool: True if initialization was successful
    
    Example:
        if init_db():
            print("Database ready!")
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # ---------------------------------------------------------------------
        # USERS TABLE
        # ---------------------------------------------------------------------
        # Stores user authentication and profile information
        # - id: Unique identifier, auto-incremented by SQLite
        # - username: User's login name, must be unique
        # - email: User's email address, must be unique
        # - password_hash: Hashed password (never store plain text passwords!)
        # - role: User's permission level (admin/lawyer/client)
        # - created_at: Timestamp when the account was created
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'client' CHECK(role IN ('admin', 'lawyer', 'client')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ---------------------------------------------------------------------
        # DOCUMENTS TABLE
        # ---------------------------------------------------------------------
        # Stores uploaded PDF documents and their extracted content
        # - id: Unique identifier for each document
        # - user_id: Links to the user who uploaded the document (foreign key)
        # - filename: System-generated unique filename (for storage)
        # - original_filename: The original name of the uploaded file
        # - file_path: Full path to where the PDF is stored on disk
        # - extracted_text: The full text content extracted from the PDF
        # - clauses: JSON string containing identified contract clauses
        # - upload_date: When the document was uploaded
        # 
        # ON DELETE CASCADE: If a user is deleted, their documents are also deleted
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                extracted_text TEXT,
                clauses TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for faster queries on frequently searched columns
        # Indexes speed up SELECT queries but slightly slow down INSERT/UPDATE
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        
        # Commit all changes to the database
        conn.commit()
        print(f"✓ Database initialized successfully at: {DATABASE_PATH}")
        return True
        
    except sqlite3.Error as e:
        # If anything goes wrong, print the error
        print(f"✗ Database initialization error: {e}")
        return False
        
    finally:
        # Always close the connection, even if an error occurred
        conn.close()


# =============================================================================
# USER MANAGEMENT FUNCTIONS
# =============================================================================

def create_user(username, email, password_hash, role='client'):
    """
    Create a new user account in the database.
    
    This function inserts a new user record with the provided information.
    The password should already be hashed before calling this function!
    Never pass plain-text passwords to this function.
    
    Args:
        username (str): Unique username for the account
        email (str): User's email address (must be unique)
        password_hash (str): Pre-hashed password (use Werkzeug's generate_password_hash)
        role (str): User's role - 'admin', 'lawyer', or 'client' (default: 'client')
    
    Returns:
        int: The ID of the newly created user, or None if creation failed
    
    Raises:
        sqlite3.IntegrityError: If username or email already exists
    
    Example:
        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash('mypassword')
        user_id = create_user('john_doe', 'john@example.com', hashed, 'lawyer')
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, role))
        
        conn.commit()
        
        # lastrowid gives us the ID of the just-inserted row
        user_id = cursor.lastrowid
        print(f"✓ User created successfully: {username} (ID: {user_id})")
        return user_id
        
    except sqlite3.IntegrityError as e:
        # This happens if username or email already exists (UNIQUE constraint)
        print(f"✗ User creation failed - duplicate entry: {e}")
        return None
        
    except sqlite3.Error as e:
        print(f"✗ User creation error: {e}")
        return None
        
    finally:
        conn.close()


def get_user_by_username(username):
    """
    Retrieve a user record by their username.
    
    This function is typically used during login to fetch the user's
    stored password hash for verification.
    
    Args:
        username (str): The username to search for
    
    Returns:
        dict: User data as a dictionary with keys:
              - id, username, email, password_hash, role, created_at
              Returns None if user not found
    
    Example:
        user = get_user_by_username('john_doe')
        if user:
            print(f"Found user: {user['email']}")
    """
    conn = get_db_connection()
    
    try:
        cursor = conn.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        )
        row = cursor.fetchone()
        
        # Convert Row object to dictionary, or return None if not found
        if row:
            return dict(row)
        return None
        
    except sqlite3.Error as e:
        print(f"✗ Error fetching user by username: {e}")
        return None
        
    finally:
        conn.close()


def get_user_by_id(user_id):
    """
    Retrieve a user record by their ID.
    
    This function is useful for fetching user details when you have
    the user's ID (e.g., from a JWT token or session).
    
    Args:
        user_id (int): The unique ID of the user
    
    Returns:
        dict: User data as a dictionary (without password_hash for security)
              Returns None if user not found
    
    Example:
        user = get_user_by_id(1)
        if user:
            print(f"User role: {user['role']}")
    """
    conn = get_db_connection()
    
    try:
        # Note: We exclude password_hash from the result for security
        cursor = conn.execute(
            'SELECT id, username, email, role, created_at FROM users WHERE id = ?',
            (user_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
        
    except sqlite3.Error as e:
        print(f"✗ Error fetching user by ID: {e}")
        return None
        
    finally:
        conn.close()


# =============================================================================
# DOCUMENT MANAGEMENT FUNCTIONS
# =============================================================================

def save_document(user_id, filename, original_filename, file_path, extracted_text=None, clauses=None):
    """
    Save a new document record to the database.
    
    This function stores metadata about an uploaded PDF document,
    including the extracted text and identified clauses.
    
    Args:
        user_id (int): ID of the user who uploaded the document
        filename (str): System-generated unique filename (e.g., UUID-based)
        original_filename (str): Original name of the uploaded file
        file_path (str): Full filesystem path where the PDF is stored
        extracted_text (str, optional): Text content extracted from the PDF
        clauses (dict/list, optional): Identified clauses (will be JSON-serialized)
    
    Returns:
        int: The ID of the saved document, or None if save failed
    
    Example:
        doc_id = save_document(
            user_id=1,
            filename='abc123.pdf',
            original_filename='Contract_2024.pdf',
            file_path='/uploads/abc123.pdf',
            extracted_text='This agreement is made between...',
            clauses={'confidentiality': 'Section 5...', 'termination': 'Section 8...'}
        )
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Convert clauses dict/list to JSON string for storage
        # SQLite doesn't have a native JSON type, so we store as TEXT
        clauses_json = json.dumps(clauses) if clauses else None
        
        cursor.execute('''
            INSERT INTO documents (user_id, filename, original_filename, file_path, extracted_text, clauses)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, filename, original_filename, file_path, extracted_text, clauses_json))
        
        conn.commit()
        
        doc_id = cursor.lastrowid
        print(f"✓ Document saved: {original_filename} (ID: {doc_id})")
        return doc_id
        
    except sqlite3.Error as e:
        print(f"✗ Document save error: {e}")
        return None
        
    finally:
        conn.close()


def get_user_documents(user_id):
    """
    Retrieve all documents uploaded by a specific user.
    
    Returns documents in reverse chronological order (newest first).
    The clauses field is automatically parsed from JSON back to Python dict.
    
    Args:
        user_id (int): ID of the user whose documents to retrieve
    
    Returns:
        list: List of document dictionaries, each containing:
              - id, filename, original_filename, file_path, 
              - extracted_text, clauses (as dict), upload_date
              Returns empty list if no documents or error
    
    Example:
        docs = get_user_documents(1)
        for doc in docs:
            print(f"Document: {doc['original_filename']}, Uploaded: {doc['upload_date']}")
    """
    conn = get_db_connection()
    
    try:
        cursor = conn.execute('''
            SELECT * FROM documents 
            WHERE user_id = ? 
            ORDER BY upload_date DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        
        # Convert rows to list of dictionaries and parse JSON clauses
        documents = []
        for row in rows:
            doc = dict(row)
            # Parse the clauses JSON string back to Python dict/list
            if doc['clauses']:
                try:
                    doc['clauses'] = json.loads(doc['clauses'])
                except json.JSONDecodeError:
                    doc['clauses'] = None
            documents.append(doc)
        
        return documents
        
    except sqlite3.Error as e:
        print(f"✗ Error fetching user documents: {e}")
        return []
        
    finally:
        conn.close()


def get_document_by_id(document_id, user_id=None):
    """
    Retrieve a single document by its ID.
    
    Optionally verify that the document belongs to a specific user
    for security purposes.
    
    Args:
        document_id (int): The ID of the document to retrieve
        user_id (int, optional): If provided, verify document ownership
    
    Returns:
        dict: Document data, or None if not found (or not owned by user)
    
    Example:
        doc = get_document_by_id(5, user_id=1)
        if doc:
            print(doc['extracted_text'])
    """
    conn = get_db_connection()
    
    try:
        if user_id:
            # Security check: only return if user owns the document
            cursor = conn.execute(
                'SELECT * FROM documents WHERE id = ? AND user_id = ?',
                (document_id, user_id)
            )
        else:
            cursor = conn.execute(
                'SELECT * FROM documents WHERE id = ?',
                (document_id,)
            )
        
        row = cursor.fetchone()
        
        if row:
            doc = dict(row)
            # Parse clauses JSON
            if doc['clauses']:
                try:
                    doc['clauses'] = json.loads(doc['clauses'])
                except json.JSONDecodeError:
                    doc['clauses'] = None
            return doc
        return None
        
    except sqlite3.Error as e:
        print(f"✗ Error fetching document: {e}")
        return None
        
    finally:
        conn.close()


def delete_document(document_id, user_id):
    """
    Delete a document from the database.
    
    This function includes an ownership check - it will only delete
    the document if it belongs to the specified user. This prevents
    users from deleting other users' documents.
    
    Note: This only deletes the database record. The actual PDF file
    should be deleted separately by the calling code.
    
    Args:
        document_id (int): ID of the document to delete
        user_id (int): ID of the user requesting deletion (for ownership verification)
    
    Returns:
        bool: True if document was deleted, False otherwise
    
    Example:
        if delete_document(5, user_id=1):
            # Also delete the physical file
            os.remove(file_path)
    """
    conn = get_db_connection()
    
    try:
        # First, get the document to verify ownership and get file path
        cursor = conn.execute(
            'SELECT file_path FROM documents WHERE id = ? AND user_id = ?',
            (document_id, user_id)
        )
        doc = cursor.fetchone()
        
        if not doc:
            print(f"✗ Document not found or not owned by user")
            return False
        
        # Delete the database record
        cursor = conn.execute(
            'DELETE FROM documents WHERE id = ? AND user_id = ?',
            (document_id, user_id)
        )
        
        conn.commit()
        
        # rowcount tells us how many rows were affected
        if cursor.rowcount > 0:
            print(f"✓ Document deleted (ID: {document_id})")
            return True
        return False
        
    except sqlite3.Error as e:
        print(f"✗ Document deletion error: {e}")
        return False
        
    finally:
        conn.close()


# =============================================================================
# DASHBOARD & STATISTICS FUNCTIONS
# =============================================================================

def get_dashboard_stats(user_id):
    """
    Get statistics for a user's dashboard.
    
    This function aggregates data to provide an overview of the user's
    document library and activity.
    
    Args:
        user_id (int): ID of the user
    
    Returns:
        dict: Dashboard statistics containing:
              - total_documents: Total number of uploaded documents
              - recent_documents: List of 5 most recent documents
              - total_clauses_extracted: Count of documents with extracted clauses
              - account_created: When the user account was created
    
    Example:
        stats = get_dashboard_stats(1)
        print(f"You have {stats['total_documents']} documents")
    """
    conn = get_db_connection()
    
    try:
        stats = {}
        
        # Count total documents
        cursor = conn.execute(
            'SELECT COUNT(*) as count FROM documents WHERE user_id = ?',
            (user_id,)
        )
        stats['total_documents'] = cursor.fetchone()['count']
        
        # Count documents with extracted clauses
        cursor = conn.execute(
            'SELECT COUNT(*) as count FROM documents WHERE user_id = ? AND clauses IS NOT NULL',
            (user_id,)
        )
        stats['total_clauses_extracted'] = cursor.fetchone()['count']
        
        # Get 5 most recent documents (just basic info, not full text)
        cursor = conn.execute('''
            SELECT id, original_filename, upload_date 
            FROM documents 
            WHERE user_id = ? 
            ORDER BY upload_date DESC 
            LIMIT 5
        ''', (user_id,))
        stats['recent_documents'] = [dict(row) for row in cursor.fetchall()]
        
        # Get user account creation date
        cursor = conn.execute(
            'SELECT created_at FROM users WHERE id = ?',
            (user_id,)
        )
        user_row = cursor.fetchone()
        stats['account_created'] = user_row['created_at'] if user_row else None
        
        return stats
        
    except sqlite3.Error as e:
        print(f"✗ Error fetching dashboard stats: {e}")
        return {
            'total_documents': 0,
            'recent_documents': [],
            'total_clauses_extracted': 0,
            'account_created': None
        }
        
    finally:
        conn.close()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def user_exists(username=None, email=None):
    """
    Check if a user with the given username or email already exists.
    
    Useful for validation before attempting to create a new user.
    
    Args:
        username (str, optional): Username to check
        email (str, optional): Email to check
    
    Returns:
        bool: True if user exists, False otherwise
    
    Example:
        if user_exists(username='john_doe'):
            print("Username already taken!")
    """
    conn = get_db_connection()
    
    try:
        if username:
            cursor = conn.execute(
                'SELECT 1 FROM users WHERE username = ?',
                (username,)
            )
            if cursor.fetchone():
                return True
        
        if email:
            cursor = conn.execute(
                'SELECT 1 FROM users WHERE email = ?',
                (email,)
            )
            if cursor.fetchone():
                return True
        
        return False
        
    except sqlite3.Error as e:
        print(f"✗ Error checking user existence: {e}")
        return False
        
    finally:
        conn.close()


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

# When this module is run directly (not imported), initialize the database
if __name__ == '__main__':
    print("Initializing ContractIQ Database...")
    print("=" * 50)
    init_db()
    print("=" * 50)
    print("Database setup complete!")
