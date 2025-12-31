-- Fix storage path validation function
-- The previous version incorrectly rejected all paths containing forward slashes

-- Drop and recreate the function with corrected logic
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

-- Add comment for documentation
COMMENT ON FUNCTION validate_storage_path(TEXT) IS 'Validates storage paths to prevent path traversal attacks - corrected to allow normal path separators';
