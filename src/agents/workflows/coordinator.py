import logging
from langgraph.graph import StateGraph, START, END
from src.agents.schemas import AgentState
from src.agents.nodes import ClassifierNode, PlannerNode, ResearcherNode, ReviewerNode, WriterNode
from src.config.llm import get_llm
from src.tools.search import get_web_search_tool, get_news_search_tool

# Import Subgraph Builders
from src.agents.workflows.news import create_news_subgraph
from src.agents.workflows.learning import create_learning_subgraph
from src.agents.workflows.comparison import create_comparison_subgraph
from src.agents.workflows.general import create_general_subgraph

logger = logging.getLogger(__name__)

def route_query(state: AgentState):
    """
    Router function to select the appropriate subgraph workflow based on the classified query_type.
    """
    query_type = state.get("query_type", "UNKNOWN")
    logger.info(f"--- Routing Query (Type: {query_type}) ---")
    
    if query_type == "NEWS":
        return "news_graph"
    elif query_type == "LEARNING":
        return "learning_graph"
    elif query_type == "COMPARISON":
        return "comparison_graph"
    else:
        return "general_graph"

def create_coordinator_graph():
    """
    Builds the main orchestrator graph, instantiating shared nodes, compiling subgraphs,
    and binding them together with conditional routing edges.
    """
    logger.info("Initializing coordinator and shared node instances...")
    
    # 1. Initialize dependencies
    llm = get_llm()
    web_tool = get_web_search_tool()
    news_tool = get_news_search_tool()
    
    # 2. Instantiate shared nodes
    classifier = ClassifierNode(llm)
    planner = PlannerNode(llm)
    researcher = ResearcherNode(web_tool, news_tool)
    reviewer = ReviewerNode(llm)
    writer = WriterNode(llm)
    
    # 3. Compile child subgraphs
    logger.info("Compiling subgraphs...")
    news_graph = create_news_subgraph(planner, researcher, reviewer, writer)
    learning_graph = create_learning_subgraph(planner, researcher, reviewer, writer)
    comparison_graph = create_comparison_subgraph(planner, researcher, reviewer, writer)
    general_graph = create_general_subgraph(planner, researcher, reviewer, writer)
    
    # 4. Construct coordinator graph
    workflow = StateGraph(AgentState)
    
    # Add nodes (Classifier + Subgraphs)
    workflow.add_node("classifier", classifier)
    workflow.add_node("news_graph", news_graph)
    workflow.add_node("learning_graph", learning_graph)
    workflow.add_node("comparison_graph", comparison_graph)
    workflow.add_node("general_graph", general_graph)
    
    # Define routing and sequential edges
    workflow.add_edge(START, "classifier")
    
    workflow.add_conditional_edges(
        "classifier",
        route_query,
        {
            "news_graph": "news_graph",
            "learning_graph": "learning_graph",
            "comparison_graph": "comparison_graph",
            "general_graph": "general_graph"
        }
    )
    
    # Connect subgraphs to END
    workflow.add_edge("news_graph", END)
    workflow.add_edge("learning_graph", END)
    workflow.add_edge("comparison_graph", END)
    workflow.add_edge("general_graph", END)
    
    logger.info("Coordinator graph compiled successfully.")
    return workflow.compile()
