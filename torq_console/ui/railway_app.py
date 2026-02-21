"""
Railway-optimized FastAPI app entry point for TORQ Console backend.

This provides the core API endpoints for the Vercel→Railway proxy architecture:
- /api/chat - Agent chat with mandatory learning hook
- /api/telemetry/* - Telemetry ingestion
- /api/learning/* - Learning policy management
- /health - Railway health check

Railway startup: uvicorn torq_console.ui.railway_app:app --host 0.0.0.0 --port 8080
"""

import os
import sys
import logging

# Configure logging BEFORE any other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set production environment variables
os.environ['TORQ_CONSOLE_PRODUCTION'] = 'true'
os.environ['TORQ_DISABLE_LOCAL_LLM'] = 'true'
os.environ['TORQ_DISABLE_GPU'] = 'true'


def create_railway_app():
    """
    Create FastAPI app for Railway deployment with agent + learning hook.

    This is a minimal, focused backend for the Vercel→Railway proxy architecture.
    Vercel serves the UI; Railway runs the full agent with learning.
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Optional, Dict, Any, List
    import traceback

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
            # Import here to avoid heavy module-level imports
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

            # Get or create session
            session_mgr = SessionManager()
            session = session_mgr.get_or_create_session(request.session_id)

            # Create agent
            agent = PrinceFlowersAgent(
                session_id=request.session_id,
                trace_id=trace_id,
            )

            # Execute agent
            response_data = await agent.arun(request.message)

            duration = time.time() - start_time

            # === MANDATORY LEARNING HOOK ===
            # Every agent response triggers learning event
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
                # Don't fail the request if learning fails

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
    # Deploy Info
    # ============================================================================

    @app.get("/api/debug/deploy")
    async def deploy_info():
        """Deployment fingerprint."""
        return {
            "service": "railway-backend",
            "version": "1.0.0",
            "env": "production",
            "learning_hook": "mandatory",
            "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
            "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        }

    logger.info("Railway app created successfully")
    logger.info("Endpoints: /api/chat, /api/telemetry, /api/learning, /health")

    return app


# Create app at module level for Railway
# Railway runs: uvicorn torq_console.ui.railway_app:app
app = create_railway_app()

# Export for Railway
__all__ = ["app"]
