-- db/schema_auth.sql
-- Rubis Intelligence — Authentication Tables
-- Run once on a fresh database, or apply as a migration

-- ─────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                   SERIAL PRIMARY KEY,
    email                VARCHAR(255) NOT NULL UNIQUE,
    password_hash        TEXT         NOT NULL,
    full_name            VARCHAR(120) NOT NULL,

    -- role: admin | analyst | branch_manager | viewer
    role                 VARCHAR(30)  NOT NULL DEFAULT 'viewer',

    -- optional: which branch a branch_manager belongs to
    branch               VARCHAR(60),

    is_verified          BOOLEAN      NOT NULL DEFAULT FALSE,
    verification_token   TEXT,
    reset_token          TEXT,
    reset_token_expires  TIMESTAMP,
    created_at           TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Fast lookup by email (used on every login)
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
-- Fast lookup by verification / reset token
CREATE INDEX IF NOT EXISTS idx_users_verification_token ON users (verification_token) WHERE verification_token IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_reset_token        ON users (reset_token)        WHERE reset_token IS NOT NULL;

-- ─────────────────────────────────────────
-- AUTH LOGS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth_logs (
    id          BIGSERIAL    PRIMARY KEY,
    email       VARCHAR(255),
    action      VARCHAR(60)  NOT NULL,  -- login, logout, register, password_reset_request, password_reset
    status      VARCHAR(20)  NOT NULL,  -- success, failed
    ip_address  VARCHAR(45),            -- supports IPv4 and IPv6
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Index for querying recent events by email (anomaly detection)
CREATE INDEX IF NOT EXISTS idx_auth_logs_email      ON auth_logs (email);
CREATE INDEX IF NOT EXISTS idx_auth_logs_created_at ON auth_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_auth_logs_action     ON auth_logs (action, status);

-- ─────────────────────────────────────────
-- AUTO-UPDATE updated_at ON users
-- ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─────────────────────────────────────────
-- SEED: default admin user
-- Password: Admin@1234  (change immediately after first login)
-- Hash generated with: python -c "from passlib.context import CryptContext; print(CryptContext(['bcrypt']).hash('Admin@1234'))"
-- ─────────────────────────────────────────
INSERT INTO users (email, password_hash, full_name, role, is_verified)
VALUES (
    'admin@rubiskenya.com',
    '$2b$12$REPLACE_WITH_REAL_BCRYPT_HASH',
    'System Administrator',
    'admin',
    TRUE
)
ON CONFLICT (email) DO NOTHING;
