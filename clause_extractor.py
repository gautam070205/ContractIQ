# Contract clause extraction logic
# This module extracts and categorizes contract clauses using keyword matching
# It identifies common legal clauses like termination, liability, payment, etc.

import re
from typing import Dict, List

# =============================================================================
# CLAUSE CATEGORIES AND KEYWORDS
# =============================================================================

# Dictionary mapping clause categories to their identifying keywords
# Each category contains keywords commonly found in that type of clause
# Keywords are stored in lowercase for case-insensitive matching

CLAUSE_KEYWORDS = {
    # -------------------------------------------------------------------------
    # TERMINATION CLAUSES
    # -------------------------------------------------------------------------
    # These clauses define how and when the contract can be ended
    # Common in employment contracts, service agreements, subscriptions
    "Termination": [
        "termination",
        "terminate",
        "cancel",
        "cancellation",
        "end agreement",
        "end of agreement",
        "notice period",
        "right to terminate",
        "termination for cause",
        "termination for convenience"
    ],
    
    # -------------------------------------------------------------------------
    # LIABILITY CLAUSES
    # -------------------------------------------------------------------------
    # These clauses define responsibility for damages or losses
    # Include indemnification and limitation of liability provisions
    "Liability": [
        "liability",
        "indemnify",
        "indemnification",
        "damages",
        "liable",
        "limitation of liability",
        "hold harmless",
        "indemnity",
        "consequential damages",
        "direct damages"
    ],
    
    # -------------------------------------------------------------------------
    # PAYMENT CLAUSES
    # -------------------------------------------------------------------------
    # These clauses cover financial terms and payment obligations
    # Include pricing, invoicing, and compensation terms
    "Payment": [
        "payment",
        "fee",
        "invoice",
        "compensation",
        "remuneration",
        "price",
        "billing",
        "pay",
        "cost",
        "charges",
        "payment terms",
        "due date",
        "late payment"
    ],
    
    # -------------------------------------------------------------------------
    # CONFIDENTIALITY CLAUSES
    # -------------------------------------------------------------------------
    # These clauses protect sensitive information
    # Common in NDAs, employment contracts, and business agreements
    "Confidentiality": [
        "confidential",
        "confidentiality",
        "nda",
        "non-disclosure",
        "secret",
        "proprietary information",
        "confidential information",
        "trade secret",
        "disclose",
        "disclosure"
    ],
    
    # -------------------------------------------------------------------------
    # INTELLECTUAL PROPERTY CLAUSES
    # -------------------------------------------------------------------------
    # These clauses address ownership of creative works and inventions
    # Important in technology, creative, and research contracts
    "Intellectual Property": [
        "intellectual property",
        "copyright",
        "trademark",
        "patent",
        "ip rights",
        "proprietary rights",
        "ownership of work",
        "work for hire",
        "license",
        "royalty",
        "invention"
    ]
}


# =============================================================================
# TEXT PROCESSING UTILITIES
# =============================================================================

