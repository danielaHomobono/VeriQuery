-- ============================================================================
-- FORENSIC DATA GUARDIAN - PostgreSQL Schema
-- ============================================================================
-- This schema stores metadata about user database configurations
-- It does NOT store credentials (those are in Azure Key Vault)
-- ============================================================================

-- Create extension for UUID if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE: user_databases
-- PURPOSE: Store what databases each user has configured
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_databases (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    db_name VARCHAR(255) NOT NULL,
    db_type VARCHAR(50) NOT NULL,  -- 'sqlserver' or 'postgresql'
    display_name VARCHAR(255),
    description TEXT,
    host VARCHAR(255) NOT NULL,
    port INTEGER DEFAULT 5432,
    database_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    -- Unique constraint: user can't have duplicate db_name
    UNIQUE(user_id, db_name),
    
    -- Indexes for fast queries
    INDEX idx_user_databases_user_id (user_id),
    INDEX idx_user_databases_active (user_id, is_active)
);

-- ============================================================================
-- TABLE: user_sessions
-- PURPOSE: Track which database user is currently using
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    active_db_name VARCHAR(255),  -- References user_databases.db_name
    schema_cache JSON,  -- Cached schema to avoid repeated calls
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_user_sessions_user_id (user_id),
    INDEX idx_user_sessions_session_id (session_id),
    INDEX idx_user_sessions_expires (expires_at)
);

-- ============================================================================
-- TABLE: audit_log
-- PURPOSE: Track all database configuration changes
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- 'create', 'update', 'delete', 'select'
    resource_type VARCHAR(50),  -- 'database', 'session'
    resource_id VARCHAR(255),
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Index for audits
    INDEX idx_audit_log_user (user_id),
    INDEX idx_audit_log_created (created_at)
);

-- ============================================================================
-- TRIGGERS: Auto-update updated_at timestamps
-- ============================================================================
DELIMITER $$

CREATE TRIGGER update_user_databases_timestamp
BEFORE UPDATE ON user_databases
FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END$$

CREATE TRIGGER update_user_sessions_timestamp
BEFORE UPDATE ON user_sessions
FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END$$

DELIMITER ;
