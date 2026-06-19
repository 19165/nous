import logging
from langchain_core.prompts import ChatPromptTemplate
from src.agents.schemas import AgentState, parser
from src.agents.prompts import load_prompt

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

        # Determine the appropriate planner system prompt based on query_type
        query_type = state.get("query_type", "UNKNOWN")
        logger.info(f"[Planner Node] Loading prompt strategy for query_type: {query_type}")
        if query_type == "NEWS":
            system_prompt_template = load_prompt("planner_news_system.txt")
        elif query_type == "LEARNING":
            system_prompt_template = load_prompt("planner_learning_system.txt")
        elif query_type == "COMPARISON":
            system_prompt_template = load_prompt("planner_comparison_system.txt")
        else:
            system_prompt_template = load_prompt("planner_general_system.txt")

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt_template), ("human", "Research Topic: {query}")]
        )

        chain = prompt | self.llm

        try:
            # Pass all variables to invoke so LangChain handles formatting once
            response = chain.invoke(
                {
                    "query": query,
                    "format_instructions": format_instructions,
                    "feedback_prompt": feedback_prompt,
                }
            )

            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            plan = parser.parse(content)
            return {"plan": plan.model_dump(), "progress_stage": "Planning research"}

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
            return {
                "plan": fallback_plan,
                "progress_stage": "Planning research (using fallback)",
            }
