import pytest
from unittest.mock import patch, MagicMock
from src.agents.workflows.coordinator import create_coordinator_graph
from src.agents.schemas import ClassifierOutput, ReviewerOutput, ResearchPlan, ResearchStep

@pytest.mark.asyncio
async def test_coordinator_workflow_news_route(mock_llm, mock_search_tools):
    web_tool, news_tool = mock_search_tools
    
    # 1. Setup mock returns for LLM
    mock_llm.structured_return_value = ClassifierOutput(
        query_type="NEWS",
        rationale="Wants news updates"
    )
    mock_llm.response_content = "## Topic: AI Models\n### Key Findings\n- AI models are cool\n### TL;DR Summary\n- Summarized AI models"
    
    # Patch get_llm and tools imports inside coordinator module
    with patch("src.agents.workflows.coordinator.get_llm", return_value=mock_llm), \
         patch("src.agents.workflows.coordinator.get_web_search_tool", return_value=web_tool), \
         patch("src.agents.workflows.coordinator.get_news_search_tool", return_value=news_tool):
         
         app = create_coordinator_graph()
         
         initial_state = {
             "query": "What are the latest AI models?",
             "plan": None,
             "findings": [],
             "reviewed_findings": [],
             "summary": None,
             "metadata": {},
             "retry_count": 0,
             "plan_history": [],
             "reviewer_feedback": None,
             "confidence_scores": {},
             "ranked_findings": [],
             "progress_stage": "Starting",
             "current_iteration": 1,
             "max_iterations": 3,
             "workflow_status": "in_progress",
             "query_type": "UNKNOWN"
         }
         
         result = await app.ainvoke(initial_state)
         
         # Assertions
         assert result["query_type"] == "NEWS"
         assert result["workflow_status"] == "completed"
         assert "Summarized AI models" in result["summary"]

@pytest.mark.asyncio
async def test_reviewer_retry_loop(mock_llm, mock_search_tools):
    web_tool, news_tool = mock_search_tools
    
    reviewer_call_count = 0
    
    # 1. Mock classifier using with_structured_output
    mock_llm.structured_return_value = ClassifierOutput(
        query_type="LEARNING", 
        rationale="Learning test"
    )
    
    from langchain_core.messages import AIMessage
    
    def dynamic_invoke(messages, *args, **kwargs):
        nonlocal reviewer_call_count
        msg_str = str(messages).lower()
        print(f"\nDEBUG MSG_STR: {msg_str}\n")
        
        # Check if PlannerNode is calling
        if "expert research planner" in msg_str:
            return AIMessage(content='''{
                "original_query": "Explain LangGraph",
                "steps": [
                    {"task_id": 1, "query": "Explain LangGraph", "rationale": "test", "tool_name": "web_search"}
                ],
                "estimated_complexity": "Medium"
            }''')
            
        # Check if ReviewerNode is calling
        if "skeptical" in msg_str or "gap analysis" in msg_str or "decision criteria" in msg_str:
            reviewer_call_count += 1
            if reviewer_call_count == 1:
                # First attempt: INSUFFICIENT
                return AIMessage(content='''{
                    "reasoning": "Missing info",
                    "decision": "INSUFFICIENT",
                    "feedback": "Need more code details",
                    "ranked_findings": []
                }''')
            else:
                # Second attempt: SUFFICIENT
                return AIMessage(content='''{
                    "reasoning": "Now complete",
                    "decision": "SUFFICIENT",
                    "feedback": "",
                    "ranked_findings": []
                }''')
                
        # Default response
        return AIMessage(content="Final summary report")
        
    print(f"\nDEBUG TEST FIXTURE LLM: id={id(mock_llm)}\n")
    mock_llm.custom_invoke = dynamic_invoke
    
    with patch("src.agents.workflows.coordinator.get_llm", return_value=mock_llm), \
         patch("src.agents.workflows.coordinator.get_web_search_tool", return_value=web_tool), \
         patch("src.agents.workflows.coordinator.get_news_search_tool", return_value=news_tool):
         
         app = create_coordinator_graph()
         
         initial_state = {
             "query": "Explain LangGraph",
             "plan": None,
             "findings": [],
             "reviewed_findings": [],
             "summary": None,
             "metadata": {},
             "retry_count": 0,
             "plan_history": [],
             "reviewer_feedback": None,
             "confidence_scores": {},
             "ranked_findings": [],
             "progress_stage": "Starting",
             "current_iteration": 1,
             "max_iterations": 3,
             "workflow_status": "in_progress",
             "query_type": "UNKNOWN"
         }
         
         result = await app.ainvoke(initial_state)
         
         # Assertions
         # Check that reviewer was called twice (initial attempt + 1 retry)
         assert reviewer_call_count == 2
         assert result["query_type"] == "LEARNING"
         assert result["workflow_status"] == "completed"
