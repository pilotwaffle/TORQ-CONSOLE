-- ============================================================
-- TORQ Console Telemetry: Canonical Schema Alignment
-- Idempotent "stop-the-bleeding" migration
-- ============================================================
--
-- This migration aligns Supabase tables to what the Vercel API expects.
-- It is idempotent (safe to re-run) and removes legacy NOT NULL landmines.
--
-- Run once in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/sql
-- ============================================================

-- 1) telemetry_traces: align column names + add expected fields
DO $$
BEGIN
  -- Rename completed_at -> ended_at if the old name exists
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'telemetry_traces' AND column_name = 'completed_at'
  ) AND NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'telemetry_traces' AND column_name = 'ended_at'
  ) THEN
    ALTER TABLE telemetry_traces RENAME COLUMN completed_at TO ended_at;
  END IF;

  -- Ensure core columns exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_traces' AND column_name='trace_id') THEN
    ALTER TABLE telemetry_traces ADD COLUMN trace_id TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_traces' AND column_name='session_id') THEN
    ALTER TABLE telemetry_traces ADD COLUMN session_id TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_traces' AND column_name='user_id') THEN
    ALTER TABLE telemetry_traces ADD COLUMN user_id TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_traces' AND column_name='meta') THEN
    ALTER TABLE telemetry_traces ADD COLUMN meta JSONB DEFAULT '{}'::jsonb;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_traces' AND column_name='error_code') THEN
    ALTER TABLE telemetry_traces ADD COLUMN error_code TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_traces' AND column_name='error_message') THEN
    ALTER TABLE telemetry_traces ADD COLUMN error_message TEXT;
  END IF;

  -- Optional: useful for timeline UI if not already present
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_traces' AND column_name='started_at') THEN
    ALTER TABLE telemetry_traces ADD COLUMN started_at TIMESTAMPTZ;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_traces' AND column_name='ended_at') THEN
    ALTER TABLE telemetry_traces ADD COLUMN ended_at TIMESTAMPTZ;
  END IF;

END $$;


-- 2) telemetry_spans: add all fields the ingest kept asking for
DO $$
BEGIN
  -- Required identity-ish fields
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='trace_id') THEN
    ALTER TABLE telemetry_spans ADD COLUMN trace_id TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='span_id') THEN
    ALTER TABLE telemetry_spans ADD COLUMN span_id TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='parent_span_id') THEN
    ALTER TABLE telemetry_spans ADD COLUMN parent_span_id TEXT;
  END IF;

  -- API expects these (based on your error trail)
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='kind') THEN
    ALTER TABLE telemetry_spans ADD COLUMN kind TEXT DEFAULT 'internal';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='name') THEN
    ALTER TABLE telemetry_spans ADD COLUMN name TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='duration_ms') THEN
    ALTER TABLE telemetry_spans ADD COLUMN duration_ms INTEGER;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='attributes') THEN
    ALTER TABLE telemetry_spans ADD COLUMN attributes JSONB DEFAULT '{}'::jsonb;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='meta') THEN
    ALTER TABLE telemetry_spans ADD COLUMN meta JSONB DEFAULT '{}'::jsonb;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='user_id') THEN
    ALTER TABLE telemetry_spans ADD COLUMN user_id TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='error_code') THEN
    ALTER TABLE telemetry_spans ADD COLUMN error_code TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='error_message') THEN
    ALTER TABLE telemetry_spans ADD COLUMN error_message TEXT;
  END IF;

  -- Millisecond timestamps
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='start_ms') THEN
    ALTER TABLE telemetry_spans ADD COLUMN start_ms BIGINT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='end_ms') THEN
    ALTER TABLE telemetry_spans ADD COLUMN end_ms BIGINT;
  END IF;

  -- Model/provider + tokens
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='provider') THEN
    ALTER TABLE telemetry_spans ADD COLUMN provider TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='model') THEN
    ALTER TABLE telemetry_spans ADD COLUMN model TEXT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='tokens_in') THEN
    ALTER TABLE telemetry_spans ADD COLUMN tokens_in INTEGER;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='tokens_out') THEN
    ALTER TABLE telemetry_spans ADD COLUMN tokens_out INTEGER;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name='telemetry_spans' AND column_name='tokens_total') THEN
    ALTER TABLE telemetry_spans ADD COLUMN tokens_total INTEGER;
  END IF;

END $$;


-- 3) Remove legacy NOT NULL constraints that conflict with new ingest fields
-- (These were the reason you saw "span_name NOT NULL" failures)
DO $$
BEGIN
  -- Only drop NOT NULL if the column exists
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name='telemetry_spans' AND column_name='span_name') THEN
    EXECUTE 'ALTER TABLE telemetry_spans ALTER COLUMN span_name DROP NOT NULL';
  END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name='telemetry_spans' AND column_name='span_type') THEN
    EXECUTE 'ALTER TABLE telemetry_spans ALTER COLUMN span_type DROP NOT NULL';
  END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name='telemetry_spans' AND column_name='completed_at') THEN
    EXECUTE 'ALTER TABLE telemetry_spans ALTER COLUMN completed_at DROP NOT NULL';
  END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name='telemetry_spans' AND column_name='duration_ms') THEN
    EXECUTE 'ALTER TABLE telemetry_spans ALTER COLUMN duration_ms DROP NOT NULL';
  END IF;

END $$;


-- 4) Helpful indexes (safe, performance win for UI + audits)
CREATE INDEX IF NOT EXISTS idx_telemetry_traces_trace_id ON telemetry_traces(trace_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_traces_session_id ON telemetry_traces(session_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_trace_id ON telemetry_spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_span_id ON telemetry_spans(span_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_parent_span_id ON telemetry_spans(parent_span_id);

-- Optional: if you commonly query by time
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_start_ms ON telemetry_spans(start_ms);


-- 5) Quick verification: list the "contract columns"
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('telemetry_traces','telemetry_spans')
AND (
  column_name IN (
    'trace_id','session_id','user_id','meta','started_at','ended_at','error_code','error_message',
    'span_id','parent_span_id','kind','name','duration_ms','attributes','start_ms','end_ms',
    'provider','model','tokens_in','tokens_out','tokens_total'
  )
)
ORDER BY table_name, column_name;
