from typing import List
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

# Initialize Parser
parser = PydanticOutputParser(pydantic_object=ResearchPlan)
