import logging
import json
from typing import List, Optional
from pydantic import BaseModel, Field, AliasChoices
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.agents.state import AgentState
from src.tools.search import get_web_search_tool, get_news_search_tool

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOllama(model="gemma4:31b-cloud")


class ResearchStep(BaseModel):
    """Information for the researcher in each step."""

    task_id: int = Field(description="Unique ID for the task")
    query: str = Field(description="Search query to use")
    rationale: str = Field(description="Reason for this search")
    tool_name: str = Field(description="Tool to use: 'web_search' or 'news_search'")


class ResearchPlan(BaseModel):
    """The main output from the Planner Node."""

    original_query: str = Field(description="The user's original query")
    steps: List[ResearchStep] = Field(description="List of search steps")
    estimated_complexity: str = Field(description="Complexity (High, Medium, Low)")


# Initialize Parser
parser = PydanticOutputParser(pydantic_object=ResearchPlan)


def planner_node(state: AgentState):
    """
    Analyzes the user query and generates a structured research plan.
    Uses explicit PydanticOutputParser and Few-Shot prompting for reliability.
    """
    logger.info("--- Executing Planner Node ---")
    query = state.get("query", "")

    # Define system prompt with format instructions
    format_instructions = parser.get_format_instructions()

    system_prompt = (
        "You are an expert research planner. Your goal is to break down a complex topic "
        "into 3-5 logical search steps. \n\n"
        "{format_instructions}\n\n"
        "This is tool list that you can use :"
        "[web_search, news_search]"
        "EXAMPLE:\n"
        "User Query: 'Impact of AI on healthcare 2024'\n"
        "Response:\n"
        "```json\n"
        "{{\n"
        '  "original_query": "Impact of AI on healthcare 2024",\n'
        '  "steps": [\n'
        '    {{"task_id": 1, "query": "AI in healthcare trends 2024", "rationale": "Get overview", "tool_name": "web_search"}},\n'
        '    {{"task_id": 2, "query": "FDA approved AI medical devices 2024", "rationale": "Check regulation", "tool_name": "news_search"}}\n'
        "  ],\n"
        '  "estimated_complexity": "Medium"\n'
        "}}\n"
        "```"
    )

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", "Research Topic: {query}")]
    )

    # Construct the full prompt
    chain = prompt | llm

    try:
        response = chain.invoke(
            {"query": query, "format_instructions": format_instructions}
        )

        # Clean response content if needed (sometimes Ollama adds text before/after triple backticks)
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        plan = parser.parse(content)
        return {"plan": plan.model_dump()}

    except Exception as e:
        logger.error(f"Planner Node parsing failed: {e}")
        # Robust Fallback
        fallback_plan = {
            "original_query": query,
            "steps": [
                {
                    "task_id": 1,
                    "query": query,
                    "rationale": "Fallback due to planning error",
                    "tool_name": "web_search",
                }
            ],
            "estimated_complexity": "Unknown",
        }
        return {"plan": fallback_plan}


def researcher_node(state: AgentState):
    """
    Gathers information based on the structured research plan.
    """
    logger.info("--- Executing Researcher Node ---")
    plan = state.get("plan", {})
    steps = plan.get("steps", [])

    web_tool = get_web_search_tool()
    news_tool = get_news_search_tool()

    all_findings = []

    for step in steps:
        tool_name = step.get("tool_name")
        search_query = step.get("query")
        logger.info(
            f"Step {step.get('task_id')}: Using {tool_name} for '{search_query}'"
        )

        try:
            if tool_name == "web_search":
                results = web_tool.invoke({"query": search_query})
                prefix = "Web"
            elif tool_name == "news_search":
                results = news_tool.invoke({"query": search_query})
                prefix = "News"
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                continue

            # Reuse the processing logic to parse findings
            process_results(results, prefix, all_findings)

        except Exception as e:
            logger.error(f"Search failed for step {step.get('task_id')}: {e}")

    if not all_findings:
        logger.warning("No findings were generated from search steps.")
        all_findings = ["No search results found for the given queries."]

    return {"findings": all_findings}


def process_results(results, prefix, findings_list):
    """Helper to process search results into strings."""
    # Case 1: Results is a dictionary (The standard Tavily response)
    if isinstance(results, dict):
        actual_results = results.get("results", [])
        if isinstance(actual_results, list):
            for res in actual_results:
                if isinstance(res, dict):
                    content = res.get("content", str(res))
                    url = res.get("url", "No URL")
                    findings_list.append(f"[{prefix}] {content} (Source: {url})")
                else:
                    findings_list.append(f"[{prefix}] {res}")
        else:
            findings_list.append(f"[{prefix}] {results}")

    # Case 2: Results is already a list
    elif isinstance(results, list):
        for res in results:
            if isinstance(res, dict):
                content = res.get("content", str(res))
                url = res.get("url", "No URL")
                findings_list.append(f"[{prefix}] {content} (Source: {url})")
            elif isinstance(res, str):
                findings_list.append(f"[{prefix}] {res}")
            else:
                findings_list.append(
                    f"[{prefix}] Received non-standard result type: {type(res)}"
                )

    # Case 3: Results is a string
    elif isinstance(results, str):
        findings_list.append(f"[{prefix}] {results}")

    # Case 4: Unexpected format
    else:
        logger.warning(f"Unexpected results format from {prefix}: {type(results)}")


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
