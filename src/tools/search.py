import os
from langchain_tavily import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()

def get_web_search_tool():
    """
    Returns a Tavily web search tool for general research.
    """
    return TavilySearchResults(
        max_results=5,
        search_depth="advanced"
    )

def get_news_search_tool():
    """
    Returns a Tavily search tool optimized for news.
    """
    # Note: topic="news" is supported in the underlying Tavily API
    # and passed through via kwargs in some versions, or explicitly in others.
    # In langchain-tavily, we can pass it to the constructor.
    return TavilySearchResults(
        max_results=5,
        topic="news",
        search_depth="advanced"
    )
