import pytest
from unittest.mock import MagicMock
from src.agents.nodes.classifier import ClassifierNode
from src.agents.schemas import ClassifierOutput

def test_classifier_node_success(mock_llm):
    # Set the structured return value to LEARNING
    mock_llm.structured_return_value = ClassifierOutput(
        query_type="LEARNING",
        rationale="Concept explanation request"
    )
    
    node = ClassifierNode(mock_llm)
    state = {"query": "What is LangGraph?"}
    
    result = node(state)
    
    assert result["query_type"] == "LEARNING"
    assert "Classified query as LEARNING" in result["progress_stage"]

def test_classifier_node_fallback(mock_llm):
    # Make with_structured_output raise an exception to trigger fallback
    mock_llm.with_structured_output = MagicMock(side_effect=Exception("API Error"))
    
    # Also make the raw invoke raise an exception to trigger absolute fallback
    mock_llm.invoke = MagicMock(side_effect=Exception("Absolute Failure"))
    
    node = ClassifierNode(mock_llm)
    state = {"query": "Some random query"}
    
    result = node(state)
    
    # Should default to UNKNOWN
    assert result["query_type"] == "UNKNOWN"
    assert "UNKNOWN" in result["progress_stage"]
