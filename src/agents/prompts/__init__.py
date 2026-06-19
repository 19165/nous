import os
from functools import lru_cache

@lru_cache(maxsize=16)
def load_prompt(filename: str) -> str:
    """
    Loads a prompt template from this prompts directory and caches the content.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()
