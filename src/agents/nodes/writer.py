import logging
from src.agents.state import AgentState

logger = logging.getLogger(__name__)

class WriterNode:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: AgentState):
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
        response = self.llm.invoke(messages)
        return {"summary": response.content}
