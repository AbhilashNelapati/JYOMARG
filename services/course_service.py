import json
from ai.providers.provider_router import ProviderRouter
from ai.prompts.course_prompts import get_course_system_prompt, get_course_user_prompt
from ai.validators.json_validator import extract_json_safely, validate_required_keys
from utils.course_builder import generate_course_skeleton

router = ProviderRouter()

def generate_hybrid_syllabus(topic: str) -> str:
    """
    Main orchestrator for Hybrid Course Generation.
    Returns the exact JSON schema originally expected by app.py.
    """
    try:
        # 1. Deterministic Scaffolding (Python ensures correct week/day loop counting)
        # Using 4 weeks x 5 days to match standard curriculum size.
        skeleton = generate_course_skeleton(topic, num_weeks=4, days_per_week=5)
        
        # 2. Extract Instruction Prompts
        system_prompt = get_course_system_prompt()
        user_prompt = get_course_user_prompt(topic, skeleton)
        
        # 3. Route to LLM
        # Gemini is preferred for heavy structured payloads.
        raw_response = router.route_json(system_prompt, user_prompt, prefer_local=False)
        
        # 4. Safely Extract & Validate
        filled_json = extract_json_safely(raw_response)
        validate_required_keys(filled_json, ["course_title", "description", "weeks"])
        
        return json.dumps(filled_json)
        
    except Exception as e:
        print(f"[COURSE HYBRID ERROR] {e}")
        error_fallback = {"error": f"Failed to generate course syllabus: {str(e)}"}
        return json.dumps(error_fallback)
