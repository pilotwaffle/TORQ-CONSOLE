-- ============================================================================
-- TORQ Console: Drift/Regression Monitor System
-- ============================================================================
--
-- This schema creates a complete monitoring system for detecting drift and
-- regression in TORQ Console based on learning_events data.
--
-- Tables:
--   - monitoring_metrics: Daily/hourly aggregated metrics
--   - monitoring_alerts: Alert history with thresholds
--   - monitoring_baseline: Rolling baseline for comparison
--
-- Materialized Views:
--   - mv_daily_metrics: Pre-computed daily aggregations
--
-- Run in Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- 1. MONITORING METRICS TABLE
-- Stores aggregated metrics from learning_events
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.monitoring_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Time period
    metric_date DATE NOT NULL,
    metric_hour INTEGER, -- NULL for daily, 0-23 for hourly
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,

    -- Reliability metrics (0-1 scale)
    total_events INTEGER DEFAULT 0,
    successful_events INTEGER DEFAULT 0,
    failed_events INTEGER DEFAULT 0,
    fallback_events INTEGER DEFAULT 0,
    duplicate_events INTEGER DEFAULT 0,

    fallback_rate DECIMAL(5,4) DEFAULT 0, -- fallbacks / total
    error_rate DECIMAL(5,4) DEFAULT 0,     -- errors / total
    duplicate_rate DECIMAL(5,4) DEFAULT 0, -- duplicates / total

    -- Performance metrics (milliseconds)
    latency_p50 DECIMAL(10,2),
    latency_p75 DECIMAL(10,2),
    latency_p90 DECIMAL(10,2),
    latency_p95 DECIMAL(10,2),
    latency_p99 DECIMAL(10,2),
    latency_avg DECIMAL(10,2),
    latency_max DECIMAL(10,2),
    latency_min DECIMAL(10,2),

    -- Model distribution
    model_distribution JSONB DEFAULT '{}'::jsonb, -- {"claude-sonnet-4-6": 0.85, ...}

    -- Service version breakdown
    service_versions JSONB DEFAULT '{}'::jsonb, -- {"railway:1.0.8": 0.95, ...}

    -- Top fallback reasons
    fallback_reasons JSONB DEFAULT '[]'::jsonb, -- [{"reason": "timeout", "count": 10}, ...]

    -- Backend distribution
    backend_distribution JSONB DEFAULT '{}'::jsonb, -- {"railway": 0.8, "vercel": 0.2}

    -- Agent distribution
    agent_distribution JSONB DEFAULT '{}'::jsonb, -- {"prince_flowers": 1.0}

    -- Event type distribution
    event_type_distribution JSONB DEFAULT '{}'::jsonb,

    -- Health score (0-100 composite)
    health_score DECIMAL(5,2),

    -- Metadata
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_source TEXT DEFAULT 'learning_events',

    CONSTRAINT unique_metric_window UNIQUE (metric_date, metric_hour)
);

-- ============================================================================
-- 2. MONITORING ALERTS TABLE
-- Stores triggered alerts for drift/regression detection
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.monitoring_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Alert identification
    alert_type TEXT NOT NULL, -- fallback_spike, error_spike, latency_spike, duplicate_spike, model_drift
    severity TEXT NOT NULL, -- low, medium, high, critical

    -- Metric details
    metric_name TEXT NOT NULL, -- fallback_rate, error_rate, latency_p95, etc.
    current_value DECIMAL(15,6),
    baseline_value DECIMAL(15,6),
    deviation_ratio DECIMAL(10,4), -- current / baseline

    -- Threshold configuration
    threshold_low DECIMAL(5,4) DEFAULT 1.5,  -- Alert if deviation > 1.5x
    threshold_medium DECIMAL(5,4) DEFAULT 2.0, -- Alert if deviation > 2.0x
    threshold_high DECIMAL(5,4) DEFAULT 3.0,   -- Alert if deviation > 3.0x

    -- Context
    metric_date DATE NOT NULL,
    metric_hour INTEGER, -- NULL for daily-level alerts
    comparison_window_days INTEGER DEFAULT 7, -- Days used for baseline

    -- Dimensions affected
    affected_model TEXT,
    affected_backend TEXT,
    affected_agent TEXT,
    affected_version TEXT,

    -- Alert lifecycle
    status TEXT DEFAULT 'open', -- open, acknowledged, resolved, ignored
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT,
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,

    -- Notification
    notified BOOLEAN DEFAULT false,
    notified_at TIMESTAMPTZ,
    notification_channels TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Enriched data
    context_data JSONB DEFAULT '{}'::jsonb,
    related_events JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 3. MONITORING BASELINE TABLE
