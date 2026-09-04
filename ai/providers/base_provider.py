from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """
    Common interface that all LLM providers must adhere to.
    Guarantees standard inputs and outputs across Gemini, Ollama, etc.
    """

    @abstractmethod
    def generate_text(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Generates a raw string response."""
        pass

    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict = None, **kwargs) -> str:
        """Generates a text response optimized/formatted for JSON extraction."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the provider is currently online and configured properly."""
        pass
