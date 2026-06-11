import logging
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from src.agents.state import AgentState
from src.agents.nodes import PlannerNode, ResearcherNode, ReviewerNode, WriterNode
from src.tools.search import get_web_search_tool, get_news_search_tool

logger = logging.getLogger(__name__)

def create_graph():
    """
    Creates and compiles the LangGraph state machine for the research assistant.
    Uses class-based nodes for better modularity and dependency injection.
    """
    logger.info("Initializing StateGraph...")
    
    # Initialize Dependencies
    # In a more advanced setup, these could be passed into create_graph()
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
