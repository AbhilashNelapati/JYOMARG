from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider

class ProviderRouter:
    """
    Selects the right LLM provider (Ollama or Gemini) and manages fallbacks.
    """
    def __init__(self):
        self.gemini = GeminiProvider()
        self.ollama = OllamaProvider()

    def route_text(self, system_prompt: str, user_prompt: str, prefer_local: bool = False) -> str:
        from utils.logger import log
        
        # Attempt Ollama first if preferred and available
        if prefer_local and self.ollama.is_available():
            try:
                log.info("Routing text task to [Ollama]...")
                return self.ollama.generate_text(system_prompt, user_prompt)
            except Exception as e:
                log.warning(f"Ollama text generation failed: {e}. Executing Fallback -> Gemini.")
        
        # Fallback to Gemini
        if self.gemini.is_available():
            log.info("Routing text task to [Gemini]...")
            return self.gemini.generate_text(system_prompt, user_prompt)
            
        raise Exception("No active providers available for text generation.")

    def route_json(self, system_prompt: str, user_prompt: str, schema: dict = None, prefer_local: bool = False) -> str:
        from utils.logger import log
        
        # Attempt Ollama first if preferred and available
        if prefer_local and self.ollama.is_available():
            try:
                log.info("Routing JSON task to [Ollama]...")
                return self.ollama.generate_json(system_prompt, user_prompt, schema)
            except Exception as e:
                log.warning(f"Ollama JSON generation failed: {e}. Executing Fallback -> Gemini.")
        
        # Fallback to Gemini
        if self.gemini.is_available():
            log.info("Routing JSON task to [Gemini]...")
            return self.gemini.generate_json(system_prompt, user_prompt, schema)
            
        raise Exception("No active providers available for JSON generation.")
