-- ============================================================
-- BRAHMO Rules Engine — Database Schema
-- Run this FIRST in the Supabase SQL Editor, then seed.sql
-- ============================================================

DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS edges CASCADE;
DROP TABLE IF EXISTS knowledge_nodes CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS hierarchy_levels CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

-- Organizations
CREATE TABLE organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    segment TEXT NOT NULL CHECK (segment IN ('hospital', 'law_firm', 'software')),
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Hierarchy Levels (15-level DAG structure)
CREATE TABLE hierarchy_levels (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    level_number INTEGER NOT NULL CHECK (level_number BETWEEN 1 AND 15),
    level_name TEXT NOT NULL,
    department TEXT,           -- NULL for cross-department levels
    parent_ids TEXT[] DEFAULT '{}',  -- DAG: multiple parents allowed
    zone INTEGER NOT NULL DEFAULT 1 CHECK (zone IN (1, 2, 3)),
    -- Zone 1 = Addressed (dept-specific), Zone 2 = Global, Zone 3 = Floating
    created_at TIMESTAMPTZ DEFAULT NOW()
    -- NOTE: the original spec declared UNIQUE(org_id, level_number, department)
    -- here. It is incompatible with the seed data and with the domain: a
    -- department legitimately has SEVERAL units at the same depth. Orthopaedics
    -- has three at level 8 -- Ortho General, Ortho TKR Unit and the Post-TKR
    -- Protocol Area -- so that constraint rejects seed.sql on load. The id
    -- primary key already guarantees uniqueness; enforcing one unit per
    -- (department, depth) would forbid the very multi-unit, multi-parent shape
    -- this DAG exists to model. Asserted by test_seed_integrity.py.
);

-- Knowledge Nodes
CREATE TABLE knowledge_nodes (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    hierarchy_level_id TEXT NOT NULL REFERENCES hierarchy_levels(id),
    type TEXT NOT NULL CHECK (type IN ('CONSTRAINT', 'DECISION', 'ANTI_PATTERN', 'FACT')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    importance DECIMAL(3,2) NOT NULL CHECK (importance BETWEEN 0.0 AND 1.0),
    zone INTEGER NOT NULL DEFAULT 1 CHECK (zone IN (1, 2, 3)),
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN (
        'ACTIVE', 'REVIEW_REQUIRED', 'SUPERSEDED', 'EXPIRED', 'LEGAL_HOLD'
    )),
    derivability_score DECIMAL(3,2) NOT NULL DEFAULT 0.0 CHECK (derivability_score BETWEEN 0.0 AND 1.0),
    compliance_tags TEXT[] DEFAULT '{}',  -- e.g., {'MNPI', 'PHI', 'CONFIDENTIAL'}
    valid_until TIMESTAMPTZ,             -- NULL = no expiry
    superseded_by TEXT REFERENCES knowledge_nodes(id),
    department TEXT,                      -- which department this node belongs to
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Edges (typed relationships between nodes)
CREATE TABLE edges (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    source_id TEXT NOT NULL REFERENCES knowledge_nodes(id),
    target_id TEXT NOT NULL REFERENCES knowledge_nodes(id),
    edge_type TEXT NOT NULL CHECK (edge_type IN (
        'SUPPORTS', 'CONTRADICTS', 'SUPERSEDES', 'DERIVED_FROM', 'REQUIRES'
    )),
    confidence DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('ADMIN', 'HOD', 'EDITOR', 'VIEWER', 'QUALITY', 'AUDITOR')),
    department TEXT NOT NULL,
    ceiling_level INTEGER NOT NULL CHECK (ceiling_level BETWEEN 1 AND 15),
    write_ceiling INTEGER,  -- NULL for VIEWER (no write)
    compliance_clearance TEXT[] DEFAULT '{}',  -- e.g., {'MNPI'} for auditors
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log (append-only)
CREATE TABLE audit_log (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    node_id TEXT REFERENCES knowledge_nodes(id),
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    actor_id TEXT REFERENCES users(id),
    org_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_nodes_org ON knowledge_nodes(org_id);
CREATE INDEX idx_nodes_zone ON knowledge_nodes(zone);
CREATE INDEX idx_nodes_status ON knowledge_nodes(status);
CREATE INDEX idx_nodes_dept ON knowledge_nodes(department);
CREATE INDEX idx_nodes_hierarchy ON knowledge_nodes(hierarchy_level_id);
CREATE INDEX idx_nodes_compliance ON knowledge_nodes USING GIN(compliance_tags);
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_hierarchy_org ON hierarchy_levels(org_id);
CREATE INDEX idx_hierarchy_parent ON hierarchy_levels USING GIN(parent_ids);
