import pytest
import sys
import os
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.agents.schemas import ClassifierOutput, ResearchPlan, ReviewerOutput
import src
print(f"\nDEBUG IMPORT SRC PATH: {src.__file__}\n")

class MockLLM:
    def __init__(self):
        self.response_content = ""
        self.structured_return_value = None

    def __call__(self, *args, **kwargs):
        return self.invoke(*args, **kwargs)

    def invoke(self, messages, *args, **kwargs):
        print(f"\nDEBUG CONFTEST LLM: id={id(self)}, custom_invoke={getattr(self, 'custom_invoke', None)}\n", flush=True)
        if getattr(self, "custom_invoke", None) is not None:
            return self.custom_invoke(messages, *args, **kwargs)
            
        msg_str = str(messages).lower()
        
        # Check if PlannerNode is invoking
        if "research planner" in msg_str or "estimated_complexity" in msg_str or "original_query" in msg_str:
            return AIMessage(content='''{
                "original_query": "Test query",
                "steps": [
                    {"task_id": 1, "query": "mocked search query", "rationale": "test", "tool_name": "web_search"}
                ],
                "estimated_complexity": "Low"
            }''')
            
        # Check if ReviewerNode is invoking
        if "skeptical" in msg_str or "gap analysis" in msg_str or "decision criteria" in msg_str:
            if not hasattr(self, "_reviewer_calls"):
                self._reviewer_calls = 0
            self._reviewer_calls += 1
            
            # Toggle decision for testing retry loop (1st: INSUFFICIENT, 2nd: SUFFICIENT)
            decision = "INSUFFICIENT" if self._reviewer_calls == 1 else "SUFFICIENT"
            feedback = "Need more code details" if decision == "INSUFFICIENT" else ""
            
            return AIMessage(content=f'''{{
                "reasoning": "Mock gap analysis",
                "decision": "{decision}",
                "feedback": "{feedback}",
                "ranked_findings": []
            }}''')

        # Fallback for WriterNode or other invocations
        return AIMessage(content=self.response_content or "Mocked default response")

    async def ainvoke(self, messages, *args, **kwargs):
        return self.invoke(messages, *args, **kwargs)

    def with_structured_output(self, schema, *args, **kwargs):
        mock_chain = MagicMock()
        
        if self.structured_return_value is not None:
            val = self.structured_return_value
        else:
            # Defaults based on schema
            if schema == ClassifierOutput:
                val = ClassifierOutput(
                    query_type="NEWS", 
                    rationale="Test news query rationale"
                )
            elif schema == ResearchPlan:
                from src.agents.schemas.structured import ResearchStep
                val = ResearchPlan(
                    original_query="Test query",
                    steps=[
                        ResearchStep(
                            task_id=1, 
                            query="mocked search query", 
                            rationale="test", 
                            tool_name="web_search"
                        )
                    ],
                    estimated_complexity="Low"
                )
            elif schema == ReviewerOutput:
                val = ReviewerOutput(
                    reasoning="All requirements met",
                    decision="SUFFICIENT",
                    feedback="",
                    ranked_findings=[]
                )
            else:
                val = MagicMock()
                
        # Make the mock callable return the value however LangChain invokes it
        mock_chain.invoke.return_value = val
        mock_chain.ainvoke.return_value = val
        mock_chain.return_value = val
        return mock_chain

@pytest.fixture
def mock_llm():
    return MockLLM()

@pytest.fixture
def mock_search_tools():
    web_mock = MagicMock()
    web_mock.name = "web_search"
    web_mock.description = "Search the web"
    web_mock.invoke.return_value = "Mocked web results"
    
    news_mock = MagicMock()
    news_mock.name = "news_search"
    news_mock.description = "Search the news"
    news_mock.invoke.return_value = "Mocked news results"
    
    return web_mock, news_mock
