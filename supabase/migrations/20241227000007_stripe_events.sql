-- CorrigeProvas Stripe Events Table
-- Stores processed Stripe webhook events for idempotency

-- Create table for tracking processed Stripe events
CREATE TABLE stripe_processed_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast lookups by event_id
CREATE INDEX idx_stripe_processed_events_event_id ON stripe_processed_events(event_id);

-- Index for cleanup queries (delete old events)
CREATE INDEX idx_stripe_processed_events_processed_at ON stripe_processed_events(processed_at);

-- Comment on table
COMMENT ON TABLE stripe_processed_events IS 'Tracks processed Stripe webhook events for idempotency';
