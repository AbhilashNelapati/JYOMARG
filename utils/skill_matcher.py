def match_skills(resume_keywords: set, jd_keywords: set) -> tuple:
    """
    Compares Resume keywords against Job Description keywords.
    Takes sets for O(1) intersection speeds.
    Returns (matched_skills_list, missing_skills_list).
    """
    # Find matching skills via set intersection
    matched = resume_keywords.intersection(jd_keywords)
    
    # Find skills in JD that are strictly missing from the Resume
    missing = jd_keywords.difference(resume_keywords)
    
    # Convert back to sorted lists for predictable, ordered JSON output
    return list(sorted(matched)), list(sorted(missing))
