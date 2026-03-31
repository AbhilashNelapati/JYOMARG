from services.lesson_service import generate_hybrid_lesson

print("\n--- Testing Phase 9 Hybrid Lesson Content ---")
topic = "React Frontend"
day_title = "Building custom hooks"

markdown_result = generate_hybrid_lesson(topic, day_title)

if "AI Error" in markdown_result:
    print("FAILED Generation.")
    print(markdown_result)
else:
    print("SUCCESS! Output translated from strict JSON payload back into Markdown string:")
    print("==================\n")
    print(markdown_result[:300] + "...\n\n[TRUNCATED FOR DISPLAY]")
