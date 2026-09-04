def generate_roadmap_skeleton(domain: str, num_phases: int = 2, weeks_per_phase: int = 3, days_per_week: int = 5) -> dict:
    """
    Generates a mathematically perfect Python dictionary skeleton for a learning roadmap.
    Guarantees continuous global numbering for weeks and days, removing LLM counting errors.
    """
    skeleton = {
        "title": domain,
        "phases": []
    }
    
    global_week = 1
    global_day = 1
    
    for phase_idx in range(1, num_phases + 1):
        phase_obj = {
            "phase_num": phase_idx,
            "phase_name": f"[FILL_PHASE_{phase_idx}_NAME]",
            "weeks": []
        }
        
        for w_idx in range(weeks_per_phase):
            week_obj = {
                "week_number": global_week,
                "week_title": f"[FILL_WEEK_{global_week}_TITLE]",
                "days": []
            }
            
            for d_idx in range(days_per_week):
                day_obj = {
                    "day_number": global_day,
                    "topics": [
                        {
                            "topic_name": f"[FILL_DAY_{global_day}_TOPIC]",
                            "explanation": f"[FILL_DAY_{global_day}_EXPLANATION]",
                            "practice": f"[FILL_DAY_{global_day}_PRACTICE]"
                        }
                    ]
                }
                week_obj["days"].append(day_obj)
                global_day += 1
                
            phase_obj["weeks"].append(week_obj)
            global_week += 1
            
        skeleton["phases"].append(phase_obj)
        
    return skeleton
