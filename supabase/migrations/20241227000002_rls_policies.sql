-- CorrigeProvas RLS Policies Migration
-- Implements Row Level Security for all user data tables

-- =============================================================================
-- ENABLE RLS ON ALL TABLES
-- =============================================================================

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE exams ENABLE ROW LEVEL SECURITY;
ALTER TABLE exam_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE answer_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE correction_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE correction_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_ledger ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to check if user belongs to an institution
CREATE OR REPLACE FUNCTION user_institution_id()
RETURNS UUID AS $$
    SELECT institution_id FROM profiles WHERE user_id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- Function to check if user has a specific role
CREATE OR REPLACE FUNCTION user_has_role(check_role user_role)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM user_roles 
        WHERE user_id = auth.uid() AND role = check_role
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- Function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
    SELECT user_has_role('ADMIN');
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- Function to check if user is institution admin
CREATE OR REPLACE FUNCTION is_institution_admin()
RETURNS BOOLEAN AS $$
    SELECT user_has_role('INSTITUTION_ADMIN');
$$ LANGUAGE sql SECURITY DEFINER STABLE;


-- =============================================================================
-- PROFILES POLICIES
-- =============================================================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (user_id = auth.uid());

-- Users can view profiles in their institution
CREATE POLICY "Users can view institution profiles"
    ON profiles FOR SELECT
    USING (
        institution_id IS NOT NULL 
        AND institution_id = user_institution_id()
    );

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- =============================================================================
-- USER ROLES POLICIES
-- =============================================================================

-- Users can view their own roles
CREATE POLICY "Users can view own roles"
    ON user_roles FOR SELECT
    USING (user_id = auth.uid());

-- Admins can manage all roles
CREATE POLICY "Admins can manage roles"
    ON user_roles FOR ALL
    USING (is_admin());

-- =============================================================================
-- INSTITUTIONS POLICIES
-- =============================================================================

-- Users can view their own institution
CREATE POLICY "Users can view own institution"
    ON institutions FOR SELECT
    USING (id = user_institution_id());

-- Admins can manage all institutions
CREATE POLICY "Admins can manage institutions"
    ON institutions FOR ALL
    USING (is_admin());


-- =============================================================================
-- TEMPLATES POLICIES
-- =============================================================================

-- Anyone authenticated can view active templates
CREATE POLICY "Authenticated users can view active templates"
    ON templates FOR SELECT
    USING (is_active = TRUE AND auth.uid() IS NOT NULL);

-- Admins can manage all templates
CREATE POLICY "Admins can manage templates"
    ON templates FOR ALL
    USING (is_admin());

-- =============================================================================
-- PLANS POLICIES
-- =============================================================================

-- Anyone authenticated can view active plans
CREATE POLICY "Authenticated users can view active plans"
    ON plans FOR SELECT
    USING (is_active = TRUE AND auth.uid() IS NOT NULL);

-- Admins can manage all plans
CREATE POLICY "Admins can manage plans"
    ON plans FOR ALL
    USING (is_admin());

-- =============================================================================
-- SUBSCRIPTIONS POLICIES
-- =============================================================================

-- Users can view their own subscriptions
CREATE POLICY "Users can view own subscriptions"
    ON subscriptions FOR SELECT
    USING (user_id = auth.uid());

-- Users can insert their own subscriptions
CREATE POLICY "Users can create own subscriptions"
    ON subscriptions FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Admins can manage all subscriptions
CREATE POLICY "Admins can manage subscriptions"
    ON subscriptions FOR ALL
    USING (is_admin());


-- =============================================================================
-- EXAMS POLICIES
-- =============================================================================

-- Users can view their own exams
CREATE POLICY "Users can view own exams"
    ON exams FOR SELECT
    USING (owner_user_id = auth.uid());

-- Users can view institution exams
CREATE POLICY "Users can view institution exams"
    ON exams FOR SELECT
    USING (
        institution_id IS NOT NULL 
        AND institution_id = user_institution_id()
    );

-- Users can create their own exams
CREATE POLICY "Users can create own exams"
    ON exams FOR INSERT
    WITH CHECK (owner_user_id = auth.uid());

-- Users can update their own exams
CREATE POLICY "Users can update own exams"
    ON exams FOR UPDATE
    USING (owner_user_id = auth.uid())
    WITH CHECK (owner_user_id = auth.uid());

-- Users can delete their own exams
CREATE POLICY "Users can delete own exams"
    ON exams FOR DELETE
    USING (owner_user_id = auth.uid());

-- Institution admins can manage institution exams
CREATE POLICY "Institution admins can manage institution exams"
    ON exams FOR ALL
    USING (
        is_institution_admin() 
        AND institution_id = user_institution_id()
    );

