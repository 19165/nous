import logging
from src.agents.state import AgentState
from src.agents.nodes.schemas import reviewer_parser

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

        system_msg = (
            "You are an expert Research Reviewer. Your task is to evaluate the collected findings "
            "based on the original research query. \n\n"
            "Guidelines:\n"
            "1. Assess if the findings sufficiently answer the query. If not, mark as INSUFFICIENT and provide specific feedback.\n"
            "2. For each finding, identify the source type and assign a confidence score (0-100).\n"
            "3. Source Ranking Priority: Official > News > Academic > Blog > Opinion > Unknown.\n"
            "4. Provide a structured response including your decision, detailed feedback, and a list of ranked findings.\n\n"
            f"{reviewer_parser.get_format_instructions()}"
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
                "reviewed_findings": [rf.content for rf in output.ranked_findings]
            }
        except Exception as e:
            logger.error(f"Error parsing reviewer output: {e}")
            # Fallback if parsing fails
            return {
                "decision": "SUFFICIENT", 
                "reviewer_feedback": {"reason": "Error in parsing, defaulting to sufficient."}
            }