-- Stores rolling baseline values for comparison
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.monitoring_baseline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Baseline identification
    baseline_name TEXT NOT NULL UNIQUE, -- '7day_rolling', '30day_rolling'
    baseline_window_days INTEGER NOT NULL DEFAULT 7,

    -- Baseline values
    baseline_fallback_rate DECIMAL(5,4) DEFAULT 0,
    baseline_error_rate DECIMAL(5,4) DEFAULT 0,
    baseline_duplicate_rate DECIMAL(5,4) DEFAULT 0,
    baseline_latency_p50 DECIMAL(10,2),
    baseline_latency_p95 DECIMAL(10,2),
    baseline_latency_p99 DECIMAL(10,2),

    -- Model-specific baselines
    model_baselines JSONB DEFAULT '{}'::jsonb,

    -- Backend-specific baselines
    backend_baselines JSONB DEFAULT '{}'::jsonb,

    -- Computed from
    baseline_start_date DATE,
    baseline_end_date DATE,

    -- Timestamps
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ
);

-- ============================================================================
-- 4. INDEXES FOR PERFORMANCE
-- ============================================================================

-- Monitoring metrics indexes
CREATE INDEX IF NOT EXISTS idx_monitoring_metrics_date
    ON public.monitoring_metrics(metric_date DESC);

CREATE INDEX IF NOT EXISTS idx_monitoring_metrics_hourly
    ON public.monitoring_metrics(metric_date DESC, metric_hour)
    WHERE metric_hour IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_monitoring_metrics_computed
    ON public.monitoring_metrics(computed_at DESC);

-- Monitoring alerts indexes
CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_date
    ON public.monitoring_alerts(metric_date DESC);

CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_status
    ON public.monitoring_alerts(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_type_severity
    ON public.monitoring_alerts(alert_type, severity, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_open
    ON public.monitoring_alerts(status)
    WHERE status = 'open';

-- Monitoring baseline indexes
CREATE INDEX IF NOT EXISTS idx_monitoring_baseline_name
    ON public.monitoring_baseline(baseline_name);

-- ============================================================================
-- 5. MATERIALIZED VIEW: DAILY METRICS SUMMARY
-- Pre-computed daily aggregations for fast dashboard queries
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_daily_metrics AS
WITH daily_raw AS (
    SELECT
        DATE(occurred_at) AS metric_date,
        COUNT(*) AS total_events,
        COUNT(*) FILTER (
            WHERE event_data->>'reward' IS NOT NULL
            AND CAST(event_data->>'reward' AS FLOAT) > 0.5
        ) AS successful_events,
        COUNT(*) FILTER (
            WHERE event_data->>'reward' IS NOT NULL
            AND CAST(event_data->>'reward' AS FLOAT) <= 0.3
        ) AS failed_events,
        COUNT(*) FILTER (
            WHERE event_data->'telemetry'->'request_chain'->0->>'fallback_reason' IS NOT NULL
        ) AS fallback_events,
        COUNT(*) FILTER (duplicate_count > 1) AS duplicate_events,
        -- Latency extraction
        ARRAY_AGG(CAST(event_data->>'duration_ms' AS INTEGER)
            FILTER (WHERE event_data->>'duration_ms' IS NOT NULL)
        ) AS latencies,
        -- Model distribution
        ARRAY_AGG(event_data->>'model'
            FILTER (WHERE event_data->>'model' IS NOT NULL)
        ) AS models,
        -- Backend distribution
        ARRAY_AGG(event_data->>'backend'
            FILTER (WHERE event_data->>'backend' IS NOT NULL)
        ) AS backends,
        -- Agent distribution
        ARRAY_AGG(source_agent
            FILTER (WHERE source_agent IS NOT NULL)
        ) AS agents,
        -- Event types
        ARRAY_AGG(event_type
            FILTER (WHERE event_type IS NOT NULL)
        ) AS event_types,
        -- Fallback reasons
        ARRAY_AGG(event_data->'telemetry'->'request_chain'->0->>'fallback_reason'
            FILTER (WHERE event_data->'telemetry'->'request_chain'->0->>'fallback_reason' IS NOT NULL)
        ) AS fallback_reasons,
        MIN(occurred_at) AS window_start,
        MAX(occurred_at) AS window_end
    FROM public.learning_events
    WHERE occurred_at >= NOW() - INTERVAL '90 days'
    GROUP BY DATE(occurred_at)
),
percentile_calc AS (
    SELECT
        metric_date,
        total_events,
        successful_events,
        failed_events,
        fallback_events,
        duplicate_events,
        window_start,
        window_end,
        -- Calculate percentiles from latencies array
        percentile_cont(0.5) WITHIN GROUP (ORDER BY unnest latencies) AS latency_p50,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY unnest latencies) AS latency_p75,
        percentile_cont(0.90) WITHIN GROUP (ORDER BY unnest latencies) AS latency_p90,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY unnest latencies) AS latency_p95,
        percentile_cont(0.99) WITHIN GROUP (ORDER BY unnest latencies) AS latency_p99,
        avg(unnest(latencies)) AS latency_avg,
        max(unnest(latencies)) AS latency_max,
        min(unnest(latencies)) AS latency_min
    FROM daily_raw
)
SELECT
    metric_date,
    total_events,
    successful_events,
    failed_events,
    fallback_events,
    duplicate_events,
    -- Rates
    ROUND(CAST(fallback_events AS NUMERIC) / NULLIF(total_events, 0), 4) AS fallback_rate,
    ROUND(CAST(failed_events AS NUMERIC) / NULLIF(total_events, 0), 4) AS error_rate,
    ROUND(CAST(duplicate_events AS NUMERIC) / NULLIF(total_events, 0), 4) AS duplicate_rate,
    -- Latencies
    ROUND(latency_p50::NUMERIC, 2) AS latency_p50,
    ROUND(latency_p75::NUMERIC, 2) AS latency_p75,
    ROUND(latency_p90::NUMERIC, 2) AS latency_p90,
    ROUND(latency_p95::NUMERIC, 2) AS latency_p95,
    ROUND(latency_p99::NUMERIC, 2) AS latency_p99,
    ROUND(latency_avg::NUMERIC, 2) AS latency_avg,
    ROUND(latency_max::NUMERIC, 2) AS latency_max,
    ROUND(latency_min::NUMERIC, 2) AS latency_min,
    -- Simple health score (0-100)
    LEAST(100, GREATEST(0,
        ROUND(
            (CAST(successful_events AS NUMERIC) / NULLIF(total_events, 0) * 50) +
            (1 - LEAST(1, CAST(fallback_events AS NUMERIC) / NULLIF(total_events, 0) * 5)) * 30 +
            (1 - LEAST(1, CAST(duplicate_events AS NUMERIC) / NULLIF(total_events, 0) * 3)) * 20
        , 2)
    )) AS health_score,
    window_start,
    window_end
