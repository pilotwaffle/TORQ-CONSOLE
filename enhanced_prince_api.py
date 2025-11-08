#!/usr/bin/env python3
"""
Enhanced Prince Flowers - REST API Server

This creates a REST API endpoint for Enhanced Prince that can be:
1. Tested directly with curl
2. Configured as a backend in Maxim.ai workflows
3. Used for comprehensive testing

Usage:
    python enhanced_prince_api.py

Then test with:
    curl -X POST http://localhost:8000/chat \
      -H "Content-Type: application/json" \
      -d '{"query": "search for top AI tools"}'
"""

import os
import sys
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

# Add torq_console to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    print("⚠️  FastAPI not installed. Install with: pip install fastapi uvicorn")
    FASTAPI_AVAILABLE = False
    sys.exit(1)

try:
    from torq_console.agents import create_prince_flowers_agent, get_agent_memory
    PRINCE_AVAILABLE = True
except ImportError:
    print("⚠️  Enhanced Prince not available. Check torq_console installation.")
    PRINCE_AVAILABLE = False
    sys.exit(1)


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str
    user_id: Optional[str] = "test_user"
    session_id: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    action_taken: str  # "IMMEDIATE_ACTION", "ASK_CLARIFICATION", "PROVIDE_OPTIONS"
    interaction_id: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    enhanced_prince_available: bool
    agent_memory_available: bool
    api_key_configured: bool


# Initialize FastAPI app
app = FastAPI(
    title="Enhanced Prince Flowers API",
    description="REST API for Enhanced Prince conversational agent with action-oriented learning",
    version="1.0.0"
)

# Add CORS middleware (for Maxim.ai and web testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance (initialized on startup)
prince_agent = None
agent_memory = None


