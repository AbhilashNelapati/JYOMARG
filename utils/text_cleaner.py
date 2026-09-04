import re

def clean_text(raw_text: str) -> str:
    """
    Normalizes raw document text for better keyword extraction.
    Lowercases, removes special characters, and normalizes whitespace.
    """
    if not raw_text:
        return ""
    
    # Lowercase everything
    text = raw_text.lower()
    
    # Replace newlines and tabs with spaces
    text = re.sub(r'[\n\t\r]', ' ', text)
    
    # Remove non-alphanumeric characters but strictly preserve specific technical chars within strings
    # Replace trailing periods or commas explicitly first
    text = re.sub(r'[\.,;:!?]+(?=\s|$)', ' ', text)
    text = re.sub(r'[^\w\s\+\#\.\-]', ' ', text)
    
    # Normalize multiple spaces to single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()