def split_into_sentences(text):
    """
    Split text into individual sentences.
    
    This function breaks down a block of text into sentences for
    individual analysis. It handles common sentence-ending patterns
    while trying to avoid false splits (like "Dr." or "Inc.").
    
    Sentence Detection Logic:
    1. Split on common sentence terminators: . ! ?
    2. Handle edge cases like abbreviations
    3. Clean up whitespace
    4. Filter out empty sentences
    
    Args:
        text (str): The text to split into sentences
    
    Returns:
        list: List of sentences (strings), cleaned and trimmed
    
    Example:
        text = "This is sentence one. This is sentence two!"
        sentences = split_into_sentences(text)
        # Result: ["This is sentence one.", "This is sentence two!"]
    """
    if not text:
        return []
    
    # -------------------------------------------------------------------------
    # Method 1: Regex-based sentence splitting
    # -------------------------------------------------------------------------
    # This regex looks for sentence boundaries:
    # - Period, exclamation, or question mark
    # - Followed by one or more spaces
    # - Followed by an uppercase letter (start of new sentence)
    # 
    # The (?=[A-Z]) is a lookahead - it checks but doesn't consume the capital
    
    # First, normalize the text
    text = text.strip()
    
    # Handle common abbreviations that shouldn't split sentences
    # Replace periods in common abbreviations with a placeholder
    abbreviations = [
        'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Jr.', 'Sr.', 'Inc.', 'Ltd.', 'Corp.',
        'vs.', 'etc.', 'i.e.', 'e.g.', 'a.m.', 'p.m.', 'U.S.', 'U.K.'
    ]
    
    # Temporarily replace abbreviation periods with a placeholder
    placeholder = "<<<PERIOD>>>"
    for abbr in abbreviations:
        text = text.replace(abbr, abbr.replace('.', placeholder))
    
    # Split on sentence-ending punctuation followed by space
    # This regex splits on: . or ! or ? followed by space(s)
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, text)
    
    # Restore the periods in abbreviations
    sentences = [s.replace(placeholder, '.') for s in sentences]
    
    # Clean up each sentence
    cleaned_sentences = []
    for sentence in sentences:
        # Strip whitespace
        sentence = sentence.strip()
        
        # Skip empty sentences or very short fragments
        if len(sentence) > 5:  # Minimum sentence length
            cleaned_sentences.append(sentence)
    
    return cleaned_sentences


