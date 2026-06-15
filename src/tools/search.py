import os
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()


@lru_cache(maxsize=1)
def get_web_search_tool():
    """
    Returns a Tavily web search tool for general research.
    """
    return TavilySearch(max_results=5, topic="general", search_depth="advanced")


@lru_cache(maxsize=1)
def get_news_search_tool():
    """
    Returns a Tavily search tool optimized for news.
    """
    # Note: topic="news" is supported in the underlying Tavily API
    # and passed through via kwargs in some versions, or explicitly in others.
    # In langchain-tavily, we can pass it to the constructor.
    return TavilySearch(max_results=5, topic="news", search_depth="advanced")
