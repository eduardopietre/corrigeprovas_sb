-- Fix pgmq_read function wrapper
-- Use a simpler approach that should work with PostgREST

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS pgmq_read(TEXT, INTEGER, INTEGER);

-- Create a simple wrapper function that matches expected return type
CREATE OR REPLACE FUNCTION pgmq_read(
    queue_name TEXT,
    visibility_timeout INTEGER DEFAULT 30,
    qty INTEGER DEFAULT 1
) RETURNS TABLE (
    msg_id BIGINT,
    read_ct INTEGER,
    enqueued_at TIMESTAMPTZ,
    vt TIMESTAMPTZ,
    message JSONB
) AS $$
BEGIN
    RETURN QUERY SELECT
        r.msg_id,
        r.read_ct,
        r.enqueued_at,
        r.vt,
        r.message
    FROM pgmq.read(queue_name, visibility_timeout, qty) r;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
