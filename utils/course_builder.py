def generate_course_skeleton(topic: str, num_weeks: int = 4, days_per_week: int = 5) -> dict:
    """
    Generates a mathematically perfect Python dictionary skeleton for a course syllabus.
    Strictly preserves the 'weeks' and 'days' structure that app.py expects,
    but enforces the counts perfectly without LLM hallucinations.
    """
    skeleton = {
        "course_title": f"{topic} Mastery Program",
        "description": "[LLM_FILL_COURSE_OVERVIEW_DESCRIPTION]",
        "weeks": []
    }
    
    global_day = 1
    
    for w_idx in range(1, num_weeks + 1):
        week_obj = {
            "week_number": w_idx,
            "title": f"[LLM_FILL_WEEK_{w_idx}_THEME_TITLE]",
            "days": []
        }
        
        for _ in range(days_per_week):
            day_obj = {
                "day_number": global_day,
                "title": f"[LLM_FILL_DAY_{global_day}_SPECIFIC_TOPIC_TITLE]"
            }
            week_obj["days"].append(day_obj)
            global_day += 1
            
        skeleton["weeks"].append(week_obj)
        
    return skeleton
