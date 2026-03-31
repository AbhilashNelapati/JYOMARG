import requests
from .base_provider import BaseProvider

class OllamaProvider(BaseProvider):
    """
    Integration for local Ollama models.
    Communicates over HTTP to localhost.
    """
    def __init__(self, host="http://localhost:11434", default_model="llama3"):
        self.host = host
        self.model = default_model

    def is_available(self) -> bool:
        try:
            # Quick alive check
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def generate_text(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"System Guidelines:\n{system_prompt}\n\nUser Input:\n{user_prompt}",
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "").strip()

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict = None, **kwargs) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"System Guidelines:\n{system_prompt}\n\nUser Input:\n{user_prompt}",
            "format": "json",
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "").strip()
