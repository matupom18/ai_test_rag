from pydantic import BaseModel, Field
from typing import List, Dict


class QAAnswer(BaseModel):
    query: str
    answer: str
    sources: List[str] = Field(default_factory=list)
    confidence: float


class IssueSummary(BaseModel):
    raw_text: str
    reported_issues: List[str]
    affected_components: List[str]
    severity: str
    suggestions: List[str] = Field(default_factory=list)


class RouterDecision(BaseModel):
    tool: str
    rationale: str
    tool_input: Dict
