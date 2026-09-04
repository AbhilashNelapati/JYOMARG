import json
import re

def extract_json_safely(raw_text: str) -> dict:
    """
    Attempts to safely parse JSON from raw LLM output, avoiding rigid regex failures.
    Tries multiple parsing strategies sequentially.
    """
    clean_text = raw_text.strip()
    
    # 1. Attempt parsing the raw string natively
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass
        
    # 2. Extract from standard Markdown blocks ```json ... ```
    match = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", clean_text, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # 3. Primitive bracket tracking (useful if model attached conversational text)
    start_obj = clean_text.find('{')
    end_obj = clean_text.rfind('}')
    
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        try:
            extracted = clean_text[start_obj:end_obj+1]
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass
            
    raise ValueError("Failed to extract valid JSON from the provider response string.")

def validate_required_keys(parsed_json: dict, required_keys: list) -> bool:
    """Ensures that the output contains the absolute minimum required keys."""
    for key in required_keys:
        if key not in parsed_json:
            raise KeyError(f"Validation Error: Missing required key '{key}'")
    return True
