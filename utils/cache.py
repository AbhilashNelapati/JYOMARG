import hashlib
from typing import Optional, Dict

# Simple in-memory cache initially, to be expanded to Redis/SQLite later
_IN_MEMORY_CACHE: Dict[str, str] = {}

def get_cache_key(prefix: str, *args) -> str:
    """
    Generates a reliable SHA256 hash using the prefix and core inputs.
    e.g., get_cache_key("chat", "How to learn python?")
    """
    raw_string = f"{prefix}:" + "|".join(str(a) for a in args)
    return hashlib.sha256(raw_string.encode()).hexdigest()

def get_cached_result(key: str) -> Optional[str]:
    """Retrieves standard string cache."""
    return _IN_MEMORY_CACHE.get(key)

def set_cached_result(key: str, value: str):
    """Sets standard string cache."""
    _IN_MEMORY_CACHE[key] = value
