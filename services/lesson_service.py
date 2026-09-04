from ai.providers.provider_router import ProviderRouter
from ai.prompts.lesson_prompts import get_lesson_system_prompt, get_lesson_user_prompt
from ai.validators.json_validator import extract_json_safely, validate_required_keys
from utils.lesson_formatter import format_lesson_to_markdown

router = ProviderRouter()

def generate_hybrid_lesson(topic: str, day_title: str) -> str:
    """
    Main orchestrator for generating day-wise content.
    Uses JSON constraint for AI coherence, but returns Markdown
    to maintain backward compatibility with app.py.
    """
    try:
        # 1. Prompts
        system_prompt = get_lesson_system_prompt()
        user_prompt = get_lesson_user_prompt(topic, day_title)
        
        # 2. LLM Call via Router (Ollama is great for specific lesson generations)
        raw_response = router.route_json(system_prompt, user_prompt, prefer_local=True)
        
        # 3. Safely Extract & Validate
        filled_json = extract_json_safely(raw_response)
        validate_required_keys(filled_json, ["title", "explanation", "examples", "summary"])
        
        # 4. Format to Markdown for UI Compatibility
        final_markdown = format_lesson_to_markdown(filled_json)
        
        return final_markdown
        
    except Exception as e:
        print(f"[LESSON HYBRID ERROR] {e}")
        return f"### AI Error\nWe encountered an issue generating this lesson. Details: Exception {str(e)}"
