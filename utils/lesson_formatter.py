def format_lesson_to_markdown(parsed_json: dict) -> str:
    """
    Converts a strictly validated JSON lesson object back into Markdown.
    This preserves the robust JSON-schema generation in the backend
    while delivering the expected Markdown payload to app.py/learn.html.
    """
    title = parsed_json.get("title", "Lesson")
    explanation = parsed_json.get("explanation", "")
    examples = parsed_json.get("examples", [])
    exercise = parsed_json.get("exercise", "")
    summary = parsed_json.get("summary", "")
    
    md = f"# {title}\n\n"
    
    md += f"## Concept Explanation\n{explanation}\n\n"
    
    md += "## Practical Examples\n"
    for ex in examples:
        md += f"- {ex}\n"
    md += "\n"
        
    md += f"## Mini-Exercise\n{exercise}\n\n"
    
    md += f"## Summary\n> {summary}\n"
    
    return md
