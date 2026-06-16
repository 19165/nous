from typing import TypedDict, List, Optional, Any, Dict

class AgentState(TypedDict):
    """
    Represents the shared workflow state for the Discord Research Assistant.
    """
    query: str
    plan: Optional[dict]
    findings: List[str]
    reviewed_findings: List[str]
    summary: Optional[str]
    metadata: dict
    
    # --- V2.0 Fields ---
    retry_count: int
    plan_history: List[dict]           # Will contain HistoricalPlan dicts
    reviewer_feedback: Optional[Dict[str, Any]]
    confidence_scores: Dict[str, int]  # Maps finding content (or ID) to score (0-100)
    ranked_findings: List[dict]        # Will contain RankedFinding dicts

    # --- V2.1 Progress Tracking ---
    progress_stage: str       # Current stage description
    current_iteration: int    # Current research iteration (starts at 1)
    max_iterations: int       # Maximum allowed iterations
    workflow_status: str      # 'in_progress', 'completed', or 'failed'