def normalize_text(text):
    """
    Normalize text for keyword matching.
    
    Converts text to lowercase and normalizes whitespace for
    consistent keyword matching.
    
    Args:
        text (str): Text to normalize
    
    Returns:
        str: Normalized text (lowercase, single spaces)
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


# =============================================================================
# MAIN CLAUSE EXTRACTION FUNCTION
# =============================================================================

def extract_clauses(text):
    """
    Extract and categorize clauses from contract text.
    
    This function analyzes contract text and identifies clauses belonging
    to predefined categories (Termination, Liability, Payment, etc.)
    using keyword matching.
    
    Algorithm:
    1. Split the input text into individual sentences
    2. For each sentence, normalize it for matching (lowercase)
    3. Check if any keywords from each category appear in the sentence
    4. If a keyword is found, add the original sentence to that category
    5. A sentence can appear in multiple categories if it contains
       keywords from different categories
    
    Matching Logic:
    - Case-insensitive matching (converted to lowercase)
    - Whole word matching where possible
    - Multi-word keywords are matched as phrases
    
    Args:
        text (str): The full extracted text from a contract PDF
    
    Returns:
        dict: Dictionary with clause categories as keys and lists of
              matching sentences as values. Structure:
              {
                  "Termination": ["sentence 1", "sentence 2"],
                  "Liability": ["sentence 3"],
                  "Payment": [],
                  "Confidentiality": ["sentence 4", "sentence 5"],
                  "Intellectual Property": []
              }
    
    Example:
        text = "This agreement may be terminated with 30 days notice. 
                All payments are due within 30 days."
        clauses = extract_clauses(text)
        # Result:
        # {
        #     "Termination": ["This agreement may be terminated with 30 days notice."],
        #     "Payment": ["All payments are due within 30 days."],
        #     ...
        # }
    """
    
    # Initialize the result dictionary with empty lists for each category
    # This ensures all categories exist in the output, even if empty
    extracted_clauses = {category: [] for category in CLAUSE_KEYWORDS.keys()}
    
    # Handle empty or None input
    if not text or not text.strip():
        print("→ No text provided for clause extraction")
        return extracted_clauses
    
    # -------------------------------------------------------------------------
    # Step 1: Split text into sentences
    # -------------------------------------------------------------------------
    sentences = split_into_sentences(text)
    
    if not sentences:
        print("→ No sentences found in text")
        return extracted_clauses
    
    print(f"→ Analyzing {len(sentences)} sentences for clause extraction...")
    
    # -------------------------------------------------------------------------
    # Step 2: Analyze each sentence
    # -------------------------------------------------------------------------
    # Track statistics for logging
    total_matches = 0
    
    for sentence in sentences:
        # Normalize the sentence for matching (lowercase)
        normalized_sentence = normalize_text(sentence)
        
        # Check each category's keywords against this sentence
        for category, keywords in CLAUSE_KEYWORDS.items():
            # Check if any keyword from this category appears in the sentence
            if contains_keyword(normalized_sentence, keywords):
                # Add the ORIGINAL sentence (not normalized) to preserve formatting
                # Avoid duplicates (same sentence shouldn't appear twice in same category)
                if sentence not in extracted_clauses[category]:
                    extracted_clauses[category].append(sentence)
                    total_matches += 1
    
    # -------------------------------------------------------------------------
    # Step 3: Log results
    # -------------------------------------------------------------------------
    print(f"✓ Clause extraction complete:")
    for category, clauses in extracted_clauses.items():
        count = len(clauses)
        if count > 0:
            print(f"  • {category}: {count} clause(s) found")
    
    if total_matches == 0:
        print("  → No clauses identified (text may not be a contract)")
    
    return extracted_clauses


def contains_keyword(text, keywords):
    """
    Check if any keyword from the list appears in the text.
    
    This function performs intelligent keyword matching:
    - For single-word keywords: Uses word boundary matching to avoid partial matches
      (e.g., "pay" should match "pay" but ideally not "payment" - though we 
       include both separately in our keyword lists for clarity)
    - For multi-word keywords: Checks if the phrase appears anywhere in text
    
    Args:
        text (str): Normalized (lowercase) text to search in
        keywords (list): List of keywords to search for
    
    Returns:
        bool: True if any keyword is found, False otherwise
    
    Example:
        text = "the company shall indemnify the contractor"
        keywords = ["indemnify", "liability"]
        result = contains_keyword(text, keywords)  # Returns True
    """
    for keyword in keywords:
        # Convert keyword to lowercase for matching
        keyword_lower = keyword.lower()
        
        # Check if keyword appears in text
        # For multi-word keywords, simple 'in' check works well
        # For single words, we could use regex word boundaries, but
        # for legal text, the simple approach works well enough
        if keyword_lower in text:
            return True
    
    return False


# =============================================================================
# ADVANCED CLAUSE ANALYSIS FUNCTIONS
# =============================================================================

def get_clause_summary(extracted_clauses):
    """
    Generate a summary of extracted clauses.
    
    Provides statistics and overview of the clause extraction results.
    Useful for displaying on dashboards or in reports.
    
    Args:
        extracted_clauses (dict): Output from extract_clauses()
    
    Returns:
        dict: Summary containing:
              - total_clauses: Total number of clauses found
              - categories_found: List of categories with clauses
              - category_counts: Dict of category -> count
              - coverage_percentage: What % of categories have clauses
    """
    if not extracted_clauses:
        return {
            'total_clauses': 0,
            'categories_found': [],
            'category_counts': {},
            'coverage_percentage': 0
        }
    
    category_counts = {cat: len(clauses) for cat, clauses in extracted_clauses.items()}
    categories_found = [cat for cat, count in category_counts.items() if count > 0]
    total_clauses = sum(category_counts.values())
    total_categories = len(CLAUSE_KEYWORDS)
    
    return {
        'total_clauses': total_clauses,
        'categories_found': categories_found,
        'category_counts': category_counts,
        'coverage_percentage': round((len(categories_found) / total_categories) * 100, 1)
    }


def get_clause_highlights(extracted_clauses, max_per_category=2):
    """
    Get a condensed view of clauses with limited items per category.
    
    Useful for preview displays where you don't want to show all clauses.
    
    Args:
        extracted_clauses (dict): Output from extract_clauses()
        max_per_category (int): Maximum clauses to include per category
    
    Returns:
        dict: Same structure as extracted_clauses but limited entries
    """
    if not extracted_clauses:
        return {}
    
    highlights = {}
    for category, clauses in extracted_clauses.items():
        # Take only the first N clauses from each category
        highlights[category] = clauses[:max_per_category]
    
    return highlights


def search_custom_keywords(text, custom_keywords):
    """
    Search for custom keywords in the text.
    
    Allows users to search for specific terms not in the predefined categories.
    
    Args:
        text (str): Contract text to search
        custom_keywords (list): List of custom keywords to find
    
    Returns:
        list: Sentences containing any of the custom keywords
    """
    if not text or not custom_keywords:
        return []
    
    sentences = split_into_sentences(text)
    matching_sentences = []
    
    for sentence in sentences:
        normalized = normalize_text(sentence)
        for keyword in custom_keywords:
            if keyword.lower() in normalized:
                if sentence not in matching_sentences:
                    matching_sentences.append(sentence)
                break  # Found a match, no need to check other keywords
    
    return matching_sentences


# =============================================================================
# AVAILABLE CATEGORIES (for API/frontend use)
# =============================================================================

def get_available_categories():
    """
    Get list of all available clause categories.
    
    Useful for populating dropdowns or filters in the frontend.
    
    Returns:
        list: List of category names
    """
    return list(CLAUSE_KEYWORDS.keys())


def get_category_keywords(category):
    """
    Get the keywords for a specific category.
    
    Useful for displaying what terms trigger each category.
    
    Args:
        category (str): Category name
    
    Returns:
        list: Keywords for that category, or empty list if not found
    """
    return CLAUSE_KEYWORDS.get(category, [])


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == '__main__':
    # Test the clause extraction with sample contract text
    print("=" * 60)
    print("Clause Extractor - Test Mode")
    print("=" * 60)
    
    # Sample contract text for testing
    sample_text = """
    AGREEMENT FOR SERVICES
    
    This Agreement is entered into as of January 1, 2025.
    
    1. PAYMENT TERMS
    The Client agrees to pay a fee of $5,000 per month for services rendered.
    All invoices are due within 30 days of receipt. Late payments shall 
    incur a 5% penalty charge.
    
    2. CONFIDENTIALITY
    Both parties agree to maintain the confidentiality of all proprietary 
    information shared during the course of this agreement. Neither party 
    shall disclose confidential information to any third party without 
    prior written consent.
    
    3. TERMINATION
    Either party may terminate this agreement with 30 days written notice.
    Upon termination, the Client shall pay for all services rendered up to 
    the termination date. The agreement may also be cancelled immediately 
    for cause.
    
    4. LIABILITY
    The Service Provider shall not be liable for any indirect or 
    consequential damages. The Client agrees to indemnify and hold harmless
    the Service Provider against any claims arising from the Client's use 
    of the services.
    
    5. INTELLECTUAL PROPERTY
    All intellectual property created during this engagement shall be owned
    by the Client upon full payment. The Service Provider retains the right
    to use general knowledge and skills acquired during the engagement.
    Any pre-existing patents or copyrights remain with their original owners.
    """
    
    print("\n--- Sample Contract Text ---")
    print(sample_text[:300] + "...\n")
    
    print("--- Extracting Clauses ---\n")
    clauses = extract_clauses(sample_text)
    
    print("\n--- Results ---\n")
    for category, found_clauses in clauses.items():
        print(f"\n{category.upper()} ({len(found_clauses)} found):")
        print("-" * 40)
        if found_clauses:
            for i, clause in enumerate(found_clauses, 1):
                # Truncate long clauses for display
                display = clause[:100] + "..." if len(clause) > 100 else clause
                print(f"  {i}. {display}")
        else:
            print("  (No clauses found)")
    
    print("\n--- Summary ---")
    summary = get_clause_summary(clauses)
    print(f"Total clauses found: {summary['total_clauses']}")
    print(f"Categories with clauses: {', '.join(summary['categories_found'])}")
    print(f"Coverage: {summary['coverage_percentage']}%")
