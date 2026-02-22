#!/usr/bin/env python3
"""
Update build_meta.json with current git SHA.

Run this before pushing to ensure Railway has the fingerprint.
Usage: python scripts/update_build_meta.py
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Get git SHA
result = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    capture_output=True,
    text=True,
    check=True
)
git_sha = result.stdout.strip()

# Get short SHA
short_sha = git_sha[:12]

# Get current version (read from railway_app.py)
# Prefer literal string values over os.getenv() calls
railway_app = Path(__file__).parent.parent / "railway_app.py"
version = "unknown"
with open(railway_app) as f:
    for line in f:
        if "APP_VERSION = " in line and "os.getenv" not in line:
            # Extract version string from literal assignment
            version = line.split("APP_VERSION = ")[1].strip().strip('"')
            if version and version != "unknown":
                break

# Build metadata
meta = {
    "git_sha": git_sha,
    "git_short_sha": short_sha,
    "version": version,
    "built_at": datetime.now(timezone.utc).isoformat(),
    "branch": subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    ).stdout.strip(),
    "commit_message": subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        capture_output=True,
        text=True,
        check=True
    ).stdout.strip(),
}

# Write to torq_console/build_meta.json (location accessible at runtime)
build_meta_path = Path(__file__).parent.parent / "torq_console" / "build_meta.json"
build_meta_path.parent.mkdir(exist_ok=True)
with open(build_meta_path, "w") as f:
    json.dump(meta, f, indent=2)

print(f"[OK] Build metadata updated:")
print(f"   git_sha: {short_sha}")
print(f"   version: {version}")
print(f"   built_at: {meta['built_at']}")
print(f"   file: {build_meta_path.relative_to(Path(__file__).parent.parent)}")
