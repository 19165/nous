import logging
from typing import List
from langchain_openai import ChatOpenAI
from src.agents.state import AgentState
from src.tools.search import get_web_search_tool, get_news_search_tool

logger = logging.getLogger(__name__)

# Initialize LLM
# Note: Ensure OPENAI_API_KEY is set in environment
llm = ChatOpenAI(model="gpt-4o")

def planner_node(state: AgentState):
    """
    Analyzes the user query and generates a research plan.
    """
    logger.info("--- Executing Planner Node ---")
    query = state.get("query", "")
    
    system_msg = "You are a research planner. Generate a clear research plan with 3-5 objectives for the given topic."
    user_msg = f"Research Topic: {query}"
    
    messages = [
        ("system", system_msg),
        ("human", user_msg)
    ]
    
    response = llm.invoke(messages)
    return {"plan": response.content}

def researcher_node(state: AgentState):
    """
    Gathers information using web and news search tools.
    """
    logger.info("--- Executing Researcher Node ---")
    query = state.get("query", "")
    
    web_tool = get_web_search_tool()
    news_tool = get_news_search_tool()
    
    logger.info(f"Performing web search for: {query}")
    web_results = web_tool.invoke({"query": query})
    
    logger.info(f"Performing news search for: {query}")
    news_results = news_tool.invoke({"query": query})
    
    # Combine results into a list of strings for findings
    findings = []
    for res in web_results:
        findings.append(f"[Web] {res.get('content', '')} (Source: {res.get('url', '')})")
    for res in news_results:
        findings.append(f"[News] {res.get('content', '')} (Source: {res.get('url', '')})")
        
    return {"findings": findings}

def reviewer_node(state: AgentState):
    """
    Evaluates findings for relevance and completeness.
    """
    logger.info("--- Executing Reviewer Node ---")
    query = state.get("query", "")
    findings = state.get("findings", [])
    
    system_msg = "You are a research reviewer. Filter the findings for relevance and remove duplicates. Keep only high-quality information."
    user_msg = f"Topic: {query}\n\nFindings:\n" + "\n".join(findings)
    
    messages = [
        ("system", system_msg),
        ("human", user_msg)
    ]
    
    response = llm.invoke(messages)
    # We store the cleaned text as a single entry in reviewed_findings for now
    return {"reviewed_findings": [response.content]}

def writer_node(state: AgentState):
    """
    Generates the final TL;DR summary for Discord.
    """
    logger.info("--- Executing Writer Node ---")
    query = state.get("query", "")
    reviewed_findings = state.get("reviewed_findings", [])
    
    system_msg = "You are a technical writer. Generate a concise TL;DR summary optimized for Discord (Markdown)."
    user_msg = (
        f"Topic: {query}\n\n"
        f"Reviewed Research:\n" + "\n".join(reviewed_findings) + "\n\n"
        "Please format your response exactly as follows:\n"
        "## Topic: [Topic Name]\n"
        "### Key Findings\n"
        "[Bullet points of key findings]\n\n"
        "### TL;DR Summary\n"
        "[3-5 high-level bullet points summary]"
    )
    
    messages = [
        ("system", system_msg),
        ("human", user_msg)
    ]
    
    response = llm.invoke(messages)
    return {"summary": response.content}
