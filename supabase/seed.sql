-- CorrigeProvas Seed Data
-- Initial data for templates and plans

-- =============================================================================
-- TEMPLATES
-- =============================================================================

INSERT INTO templates (id, name, question_count, alternatives_count, version, template_storage_path, is_active)
VALUES
    ('00000000-0000-0000-0000-000000000010', 'Modelo 10 Questões (A-D)', 10, 4, 1, 'templates/modelo-10-abcd/v1/template.png', TRUE),
    ('00000000-0000-0000-0000-000000000011', 'Modelo 10 Questões (A-E)', 10, 5, 1, 'templates/modelo-10-abcde/v1/template.png', TRUE),
    ('00000000-0000-0000-0000-000000000020', 'Modelo 20 Questões (A-D)', 20, 4, 1, 'templates/modelo-20-abcd/v1/template.png', TRUE),
    ('00000000-0000-0000-0000-000000000021', 'Modelo 20 Questões (A-E)', 20, 5, 1, 'templates/modelo-20-abcde/v1/template.png', TRUE),
    ('00000000-0000-0000-0000-000000000050', 'Modelo 50 Questões (A-D)', 50, 4, 1, 'templates/modelo-50-abcd/v1/template.png', TRUE),
    ('00000000-0000-0000-0000-000000000051', 'Modelo 50 Questões (A-E)', 50, 5, 1, 'templates/modelo-50-abcde/v1/template.png', TRUE),
    ('00000000-0000-0000-0000-000000000100', 'Modelo 100 Questões (A-D)', 100, 4, 1, 'templates/modelo-100-abcd/v1/template.png', TRUE),
    ('00000000-0000-0000-0000-000000000101', 'Modelo 100 Questões (A-E)', 100, 5, 1, 'templates/modelo-100-abcde/v1/template.png', TRUE);

-- =============================================================================
-- PLANS
-- =============================================================================

INSERT INTO plans (id, monthly_price_cents, monthly_tokens, is_active)
VALUES
    ('free', 0, 50, TRUE),
    ('basic', 2990, 500, TRUE),
    ('pro', 7990, 2000, TRUE),
    ('enterprise', 19990, 10000, TRUE);
