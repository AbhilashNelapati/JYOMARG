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
        
        genai.configure(api_key=api_key or "DUMMY_KEY")
        
        # --- AUTO MODEL SELECTION ---
        self.model_name = "gemini-pro" # Standard fallback
        try:
            # We list models and find one that supports 'generateContent'
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            print(f"[SYSTEM] Available models: {available}")
            
            # Prefer flash if available, otherwise pro
            if any("gemini-1.5-flash" in m for m in available):
                self.model_name = [m for m in available if "gemini-1.5-flash" in m][0]
            elif any("gemini-pro" in m for m in available):
                self.model_name = [m for m in available if "gemini-pro" in m][0]
            elif available:
                self.model_name = available[0]
                
        except Exception as e:
            print(f"[SYSTEM] Discovery failed, using default: {e}")

        self.model = genai.GenerativeModel(model_name=self.model_name)
        print(f"[SYSTEM] AI Initialized with {self.model_name}")

    def _get_json_response(self, prompt):
        import time
        max_retries = 1
        
        for attempt in range(max_retries + 1):
            try:
                full_prompt = f"SYSTEM: You are ABHI AI. Always output valid JSON.\nUSER: {prompt}"
                response = self.model.generate_content(full_prompt)
                raw_text = response.text.strip()
                
                clean_json = raw_text
                if "```" in clean_json:
                    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_json, re.DOTALL | re.IGNORECASE)
                    if match: clean_json = match.group(1)
                
                json.loads(clean_json.strip())
                return clean_json.strip()
                
            except Exception as e:
                err_str = str(e)
                if "429" in err_str and attempt < max_retries:
                    print(f"[RETRY] Quota exceeded. Waiting 5s for attempt {attempt + 1}...")
                    time.sleep(5)
                    continue
                    
                print(f"[ERROR] AI Failed ({self.model_name}): {e}")
                if "429" in err_str:
                    return '{"error": "AI Quota Exceeded. Please wait 1 minute and retry."}'
                return f'{{"error": "AI Logic Failed: {err_str[:100]}"}}'

    def analyze_skill_gap(self, resume_text, jd_text):
        prompt = f"Analyze Resume vs JD. Output JSON: {{'match_score': 0..100, 'skill_scores': {{}}, 'missing_skills': [], 'advice': ''}}"
        return self._get_json_response(prompt)

    def ask_abhi(self, user_input):
        prompt = f"User Query: {user_input}. Output JSON: {{'spoken_summary': '', 'display_content': ''}}"
        return self._get_json_response(prompt)

    def generate_job_alerts(self, user_profile):
        prompt = f"Generate 3 job alerts list in JSON format for: {user_profile}."
        return self._get_json_response(prompt)

    def generate_course_syllabus(self, topic):
        prompt = f"Generate syllabus for {topic} in JSON format."
        return self._get_json_response(prompt)

    def generate_day_content(self, topic, day_title):
        prompt = f"Detailed Markdown tutorial for {topic} - {day_title}."
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return "Error generating content."

    def generate_assessment(self, topic, week_number, is_final=False):
        prompt = f"Generate quiz JSON for {topic}."
        return self._get_json_response(prompt)

    def generate_career_roadmap(self, domain):
        prompt = f"Generate a deep 6-phase technical roadmap for {domain} in JSON format."
        return self._get_json_response(prompt)
