"""
TORQ Native Chrome Bridge - Host Process

This process runs on the user's machine and:
1. Speaks Chrome Native Messaging protocol (stdin/stdout)
2. Runs a FastAPI HTTP server (/v1/session, /v1/act, /v1/observe)
3. Maintains sessions, pending approvals, request correlation IDs

Environment variables:
    CHROME_BRIDGE_API_KEY: API key for HTTP authentication (optional, recommended)
    CHROME_BRIDGE_HOST: HTTP server host (default: 127.0.0.1)
    CHROME_BRIDGE_PORT: HTTP server port (default: 4545)

Usage:
    python host.py
"""
import asyncio
import json
import os
import struct
import sys
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uvicorn

# =============================================================================
# Configuration
# =============================================================================

API_KEY = os.getenv("CHROME_BRIDGE_API_KEY", "")
HOST = os.getenv("CHROME_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.getenv("CHROME_BRIDGE_PORT", "4545"))
# Set to '1' to run HTTP server without native messaging (for Railway/tunnel testing)
NO_NATIVE_MESSAGING = os.getenv("NO_NATIVE_MESSAGING", "") == "1"

app = FastAPI(
    title="TORQ Native Chrome Bridge",
    version="1.0.0",
    description="Native messaging bridge for Prince Flowers Agent browser operations"
)

# =============================================================================
# Native Messaging Framing (Chrome protocol)
# =============================================================================

def read_native_message() -> Optional[Dict[str, Any]]:
    """
    Read a message from Chrome via Native Messaging.
    Messages are length-prefixed with 4-byte little-endian integer.
    """
    try:
        raw_len = os.read(0, 4)  # stdin fd=0
        if not raw_len or len(raw_len) < 4:
            return None
        msg_len = struct.unpack("<I", raw_len)[0]
        raw = b""
        while len(raw) < msg_len:
            chunk = os.read(0, msg_len - len(raw))
            if not chunk:
                return None
            raw += chunk
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def send_native_message(msg: Dict[str, Any]) -> None:
    """
    Send a message to Chrome via Native Messaging.
    Messages are length-prefixed with 4-byte little-endian integer.
    """
    data = json.dumps(msg).encode("utf-8")
    os.write(1, struct.pack("<I", len(data)))  # stdout fd=1
    os.write(1, data)


# =============================================================================
# Authentication
# =============================================================================

def auth(authorization: Optional[str]) -> None:
    """Validate Bearer token if API_KEY is set."""
    if not API_KEY:
        return
    if not authorization or authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")


# =============================================================================
# Session & Request State
# =============================================================================

SESSIONS: Dict[str, Dict[str, Any]] = {}
PENDING_RESULTS: Dict[str, asyncio.Future] = {}


def now_ts() -> int:
    """Current Unix timestamp."""
    return int(time.time())


# =============================================================================
# API Models (Pydantic)
# =============================================================================

class SessionReq(BaseModel):
    metadata: Dict[str, Any] = {}


class ActReq(BaseModel):
    session_id: str
    actions: List[Dict[str, Any]]
    require_approval: bool = True


class ObserveReq(BaseModel):
    session_id: str
    what: List[str] = ["console_logs"]


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "torq-chrome-bridge",
        "version": "1.0.0",
        "active_sessions": len(SESSIONS),
        "pending_requests": len(PENDING_RESULTS)
    }


@app.post("/v1/session")
async def create_session(req: SessionReq, authorization: Optional[str] = Header(default=None)):
    """
    Create a new browser session.

    Returns a session_id that must be approved before actions can execute.
    """
    auth(authorization)
    sid = str(uuid.uuid4())
    SESSIONS[sid] = {
        "metadata": req.metadata,
        "approved": False,
        "created_at": now_ts(),
        "last_seen": now_ts(),
    }
    return {
        "ok": True,
        "session_id": sid,
        "message": "Session created. Approve in Chrome extension popup before executing actions."
    }