-- =============================================================================
-- EXAM VARIANTS POLICIES
-- =============================================================================

-- Users can view variants of their own exams
CREATE POLICY "Users can view own exam variants"
    ON exam_variants FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM exams 
            WHERE exams.id = exam_variants.exam_id 
            AND exams.owner_user_id = auth.uid()
        )
    );

-- Users can view variants of institution exams
CREATE POLICY "Users can view institution exam variants"
    ON exam_variants FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM exams 
            WHERE exams.id = exam_variants.exam_id 
            AND exams.institution_id = user_institution_id()
        )
    );

-- Users can manage variants of their own exams
CREATE POLICY "Users can manage own exam variants"
    ON exam_variants FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM exams 
            WHERE exams.id = exam_variants.exam_id 
            AND exams.owner_user_id = auth.uid()
        )
    );


-- =============================================================================
-- ANSWER KEYS POLICIES
-- =============================================================================

-- Users can view their own answer keys
CREATE POLICY "Users can view own answer keys"
    ON answer_keys FOR SELECT
    USING (owner_user_id = auth.uid());

-- Users can view institution answer keys
CREATE POLICY "Users can view institution answer keys"
    ON answer_keys FOR SELECT
    USING (
        institution_id IS NOT NULL 
        AND institution_id = user_institution_id()
    );

-- Users can create their own answer keys
CREATE POLICY "Users can create own answer keys"
    ON answer_keys FOR INSERT
    WITH CHECK (owner_user_id = auth.uid());

-- Users can update their own answer keys
CREATE POLICY "Users can update own answer keys"
    ON answer_keys FOR UPDATE
    USING (owner_user_id = auth.uid())
    WITH CHECK (owner_user_id = auth.uid());

-- Users can delete their own answer keys
CREATE POLICY "Users can delete own answer keys"
    ON answer_keys FOR DELETE
    USING (owner_user_id = auth.uid());

-- Institution admins can manage institution answer keys
CREATE POLICY "Institution admins can manage institution answer keys"
    ON answer_keys FOR ALL
    USING (
        is_institution_admin() 
        AND institution_id = user_institution_id()
    );

-- =============================================================================
-- CORRECTION JOBS POLICIES
-- =============================================================================

-- Users can view their own correction jobs
CREATE POLICY "Users can view own correction jobs"
    ON correction_jobs FOR SELECT
    USING (owner_user_id = auth.uid());

-- Users can view institution correction jobs
CREATE POLICY "Users can view institution correction jobs"
    ON correction_jobs FOR SELECT
    USING (
        institution_id IS NOT NULL 
        AND institution_id = user_institution_id()
    );

-- Users can create their own correction jobs
CREATE POLICY "Users can create own correction jobs"
    ON correction_jobs FOR INSERT
    WITH CHECK (owner_user_id = auth.uid());

-- Users can update their own correction jobs (limited)
CREATE POLICY "Users can update own correction jobs"
    ON correction_jobs FOR UPDATE
    USING (owner_user_id = auth.uid())
    WITH CHECK (owner_user_id = auth.uid());

-- Institution admins can manage institution correction jobs
CREATE POLICY "Institution admins can manage institution correction jobs"
    ON correction_jobs FOR ALL
    USING (
        is_institution_admin() 
        AND institution_id = user_institution_id()
    );


-- =============================================================================
-- CORRECTION ITEMS POLICIES
-- =============================================================================

-- Users can view items of their own jobs
CREATE POLICY "Users can view own correction items"
    ON correction_items FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM correction_jobs 
            WHERE correction_jobs.id = correction_items.job_id 
            AND correction_jobs.owner_user_id = auth.uid()
        )
    );

-- Users can view items of institution jobs
CREATE POLICY "Users can view institution correction items"
    ON correction_items FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM correction_jobs 
            WHERE correction_jobs.id = correction_items.job_id 
            AND correction_jobs.institution_id = user_institution_id()
        )
    );

-- Users can create items for their own jobs
CREATE POLICY "Users can create own correction items"
    ON correction_items FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM correction_jobs 
            WHERE correction_jobs.id = correction_items.job_id 
            AND correction_jobs.owner_user_id = auth.uid()
        )
    );

-- =============================================================================
-- USAGE LEDGER POLICIES
-- =============================================================================

-- Users can view their own usage ledger
CREATE POLICY "Users can view own usage ledger"
    ON usage_ledger FOR SELECT
    USING (user_id = auth.uid());

-- Admins can view all usage ledger entries
CREATE POLICY "Admins can view all usage ledger"
    ON usage_ledger FOR SELECT
    USING (is_admin());

-- Note: INSERT/UPDATE/DELETE on usage_ledger should only be done via 
-- server-side functions (service_role), not directly by users
