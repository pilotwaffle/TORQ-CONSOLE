"""
torq_console.launch

Hardened launch wrapper:
- Runs preflight first
- Enables debug logging
- Ensures tracebacks print on startup failures
- Works on Windows + production
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback

import uvicorn

from torq_console.core.console import TorqConsole
from torq_console.core.config import TorqConfig
from torq_console.ui.web import WebUI


def run_preflight(repo_root: str, provider: str, smoke: bool) -> None:
    """Run preflight checks before starting the server."""
    # Import preflight only here so it doesn't interfere with module import order in prod
    from torq_console.preflight import main as preflight_main

    argv = ["--repo-root", repo_root, "--provider", provider]
    if smoke:
        argv.append("--smoke")

    old_argv = sys.argv[:]
    try:
        sys.argv = ["torq_console.preflight"] + argv
        code = preflight_main()
        if code != 0:
            raise RuntimeError("Preflight failed; refusing to start.")
    finally:
        sys.argv = old_argv


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch TORQ Console (hardened)")
    parser.add_argument("--repo-root", default=".", help="Repo root (where .env lives)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8899)
    parser.add_argument("--log-level", default=os.getenv("TORQ_LOG_LEVEL", "debug"))
    parser.add_argument("--access-log", action="store_true", default=True)
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER", "claude"))
    parser.add_argument("--preflight-smoke", action="store_true", help="Run real LLM smoke test before starting")
    args = parser.parse_args()

    # Make sure prints/logs flush immediately (prevents "silent" failures when output is buffered)
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    try:
        print(f"[LAUNCH] Starting TORQ Console preflight...")
        run_preflight(args.repo_root, args.provider, smoke=args.preflight_smoke)
        print(f"[LAUNCH] Preflight passed. Initializing console...")

        # Use TorqConfig for proper initialization
        config = TorqConfig()
        console = TorqConsole(config=config)
        ui = WebUI(console)

        print(f"[LAUNCH] Starting Uvicorn on {args.host}:{args.port}...")
        uvicorn.run(
            ui.app,
            host=args.host,
            port=args.port,
            log_level=args.log_level.lower(),  # Uvicorn expects lowercase
            access_log=args.access_log,
        )
        return 0

    except Exception as e:
        print("\n[LAUNCH] Startup failed.\n")
        print(f"[LAUNCH] {type(e).__name__}: {e}\n")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
