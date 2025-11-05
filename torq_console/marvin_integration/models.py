"""
Pydantic Models for TORQ Console Marvin Integration

Type-safe models for structured outputs from Marvin operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class AnalysisConfidence(str, Enum):
    """Confidence level for analysis results."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Severity(str, Enum):
    """Severity levels for issues and risks."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Priority(str, Enum):
    """Priority levels for tasks and issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TorqSpecAnalysis(BaseModel):
    """
    Structured analysis of a software specification.

    Used for Spec-Kit integration to provide AI-powered
    specification quality assessment.
    """
    clarity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Clarity score (0.0 = unclear, 1.0 = very clear)"
    )
    completeness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Completeness score (0.0 = incomplete, 1.0 = complete)"
    )
    feasibility_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Feasibility score (0.0 = not feasible, 1.0 = highly feasible)"
    )
    confidence: AnalysisConfidence = Field(
        description="Confidence level in this analysis"
    )
    missing_requirements: List[str] = Field(
        default_factory=list,
        description="List of missing or unclear requirements"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improvement"
    )
    technical_risks: List[str] = Field(
        default_factory=list,
        description="Identified technical risks"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Specification strengths"
    )
    summary: str = Field(
        description="Brief summary of the analysis"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "clarity_score": 0.85,
                "completeness_score": 0.70,
                "feasibility_score": 0.90,
                "confidence": "high",
                "missing_requirements": [
                    "Error handling strategy not defined",
                    "Performance benchmarks missing"
                ],
                "recommendations": [
                    "Add specific error handling requirements",
                    "Define performance SLAs"
                ],
                "technical_risks": [
                    "Database scalability not addressed"
                ],
                "strengths": [
                    "Clear authentication requirements",
                    "Well-defined API structure"
                ],
                "summary": "Good foundation but needs more detail on error handling and performance"
            }
        }


class CodeIssue(BaseModel):
    """A single code issue identified during review."""
    severity: Severity = Field(description="Issue severity level")
    line_number: Optional[int] = Field(
        None,
        description="Line number where issue occurs (if applicable)"
    )
    description: str = Field(description="Description of the issue")
    suggestion: str = Field(description="Suggested fix or improvement")
    category: str = Field(
        description="Issue category (e.g., 'security', 'performance', 'style')"
    )


class TorqCodeReview(BaseModel):
    """
    Structured code review results.

    Provides type-safe code review output with categorized issues
    and quality metrics.
    """
    quality_score: float = Field(
        ge=0.0,
        le=10.0,
        description="Overall quality score (0-10)"
    )
    issues: List[CodeIssue] = Field(
        default_factory=list,
        description="List of identified issues"
    )
    summary: str = Field(description="Summary of the review")
    positive_aspects: List[str] = Field(
        default_factory=list,
        description="Positive aspects of the code"
    )
    security_concerns: List[str] = Field(
        default_factory=list,
        description="Security-related concerns"
    )
    performance_notes: List[str] = Field(
        default_factory=list,
        description="Performance-related observations"
    )
    maintainability_score: float = Field(
        ge=0.0,
        le=10.0,
        description="Maintainability score (0-10)"
    )
    test_coverage_assessment: str = Field(
        description="Assessment of test coverage"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "quality_score": 7.5,
                "issues": [
                    {
                        "severity": "warning",
                        "line_number": 42,
                        "description": "Potential division by zero",
                        "suggestion": "Add zero check before division",
                        "category": "safety"
                    }
                ],
                "summary": "Good code structure with minor safety improvements needed",
                "positive_aspects": ["Clear variable names", "Good error handling"],
                "security_concerns": ["Input validation could be stronger"],
                "performance_notes": ["Consider caching frequently accessed data"],
                "maintainability_score": 8.0,
                "test_coverage_assessment": "Adequate unit tests, missing integration tests"
            }
        }


class ResearchSource(BaseModel):
    """A single research source."""
    url: str = Field(description="Source URL")
    title: str = Field(description="Source title")
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Relevance to query (0.0 = not relevant, 1.0 = highly relevant)"
    )
    summary: str = Field(description="Brief summary of the source")


