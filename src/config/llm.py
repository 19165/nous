import logging
from langchain_ollama import ChatOllama
from src.config.settings import settings

logger = logging.getLogger(__name__)

def get_llm():
    """
    Factory function to instantiate and return the configured LLM client.
    Easily configurable to switch between Ollama, OpenAI, Gemini, etc.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "ollama":
        logger.info(f"Initializing ChatOllama model: {settings.OLLAMA_MODEL}")
        kwargs = {}
        if settings.OLLAMA_BASE_URL:
            kwargs["base_url"] = settings.OLLAMA_BASE_URL
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            **kwargs
        )
        
    elif provider == "openai":
        logger.info(f"Initializing ChatOpenAI model: {settings.OPENAI_MODEL}")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY
        )
        
    elif provider == "gemini":
        logger.info(f"Initializing ChatGoogleGenerativeAI model: {settings.GEMINI_MODEL}")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY
        )
        
    else:
        logger.error(f"Unsupported LLM provider: {provider}. Falling back to default Ollama.")
        return ChatOllama(model=settings.OLLAMA_MODEL)
