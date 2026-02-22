"""
Railway-optimized FastAPI app entry point for TORQ Console backend.

This provides the core API endpoints for the Vercel->Railway proxy architecture:
- /api/chat - Agent chat with mandatory learning hook
- /api/telemetry/* - Telemetry ingestion
- /api/learning/* - Learning policy management
- /api/debug/deploy - Deploy identity (torq-deploy-v1 contract)
- /health - Railway health check

Railway startup: uvicorn torq_console.ui.railway_app:app --host 0.0.0.0 --port 8080
"""
import os
import sys
import uuid
import logging
from datetime import datetime, timezone

# ============================================================================
# Logging - INFO to stdout, WARNING+ to stderr
# Prevents Railway from misclassifying INFO logs as errors
# ============================================================================
class _StdoutFilter(logging.Filter):
        def filter(self, record):
                    return record.levelno <= logging.INFO

    class _StderrFilter(logging.Filter):
            def filter(self, record):
                        return record.levelno >= logging.WARNING

        _stdout_handler = logging.StreamHandler(sys.stdout)
_stdout_handler.setLevel(logging.INFO)
_stdout_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
_stdout_handler.addFilter(_StdoutFilter())

_stderr_handler = logging.StreamHandler(sys.stderr)
_stderr_handler.setLevel(logging.WARNING)
_stderr_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
_stderr_handler.addFilter(_StderrFilter())

logging.basicConfig(
        level=logging.INFO,
        handlers=[_stdout_handler, _stderr_handler],
        force=True
)
logger = logging.getLogger(__name__)

# Set production environment variables
os.environ['TORQ_CONSOLE_PRODUCTION'] = 'true'
os.environ['TORQ_DISABLE_LOCAL_LLM'] = 'true'
os.environ['TORQ_DISABLE_GPU'] = 'true'


def create_railway_app():
        """
            Create FastAPI app for Railway deployment with agent + learning hook.
                This is a minimal, focused backend for the Vercel->Railway proxy architecture.
                    Vercel serves the UI; Railway runs the full agent with learning.
                        """
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        from typing import Optional, Dict, Any, List
        import traceback

    from torq_console.build_info import (
        get_app_version_with_source,
        get_git_sha,
        get_build_time,
        get_build_branch,
        get_container_start_time,
        get_platform,
        get_service_name,
        get_schema_updated,
        now_ts,
)

    logger.info("=" * 60)
    logger.info("TORQ Console - Railway Backend")
    logger.info("=" * 60)

    app = FastAPI(
                title="TORQ Console Railway Backend",
                description="Agent backend with mandatory learning hook",
                version="1.0.0"
    )

    # CORS for Vercel proxy
    app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
    )

    # Security middleware
    try:
                from torq_console.api.middleware import ProxySecretMiddleware, AdminTokenMiddleware
                app.add_middleware(ProxySecretMiddleware)
                app.add_middleware(AdminTokenMiddleware)
                logger.info("Security middleware installed")
except ImportError as e:
            logger.warning(f"Security middleware not available: {e}")

    # ============================================================================
        # Request/Response Models
        # ============================================================================
        class ChatRequest(BaseModel):
                    message: str
                    session_id: str
                    agent_id: Optional[str] = None
                    trace_id: Optional[str] = None
                    context: Optional[Dict[str, Any]] = None

    class TelemetryIngest(BaseModel):
                trace: Dict[str, Any]
                spans: List[Dict[str, Any]]

    class LearningPolicyUpdate(BaseModel):
                policy_id: str
                routing_data: Dict[str, Any]

    # ============================================================================
    # Health Check
    # ============================================================================
    @app.get("/health")
    async def health_check():
                """Railway health check endpoint."""
                return {
                    "status": "healthy",
                    "service": "torq-console-railway",
                    "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
                    "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
                    "learning_hook": "mandatory"
                }

    # ============================================================================
    # Chat Endpoint (with mandatory learning hook)
    # ============================================================================
    @app.post("/api/chat")
    async def chat(request: ChatRequest):
                """
                        Agent chat endpoint with mandatory learning hook.
                                Every response triggers learning event calculation and persistence.
                                        """
                try:
                                from torq_console.agents.torq_prince_flowers.core.agent import PrinceFlowersAgent
                                from torq_console.agents.torq_prince_flowers.core.learning_hook import (
                                    record_learning_event,
                                    calculate_consulting_reward,
                    )
                                from torq_console.core.session import SessionManager
                                import time

                    start_time = time.time()
            trace_id = request.trace_id or f"chat-{int(time.time() * 1000)}"
            logger.info(f"[{trace_id}] Chat request: {request.message[:100]}...")

            session_mgr = SessionManager()
            session = session_mgr.get_or_create_session(request.session_id)

            agent = PrinceFlowersAgent(
                                session_id=request.session_id,
                                trace_id=trace_id,
            )

            response_data = await agent.arun(request.message)
            duration = time.time() - start_time

            # === MANDATORY LEARNING HOOK ===
            try:
                                reward = calculate_consulting_reward(
                                                        evidence_level=response_data.get("evidence_level", "medium"),
                                                        routing_success=response_data.get("routing_success", True),
                                                        policy_compliance=response_data.get("policy_compliance", 1.0),
                                                        user_satisfaction_prediction=response_data.get("satisfaction", 0.8),
                                                        response_time=duration,
                                )
                                await record_learning_event(
                                    trace_id=trace_id,
                                    session_id=request.session_id,
                                    agent_name="prince_flowers",
                                    user_query=request.message,
                                    agent_response=response_data.get("response", ""),
                                    reward=reward,
                                    metadata={
                                        "routing_agent": response_data.get("routing_agent"),
                                        "duration_ms": int(duration * 1000),
                                        "evidence_level": response_data.get("evidence_level"),
                                    }
                                )
                                logger.info(f"[{trace_id}] Learning event recorded: reward={reward:.3f}")
