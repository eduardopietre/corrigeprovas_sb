-- CorrigeProvas Storage Buckets Configuration
-- Creates storage buckets and access policies

-- =============================================================================
-- CREATE STORAGE BUCKETS
-- =============================================================================

-- Templates bucket (public read for active templates)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'templates',
    'templates',
    FALSE,
    52428800, -- 50MB limit
    ARRAY['image/png', 'image/jpeg', 'image/webp', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
);

-- Uploads bucket (user uploads of scanned answer sheets)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'uploads',
    'uploads',
    FALSE,
    20971520, -- 20MB limit per file
    ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/tiff', 'application/pdf']
);

-- Results bucket (processed results, marked images, XLSX)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'results',
    'results',
    FALSE,
    52428800, -- 50MB limit
    ARRAY['image/jpeg', 'image/png', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
);

-- Exports bucket (generated exams, ZIPs)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'exports',
    'exports',
    FALSE,
    104857600, -- 100MB limit
    ARRAY['application/zip', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
);


-- =============================================================================
-- TEMPLATES BUCKET POLICIES
-- =============================================================================

-- Authenticated users can read templates
CREATE POLICY "Authenticated users can read templates"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'templates' 
        AND auth.uid() IS NOT NULL
    );

-- Only admins can upload/modify templates
CREATE POLICY "Admins can manage templates"
    ON storage.objects FOR ALL
    USING (
        bucket_id = 'templates' 
        AND EXISTS (
            SELECT 1 FROM user_roles 
            WHERE user_id = auth.uid() AND role = 'ADMIN'
        )
    );

-- =============================================================================
-- UPLOADS BUCKET POLICIES
-- =============================================================================

-- Users can upload to their own folder: uploads/{uid}/*
CREATE POLICY "Users can upload to own folder"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'uploads'
        AND auth.uid() IS NOT NULL
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can read their own uploads
CREATE POLICY "Users can read own uploads"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'uploads'
        AND auth.uid() IS NOT NULL
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can delete their own uploads
CREATE POLICY "Users can delete own uploads"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'uploads'
        AND auth.uid() IS NOT NULL
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Service role can access all uploads (for worker processing)
-- Note: service_role bypasses RLS by default


-- =============================================================================
-- RESULTS BUCKET POLICIES
-- =============================================================================

-- Users can read their own results: results/{uid}/*
CREATE POLICY "Users can read own results"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'results'
        AND auth.uid() IS NOT NULL
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users in same institution can read institution results
CREATE POLICY "Users can read institution results"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'results'
        AND auth.uid() IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM profiles p1
            JOIN profiles p2 ON p1.institution_id = p2.institution_id
            WHERE p1.user_id = auth.uid()
            AND p2.user_id::text = (storage.foldername(name))[1]
            AND p1.institution_id IS NOT NULL
        )
    );

-- Service role can write results (worker uploads processed images/XLSX)
-- Note: service_role bypasses RLS by default

-- =============================================================================
-- EXPORTS BUCKET POLICIES
-- =============================================================================

-- Users can upload to their own exports folder: exports/{uid}/*
CREATE POLICY "Users can upload to own exports folder"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'exports'
        AND auth.uid() IS NOT NULL
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can read their own exports
CREATE POLICY "Users can read own exports"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'exports'
        AND auth.uid() IS NOT NULL
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can delete their own exports
CREATE POLICY "Users can delete own exports"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'exports'
        AND auth.uid() IS NOT NULL
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users in same institution can read institution exports
CREATE POLICY "Users can read institution exports"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'exports'
        AND auth.uid() IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM profiles p1
            JOIN profiles p2 ON p1.institution_id = p2.institution_id
            WHERE p1.user_id = auth.uid()
            AND p2.user_id::text = (storage.foldername(name))[1]
            AND p1.institution_id IS NOT NULL
        )
    );
