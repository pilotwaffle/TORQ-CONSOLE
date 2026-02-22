-- ============================================
-- TORQ Console: Seed Learning Policy Data
-- Adds initial policy data for testing
-- ============================================

-- Step 1: Create the policy version first (required by FK)
INSERT INTO policy_versions (
    id,
    policy_id,
    version,
    policy_name,
    policy_type,
    content,
    content_hash,
    status,
    created_by,
    approved_by,
    approved_at
) VALUES (
    uuid_generate_v4(),
    'prince_flowers_system',
    1,
    'Prince Flowers System Prompt',
    'agent_prompt',
    'You are Prince Flowers, an action-oriented AI assistant.',
    md5('Prince Flowers System Prompt'),
    'active',
    'system',
    'system',
    NOW()
)
ON CONFLICT DO NOTHING;

-- Step 2: Now insert into policy_active using the version we just created
INSERT INTO policy_active (policy_id, active_version_id, active_version, activated_by)
VALUES (
    'prince_flowers_system',
    (SELECT id FROM policy_versions WHERE policy_id = 'prince_flowers_system' AND version = 1),
    1,
    'system'
)
ON CONFLICT (policy_id) DO UPDATE SET
    active_version_id = (SELECT id FROM policy_versions WHERE policy_id = 'prince_flowers_system' AND version = 1),
    activated_at = NOW();

-- Verify the seed data
SELECT 'policy_active' as table_name, policy_id, active_version, activated_by
FROM policy_active;

SELECT 'policy_versions' as table_name, policy_id, version, policy_name, status
FROM policy_versions
LIMIT 5;
