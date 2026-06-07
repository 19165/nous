from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    """
    Represents the shared workflow state for the Discord Research Assistant.
    """
    query: str
    plan: Optional[str]
    findings: List[str]
    reviewed_findings: List[str]
    summary: Optional[str]
    metadata: dict
