-- StyleSync Design System Database Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Scraped sites table
CREATE TABLE IF NOT EXISTS scraped_sites (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    favicon_url TEXT,
    raw_html_snapshot TEXT,
    extraction_status VARCHAR(20) DEFAULT 'pending' CHECK (extraction_status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Design tokens table (JSONB for flexibility)
CREATE TABLE IF NOT EXISTS design_tokens (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES scraped_sites(id) ON DELETE CASCADE,
    colors JSONB DEFAULT '{}',
    typography JSONB DEFAULT '{}',
    spacing JSONB DEFAULT '{}',
    border_radius JSONB DEFAULT '{}',
    shadows JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locked tokens junction table (tracks which tokens are frozen per site/session)
CREATE TABLE IF NOT EXISTS locked_tokens (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES scraped_sites(id) ON DELETE CASCADE,
    token_category VARCHAR(50) NOT NULL,
    token_key VARCHAR(100) NOT NULL,
    token_value TEXT NOT NULL,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, token_category, token_key)
);

-- Version history table (audit log of token changes)
CREATE TABLE IF NOT EXISTS version_history (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES scraped_sites(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL DEFAULT 1,
    token_category VARCHAR(50),
    token_key VARCHAR(100),
    before_value TEXT,
    after_value TEXT,
    change_type VARCHAR(20) DEFAULT 'edit' CHECK (change_type IN ('edit', 'lock', 'unlock', 'reset', 'import')),
    changes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_design_tokens_site_id ON design_tokens(site_id);
CREATE INDEX IF NOT EXISTS idx_locked_tokens_site_id ON locked_tokens(site_id);
CREATE INDEX IF NOT EXISTS idx_version_history_site_id ON version_history(site_id);
CREATE INDEX IF NOT EXISTS idx_scraped_sites_url ON scraped_sites(url);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_scraped_sites_updated_at') THEN
        CREATE TRIGGER update_scraped_sites_updated_at
            BEFORE UPDATE ON scraped_sites
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_design_tokens_updated_at') THEN
        CREATE TRIGGER update_design_tokens_updated_at
            BEFORE UPDATE ON design_tokens
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END;
$$;
