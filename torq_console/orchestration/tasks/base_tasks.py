"""
Base Task Result Models for TORQ Console ControlFlow Integration

Type-safe result models using Pydantic for task outputs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchResult(BaseModel):
    """Result from web search task."""
    query: str = Field(description="The search query used")
    results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of search results with title, url, snippet"
    )
    sources_count: int = Field(default=0, description="Number of sources found")
    search_time: float = Field(default=0.0, description="Time taken to search (seconds)")
    method: str = Field(default="unknown", description="Search method/provider used")
    success: bool = Field(default=True, description="Whether search was successful")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "ControlFlow AI orchestration",
                "results": [
                    {
                        "title": "ControlFlow Documentation",
                        "url": "https://controlflow.ai",
                        "snippet": "Task-centric AI agent orchestration..."
                    }
                ],
                "sources_count": 5,
                "search_time": 1.2,
                "method": "duckduckgo",
                "success": True
            }
        }


class AnalysisResult(BaseModel):
    """Result from content analysis task."""
    key_themes: List[str] = Field(
        default_factory=list,
        description="Main themes identified in content"
    )
    insights: List[str] = Field(
        default_factory=list,
        description="Key insights extracted"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for analysis"
    )
    source_quality: str = Field(
        default="unknown",
        description="Assessment of source quality (high/medium/low)"
    )
    summary: str = Field(default="", description="Brief summary of analysis")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "key_themes": ["AI agents", "workflow orchestration", "task management"],
                "insights": [
                    "ControlFlow uses task-centric design",
                    "Built on Prefect for observability"
                ],
                "confidence": 0.85,
                "source_quality": "high",
                "summary": "ControlFlow provides structured AI agent orchestration",
                "metadata": {"analyzed_sources": 3}
            }
        }


class ReportResult(BaseModel):
    """Result from report generation task."""
    title: str = Field(description="Report title")
    content: str = Field(description="Report content in markdown format")
    summary: str = Field(default="", description="Executive summary")
    sections: List[str] = Field(
        default_factory=list,
        description="List of section titles"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of sources cited"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in report accuracy"
    )
    word_count: int = Field(default=0, description="Total word count")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "ControlFlow Integration Analysis",
                "content": "# Introduction\n\nControlFlow is...",
                "summary": "Brief overview of key findings",
                "sections": ["Introduction", "Key Features", "Conclusion"],
                "sources": ["https://controlflow.ai", "https://prefect.io"],
                "confidence": 0.88,
                "word_count": 1500
            }
        }


class CodeAnalysisResult(BaseModel):
    """Result from code analysis task."""
    language: str = Field(description="Programming language")
    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall code quality score"
    )
    issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of issues found"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Improvement suggestions"
    )
    complexity: str = Field(
        default="unknown",
        description="Code complexity assessment (low/medium/high)"
    )
    has_tests: bool = Field(default=False, description="Whether tests are present")
    has_docs: bool = Field(default=False, description="Whether docs are present")

    class Config:
        json_schema_extra = {
            "example": {
                "language": "python",
                "quality_score": 0.78,
                "issues": [
                    {
                        "type": "warning",
                        "line": 42,
                        "message": "Unused variable 'x'"
                    }
                ],
                "suggestions": [
                    "Add type hints",
                    "Include docstrings"
                ],
                "complexity": "medium",
                "has_tests": True,
                "has_docs": False
            }
        }


class SimpleResult(BaseModel):
    """Simple string result wrapper."""
    content: str = Field(description="Result content")
    success: bool = Field(default=True, description="Whether task was successful")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Task completed successfully",
                "success": True,
                "metadata": {"execution_time": 1.5}
            }
        }
