import json
from ai.providers.provider_router import ProviderRouter
from ai.prompts.ats_prompts import get_ats_system_prompt, get_ats_user_prompt
from ai.validators.json_validator import extract_json_safely, validate_required_keys
from utils.text_cleaner import clean_text
from utils.keyword_extractor import extract_keywords
from utils.skill_matcher import match_skills
from utils.scoring_engine import calculate_ats_score

# Instantiate the router
router = ProviderRouter()

def analyze_hybrid_ats(resume_text: str, jd_text: str) -> str:
    """
    Main orchestrator for Hybrid ATS Analysis.
    Performs parsing, matching, and scoring deterministically in Python.
    Uses LLM solely for human-readable explanation and suggestions.
    Return JSON format matches existing frontend expectations.
    """
    try:
        # 1. Clean Texts (Python)
        clean_resume = clean_text(resume_text)
        clean_jd = clean_text(jd_text)
        
        # 2. Extract Keywords (Python)
        resume_keywords = extract_keywords(clean_resume)
        jd_keywords = extract_keywords(clean_jd)
        
        # 3. Match Skills (Python)
        matched_skills, missing_skills = match_skills(resume_keywords, jd_keywords)
        
        # 4. Calculate Exact Score (Python)
        total_jd = len(jd_keywords)
        score = calculate_ats_score(matched_skills, total_jd)
        
        # 5. Call LLM ONLY for Contextual Explanation and Guidance
        system_prompt = get_ats_system_prompt()
        user_prompt = get_ats_user_prompt(score, missing_skills, jd_text)
        
        # Prefer Gemini for reasoning, but router gracefully handles it
        raw_llm_response = router.route_json(system_prompt, user_prompt, prefer_local=False)
        
        # Safely parse LLM output
        llm_data = extract_json_safely(raw_llm_response)
        validate_required_keys(llm_data, ["explanation", "suggestions"])
        
        # 6. Assemble Final Hybrid Payload mapped to legacy frontend keys
        final_result = {
            "score": score,
            "keyword_matches": matched_skills[:25], 
            "missing_keywords": missing_skills[:25],
            "content_suggestions": llm_data["suggestions"],
            "alignment_suggestions": [
                "ATS algorithms prefer standard fonts (Arial, Calibri).",
                "Ensure your structure uses clearly defined sections like 'Experience' and 'Skills'."
            ],
            "jd_matches_highlighted": [f"Validated Match: {k}" for k in matched_skills[:5]],
            "ai_improved_resume": f"### AI Analysis Summary\n{llm_data['explanation']}\n\n### Actionable Steps\n" + "\n".join([f"- {s}" for s in llm_data["suggestions"]])
        }
        
        return json.dumps(final_result)
        
    except Exception as e:
        print(f"[ATS HYBRID SERVICE ERROR] {e}")
        # Graceful fallback schema matching frontend
        error_fallback = {
            "score": 0,
            "keyword_matches": [],
            "missing_keywords": [],
            "content_suggestions": [f"System Detail: {str(e)}", "Please check your document formatting and try again."],
            "alignment_suggestions": [],
            "jd_matches_highlighted": [],
            "ai_improved_resume": "Our system encountered an error while analyzing the documents."
        }
        return json.dumps(error_fallback)
