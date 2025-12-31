-- Security constraints and validation functions
-- This migration adds security constraints to prevent path traversal and other attacks

-- Function to validate storage paths
CREATE OR REPLACE FUNCTION validate_storage_path(path TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    -- Check for null or empty path
    IF path IS NULL OR trim(path) = '' THEN
        RETURN FALSE;
    END IF;
    
    -- Check for path traversal sequences
    IF path LIKE '%/../%' OR path LIKE '%\..\%' OR path LIKE '%..%' THEN
        RETURN FALSE;
    END IF;
    
    -- Check for control characters and dangerous characters
    IF path ~ '[\x00-\x1f\x7f-\x9f<>:"|?*]' THEN
        RETURN FALSE;
    END IF;
    
    -- Path should not start with / or \
    IF path LIKE '/%' OR path LIKE '\%' THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$;

-- Function to validate bucket names
CREATE OR REPLACE FUNCTION validate_bucket_name(bucket TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    -- Check for null or empty bucket
    IF bucket IS NULL OR trim(bucket) = '' THEN
        RETURN FALSE;
    END IF;
    
    -- Only allow specific bucket names
    RETURN bucket IN ('uploads', 'results', 'templates', 'exports');
END;
$$;

-- Function to validate UUID format
CREATE OR REPLACE FUNCTION validate_uuid_format(uuid_text TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    -- Check if the text matches UUID format
    RETURN uuid_text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$';
END;
$$;

-- Function to extract user ID from storage path
CREATE OR REPLACE FUNCTION extract_user_id_from_path(path TEXT)
RETURNS UUID
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    path_parts TEXT[];
    user_id_text TEXT;
BEGIN
    -- Split path by '/'
    path_parts := string_to_array(path, '/');
    
    -- First part should be user ID
    IF array_length(path_parts, 1) < 1 THEN
        RETURN NULL;
    END IF;
    
    user_id_text := path_parts[1];
    
    -- Validate UUID format
    IF NOT validate_uuid_format(user_id_text) THEN
        RETURN NULL;
    END IF;
    
    RETURN user_id_text::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$;

-- Add check constraints to correction_items table
ALTER TABLE correction_items 
ADD CONSTRAINT check_original_storage_path_valid 
CHECK (validate_storage_path(original_storage_path));

ALTER TABLE correction_items 
ADD CONSTRAINT check_marked_storage_path_valid 
CHECK (marked_storage_path IS NULL OR validate_storage_path(marked_storage_path));

-- Add check constraints to templates table
ALTER TABLE templates 
ADD CONSTRAINT check_template_storage_path_valid 
CHECK (validate_storage_path(template_storage_path));

-- Add check constraints to correction_jobs table for xlsx_storage_path
ALTER TABLE correction_jobs 
ADD CONSTRAINT check_xlsx_storage_path_valid 
CHECK (xlsx_storage_path IS NULL OR validate_storage_path(xlsx_storage_path));

-- Add check constraint for idempotency key format
ALTER TABLE correction_jobs 
ADD CONSTRAINT check_idempotency_key_format 
CHECK (
    idempotency_key IS NULL OR 
    (
        length(idempotency_key) BETWEEN 1 AND 255 AND
        idempotency_key ~ '^[a-zA-Z0-9_-]+$'
    )
);

-- Create index for idempotency key lookups
CREATE INDEX IF NOT EXISTS idx_correction_jobs_idempotency_key 
ON correction_jobs(idempotency_key) 
WHERE idempotency_key IS NOT NULL;

-- RLS policy to ensure users can only access their own storage paths
-- This policy checks that the storage path starts with the user's ID

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can only access their own correction items" ON correction_items;
DROP POLICY IF EXISTS "Users can only create correction items for their jobs" ON correction_items;

-- Create new policies with path validation
CREATE POLICY "Users can only access their own correction items" ON correction_items
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM correction_jobs 
            WHERE correction_jobs.id = correction_items.job_id 
            AND correction_jobs.owner_user_id = auth.uid()
        )
        AND (
            original_storage_path IS NULL OR
            extract_user_id_from_path(
                CASE 
                    WHEN original_storage_path LIKE 'uploads/%' THEN substring(original_storage_path from 9)
                    ELSE original_storage_path
                END
            ) = auth.uid()
        )
    );

CREATE POLICY "Users can only create correction items for their jobs" ON correction_items
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM correction_jobs 
            WHERE correction_jobs.id = correction_items.job_id 
            AND correction_jobs.owner_user_id = auth.uid()
        )
        AND (
            original_storage_path IS NULL OR
            extract_user_id_from_path(
                CASE 
                    WHEN original_storage_path LIKE 'uploads/%' THEN substring(original_storage_path from 9)
                    ELSE original_storage_path
                END
            ) = auth.uid()
        )
    );

-- Create policy for updates (worker updates marked_storage_path)
CREATE POLICY "Service role can update correction items" ON correction_items
    FOR UPDATE
    USING (true)  -- Service role bypasses RLS
    WITH CHECK (
        marked_storage_path IS NULL OR
        validate_storage_path(marked_storage_path)
    );

-- Add security logging function
CREATE OR REPLACE FUNCTION log_security_violation(
    violation_type TEXT,
    user_id UUID,
    details JSONB DEFAULT '{}'::JSONB
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Log security violations for monitoring
    INSERT INTO security_logs (violation_type, user_id, details, created_at)
    VALUES (violation_type, user_id, details, NOW());
EXCEPTION
    WHEN OTHERS THEN
        -- Don't fail the main operation if logging fails
        NULL;
END;
$$;

-- Create security_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS security_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    violation_type TEXT NOT NULL,
    user_id UUID,
    details JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for security log queries
CREATE INDEX IF NOT EXISTS idx_security_logs_created_at ON security_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_security_logs_violation_type ON security_logs(violation_type);
CREATE INDEX IF NOT EXISTS idx_security_logs_user_id ON security_logs(user_id);

-- Enable RLS on security_logs
ALTER TABLE security_logs ENABLE ROW LEVEL SECURITY;

-- Only service role can access security logs
CREATE POLICY "Only service role can access security logs" ON security_logs
    FOR ALL
    USING (auth.role() = 'service_role');

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated, anon;
GRANT EXECUTE ON FUNCTION validate_storage_path(TEXT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION validate_bucket_name(TEXT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION validate_uuid_format(TEXT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION extract_user_id_from_path(TEXT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION log_security_violation(TEXT, UUID, JSONB) TO service_role;

-- Comment on functions for documentation
COMMENT ON FUNCTION validate_storage_path(TEXT) IS 'Validates storage paths to prevent path traversal attacks';
COMMENT ON FUNCTION validate_bucket_name(TEXT) IS 'Validates bucket names against allowed list';
COMMENT ON FUNCTION validate_uuid_format(TEXT) IS 'Validates UUID format using regex';
COMMENT ON FUNCTION extract_user_id_from_path(TEXT) IS 'Extracts and validates user ID from storage path';
COMMENT ON FUNCTION log_security_violation(TEXT, UUID, JSONB) IS 'Logs security violations for monitoring';