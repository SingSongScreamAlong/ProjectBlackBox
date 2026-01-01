-- Migration: Add V1 Entitlement Fields
-- Description: Adds scope, billing_period, series_addons_count, and external_event_id to entitlements

ALTER TABLE entitlements
ADD COLUMN IF NOT EXISTS scope VARCHAR(10) DEFAULT 'user',
ADD COLUMN IF NOT EXISTS billing_period VARCHAR(10) DEFAULT 'monthly',
ADD COLUMN IF NOT EXISTS series_addons_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS external_event_id VARCHAR(255);

-- Make external_event_id unique to prevent duplicate processing of the same webhook event
-- (Nullable unique constraint: multiple nulls allowed, but non-nulls must be unique)
CREATE UNIQUE INDEX IF NOT EXISTS idx_entitlements_external_event_id 
ON entitlements(external_event_id) 
WHERE external_event_id IS NOT NULL;

-- Track processed webhook events separately if needed, but the column above helps coverage.
-- We also want to ensure we track the original event ID if we want strict idempotency log.
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    topic VARCHAR(50),
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'processed'
);
