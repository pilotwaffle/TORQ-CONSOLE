"""
torq_console.preflight

Run before launching the backend:
- Detect WindowsApps python stub
- Load .env
- Validate provider-related env vars
- Initialize provider via LLMManager
- Ensure Prince Flowers loads
- Optional: run a real "direct" LLM smoke call (fast, tiny prompt)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


BANNED_EXECUTABLE_SUBSTRINGS = [
    r"WindowsApps",  # Windows Store python stub
]

# Keep this list conservative: fail only on strings that *must never* appear in runtime responses.
BANNED_RESPONSE_SUBSTRINGS = [
    "direct reasoning execution (placeholder)",
    "placeholder",
    "stub",
]

# Map providers -> required env vars (adjust to match your adapters)
PROVIDER_REQUIRED_ENV = {
    "claude": ["ANTHROPIC_API_KEY"],   # if ClaudeProvider uses Anthropic
    "openai": ["OPENAI_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
    "zai": ["ZAI_API_KEY"],
    "ollama": ["OLLAMA_BASE_URL"],     # typically no key required
}

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "claude")


@dataclass
class PreflightResult:
    ok: bool
    provider: str
    details: Dict[str, Any]
    error: Optional[str] = None


def _fail(provider: str, msg: str, details: Optional[Dict[str, Any]] = None) -> PreflightResult:
    return PreflightResult(ok=False, provider=provider, details=details or {}, error=msg)


def _ok(provider: str, details: Dict[str, Any]) -> PreflightResult:
    return PreflightResult(ok=True, provider=provider, details=details)


def check_python_interpreter() -> Optional[str]:
    """Check for banned Python interpreter paths (e.g., WindowsApps stub)."""
    exe = sys.executable or ""
    for bad in BANNED_EXECUTABLE_SUBSTRINGS:
        if bad.lower() in exe.lower():
            return f"Detected disallowed Python interpreter path: {exe} (contains '{bad}'). Use your installed Python/venv interpreter."
    return None


def load_env(repo_root: str) -> Optional[str]:
    """Load .env file from repo root."""
    # Your app already loads env in some places; this is just to make preflight deterministic.
    if load_dotenv is None:
        return "python-dotenv not installed; cannot load .env deterministically in preflight."
    env_path = os.path.join(repo_root, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=False)
        return None
    # Not necessarily fatal in production environments that use real env vars
    return None


def validate_provider_env(provider: str) -> Optional[str]:
    """Validate that required environment variables are set for the provider."""
    req = PROVIDER_REQUIRED_ENV.get(provider, [])
    missing = []
    for key in req:
        val = os.getenv(key)
        if not val:
            missing.append(key)
        # protect against placeholder patterns you used earlier
        if val and "your_" in val and "_here" in val:
            missing.append(f"{key} (looks like placeholder)")
    if missing:
        return f"Missing/invalid env for provider '{provider}': {', '.join(missing)}"
    return None


def init_provider(provider: str) -> Dict[str, Any]:
    """
    Try to initialize the provider via your LLMManager.
    Adjust the import paths below to match your repo exactly.
    """
    t0 = time.time()
    # These imports should be lightweight and fail loudly if startup wiring is broken.
    from torq_console.core.console import TorqConsole  # noqa
    from torq_console.core.config import TorqConfig  # noqa

    config = TorqConfig()
    console = TorqConsole(config=config)

    # Your notes: TorqConsole → llm_manager → ClaudeProvider → Prince
    llm_manager = getattr(console, "llm_manager", None)
    if llm_manager is None:
        raise RuntimeError("TorqConsole.llm_manager is missing")

    # Prefer explicit provider, fallback to env-driven selection in your manager
    prov = llm_manager.get_provider(provider) if hasattr(llm_manager, "get_provider") else None
    if prov is None:
        raise RuntimeError(f"LLMManager could not return provider '{provider}'")

    dt = time.time() - t0
    return {
        "provider_class": prov.__class__.__name__,
        "init_seconds": round(dt, 3),
    }


def load_prince_agent(repo_root: str) -> Dict[str, Any]:
    """
    Ensure Prince Flowers agent loads without exceptions.
    Adjust import/factory to your actual Prince agent path.
    """
    t0 = time.time()

    # Import TorqConsole to access Prince Flowers agent
    from torq_console.core.console import TorqConsole  # noqa
    from torq_console.core.config import TorqConfig  # noqa

    config = TorqConfig()
    console = TorqConsole(config=config)

    # Try common places for agent resolution:
    prince = None
    if hasattr(console, "agents") and isinstance(console.agents, dict):
        prince = console.agents.get("prince_flowers") or console.agents.get("prince")  # type: ignore

    if prince is None and hasattr(console, "get_agent"):
        try:
            prince = console.get_agent("prince_flowers")  # type: ignore
        except Exception:
            prince = None

    if prince is None:
        # Last resort: import directly (adjust path)
        try:
            from torq_console.agents.torq_prince_flowers.interface import TORQPrinceFlowersInterface  # noqa
            prince = TORQPrinceFlowersInterface(console_instance=console)  # type: ignore
        except Exception as e:
            # If Prince fails to load, raise an error
            raise RuntimeError(f"Failed to load Prince Flowers agent: {e}")

    dt = time.time() - t0
    return {
        "agent_class": prince.__class__.__name__,
        "load_seconds": round(dt, 3),
    }


def direct_llm_smoke(provider: str) -> Dict[str, Any]:
    """
    Optional: do a tiny real generate to ensure direct path is wired.
    This is what will catch the failing A1 condition early.
    """
    from torq_console.core.console import TorqConsole  # noqa
    from torq_console.core.config import TorqConfig  # noqa

    config = TorqConfig()
    console = TorqConsole(config=config)
    llm_manager = getattr(console, "llm_manager", None)
    prov = llm_manager.get_provider(provider)

    prompt = "Answer with only: 4"
    t0 = time.time()
    text = prov.generate_response(prompt=prompt)  # adjust signature if needed
    dt = time.time() - t0

    lowered = (text or "").lower()
    for bad in BANNED_RESPONSE_SUBSTRINGS:
        if bad in lowered:
            raise RuntimeError(f"Smoke test response contains banned substring: '{bad}'")

    return {
        "smoke_seconds": round(dt, 3),
        "response_preview": (text or "")[:120],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="TORQ Console preflight checks")
    parser.add_argument("--repo-root", default=".", help="Path to repo root (where .env lives)")
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER), help="Provider name (claude/openai/deepseek/ollama/...)")
    parser.add_argument("--smoke", action="store_true", help="Run a real, tiny LLM smoke call (direct path)")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    provider = (args.provider or DEFAULT_PROVIDER).strip().lower()
    details: Dict[str, Any] = {
        "python_executable": sys.executable,
        "provider": provider,
    }

    try:
        err = check_python_interpreter()
        if err:
            res = _fail(provider, err, details)

        else:
            env_err = load_env(args.repo_root)
            if env_err:
                # treat as warning; add to details
                details["env_warning"] = env_err

            env_req_err = validate_provider_env(provider)
            if env_req_err:
                res = _fail(provider, env_req_err, details)
            else:
                details["provider_init"] = init_provider(provider)
                details["prince_load"] = load_prince_agent(args.repo_root)
                if args.smoke:
                    details["direct_smoke"] = direct_llm_smoke(provider)
                res = _ok(provider, details)

    except Exception as e:
        tb = traceback.format_exc()
        res = _fail(provider, f"{type(e).__name__}: {e}", {**details, "traceback": tb})

    if args.json:
        print(json.dumps(res.__dict__, indent=2))
    else:
        print(f"[PREFLIGHT] ok={res.ok} provider={res.provider}")
        if res.error:
            print(f"[PREFLIGHT] error: {res.error}")
        for k, v in details.items():
            if k == "traceback":
                continue
            print(f"[PREFLIGHT] {k}: {v}")
        if "traceback" in details:
            print(details["traceback"])

    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
