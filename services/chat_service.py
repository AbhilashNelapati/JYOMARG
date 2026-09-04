import json
from ai.providers.provider_router import ProviderRouter
from ai.prompts.chat_prompts import get_chat_system_prompt, get_chat_user_prompt
from ai.validators.json_validator import extract_json_safely, validate_required_keys

# Instantiate the router
router = ProviderRouter()

def handle_ask_abhi(user_input: str) -> str:
    """
    Service layer logic to answer user chat queries.
    Replaces the current tight logic in abhi_ai.ask_abhi().
    Returns a JSON string expected by app.py.
    """
    system_prompt = get_chat_system_prompt()
    user_prompt = get_chat_user_prompt(user_input)
    
    try:
        # Chat is low risk - use Ollama if available, fallback to Gemini
        raw_response = router.route_json(system_prompt, user_prompt, prefer_local=True)
        
        # Safely extract and validate the JSON
        parsed_dict = extract_json_safely(raw_response)
        validate_required_keys(parsed_dict, ["spoken_summary", "display_content"])
        
        # FastAPI expects JSON string here to return properly
        return json.dumps(parsed_dict)
        
    except Exception as e:
        print(f"[CHAT SERVICE ERROR] {e}")
        error_payload = {
            "error": "AI service is temporarily overloaded or unavailable.",
            "details": str(e)
        }
        return json.dumps({"display_content": f"**System Notice:** {error_payload['error']}"})
