"""
Railway entry point for TORQ Console Web UI.
Creates a standalone FastAPI app instance for uvicorn without full TorqConsole.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

# Create a standalone FastAPI app for Railway
app = FastAPI(
    title="TORQ CONSOLE Web UI - Railway",
    description="Enhanced AI pair programming interface (standalone mode)",
    version="0.80.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTML Dashboard
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TORQ CONSOLE - Railway Deployment</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 800px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .badge {
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .info-card {
            background: #f3f4f6;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        .info-card h3 {
            color: #374151;
            font-size: 0.9em;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .info-card p {
            color: #667eea;
            font-size: 1.3em;
            font-weight: 600;
        }
        .endpoints {
            margin-top: 30px;
        }
        .endpoint {
            background: #f9fafb;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .endpoint-path {
            font-family: 'Courier New', monospace;
            color: #374151;
            font-weight: 600;
        }
        .endpoint-status {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .status-ok {
            background: #d1fae5;
            color: #065f46;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #6b7280;
            font-size: 0.9em;
        }
        .test-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9em;
            font-weight: 600;
            transition: background 0.3s;
        }
        .test-button:hover {
            background: #5568d3;
        }
        #test-results {
            margin-top: 20px;
            padding: 15px;
            background: #f9fafb;
            border-radius: 8px;
            display: none;
        }
        .test-results-show {
            display: block !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 TORQ CONSOLE</h1>
            <span class="badge">🟢 LIVE ON RAILWAY</span>
        </div>

        <div class="info-grid">
            <div class="info-card">
                <h3>Version</h3>
                <p>v0.80.0</p>
            </div>
            <div class="info-card">
                <h3>Mode</h3>
                <p>Standalone</p>
            </div>
            <div class="info-card">
                <h3>Platform</h3>
                <p>Railway</p>
            </div>
            <div class="info-card">
                <h3>Region</h3>
                <p>US East</p>
            </div>
        </div>

        <div class="endpoints">
            <h2 style="margin-bottom: 15px; color: #374151;">API Endpoints</h2>

            <div class="endpoint">
                <span class="endpoint-path">GET /</span>
                <span class="endpoint-status status-ok">✓ Active</span>
            </div>

            <div class="endpoint">
                <span class="endpoint-path">GET /api/health</span>
                <span class="endpoint-status status-ok">✓ Active</span>
            </div>

            <div class="endpoint">
                <span class="endpoint-path">GET /api/console/info</span>
                <span class="endpoint-status status-ok">✓ Active</span>
            </div>
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <button class="test-button" onclick="testEndpoints()">Test All Endpoints</button>
        </div>

        <div id="test-results"></div>

        <div class="footer">
            <p><strong>TORQ CONSOLE</strong> - AI Pair Programming Interface</p>
            <p style="margin-top: 10px;">Deployed with Railway • FastAPI + Python 3.11</p>
        </div>
    </div>

    <script>
        async function testEndpoints() {
            const resultsDiv = document.getElementById('test-results');
            resultsDiv.innerHTML = '<p style="color: #667eea;">Testing endpoints...</p>';
            resultsDiv.classList.add('test-results-show');

            const endpoints = ['/', '/api/health', '/api/console/info'];
            let results = '<h3 style="margin-bottom: 10px; color: #374151;">Test Results:</h3>';

            for (const endpoint of endpoints) {
                try {
                    const response = await fetch(endpoint);
                    const data = await response.json();
                    results += `
                        <div style="margin: 10px 0; padding: 10px; background: white; border-radius: 6px; border-left: 3px solid #10b981;">
                            <strong style="color: #10b981;">✓ ${endpoint}</strong><br>
                            <pre style="margin-top: 8px; font-size: 0.85em; color: #6b7280; overflow-x: auto;">${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                } catch (error) {
                    results += `
                        <div style="margin: 10px 0; padding: 10px; background: white; border-radius: 6px; border-left: 3px solid #ef4444;">
                            <strong style="color: #ef4444;">✗ ${endpoint}</strong><br>
                            <span style="color: #6b7280; font-size: 0.85em;">${error.message}</span>
                        </div>
                    `;
                }
            }

            resultsDiv.innerHTML = results;
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - Returns HTML dashboard"""
    return HTML_DASHBOARD

@app.get("/api")
async def api_root():
    """API root endpoint - Returns JSON"""
    return {
        "name": "TORQ CONSOLE Web UI",
        "version": "0.80.0",
        "status": "running",
        "mode": "standalone",
        "message": "TORQ Console Web UI is running on Railway!"
    }

@app.get("/api/health")
async def health():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "torq-console-web-ui"}

@app.get("/api/console/info")
async def console_info():
    """Console information endpoint"""
    return {
        "title": "TORQ CONSOLE",
        "version": "0.80.0",
        "mode": "standalone",
        "features": [
            "FastAPI Web Server",
            "REST API",
            "Railway Deployment"
        ]
    }
