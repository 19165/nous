import logging
from langgraph.graph import StateGraph, START, END
from src.agents.state import AgentState
from src.agents.nodes import planner_node, researcher_node, reviewer_node, writer_node

logger = logging.getLogger(__name__)

def create_graph():
    """
    Creates and compiles the LangGraph state machine for the research assistant.
    """
    logger.info("Initializing StateGraph...")
    workflow = StateGraph(AgentState)
    
    # Add nodes to the graph
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("writer", writer_node)
    
    # Define the sequential edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "reviewer")
    workflow.add_edge("reviewer", "writer")
    workflow.add_edge("writer", END)
    
    # Compile the workflow into a runnable app
    return workflow.compile()

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
        "metadata": {}
    }
    
    try:
        # Use ainvoke for asynchronous execution
        result = await app.ainvoke(initial_state)
        return result
    except Exception as e:
        logger.error(f"Error during workflow execution: {e}")
        raise e
