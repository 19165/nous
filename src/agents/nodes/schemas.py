from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

class ResearchStep(BaseModel):
    """Information for the researcher in each step."""
    task_id: int = Field(description="Unique ID for the task")
    query: str = Field(description="Search query to use")
    rationale: str = Field(description="Reason for this search")
    tool_name: str = Field(description="Tool to use: 'web_search' or 'news_search'")

class ResearchPlan(BaseModel):
    """The main output from the Planner Node."""
    original_query: str = Field(description="The user's original query")
    steps: List[ResearchStep] = Field(description="List of search steps")
    estimated_complexity: str = Field(description="Complexity (High, Medium, Low)")

class HistoricalPlan(BaseModel):
    """Records a previous plan and the feedback that caused it to be revised."""
    iteration: int = Field(description="The retry iteration number")
    plan: ResearchPlan = Field(description="The plan that was executed")
    feedback_received: str = Field(description="The feedback received from the reviewer")

class RankedFinding(BaseModel):
    """A finding that has been ranked and scored by the Reviewer."""
    content: str = Field(description="The extracted information or finding")
    source_url: str = Field(description="The URL where this finding was sourced")
    source_type: Literal["Official", "News", "Academic", "Blog", "Opinion", "Unknown"] = Field(
        description="The categorization of the source quality"
    )
    confidence_score: int = Field(description="Confidence score for this specific finding (0-100)")

class ReviewerOutput(BaseModel):
    """The main output from the Reviewer Node."""
    reasoning: str = Field(
        description="Step-by-step Gap Analysis. Compare 'User Needs' vs 'Collected Findings' to identify what is missing."
    )
    decision: Literal["SUFFICIENT", "INSUFFICIENT"] = Field(
        description="Whether the research objective has been sufficiently addressed."
    )
    feedback: str = Field(
        description="Explanation of why findings are insufficient, identifying missing info categories. Leave empty if SUFFICIENT."
    )
    ranked_findings: List[RankedFinding] = Field(
        description="List of findings ordered by source quality (Official > News > Academic > Blog > Opinion)."
    )

# Initialize Parser
parser = PydanticOutputParser(pydantic_object=ResearchPlan)
reviewer_parser = PydanticOutputParser(pydantic_object=ReviewerOutput)
