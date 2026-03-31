import json

def get_roadmap_system_prompt() -> str:
    """Builds the main behavioral instructions assuring correct injection into the skeleton."""
    return (
        "You are an elite career architect creating highly actionable learning roadmaps. "
        "A JSON skeleton has been generated for you with strict numbering. "
        "Your ONLY job is to replace the placeholder values (like [FILL_...]) with real educational concepts. "
        "STRICT CONSTRAINTS:\n"
        "1. PHASE Title: Max 3 words.\n"
        "2. WEEK Title: Max 4 words.\n"
        "3. EXPLANATION: Exactly one professional, short sentence.\n"
        "4. PRACTICE: One concise actionable task.\n"
        "5. ONLY return the final JSON. DO NOT change existing keys or structural brackets."
    )

def get_roadmap_user_prompt(domain: str, skeleton: dict) -> str:
    """Formats the specific domain and scaffolding array."""
    skel_str = json.dumps(skeleton, indent=2)
    return (
        f"Domain Target: {domain}\n\n"
        f"Inject your curriculum cleanly into this exact JSON skeleton:\n"
        f"{skel_str}"
    )
