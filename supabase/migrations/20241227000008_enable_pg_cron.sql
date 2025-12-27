-- CorrigeProvas pg_cron Configuration
-- Enable pg_cron extension and create cron jobs for maintenance

-- Enable pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Grant necessary permissions to postgres role for cron jobs
-- Note: In Supabase, cron jobs run as the postgres superuser

-- Create a function to handle orphaned jobs (jobs stuck in PROCESSING status)
CREATE OR REPLACE FUNCTION handle_orphaned_jobs()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    timeout_threshold INTERVAL := '30 minutes'; -- Jobs stuck for more than 30 minutes
    orphaned_job RECORD;
    tokens_to_refund INTEGER;
BEGIN
    -- Find jobs that have been in PROCESSING status for too long
    FOR orphaned_job IN
        SELECT id, owner_user_id, total_items, started_at
        FROM correction_jobs
        WHERE status = 'PROCESSING'
        AND started_at IS NOT NULL
        AND started_at < (NOW() - timeout_threshold)
    LOOP
        -- Log the orphaned job (for debugging)
        RAISE NOTICE 'Handling orphaned job: % (started at: %)', orphaned_job.id, orphaned_job.started_at;
        
        -- Update job status to FAILED
        UPDATE correction_jobs
        SET 
            status = 'FAILED',
            finished_at = NOW(),
            elapsed_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000
        WHERE id = orphaned_job.id;
        
        -- Refund tokens by calling release_tokens function
        PERFORM release_tokens(orphaned_job.id);
        
        -- Update any correction_items that are still pending
        UPDATE correction_items
        SET 
            error_code = 'TIMEOUT',
            error_message = 'Job timed out and was marked as failed by cron job'
        WHERE job_id = orphaned_job.id
        AND error_code IS NULL;
        
    END LOOP;
    
    -- Log completion
    RAISE NOTICE 'Orphaned jobs cleanup completed at %', NOW();
END;
$$;

-- Create a function to cleanup old processed Stripe events (optional maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_stripe_events()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    retention_period INTERVAL := '30 days'; -- Keep events for 30 days
    deleted_count INTEGER;
BEGIN
    -- Delete old processed events
    DELETE FROM stripe_processed_events
    WHERE processed_at < (NOW() - retention_period);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the cleanup
    RAISE NOTICE 'Cleaned up % old Stripe events at %', deleted_count, NOW();
END;
$$;

-- Schedule the orphaned jobs cleanup to run every 5 minutes
-- This ensures jobs don't stay stuck for too long
SELECT cron.schedule(
    'cleanup-orphaned-jobs',
    '*/5 * * * *', -- Every 5 minutes
    'SELECT handle_orphaned_jobs();'
);

-- Schedule Stripe events cleanup to run daily at 2 AM
-- This keeps the stripe_processed_events table from growing indefinitely
SELECT cron.schedule(
    'cleanup-stripe-events',
    '0 2 * * *', -- Daily at 2 AM
    'SELECT cleanup_old_stripe_events();'
);

-- Add comments for documentation
COMMENT ON FUNCTION handle_orphaned_jobs() IS 'Handles correction jobs stuck in PROCESSING status by marking them as FAILED and refunding tokens';
COMMENT ON FUNCTION cleanup_old_stripe_events() IS 'Removes old processed Stripe events to prevent table bloat';

-- Log that cron jobs have been set up
DO $$
BEGIN
    RAISE NOTICE 'pg_cron has been configured with the following jobs:';
    RAISE NOTICE '1. cleanup-orphaned-jobs: Runs every 5 minutes to handle stuck jobs';
    RAISE NOTICE '2. cleanup-stripe-events: Runs daily at 2 AM to cleanup old events';
END;
$$;