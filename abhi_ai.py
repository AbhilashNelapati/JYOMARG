import os
import google.genai as genai
from dotenv import load_dotenv
import json
import re




load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

class ABHIAssistant:
    def __init__(self):
        # API Key check
        if not api_key:
            print("[CRITICAL] GOOGLE_API_KEY is missing from .env file!")
            
        # Initialize the new GenAI client
        if not api_key or api_key == "DUMMY_KEY":
             print("[CRITICAL] GOOGLE_API_KEY IS MISSING! Please add it to your Railway/Vercel Variables.")
             self.client = None
        else:
             self.client = genai.Client(api_key=api_key)
        
        # --- ROBUST MODEL SELECTION ---
        self.model_name = "gemini-1.5-flash" 
        
        if self.client:
            try:
                print("[SYSTEM] Discovering available models...")
                available_models = []
                for model in self.client.models.list():
                    if "gemini" in model.name.lower() and "generateContent" in model.supported_generation_methods:
                        clean_name = model.name.replace("models/", "")
                        available_models.append(clean_name)
                
                print(f"[SYSTEM] Found models: {available_models}")
                priorities = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
                for p in priorities:
                    if p in available_models:
                        self.model_name = p
                        break
                print(f"[SYSTEM] Selected: {self.model_name}")
            except Exception as e:
                print(f"[ERROR] Discovery failed: {e}")

        self.instruction = (
            "You are ABHI (Artificial Being for Human Intelligence), the dual-role AI Tutor and Career Assistant for Project JYOMARG.\n\n"
            "ROLE 1: CAREER ASSISTANT\n"
            "- Help with course discovery and job portals.\n"
            "ROLE 2: AI TUTOR\n"
            "- Explain topics directly in chat with bold headers.\n"
        )

    def _get_json_response(self, prompt):
        """Helper to get clean JSON from AI. Robust version with fallback."""
        if not self.client:
             return '{"error": "AI Config Error: GOOGLE_API_KEY is missing from environment variables."}'
             
        try:
            # Attempt with the auto-discovered model
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=10000,
                    system_instruction=self.instruction
                )
            )
            raw_text = response.text.strip()
            
            # Cleanup Markdown backticks if AI adds them
            clean_json = raw_text
            if "```" in clean_json:
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_json, re.DOTALL | re.IGNORECASE)
                if match: clean_json = match.group(1)
            
            # Validate JSON
            json.loads(clean_json.strip())
            return clean_json.strip()

        except Exception as e:
            print(f"[ERROR] AI Logic Failed for {self.model_name}: {e}")
            # Final Fallback Attempt with gemini-1.5-flash (Standard)
            if self.model_name != "gemini-1.5-flash":
                try:
                    print("[SYSTEM] Attempting final fallback to gemini-1.5-flash...")
                    response = self.client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt,
                        config=genai.types.GenerateContentConfig(
                            response_mime_type="application/json",
                            system_instruction=self.instruction
                        )
                    )
                    return response.text.strip()
                except:
                    pass
            
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower():
                return '{"error": "AI Quota Exceeded. Please wait 1 minute."}'
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
        prompt = f"""
        Generate a comprehensive learning syllabus for the topic: '{topic}'.
        STRICT RULES:
        1. Use ONLY lowercase keys in the JSON (e.g., 'weeks', 'days', 'title', 'day_number').
        2. Format: Phase -> weeks -> days.
        
        Output ONLY valid JSON in this structure:
        {{
            "title": "Mastering {topic}",
            "description": "A detailed course to master {topic} from scratch.",
            "weeks": [
                {{
                    "week_number": 1,
                    "title": "Introduction to {topic}",
                    "days": [
                        {{ "day_number": 1, "title": "Basics of {topic}" }},
                        {{ "day_number": 2, "title": "Fundamental Concepts" }},
                        ...
                    ]
                }}
            ]
        }}
        Provide 4-8 weeks of content.
        """
        return self._get_json_response(prompt)

    def generate_day_content(self, topic, day_title):
        prompt = f"Detailed Markdown tutorial for {topic} - {day_title}."
        try:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(system_instruction=self.instruction)
                )
            except Exception as e:
                # Fallback on any error for content generation
                response = self.client.models.generate_content(
                    model="models/gemini-1.5-flash",
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(system_instruction=self.instruction)
                )
            return response.text.strip()
        except:
            return "Error generating content. Please retry."
    
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
