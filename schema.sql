-- Canonical schema is maintained in claimtrace/db.py and applied with SQLite.
-- This seed-compatible entrypoint can be run with: sqlite3 data/claimtrace.db < schema.sql
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS claimants (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL, address TEXT NOT NULL, household_id TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS policies (id TEXT PRIMARY KEY, claimant_id TEXT NOT NULL REFERENCES claimants(id), policy_type TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL, status TEXT NOT NULL, coverage_limit REAL NOT NULL);
CREATE TABLE IF NOT EXISTS claims (id TEXT PRIMARY KEY, claimant_id TEXT NOT NULL REFERENCES claimants(id), policy_id TEXT NOT NULL, incident_id TEXT NOT NULL REFERENCES incidents(id), filed_date TEXT NOT NULL, approved_amount REAL NOT NULL, status TEXT NOT NULL, issue_type TEXT);
CREATE TABLE IF NOT EXISTS incidents (id TEXT PRIMARY KEY, claimant_id TEXT NOT NULL REFERENCES claimants(id), incident_date TEXT NOT NULL, incident_type TEXT NOT NULL, narrative TEXT NOT NULL, location TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS providers (id TEXT PRIMARY KEY, name TEXT NOT NULL, provider_type TEXT NOT NULL, address TEXT NOT NULL, phone TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS claim_providers (claim_id TEXT NOT NULL REFERENCES claims(id), provider_id TEXT NOT NULL REFERENCES providers(id), role TEXT NOT NULL, PRIMARY KEY(claim_id, provider_id, role));
CREATE TABLE IF NOT EXISTS invoices (id TEXT PRIMARY KEY, claim_id TEXT NOT NULL REFERENCES claims(id), provider_id TEXT NOT NULL REFERENCES providers(id), amount REAL NOT NULL, invoice_date TEXT NOT NULL, duplicate_group TEXT);
CREATE TABLE IF NOT EXISTS payments (id TEXT PRIMARY KEY, claim_id TEXT NOT NULL REFERENCES claims(id), invoice_id TEXT NOT NULL REFERENCES invoices(id), amount REAL NOT NULL, paid_date TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS relationship_edges (id TEXT PRIMARY KEY, source_id TEXT NOT NULL, source_type TEXT NOT NULL, target_id TEXT NOT NULL, target_type TEXT NOT NULL, relationship TEXT NOT NULL, effective_date TEXT NOT NULL, planted INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS fraud_indicators (id TEXT PRIMARY KEY, claim_id TEXT NOT NULL REFERENCES claims(id), indicator_type TEXT NOT NULL, severity TEXT NOT NULL, score REAL NOT NULL, explanation TEXT NOT NULL, evidence_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS investigations (id TEXT PRIMARY KEY, claim_id TEXT NOT NULL UNIQUE REFERENCES claims(id), risk_score REAL NOT NULL, severity TEXT NOT NULL, status TEXT NOT NULL, summary TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS investigation_events (id TEXT PRIMARY KEY, investigation_id TEXT NOT NULL REFERENCES investigations(id), from_status TEXT, to_status TEXT NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL);