FROM percentile_calc;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_metrics_date
    ON public.mv_daily_metrics(metric_date);

-- ============================================================================
-- 6. AGGREGATION FUNCTIONS
-- ============================================================================

-- Function: Compute hourly metrics from learning_events
CREATE OR REPLACE FUNCTION public.compute_hourly_metrics(
    p_target_date DATE DEFAULT CURRENT_DATE,
    p_target_hour INTEGER DEFAULT NULL
)
RETURNS TABLE (
    rows_computed INTEGER,
    metrics_inserted INTEGER,
    computation_time_ms DECIMAL
) AS $$
DECLARE
    v_start_time TIMESTAMPTZ := clock_timestamp();
    v_rows_computed INTEGER := 0;
    v_metrics_inserted INTEGER := 0;
    v_window_start TIMESTAMPTZ;
    v_window_end TIMESTAMPTZ;
BEGIN
    -- Set time window
    IF p_target_hour IS NOT NULL THEN
        v_window_start := make_timestamp(
            EXTRACT(YEAR FROM p_target_date)::INTEGER,
            EXTRACT(MONTH FROM p_target_date)::INTEGER,
            EXTRACT(DAY FROM p_target_date)::INTEGER,
            p_target_hour, 0, 0
        ) AT TIME ZONE 'UTC';
        v_window_end := v_window_start + INTERVAL '1 hour';
    ELSE
        -- Compute all hours for the date
        FOR p_target_hour IN 0..23 LOOP
            -- Recursively call for each hour
            FOR result IN SELECT * FROM public.compute_hourly_metrics(p_target_date, p_target_hour) LOOP
                v_rows_computed := v_rows_computed + result.rows_computed;
                v_metrics_inserted := v_metrics_inserted + result.metrics_inserted;
            END LOOP;
        END LOOP;

        RETURN QUERY SELECT v_rows_computed, v_metrics_inserted,
            EXTRACT(EPOCH FROM (clock_timestamp() - v_start_time)) * 1000;
        RETURN;
    END IF;

    -- Compute metrics for the hour
    WITH hourly_data AS (
        SELECT
            COUNT(*) AS total_events,
            COUNT(*) FILTER (
                WHERE event_data->>'reward' IS NOT NULL
                AND CAST(event_data->>'reward' AS FLOAT) > 0.5
            ) AS successful_events,
            COUNT(*) FILTER (
                WHERE event_data->>'reward' IS NOT NULL
                AND CAST(event_data->>'reward' AS FLOAT) <= 0.3
            ) AS failed_events,
            COUNT(*) FILTER (
                WHERE event_data->'telemetry'->'request_chain'->0->>'fallback_reason' IS NOT NULL
            ) AS fallback_events,
            COUNT(*) FILTER (duplicate_count > 1) AS duplicate_events,
            -- Percentile aggregations
            percentile_cont(0.5) WITHIN GROUP (
                ORDER BY CAST(event_data->>'duration_ms' AS NUMERIC)
            ) AS latency_p50,
            percentile_cont(0.95) WITHIN GROUP (
                ORDER BY CAST(event_data->>'duration_ms' AS NUMERIC)
            ) AS latency_p95,
            percentile_cont(0.99) WITHIN GROUP (
                ORDER BY CAST(event_data->>'duration_ms' AS NUMERIC)
            ) AS latency_p99,
            AVG(CAST(event_data->>'duration_ms' AS NUMERIC)) AS latency_avg,
            MAX(CAST(event_data->>'duration_ms' AS NUMERIC)) AS latency_max,
            MIN(CAST(event_data->>'duration_ms' AS NUMERIC)) AS latency_min,
            -- Model distribution
            jsonb_object_agg(
                event_data->>'model',
                COUNT(*)
            ) FILTER (WHERE event_data->>'model' IS NOT NULL) AS model_dist,
            -- Backend distribution
            jsonb_object_agg(
                event_data->>'backend',
                COUNT(*)
            ) FILTER (WHERE event_data->>'backend' IS NOT NULL) AS backend_dist,
            -- Agent distribution
            jsonb_object_agg(
                source_agent,
                COUNT(*)
            ) FILTER (WHERE source_agent IS NOT NULL) AS agent_dist,
            -- Top fallback reasons
            jsonb_agg(
                jsonb_build_object(
                    'reason', event_data->'telemetry'->'request_chain'->0->>'fallback_reason',
                    'count', COUNT(*)
                )
            ) FILTER (
                WHERE event_data->'telemetry'->'request_chain'->0->>'fallback_reason' IS NOT NULL
            ) AS fallback_reasons
        FROM public.learning_events
        WHERE occurred_at >= v_window_start
        AND occurred_at < v_window_end
    )
    INSERT INTO public.monitoring_metrics (
        metric_date, metric_hour,
        window_start, window_end,
        total_events, successful_events, failed_events,
        fallback_events, duplicate_events,
        fallback_rate, error_rate, duplicate_rate,
        latency_p50, latency_p95, latency_p99,
        latency_avg, latency_max, latency_min,
        model_distribution, backend_distribution, agent_distribution,
        fallback_reasons,
        health_score,
        computed_at
    )
    SELECT
        p_target_date,
        p_target_hour,
        v_window_start,
        v_window_end,
        COALESCE(total_events, 0),
        COALESCE(successful_events, 0),
        COALESCE(failed_events, 0),
        COALESCE(fallback_events, 0),
        COALESCE(duplicate_events, 0),
        CASE WHEN total_events > 0
            THEN ROUND(CAST(fallback_events AS NUMERIC) / total_events, 4)
            ELSE 0 END,
        CASE WHEN total_events > 0
            THEN ROUND(CAST(failed_events AS NUMERIC) / total_events, 4)
            ELSE 0 END,
        CASE WHEN total_events > 0
            THEN ROUND(CAST(duplicate_events AS NUMERIC) / total_events, 4)
            ELSE 0 END,
        ROUND(latency_p50::NUMERIC, 2),
        ROUND(latency_p95::NUMERIC, 2),
        ROUND(latency_p99::NUMERIC, 2),
        ROUND(latency_avg::NUMERIC, 2),
        ROUND(latency_max::NUMERIC, 2),
        ROUND(latency_min::NUMERIC, 2),
        COALESCE(model_dist, '{}'::jsonb),
        COALESCE(backend_dist, '{}'::jsonb),
        COALESCE(agent_dist, '{}'::jsonb),
        COALESCE(fallback_reasons, '[]'::jsonb),
        LEAST(100, GREATEST(0, ROUND(
            CASE WHEN total_events > 0 THEN
                (CAST(successful_events AS NUMERIC) / total_events * 50) +
                (1 - LEAST(1, CAST(fallback_events AS NUMERIC) / total_events * 5)) * 30 +
                (1 - LEAST(1, CAST(duplicate_events AS NUMERIC) / total_events * 3)) * 20
            ELSE 50 END, 2))),
        clock_timestamp()
    FROM hourly_data
    ON CONFLICT (metric_date, metric_hour)
    DO UPDATE SET
        total_events = EXCLUDED.total_events,
        successful_events = EXCLUDED.successful_events,
        failed_events = EXCLUDED.failed_events,
        fallback_events = EXCLUDED.fallback_events,
        duplicate_events = EXCLUDED.duplicate_events,
        fallback_rate = EXCLUDED.fallback_rate,
        error_rate = EXCLUDED.error_rate,
        duplicate_rate = EXCLUDED.duplicate_rate,
        latency_p50 = EXCLUDED.latency_p50,
        latency_p95 = EXCLUDED.latency_p95,
        latency_p99 = EXCLUDED.latency_p99,
        latency_avg = EXCLUDED.latency_avg,
        latency_max = EXCLUDED.latency_max,
        latency_min = EXCLUDED.latency_min,
        model_distribution = EXCLUDED.model_distribution,
        backend_distribution = EXCLUDED.backend_distribution,
        agent_distribution = EXCLUDED.agent_distribution,
        fallback_reasons = EXCLUDED.fallback_reasons,
        health_score = EXCLUDED.health_score,
        computed_at = EXCLUDED.computed_at;

    GET DIAGNOSTICS v_metrics_inserted = ROW_COUNT;
    v_rows_computed := 1;

    RETURN QUERY SELECT v_rows_computed, v_metrics_inserted,
        EXTRACT(EPOCH FROM (clock_timestamp() - v_start_time)) * 1000;
