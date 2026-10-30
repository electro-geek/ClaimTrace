# ClaimTrace data dictionary

All IDs are required, immutable primary keys. Dates use ISO-8601. Amounts are decimal currency units in USD.

| Entity | Required fields | Allowed values / validation |
|---|---|---|
| Claimant | id, name, email, phone, address, household_id | Email/phone are synthetic; `id` is unique `CLT-2026-######`. |
| Policy | id, claimant_id, policy_type, start_date, end_date, status, coverage_limit | Type: AUTO/HOME/HEALTH; dates ordered; claimant FK valid. |
| Claim | id, claimant_id, policy_id, incident_id, filed_date, approved_amount, status | Status: PAID/REVIEW, derived from payment existence and labelled source exceptions; amount non-negative; incident precedes filing. `policy_id` is deliberately validated by the validator rather than enforced so missing-policy exceptions survive. |
| Incident | id, claimant_id, incident_date, incident_type, narrative, location | Type: collision/water/theft/injury; claimant FK valid. |
| Provider | id, name, provider_type, address, phone | Type: repairer/medical/assessor; ID is `PRV-######`. |
| Invoice | id, claim_id, provider_id, amount, invoice_date, duplicate_group | Amount non-negative; claim/provider FKs valid. Duplicate groups are explicit labels. |
| Payment | id, claim_id, invoice_id, amount, paid_date, status | Status: settled; invoice/claim FKs valid; amount reconciles to source records. |
| RelationshipEdge | id, source_id/type, target_id/type, relationship, effective_date | Relationship: shared_contact/household/prior_claim; bridge supports N:M links. |
| FraudIndicator | id, claim_id, indicator_type, severity, score, explanation, evidence_json | Severity: medium/high/critical; score derived from source evidence. |
| Investigation | id, claim_id, risk_score, severity, status, summary, timestamps | Status lifecycle: NEW → REVIEWING → ESCALATED/ CLEARED → CONFIRMED. |

The generator creates normal shared households and repeat activity before injecting controlled cases. Ground truth is kept in `data/ground_truth.csv`, never used as a detector feature, and is only consumed by evaluation.

## Cardinality and lifecycle

| Relationship | Cardinality | Optionality / effective dates |
|---|---|---|
| Claimant → Policy | 1:N | Required claimant; policy active between start/end dates. |
| Policy → Claim | 1:N | Required for normal claims; missing-policy exception is retained with `issue_type`. |
| Claimant → Incident | 1:N | Required claimant; incident date precedes filing date. |
| Claim → Incident | 1:1 | Required incident for every generated claim. |
| Claim ↔ Provider | N:M | Implemented through `claim_providers`; role is required. |
| Claim → Invoice | 1:N | Required claim/provider; invoice date follows filing date. |
| Invoice → Payment | 1:N | Optional until payment; payment references invoice and claim. |
| Entity ↔ Entity | N:M | Implemented through `relationship_edges`; effective date is required. |
| Claim → FraudIndicator | 1:N | Optional; indicators are derived from source evidence. |
| Claim → Investigation | 0:1 | Created only when indicators exist; status history is append-only in `investigation_events`. |

Generated exports are in `data/exports/` as one CSV and one JSON file per table. `validation_summary.json`, `manifest.json`, and `source_manifest.json` describe the run and provenance.
