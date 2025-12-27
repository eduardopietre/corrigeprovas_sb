-- CorrigeProvas Update Cron Jobs
-- Update existing cron jobs to use enhanced timeout handler

-- Remove the old cron job
SELECT cron.unschedule('cleanup-orphaned-jobs');

-- Schedule the enhanced orphaned jobs cleanup to run every 5 minutes
-- This version returns detailed information about handled jobs
SELECT cron.schedule(
    'cleanup-orphaned-jobs-enhanced',
    '*/5 * * * *', -- Every 5 minutes
    'SELECT * FROM handle_orphaned_jobs();'
);

-- Add a monitoring job that runs every hour to log job statistics
-- This helps with monitoring system health
SELECT cron.schedule(
    'log-job-statistics',
    '0 * * * *', -- Every hour at minute 0
    $$
    DO $log$
    DECLARE
        stat_record RECORD;
    BEGIN
        RAISE NOTICE 'Job Processing Statistics at %:', NOW();
        FOR stat_record IN SELECT * FROM get_job_processing_stats() LOOP
            RAISE NOTICE 'Status: %, Count: %, Avg Minutes: %, Max Minutes: %, Oldest Started: %',
                stat_record.status,
                stat_record.count,
                stat_record.avg_processing_minutes,
                stat_record.max_processing_minutes,
                stat_record.oldest_job_started;
        END LOOP;
    END;
    $log$;
    $$
);

-- Log the cron job updates
DO $$
BEGIN
    RAISE NOTICE 'Updated pg_cron jobs:';
    RAISE NOTICE '1. cleanup-orphaned-jobs-enhanced: Enhanced cleanup every 5 minutes';
    RAISE NOTICE '2. cleanup-stripe-events: Daily cleanup at 2 AM (unchanged)';
    RAISE NOTICE '3. log-job-statistics: Hourly statistics logging';
END;
$$;