END;
$$ LANGUAGE plpgsql;

-- Function: Compute daily metrics (calls hourly for all hours)
CREATE OR REPLACE FUNCTION public.compute_daily_metrics(
    p_target_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    rows_computed INTEGER,
    metrics_inserted INTEGER,
    computation_time_ms DECIMAL
) AS $$
BEGIN
    RETURN QUERY SELECT * FROM public.compute_hourly_metrics(p_target_date, NULL);
END;
$$ LANGUAGE plpgsql;

-- Function: Update baseline from recent metrics
CREATE OR REPLACE FUNCTION public.update_baseline(
    p_baseline_name TEXT DEFAULT '7day_rolling',
    p_window_days INTEGER DEFAULT 7
)
RETURNS monitoring_baseline AS $$
DECLARE
    v_result monitoring_baseline;
    v_baseline_start DATE := CURRENT_DATE - p_window_days;
    v_baseline_end DATE := CURRENT_DATE - INTERVAL '1 day'::DATE;
BEGIN
    INSERT INTO public.monitoring_baseline (
        baseline_name,
        baseline_window_days,
        baseline_fallback_rate,
        baseline_error_rate,
        baseline_duplicate_rate,
        baseline_latency_p50,
        baseline_latency_p95,
        baseline_latency_p99,
        baseline_start_date,
        baseline_end_date,
        computed_at,
        valid_until
    )
    SELECT
        p_baseline_name,
        p_window_days,
        -- Average rates over baseline period
        ROUND(AVG(fallback_rate)::NUMERIC, 4) AS baseline_fallback_rate,
        ROUND(AVG(error_rate)::NUMERIC, 4) AS baseline_error_rate,
        ROUND(AVG(duplicate_rate)::NUMERIC, 4) AS baseline_duplicate_rate,
        ROUND(AVG(latency_p50)::NUMERIC, 2) AS baseline_latency_p50,
        ROUND(AVG(latency_p95)::NUMERIC, 2) AS baseline_latency_p95,
        ROUND(AVG(latency_p99)::NUMERIC, 2) AS baseline_latency_p99,
        v_baseline_start,
        v_baseline_end,
        clock_timestamp(),
        clock_timestamp() + INTERVAL '1 day'
    FROM public.monitoring_metrics
    WHERE metric_date >= v_baseline_start
    AND metric_date <= v_baseline_end
    AND metric_hour IS NULL  -- Daily metrics only
    ON CONFLICT (baseline_name)
    DO UPDATE SET
        baseline_fallback_rate = EXCLUDED.baseline_fallback_rate,
        baseline_error_rate = EXCLUDED.baseline_error_rate,
        baseline_duplicate_rate = EXCLUDED.baseline_duplicate_rate,
        baseline_latency_p50 = EXCLUDED.baseline_latency_p50,
        baseline_latency_p95 = EXCLUDED.baseline_latency_p95,
        baseline_latency_p99 = EXCLUDED.baseline_latency_p99,
        baseline_start_date = EXCLUDED.baseline_start_date,
        baseline_end_date = EXCLUDED.baseline_end_date,
        computed_at = EXCLUDED.computed_at,
        valid_until = EXCLUDED.valid_until
    RETURNING * INTO v_result;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Function: Check for drift and create alerts
