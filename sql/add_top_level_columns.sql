-- ============================================================================
-- TORQ Console: Add Top-Level Columns for Analytics Performance
-- ============================================================================
--
-- This script adds indexed top-level columns for frequently filtered fields.
-- Keep rich data in event_data JSONB, but put filter keys in columns for speed.
--
-- Columns to add:
--   - session_id (indexed) - filter by session
--   - trace_id (indexed) - filter by trace (alias for source_trace_id)
--   - duplicate_count - track retry frequency without breaking idempotency
--   - last_seen_at - for attempt counter tracking
--
-- Run in Supabase SQL Editor
-- ============================================================================

-- 1. Add session_id column (if not exists as top-level)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'learning_events' AND column_name = 'session_id'
    ) THEN
        ALTER TABLE public.learning_events
        ADD COLUMN session_id TEXT;

        -- Create index for session lookups
        CREATE INDEX idx_learning_events_session_id
        ON public.learning_events(session_id DESC);

        RAISE NOTICE 'Added session_id column and index';
    ELSE
        RAISE NOTICE 'session_id column already exists';
    END IF;
END $$;

-- 2. Add trace_id column (alias for source_trace_id, easier naming)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'learning_events' AND column_name = 'trace_id'
    ) THEN
        ALTER TABLE public.learning_events
        ADD COLUMN trace_id TEXT;

        -- Copy existing source_trace_id values
        UPDATE public.learning_events
        SET trace_id = source_trace_id
        WHERE trace_id IS NULL AND source_trace_id IS NOT NULL;

        -- Create index for trace lookups
        CREATE INDEX idx_learning_events_trace_id
        ON public.learning_events(trace_id DESC);

        RAISE NOTICE 'Added trace_id column and index';
    ELSE
        RAISE NOTICE 'trace_id column already exists';
    END IF;
END $$;

-- 3. Add attempt counter columns (for tracking retries/duplicates)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'learning_events' AND column_name = 'duplicate_count'
    ) THEN
        ALTER TABLE public.learning_events
        ADD COLUMN duplicate_count INTEGER DEFAULT 0;

        RAISE NOTICE 'Added duplicate_count column';
    ELSE
        RAISE NOTICE 'duplicate_count column already exists';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'learning_events' AND column_name = 'last_seen_at'
    ) THEN
        ALTER TABLE public.learning_events
        ADD COLUMN last_seen_at TIMESTAMPTZ;

        RAISE NOTICE 'Added last_seen_at column';
    ELSE
        RAISE NOTICE 'last_seen_at column already exists';
    END IF;
END $$;

-- 4. Create partial index for analytics (recent events only)
-- This keeps index size small while supporting dashboard queries
-- Recent events index - use simple index without time-based predicate
CREATE INDEX IF NOT EXISTS idx_learning_events_recent
ON public.learning_events(occurred_at DESC);

-- 5. Create composite index for common session+time queries
CREATE INDEX IF NOT EXISTS idx_learning_events_session_time
ON public.learning_events(session_id, occurred_at DESC)
WHERE session_id IS NOT NULL;

-- 6. Add comment for documentation
COMMENT ON TABLE public.learning_events IS
'TORQ Console learning events with top-level columns for analytics speed. Rich data in event_data JSONB.';

COMMENT ON COLUMN public.learning_events.event_id IS 'Unique event identifier (SHA256 hash, idempotency key)';
COMMENT ON COLUMN public.learning_events.trace_id IS 'Trace identifier (correlates all events from one request)';
COMMENT ON COLUMN public.learning_events.session_id IS 'Session identifier (groups events from one user session)';
COMMENT ON COLUMN public.learning_events.duplicate_count IS 'Number of times this event_id was retried (attempt counter)';
COMMENT ON COLUMN public.learning_events.last_seen_at IS 'Last time this event_id was seen (for duplicate tracking)';

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check table structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'learning_events'
ORDER BY ordinal_position;

-- Check indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'learning_events'
ORDER BY indexname;

-- ============================================================================
-- Application Changes Required
-- ============================================================================
--
-- Update railway_app.py chat endpoint to:
--   1. Set session_id, trace_id as top-level columns
--   2. Use ON CONFLICT to increment duplicate_count and update last_seen_at
--
-- Example insert payload:
--
-- learning_payload = {
--     "event_id": learning_event_id,
--     "trace_id": trace_id,           # NEW: top-level
--     "session_id": request.session_id,  # NEW: top-level
--     "event_type": "chat_interaction",
--     "category": "learning",
--     "source_agent": "prince_flowers",
--     "source_trace_id": trace_id,
--     "event_data": {...},
--     "occurred_at": datetime.utcnow().isoformat()
-- }
--
-- With ON CONFLICT handling:
--
-- headers["Prefer"] = "resolution=merge-duplicates"
--
-- On conflict, the merge will:
-- - increment duplicate_count
-- - update last_seen_at
--
-- ============================================================================
