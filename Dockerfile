# TORQ Console - Railway Production Dockerfile
FROM python:3.11-slim

# Build-time args for deploy identity (injected at build, never hardcoded)
ARG GIT_SHA=unknown
ARG GIT_BRANCH=unknown

# Cache buster for deterministic fresh builds
ARG CACHE_BUST=20260222-v1
RUN echo "cache_bust=$CACHE_BUST"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONDISABLEBYTECODE=1
ENV PIPNOcachedir=1
ENV PIPDISABLEPIPVERSIONCHECK=1
ENV TORQCONSOLEPRODUCTION=true
ENV TORQDISABLELOCALLM=true
ENV TORQDISABLEGPU=true

# Inject build-time SHA as runtime env var (fallback for get_git_sha())
ENV GIT_SHA=$GIT_SHA
ENV GIT_BRANCH=$GIT_BRANCH

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements-railway.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements-railway.txt

# Copy application code
# Deterministic cache buster - forces new layer every build
RUN date -u +"%Y-%m-%dT%H:%M:%SZ" > /tmp/build_timestamp

COPY . .

# Add /app to Python path so imports work without package install
ENV PYTHONPATH=/app:$PYTHONPATH

# Write build_meta.json directly (without importing torq_console)
# This is the file fallback for get_git_sha() / get_build_time() / get_build_branch()
RUN python - << 'PY'
import json, os, datetime, pathlib

meta = {
    "git_sha": os.getenv("GIT_SHA", "unknown"),
    "built_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    "branch": os.getenv("GIT_BRANCH", "unknown"),
}
# Write directly to torq_console directory
path = pathlib.Path("/app/torq_console/build_meta.json")
path.parent.mkdir(parents=True, exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    json.dump(meta, f)
    print("[build] wrote", path, "->", meta)
PY

# Start command - Railway exposes port 8080
ENV PORT=8080
CMD ["python", "-m", "uvicorn", "torq_console.ui.railway_app:app", "--host", "0.0.0.0", "--port", "8080"]
