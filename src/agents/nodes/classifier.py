import logging
from langchain_core.prompts import ChatPromptTemplate
from src.agents.schemas import AgentState, ClassifierOutput, classifier_parser
from src.agents.prompts import load_prompt

logger = logging.getLogger(__name__)


class ClassifierNode:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: AgentState) -> dict:
        """
        Classifies the user query's research intent (NEWS, LEARNING, COMPARISON, UNKNOWN).
        """
        logger.info("--- Executing Classifier Node ---")
        query = state.get("query", "")

        system_prompt = load_prompt("classifier_system.txt")

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", "User Query: {query}")]
        )

        # Try structured output first
        try:
            structured_llm = self.llm.with_structured_output(ClassifierOutput)
            chain = prompt | structured_llm
            result = chain.invoke({"query": query})

            # Extract values depending on whether result is a dict or object
            if isinstance(result, dict):
                query_type = result.get("query_type", "UNKNOWN")
                rationale = result.get("rationale", "")
            else:
                query_type = result.query_type
                rationale = result.rationale

            logger.info(
                f"Classification result (Structured): {query_type} - {rationale}"
            )

            return {
                "query_type": query_type,
                "progress_stage": f"Classified query as {query_type}",
            }
        except Exception as e:
            logger.warning(
                f"with_structured_output failed, falling back to manual parsing: {e}"
            )

            # Fallback to standard prompt and manual parser
            try:
                format_instructions = classifier_parser.get_format_instructions()
                prompt_fallback = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            system_prompt + "\n\n{format_instructions}",
                        ),
                        ("human", "User Query: {query}"),
                    ]
                )
                chain = prompt_fallback | self.llm
                response = chain.invoke(
                    {"query": query, "format_instructions": format_instructions}
                )

                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                parsed = classifier_parser.parse(content)
                logger.info(
                    f"Classification result (Fallback Parser): {parsed.query_type} - {parsed.rationale}"
                )
                return {
                    "query_type": parsed.query_type,
                    "progress_stage": f"Classified query as {parsed.query_type}",
                }
            except Exception as ex:
                logger.error(
                    f"Classifier Node failed completely: {ex}. Defaulting query_type to UNKNOWN."
                )
                return {
                    "query_type": "UNKNOWN",
                    "progress_stage": "Classified query as UNKNOWN (fallback)",
                }
