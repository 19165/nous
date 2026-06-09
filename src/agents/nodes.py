import logging
from typing import List
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from src.agents.state import AgentState
from src.tools.search import get_web_search_tool, get_news_search_tool

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize LLM
# Note: Ensure OPENAI_API_KEY is set in environment
llm = ChatOllama(model="gemma4:31b-cloud")


# IMPORTANT!!!
# ปรับ planner_node ให้ส่ง output แบบ "structured output" เพื่อที่ "researcher_node" สามารถนำ plan (output ก่อนหน้า) มาใช้ได้
def planner_node(state: AgentState):
    """
    Analyzes the user query and generates a research plan.
    """
    logger.info("--- Executing Planner Node ---")
    query = state.get("query", "")

    system_msg = "You are a research planner. Generate a clear research plan with 3-5 objectives for the given topic."
    user_msg = f"Research Topic: {query}"

    messages = [("system", system_msg), ("human", user_msg)]

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
    try:
        web_results = web_tool.invoke({"query": query})
        logger.debug(f"Web results type: {type(web_results)}")
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        web_results = []

    logger.info(f"Performing news search for: {query}")
    try:
        news_results = news_tool.invoke({"query": query})
        logger.debug(f"News results type: {type(news_results)}")
    except Exception as e:
        logger.error(f"News search failed: {e}")
        news_results = []

    # Combine results into a list of strings for findings with robust validation
    findings = []

    def process_results(results, prefix):
        # Case 1: Results is a dictionary (The standard Tavily response)
        if isinstance(results, dict):
            # Try to get the list of results from the 'results' key
            actual_results = results.get("results", [])
            if isinstance(actual_results, list):
                for res in actual_results:
                    if isinstance(res, dict):
                        content = res.get("content", str(res))
                        url = res.get("url", "No URL")
                        findings.append(f"[{prefix}] {content} (Source: {url})")
                    else:
                        findings.append(f"[{prefix}] {res}")
            else:
                # If 'results' key isn't a list, maybe the dict itself is interesting
                findings.append(f"[{prefix}] {results}")

        # Case 2: Results is already a list
        elif isinstance(results, list):
            for res in results:
                if isinstance(res, dict):
                    content = res.get("content", str(res))
                    url = res.get("url", "No URL")
                    findings.append(f"[{prefix}] {content} (Source: {url})")
                elif isinstance(res, str):
                    findings.append(f"[{prefix}] {res}")
                else:
                    findings.append(
                        f"[{prefix}] Received non-standard result type: {type(res)}"
                    )

        # Case 3: Results is a string
        elif isinstance(results, str):
            findings.append(f"[{prefix}] {results}")

        # Case 4: Unexpected format
        else:
            logger.warning(f"Unexpected results format from {prefix}: {type(results)}")

    process_results(web_results, "Web")
    process_results(news_results, "News")

    if not findings:
        logger.warning("No findings were generated from search tools.")
        findings = ["No search results found for the given query."]

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

    messages = [("system", system_msg), ("human", user_msg)]

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

    messages = [("system", system_msg), ("human", user_msg)]

    response = llm.invoke(messages)
    return {"summary": response.content}
