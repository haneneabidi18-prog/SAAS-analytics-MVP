-- ═══════════════════════════════════════════════════════════════════════════
-- Migration : Organisations & Gestion d'équipe (licences par seat)
-- À exécuter dans Supabase > SQL Editor
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. Table des organisations (clients ISP)
CREATE TABLE IF NOT EXISTS organizations (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                 TEXT NOT NULL,
    plan_tier            TEXT NOT NULL DEFAULT 'starter',  -- starter | business | enterprise | enterprise_plus
    max_users            INTEGER NOT NULL DEFAULT 5,
    status               TEXT NOT NULL DEFAULT 'active',    -- active | suspended
    contact_email        TEXT,
    notes                TEXT,
    custom_monthly_price NUMERIC,  -- tarif negocie (palier enterprise_plus)
    created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Si la table existait deja avant cette migration :
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS custom_monthly_price NUMERIC;

ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all organizations" ON organizations
    FOR ALL USING (true) WITH CHECK (true);

-- 2. Ajout des colonnes a la table users existante
ALTER TABLE users ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id);
ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'member';
-- role possibles : 'super_admin' (ABIDSON), 'org_admin' (admin client ISP), 'member'

-- 3. Te definir comme super admin (remplace 'hanene' par ton username)
UPDATE users SET role = 'super_admin' WHERE username = 'hanene';

-- 4. (Optionnel) Verifier la structure
-- SELECT username, email, role, org_id, plan FROM users;
-- SELECT * FROM organizations;
