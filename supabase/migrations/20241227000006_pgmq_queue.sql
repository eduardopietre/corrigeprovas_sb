-- CorrigeProvas Queue Configuration
-- Sets up pgmq for async job processing

-- Enable pgmq extension
CREATE EXTENSION IF NOT EXISTS pgmq;

-- Create the corrections queue
SELECT pgmq.create('corrections');

-- Create a wrapper function for sending messages (for use in Edge Functions)
CREATE OR REPLACE FUNCTION pgmq_send(
    queue_name TEXT,
    message JSONB
) RETURNS BIGINT AS $
BEGIN
    RETURN pgmq.send(queue_name, message);
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a wrapper function for reading messages (for use in Worker)
CREATE OR REPLACE FUNCTION pgmq_read(
    queue_name TEXT,
    vt INTEGER DEFAULT 30,
    qty INTEGER DEFAULT 1
) RETURNS TABLE (
    msg_id BIGINT,
    read_ct INTEGER,
    enqueued_at TIMESTAMPTZ,
    vt TIMESTAMPTZ,
    message JSONB
) AS $
BEGIN
    RETURN QUERY SELECT * FROM pgmq.read(queue_name, vt, qty);
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a wrapper function for deleting messages (for use in Worker)
CREATE OR REPLACE FUNCTION pgmq_delete(
    queue_name TEXT,
    msg_id BIGINT
) RETURNS BOOLEAN AS $
BEGIN
    RETURN pgmq.delete(queue_name, msg_id);
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a wrapper function for archiving messages (for use in Worker)
CREATE OR REPLACE FUNCTION pgmq_archive(
    queue_name TEXT,
    msg_id BIGINT
) RETURNS BOOLEAN AS $
BEGIN
    RETURN pgmq.archive(queue_name, msg_id);
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions to service role functions
-- Note: These functions use SECURITY DEFINER so they run with owner privileges