@app.post("/v1/act")
async def act(req: ActReq, authorization: Optional[str] = Header(default=None)):
    """
    Execute browser actions.

    Actions are sent to the Chrome extension which executes them in the active tab.
    If require_approval=True and session not approved, returns needs_approval response.
    """
    auth(authorization)
    sess = SESSIONS.get(req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    sess["last_seen"] = now_ts()

    # Approval gate
    if req.require_approval and not sess.get("approved"):
        return {
            "ok": False,
            "needs_approval": True,
            "session_id": req.session_id,
            "message": "Approval required in Chrome extension popup (enter session_id, click Approve).",
            "actions_preview": req.actions
        }

    # Create request and wait for result
    request_id = str(uuid.uuid4())
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    PENDING_RESULTS[request_id] = fut

    # Send execute to extension
    send_native_message({
        "type": "execute",
        "request_id": request_id,
        "session_id": req.session_id,
        "require_approval": req.require_approval,
        "actions": req.actions
    })

    try:
        result = await asyncio.wait_for(fut, timeout=120)
        return result
    except asyncio.TimeoutError:
        PENDING_RESULTS.pop(request_id, None)
        raise HTTPException(status_code=504, detail="Timed out waiting for extension result")


@app.post("/v1/observe")
async def observe(req: ObserveReq, authorization: Optional[str] = Header(default=None)):
    """
    Observe browser state (console logs, network events, etc.).

    In v1, this is a placeholder. Best implemented as an "execute" with observe ops.
    """
    auth(authorization)
    if req.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    # v1: observe returns empty data
    # v2: can send "observe" action to extension and collect real data
    return {
        "ok": True,
        "session_id": req.session_id,
        "data": {k: [] for k in req.what},
        "note": "v1: observe is stubbed. Use execute actions for real data collection."
    }


@app.get("/v1/sessions")
async def list_sessions(authorization: Optional[str] = Header(default=None)):
    """List all active sessions (debug endpoint)."""
    auth(authorization)
    return {
        "ok": True,
        "sessions": {
            sid: {
                "approved": s["approved"],
                "created_at": s["created_at"],
                "last_seen": s["last_seen"],
                "metadata": s["metadata"]
            }
            for sid, s in SESSIONS.items()
        }
    }


@app.delete("/v1/session/{session_id}")
async def delete_session(session_id: str, authorization: Optional[str] = Header(default=None)):
    """Delete a session."""
    auth(authorization)
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    del SESSIONS[session_id]
    return {"ok": True, "message": f"Session {session_id} deleted"}


# =============================================================================
# Native Message Handling Loop
# =============================================================================

async def native_loop():
    """
    Main loop for processing messages from Chrome extension.
    Runs in the main thread event loop.
    """
    print("[TORQ Bridge] Native message loop started", file=sys.stderr)
    while True:
        msg = await asyncio.to_thread(read_native_message)
        if msg is None:
            print("[TORQ Bridge] No more messages, exiting", file=sys.stderr)
            break

        mtype = msg.get("type")
        request_id = msg.get("request_id")

        if mtype == "result":
            # Extension returned action results
            fut = PENDING_RESULTS.pop(request_id, None)
            if fut and not fut.done():
                fut.set_result(msg)
            continue

        if mtype == "approve":
            # User approved session in extension popup
            sid = msg.get("session_id")
            if sid in SESSIONS:
                SESSIONS[sid]["approved"] = True
                SESSIONS[sid]["last_seen"] = now_ts()
                print(f"[TORQ Bridge] Session {sid} approved", file=sys.stderr)
            # Ack
            send_native_message({
                "type": "ack",
                "request_id": request_id,
                "session_id": sid,
                "ok": True
            })
            continue

        if mtype == "deny":
            # User denied session in extension popup
            sid = msg.get("session_id")
            if sid in SESSIONS:
                SESSIONS[sid]["approved"] = False
                SESSIONS[sid]["last_seen"] = now_ts()
                print(f"[TORQ Bridge] Session {sid} denied", file=sys.stderr)
            send_native_message({
                "type": "ack",
                "request_id": request_id,
                "session_id": sid,
                "ok": True
            })
            continue

        if mtype == "ping":
            # Heartbeat from extension
            send_native_message({
                "type": "pong",
                "request_id": request_id,
                "ts": now_ts()
            })
            continue

        # Unknown message type
        print(f"[TORQ Bridge] Unknown message type: {mtype}", file=sys.stderr)
        send_native_message({
            "type": "error",
            "request_id": request_id,
            "ok": False,
            "message": f"Unknown message type: {mtype}"
        })


def run_api():
    """Run FastAPI server (called in background thread)."""
    print(f"[TORQ Bridge] Starting API server on {HOST}:{PORT}", file=sys.stderr)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


def main():
    """
    Main entry point.

    Starts FastAPI in background thread and runs native loop in main thread.

    Environment variable NO_NATIVE_MESSAGING=1 runs API server only without
    native messaging (useful for Railway/tunnel testing).
    """
    print("[TORQ Bridge] Starting TORQ Native Chrome Bridge", file=sys.stderr)
    print(f"[TORQ Bridge] API: http://{HOST}:{PORT}", file=sys.stderr)
    print(f"[TORQ Bridge] API Key: {'set' if API_KEY else 'none (INSECURE!)'}", file=sys.stderr)
    if NO_NATIVE_MESSAGING:
        print("[TORQ Bridge] NO_NATIVE_MESSAGING=1: API server mode only", file=sys.stderr)

    # Start FastAPI in background thread
    t = threading.Thread(target=run_api, daemon=True)
    t.start()

    if NO_NATIVE_MESSAGING:
        # HTTP-only mode: keep running forever
        print("[TORQ Bridge] Running in HTTP-only mode (press Ctrl+C to stop)", file=sys.stderr)
        try:
            t.join()  # Wait forever since thread is daemon
        except KeyboardInterrupt:
            print("[TORQ Bridge] Shutting down", file=sys.stderr)
    else:
        # Native messaging mode: run native loop
        try:
            asyncio.run(native_loop())
        except KeyboardInterrupt:
            print("[TORQ Bridge] Shutting down", file=sys.stderr)


if __name__ == "__main__":
    main()
