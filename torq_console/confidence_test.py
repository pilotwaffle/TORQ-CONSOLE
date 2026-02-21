"""
torq_console.confidence_test

Runs:
- 10 direct prompts
- 10 research prompts (tools enabled)
Validates:
- HTTP 200
- success flag
- no banned substrings
- latency stats (avg/p95)
Optional:
- RSS memory delta if /api/status returns pid and psutil is available
"""

from __future__ import annotations

import argparse
import statistics
import time
from typing import Dict, Any, List, Tuple

import requests

BANNED_SUBSTRINGS = [
    "direct reasoning execution (placeholder)",
    "placeholder",
    "stub",
]


def _has_banned(text: str) -> Tuple[bool, str]:
    """Check if response contains banned placeholder substrings."""
    low = (text or "").lower()
    for bad in BANNED_SUBSTRINGS:
        if bad in low:
            return True, bad
    return False, ""


def post_chat(base_url: str, message: str, tools: List[str] | None = None, timeout: int = 60) -> Tuple[float, Dict[str, Any]]:
    """Send a chat request and return latency + response data."""
    t0 = time.time()
    r = requests.post(
        f"{base_url}/api/chat",
        json={"message": message, "tools": tools or []},
        timeout=timeout,
    )
    dt = time.time() - t0
    data = r.json() if r.headers.get("content-type", "").lower().startswith("application/json") else {"raw": r.text}
    data["_http_status"] = r.status_code
    return dt, data


def try_get_pid(base_url: str) -> int | None:
    """Try to get process ID from /api/status endpoint."""
    try:
        r = requests.get(f"{base_url}/api/status", timeout=5)
        if r.status_code != 200:
            return None
        js = r.json()
        return js.get("pid") or js.get("process_id")
    except Exception:
        return None


def try_rss_bytes(pid: int) -> int | None:
    """Try to get RSS memory usage for a process."""
    try:
        import psutil  # type: ignore
        p = psutil.Process(pid)
        return int(p.memory_info().rss)
    except Exception:
        return None


def summarize_latencies(name: str, latencies: List[float]) -> Dict[str, float]:
    """Calculate latency statistics."""
    lat_sorted = sorted(latencies)
    p95 = lat_sorted[int(0.95 * (len(lat_sorted) - 1))]
    return {
        f"{name}_count": float(len(latencies)),
        f"{name}_avg_s": round(statistics.mean(latencies), 3),
        f"{name}_p95_s": round(p95, 3),
        f"{name}_max_s": round(max(latencies), 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="TORQ Console confidence test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8899")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--direct-n", type=int, default=10)
    parser.add_argument("--research-n", type=int, default=10)
    parser.add_argument("--min-direct-latency", type=float, default=0.3, help="Minimum direct latency (s) to detect stubs")
    parser.add_argument("--min-research-latency", type=float, default=0.7, help="Minimum research latency (s) to detect stubs")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    direct_lat: List[float] = []
    research_lat: List[float] = []

    pid = try_get_pid(base)
    rss_before = try_rss_bytes(pid) if pid else None

    failures: List[str] = []

    # Direct prompts
    print(f"[CONFIDENCE] Running {args.direct_n} direct prompts...")
    for i in range(args.direct_n):
        msg = f"Direct test {i+1}: What is 2+2? Respond with only the number."
        dt, data = post_chat(base, msg, tools=[], timeout=args.timeout)
        direct_lat.append(dt)

        if data.get("_http_status") != 200 or not data.get("success", True):
            failures.append(f"[DIRECT {i+1}] HTTP/Success failure: {data}")
            continue

        text = data.get("response", "") or ""

        # Check 1: Banned substrings (placeholders, stubs)
        bad, which = _has_banned(text)
        if bad:
            failures.append(f"[DIRECT {i+1}] Banned substring '{which}' in response: {text[:200]}")
            continue

        # Check 2: Fallback message detection (LLM provider not available)
        if "cannot generate a response" in text.lower() or "without an llm provider" in text.lower():
            failures.append(f"[DIRECT {i+1}] Fallback message detected (LLM provider missing): {text[:200]}")
            continue

        # Check 3: Content quality (must have actual content, not just acknowledgment)
        if len(text.strip()) < 10:
            failures.append(f"[DIRECT {i+1}] Response too short ({len(text)} chars): {text[:100]}")
            continue

        # Check 4: Latency floor (detect stub/fast-fail responses)
        if dt < args.min_direct_latency:
            failures.append(f"[DIRECT {i+1}] Latency too fast ({dt:.3f}s < {args.min_direct_latency}s) - likely stub response")

        if (i + 1) % 5 == 0:
            print(f"[CONFIDENCE] Completed {i+1}/{args.direct_n} direct prompts")

    # Research prompts
    print(f"[CONFIDENCE] Running {args.research_n} research prompts...")
    for i in range(args.research_n):
        msg = f"Research test {i+1}: What time is it in Texas right now? Explain briefly."
        dt, data = post_chat(base, msg, tools=["web_search"], timeout=args.timeout)
        research_lat.append(dt)

        if data.get("_http_status") != 200 or not data.get("success", True):
            failures.append(f"[RESEARCH {i+1}] HTTP/Success failure: {data}")
            continue

        text = data.get("response", "") or ""

        # Check 1: Banned substrings (placeholders, stubs)
        bad, which = _has_banned(text)
        if bad:
            failures.append(f"[RESEARCH {i+1}] Banned substring '{which}' in response: {text[:200]}")
            continue

        # Check 2: Fallback message detection (LLM provider not available)
        if "cannot generate a response" in text.lower() or "without an llm provider" in text.lower():
            failures.append(f"[RESEARCH {i+1}] Fallback message detected (LLM provider missing): {text[:200]}")
            continue

        # Check 3: Content quality (must have actual content)
        if len(text.strip()) < 20:
            failures.append(f"[RESEARCH {i+1}] Response too short ({len(text)} chars): {text[:100]}")
            continue

        # Check 4: Latency floor (research should be slower due to web search)
        if dt < args.min_research_latency:
            failures.append(f"[RESEARCH {i+1}] Latency too fast ({dt:.3f}s < {args.min_research_latency}s) - web search likely not executed")

        if (i + 1) % 5 == 0:
            print(f"[CONFIDENCE] Completed {i+1}/{args.research_n} research prompts")

    rss_after = try_rss_bytes(pid) if pid else None

    print("\n=== CONFIDENCE TEST RESULTS ===")
    print(summarize_latencies("direct", direct_lat))
    print(summarize_latencies("research", research_lat))

    if rss_before is not None and rss_after is not None:
        delta_mb = (rss_after - rss_before) / (1024 * 1024)
        print(f"rss_before_mb={rss_before/(1024*1024):.1f} rss_after_mb={rss_after/(1024*1024):.1f} rss_delta_mb={delta_mb:.1f}")
    else:
        print("rss_check=skipped (pid not available from /api/status or psutil not installed)")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(" -", f)
        return 1

    print("\n[OK] All requests succeeded. No banned substrings detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
