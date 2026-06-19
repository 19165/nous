import pytest
import sys
import os
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.agents.schemas import ClassifierOutput, ResearchPlan, ReviewerOutput

class MockLLM:
    def __init__(self):
        self.response_content = ""
        self.structured_return_value = None

    def __call__(self, *args, **kwargs):
        return self.invoke(*args, **kwargs)

    def invoke(self, messages, *args, **kwargs):
        return AIMessage(content=self.response_content)

    async def ainvoke(self, messages, *args, **kwargs):
        return AIMessage(content=self.response_content)

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
