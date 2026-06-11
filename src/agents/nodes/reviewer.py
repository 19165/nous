import logging
from src.agents.state import AgentState

logger = logging.getLogger(__name__)

class ReviewerNode:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: AgentState):
        """
        Evaluates findings for relevance and completeness.
        """
        logger.info("--- Executing Reviewer Node ---")
        query = state.get("query", "")
        findings = state.get("findings", [])

        system_msg = "You are a research reviewer. Filter the findings for relevance and remove duplicates. Keep only high-quality information."
        user_msg = f"Topic: {query}\n\nFindings:\n" + "\n".join(findings)

        messages = [("system", system_msg), ("human", user_msg)]
        response = self.llm.invoke(messages)
        return {"reviewed_findings": [response.content]}
