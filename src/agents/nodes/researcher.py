import logging
from src.agents.state import AgentState
from .utils import process_results

logger = logging.getLogger(__name__)

class ResearcherNode:
    def __init__(self, web_tool, news_tool):
        self.web_tool = web_tool
        self.news_tool = news_tool

    def __call__(self, state: AgentState):
        """
        Gathers information based on the structured research plan.
        """
        logger.info("--- Executing Researcher Node ---")
        plan = state.get("plan", {})
        steps = plan.get("steps", [])
        all_findings = []

        for step in steps:
            tool_name = step.get("tool_name")
            search_query = step.get("query")
            logger.info(f"Step {step.get('task_id')}: Using {tool_name} for '{search_query}'")

            try:
                if tool_name == "web_search":
                    results = self.web_tool.invoke({"query": search_query})
                    prefix = "Web"
                elif tool_name == "news_search":
                    results = self.news_tool.invoke({"query": search_query})
                    prefix = "News"
                else:
                    logger.warning(f"Unknown tool: {tool_name}")
                    continue

                process_results(results, prefix, all_findings)

            except Exception as e:
                logger.error(f"Search failed for step {step.get('task_id')}: {e}")

        if not all_findings:
            logger.warning("No findings were generated from search steps.")
            all_findings = ["No search results found for the given queries."]

        return {"findings": all_findings}
