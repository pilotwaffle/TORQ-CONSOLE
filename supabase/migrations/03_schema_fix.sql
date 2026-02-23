-- ============================================
-- TORQ Console: Schema Fix Migration
-- Fixes column name mismatches between
-- migration and application expectations
-- ============================================

-- Fix telemetry_traces table
-- Rename completed_at to ended_at (expected by API)
-- Note: This may have already been run
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'telemetry_traces' AND column_name = 'completed_at'
    ) THEN
        ALTER TABLE telemetry_traces RENAME COLUMN completed_at TO ended_at;
    END IF;
END $$;

-- Add missing 'meta' column (JSONB for metadata)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'telemetry_traces' AND column_name = 'meta'
    ) THEN
        ALTER TABLE telemetry_traces ADD COLUMN meta JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Ensure trace_id column is properly named
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'telemetry_traces' AND column_name = 'trace_id'
    ) THEN
        ALTER TABLE telemetry_traces ADD COLUMN trace_id TEXT;
    END IF;
END $$;

-- Fix telemetry_spans table
DO $$
BEGIN
    -- Ensure ttft_ms exists for Time To First Token
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'telemetry_spans' AND column_name = 'ttft_ms'
    ) THEN
        ALTER TABLE telemetry_spans ADD COLUMN ttft_ms INTEGER;
    END IF;

    -- Ensure meta column exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'telemetry_spans' AND column_name = 'meta'
    ) THEN
        ALTER TABLE telemetry_spans ADD COLUMN meta JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Verify the fix
SELECT
    'telemetry_traces' as table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'telemetry_traces'
AND column_name IN ('ended_at', 'completed_at', 'meta', 'trace_id')
ORDER BY ordinal_position;

SELECT
    'telemetry_spans' as table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'telemetry_spans'
AND column_name IN ('ttft_ms', 'first_token_at', 'meta')
ORDER BY ordinal_position;