CREATE OR REPLACE FUNCTION public.check_drift_and_alert(
    p_baseline_name TEXT DEFAULT '7day_rolling',
    p_threshold_low DECIMAL DEFAULT 1.5,
    p_threshold_medium DECIMAL DEFAULT 2.0,
    p_threshold_high DECIMAL DEFAULT 3.0
)
RETURNS TABLE (
    alerts_created INTEGER,
    alert_ids UUID[]
) AS $$
DECLARE
    v_alert_count INTEGER := 0;
    v_alert_ids UUID[] := ARRAY[]::UUID[];
    v_baseline RECORD;
    v_current RECORD;
    v_new_alert_id UUID;
BEGIN
    -- Get baseline
    SELECT * INTO v_baseline
    FROM public.monitoring_baseline
    WHERE baseline_name = p_baseline_name
    AND valid_until > NOW();

    IF NOT FOUND THEN
        -- Baseline not found or expired, compute fresh
        SELECT * INTO v_baseline
        FROM public.update_baseline(p_baseline_name);
    END IF;

    -- Get current metrics (today)
    SELECT * INTO v_current
    FROM public.mv_daily_metrics
    WHERE metric_date = CURRENT_DATE;

    IF NOT FOUND THEN
        RAISE NOTICE 'No metrics available for today';
        RETURN QUERY SELECT 0, ARRAY[]::UUID[];
        RETURN;
    END IF;

    -- Check fallback rate drift
    IF v_baseline.baseline_fallback_rate > 0 THEN
        v_current.fallback_rate / v_baseline.baseline_fallback_rate INTO v_current;
    END IF;

    -- Fallback rate alert
    IF v_baseline.baseline_fallback_rate > 0 THEN
        IF v_current.fallback_rate / v_baseline.baseline_fallback_rate >= p_threshold_high THEN
            INSERT INTO public.monitoring_alerts (
                alert_type, severity, metric_name,
                current_value, baseline_value, deviation_ratio,
                threshold_low, threshold_medium, threshold_high,
                metric_date, comparison_window_days,
                status, context_data
            )
            VALUES (
                'fallback_spike', 'critical', 'fallback_rate',
                v_current.fallback_rate, v_baseline.baseline_fallback_rate,
                ROUND((v_current.fallback_rate / v_baseline.baseline_fallback_rate)::NUMERIC, 4),
                p_threshold_low, p_threshold_medium, p_threshold_high,
                CURRENT_DATE, 7,
                'open',
                jsonb_build_object(
                    'baseline_window', p_baseline_name,
                    'absolute_increase', ROUND((v_current.fallback_rate - v_baseline.baseline_fallback_rate)::NUMERIC, 4)
                )
            )
            RETURNING id INTO v_new_alert_id;
            v_alert_ids := array_append(v_alert_ids, v_new_alert_id);
            v_alert_count := v_alert_count + 1;

        ELSIF v_current.fallback_rate / v_baseline.baseline_fallback_rate >= p_threshold_medium THEN
            INSERT INTO public.monitoring_alerts (
                alert_type, severity, metric_name,
                current_value, baseline_value, deviation_ratio,
                threshold_low, threshold_medium, threshold_high,
                metric_date, comparison_window_days,
                status
            )
            VALUES (
                'fallback_spike', 'high', 'fallback_rate',
                v_current.fallback_rate, v_baseline.baseline_fallback_rate,
                ROUND((v_current.fallback_rate / v_baseline.baseline_fallback_rate)::NUMERIC, 4),
                p_threshold_low, p_threshold_medium, p_threshold_high,
                CURRENT_DATE, 7, 'open'
            )
            RETURNING id INTO v_new_alert_id;
            v_alert_ids := array_append(v_alert_ids, v_new_alert_id);
            v_alert_count := v_alert_count + 1;

        ELSIF v_current.fallback_rate / v_baseline.baseline_fallback_rate >= p_threshold_low THEN
            INSERT INTO public.monitoring_alerts (
                alert_type, severity, metric_name,
                current_value, baseline_value, deviation_ratio,
                threshold_low, threshold_medium, threshold_high,
                metric_date, comparison_window_days,
                status
            )
            VALUES (
                'fallback_spike', 'medium', 'fallback_rate',
                v_current.fallback_rate, v_baseline.baseline_fallback_rate,
                ROUND((v_current.fallback_rate / v_baseline.baseline_fallback_rate)::NUMERIC, 4),
                p_threshold_low, p_threshold_medium, p_threshold_high,
                CURRENT_DATE, 7, 'open'
            )
            RETURNING id INTO v_new_alert_id;
            v_alert_ids := array_append(v_alert_ids, v_new_alert_id);
            v_alert_count := v_alert_count + 1;
        END IF;
    END IF;

    -- Error rate alert
    IF v_baseline.baseline_error_rate > 0 THEN
        IF v_current.error_rate / v_baseline.baseline_error_rate >= p_threshold_medium THEN
            INSERT INTO public.monitoring_alerts (
                alert_type, severity, metric_name,
                current_value, baseline_value, deviation_ratio,
                threshold_low, threshold_medium, threshold_high,
                metric_date, comparison_window_days,
                status
            )
            VALUES (
                'error_spike', 'high', 'error_rate',
                v_current.error_rate, v_baseline.baseline_error_rate,
                ROUND((v_current.error_rate / v_baseline.baseline_error_rate)::NUMERIC, 4),
                p_threshold_low, p_threshold_medium, p_threshold_high,
                CURRENT_DATE, 7, 'open'
            )
            RETURNING id INTO v_new_alert_id;
            v_alert_ids := array_append(v_alert_ids, v_new_alert_id);
            v_alert_count := v_alert_count + 1;
        END IF;
    END IF;

    -- Latency alert (p95)
    IF v_baseline.baseline_latency_p95 > 0 THEN
        IF v_current.latency_p95 / v_baseline.baseline_latency_p95 >= p_threshold_medium THEN
            INSERT INTO public.monitoring_alerts (
                alert_type, severity, metric_name,
                current_value, baseline_value, deviation_ratio,
                threshold_low, threshold_medium, threshold_high,
                metric_date, comparison_window_days,
                status
            )
            VALUES (
                'latency_spike', 'high', 'latency_p95',
                v_current.latency_p95, v_baseline.baseline_latency_p95,
                ROUND((v_current.latency_p95 / v_baseline.baseline_latency_p95)::NUMERIC, 4),
                p_threshold_low, p_threshold_medium, p_threshold_high,
                CURRENT_DATE, 7, 'open'
            )
            RETURNING id INTO v_new_alert_id;
            v_alert_ids := array_append(v_alert_ids, v_new_alert_id);
            v_alert_count := v_alert_count + 1;
        END IF;
    END IF;

    -- Duplicate rate alert
    IF v_baseline.baseline_duplicate_rate > 0 THEN
        IF v_current.duplicate_rate / v_baseline.baseline_duplicate_rate >= p_threshold_medium THEN
            INSERT INTO public.monitoring_alerts (
                alert_type, severity, metric_name,
                current_value, baseline_value, deviation_ratio,
                threshold_low, threshold_medium, threshold_high,
                metric_date, comparison_window_days,
                status
            )
            VALUES (
                'duplicate_spike', 'medium', 'duplicate_rate',
                v_current.duplicate_rate, v_baseline.baseline_duplicate_rate,
                ROUND((v_current.duplicate_rate / v_baseline.baseline_duplicate_rate)::NUMERIC, 4),
                p_threshold_low, p_threshold_medium, p_threshold_high,
                CURRENT_DATE, 7, 'open'
            )
            RETURNING id INTO v_new_alert_id;
            v_alert_ids := array_append(v_alert_ids, v_new_alert_id);
            v_alert_count := v_alert_count + 1;
        END IF;
    END IF;

    RETURN QUERY SELECT v_alert_count, v_alert_ids;
