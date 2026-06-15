import logging
from src.agents.state import AgentState
from src.agents.nodes.schemas import reviewer_parser
from .prompts import REVIEWER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class ReviewerNode:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: AgentState):
        """
        Evaluates findings for relevance, quality, and completeness.
        Assigns confidence scores and ranks findings by source quality.
        """
        logger.info("--- Executing Reviewer Node ---")
        query = state.get("query", "")
        findings = state.get("findings", [])
        current_retry = state.get("retry_count", 0)

        system_msg = REVIEWER_SYSTEM_PROMPT.format(
            format_instructions=reviewer_parser.get_format_instructions()
        )

        user_msg = f"Original Query: {query}\nIteration: {current_retry}\n\nFindings gathered so far:\n" + "\n".join(findings)

        messages = [("system", system_msg), ("human", user_msg)]
        
        # Invoke LLM with structured output guidance
        response = self.llm.invoke(messages)
        
        try:
            # Parse the structured output
            output = reviewer_parser.parse(response.content)
            
            # Prepare confidence_scores map (using content as key for now as requested)
            conf_scores = {rf.content: rf.confidence_score for rf in output.ranked_findings}
            
            # Convert RankedFinding models back to dicts for AgentState compatibility
            ranked_dicts = [rf.model_dump() for rf in output.ranked_findings]

            return {
                "reviewer_feedback": {"reason": output.feedback},
                "decision": output.decision,
                "ranked_findings": ranked_dicts,
                "confidence_scores": conf_scores,
                "reviewed_findings": [rf.content for rf in output.ranked_findings],
                "retry_count": current_retry + 1
            }
        except Exception as e:
            logger.error(f"Error parsing reviewer output: {e}")
            # Fallback if parsing fails
            return {
                "decision": "SUFFICIENT", 
                "reviewer_feedback": {"reason": "Error in parsing, defaulting to sufficient."},
                "retry_count": current_retry + 1
            }