@app.on_event("startup")
async def startup_event():
    """Initialize Enhanced Prince on startup."""
    global prince_agent, agent_memory

    print("\n" + "="*80)
    print("ENHANCED PRINCE FLOWERS - REST API SERVER")
    print("="*80)

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  WARNING: No API key found")
        print("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable")
        print("   Enhanced Prince will have limited functionality")
    else:
        print("✅ API key configured")

    # Initialize Enhanced Prince
    try:
        prince_agent = create_prince_flowers_agent()
        print("✅ Enhanced Prince initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Enhanced Prince: {e}")
        prince_agent = None

    # Initialize agent memory
    try:
        agent_memory = get_agent_memory()
        print("✅ Agent memory initialized")
    except Exception as e:
        print(f"⚠️  Agent memory not available: {e}")
        agent_memory = None

    print("\n🚀 Server ready!")
    print("   • Endpoint: http://localhost:8000/chat")
    print("   • Docs: http://localhost:8000/docs")
    print("   • Health: http://localhost:8000/health")
    print("\n" + "="*80 + "\n")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Enhanced Prince Flowers API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")

    return HealthResponse(
        status="healthy" if prince_agent else "degraded",
        enhanced_prince_available=prince_agent is not None,
        agent_memory_available=agent_memory is not None,
        api_key_configured=api_key is not None
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with Enhanced Prince Flowers.

    This endpoint demonstrates Enhanced Prince's action-oriented behavior:
    - Type A queries (search, find, research) → IMMEDIATE_ACTION
    - Type B queries (build, create, develop) → ASK_CLARIFICATION

    Examples:
        Type A: "search for top AI tools" → Immediate search
        Type B: "build a todo app" → Ask clarifying questions
    """
    if not prince_agent:
        raise HTTPException(
            status_code=503,
            detail="Enhanced Prince not available. Check server logs."
        )

    try:
        # Get response from Enhanced Prince
        response_text = await prince_agent.chat(
            request.query,
            context=request.context or {}
        )

        # Determine action taken (analyze the response)
        action_taken = _classify_action(request.query, response_text)

        # Get interaction ID from memory if available
        interaction_id = None
        if agent_memory:
            # Memory is automatically updated by prince_agent.chat()
            snapshot = agent_memory.get_memory_snapshot()
            if snapshot.get("total_interactions", 0) > 0:
                interaction_id = f"interaction_{snapshot['total_interactions']}"

        # Debug info
        debug_info = {
            "query_length": len(request.query),
            "response_length": len(response_text),
            "session_id": request.session_id,
            "user_id": request.user_id
        }

        return ChatResponse(
            response=response_text,
            action_taken=action_taken,
            interaction_id=interaction_id,
            debug_info=debug_info
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@app.post("/feedback")
async def submit_feedback(
    interaction_id: str,
    score: float,
    comment: Optional[str] = None
):
    """
    Submit feedback for an interaction.

    This helps Enhanced Prince learn from user feedback.
    """
    if not agent_memory:
        raise HTTPException(
            status_code=503,
            detail="Agent memory not available"
        )

    try:
        # Extract numeric ID from interaction_id
        if "_" in interaction_id:
            numeric_id = int(interaction_id.split("_")[1])
        else:
            numeric_id = int(interaction_id)

        agent_memory.add_feedback(numeric_id, score, comment)

        return {
            "status": "success",
            "interaction_id": interaction_id,
            "score": score
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting feedback: {str(e)}"
        )


@app.get("/memory/snapshot")
async def get_memory_snapshot():
    """Get current agent memory snapshot."""
    if not agent_memory:
        raise HTTPException(
            status_code=503,
            detail="Agent memory not available"
        )

    return agent_memory.get_memory_snapshot()


def _classify_action(query: str, response: str) -> str:
    """
    Classify what action Enhanced Prince took.

    This is a simple heuristic - in a real implementation,
    Enhanced Prince would return this information directly.
    """
    query_lower = query.lower()
    response_lower = response.lower()

    # Check if response contains code (Type B immediate code generation - BAD for Type A)
    code_indicators = [
        "```", "typescript", "javascript", "python",
        "package.json", "npm install", "pip install"
    ]
    has_code = any(ind in response_lower for ind in code_indicators)

    # Check if response contains questions (Type B clarification - GOOD)
    question_count = response.count("?")
    has_questions = question_count >= 2

    # Check if response indicates search (Type A action - GOOD)
    search_indicators = [
        "based on my search", "search results", "i found",
        "according to", "sources:", "web search"
    ]
    used_search = any(ind in response_lower for ind in search_indicators)

    # Classify based on query type and response
    research_keywords = ["search", "find", "research", "look up", "explore", "show", "list", "get"]
    build_keywords = ["build", "create", "develop", "implement", "make", "design"]

    is_research = any(kw in query_lower for kw in research_keywords)
    is_build = any(kw in query_lower for kw in build_keywords)

    if is_research:
        # Type A query
        if used_search and not has_code:
            return "IMMEDIATE_ACTION"  # ✅ Correct behavior
        elif has_code:
            return "IMMEDIATE_ACTION (ERROR: generated code)"  # ❌ Wrong behavior
        else:
            return "IMMEDIATE_ACTION (UNCLEAR: no clear search)"

    elif is_build:
        # Type B query
        if has_questions and not has_code:
            return "ASK_CLARIFICATION"  # ✅ Correct behavior
        elif has_code and not has_questions:
            return "ASK_CLARIFICATION (ERROR: code without questions)"  # ⚠️ Rushed
        else:
            return "ASK_CLARIFICATION (UNCLEAR)"

    else:
        # Ambiguous query
        if has_questions:
            return "PROVIDE_OPTIONS"
        else:
            return "IMMEDIATE_ACTION (assumed)"


def main():
    """Run the API server."""
    # Check for FastAPI
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI not installed")
        print("Install with: pip install fastapi uvicorn")
        return

    # Check for Enhanced Prince
    if not PRINCE_AVAILABLE:
        print("❌ Enhanced Prince not available")
        print("Check torq_console installation")
        return

    # Run server
    print("\n🚀 Starting Enhanced Prince API server...")
    print("   Press Ctrl+C to stop\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