END;
$$ LANGUAGE plpgsql;

-- Function: Refresh materialized view
CREATE OR REPLACE FUNCTION public.refresh_daily_metrics_mv()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_daily_metrics;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE public.monitoring_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.monitoring_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.monitoring_baseline ENABLE ROW LEVEL SECURITY;

-- Service role full access
CREATE POLICY "Service role full access monitoring_metrics"
    ON public.monitoring_metrics FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access monitoring_alerts"
    ON public.monitoring_alerts FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access monitoring_baseline"
    ON public.monitoring_baseline FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Authenticated read access
CREATE POLICY "Read access monitoring_metrics"
    ON public.monitoring_metrics FOR SELECT TO authenticated, anon USING (true);

CREATE POLICY "Read access monitoring_alerts"
    ON public.monitoring_alerts FOR SELECT TO authenticated, anon USING (true);

CREATE POLICY "Read access monitoring_baseline"
    ON public.monitoring_baseline FOR SELECT TO authenticated, anon USING (true);

-- Materialized view read access
GRANT SELECT ON public.mv_daily_metrics TO authenticated, anon, service_role;

-- ============================================================================
-- 8. COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE public.monitoring_metrics IS 'Aggregated metrics for drift/regression monitoring. Computed from learning_events.';
COMMENT ON TABLE public.monitoring_alerts IS 'Alert history for drift and regression detection';
COMMENT ON TABLE public.monitoring_baseline IS 'Rolling baseline values for metric comparison';
COMMENT ON MATERIALIZED VIEW public.mv_daily_metrics IS 'Pre-computed daily metrics for fast dashboard queries';

