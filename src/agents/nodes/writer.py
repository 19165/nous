import logging
from src.agents.schemas import AgentState
from src.agents.prompts import load_prompt

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
            if reviewed_findings:
                findings_text = "\n".join(reviewed_findings)
            else:
                # Fallback to raw findings if reviewer was bypassed (e.g. general route)
                findings = state.get("findings", [])
                findings_text = "\n".join([f"- {f}" for f in findings])

        writer_user_template = load_prompt("writer/user.txt")
        user_msg = writer_user_template.format(
            query=query,
            findings_text=findings_text
        )

        # Determine the appropriate writer system prompt based on query_type
        query_type = state.get("query_type", "UNKNOWN")
        logger.info(f"[Writer Node] Loading prompt strategy for query_type: {query_type}")
        if query_type == "NEWS":
            system_prompt = load_prompt("writer/v2_news.txt")
        elif query_type == "LEARNING":
            system_prompt = load_prompt("writer/v2_learning.txt")
        elif query_type == "COMPARISON":
            system_prompt = load_prompt("writer/v2_comparison.txt")
        else:
            system_prompt = load_prompt("writer/v2_general.txt")

        messages = [("system", system_prompt), ("human", user_msg)]
        response = self.llm.invoke(messages)
        return {
            "summary": response.content,
            "progress_stage": "Writing report",
            "workflow_status": "completed"
        }
