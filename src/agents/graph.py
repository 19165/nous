import logging
from src.agents.workflows.coordinator import create_coordinator_graph

logger = logging.getLogger(__name__)

# Compile the workflow into a runnable app
graph = create_coordinator_graph()

def create_graph():
    """
    Creates and compiles the LangGraph state machine for the research assistant.
    Refactored in V2.2 to return the compiled coordinator graph.
    """
    return graph

async def run_research_workflow(query: str):
    """
    A wrapper function to invoke the research graph.
    """
    logger.info(f"Invoking research workflow for query: {query}")
    app = create_graph()
    
    initial_state = {
        "query": query,
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
        # --- V2.1 Progress Tracking ---
        "progress_stage": "Starting research...",
        "current_iteration": 1,
        "max_iterations": 3,
        "workflow_status": "in_progress",
        # --- V2.2 Adaptive Routing ---
        "query_type": "UNKNOWN"
    }
    
    try:
        # Use ainvoke for asynchronous execution
        result = await app.ainvoke(initial_state)
        return result
    except Exception as e:
        logger.error(f"Error during workflow execution: {e}")
        raise e

async def stream_research_workflow(query: str):
    """
    A generator that yields state updates from the research graph.
    """
    logger.info(f"Streaming research workflow for query: {query}")
    app = create_graph()
    
    initial_state = {
        "query": query,
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
        # --- V2.1 Progress Tracking ---
        "progress_stage": "Starting research...",
        "current_iteration": 1,
        "max_iterations": 3,
        "workflow_status": "in_progress",
        # --- V2.2 Adaptive Routing ---
        "query_type": "UNKNOWN"
    }

    # Stream events from the graph
    async for event in app.astream(initial_state, stream_mode="values"):
        yield event
