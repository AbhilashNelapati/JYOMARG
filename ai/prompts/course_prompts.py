import json

def get_course_system_prompt() -> str:
    """Builds instructions restricting LLM to content filling only."""
    return (
        "You are an expert curriculum designer. "
        "A rigid JSON skeleton representing a syllabus has been provided. "
        "Your ONLY task is to replace the placeholder fields (e.g., [LLM_FILL...]) with high-quality educational titles and descriptions. "
        "STRICT RULES:\n"
        "1. DO NOT add or remove any weeks or days.\n"
        "2. Keep the 'description' to exactly two sentences.\n"
        "3. Keep titles concise and engaging.\n"
        "4. Output ONLY the completed JSON. Do not deviate from the structure."
    )

def get_course_user_prompt(topic: str, skeleton: dict) -> str:
    """Combines user target with the Python-constructed schema."""
    skel_str = json.dumps(skeleton, indent=2)
    return (
        f"Target Topic: {topic}\n\n"
        f"Inject your curriculum cleanly into this exact JSON skeleton:\n"
        f"{skel_str}"
    )
