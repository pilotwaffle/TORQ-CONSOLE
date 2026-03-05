"""
TORQ Console - FastAPI Integration Example

Complete example showing how to integrate OpenTelemetry tracing
with a Railway/FastAPI backend.
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from infrastructure import (
    init_tracing,
    add_tracing_middleware,
    traced,
    traced_db,
    traced_llm,
    get_tracer,
    SpanKind
)

# Initialize tracing
tracer = init_tracing(
    service_name="torq-console-api",
    otlp_endpoint=None,  # Set to your OTLP endpoint
    enable_console=True   # Enable for debugging
)

# Create FastAPI app
app = FastAPI(
    title="TORQ Console API",
    version="1.0.0",
    description="AI Agent Console with OpenTelemetry Tracing"
)

# Add tracing middleware
add_tracing_middleware(app, service_name="torq-console-api")


# Example: Traced database operation
@traced_db(operation="select")
async def get_user_from_db(user_id: str, trace_context=None):
    """Simulated database query"""
    # Your actual database query here
    return {
        "id": user_id,
        "name": "Demo User",
        "email": f"{user_id}@torq.ai"
    }


# Example: Traced LLM call
@traced_llm(provider="openai", model="gpt-4")
async def call_llm(prompt: str, trace_context=None):
    """Simulated LLM call"""
    # Your actual LLM API call here
    return f"LLM response to: {prompt}"


# Example endpoint: Agent reasoning
@app.post("/api/agent/reason")
@traced(name="agent.reason.endpoint", kind=SpanKind.AGENT_REASON)
async def agent_reason(request: Request, payload: dict):
    """
    Agent reasoning endpoint with automatic tracing.
    """
    # Get trace context from request state (injected by middleware)
    trace_context = getattr(request.state, "trace_context", None)

    # Perform reasoning (LLM call)
    response = await call_llm(
        prompt=payload.get("prompt", ""),
        trace_context=trace_context
    )

    return {
        "trace_id": trace_context.trace_id if trace_context else None,
        "response": response
    }


# Example endpoint: Knowledge retrieval
@app.get("/api/agent/retrieve/{query}")
@traced(name="agent.retrieve.endpoint", kind=SpanKind.AGENT_RETRIEVE)
async def agent_retrieve(query: str, request: Request):
    """
    Knowledge retrieval endpoint with automatic tracing.
    """
    trace_context = getattr(request.state, "trace_context", None)

    # Simulated retrieval
    results = [
        {"id": "1", "text": "Sample result 1"},
        {"id": "2", "text": "Sample result 2"}
    ]

    return {
        "trace_id": trace_context.trace_id if trace_context else None,
        "query": query,
        "results": results
    }


# Example endpoint: Database query
@app.get("/api/users/{user_id}")
@traced(name="user.get", kind=SpanKind.API_REQUEST)
async def get_user(user_id: str, request: Request):
    """
    User lookup with automatic database tracing.
    """
    trace_context = getattr(request.state, "trace_context", None)

    # Traced database operation
    user = await get_user_from_db(user_id, trace_context=trace_context)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "trace_id": trace_context.trace_id if trace_context else None,
        "user": user
    }


# Health check
@app.get("/health")
async def health_check():
    """Health endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "torq-console-api",
        "tracing": "enabled"
    }


if __name__ == "__main__":
    uvicorn.run(
        "tracing_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
