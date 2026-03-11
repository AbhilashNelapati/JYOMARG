import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

import hashlib
from database import get_cached_ai_response, save_ai_response_to_cache

class ABHIAssistant:
    def __init__(self):
        if not api_key:
            print("[CRITICAL] GOOGLE_API_KEY is missing!")
        
        # Using 1.5-flash as it's often more stable for free-tier quotas than 2.0-flash previews
        self.model_name = "gemini-3-flash-preview" 
        self.fallback_model_name = "gemini-flash-latest"
        
        try:
            self.model = genai.GenerativeModel(model_name=self.model_name)
            print(f"[SYSTEM] AI Initialized with {self.model_name}")
        except:
            self.model = genai.GenerativeModel(model_name=self.fallback_model_name)
            print(f"[SYSTEM] AI Falling back to {self.fallback_model_name}")

    def _get_json_response(self, prompt):
        import time
        import random
        
        # 1. Check Cache First
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        cached = get_cached_ai_response(prompt_hash)
        if cached:
            print(f"[CACHE] Hit for prompt hash: {prompt_hash[:10]}")
            return cached

        max_attempts = 5
        full_prompt = f"SYSTEM: You are ABHI AI. You MUST output ONLY valid JSON. No conversational text.\nUSER: {prompt}"
        
        for attempt in range(max_attempts):
            try:
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
                
                clean_json = clean_json.strip()
                json.loads(clean_json) # Validate JSON
                
                # 2. Save Successfully Parsed Response to Cache
                save_ai_response_to_cache(prompt_hash, clean_json)
                return clean_json
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    if attempt < max_attempts - 1:
                        wait_time = (2 ** attempt) * 5 + random.uniform(0, 1)
                        print(f"[SYSTEM] Rate limit hit (Attempt {attempt+1}/{max_attempts}). Retrying in {wait_time:.1f}s...")
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

    def generate_job_alerts(self, user_profile, existing_jobs=None):
        existing_str = ""
        if existing_jobs:
            existing_str = f" DO NOT recommend any of these previously recommended jobs or companies: {', '.join(existing_jobs)}. "
            
        prompt = (
            f"Based on this profile: {user_profile}, generate 3 realistic job alerts relevant to their skills. "
            f"STRICT REQUIREMENT: Only include jobs that were posted within the LAST 3 TO 4 DAYS.{existing_str} "
            f"Output ONLY as JSON: {{'jobs': [{{'job_title': '', 'company': '', 'match_score': 0-100, 'reason': '', 'apply_link': ''}}]}}"
        )
        # Avoid caching if we have existing jobs, or hash existing jobs as well, by ensuring existing_jobs affects the prompt, which it does.
        return self._get_json_response(prompt)

    def generate_course_syllabus(self, topic):
        prompt = f"Generate a week-wise syllabus for {topic}. Output ONLY as JSON: {{'course_title': '', 'description': '', 'weeks': [{{'week_number': 1, 'title': '', 'days': [{{'day_number': 1, 'title': ''}}]}}]}}"
        return self._get_json_response(prompt)

    def generate_day_content(self, topic, day_title):
        import time
        import random
        
        prompt = f"Write a detailed professional markdown guide for {topic}: {day_title}. Focus on practical examples."
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        
        # 1. Check Cache
        cached = get_cached_ai_response(prompt_hash)
        if cached:
            print(f"[CACHE] Content Hit for: {topic} - {day_title}")
            return cached

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                response = self.model.generate_content(prompt)
                if not response or not hasattr(response, 'text'):
                    raise Exception("Empty response from AI")
                
                content = response.text.strip()
                # 2. Save to Cache
                save_ai_response_to_cache(prompt_hash, content)
                return content
                
            except Exception as e:
                error_str = str(e)
                if ("429" in error_str or "quota" in error_str.lower()) and attempt < max_attempts - 1:
                    wait_time = (2 ** attempt) * 5 + random.uniform(0, 1)
                    print(f"[SYSTEM] Content generation Rate limit hit (Attempt {attempt+1}/{max_attempts}). Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
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
    def check_ats_score(self, resume_text, jd_text):
        prompt = (
            f"Act as an expert ATS (Applicant Tracking System) optimizer. "
            f"Analyze the following Resume against the Job Description. "
            f"Resume: {resume_text}\n"
            f"Job Description: {jd_text}\n"
            f"Output ONLY a JSON object with keys: "
            f"'score' (0-100), "
            f"'keyword_matches' (list of matched keywords), "
            f"'missing_keywords' (list of keywords to add), "
            f"'formatting_score' (0-100), "
            f"'content_suggestions' (list of specific improvements), "
            f"'alignment_suggestions' (list of specific layout/alignment suggestions for a professional look), "
            f"'jd_matches_highlighted' (list of phrases/sections from the resume that already perfectly match the JD or role requirements), "
            f"'ai_improved_resume' (a professionally rewritten version of the resume optimized for this JD, maintaining a clear professional structure with headings and bullet points)."
        )
        return self._get_json_response(prompt)
