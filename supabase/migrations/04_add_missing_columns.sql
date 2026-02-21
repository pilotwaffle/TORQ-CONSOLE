-- ============================================
-- TORQ Console: Add Missing Columns
-- Adds user_id and other missing columns
-- ============================================

-- Add missing columns to telemetry_traces
ALTER TABLE telemetry_traces ADD COLUMN IF NOT EXISTS user_id TEXT;
ALTER TABLE telemetry_traces ADD COLUMN IF NOT EXISTS meta JSONB DEFAULT '{}'::jsonb;

-- Add missing columns to telemetry_spans
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS user_id TEXT;
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS meta JSONB DEFAULT '{}'::jsonb;

-- Verify all columns
SELECT
    'telemetry_traces' as table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'telemetry_traces'
AND column_name IN ('user_id', 'meta', 'ended_at', 'trace_id')
ORDER BY column_name;
