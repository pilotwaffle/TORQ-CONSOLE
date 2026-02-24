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
from contextlib import asynccontextmanager

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

    # Lifespan handler for graceful startup/shutdown (fixes Railway deployment hangs)
    @asynccontextmanager
    async def lifespan(app_instance):
        # Startup - validate agent contract
        logger.info("TORQ Console Railway Backend starting...")

        # ============================================================
        # STARTUP CONTRACT VALIDATION
        # Fail fast if agent is misconfigured - prevents silent broken UI
        # ============================================================
        try:
            from torq_console.agents.torq_prince_flowers.core.agent import TORQPrinceFlowers
            from torq_console.agents.protocols import validate_agent_contract

            # Create agent instance
            test_agent = TORQPrinceFlowers()

            # Validate contract
            is_valid, errors = validate_agent_contract(test_agent)
            if not is_valid:
                logger.error("=" * 60)
                logger.error("AGENT CONTRACT VALIDATION FAILED")
                logger.error("The web API will NOT function correctly:")
                for error in errors:
                    logger.error(f"  - {error}")
                logger.error("=" * 60)
                raise RuntimeError(
                    f"Agent contract validation failed: {errors}. "
                    "This prevents the web API from functioning correctly."
                )
            logger.info("✓ Agent contract validation passed")
        except Exception as e:
            logger.error(f"Agent validation failed: {e}")
            # In dev mode, continue; in prod, fail
            if os.environ.get('RAILWAY_STATIC_URL') or os.environ.get('RAILWAY_ENVIRONMENT'):
                raise

        # Configure telemetry as best-effort
        telemetry_strict = os.environ.get('TORQ_TELEMETRY_STRICT', 'false').lower() == 'true'
        telemetry_enabled = os.environ.get('TORQ_TELEMETRY_ENABLED', 'true').lower() == 'true'

        if not telemetry_enabled:
            logger.info("⚠ Telemetry disabled (TORQ_TELEMETRY_ENABLED=false)")
        elif not telemetry_strict:
            logger.info("✓ Telemetry in best-effort mode (errors will be logged but not raise)")
        else:
            logger.info("✓ Telemetry in strict mode (errors will raise)")

        # Store telemetry config in app state
        app_instance.state.telemetry_config = {
            'enabled': telemetry_enabled,
            'strict': telemetry_strict,
            'disabled_due_to_error': False,
            'last_error': None,
        }

        yield

        # Shutdown
        logger.info("TORQ Console Railway Backend shutting down...")

    app = FastAPI(
        title="TORQ Console Railway Backend",
        description="Agent backend with mandatory learning hook",
        version="1.0.0",
        lifespan=lifespan
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
    # Trace Explorer Query Models
    # ============================================================================
    class TraceQueryParams(BaseModel):
        session_id: Optional[str] = None
        user_id: Optional[str] = None
        limit: int = 100
        offset: int = 0
        start_date: Optional[str] = None
        end_date: Optional[str] = None

    # ============================================================================
    # Health Check
    # ============================================================================
    @app.get("/health")
    async def health_check():
        """Railway health check endpoint with smoking gun git_sha and agent contract status."""
        from torq_console.agents.protocols import validate_agent_contract
        from torq_console.research import get_research_status

        # Check agent contract
        agent_contract_ok = False
        agent_contract_schema = None
        agent_name = None

        try:
            from torq_console.agents.torq_prince_flowers.core.agent import TORQPrinceFlowers
            test_agent = TORQPrinceFlowers()
            is_valid, _ = validate_agent_contract(test_agent)
            agent_contract_ok = is_valid
            agent_contract_schema = "torq-agent-run-v1"
            agent_name = "torq_prince_flowers"
        except Exception as e:
            agent_contract_ok = False
            agent_name = str(e)

        # Check research status
        research_status = get_research_status()

        return {
            "status": "healthy" if agent_contract_ok else "degraded",
            "service": "torq-console-railway",
            "_schema": "torq-deploy-v1",
            "running_file": "torq_console/ui/railway_app.py",
            "git_sha": get_git_sha(),
            "app_version": get_app_version_with_source()[0],
            "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
            "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "learning_hook": "mandatory",
            # Agent contract status
            "agent_contract_ok": agent_contract_ok,
            "agent_contract_schema": agent_contract_schema,
            "agent_name": agent_name,
            # Research break-glass switch status
            "research_enabled": research_status["enabled"],
            "research_reason": research_status["reason"],
        }

    # ============================================================================
    # Chat Endpoint (with mandatory learning hook)
    # ============================================================================
    @app.post("/api/chat")
    async def chat(request: ChatRequest):
        """
        Agent chat endpoint with versioned response contract.

        Schema: torq-chat-response-v1 (FROZEN)

        Single envelope for both success and error responses.
        Success returns data, errors return error - never both.

        === DO NOT MODIFY RESPONSE STRUCTURE WITHOUT INCREMENTS SCHEMA VERSION ===
        """
        from torq_console.agents.torq_prince_flowers.core.agent import TORQPrinceFlowers
        from torq_console.telemetry.learning import (
            record_learning_event,
            calculate_consulting_reward,
        )
        from torq_console.ui.api_contracts import (
            success_response,
            error_response,
            map_exception_to_error_category,
        )
        import time
        import uuid

        start_time = time.time()
        trace_id = request.trace_id or f"chat-{int(time.time() * 1000)}"
        request_id = f"req-{trace_id}-{uuid.uuid4().hex[:8]}"
        logger.info(f"[{trace_id}] Chat request: {request.message[:100]}...")

        try:
            agent = TORQPrinceFlowers()
            response_data = await agent.arun(request.message)
            duration = time.time() - start_time

            # Extract response fields
            response_text = response_data.get("response", "")
            success = response_data.get("success", True)

            if not success:
                # Agent reported failure - use stable error category
                error_type = response_data.get("error_type", "provider_error")
                # Map common agent errors to stable categories
                if "timeout" in str(error_type).lower():
                    error_type = "provider_error"
                elif "rate" in str(error_type).lower():
                    error_type = "rate_limited"
                else:
                    error_type = "provider_error"

                return error_response(
                    request_id=request_id,
                    trace_id=trace_id,
                    error_type=error_type,
                    message=response_data.get("error", "Agent processing failed"),
                    code=502,  # Provider errors are 502
                    duration_ms=int(duration * 1000),
                    debug_type=response_data.get("error_type"),
                    session_id=request.session_id,
                ).model_dump()

            # === MANDATORY LEARNING HOOK (best-effort) ===
            learning_recorded = False
            try:
                reward = calculate_consulting_reward(
                    evidence_level=response_data.get("evidence_level") or "low",
                    routing_success=response_data.get("routing_success", True),
                    policy_compliance=response_data.get("policy_compliance") or 0.8,
                    user_satisfaction_prediction=response_data.get("satisfaction") or 0.5,
                    response_time=duration,
                )
                await record_learning_event(
                    trace_id=trace_id,
                    session_id=request.session_id,
                    agent_name="prince_flowers",
                    user_query=request.message,
                    agent_response=response_text,
                    reward=reward,
                    metadata={
                        "duration_ms": int(duration * 1000),
                        "evidence_level": response_data.get("evidence_level"),
                        "routing_success": response_data.get("routing_success"),
                        "tools_used": response_data.get("tools_used", []),
                        "request_id": request_id,
                    }
                )
                learning_recorded = True
                logger.info(f"[{trace_id}] Learning event recorded: reward={reward:.3f}")
            except Exception as e:
                # Learning hook failure should not break the response
                logger.error(f"[{trace_id}] Learning hook failed (non-fatal): {e}")

            # Build versioned success response with telemetry info
            return success_response(
                request_id=request_id,
                trace_id=trace_id,
                response=response_text,
                agent=response_data.get("agent_name", "prince_flowers"),
                duration_ms=int(duration * 1000),
                metadata={
                    "evidence_level": response_data.get("evidence_level"),
                    "routing_success": response_data.get("routing_success"),
                    "tools_used": response_data.get("tools_used", []),
                },
                session_id=request.session_id,
                learning_recorded=learning_recorded,
                telemetry={
                    "enabled": telemetry_config.get('enabled', True),
                    "sink": "supabase" if telemetry_config.get('enabled') else "null",
                },
            ).model_dump()

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{trace_id}] Chat error: {e}")
            logger.error(traceback.format_exc())

            # Map exception to stable error category
            error_type, http_code = map_exception_to_error_category(e)

            return error_response(
                request_id=request_id,
                trace_id=trace_id,
                error_type=error_type,
                message=str(e)[:500],  # Truncate for safety
                code=http_code,
                duration_ms=int(duration * 1000),
                debug_type=type(e).__name__,
                session_id=request.session_id,
                telemetry={
                    "enabled": telemetry_config.get('enabled', True),
                    "sink": "supabase" if telemetry_config.get('enabled') else "null",
                },
            ).model_dump()

    # ============================================================================
    # Telemetry Endpoints (best-effort)
    # ============================================================================
    @app.post("/api/telemetry")
    async def ingest_telemetry(request: TelemetryIngest):
        """
        Ingest telemetry data from Vercel/frontend.

        Best-effort mode: errors are logged but don't fail the request.
        This prevents test noise and user-facing slowdowns from telemetry issues.
        """
        # Check if telemetry is disabled
        telemetry_config = getattr(app.state, 'telemetry_config', {})
        if telemetry_config.get('disabled_due_to_error', False):
            return {
                "ok": False,
                "skipped": True,
                "reason": "telemetry_disabled_due_to_error",
                "last_error": telemetry_config.get('last_error'),
            }

        if not telemetry_config.get('enabled', True):
            return {
                "ok": False,
                "skipped": True,
                "reason": "telemetry_disabled",
            }

        try:
            from torq_console.telemetry import supabase_ingest
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
            # Extract error type for classification
            error_str = str(e).lower()
            error_code = "unknown"

            if "401" in error_str or "unauthorized" in error_str:
                error_code = "401"
                error_type = "authentication"
            elif "403" in error_str or "forbidden" in error_str:
                error_code = "403"
                error_type = "authorization"
            elif "409" in error_str or "conflict" in error_str:
                error_code = "409"
                error_type = "conflict"
            elif "429" in error_str or "rate limit" in error_str:
                error_code = "429"
                error_type = "rate_limit"
            elif "503" in error_str or "unavailable" in error_str:
                error_code = "503"
                error_type = "service_unavailable"
            else:
                error_type = "unknown"

            logger.error(f"Telemetry ingest error: {e}")

            # In strict mode, raise; in best-effort, log and continue
            if telemetry_config.get('strict', False):
                raise HTTPException(status_code=500, detail=str(e))

            # Log once per error type to avoid spam
            last_error = telemetry_config.get('last_error')
            if last_error != error_code:
                logger.warning(f"Telemetry error [{error_code}]: {error_type} - will be logged once")
                app.state.telemetry_config['last_error'] = error_code
                app.state.telemetry_config['disabled_due_to_error'] = (error_code == "401")

            return {
                "ok": False,
                "error": {
                    "code": error_code,
                    "type": error_type,
                    "message": str(e)[:200],  # Truncate for safety
                },
                "telemetry_failed": True,
            }

    @app.get("/api/telemetry/health")
    async def telemetry_health():
        """
        Check telemetry system health with self-diagnosis.

        Reports:
        - Supabase connection status
        - Project ref detection
        - Key type (service_role vs anon)
        - Access test result (read-only)
        - Actionable recommendations
        """
        from torq_console.telemetry.health import get_telemetry_diagnostics

        telemetry_config = getattr(app.state, 'telemetry_config', {})

        base_health = {
            "enabled": telemetry_config.get('enabled', True),
            "strict": telemetry_config.get('strict', False),
            "disabled_due_to_error": telemetry_config.get('disabled_due_to_error', False),
            "last_error": telemetry_config.get('last_error'),
        }

        # Get detailed diagnostics
        try:
            diagnostics = await get_telemetry_diagnostics()
            diagnostics.update(base_health)

            # Use status from access_test
            access_test_status = diagnostics.get("access_test", {}).get("status")
            if access_test_status:
                diagnostics["status"] = access_test_status
            elif diagnostics.get("access_test", {}).get("success"):
                diagnostics["status"] = "healthy"
            else:
                diagnostics["status"] = "degraded"

            return diagnostics
        except Exception as e:
            return {
                **base_health,
                "status": "error",
                "error": str(e),
                "supabase_project_ref": None,
                "access_test": {"success": False, "error": "diagnostic_failed"},
            }

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
    async def approve_policy(request: Request, policy_data: LearningPolicyUpdate):
        """Approve a new learning policy (admin only)."""
        from torq_console.telemetry.admin import admin_required, log_admin_action

        # Admin check
        token = request.headers.get("X-Torq-Admin-Token", "")
        if not verify_admin_token(token):
            await log_admin_action(
                action="policy_approve_denied",
                details={"policy_id": policy_data.policy_id},
                actor="unauthorized",
                success=False,
            )
            raise HTTPException(status_code=401, detail="Valid admin token required")

        actor = f"token_{hash(token) % 10000:04d}" if token else "dev"

        try:
            from torq_console.telemetry.learning import approve_policy_version
            result = await approve_policy_version(
                policy_id=policy_data.policy_id,
                routing_data=policy_data.routing_data,
            )

            await log_admin_action(
                action="policy_approve",
                details={"policy_id": policy_data.policy_id, "result": result},
                actor=actor,
                success=True,
            )

            return {"ok": True, "policy_id": policy_data.policy_id, **result}
        except Exception as e:
            logger.error(f"Policy approval error: {e}")
            await log_admin_action(
                action="policy_approve",
                details={"policy_id": policy_data.policy_id, "error": str(e)},
                actor=actor,
                success=False,
            )
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/learning/policy/rollback")
    async def rollback_policy(request: Request):
        """Rollback to previous policy (admin only)."""
        from torq_console.telemetry.admin import log_admin_action

        # Admin check
        token = request.headers.get("X-Torq-Admin-Token", "")
        if not verify_admin_token(token):
            await log_admin_action(
                action="policy_rollback_denied",
                details={},
                actor="unauthorized",
                success=False,
            )
            raise HTTPException(status_code=401, detail="Valid admin token required")

        actor = f"token_{hash(token) % 10000:04d}" if token else "dev"

        try:
            from torq_console.telemetry.learning import rollback_policy_version
            result = await rollback_policy_version()

            await log_admin_action(
                action="policy_rollback",
                details={"result": result},
                actor=actor,
                success=True,
            )

            return {"ok": True, **result}
        except Exception as e:
            logger.error(f"Policy rollback error: {e}")
            await log_admin_action(
                action="policy_rollback",
                details={"error": str(e)},
                actor=actor,
                success=False,
            )
            raise HTTPException(status_code=500, detail=str(e))