class TorqResearchFindings(BaseModel):
    """
    Structured research results.

    Type-safe research findings with sources and confidence metrics.
    """
    query: str = Field(description="Original research query")
    key_findings: List[str] = Field(
        description="Main findings from the research"
    )
    sources: List[ResearchSource] = Field(
        default_factory=list,
        description="Research sources"
    )
    confidence: AnalysisConfidence = Field(
        description="Confidence in research findings"
    )
    summary: str = Field(description="Executive summary of findings")
    related_topics: List[str] = Field(
        default_factory=list,
        description="Related topics worth exploring"
    )
    methodology: str = Field(
        description="How the research was conducted"
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Limitations of the research"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Best practices for API authentication",
                "key_findings": [
                    "JWT tokens are industry standard",
                    "OAuth 2.0 preferred for third-party access"
                ],
                "sources": [
                    {
                        "url": "https://example.com/api-auth",
                        "title": "API Authentication Guide",
                        "relevance_score": 0.95,
                        "summary": "Comprehensive guide to API authentication methods"
                    }
                ],
                "confidence": "high",
                "summary": "Modern API authentication relies heavily on JWT and OAuth 2.0",
                "related_topics": ["API security", "Token refresh strategies"],
                "methodology": "Web search and documentation analysis",
                "limitations": ["Limited to publicly available information"]
            }
        }


class Task(BaseModel):
    """A single task in a breakdown."""
    title: str = Field(description="Task title")
    description: str = Field(description="Detailed task description")
    priority: Priority = Field(description="Task priority")
    estimated_hours: float = Field(
        gt=0.0,
        description="Estimated hours to complete"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Task dependencies (titles of other tasks)"
    )
    skills_required: List[str] = Field(
        default_factory=list,
        description="Skills required to complete this task"
    )
    risks: List[str] = Field(
        default_factory=list,
        description="Identified risks for this task"
    )


class Milestone(BaseModel):
    """A project milestone."""
    title: str = Field(description="Milestone title")
    description: str = Field(description="Milestone description")
    target_date: str = Field(description="Target completion date (ISO format or relative)")
    tasks: List[str] = Field(
        description="Task titles included in this milestone"
    )


class TorqTaskBreakdown(BaseModel):
    """
    Structured task breakdown and planning.

    AI-generated project plan with tasks, milestones, and estimates.
    """
    project_title: str = Field(description="Project title")
    total_estimated_hours: float = Field(
        gt=0.0,
        description="Total estimated hours for all tasks"
    )
    tasks: List[Task] = Field(description="List of tasks")
    milestones: List[Milestone] = Field(
        default_factory=list,
        description="Project milestones"
    )
    critical_path: List[str] = Field(
        default_factory=list,
        description="Critical path task titles"
    )
    resource_requirements: Dict[str, int] = Field(
        default_factory=dict,
        description="Required resources (e.g., {'backend_dev': 2, 'frontend_dev': 1})"
    )
    risk_summary: str = Field(description="Overall risk assessment")
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Success criteria for the project"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "project_title": "User Authentication System",
                "total_estimated_hours": 120.0,
                "tasks": [
                    {
                        "title": "Design database schema",
                        "description": "Create user tables with proper indexing",
                        "priority": "high",
                        "estimated_hours": 8.0,
                        "dependencies": [],
                        "skills_required": ["Database design", "SQL"],
                        "risks": ["Schema changes may require migration"]
                    }
                ],
                "milestones": [
                    {
                        "title": "MVP Complete",
                        "description": "Basic login/logout functionality working",
                        "target_date": "Week 4",
                        "tasks": ["Design database schema", "Implement authentication"]
                    }
                ],
                "critical_path": ["Design database schema", "Implement authentication"],
                "resource_requirements": {"backend_dev": 2, "qa": 1},
                "risk_summary": "Medium risk - well-understood domain but tight timeline",
                "success_criteria": ["All tests pass", "Security audit complete"]
            }
        }


class IntentClassification(str, Enum):
    """User intent classification for query routing."""
    SPEC_CREATE = "spec_create"
    SPEC_ANALYZE = "spec_analyze"
    CODE_REVIEW = "code_review"
    WEB_SEARCH = "web_search"
    RESEARCH = "research"
    CHAT = "chat"
    TASK_PLANNING = "task_planning"
    QUESTION = "question"


class SentimentClassification(str, Enum):
    """Sentiment classification."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class ComplexityLevel(str, Enum):
    """Complexity level classification."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"
