def get_ats_system_prompt() -> str:
    """Builds the main personality and instructions for ATS analysis."""
    return (
        "You are an expert Applicant Tracking System (ATS) optimization consultant. "
        "Your role is to logically explain skill gaps to the user and structurally improve their resume flow. "
        "You MUST output ONLY valid JSON with exactly two keys: "
        "'explanation' (a concise 2-sentence explanation of the candidate's fit) and "
        "'suggestions' (a list of exactly 3 specific, actionable bullet points to improve the resume or add skills)."
    )

def get_ats_user_prompt(score: int, missing_skills: list, jd_snippet: str) -> str:
    """Formats the user query containing deterministic Python data for the LLM."""
    missing_str = ", ".join(missing_skills[:15]) # Cap missing skills to prevent token bloat/confusion
    jd_short = jd_snippet[:600] # Provide just enough context
    
    return (
        f"The candidate achieved a deterministic ATS match score of {score}/100 based on exact keyword analysis.\n"
        f"They are missing these key technical elements required by the JD: {missing_str}.\n"
        f"JD Context snippet: {jd_short}...\n\n"
        f"Based strictly on this data, provide the 'explanation' of the gap and exactly 3 'suggestions' for improvement."
    )
