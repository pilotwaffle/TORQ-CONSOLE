# TORQ Console: Drift/Regression Monitor System

Complete implementation of drift and regression detection for TORQ Console based on `learning_events` data.

## Files Created

### 1. SQL Schema: `E:\TORQ-CONSOLE\sql\monitoring_schema.sql`

Complete database schema for monitoring system:

**Tables:**
- `monitoring_metrics` - Daily/hourly aggregated metrics from learning_events
- `monitoring_alerts` - Alert history with thresholds and lifecycle
- `monitoring_baseline` - Rolling baseline values for comparison

**Materialized View:**
- `mv_daily_metrics` - Pre-computed daily aggregations for fast queries

**PostgreSQL Functions:**
- `compute_hourly_metrics(p_target_date, p_target_hour)` - Compute hourly aggregations
- `compute_daily_metrics(p_target_date)` - Compute full day metrics
- `update_baseline(p_baseline_name, p_window_days)` - Update rolling baseline
- `check_drift_and_alert(...)` - Run drift detection and create alerts
- `refresh_daily_metrics_mv()` - Refresh materialized view

**Views:**
- `v_monitoring_current_status` - Current status vs baseline
- `v_monitoring_alert_summary` - Alert summary by type/severity

### 2. Python Module: `E:\TORQ-CONSOLE\monitoring.py`

Client-side monitoring logic:

**Classes:**
- `ThresholdConfig` - Configurable alert thresholds (low/medium/high)
- `MetricSnapshot` - Current metrics data structure
- `BaselineSnapshot` - Baseline metrics data structure
- `Alert` - Alert data structure with context
- `DriftDetector` - Main drift detection engine
- `MonitoringSummary` - Dashboard summary generator

**Usage:**
```python
from monitoring import create_detector, create_summary

detector = create_detector(supabase_url, supabase_key)
result = await detector.check_and_alert(date="2026-02-21", auto_save=True)

summary = create_summary(supabase_url, supabase_key)
status = await summary.get_summary(window_days=7)
```

### 3. Updated: `E:\TORQ-CONSOLE\railway_app.py`

Added monitoring endpoints to Railway backend:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/monitor/summary` | GET | Get monitoring summary with trends and alerts |
| `/api/monitor/alerts` | GET | Get alerts filtered by threshold/status |
| `/api/monitor/compute` | POST | Trigger manual metric computation |
| `/api/monitor/baseline` | GET | Get current baseline values |
| `/api/monitor/metrics/daily` | GET | Get daily metrics for date range |
| `/api/monitor/alerts/{id}/acknowledge` | POST | Acknowledge an alert |
| `/api/monitor/alerts/{id}/resolve` | POST | Resolve an alert |

## Metrics Tracked

### Reliability Signals
- **Fallback Rate**: `fallback_events / total_events`
- **Error Rate**: `failed_events / total_events`
- **Duplicate Rate**: `duplicate_events / total_events`

### Performance Signals
- **Latency Percentiles**: p50, p75, p90, p95, p99
- **Latency Stats**: avg, min, max

### Behavior Signals
- **Model Distribution**: JSON map of model usage counts
- **Backend Distribution**: Railway vs Vercel breakdown
- **Agent Distribution**: Prince Flowers usage
- **Top Fallback Reasons**: Ranked list

### Health Score
Composite score (0-100):
```
health = (success_rate * 50) +
         (1 - min(1, fallback_rate * 5)) * 30 +
         (1 - min(1, duplicate_rate * 3)) * 20
```

## Alert Logic

### Thresholds (configurable)
| Severity | Deviation Ratio |
|----------|-----------------|
| LOW | >= 1.5x baseline |
| MEDIUM | >= 2.0x baseline |
| HIGH | >= 3.0x baseline |
| CRITICAL | >= 3.0x baseline |

### Alert Types
1. **fallback_spike** - Fallback rate exceeds baseline
2. **error_spike** - Error rate exceeds baseline
3. **latency_spike** - p95 latency exceeds baseline
4. **duplicate_spike** - Duplicate/retry rate exceeds baseline
5. **health_decline** - Health score drops below 50

## Deployment Steps

### 1. Run SQL Schema in Supabase
```bash
# Copy and paste contents into Supabase SQL Editor
cat E:/TORQ-CONSOLE/sql/monitoring_schema.sql
```

### 2. Deploy Updated Railway App
```bash
# The railway_app.py is already updated
# Railway will auto-deploy on git push
git add E:/TORQ-CONSOLE/railway_app.py
git commit -m "Add drift/regression monitoring endpoints"
git push
```

### 3. Optional: Set up pg_cron for Automatic Refresh
```sql
-- Enable pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Hourly metric computation (every hour at :00)
SELECT cron.schedule(
    'compute-hourly-metrics',
    '0 * * * *',
    $$SELECT compute_hourly_metrics(CURRENT_DATE, EXTRACT(HOUR FROM NOW() - INTERVAL '1 hour')::INTEGER)$$
);