COMMENT ON FUNCTION public.compute_hourly_metrics IS 'Compute hourly metrics from learning_events. Specify hour or NULL for all hours.';
COMMENT ON FUNCTION public.compute_daily_metrics IS 'Compute daily metrics by aggregating all hours.';
COMMENT ON FUNCTION public.update_baseline IS 'Update rolling baseline from recent metrics.';
COMMENT ON FUNCTION public.check_drift_and_alert IS 'Check current metrics against baseline and create alerts for drift.';
COMMENT ON FUNCTION public.refresh_daily_metrics_mv IS 'Refresh the daily metrics materialized view.';

-- ============================================================================
-- 9. CONVENIENCE VIEWS
-- ============================================================================

-- View: Current status summary
CREATE OR REPLACE VIEW public.v_monitoring_current_status AS
SELECT
    CURRENT_DATE AS metric_date,
    m.total_events,
    m.fallback_rate,
    m.error_rate,
    m.duplicate_rate,
    m.latency_p50,
    m.latency_p95,
    m.latency_p99,
    m.health_score,
    b.baseline_fallback_rate,
    b.baseline_error_rate,
    b.baseline_latency_p95,
    CASE
        WHEN m.fallback_rate > 0 AND b.baseline_fallback_rate > 0
        THEN ROUND((m.fallback_rate / b.baseline_fallback_rate)::NUMERIC, 2)
        ELSE NULL
    END AS fallback_vs_baseline,
    CASE
        WHEN m.error_rate > 0 AND b.baseline_error_rate > 0
        THEN ROUND((m.error_rate / b.baseline_error_rate)::NUMERIC, 2)
        ELSE NULL
    END AS error_vs_baseline,
    CASE
        WHEN m.latency_p95 > 0 AND b.baseline_latency_p95 > 0
        THEN ROUND((m.latency_p95 / b.baseline_latency_p95)::NUMERIC, 2)
        ELSE NULL
    END AS latency_vs_baseline,
    (SELECT COUNT(*) FROM public.monitoring_alerts WHERE status = 'open') AS open_alerts
