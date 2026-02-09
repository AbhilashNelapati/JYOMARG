import os
import google.genai as genai
from dotenv import load_dotenv
import json
import re




load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

class ABHIAssistant:
    def __init__(self):
        # Initialize the new GenAI client
        self.client = genai.Client(api_key=api_key)
        
        self.instruction = (
            "You are ABHI (Artificial Being for Human Intelligence), the dual-role AI Tutor and Career Assistant for Project JYOMARG.\n\n"
            "ROLE 1: CAREER ASSISTANT (Old Features)\n"
            "- Help with course discovery and job portals.\n"
            "- Provide recommendations in Markdown Tables.\n\n"
            "ROLE 2: AI TUTOR (New Features)\n"
            "- Explain topics (e.g., 'What is Recursion?') directly in chat.\n"
            "- Format with bold headers and code blocks.\n\n"
            "ROADMAP GENERATION:\n"
            "- When asked for a roadmap, strictly follow the Phase -> Week -> Day -> Topics hierarchy.\n"
        )
        
        
        # Using Gemini 2.0 Flash - stable and widely available in new API
        self.model_name = "models/gemini-2.0-flash"
        print(f"[SYSTEM] AI Model set to: {self.model_name}")

    def _get_json_response(self, prompt):
        """Helper to get clean JSON from AI. Robust version with Logging."""
        
        def log_debug(msg):
            try:
                with open("debug_ai.log", "a", encoding="utf-8") as f:
                    f.write(f"{msg}\n")
            except:
                pass 
        
        try:
            log_debug(f"Generating for prompt: {prompt[:100]}...")
            
            # Request using new API
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        response_mime_type="application/json",
                        max_output_tokens=40000,  # Significantly increased for deep roadmaps
                        system_instruction=self.instruction
                    )
                )
            except Exception as outer_e:
                err_str = str(outer_e)
                # If any error with primary model, attempt fallback
                if "429" in err_str or "quota" in err_str.lower():
                    log_debug("PRIMARY QUOTA EXCEEDED. Attempting fallback to gemini-2.5-flash...")
                    response = self.client.models.generate_content(
                        model="models/gemini-2.5-flash",
                        contents=prompt,
                        config=genai.types.GenerateContentConfig(
                            response_mime_type="application/json",
                            max_output_tokens=40000,  # Significantly increased for deep roadmaps
                            system_instruction=self.instruction
                        )
                    )
                else:
                    raise outer_e

            raw_text = response.text.strip()
            log_debug(f"RAW RESP: {raw_text[:200]}")

            # Cleanup
            clean_json = raw_text
            if "```" in clean_json:
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_json, re.DOTALL | re.IGNORECASE)
                if match:
                    clean_json = match.group(1)
            
            clean_json = clean_json.strip()
            
            # Validate
            json.loads(clean_json)
            return clean_json

        except Exception as e:
            log_debug(f"CRITICAL ERROR: {e}")
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower():
                return '{"error": "AI Quota Exceeded on all models. Please wait 1 minute and retry."}'
            if "404" in err_str:
                return f'{{"error": "Model Error: {self.model_name} not found. Please check API access."}}'
            return f'{{"error": "AI Error: {err_str[:100]}..."}}'
    
    def analyze_skill_gap(self, resume_text, jd_text):
        prompt = f"Analyze Resume vs JD. Output JSON: {{'match_score': 0..100, 'skill_scores': {{}}, 'missing_skills': [], 'advice': ''}}"
        return self._get_json_response(prompt)

    def ask_abhi(self, user_input):
        prompt = f"User Query: {user_input}. Output JSON: {{'spoken_summary': '', 'display_content': ''}}"
        return self._get_json_response(prompt)

    def generate_job_alerts(self, user_profile):
        prompt = f"Generate 3 job alerts for: {user_profile}. Output JSON list."
        return self._get_json_response(prompt)

    def generate_course_syllabus(self, topic):
        prompt = f"Generate syllabus for {topic}. Phase/Week/Day JSON."
        return self._get_json_response(prompt)

    def generate_day_content(self, topic, day_title):
        prompt = f"Detailed Markdown tutorial for {topic} - {day_title}."
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=self.instruction
                )
            )
            return response.text.strip()
        except:
            return "Error generating content."
    
    def generate_assessment(self, topic, week_number, is_final=False):
        prompt = f"Generate quiz JSON for {topic}."
        return self._get_json_response(prompt)

    def generate_career_roadmap(self, domain):
        """Generates a DEEP 5-tier roadmap with optimized speed and global numbering."""
        prompt = f"""
Act as a Master Career Architect. Generate a fast, optimized, deep technical learning roadmap for: '{domain}'.

STRICT RULES:
1. HIERARCHY: Phase -> Week -> Day -> Topic -> Details.
2. GLOBAL WEEK NUMBERING: Week numbers must be continuous across phases. 
   - Example: Phase 1 (Weeks 1-4), Phase 2 (Weeks 5-8). DO NOT RESET week numbers inside new phases.
3. BREVITY is critical for speed.
   - "explanation": Max 5-8 words. Direct and concise.
   - "practice": 1 short, specific task.
4. STRUCTURE: 
   - 6 Phases total.
   - 2-3 Weeks per Phase.
   - 5 Days per Week.
   - 1-2 Topics per Day.

Output ONLY in this JSON format:
{{
    "title": "Professional Path to {domain}",
    "estimated_duration": "6 Months",
    "phases": [
        {{
            "phase_name": "Phase 1: Foundation",
            "weeks": [
                {{
                    "week_number": 1,  # Must continue from previous phase (e.g. 5, 6...)
                    "week_title": "Concept Clarity",
                    "days": [
                        {{
                            "day_number": 1,
                            "topics": [
                                {{
                                    "topic_name": "Topic Title",
                                    "explanation": "Brief concept summary.",
                                    "practice": "Hands-on task."
                                }}
                            ]
                        }}
                    ]
                }}
            ]
        }}
    ]
}}
Ensure valid JSON output.
        """
        return self._get_json_response(prompt)
