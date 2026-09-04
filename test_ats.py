from services.ats_service import analyze_hybrid_ats
import json

print("\n--- Testing Phase 6 Hybrid ATS System ---")
print("Extracting, Cleaning, Matching, and Scoring via Python...")

dummy_resume = """
John Doe - Senior Backend Engineer
Experience building massive scale applications.
Skills: Python, FastAPI, Docker, SQL, Git, Linux.
"""

dummy_jd = """
We are looking for a backend engineer.
Required Skills: Python, FastAPI, Docker, Kubernetes, AWS, SQL.
"""

result_json = analyze_hybrid_ats(dummy_resume, dummy_jd)
parsed_result = json.loads(result_json)

print("\nSUCCESS! Final Hybrid Response:\n")
print(f"Total ATS Score: {parsed_result['score']}/100")
print(f"Matched Skills:  {parsed_result['matched_skills']}")
print(f"Missing Skills:  {parsed_result['missing_skills']}")
print(f"\nLLM Explanation: {parsed_result['explanation']}")
print(f"\nLLM Suggestions:")
for s in parsed_result['suggestions']:
    print(f" - {s}")
