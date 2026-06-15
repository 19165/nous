import logging
from langchain_core.prompts import ChatPromptTemplate
from src.agents.state import AgentState
from .schemas import parser
from .prompts import PLANNER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class PlannerNode:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: AgentState):
        """
        Analyzes the user query and generates a structured research plan.
        Incorporates reviewer feedback if available.
        """
        logger.info("--- Executing Planner Node ---")
        query = state.get("query", "")
        reviewer_feedback = state.get("reviewer_feedback", {})
        retry_count = state.get("retry_count", 0)
        format_instructions = parser.get_format_instructions()

        # Add feedback to prompt if this is a retry
        feedback_prompt = ""
        if retry_count > 0 and reviewer_feedback:
            feedback_prompt = (
                "\n\n--- PREVIOUS ATTEMPT FEEDBACK ---\n"
                "Your previous research plan was marked as INSUFFICIENT for the following reason:\n"
                f"{reviewer_feedback.get('reason', 'N/A')}\n"
                "Please generate a REVISED plan that specifically addresses this missing information "
                "and improves the overall research quality. Avoid repeating unnecessary search steps.\n"
                "-----------------------------------\n"
            )

        system_prompt = PLANNER_SYSTEM_PROMPT.format(
            format_instructions=format_instructions,
            feedback_prompt=feedback_prompt
        )

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", "Research Topic: {query}")]
        )

        chain = prompt | self.llm

        try:
            response = chain.invoke(
                {"query": query, "format_instructions": format_instructions}
            )

            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            plan = parser.parse(content)
            return {"plan": plan.model_dump()}

        except Exception as e:
            logger.error(f"Planner Node parsing failed: {e}")
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
