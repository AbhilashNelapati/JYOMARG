def get_lesson_system_prompt() -> str:
    """Forces the LLM to output teaching content structurally as JSON."""
    return (
        "You are an expert technical instructor. "
        "You MUST output exactly one JSON object following this strict schema. "
        "Do NOT wrap it in markdown block quotes. Just the raw JSON object.\n"
        "{\n"
        '  "title": "String: Name of the topic",\n'
        '  "explanation": "String: Detailed teaching content (multi-paragraph allowed).",\n'
        '  "examples": ["Array", "of", "strings containing real world or code examples"],\n'
        '  "exercise": "String: A short practice task.",\n'
        '  "summary": "String: A 1-sentence wrap up."\n'
        "}"
    )

def get_lesson_user_prompt(topic: str, day_title: str) -> str:
    """Provides the specific lesson criteria."""
    return (
        f"Course Topic: {topic}\n"
        f"Specific Day Lesson: {day_title}\n\n"
        "Generate the deep, professional educational content for this day following the JSON schema."
    )
