import logging
from langgraph.graph import StateGraph, START, END
from src.agents.schemas import AgentState
from src.config.settings import settings

logger = logging.getLogger(__name__)

def create_general_subgraph(planner, researcher, reviewer, writer):
    """
    Factory function to compile and return the GENERAL research subgraph.
    Reuses node instances passed from the parent coordinator.
    Bypasses reviewer to optimize speed for general queries.
    """
    logger.info("Building GENERAL Subgraph...")
    workflow = StateGraph(AgentState)
    
    # Add shared nodes (keeping reviewer in signature for coordinator compatibility)
    workflow.add_node("planner", planner)
    workflow.add_node("researcher", researcher)
    workflow.add_node("writer", writer)
    
    # Connect graph edges: Straight path
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", END)
    
    return workflow.compile()
