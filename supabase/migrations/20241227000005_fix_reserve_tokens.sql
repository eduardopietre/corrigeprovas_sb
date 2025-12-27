-- Fix reserve_tokens function to use advisory locks instead of FOR UPDATE with aggregates
-- FOR UPDATE cannot be used with aggregate functions in PostgreSQL

CREATE OR REPLACE FUNCTION reserve_tokens(
    p_user_id UUID,
    p_amount INTEGER,
    p_job_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_balance INTEGER;
    v_lock_key BIGINT;
BEGIN
    -- Validate inputs
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be positive';
    END IF;
    
    IF p_user_id IS NULL THEN
        RAISE EXCEPTION 'User ID cannot be null';
    END IF;
    
    IF p_job_id IS NULL THEN
        RAISE EXCEPTION 'Job ID cannot be null';
    END IF;
    
    -- Use advisory lock based on user_id to prevent race conditions
    -- Convert first 8 hex chars of UUID to bigint for advisory lock
    v_lock_key := ('x' || replace(substr(p_user_id::text, 1, 8), '-', ''))::bit(32)::bigint;
    PERFORM pg_advisory_xact_lock(v_lock_key);
    
    -- Calculate current balance
    SELECT COALESCE(SUM(delta_tokens), 0) INTO v_balance
    FROM usage_ledger
    WHERE user_id = p_user_id;
    
    -- Check if sufficient balance
    IF v_balance < p_amount THEN
        RETURN FALSE;
    END IF;
    
    -- Debit tokens (negative delta)
    INSERT INTO usage_ledger (user_id, delta_tokens, reason, job_id)
    VALUES (p_user_id, -p_amount, 'CORRECTION_JOB', p_job_id);
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
