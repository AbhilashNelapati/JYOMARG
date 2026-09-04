def get_chat_system_prompt() -> str:
    """Builds the main personality and instructions for ABHI AI Chat Assistant."""
    return (
        "You are ABHI AI, an expert career tracking assistant. "
        "Provide a friendly, useful response. "
        "Output ONLY valid JSON with exactly two keys: 'spoken_summary' (a short summary) and 'display_content' (detailed markdown)."
    )

def get_chat_user_prompt(user_input: str) -> str:
    """Formats the user query for the chat model."""
    return f"User asked: '{user_input}'."
