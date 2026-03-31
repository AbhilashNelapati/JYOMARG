import json
from ai.providers.provider_router import ProviderRouter
from ai.prompts.roadmap_prompts import get_roadmap_system_prompt, get_roadmap_user_prompt
from ai.validators.json_validator import extract_json_safely, validate_required_keys
from utils.roadmap_builder import generate_roadmap_skeleton

router = ProviderRouter()

def generate_hybrid_roadmap(domain: str) -> str:
    """
    Main orchestrator for Hybrid Roadmap Generation.
    Eliminates LLM structural drifting by building the array in Python,
    leaving the LLM exclusively responsible for content enrichment.
    """
    try:
        # 1. Deterministic Structural Scaffolding (Python ensures correct numbering)
        skeleton = generate_roadmap_skeleton(domain, num_phases=2, weeks_per_phase=3, days_per_week=5)
        
        # 2. Extract Instruction Prompts
        system_prompt = get_roadmap_system_prompt()
        user_prompt = get_roadmap_user_prompt(domain, skeleton)
        
        # 3. Route to LLM
        # We prefer Gemini here as long context window & structural adherence is usually better than local 8B models.
        raw_response = router.route_json(system_prompt, user_prompt, prefer_local=False)
        
        # 4. Safely Extract & Validate Output
        filled_json = extract_json_safely(raw_response)
        validate_required_keys(filled_json, ["title", "phases"])
        
        return json.dumps(filled_json)
        
    except Exception as e:
        print(f"[ROADMAP HYBRID ERROR] {e}")
        error_fallback = {
            "error": "Failed to generate roadmap structure.",
            "details": str(e)
        }
        return json.dumps(error_fallback)
