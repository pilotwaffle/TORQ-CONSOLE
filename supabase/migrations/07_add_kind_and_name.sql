-- ============================================
-- TORQ Console: Add kind and name columns
-- API expects 'kind' but schema has 'span_type'
-- ============================================

-- Add 'kind' column (api expects this, separate from span_type)
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS kind TEXT DEFAULT 'internal';

-- Add 'name' column if missing (api expects this, separate from span_name)
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS name TEXT;

-- Ensure duration_ms exists
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS duration_ms INTEGER;

-- Ensure attributes exists for additional data
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS attributes JSONB DEFAULT '{}'::jsonb;

-- Verify the columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'telemetry_spans'
AND column_name IN ('kind', 'name', 'span_type', 'span_name', 'duration_ms', 'attributes')
ORDER BY column_name;
