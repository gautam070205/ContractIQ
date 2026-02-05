# PDF processing utilities
# This module handles PDF text extraction using PyPDF2 library
# It provides robust error handling for various PDF-related issues

import os
import re
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError, EmptyFileError

# =============================================================================
# PDF TEXT EXTRACTION
# =============================================================================

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a PDF file.
    
    This function reads a PDF file and extracts all text content from every page.
    The extracted text is cleaned and normalized for further processing.
    
    Process:
    1. Validate that the file exists
    2. Open and read the PDF using PyPDF2
    3. Check if PDF is encrypted (password-protected)
    4. Iterate through all pages and extract text
    5. Clean the extracted text (remove extra whitespace)
    6. Return the combined text from all pages
    
    Args:
        pdf_path (str): Absolute or relative path to the PDF file
    
    Returns:
        str: Cleaned extracted text from all pages combined
        None: If extraction fails for any reason (with error logged)
    
    Error Handling:
        - FileNotFoundError: PDF file doesn't exist at the specified path
        - EmptyFileError: PDF file is empty (0 bytes)
        - PdfReadError: PDF is corrupted or in an invalid format
        - Encrypted PDFs: Password-protected files cannot be read
    
    Example:
        text = extract_text_from_pdf('/path/to/contract.pdf')
        if text:
            print(f"Extracted {len(text)} characters")
        else:
            print("Failed to extract text")
    """
    
    # -------------------------------------------------------------------------
    # Step 1: Validate file exists
    # -------------------------------------------------------------------------
    # Check if the file exists before attempting to read it
    # This provides a clear error message rather than a generic exception
    if not os.path.exists(pdf_path):
        print(f"✗ Error: PDF file not found at path: {pdf_path}")
        return None
    
    # Check if the path points to a file (not a directory)
    if not os.path.isfile(pdf_path):
        print(f"✗ Error: Path is not a file: {pdf_path}")
        return None
    
    # Check file size - empty files will cause issues
    if os.path.getsize(pdf_path) == 0:
        print(f"✗ Error: PDF file is empty (0 bytes): {pdf_path}")
        return None
    
    try:
        # ---------------------------------------------------------------------
        # Step 2: Open and read the PDF
        # ---------------------------------------------------------------------
        # PdfReader is the main class for reading PDF files in PyPDF2
        # It parses the PDF structure and provides access to pages
        print(f"→ Opening PDF: {os.path.basename(pdf_path)}")
        reader = PdfReader(pdf_path)
        
        # ---------------------------------------------------------------------
        # Step 3: Check for encryption
        # ---------------------------------------------------------------------
        # Encrypted PDFs require a password to read content
        # We cannot extract text from password-protected PDFs without the password
        if reader.is_encrypted:
            # Try to decrypt with empty password (some PDFs have empty passwords)
            try:
                # attempt to decrypt with empty password
                decrypt_result = reader.decrypt('')
                if decrypt_result == 0:
                    # Decryption failed - file is truly password-protected
                    print(f"✗ Error: PDF is password-protected and cannot be read: {pdf_path}")
                    return None
                print(f"→ PDF was encrypted but decrypted with empty password")
            except Exception:
                print(f"✗ Error: PDF is encrypted and cannot be decrypted: {pdf_path}")
                return None
        
        # ---------------------------------------------------------------------
        # Step 4: Extract text from all pages
        # ---------------------------------------------------------------------
        # Get the total number of pages in the PDF
        num_pages = len(reader.pages)
        
        # Check if PDF has any pages
        if num_pages == 0:
            print(f"✗ Error: PDF has no pages: {pdf_path}")
            return None
        
        print(f"→ Processing {num_pages} page(s)...")
        
        # List to store text from each page
        all_text = []
        
        # Iterate through each page and extract text
        for page_num in range(num_pages):
            try:
                # Get the page object
                page = reader.pages[page_num]
                
                # Extract text from the page
                # extract_text() returns all text content from the page
                page_text = page.extract_text()
                
                # Some pages might return None or empty string
                if page_text:
                    all_text.append(page_text)
                else:
                    # Page has no extractable text (might be scanned image)
                    print(f"  → Page {page_num + 1}: No extractable text (possibly scanned/image)")
                    
            except Exception as page_error:
                # Log the error but continue with other pages
                print(f"  → Page {page_num + 1}: Error extracting text - {str(page_error)}")
                continue
        
        # ---------------------------------------------------------------------
        # Step 5: Combine and clean the text
        # ---------------------------------------------------------------------
        # Join all page texts with newlines
        combined_text = '\n'.join(all_text)
        
        # Check if we extracted any text
        if not combined_text.strip():
            print(f"✗ Warning: No text could be extracted from PDF (may be scanned/image-based)")
            return None
        
        # Clean the extracted text
        cleaned_text = clean_extracted_text(combined_text)
        
        print(f"✓ Successfully extracted {len(cleaned_text)} characters from {num_pages} page(s)")
        return cleaned_text
        
    # -------------------------------------------------------------------------
    # Error Handling
    # -------------------------------------------------------------------------
    except EmptyFileError:
        # PyPDF2 raises this for empty or nearly empty files
        print(f"✗ Error: PDF file is empty or invalid: {pdf_path}")
        return None
        
    except PdfReadError as e:
        # PyPDF2 raises this for corrupted or malformed PDFs
        print(f"✗ Error: PDF is corrupted or invalid format: {pdf_path}")
        print(f"  Details: {str(e)}")
        return None
        
    except PermissionError:
        # File exists but we don't have permission to read it
        print(f"✗ Error: Permission denied to read PDF: {pdf_path}")
        return None
        
    except Exception as e:
        # Catch any other unexpected errors
        print(f"✗ Unexpected error reading PDF: {pdf_path}")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Details: {str(e)}")
        return None


# =============================================================================
# TEXT CLEANING UTILITIES
# =============================================================================

def clean_extracted_text(text):
    """
    Clean and normalize extracted PDF text.
    
    PDF text extraction often results in messy output with:
    - Multiple consecutive spaces
    - Excessive newlines
    - Tab characters
    - Non-breaking spaces
    - Other whitespace artifacts
    
    This function normalizes the text for better readability and processing.
    
    Args:
        text (str): Raw extracted text from PDF
    
    Returns:
        str: Cleaned and normalized text
    
    Example:
        raw = "This   is    messy\\n\\n\\n\\ntext"
        clean = clean_extracted_text(raw)
        # Result: "This is messy\\n\\ntext"
    """
    if not text:
        return ""
    
    # Replace non-breaking spaces with regular spaces
    # Non-breaking spaces (\\xa0) are common in PDFs
    text = text.replace('\xa0', ' ')
    
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    
    # Replace carriage returns with newlines (Windows line endings)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove multiple consecutive spaces (but keep single spaces)
    # This regex replaces 2+ spaces with a single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove multiple consecutive newlines (keep max 2 for paragraph breaks)
    # This preserves paragraph structure while removing excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove spaces at the beginning and end of each line
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    # Remove leading/trailing whitespace from the entire text
    text = text.strip()
    
    return text


def get_pdf_info(pdf_path):
    """
    Get metadata and basic information about a PDF file.
    
    This function extracts PDF metadata such as title, author, 
    creation date, and page count without extracting the full text.
    Useful for displaying file information before processing.
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        dict: PDF information containing:
              - filename: Name of the file
              - file_size: Size in bytes
              - num_pages: Number of pages
              - is_encrypted: Whether PDF is password-protected
              - metadata: PDF metadata (title, author, etc.)
        None: If file cannot be read
    
    Example:
        info = get_pdf_info('/path/to/contract.pdf')
        if info:
            print(f"Pages: {info['num_pages']}")
    """
    if not os.path.exists(pdf_path):
        return None
    
    try:
        reader = PdfReader(pdf_path)
        
        # Extract metadata
        metadata = {}
        if reader.metadata:
            # Common PDF metadata fields
            metadata = {
                'title': reader.metadata.get('/Title', None),
                'author': reader.metadata.get('/Author', None),
                'subject': reader.metadata.get('/Subject', None),
                'creator': reader.metadata.get('/Creator', None),
                'producer': reader.metadata.get('/Producer', None),
                'creation_date': str(reader.metadata.get('/CreationDate', None)),
                'modification_date': str(reader.metadata.get('/ModDate', None)),
            }
            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v and v != 'None'}
        
        return {
            'filename': os.path.basename(pdf_path),
            'file_size': os.path.getsize(pdf_path),
            'file_size_readable': format_file_size(os.path.getsize(pdf_path)),
            'num_pages': len(reader.pages),
            'is_encrypted': reader.is_encrypted,
            'metadata': metadata
        }
        
    except Exception as e:
        print(f"✗ Error getting PDF info: {str(e)}")
        return None


def format_file_size(size_bytes):
    """
    Convert file size in bytes to human-readable format.
    
    Args:
        size_bytes (int): File size in bytes
    
    Returns:
        str: Human-readable size (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == '__main__':
    # Test the PDF extraction with a sample file
    import sys
    
    print("=" * 50)
    print("PDF Processor - Test Mode")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Test with provided PDF path
        test_path = sys.argv[1]
        
        print(f"\nTesting with: {test_path}\n")
        
        # Get PDF info
        info = get_pdf_info(test_path)
        if info:
            print(f"File: {info['filename']}")
            print(f"Size: {info['file_size_readable']}")
            print(f"Pages: {info['num_pages']}")
            print(f"Encrypted: {info['is_encrypted']}")
            print()
        
        # Extract text
        text = extract_text_from_pdf(test_path)
        if text:
            print("\n--- Extracted Text (first 500 chars) ---")
            print(text[:500])
            print("..." if len(text) > 500 else "")
        else:
            print("\nNo text extracted.")
    else:
        print("\nUsage: python pdf_processor.py <path_to_pdf>")
        print("Example: python pdf_processor.py contract.pdf")
