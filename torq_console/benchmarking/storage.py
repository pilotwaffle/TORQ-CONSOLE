"""
Benchmark Result Storage and Tracking

Handles storage, retrieval, and analysis of benchmark results over time.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager

import numpy as np
from pydantic import BaseModel, Field


class BenchmarkMetric(BaseModel):
    """Individual metric measurement from a benchmark run."""

    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BenchmarkIteration(BaseModel):
    """Single benchmark iteration result."""

    iteration_id: str
    category: str
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    success: bool
    error: Optional[str] = None

    # Performance metrics
    ttfuo_ms: Optional[float] = None  # Time to First Useful Output
    e2e_ms: float = 0.0               # End-to-End execution time
    response_ms: Optional[float] = None

    # Resource metrics
    memory_peak_mb: Optional[float] = None
    cpu_percent: Optional[float] = None

    # LLM-specific metrics
    tokens_generated: Optional[int] = None
    tokens_per_sec: Optional[float] = None
    cost_estimate: Optional[float] = None

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BenchmarkResult(BaseModel):
    """Complete benchmark result for a test suite."""

    run_id: str
    category: str
    test_name: str
    environment: str
    timestamp: datetime

    # Test configuration
    config: Dict[str, Any] = Field(default_factory=dict)

    # Iteration results
    iterations: List[BenchmarkIteration] = Field(default_factory=list)

    # Aggregated statistics
    total_iterations: int = 0
    successful_iterations: int = 0
    success_rate: float = 0.0

    # Performance percentiles (in ms)
    p50_duration: Optional[float] = None
    p90_duration: Optional[float] = None
    p95_duration: Optional[float] = None
    p99_duration: Optional[float] = None

    # Primary metric percentiles
    p50_primary: Optional[float] = None
    p90_primary: Optional[float] = None
    p95_primary: Optional[float] = None
    p99_primary: Optional[float] = None

    # Token and cost metrics
    total_tokens: Optional[int] = None
    avg_tokens_per_sec: Optional[float] = None
    total_cost: Optional[float] = None
    cost_per_success: Optional[float] = None

    # SLO compliance
    slo_met: bool = True
    slo_degradation_level: str = "ok"

    # System info
    system_info: Dict[str, Any] = Field(default_factory=dict)

    def calculate_statistics(self) -> None:
        """Calculate aggregated statistics from iterations."""
        if not self.iterations:
            return

        self.total_iterations = len(self.iterations)
        self.successful_iterations = sum(1 for it in self.iterations if it.success)
        self.success_rate = self.successful_iterations / self.total_iterations

        # Calculate duration percentiles
        durations = [it.duration_ms for it in self.iterations if it.success]
        if durations:
            percentiles = [50, 90, 95, 99]
            values = np.percentile(durations, percentiles)
            self.p50_duration, self.p90_duration, self.p95_duration, self.p99_duration = values

        # Calculate primary metric percentiles (TTFUO or E2E)
        primary_metrics = []
        for it in self.iterations:
            if it.success:
                if it.ttfuo_ms is not None:
                    primary_metrics.append(it.ttfuo_ms)
                else:
                    primary_metrics.append(it.e2e_ms)

        if primary_metrics:
            percentiles = [50, 90, 95, 99]
            values = np.percentile(primary_metrics, percentiles)
            self.p50_primary, self.p90_primary, self.p95_primary, self.p99_primary = values

        # Calculate token and cost metrics
        tokens = [it.tokens_generated for it in self.iterations if it.success and it.tokens_generated is not None]
        if tokens:
            self.total_tokens = sum(tokens)
            total_duration = sum(it.e2e_ms for it in self.iterations if it.success) / 1000.0
            if total_duration > 0:
                self.avg_tokens_per_sec = self.total_tokens / total_duration

        costs = [it.cost_estimate for it in self.iterations if it.success and it.cost_estimate is not None]
        if costs:
            self.total_cost = sum(costs)
            if self.successful_iterations > 0:
                self.cost_per_success = self.total_cost / self.successful_iterations


class BenchmarkStorage:
    """Storage backend for benchmark results."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize benchmark storage.

        Args:
            storage_path: Path to storage directory. If None, uses default .torq/benchmarks
        """
        if storage_path is None:
            storage_path = Path.cwd() / ".torq" / "benchmarks"

        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database
        self.db_path = self.storage_path / "benchmarks.db"
        self._init_database()

        # Initialize results directory for detailed JSON exports
        self.results_dir = self.storage_path / "results"
        self.results_dir.mkdir(exist_ok=True)

        # Initialize releases directory for per-release tracking
        self.releases_dir = self.storage_path / "releases"
        self.releases_dir.mkdir(exist_ok=True)

    def _init_database(self) -> None:
        """Initialize SQLite database schema."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS benchmark_runs (
                    run_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    config TEXT,
                    total_iterations INTEGER,
                    successful_iterations INTEGER,
                    success_rate REAL,
                    p95_duration REAL,
                    p95_primary REAL,
                    slo_met BOOLEAN,
                    slo_degradation_level TEXT,
                    total_tokens INTEGER,
                    avg_tokens_per_sec REAL,
                    total_cost REAL,
                    cost_per_success REAL,
                    system_info TEXT,
                    release_version TEXT,
                    INDEX(category, environment, timestamp),
                    INDEX(test_name, timestamp),
                    INDEX(release_version, timestamp)
                );

                CREATE TABLE IF NOT EXISTS benchmark_iterations (
                    iteration_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    duration_ms REAL,
                    success BOOLEAN,
                    error TEXT,
                    ttfuo_ms REAL,
                    e2e_ms REAL,
                    memory_peak_mb REAL,
                    tokens_generated INTEGER,
                    tokens_per_sec REAL,
                    cost_estimate REAL,
                    metadata TEXT,
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs(run_id)
                );

                CREATE TABLE IF NOT EXISTS slo_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    slo_target REAL,
                    degradation_level TEXT,
                    timestamp DATETIME NOT NULL,
                    release_version TEXT,
                    INDEX(category, environment, metric_name, timestamp)
                );
            """)

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def store_result(self, result: BenchmarkResult, release_version: Optional[str] = None) -> None:
        """Store a complete benchmark result."""
        # Store in SQLite database
        with self._get_connection() as conn:
            # Store run summary
            conn.execute("""
                INSERT OR REPLACE INTO benchmark_runs
                (run_id, category, test_name, environment, timestamp, config,
                 total_iterations, successful_iterations, success_rate,
                 p95_duration, p95_primary, slo_met, slo_degradation_level,
                 total_tokens, avg_tokens_per_sec, total_cost, cost_per_success,
                 system_info, release_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.run_id, result.category, result.test_name, result.environment,
                result.timestamp, json.dumps(result.config),
                result.total_iterations, result.successful_iterations, result.success_rate,
                result.p95_duration, result.p95_primary, result.slo_met, result.slo_degradation_level,
                result.total_tokens, result.avg_tokens_per_sec, result.total_cost, result.cost_per_success,
                json.dumps(result.system_info), release_version
            ))

            # Store iterations
            for iteration in result.iterations:
                conn.execute("""
                    INSERT OR REPLACE INTO benchmark_iterations
                    (iteration_id, run_id, start_time, end_time, duration_ms,
                     success, error, ttfuo_ms, e2e_ms, memory_peak_mb,
                     tokens_generated, tokens_per_sec, cost_estimate, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    iteration.iteration_id, result.run_id, iteration.start_time,
                    iteration.end_time, iteration.duration_ms, iteration.success,
                    iteration.error, iteration.ttfuo_ms, iteration.e2e_ms,
                    iteration.memory_peak_mb, iteration.tokens_generated,
                    iteration.tokens_per_sec, iteration.cost_estimate,
                    json.dumps(iteration.metadata)
                ))

        # Store detailed JSON result
        result_file = self.results_dir / f"{result.run_id}.json"
        result_file.write_text(result.json(indent=2), encoding='utf-8')

        # Store in release directory if version specified
        if release_version:
            release_dir = self.releases_dir / release_version
            release_dir.mkdir(exist_ok=True)
            release_result_file = release_dir / f"{result.run_id}.json"
            release_result_file.write_text(result.json(indent=2), encoding='utf-8')

    def get_result(self, run_id: str) -> Optional[BenchmarkResult]:
        """Retrieve a specific benchmark result."""
        # Try detailed JSON file first
        result_file = self.results_dir / f"{run_id}.json"
        if result_file.exists():
            return BenchmarkResult.parse_raw(result_file.read_text(encoding='utf-8'))

        # Fallback to database
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM benchmark_runs WHERE run_id = ?",
                (run_id,)
            ).fetchone()

            if row is None:
                return None

            # Load iterations
            iterations = []
            iter_rows = conn.execute(
                "SELECT * FROM benchmark_iterations WHERE run_id = ?",
                (run_id,)
            ).fetchall()

            for iter_row in iter_rows:
                iteration = BenchmarkIteration(
                    iteration_id=iter_row['iteration_id'],
                    category=row['category'],
                    test_name=row['test_name'],
                    start_time=datetime.fromisoformat(iter_row['start_time']),
                    end_time=datetime.fromisoformat(iter_row['end_time']),
                    duration_ms=iter_row['duration_ms'],
                    success=bool(iter_row['success']),
                    error=iter_row['error'],
                    ttfuo_ms=iter_row['ttpuo_ms'],
                    e2e_ms=iter_row['e2e_ms'],
                    memory_peak_mb=iter_row['memory_peak_mb'],
                    tokens_generated=iter_row['tokens_generated'],
                    tokens_per_sec=iter_row['tokens_per_sec'],
                    cost_estimate=iter_row['cost_estimate'],
                    metadata=json.loads(iter_row['metadata']) if iter_row['metadata'] else {}
                )
                iterations.append(iteration)

            return BenchmarkResult(
                run_id=row['run_id'],
                category=row['category'],
                test_name=row['test_name'],
                environment=row['environment'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                config=json.loads(row['config']) if row['config'] else {},
                iterations=iterations,
                total_iterations=row['total_iterations'],
                successful_iterations=row['successful_iterations'],
                success_rate=row['success_rate'],
                p95_duration=row['p95_duration'],
                p95_primary=row['p95_primary'],
                slo_met=bool(row['slo_met']),
                slo_degradation_level=row['slo_degradation_level'],
                total_tokens=row['total_tokens'],
                avg_tokens_per_sec=row['avg_tokens_per_sec'],
                total_cost=row['total_cost'],
                cost_per_success=row['cost_per_success'],
                system_info=json.loads(row['system_info']) if row['system_info'] else {}
            )

    def list_results(self, category: Optional[str] = None,
                    environment: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """List benchmark results with optional filtering."""
        with self._get_connection() as conn:
            query = "SELECT * FROM benchmark_runs WHERE 1=1"
            params = []

            if category:
                query += " AND category = ?"
                params.append(category)

            if environment:
                query += " AND environment = ?"
                params.append(environment)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            return [dict(row) for row in rows]

    def get_trend_data(self, category: str, metric_name: str,
                      days: int = 30, environment: str = "production") -> List[Dict[str, Any]]:
        """Get trend data for a specific category and metric."""
        start_date = datetime.now() - timedelta(days=days)

        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT timestamp, metric_value, slo_target, degradation_level, release_version
                FROM slo_trends
                WHERE category = ? AND environment = ? AND metric_name = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (category, environment, metric_name, start_date.isoformat())).fetchall()

            return [dict(row) for row in rows]

    def detect_regressions(self, category: str, environment: str = "production",
                          window_days: int = 7) -> List[Dict[str, Any]]:
        """Detect performance regressions in recent benchmark runs."""
        start_date = datetime.now() - timedelta(days=window_days)

        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT metric_name, AVG(metric_value) as avg_value, COUNT(*) as sample_count,
                       slo_target, degradation_level
                FROM slo_trends
                WHERE category = ? AND environment = ? AND timestamp >= ?
                  AND sample_count >= 5
                GROUP BY metric_name
                HAVING degradation_level IN ('warning', 'critical')
                ORDER BY degradation_level DESC, avg_value DESC
            """, (category, environment, start_date.isoformat())).fetchall()

            return [dict(row) for row in rows]

    def get_release_summary(self, release_version: str) -> Dict[str, Any]:
        """Get performance summary for a specific release."""
        release_dir = self.releases_dir / release_version
        if not release_dir.exists():
            return {}

        # Load all results for this release
        results = []
        for result_file in release_dir.glob("*.json"):
            try:
                result = BenchmarkResult.parse_raw(result_file.read_text(encoding='utf-8'))
                results.append(result)
            except Exception as e:
                print(f"Warning: Failed to load {result_file}: {e}")

        if not results:
            return {}

        # Aggregate summary
        summary = {
            "release_version": release_version,
            "total_runs": len(results),
            "categories": {},
            "overall_success_rate": sum(r.success_rate for r in results) / len(results),
            "slo_compliance_rate": sum(1 for r in results if r.slo_met) / len(results),
            "avg_cost_per_success": sum(r.cost_per_success for r in results if r.cost_per_success) / len([r for r in results if r.cost_per_success]),
            "total_cost": sum(r.total_cost for r in results if r.total_cost),
            "date_range": {
                "start": min(r.timestamp for r in results).isoformat(),
                "end": max(r.timestamp for r in results).isoformat()
            }
        }

        # Category breakdown
        for result in results:
            if result.category not in summary["categories"]:
                summary["categories"][result.category] = {
                    "runs": 0,
                    "success_rate": 0.0,
                    "slo_compliance": 0,
                    "avg_p95_primary": 0.0,
                    "avg_cost_per_success": 0.0
                }

            cat_summary = summary["categories"][result.category]
            cat_summary["runs"] += 1
            cat_summary["success_rate"] += result.success_rate
            if result.slo_met:
                cat_summary["slo_compliance"] += 1
            if result.p95_primary:
                cat_summary["avg_p95_primary"] += result.p95_primary
            if result.cost_per_success:
                cat_summary["avg_cost_per_success"] += result.cost_per_success

        # Calculate category averages
        for cat_data in summary["categories"].values():
            runs = cat_data["runs"]
            cat_data["success_rate"] /= runs
            cat_data["slo_compliance"] /= runs
            cat_data["avg_p95_primary"] /= runs if cat_data["avg_p95_primary"] > 0 else 1
            cat_data["avg_cost_per_success"] /= runs if cat_data["avg_cost_per_success"] > 0 else 1

        return summary