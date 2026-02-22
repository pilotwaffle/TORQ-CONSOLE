-- ============================================
-- TORQ Console: Complete Schema Fix
-- Adds ALL missing columns for full API compatibility
-- ============================================

-- Add missing columns to telemetry_traces
ALTER TABLE telemetry_traces ADD COLUMN IF NOT EXISTS error_code TEXT;
ALTER TABLE telemetry_traces ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE telemetry_traces ADD COLUMN IF NOT EXISTS user_id TEXT;
ALTER TABLE telemetry_traces ADD COLUMN IF NOT EXISTS meta JSONB DEFAULT '{}'::jsonb;

-- Add missing columns to telemetry_spans  
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS error_code TEXT;
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS user_id TEXT;
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS meta JSONB DEFAULT '{}'::jsonb;
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS start_ms BIGINT;
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS end_ms BIGINT;

-- Verify all columns in telemetry_traces
SELECT 'telemetry_traces' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'telemetry_traces'
ORDER BY column_name;

-- Verify all columns in telemetry_spans
SELECT 'telemetry_spans' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'telemetry_spans'
ORDER BY column_name;
