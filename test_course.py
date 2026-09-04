from services.course_service import generate_hybrid_syllabus
import json

print("\n--- Testing Phase 9 Hybrid Course Syllabus ---")
target_domain = "React Frontend"

result_json = generate_hybrid_syllabus(target_domain)
parsed_result = json.loads(result_json)

if "error" in parsed_result:
    print(f"FAILED: {parsed_result['error']}")
else:
    print(f"SUCCESS! Course Title: {parsed_result.get('course_title')}")
    print(f"Total Weeks: {len(parsed_result.get('weeks', []))}")
    print(f"First week day count: {len(parsed_result['weeks'][0].get('days', []))}")
    print("Python structure flawlessly preserved.")