def verify_admin_token(token: str) -> bool:
    """Verify admin token is valid."""
    import os
    import hmac

    admin_token = os.getenv("TORQ_ADMIN_TOKEN", "")
    if not admin_token:
        # Dev mode: no admin token required
        return True
    if not token:
        return False
    return hmac.compare_digest(token, admin_token)

    # ============================================================================
    # Trace Explorer API - Query telemetry traces with deploy identity filtering
    # ============================================================================
    @app.get("/api/traces")
    async def list_traces(
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """
        List telemetry traces with filtering and pagination.

        All traces include deploy identity (git_sha, platform, app_version)
        for correlation with the code that generated them.
        """
        try:
            from torq_console.telemetry import list_traces as db_list_traces

            # Build filters from query params
            filters = {}
            if session_id:
                filters["session_id"] = session_id
            if user_id:
                filters["user_id"] = user_id
            if start_date:
                filters["start_date"] = start_date
            if end_date:
                filters["end_date"] = end_date

            traces = await db_list_traces(
                filters=filters,
                limit=limit,
                offset=offset,
            )

            return {
                "traces": traces,
                "count": len(traces),
                "limit": limit,
                "offset": offset,
                "filters": filters,
            }
        except Exception as e:
            logger.error(f"List traces error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/traces/{trace_id}")
    async def get_trace(trace_id: str):
        """
        Get a single trace with all its metadata and deploy identity.

        Returns the complete trace record including deploy stamp fields
        (deploy_git_sha, deploy_platform, deploy_app_version) for correlation.
        """
        try:
            from torq_console.telemetry import get_trace as db_get_trace

            trace = await db_get_trace(trace_id)

            if not trace:
                raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

            return trace
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get trace error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/traces/{trace_id}/spans")
    async def get_trace_spans(
        trace_id: str,
        limit: int = 500,
        offset: int = 0,
    ):
        """
        Get all spans for a specific trace.

        Spans include timing, parent-child relationships, and deploy identity.
        Returns a tree structure that can be visualized in a timeline UI.
        """
        try:
            from torq_console.telemetry import get_trace_spans as db_get_spans

            spans = await db_get_spans(
                trace_id=trace_id,
                limit=limit,
                offset=offset,
            )

            if not spans:
                return {"spans": [], "trace_id": trace_id, "count": 0}

            # Build span tree for frontend visualization
            span_map = {span["span_id"]: span for span in spans}
            root_spans = [s for s in spans if not s.get("parent_span_id")]

            for span in spans:
                span["children"] = []

            for span in spans:
                parent_id = span.get("parent_span_id")
                if parent_id and parent_id in span_map:
                    span_map[parent_id]["children"].append(span)

            return {
                "trace_id": trace_id,
                "spans": spans,
                "root_spans": root_spans,
                "count": len(spans),
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"Get trace spans error: {e}")
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
            # Module path identification (zero guesswork)
            "running_file": "torq_console/ui/railway_app.py",
            "running_module": __name__,
            # Platform and service
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
