import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

class ABHIAssistant:
    def __init__(self):
        if not api_key:
            print("[CRITICAL] GOOGLE_API_KEY is missing!")
        
        self.model_name = "gemini-1.5-flash"
        self.model = genai.GenerativeModel(model_name=self.model_name)
        
        print(f"[SYSTEM] AI Initialized with {self.model_name}")

    def _get_json_response(self, prompt):
        import time
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                full_prompt = f"SYSTEM: You are ABHI AI. You MUST output ONLY valid JSON. No conversational text.\nUSER: {prompt}"
                response = self.model.generate_content(full_prompt)
                
                if not response or not hasattr(response, 'text'):
                    raise Exception("Empty response from AI")
                
                raw_text = response.text.strip()
                clean_json = raw_text
                
                if "```" in clean_json:
                    match = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", clean_json, re.DOTALL | re.IGNORECASE)
                    if match: 
                        clean_json = match.group(1)
                    else:
                        start_obj = clean_json.find('{')
                        start_list = clean_json.find('[')
                        start = min(start_obj, start_list) if (start_obj != -1 and start_list != -1) else max(start_obj, start_list)
                        
                        end_obj = clean_json.rfind('}')
                        end_list = clean_json.rfind(']')
                        end = max(end_obj, end_list)
                        
                        if start != -1 and end != -1:
                            clean_json = clean_json[start:end+1]
                
                json.loads(clean_json.strip())
                return clean_json.strip()
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str:
                    if attempt < max_attempts - 1:
                        wait_time = (attempt + 1) * 5 
                        print(f"[SYSTEM] Rate limit hit. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return json.dumps({"error": "AI is temporarily busy (Rate Limit). Please wait 60 seconds and try again."})
                
                print(f"[ERROR] AI Failed: {error_str}")
                return json.dumps({"error": f"AI Error: {error_str}"})

    def analyze_skill_gap(self, resume_text, jd_text):
        prompt = f"Analyze Resume vs JD. Output JSON: {{'match_score': 0..100, 'skill_scores': {{}}, 'missing_skills': [], 'advice': ''}}"
        return self._get_json_response(prompt)

    def ask_abhi(self, user_input):
        prompt = (
            f"You are ABHI AI, a helpful career assistant. "
            f"User asked: '{user_input}'. "
            f"Provide a friendly, useful response. "
            f"Output as JSON with keys: 'spoken_summary' (short summary) and 'display_content' (detailed markdown)."
        )
        return self._get_json_response(prompt)

    def generate_job_alerts(self, user_profile):
        prompt = f"Based on this profile: {user_profile}, generate 3 realistic job alerts. Output ONLY as JSON: {{'jobs': [{{'job_title': '', 'company': '', 'match_score': 0-100, 'reason': '', 'apply_link': ''}}]}}"
        return self._get_json_response(prompt)

    def generate_course_syllabus(self, topic):
        prompt = f"Generate a week-wise syllabus for {topic}. Output ONLY as JSON: {{'course_title': '', 'description': '', 'weeks': [{{'week_number': 1, 'title': '', 'days': [{{'day_number': 1, 'title': ''}}]}}]}}"
        return self._get_json_response(prompt)

    def generate_day_content(self, topic, day_title):
        import time
        prompt = f"Write a detailed professional markdown guide for {topic}: {day_title}. Focus on practical examples."
        for attempt in range(2):
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                if "429" in str(e) and attempt == 0:
                    time.sleep(5)
                    continue
                return f"AI is temporarily overloaded. Please try again in a minute. (Error: {str(e)})"

    def generate_assessment(self, topic, week_number, is_final=False):
        prompt = f"Generate 5 MCQs for {topic} Week {week_number}. Output ONLY as JSON: {{'questions': [{{'id': 1, 'question': '', 'options': ['', '', '', ''], 'answer': ''}}]}}"
        return self._get_json_response(prompt)

    def generate_career_roadmap(self, domain):
        prompt = (
            f"Generate a minimalist professional roadmap for {domain}. "
            f"STRICT RULES: "
            f"1. PHASE Title: Max 3 words. "
            f"2. WEEK Title: Max 4 words. "
            f"3. DAY: Max 1 topic per day. "
            f"4. EXPLANATION: Exactly one short sentence. "
            f"5. PRACTICE: One short action. "
            f"JSON: {{'title': '{domain}', 'phases': [{{'phase_num': 1, 'phase_name': '', 'weeks': [{{'week_number': 1, 'week_title': '', 'days': [{{'day_number': 1, 'topics': [{{'topic_name': '', 'explanation': '', 'practice': ''}}]}}]}}]}}]}} "
            f"RULE: Global day numbering. Output ONLY JSON."
        )
        return self._get_json_response(prompt)
