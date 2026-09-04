import os
import google.generativeai as genai
from .base_provider import BaseProvider

class GeminiProvider(BaseProvider):
    """
    Integration for Google's Gemini Models.
    Separates the initialization logic outward from application behavior.
    """
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
        self.model_name = "gemini-3-flash-preview"
        self.fallback_model_name = "gemini-flash-latest"
        
        try:
            self.model = genai.GenerativeModel(model_name=self.model_name)
        except Exception:
            self.model = genai.GenerativeModel(model_name=self.fallback_model_name)

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_text(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        full_prompt = f"SYSTEM: {system_prompt}\nUSER: {user_prompt}"
        response = self.model.generate_content(full_prompt)
        
        if not response or not hasattr(response, 'text'):
            raise Exception("Empty text response from Gemini")
            
        return response.text.strip()

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict = None, **kwargs) -> str:
        full_prompt = f"SYSTEM: {system_prompt}\nIMPORTANT: You MUST output ONLY valid JSON. No conversational text.\nUSER: {user_prompt}"
        response = self.model.generate_content(full_prompt)
        
        if not response or not hasattr(response, 'text'):
            raise Exception("Empty JSON response from Gemini")
            
        return response.text.strip()
