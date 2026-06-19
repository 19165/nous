import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # --- Discord Configuration ---
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")

    # --- LLM Provider Configuration ---
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # e.g., 'ollama', 'openai', 'gemini'
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "")  # Empty defaults to localhost:11434

    # Future-proofing for other LLMs
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

    # --- Search Tools Configuration ---
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # --- LangSmith Configuration ---
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_TRACING: str = os.getenv("LANGSMITH_TRACING", "false")
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "test_environment_01")

    # --- Agent Configuration Constants ---
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "bot.log")

settings = Settings()
