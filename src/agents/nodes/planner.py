import logging
from langchain_core.prompts import ChatPromptTemplate
from src.agents.state import AgentState
from .schemas import parser

logger = logging.getLogger(__name__)

class PlannerNode:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: AgentState):
        """
        Analyzes the user query and generates a structured research plan.
        """
        logger.info("--- Executing Planner Node ---")
        query = state.get("query", "")
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
