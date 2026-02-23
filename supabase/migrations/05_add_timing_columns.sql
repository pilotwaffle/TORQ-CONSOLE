-- ============================================
-- TORQ Console: Add Timing Columns
-- Adds start_ms, end_ms columns for API compatibility
-- ============================================

-- Add timing columns to telemetry_spans (milliseconds since epoch)
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS start_ms BIGINT;
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS end_ms BIGINT;

-- Verify the columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'telemetry_spans'
AND column_name IN ('start_ms', 'end_ms', 'user_id', 'meta', 'started_at', 'completed_at')
ORDER BY column_name;
