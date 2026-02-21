"""
Vercel serverless function entry point for TORQ Console.

IMPORTANT: This file must be completely self-contained. It must NOT import
from torq_console.core, torq_console.ui, torq_console.llm, or any module
that transitively imports numpy, scikit-learn, sentence-transformers, or
torch. Vercel serverless functions have a 250MB size limit.

This provides a lightweight API that proxies chat requests directly to
Anthropic Claude or OpenAI, with health/status endpoints.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
import asyncio

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
os.environ.setdefault("TORQ_CONSOLE_PRODUCTION", "true")
os.environ.setdefault("TORQ_DISABLE_LOCAL_LLM", "true")
os.environ.setdefault("TORQ_DISABLE_GPU", "true")

logger = logging.getLogger("torq-vercel")

# Railway proxy configuration
RAILWAY_URL = os.environ.get("TORQ_BACKEND_URL", "").rstrip("/")
PROXY_SECRET = os.environ.get("TORQ_PROXY_SHARED_SECRET", "")
PROXY_TIMEOUT = int(os.environ.get("TORQ_PROXY_TIMEOUT_MS", "25000")) / 1000

logger.info(f"Railway proxy configured: {bool(RAILWAY_URL)}")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Incoming chat message."""
    message: str = Field(..., min_length=1, description="User message text")
    context: Optional[dict[str, Any]] = Field(None, description="Optional context")
    mode: Optional[str] = Field("single_agent", description="Orchestration mode")
    model: Optional[str] = Field(None, description="Override model (e.g. claude-sonnet-4-20250514)")


class ChatResponse(BaseModel):
    """Chat reply."""
    response: str
    agent_id: str = "prince_flowers"
    timestamp: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check."""
    status: str
    service: str = "torq-console"
    platform: str = "vercel"
    anthropic_configured: bool
    openai_configured: bool
    timestamp: str


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="TORQ Console API",
    description="TORQ Console — Vercel Serverless Deployment",
    version="0.80.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are Prince Flowers, the TORQ Console AI assistant.
You are an action-oriented AI that helps with software engineering tasks.

For research/search requests: Provide information directly.
For build/implementation requests: Ask 2-3 clarifying questions first.

Be concise, helpful, and accurate."""

import time
BOOT_TIME = time.time()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_key(name: str) -> bool:
    val = os.environ.get(name, "")
    return bool(val and not val.startswith("@") and val != "")


def _proxy_to_railway(
    path: str,
    method: str = "GET",
    body: bytes = None,
    extra_headers: dict = None,
    query_string: str = "",
) -> dict:
    """Forward request to Railway backend using stdlib urllib."""
    if not RAILWAY_URL:
        raise HTTPException(status_code=503, detail="Backend not configured.")

    import urllib.request
    import urllib.error

    url = f"{RAILWAY_URL}{path}"
    if query_string:
        url = f"{url}?{query_string}"

    headers = {"Content-Type": "application/json"}

    if PROXY_SECRET:
        headers["x-torq-proxy-secret"] = PROXY_SECRET

    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=PROXY_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        logger.error(f"Railway {e.code}: {error_body[:500]}")
        raise HTTPException(status_code=e.code, detail=f"Backend error: {error_body[:200]}")
    except urllib.error.URLError as e:
        logger.error(f"Railway unreachable: {e}")
        raise HTTPException(status_code=502, detail=f"Backend unreachable: {str(e)}")
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")


async def _chat_anthropic(message: str, model: str | None = None) -> str:
    """Send a chat message via Anthropic SDK (blocking)."""
    import anthropic

    async with anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"]) as client:
        resp = await client.messages.create(
            model=model or "claude-3-5-sonnet-20240620",
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message}],
        )
        return resp.content[0].text


async def _stream_anthropic(message: str, model: str | None = None):
    """Stream chat via Anthropic SDK (async generator)."""
    import anthropic

    async with anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"]) as client:
        async with client.messages.stream(
            model=model or "claude-3-5-sonnet-20240620",
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message}],
        ) as stream:
            async for text in stream.text_stream:
                yield text


async def _chat_openai(message: str, model: str | None = None) -> str:
    """Send a chat message via OpenAI SDK (blocking)."""
    import openai

    async with openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"]) as client:
        resp = await client.chat.completions.create(
            model=model or "gpt-4o",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
        )
        return resp.choices[0].message.content


