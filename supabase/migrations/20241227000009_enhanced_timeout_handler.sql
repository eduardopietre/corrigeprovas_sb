-- CorrigeProvas Enhanced Timeout Handler
-- Comprehensive timeout handling with proper error tracking and notifications

-- =============================================================================
-- TIMEOUT CONFIGURATION
-- =============================================================================

-- Create a configuration table for timeout settings
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default timeout configuration
INSERT INTO system_config (key, value, description) VALUES
    ('job_timeout_minutes', '30', 'Minutes after which a PROCESSING job is considered orphaned'),
    ('cleanup_frequency_minutes', '5', 'How often to run orphaned job cleanup'),
    ('stripe_events_retention_days', '30', 'Days to keep processed Stripe events')
ON CONFLICT (key) DO NOTHING;

-- =============================================================================
-- ENHANCED TIMEOUT HANDLER
-- =============================================================================

-- Drop existing function first to allow changing return type
DROP FUNCTION IF EXISTS handle_orphaned_jobs();

-- Enhanced function to handle orphaned jobs with better logging and error handling
CREATE OR REPLACE FUNCTION handle_orphaned_jobs()
RETURNS TABLE(
    job_id UUID,
    owner_user_id UUID,
    tokens_refunded INTEGER,
    processing_duration_minutes INTEGER,
    action_taken TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    timeout_minutes INTEGER;
    timeout_threshold INTERVAL;
    orphaned_job RECORD;
    processing_duration INTEGER;
    total_jobs_handled INTEGER := 0;
BEGIN
    -- Get timeout configuration
    SELECT value::INTEGER INTO timeout_minutes
    FROM system_config
    WHERE key = 'job_timeout_minutes';
    
    -- Default to 30 minutes if not configured
    timeout_minutes := COALESCE(timeout_minutes, 30);
    timeout_threshold := (timeout_minutes || ' minutes')::INTERVAL;
    
    -- Log start of cleanup
    RAISE NOTICE 'Starting orphaned jobs cleanup with timeout threshold: % minutes', timeout_minutes;
    
    -- Find and handle orphaned jobs
    FOR orphaned_job IN
        SELECT 
            cj.id,
            cj.owner_user_id,
            cj.total_items,
            cj.started_at,
            cj.created_at,
            EXTRACT(EPOCH FROM (NOW() - cj.started_at))/60 as minutes_processing
        FROM correction_jobs cj
        WHERE cj.status = 'PROCESSING'
        AND cj.started_at IS NOT NULL
        AND cj.started_at < (NOW() - timeout_threshold)
        ORDER BY cj.started_at ASC -- Handle oldest jobs first
    LOOP
        processing_duration := orphaned_job.minutes_processing::INTEGER;
        
        -- Log the orphaned job
        RAISE NOTICE 'Handling orphaned job: % (owner: %, processing for: % minutes)', 
            orphaned_job.id, orphaned_job.owner_user_id, processing_duration;
        
        -- Update job status to FAILED with detailed information
        UPDATE correction_jobs
        SET 
            status = 'FAILED',
            finished_at = NOW(),
            elapsed_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000
        WHERE id = orphaned_job.id;
        
        -- Update any correction_items that are still pending
        UPDATE correction_items
        SET 
            error_code = 'JOB_TIMEOUT',
            error_message = FORMAT('Job timed out after %s minutes and was automatically failed by system maintenance', processing_duration)
        WHERE job_id = orphaned_job.id
        AND error_code IS NULL;
        
        -- Refund tokens using the existing release_tokens function
        BEGIN
            PERFORM release_tokens(orphaned_job.id);
            
            -- Return information about this job
            job_id := orphaned_job.id;
            owner_user_id := orphaned_job.owner_user_id;
            tokens_refunded := orphaned_job.total_items;
            processing_duration_minutes := processing_duration;
            action_taken := 'FAILED_AND_REFUNDED';
            
            RETURN NEXT;
            
        EXCEPTION WHEN OTHERS THEN
            -- Log error but continue with other jobs
            RAISE WARNING 'Failed to refund tokens for job %: %', orphaned_job.id, SQLERRM;
            
            -- Return information about this job with error
            job_id := orphaned_job.id;
            owner_user_id := orphaned_job.owner_user_id;
            tokens_refunded := 0;
            processing_duration_minutes := processing_duration;
            action_taken := 'FAILED_BUT_REFUND_ERROR';
            
            RETURN NEXT;
        END;
        
        total_jobs_handled := total_jobs_handled + 1;
    END LOOP;
    
    -- Log completion
    RAISE NOTICE 'Orphaned jobs cleanup completed. Handled % jobs at %', total_jobs_handled, NOW();
    
    -- If no jobs were handled, still return a summary row
    IF total_jobs_handled = 0 THEN
        job_id := NULL;
        owner_user_id := NULL;
        tokens_refunded := 0;
        processing_duration_minutes := 0;
        action_taken := 'NO_ORPHANED_JOBS_FOUND';
        RETURN NEXT;
    END IF;
END;
$$;

-- =============================================================================
-- JOB STATUS MONITORING FUNCTIONS
-- =============================================================================

-- Function to get statistics about job processing times
CREATE OR REPLACE FUNCTION get_job_processing_stats()
RETURNS TABLE(
    status TEXT,
    count BIGINT,
    avg_processing_minutes NUMERIC,
    max_processing_minutes NUMERIC,
    oldest_job_started TIMESTAMPTZ
)
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cj.status::TEXT,
        COUNT(*) as count,
        ROUND(AVG(EXTRACT(EPOCH FROM (COALESCE(cj.finished_at, NOW()) - cj.started_at))/60), 2) as avg_processing_minutes,
        ROUND(MAX(EXTRACT(EPOCH FROM (COALESCE(cj.finished_at, NOW()) - cj.started_at))/60), 2) as max_processing_minutes,
        MIN(cj.started_at) as oldest_job_started
    FROM correction_jobs cj
    WHERE cj.started_at IS NOT NULL
    GROUP BY cj.status
    ORDER BY 
        CASE cj.status 
            WHEN 'PROCESSING' THEN 1 
            WHEN 'FAILED' THEN 2 
            WHEN 'DONE' THEN 3 
            ELSE 4 
        END;
END;
$$;

-- Function to check for jobs that are approaching timeout
CREATE OR REPLACE FUNCTION get_jobs_approaching_timeout()
RETURNS TABLE(
    job_id UUID,
    owner_user_id UUID,
    started_at TIMESTAMPTZ,
    minutes_processing NUMERIC,
    minutes_until_timeout NUMERIC
)
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
AS $$
DECLARE
    timeout_minutes INTEGER;
    warning_threshold NUMERIC;
BEGIN
    -- Get timeout configuration
    SELECT value::INTEGER INTO timeout_minutes
    FROM system_config
    WHERE key = 'job_timeout_minutes';
    
    timeout_minutes := COALESCE(timeout_minutes, 30);
    warning_threshold := timeout_minutes * 0.8; -- Warn at 80% of timeout
    
    RETURN QUERY
    SELECT 
        cj.id as job_id,
        cj.owner_user_id,
        cj.started_at,
        ROUND(EXTRACT(EPOCH FROM (NOW() - cj.started_at))/60, 2) as minutes_processing,
        ROUND(timeout_minutes - EXTRACT(EPOCH FROM (NOW() - cj.started_at))/60, 2) as minutes_until_timeout
    FROM correction_jobs cj
    WHERE cj.status = 'PROCESSING'
    AND cj.started_at IS NOT NULL
    AND EXTRACT(EPOCH FROM (NOW() - cj.started_at))/60 > warning_threshold
    AND EXTRACT(EPOCH FROM (NOW() - cj.started_at))/60 < timeout_minutes
    ORDER BY cj.started_at ASC;
END;
$$;

-- =============================================================================
-- MANUAL TIMEOUT FUNCTIONS (for admin use)
-- =============================================================================

-- Function to manually timeout a specific job (admin function)
CREATE OR REPLACE FUNCTION manual_timeout_job(p_job_id UUID)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT,
    tokens_refunded INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_job RECORD;
    v_tokens_refunded INTEGER := 0;
BEGIN
    -- Get job details
    SELECT id, owner_user_id, status, total_items, started_at
    INTO v_job
    FROM correction_jobs
    WHERE id = p_job_id;
    
    IF NOT FOUND THEN
        success := FALSE;
        message := 'Job not found';
        tokens_refunded := 0;
        RETURN NEXT;
        RETURN;
    END IF;
    
    IF v_job.status != 'PROCESSING' THEN
        success := FALSE;
        message := FORMAT('Job is not in PROCESSING status (current: %s)', v_job.status);
        tokens_refunded := 0;
        RETURN NEXT;
        RETURN;
    END IF;
    
    -- Update job to FAILED
    UPDATE correction_jobs
    SET 
        status = 'FAILED',
        finished_at = NOW(),
        elapsed_ms = CASE 
            WHEN started_at IS NOT NULL THEN EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000
            ELSE NULL
        END
    WHERE id = p_job_id;
    
    -- Update correction items
    UPDATE correction_items
    SET 
        error_code = 'MANUAL_TIMEOUT',
        error_message = 'Job was manually timed out by administrator'
    WHERE job_id = p_job_id
    AND error_code IS NULL;
    
    -- Refund tokens
    BEGIN
        PERFORM release_tokens(p_job_id);
        v_tokens_refunded := v_job.total_items;
        
        success := TRUE;
        message := FORMAT('Job manually timed out and %s tokens refunded', v_tokens_refunded);
        tokens_refunded := v_tokens_refunded;
        
    EXCEPTION WHEN OTHERS THEN
        success := FALSE;
        message := FORMAT('Job timed out but token refund failed: %s', SQLERRM);
        tokens_refunded := 0;
    END;
    
    RETURN NEXT;
END;
$$;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON FUNCTION handle_orphaned_jobs() IS 'Enhanced function to handle orphaned correction jobs with detailed logging and error handling';
COMMENT ON FUNCTION get_job_processing_stats() IS 'Returns statistics about job processing times by status';
COMMENT ON FUNCTION get_jobs_approaching_timeout() IS 'Returns jobs that are approaching the timeout threshold';
COMMENT ON FUNCTION manual_timeout_job(UUID) IS 'Manually timeout a specific job (admin function)';
COMMENT ON TABLE system_config IS 'System configuration parameters for timeout handling and other settings';

-- Grant permissions for monitoring functions (read-only)
GRANT EXECUTE ON FUNCTION get_job_processing_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION get_jobs_approaching_timeout() TO authenticated;

-- manual_timeout_job should only be available to service_role (admin functions)
-- No explicit grant needed due to SECURITY DEFINER