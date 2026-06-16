import logging
from src.agents.state import AgentState
from .prompts import WRITER_SYSTEM_PROMPT, WRITER_USER_TEMPLATE

logger = logging.getLogger(__name__)

class WriterNode:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: AgentState):
        """
        Generates the final report for Discord using ranked findings.
        """
        logger.info("--- Executing Writer Node ---")
        query = state.get("query", "")
        # Use ranked findings for better quality
        ranked_findings = state.get("ranked_findings", [])
        
        findings_text = ""
        if ranked_findings:
            findings_text = "\n".join([
                f"- [{f.get('source_type', 'Unknown')}] {f.get('content')} (Confidence: {f.get('confidence_score')})" 
                for f in ranked_findings
            ])
        else:
            # Fallback to reviewed_findings if ranked_findings not available
            reviewed_findings = state.get("reviewed_findings", [])
            findings_text = "\n".join(reviewed_findings)

        user_msg = WRITER_USER_TEMPLATE.format(
            query=query,
            findings_text=findings_text
        )

        messages = [("system", WRITER_SYSTEM_PROMPT), ("human", user_msg)]
        response = self.llm.invoke(messages)
        return {
            "summary": response.content,
            "progress_stage": "Writing report",
            "workflow_status": "completed"
        }
