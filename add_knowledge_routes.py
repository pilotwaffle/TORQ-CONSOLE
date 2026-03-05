"""
Script to add Knowledge Plane routes to railway_app.py
"""
import re

# Read the current railway_app.py
with open("E:/TORQ-CONSOLE/railway_app.py", "r") as f:
    content = f.read()

# Find the line after CORS middleware and before Security Middleware
# Insert the Knowledge Plane routes import

# Find the place to insert - after app.add_middleware
insert_marker = """app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Knowledge Plane Routes
# ============================================================================

from torq_console.knowledge_plane.railway_integration import knowledge_router
app.include_router(knowledge_router)

# ============================================================================
# Security Middleware (inline to avoid import)
# =========================================================================="""

# Replace the section
new_content = content.replace(
    """app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Security Middleware (inline to avoid import)
# ==========================================================================""",
    insert_marker
)

# Also update the root endpoint to include knowledge endpoints
old_root_endpoints = '''"endpoints": [
            "/health",
            "/api/chat",
            "/api/telemetry",
            "/api/learning",
            "/api/monitor/summary",
            "/api/monitor/alerts",
            "/api/monitor/compute",
            "/api/monitor/baseline",
            "/api/monitor/metrics/daily",
        ]'''

new_root_endpoints = '''"endpoints": [
            "/health",
            "/api/chat",
            "/api/telemetry",
            "/api/learning",
            "/api/monitor/summary",
            "/api/monitor/alerts",
            "/api/monitor/compute",
            "/api/monitor/baseline",
            "/api/monitor/metrics/daily",
            "/api/knowledge/store",
            "/api/knowledge/search",
            "/api/knowledge/recent",
            "/api/knowledge/stats",
            "/api/knowledge/health"
        ]'''

new_content = new_content.replace(old_root_endpoints, new_root_endpoints)

# Also update the description
new_content = new_content.replace(
    'description="Agent backend with mandatory learning hook and drift monitoring"',
    'description="Agent backend with mandatory learning hook, drift monitoring, and Knowledge Plane"'
)

# Update version
new_content = new_content.replace(
    "APP_VERSION = os.getenv('APP_VERSION', '1.0.10-standalone')",
    "APP_VERSION = os.getenv('APP_VERSION', '1.1.0-knowledge-plane')"
)

# Write the updated content
with open("E:/TORQ-CONSOLE/railway_app.py", "w") as f:
    f.write(new_content)

print("Updated railway_app.py with Knowledge Plane routes")
