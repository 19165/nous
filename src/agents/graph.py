import logging
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from src.agents.state import AgentState
from src.agents.nodes import PlannerNode, ResearcherNode, ReviewerNode, WriterNode
from src.tools.search import get_web_search_tool, get_news_search_tool

logger = logging.getLogger(__name__)

def route_after_reviewer(state: AgentState):
    """
    Routes the workflow based on the Reviewer's decision and retry count.
    """
    decision = state.get("decision", "SUFFICIENT")
    retry_count = state.get("retry_count", 0)
    # Configure retry limit
    MAX_RETRIES = 3 
    
    if decision == "INSUFFICIENT" and retry_count < MAX_RETRIES:
        logger.info(f"Decision is INSUFFICIENT. Retrying... (Attempt {retry_count} of {MAX_RETRIES})")
        return "planner"
    
    if retry_count >= MAX_RETRIES:
        logger.warning(f"Max retries ({MAX_RETRIES}) reached. Proceeding to writer.")
    else:
        logger.info("Decision is SUFFICIENT. Proceeding to writer.")
        
    return "writer"

def create_graph():
    """
    Creates and compiles the LangGraph state machine for the research assistant.
    Uses class-based nodes for better modularity and dependency injection.
    """
    logger.info("Initializing StateGraph...")
    
    # Initialize Dependencies
    llm = ChatOllama(model="gemma4:31b-cloud")
    web_tool = get_web_search_tool()
    news_tool = get_news_search_tool()
    
    # Instantiate Nodes
    planner = PlannerNode(llm)
    researcher = ResearcherNode(web_tool, news_tool)
    reviewer = ReviewerNode(llm)
    writer = WriterNode(llm)
    
    workflow = StateGraph(AgentState)
    
    # Add nodes to the graph (callable class instances)
    workflow.add_node("planner", planner)
    workflow.add_node("researcher", researcher)
    workflow.add_node("reviewer", reviewer)
    workflow.add_node("writer", writer)
    
    # Define the sequential edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "reviewer")
    
    # Define conditional edges from reviewer
    workflow.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "planner": "planner",
            "writer": "writer"
        }
    )
    
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
        "workflow_status": "in_progress"
    }
    
    try:
        # Use ainvoke for asynchronous execution
        result = await app.ainvoke(initial_state)
        return result
    except Exception as e:
        logger.error(f"Error during workflow execution: {e}")
        raise e

# Export the graph for LangGraph Studio
graph = create_graph()
