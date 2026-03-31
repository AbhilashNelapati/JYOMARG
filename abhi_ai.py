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
        # [MIGRATED] Now uses the decentralized ProviderRouter for Gemini/Ollama Fallback support
        from services.chat_service import handle_ask_abhi
        return handle_ask_abhi(user_input)

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
        # [MIGRATED in Phase 9] Deterministic week mapping
        from services.course_service import generate_hybrid_syllabus
        return generate_hybrid_syllabus(topic)

    def generate_day_content(self, topic, day_title):
        # [MIGRATED in Phase 9] Schema constrained JSON output rendered to Markdown
        from services.lesson_service import generate_hybrid_lesson
        return generate_hybrid_lesson(topic, day_title)

    def generate_assessment(self, topic, week_number, is_final=False):
        prompt = f"Generate 5 MCQs for {topic} Week {week_number}. Output ONLY as JSON: {{'questions': [{{'id': 1, 'question': '', 'options': ['', '', '', ''], 'answer': ''}}]}}"
        return self._get_json_response(prompt)

    def generate_career_roadmap(self, domain):
        # [MIGRATED in Phase 8] Now utilizes Hybrid Python logic for structural
        # integrity (phase/week counts) and LLM solely for learning content synthesis.
        from services.roadmap_service import generate_hybrid_roadmap
        return generate_hybrid_roadmap(domain)
    def check_ats_score(self, resume_text, jd_text):
        # [MIGRATED] Now uses deterministic Python logic for scoring
        # and delegating to the unified Provider Router for explanations via LLM
        from services.ats_service import analyze_hybrid_ats
        return analyze_hybrid_ats(resume_text, jd_text)