-- Daily baseline update (2 AM UTC)
SELECT cron.schedule(
    'update-daily-baseline',
    '0 2 * * *',
    $$SELECT update_baseline(); REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_metrics;$$
);
```

## API Usage Examples

### Get Monitoring Summary
```bash
curl "https://your-railway-app.railway.app/api/monitor/summary?window=7d"
```

Response:
```json
{
  "window": {"start_date": "2026-02-14", "end_date": "2026-02-21", "days": 7},
  "metrics": {
    "total_events": 12345,
    "avg_fallback_rate": 0.0450,
    "avg_error_rate": 0.0080,
    "avg_health_score": 87.5
  },
  "baseline": {
    "fallback_rate": 0.0400,
    "error_rate": 0.0100,
    "latency_p95": 2500
  },
  "trends": {"fallback_rate": "up", "latency_p95": "stable"},
  "alerts": {"total_open": 2, "by_severity": {"medium": 2}}
}
```

### Get Alerts
```bash
curl "https://your-railway-app.railway.app/api/monitor/alerts?threshold=medium&status=open"
```

### Trigger Manual Computation
```bash
curl -X POST "https://your-railway-app.railway.app/api/monitor/compute" \
  -H "Content-Type: application/json" \
  -d '{"update_baseline": true}'
```

## Sample Aggregation Queries

### Fallback Rate by Model
```sql
SELECT
    event_data->>'model' AS model,
    COUNT(*) FILTER (
        WHERE event_data->'telemetry'->'request_chain'->0->>'fallback_reason' IS NOT NULL
    )::FLOAT / COUNT(*) AS fallback_rate
FROM learning_events
WHERE occurred_at >= NOW() - INTERVAL '7 days'
GROUP BY event_data->>'model'
ORDER BY fallback_rate DESC;
```

### Latency Percentiles
```sql
SELECT
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY (event_data->>'duration_ms')::INT) AS p50,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY (event_data->>'duration_ms')::INT) AS p95,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY (event_data->>'duration_ms')::INT) AS p99
FROM learning_events
WHERE occurred_at >= NOW() - INTERVAL '24 hours'
AND event_data->>'duration_ms' IS NOT NULL;
```

### Top Fallback Reasons
```sql
SELECT
    event_data->'telemetry'->'request_chain'->0->>'fallback_reason' AS reason,
    COUNT(*) AS count
FROM learning_events
WHERE event_data->'telemetry'->'request_chain'->0->>'fallback_reason' IS NOT NULL
AND occurred_at >= NOW() - INTERVAL '7 days'
GROUP BY reason
ORDER BY count DESC
LIMIT 10;
```

## Key Design Decisions

1. **Materialized View for Daily Metrics**: Pre-aggregates data for fast dashboard queries without scanning raw events

2. **Separate Baseline Table**: Stores rolling averages for fair comparison; automatically refreshed

3. **Threshold Configuration**: Default thresholds (1.5x/2x/3x) are configurable per deployment

4. **Alert Lifecycle**: Alerts progress through states (open -> acknowledged -> resolved)

5. **Idempotent Computation**: Can safely recompute metrics for past dates without duplicates

6. **Supabase Native**: Uses Supabase PostgreSQL features (RLS, pg_cron, materialized views)

## Related Files

- `E:\TORQ-CONSOLE\sql\monitoring_schema.sql` - Database schema
- `E:\TORQ-CONSOLE\monitoring.py` - Python monitoring module
- `E:\TORQ-CONSOLE\railway_app.py` - FastAPI endpoints (updated)
- `E:\TORQ-CONSOLE\supabase\migrations\02_learning_tables.sql` - Source learning_events schema
