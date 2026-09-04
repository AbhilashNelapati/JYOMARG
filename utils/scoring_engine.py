def calculate_ats_score(matched_skills: list, total_jd_skills: int) -> int:
    """
    Calculates a deterministic ATS score (0 to 100) based strictly on keyword match percentage.
    This guarantees mathematically accurate scores instead of LLM hallucinations.
    """
    if total_jd_skills == 0:
        return 0 # Prevent division by zero if JD is empty or too short
        
    match_count = len(matched_skills)
    
    # Simple direct percentage
    score = (match_count / total_jd_skills) * 100
    
    # Ensure score caps at 100 max and round to nearest integer
    final_score = min(100, round(score))
    
    return final_score
