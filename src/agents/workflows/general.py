import logging
from langgraph.graph import StateGraph, START, END
from src.agents.schemas import AgentState
from src.config.settings import settings

logger = logging.getLogger(__name__)

def route_after_reviewer(state: AgentState):
    """
    Conditional routing for the GENERAL subgraph based on the Reviewer's decision and retry count.
    """
    decision = state.get("decision", "SUFFICIENT")
    retry_count = state.get("retry_count", 0)
    MAX_RETRIES = settings.MAX_RETRIES
    
    if decision == "INSUFFICIENT" and retry_count < MAX_RETRIES:
        logger.info(f"[GENERAL Subgraph] Decision is INSUFFICIENT. Retrying... (Attempt {retry_count} of {MAX_RETRIES})")
        return "planner"
    
    if retry_count >= MAX_RETRIES:
        logger.warning(f"[GENERAL Subgraph] Max retries ({MAX_RETRIES}) reached. Proceeding to writer.")
    else:
        logger.info("[GENERAL Subgraph] Decision is SUFFICIENT. Proceeding to writer.")
        
    return "writer"

def create_general_subgraph(planner, researcher, reviewer, writer):
    """
    Factory function to compile and return the GENERAL research subgraph.
    Reuses node instances passed from the parent coordinator.
    """
    logger.info("Building GENERAL Subgraph...")
    workflow = StateGraph(AgentState)
    
    # Add shared nodes
    workflow.add_node("planner", planner)
    workflow.add_node("researcher", researcher)
    workflow.add_node("reviewer", reviewer)
    workflow.add_node("writer", writer)
    
    # Connect graph edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "reviewer")
    
    workflow.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "planner": "planner",
            "writer": "writer"
        }
    )
    workflow.add_edge("writer", END)
    
    return workflow.compile()