async def _stream_openai(message: str, model: str | None = None):
    """Stream chat via OpenAI SDK (async generator)."""
    import openai

    async with openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"]) as client:
        stream = await client.chat.completions.create(
            model=model or "gpt-4o",
            max_tokens=2048,
            stream=True,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


async def token_stream(message: str, model: str | None = None, provider: str = "none"):
    """Generator for SSE token stream."""
    start_time = time.time()

    try:
        stream_gen = None
        if provider == "anthropic":
            stream_gen = _stream_anthropic(message, model)
        elif provider == "openai":
            stream_gen = _stream_openai(message, model)
        
        if stream_gen:
            async for token in stream_gen:
                yield f"data: {json.dumps({'token': token})}\\n\\n"

        latency_ms = (time.time() - start_time) * 1000
        cold_start_ms = (start_time - BOOT_TIME) * 1000 if (time.time() - BOOT_TIME) < 10.0 else 0

        meta = {
            "latency_ms": latency_ms,
            "provider": provider,
            "cold_start_ms": cold_start_ms,
            "timestamp": _now_iso()
        }
        
        yield f"data: {json.dumps({'meta': meta})}\\n\\n"
        yield "data: [DONE]\\n\\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\\n\\n"
        yield "data: [DONE]\\n\\n"

@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page."""
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TORQ Console</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }}
        .container {{
            max-width: 720px;
            text-align: center;
        }}
        h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d2ff, #7b2ff7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        .version {{ color: #888; margin-bottom: 2rem; }}
        .status {{
            display: inline-block;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            background: #1a3a1a;
            color: #4caf50;
            font-weight: 600;
            margin-bottom: 2rem;
        }}
        .card {{
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            text-align: left;
        }}
        .card h3 {{ color: #00d2ff; margin-bottom: 0.5rem; }}
        code {{
            background: rgba(0,0,0,0.3);
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9rem;
        }}
        pre {{
            background: rgba(0,0,0,0.4);
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin-top: 0.5rem;
            font-size: 0.85rem;
            line-height: 1.5;
        }}
        a {{ color: #00d2ff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .links {{ margin-top: 1rem; }}
        .links a {{
            display: inline-block;
            margin: 0 0.5rem;
            padding: 0.5rem 1rem;
            border: 1px solid #00d2ff;
            border-radius: 8px;
            transition: background 0.2s;
        }}
        .links a:hover {{ background: rgba(0,210,255,0.15); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>TORQ Console</h1>
        <p class="version">v0.80.0 &mdash; Vercel Serverless</p>
        <div class="status">Running</div>

        <div class="card">
            <h3>Chat API</h3>
            <p>Send messages to Prince Flowers AI assistant:</p>
            <pre>curl -X POST {os.environ.get('VERCEL_URL', 'https://your-app.vercel.app')}/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{{"message": "Hello, Prince Flowers!"}}'</pre>
        </div>

        <div class="card">
            <h3>Endpoints</h3>
            <p><code>GET /health</code> &mdash; Health check</p>
            <p><code>POST /api/chat</code> &mdash; Chat with AI</p>
            <p><code>GET /api/status</code> &mdash; System status</p>
            <p><code>GET /api/agents</code> &mdash; List agents</p>
            <p><code>GET /docs</code> &mdash; OpenAPI docs</p>
        </div>

        <div class="links">
            <a href="/docs">API Docs</a>
            <a href="/health">Health</a>
            <a href="https://github.com/pilotwaffle/TORQ-CONSOLE">GitHub</a>
        </div>
    </div>
</body>
</html>""")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        anthropic_configured=_has_key("ANTHROPIC_API_KEY"),
        openai_configured=_has_key("OPENAI_API_KEY"),
        timestamp=_now_iso(),
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Chat with Prince Flowers AI assistant.

    PROXY MODE: Forwards to Railway where full agent + learning runs.
    FALLBACK MODE: Direct Anthropic/OpenAI call (no learning).
    """
    # Try Railway proxy first
    if RAILWAY_URL:
        import uuid
        session_id = str(uuid.uuid4())

        payload = json.dumps({
            "message": req.message,
            "session_id": session_id,
        }).encode("utf-8")

        try:
            result = _proxy_to_railway(
                "/api/chat",  # Railway's endpoint
                method="POST",
                body=payload,
            )

            return ChatResponse(
                response=result.get("response", ""),
                agent_id=result.get("agent", "prince_flowers"),
                timestamp=result.get("timestamp", _now_iso()),
                metadata={
                    "backend": "railway",
                    "proxy": "vercel→railway",
                    "learning_recorded": result.get("learning_recorded", False),
                    "trace_id": result.get("trace_id"),
                    "duration_ms": result.get("duration_ms"),
                },
            )
        except HTTPException as e:
            # If Railway fails, log and fall through to direct call
            logger.warning(f"Railway proxy failed: {e.detail}, falling back to direct call")

    # Fallback: direct Anthropic/OpenAI call
    provider = "none"
    try:
        if _has_key("ANTHROPIC_API_KEY"):
            provider = "anthropic"
            text = await _chat_anthropic(req.message, req.model)
        elif _has_key("OPENAI_API_KEY"):
            provider = "openai"
            text = await _chat_openai(req.message, req.model)
        else:
            raise HTTPException(
                status_code=503,
                detail="No API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in Vercel Dashboard > Settings > Environment Variables.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        print("CHAT_API_ERROR:", repr(exc))
        print(traceback.format_exc())
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=f"Chat error ({provider}): {exc}")

    return ChatResponse(
        response=text,
        agent_id="prince_flowers",
        timestamp=_now_iso(),
        metadata={
            "backend": "vercel-direct",
            "provider": provider,
            "mode": req.mode or "single_agent",
            "model": req.model,
            "platform": "vercel",
            "success": True,
            "learning": False,
            "degraded": True,
        },
    )


@app.post("/api/chat/stream", response_class=StreamingResponse)
async def chat_stream(req: ChatRequest):
    """
    Stream chat response (SSE) - Phase 1 Feature.
    Enabled via TORQ_STREAMING_ENABLED env var.
    """
    if os.environ.get("TORQ_STREAMING_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=400, detail="Streaming is currently disabled via feature flag.")

    provider = "none"
    if _has_key("ANTHROPIC_API_KEY"):
        provider = "anthropic"
    elif _has_key("OPENAI_API_KEY"):
        provider = "openai"
    else:
        raise HTTPException(
            status_code=503,
            detail="No API key configured.",
        )

    return StreamingResponse(
        token_stream(req.message, req.model, provider),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Torq-Provider": provider,
        },
    )


@app.get("/api/agents")
async def list_agents():
    """List available agents."""
    return [
        {
            "id": "prince_flowers",
            "name": "Prince Flowers",
            "description": "Enhanced conversational AI assistant with action-oriented behavior",
            "capabilities": [
                "general_chat",
                "code_generation",
                "task_planning",
                "documentation",
                "web_search",
            ],
            "status": "active",
        }
    ]


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details."""
    if agent_id != "prince_flowers":
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return {
        "id": "prince_flowers",
        "name": "Prince Flowers",
        "description": "Enhanced conversational AI assistant with action-oriented behavior",
        "capabilities": [
            "general_chat",
            "code_generation",
            "task_planning",
            "documentation",
            "web_search",
        ],
        "status": "active",
        "provider": "anthropic" if _has_key("ANTHROPIC_API_KEY") else "openai" if _has_key("OPENAI_API_KEY") else "none",
    }


