-- CorrigeProvas Token Management Functions
-- Implements transactional token operations for the usage ledger

-- =============================================================================
-- GET BALANCE FUNCTION
-- =============================================================================

-- Function to get current token balance for a user
CREATE OR REPLACE FUNCTION get_balance(p_user_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_balance INTEGER;
BEGIN
    SELECT COALESCE(SUM(delta_tokens), 0) INTO v_balance
    FROM usage_ledger
    WHERE user_id = p_user_id;
    
    RETURN v_balance;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- =============================================================================
-- RESERVE TOKENS FUNCTION
-- =============================================================================

-- Function to reserve tokens for a correction job
-- Returns TRUE if successful, FALSE if insufficient balance
CREATE OR REPLACE FUNCTION reserve_tokens(
    p_user_id UUID,
    p_amount INTEGER,
    p_job_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_balance INTEGER;
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
    
    -- Calculate current balance with row-level lock to prevent race conditions
    SELECT COALESCE(SUM(delta_tokens), 0) INTO v_balance
    FROM usage_ledger
    WHERE user_id = p_user_id
    FOR UPDATE;
    
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


-- =============================================================================
-- RELEASE TOKENS FUNCTION
-- =============================================================================

-- Function to release/refund tokens when a job fails or is canceled
CREATE OR REPLACE FUNCTION release_tokens(p_job_id UUID)
RETURNS VOID AS $$
DECLARE
    v_job RECORD;
    v_already_refunded BOOLEAN;
BEGIN
    -- Validate input
    IF p_job_id IS NULL THEN
        RAISE EXCEPTION 'Job ID cannot be null';
    END IF;
    
    -- Get job details
    SELECT owner_user_id, total_items, status INTO v_job
    FROM correction_jobs
    WHERE id = p_job_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Job not found: %', p_job_id;
    END IF;
    
    -- Only refund for FAILED or CANCELED jobs
    IF v_job.status NOT IN ('FAILED', 'CANCELED') THEN
        RAISE EXCEPTION 'Can only release tokens for FAILED or CANCELED jobs';
    END IF;
    
    -- Check if already refunded
    SELECT EXISTS (
        SELECT 1 FROM usage_ledger 
        WHERE job_id = p_job_id AND reason = 'JOB_FAILED_REFUND'
    ) INTO v_already_refunded;
    
    IF v_already_refunded THEN
        -- Already refunded, do nothing (idempotent)
        RETURN;
    END IF;
    
    -- Credit tokens back (positive delta)
    INSERT INTO usage_ledger (user_id, delta_tokens, reason, job_id)
    VALUES (v_job.owner_user_id, v_job.total_items, 'JOB_FAILED_REFUND', p_job_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- CREDIT TOKENS FUNCTION (for plan renewals and admin adjustments)
-- =============================================================================

-- Function to credit tokens to a user (for subscriptions, admin adjustments)
CREATE OR REPLACE FUNCTION credit_tokens(
    p_user_id UUID,
    p_amount INTEGER,
    p_reason usage_reason,
    p_job_id UUID DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    -- Validate inputs
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be positive';
    END IF;
    
    IF p_user_id IS NULL THEN
        RAISE EXCEPTION 'User ID cannot be null';
    END IF;
    
    IF p_reason NOT IN ('PLAN_RENEW', 'ADMIN_ADJUSTMENT', 'JOB_FAILED_REFUND') THEN
        RAISE EXCEPTION 'Invalid reason for credit operation';
    END IF;
    
    -- Credit tokens (positive delta)
    INSERT INTO usage_ledger (user_id, delta_tokens, reason, job_id)
    VALUES (p_user_id, p_amount, p_reason, p_job_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- GRANT EXECUTE PERMISSIONS
-- =============================================================================

-- Allow authenticated users to check their own balance
GRANT EXECUTE ON FUNCTION get_balance(UUID) TO authenticated;

-- reserve_tokens, release_tokens, and credit_tokens should only be called
-- by service_role (Edge Functions, Worker) - no explicit grant needed
-- as SECURITY DEFINER functions run with owner privileges
