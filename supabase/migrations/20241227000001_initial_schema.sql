-- CorrigeProvas Initial Schema Migration
-- Creates all tables, enums, and indexes for the application

-- =============================================================================
-- ENUMS
-- =============================================================================

-- Job status enum
CREATE TYPE job_status AS ENUM ('QUEUED', 'PROCESSING', 'DONE', 'FAILED', 'CANCELED');

-- User role enum
CREATE TYPE user_role AS ENUM ('USER', 'ADMIN', 'INSTITUTION_ADMIN');

-- Subscription status enum
CREATE TYPE subscription_status AS ENUM ('ACTIVE', 'PAST_DUE', 'CANCELED');

-- Usage reason enum
CREATE TYPE usage_reason AS ENUM ('CORRECTION_JOB', 'PLAN_RENEW', 'JOB_FAILED_REFUND', 'ADMIN_ADJUSTMENT');

-- =============================================================================
-- TABLES
-- =============================================================================

-- Institutions table
CREATE TABLE institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Profiles table (linked to auth.users)
CREATE TABLE profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    display_name TEXT,
    institution_id UUID REFERENCES institutions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- User roles table (many-to-many relationship)
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
    role user_role NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, role)
);

-- Templates table
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    question_count INTEGER NOT NULL CHECK (question_count IN (10, 20, 50, 100)),
    alternatives_count INTEGER NOT NULL CHECK (alternatives_count IN (4, 5)),
    version INTEGER NOT NULL DEFAULT 1,
    template_storage_path TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Plans table
CREATE TABLE plans (
    id TEXT PRIMARY KEY,
    monthly_price_cents INTEGER NOT NULL,
    monthly_tokens INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
    plan_id TEXT NOT NULL REFERENCES plans(id),
    status subscription_status NOT NULL DEFAULT 'ACTIVE',
    current_period_end TIMESTAMPTZ NOT NULL,
    provider TEXT NOT NULL DEFAULT 'stripe',
    provider_subscription_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Exams table
CREATE TABLE exams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id UUID NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
    institution_id UUID REFERENCES institutions(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- Exam variants table
CREATE TABLE exam_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    variant_index INTEGER NOT NULL,
    model_id UUID REFERENCES templates(id),
    qrcode_payload TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (exam_id, variant_index)
);

-- Answer keys table
CREATE TABLE answer_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id UUID NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
    institution_id UUID REFERENCES institutions(id) ON DELETE SET NULL,
    exam_id UUID REFERENCES exams(id) ON DELETE SET NULL,
    template_id UUID NOT NULL REFERENCES templates(id),
    answers_string TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Correction jobs table
CREATE TABLE correction_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id UUID NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
    institution_id UUID REFERENCES institutions(id) ON DELETE SET NULL,
    answer_key_id UUID NOT NULL REFERENCES answer_keys(id),
    template_id UUID NOT NULL REFERENCES templates(id),
    status job_status NOT NULL DEFAULT 'QUEUED',
    total_items INTEGER NOT NULL DEFAULT 0,
    success_items INTEGER NOT NULL DEFAULT 0,
    error_items INTEGER NOT NULL DEFAULT 0,
    elapsed_ms INTEGER,
    xlsx_storage_path TEXT,
    idempotency_key TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);


-- Correction items table
CREATE TABLE correction_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES correction_jobs(id) ON DELETE CASCADE,
    index INTEGER NOT NULL,
    original_storage_path TEXT NOT NULL,
    marked_storage_path TEXT,
    identifier TEXT,
    detected_answers TEXT,
    correct_count INTEGER,
    error_code TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (job_id, index)
);

-- Usage ledger table
CREATE TABLE usage_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
    delta_tokens INTEGER NOT NULL,
    reason usage_reason NOT NULL,
    job_id UUID REFERENCES correction_jobs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Profiles indexes
CREATE INDEX idx_profiles_institution_id ON profiles(institution_id);
CREATE INDEX idx_profiles_email ON profiles(email);

-- User roles indexes
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);

-- Templates indexes
CREATE INDEX idx_templates_is_active ON templates(is_active);
CREATE INDEX idx_templates_question_count ON templates(question_count);

-- Subscriptions indexes
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_provider_subscription_id ON subscriptions(provider_subscription_id);


-- Exams indexes
CREATE INDEX idx_exams_owner_user_id ON exams(owner_user_id);
CREATE INDEX idx_exams_institution_id ON exams(institution_id);

-- Exam variants indexes
CREATE INDEX idx_exam_variants_exam_id ON exam_variants(exam_id);

-- Answer keys indexes
CREATE INDEX idx_answer_keys_owner_user_id ON answer_keys(owner_user_id);
CREATE INDEX idx_answer_keys_institution_id ON answer_keys(institution_id);
CREATE INDEX idx_answer_keys_template_id ON answer_keys(template_id);
CREATE INDEX idx_answer_keys_exam_id ON answer_keys(exam_id);

-- Correction jobs indexes
CREATE INDEX idx_correction_jobs_owner_user_id ON correction_jobs(owner_user_id);
CREATE INDEX idx_correction_jobs_institution_id ON correction_jobs(institution_id);
CREATE INDEX idx_correction_jobs_status ON correction_jobs(status);
CREATE INDEX idx_correction_jobs_answer_key_id ON correction_jobs(answer_key_id);
CREATE INDEX idx_correction_jobs_created_at ON correction_jobs(created_at);
CREATE INDEX idx_correction_jobs_idempotency_key ON correction_jobs(idempotency_key);

-- Correction items indexes
CREATE INDEX idx_correction_items_job_id ON correction_items(job_id);

-- Usage ledger indexes
CREATE INDEX idx_usage_ledger_user_id ON usage_ledger(user_id);
CREATE INDEX idx_usage_ledger_job_id ON usage_ledger(job_id);
CREATE INDEX idx_usage_ledger_created_at ON usage_ledger(created_at);
CREATE INDEX idx_usage_ledger_reason ON usage_ledger(reason);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for subscriptions updated_at
CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- PROFILE CREATION TRIGGER
-- =============================================================================

-- Function to create profile on user signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (user_id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile when user signs up
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();