@app.post("/api/agents/{agent_id}/chat", response_model=ChatResponse)
async def agent_chat(agent_id: str, req: ChatRequest):
    """Chat with a specific agent (routes to /api/chat)."""
    if agent_id != "prince_flowers":
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return await chat(req)


@app.get("/api/status")
async def status():
    """System status."""
    return {
        "status": "healthy",
        "service": "torq-console",
        "version": "0.80.0",
        "platform": "vercel",
        "agents_active": 1,
        "anthropic_configured": _has_key("ANTHROPIC_API_KEY"),
        "openai_configured": _has_key("OPENAI_API_KEY"),
        "streaming_enabled": os.environ.get("TORQ_STREAMING_ENABLED", "false").lower() == "true",
        "timestamp": _now_iso(),
    }


@app.get("/api/sessions")
async def list_sessions():
    """List sessions (stateless on Vercel — returns empty)."""
    return []


@app.post("/api/sessions")
async def create_session(request: Request):
    """Create session (stateless stub for API compatibility)."""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    session_id = f"vercel-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    return {
        "session_id": session_id,
        "created_at": _now_iso(),
        "agent_id": body.get("agent_id", "prince_flowers"),
        "message_count": 0,
        "status": "active",
        "note": "Sessions are stateless on Vercel serverless. Use Railway deployment for persistent sessions.",
    }
