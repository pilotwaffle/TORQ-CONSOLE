"""
Observability Dashboard for TORQ Console

Web dashboard for real-time system metrics and monitoring.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Template

from .collector import MetricsCollector
from .exporter import MetricsExporter


class Dashboard:
    """
    Web dashboard for TORQ Console observability.

    Provides:
    - Real-time metrics display
    - System health overview
    - Performance graphs
    - Component status
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """
        Initialize dashboard.

        Args:
            collector: Optional MetricsCollector instance (creates one if not provided)
        """
        self.collector = collector or MetricsCollector()
        self.exporter = MetricsExporter(self.collector)
        self.logger = logging.getLogger(__name__)

        # FastAPI app for dashboard
        self.app = FastAPI(
            title="TORQ Console Dashboard",
            description="Real-time observability and monitoring",
            version="1.0.0"
        )

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup dashboard routes."""
        self.app.add_api_route("/dashboard", self._dashboard_html)

        @self.app.get("/dashboard/api/metrics")
        async def get_metrics():
            """Get current metrics as JSON."""
            return JSONResponse(self.exporter.get_dashboard_data())

        @self.app.get("/dashboard/api/prometheus")
        async def get_prometheus():
            """Get metrics in Prometheus format."""
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                content=self.exporter.to_prometheus(),
                media_type="text/plain"
            )

    async def _dashboard_html(self) -> HTMLResponse:
        """Render the dashboard HTML."""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TORQ Console - Observability Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%%, #2a5298 100%%);
            color: #ffffff;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header {
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 40px;
        }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .header p { color: rgba(255,255,255,0.7); font-size: 1.1rem; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 24px;
            backdrop-filter: blur(10px);
        }
        .card h2 { font-size: 1.5rem; margin-bottom: 15px; color: #60a5fa; }
        .card .value { font-size: 2.5rem; font-weight: bold; margin: 10px 0; }
        .card .label { color: rgba(255,255,255,0.7); font-size: 0.9rem; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
        .metric { background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; }
        .metric-name { font-size: 0.85rem; color: rgba(255,255,255,0.7); }
        .metric-value { font-size: 1.5rem; font-weight: bold; }
        .uptime { text-align: center; }
        .status { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; }
        .status.online { background: #10b981; }
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TORQ Console</h1>
            <p>Observability Dashboard</p>
        </div>

        <div class="grid">
            <div class="card">
                <h2>System Status</h2>
                <div class="uptime">
                    <span class="status online">ONLINE</span>
                </div>
            </div>

            <div class="card">
                <h2>Uptime</h2>
                <div class="value" id="uptime">Loading...</div>
                <div class="label">seconds</div>
            </div>

            <div class="card">
                <h2>Total Metrics</h2>
                <div class="value" id="total-metrics">Loading...</div>
                <div class="label">collected</div>
            </div>

            <div class="card">
                <h2>Active Counters</h2>
                <div class="value" id="active-counters">Loading...</div>
                <div class="label">counters</div>
            </div>
        </div>

        <div class="card">
            <h2>Live Metrics</h2>
            <div class="metrics" id="metrics-container">
                <div class="loading">Loading metrics...</div>
            </div>
        </div>
    </div>

    <script>
        async function loadMetrics() {
            try {
                const response = await fetch('/dashboard/api/metrics');
                const data = await response.json();

                // Update uptime
                document.getElementById('uptime').textContent =
                    Math.floor(data.uptime_seconds).toLocaleString();

                // Update summary
                document.getElementById('total-metrics').textContent =
                    data.summary.total_metrics.toLocaleString();
                document.getElementById('active-counters').textContent =
                    data.summary.total_counters.toLocaleString();

                // Update metrics grid
                const container = document.getElementById('metrics-container');
                container.innerHTML = '';

                // Add counters
                data.counters.forEach(metric => {
                    const div = document.createElement('div');
                    div.className = 'metric';
                    div.innerHTML = `
                        <div class="metric-name">${metric.name}</div>
                        <div class="metric-value">${metric.value.toLocaleString()}</div>
                    `;
                    container.appendChild(div);
                });

                // Add gauges
                data.gauges.forEach(metric => {
                    const div = document.createElement('div');
                    div.className = 'metric';
                    div.innerHTML = `
                        <div class="metric-name">${metric.name}</div>
                        <div class="metric-value">${metric.value.toLocaleString()}</div>
                    `;
                    container.appendChild(div);
                });

            } catch (error) {
                console.error('Failed to load metrics:', error);
            }
        }

        // Load metrics immediately and every 5 seconds
        loadMetrics();
        setInterval(loadMetrics, 5000);
    </script>
</body>
</html>
        """
        return HTMLResponse(content=html)

    def get_app(self) -> FastAPI:
        """Get the FastAPI app for mounting."""
        return self.app

    def integrate_with_console(self, console) -> None:
        """
        Integrate dashboard with TORQ Console.

        Args:
            console: TorqConsole instance to integrate with
        """
        # Mount dashboard routes on console's web app
        if hasattr(console, 'web_ui') and hasattr(console.web_ui, 'app'):
            console.web_ui.app.mount("/dashboard", self.app, name="dashboard")
            self.logger.info("Dashboard integrated with TORQ Console web UI")
