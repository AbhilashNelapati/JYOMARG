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
        
        # Configure with legacy SDK
        genai.configure(api_key=api_key or "DUMMY_KEY")
        
        # Most universal model name for this SDK
        self.model_name = "gemini-1.5-flash"
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=(
                "You are ABHI, the AI Tutor and Career Assistant for Project JYOMARG. "
                "Always output valid JSON when requested."
            )
        )
        print(f"[SYSTEM] AI Initialized with {self.model_name}")

    def _get_json_response(self, prompt):
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.strip()
            
            # Extract JSON from Markdown
            clean_json = raw_text
            if "```" in clean_json:
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_json, re.DOTALL | re.IGNORECASE)
                if match: clean_json = match.group(1)
            
            # Simple validation
            json.loads(clean_json.strip())
            return clean_json.strip()
        except Exception as e:
            print(f"[ERROR] AI Failed: {e}")
            return f'{{"error": "AI Logic Failed: {str(e)[:100]}"}}'

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