FROM public.mv_daily_metrics m
CROSS JOIN public.monitoring_baseline b
WHERE m.metric_date = CURRENT_DATE
AND b.baseline_name = '7day_rolling';

COMMENT ON VIEW public.v_monitoring_current_status IS 'Current monitoring status compared to baseline';

-- View: Alert summary
CREATE OR REPLACE VIEW public.v_monitoring_alert_summary AS
SELECT
    metric_date,
    alert_type,
    severity,
    COUNT(*) AS alert_count,
    MAX(current_value) AS max_current_value,
    MAX(baseline_value) AS max_baseline_value,
    MAX(deviation_ratio) AS max_deviation,
    MAX(created_at) AS latest_alert_at,
    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open_count
FROM public.monitoring_alerts
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY metric_date, alert_type, severity
ORDER BY metric_date DESC, alert_type, severity;

COMMENT ON VIEW public.v_monitoring_alert_summary IS 'Summary of alerts by type and severity';

-- ============================================================================
-- 10. SCHEDULED REFRESH (Manual - use pg_cron if available)
-- ============================================================================

-- To enable automatic refresh with pg_cron (if installed):
--
-- SELECT cron.schedule(
--     'refresh-monitoring-metrics',
--     '0 * * * *', -- Every hour
--     $$SELECT compute_hourly_metrics(CURRENT_DATE, EXTRACT(HOUR FROM NOW())::INTEGER)$$
-- );
--
-- SELECT cron.schedule(
--     'refresh-monitoring-baseline',
--     '0 2 * * *', -- Daily at 2 AM
--     $$SELECT update_baseline(); REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_metrics;$$
-- );

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check tables exist
SELECT
    table_name,
    object_type,
    schema_name
FROM information_schema.tables
WHERE table_name LIKE 'monitoring%'
   OR table_name = 'mv_daily_metrics'
ORDER BY table_name;

-- Check indexes
SELECT
    indexname,
    tablename
FROM pg_indexes
WHERE tablename LIKE 'monitoring%'
   OR tablename = 'mv_daily_metrics'
ORDER BY tablename, indexname;

-- Check functions
SELECT
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name LIKE '%monitoring%'
   OR routine_name LIKE 'compute_%'
   OR routine_name LIKE 'update_baseline'
   OR routine_name LIKE 'check_drift%'
ORDER BY routine_name;