except Exception as e:
                logger.error(f"[{trace_id}] Learning hook failed: {e}")

            return {
                                "response": response_data.get("response", ""),
                                "session_id": request.session_id,
                                "trace_id": trace_id,
                                "agent": "prince_flowers",
                                "learning_recorded": True,
                                "duration_ms": int(duration * 1000),
            }

except Exception as e:
            logger.error(f"Chat error: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

    # ============================================================================
    # Telemetry Endpoints
    # ============================================================================
    @app.post("/api/telemetry")
    async def ingest_telemetry(request: TelemetryIngest):
                """Ingest telemetry data from Vercel/frontend."""
        try:
                        from torq_console.telemetry.storage import supabase_ingest
                        result = await supabase_ingest(
                            trace=request.trace,
                            spans=request.spans,
                        )
                        return {
                            "ok": True,
                            "trace_id": request.trace.get("trace_id"),
                            "spans_ingested": len(request.spans),
                            "storage": "supabase"
                        }
except Exception as e:
            logger.error(f"Telemetry ingest error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/telemetry/health")
    async def telemetry_health():
                """Check telemetry system health."""
        from torq_console.telemetry.storage import get_telemetry_health
        health = await get_telemetry_health()
        return health

    # ============================================================================
    # Learning Endpoints
    # ============================================================================
    @app.get("/api/learning/status")
    async def learning_status():
                """Get learning system status."""
        try:
                        from torq_console.telemetry.learning import get_learning_status
                        status = await get_learning_status()
                        return status
except Exception as e:
            return {
                                "configured": False,
                                "error": str(e),
                                "backend": "supabase"
            }

    @app.post("/api/learning/policy/approve")
    async def approve_policy(request: LearningPolicyUpdate):
                """Approve a new learning policy (admin only)."""
        try:
                        from torq_console.telemetry.learning import approve_policy_version
                        result = await approve_policy_version(
                            policy_id=request.policy_id,
                            routing_data=request.routing_data,
                        )
                        return {"ok": True, "policy_id": request.policy_id, **result}
except Exception as e:
            logger.error(f"Policy approval error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/learning/policy/rollback")
    async def rollback_policy():
                """Rollback to previous policy (admin only)."""
        try:
                        from torq_console.telemetry.learning import rollback_policy_version
                        result = await rollback_policy_version()
                        return {"ok": True, **result}
except Exception as e:
            logger.error(f"Policy rollback error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ============================================================================
    # Deploy Identity - torq-deploy-v1 contract
    # See docs/ops/deploy-identity.md for full spec.
    # Rules:
    #   - All fields always present; never null or absent
    #   - "unknown" and "serverless" are valid explicit values
    #   - All timestamps use ISO 8601 UTC with Z suffix
    #   - _schema_version must increment on any breaking field change
    #   - request_id must be unique per call (never cached)
    #   - version must always equal app_version
    # ============================================================================
    @app.get("/api/debug/deploy")
    async def debug_deploy():
                """Authoritative deployment identity. Conforms to torq-deploy-v1 contract."""
        app_version, version_source = get_app_version_with_source()
        platform = get_platform()

        return {
                        "_schema": "torq-deploy-v1",
                        "_schema_version": 1,
                        "_schema_updated": get_schema_updated(),
                        "request_id": str(uuid.uuid4()),
                        "platform": platform,
                        "service": get_service_name(),
                        "env": os.getenv("TORQ_ENV", "production"),
                        # version - backward compat alias; must equal app_version
                        "version": app_version,
                        "app_version": app_version,
                        "version_source": version_source,
                        "package_installed": version_source == "package",
                        # build provenance
                        "git_sha": get_git_sha(),
                        "build_branch": get_build_branch(),
                        "build_time": get_build_time(),
                        # timing
                        "container_start_time": "serverless" if platform == "vercel" else get_container_start_time(),
                        "timestamp": now_ts(),
                        # runtime config
                        "env_name": os.getenv("TORQ_ENV", "production"),
                        "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                        "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
                        "supabase_configured": bool(
                                            os.getenv("SUPABASE_URL")
                                            and (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY"))
                        ),
                        "proxy_secret_configured": bool(os.getenv("TORQ_PROXY_SECRET")),
                        "proxy_secret_required": os.getenv("TORQ_PROXY_SECRET_REQUIRED", "true").strip().lower() == "true",
                        # legacy fields kept for backward compat
                        "learning_hook": "mandatory",
                        "backend": "railway",
        }

    logger.info("Railway app created successfully")
    logger.info("Endpoints: /api/chat, /api/telemetry, /api/learning, /api/debug/deploy, /health")

    return app


# Create app at module level for Railway
# Railway runs: uvicorn torq_console.ui.railway_app:app
app = create_railway_app()

# Export for Railway
__all__ = ["app"]
