# ClaimTrace

ClaimTrace is a reproducible synthetic insurance-claims investigation platform. It links claimants, policies, incidents, providers, invoices, payments, and relationship edges so an operations or risk analyst can find suspicious networks, inspect the evidence, and record a decision.

This project uses synthetic data only. It is a local demonstration and evaluation system, not a production fraud decisioning service.

## What the project does

ClaimTrace implements this workflow:

```text
Generate master data
        ↓
Generate linked claims, incidents, invoices, and payments
        ↓
Inject documented suspicious and benign patterns
        ↓
Validate keys, dates, enums, amounts, and lifecycle history
        ↓
Calculate explainable fraud indicators and investigation scores
        ↓
Compare detections with a separate ground-truth file
        ↓
Review cases in the analyst dashboard
```

The system deliberately includes normal repeat claims and shared households so that a shared address alone is not treated as proof of fraud.

## Features

- Deterministic synthetic data generation using a fixed seed
- Starter and full benchmark scales
- SQLite persistence with explicit investigation event history
- CSV and JSON exports for every domain table
- Separate ground truth that is not served to the analyst UI
- Explainable rule-based indicators with evidence JSON
- Missing-policy, overpayment, duplicate-invoice, shared-contact, timing, and repeated-narrative scenarios
- Relationship/network exploration API and dashboard
- Validation report and evaluation metrics
- SQL `INSERT` seed export alongside the schema
- Same-seed reproducibility checks
- Local `.env` configuration for backend and frontend runtime settings

## Technology

- Python 3.10+
- SQLite
- FastAPI and Uvicorn
- React and Vite
- Plain CSS using the Paper Brutalist UI design system

No external or personal data is downloaded. All people, providers, addresses, claims, and payment values are generated locally.

## Quick start

From the repository root, install dependencies and configure the local environment:

```bash
cp .env.example .env
cp web/.env.example web/.env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd web && npm install && cd ..
```

Generate, validate, detect, and evaluate the full benchmark:

```bash
python3 -m claimtrace generate --seed 20261022 --scale full
python3 -m claimtrace validate
python3 -m claimtrace detect
python3 -m claimtrace evaluate
```

Start the backend in one terminal:

```bash
uvicorn claimtrace.api:app --reload --port 8000
```

Start the dashboard in a second terminal:

```bash
cd web
npm run dev
```

Open `http://localhost:5173` for the dashboard or `http://localhost:8000/docs` for the API documentation.

## Requirements

Install:

- Python 3.10 or newer
- Node.js 18 or newer
- npm

## Installation

From the repository root:

```bash
cd /home/mritunjay/Desktop/ClaimTrace
```

Create and activate a Python virtual environment if desired:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd web
npm install
cd ..
```

## Environment configuration

The backend reads `.env` from the repository root. The frontend reads `web/.env` through Vite.

Copy the examples if the files do not already exist:

```bash
cp .env.example .env
cp web/.env.example web/.env
```

Backend `.env` values:

```dotenv
CLAIMTRACE_DATA_DIR=./data
CLAIMTRACE_DB_PATH=./data/claimtrace.db
CLAIMTRACE_SEED=20261022
CLAIMTRACE_SCALE=full
CLAIMTRACE_CORS_ORIGINS=http://localhost:5173
```

Frontend `web/.env`:

```dotenv
VITE_API_URL=http://localhost:8000/api
```

The frontend value is intentionally not a secret. Vite exposes every `VITE_*` variable to browser JavaScript, so never put passwords, private keys, database credentials, or API secrets in `web/.env`.

`.env` and `web/.env` are ignored by Git. The committed `.env.example` files contain safe local defaults.

Generated databases, exports, validation output, build artifacts, virtual environments, caches, and logs are also ignored by Git. Run the generator after cloning to recreate the `data/` directory.

## Generate the dataset

Generate the full benchmark:

```bash
python3 -m claimtrace generate --seed 20261022 --scale full
```

This creates:

| Entity | Full volume |
|---|---:|
| Claimants | 2,000 |
| Policies | 2,000 |
| Claims | 5,000 |
| Incidents | 5,000 |
| Providers | 500 |
| Claim-provider links | 5,000 |
| Invoices | 5,000 |
| Payments | 5,000 |
| Relationship edges | 8,000 |

Generate a smaller dataset for quick development:

```bash
python3 -m claimtrace generate --seed 20261022 --scale starter
```

The starter scale uses 120 claimants, 250 claims, 45 providers, and 400 relationship edges. Both scales use the same generation logic.

The generator creates parent records first, then dependent records. It keeps the deliberately invalid policy reference as a labelled exception rather than silently changing unrelated rows.

## Run the pipeline

Run each stage explicitly:

```bash
python3 -m claimtrace generate --seed 20261022 --scale full
python3 -m claimtrace validate
python3 -m claimtrace detect
python3 -m claimtrace evaluate
```

What each command does:

### `generate`

Creates the SQLite database, CSV/JSON table exports, ground truth, manifest, and source manifest.

### `validate`

Checks:

- Table presence and row counts
- Primary-key uniqueness
- Foreign-key integrity for normal relationships
- The expected missing-policy exception
- Allowed enum values
- Incident/filed date ordering
- Non-negative monetary amounts
- Payment/invoice reconciliation
- Duplicate invoice-group labelling
- Investigation lifecycle transitions

The result is printed and written to:

```text
data/validation_summary.json
```

The missing policy is intentionally reported as an expected exception, not as an accidental orphan.

### `detect`

Calculates fraud indicators from visible source data and creates investigations. Current indicators include:

- `missing_policy`
- `payment_over_approved`
- `duplicate_invoice`
- `shared_contact_cluster`
- `unusual_timing`
- `repeated_narrative`
- `provider_concentration`

Claim status is derived from source records: claims with a settled payment and no injected exception become `PAID`; claims with an exception become `REVIEW`.

Each indicator contains a score, severity, explanation, and evidence JSON. Ground truth is not loaded by the detector.

### `evaluate`

Compares investigations with `data/ground_truth.csv` and reports:

- Precision
- Recall
- False-positive rate
- False-negative rate
- Precision/recall at top 10 and top 100
- Per-issue recall
- Relationship ground-truth count
- Number of claims containing relationship evidence

## Domain model

```text
Claimant 1 ─── N Policy
Claimant 1 ─── N Incident
Policy   1 ─── N Claim
Incident 1 ─── 1 Claim
Claim    N ─── M Provider       through claim_providers
Claim    1 ─── N Invoice
Invoice  1 ─── N Payment
Entity   N ─── M Entity         through relationship_edges
Claim    1 ─── N FraudIndicator
Claim    0 ─── 1 Investigation
Investigation 1 ─── N InvestigationEvent
```

The canonical schema is in [schema.sql](schema.sql). The runtime schema is applied by [db.py](claimtrace/db.py). Field definitions and lifecycle/cardinality rules are documented in [data_dictionary.md](data_dictionary.md).

## ID conventions

IDs are immutable and zero-padded:

```text
CLT-2026-000001       claimant
POL-2026-000001       policy
CLM-2026-000001       claim
INC-2026-000001       incident
PRV-000001            provider
INV-PRV-PRV-000001-000001 invoice
PAY-2026-000001       payment
RE-2026-000001        relationship edge
FI-CLM-2026-000001-*  fraud indicator
INVG-2026-000001      investigation
```

`CLT` is used for claimants so it cannot be confused with `CLM` claims. The original brief used `CLM` in both contexts; this project documents the distinction explicitly.

## Controlled scenarios

The generator creates valid baseline data and then injects labelled cases:

| Scenario | Example treatment |
|---|---|
| Missing policy | Claim keeps `POL-2026-999999` and `issue_type=missing_policy`. |
| Payment over approval | Payment amount is greater than the claim approval amount. |
| Duplicate invoice | Two claims share `DUP-GROUP-001`. |
| Repeated narrative | Five claims share a deliberately repeated incident narrative. |
| Shared contact | Five claimants share a synthetic phone number. |
| Unusual timing | Five incidents occur on the same planted date. |
| Missing relationship edge | The planted relationship is recorded in ground truth but omitted from visible edges. |
| Benign shared household | Multiple normal claimants share household/address patterns. |

Ground truth is stored separately in:

```text
data/ground_truth.csv
```

It is never passed to detection as an input feature and is not exposed by the normal API.

## Generated files

After generation, the important outputs are:

```text
data/
├── claimtrace.db
├── ground_truth.csv
├── manifest.json
├── validation_summary.json
└── exports/
    ├── claimants.csv / claimants.json
    ├── policies.csv / policies.json
    ├── claims.csv / claims.json
    ├── incidents.csv / incidents.json
    ├── providers.csv / providers.json
    ├── claim_providers.csv / claim_providers.json
    ├── invoices.csv / invoices.json
    ├── payments.csv / payments.json
    ├── relationship_edges.csv / relationship_edges.json
    ├── fraud_indicators.csv / fraud_indicators.json
    ├── investigations.csv / investigations.json
    ├── investigation_events.csv / investigation_events.json
    └── source_manifest.json
```

The source manifest records that the files are synthetic, lists each table, and records row counts and export filenames.

## Start the backend API

From the repository root:

```bash
uvicorn claimtrace.api:app --reload --port 8000
```

Open the interactive API documentation at:

```text
http://localhost:8000/docs
```

Available endpoints include:

```text
GET  /api/metrics
GET  /api/validation
GET  /api/evaluation
GET  /api/investigations
GET  /api/investigations/{id}
GET  /api/investigations/{id}/events
PATCH /api/investigations/{id}
GET  /api/entities/{type}/{id}
GET  /api/entities/{type}/{id}/network
```

Supported entity types are `claimant`, `policy`, `claim`, `incident`, `provider`, `invoice`, and `payment`.

Investigation status transitions are enforced:

```text
NEW → REVIEWING
REVIEWING → ESCALATED or CLEARED
ESCALATED → CONFIRMED or CLEARED
```

Every update creates an `investigation_events` record.

## Start the dashboard

In a second terminal:

```bash
cd web
npm run dev
```

Open:

```text
http://localhost:5173
```

The dashboard contains:

- Queue: ranked investigations, filtering, search, evidence, and decisions
- Network Explorer: inspect claimant/provider relationships and linked claims
- Validation Report: inspect integrity checks and evaluation metrics

The dashboard gets its API base URL from `web/.env` using `VITE_API_URL`.

## Reproducibility

The generator uses a fixed seed. To verify reproducibility:

```bash
python3 -m claimtrace generate --seed 20261022 --scale full
sha256sum data/claimtrace.db data/ground_truth.csv data/manifest.json

python3 -m claimtrace generate --seed 20261022 --scale full
sha256sum data/claimtrace.db data/ground_truth.csv data/manifest.json
```

The generated SQLite database, ground truth, manifest, and table exports should have identical checksums across both runs.

## Tests and build verification

Run backend tests:

```bash
python3 -m unittest discover -s tests -v
```

Build the frontend:

```bash
cd web
npm run build
```

The tests cover generation, ID conventions, detection, validation, exports, and planted scenarios.

## Troubleshooting

### `ModuleNotFoundError: fastapi`

Activate the virtual environment and install dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Dashboard says it cannot reach the API

Confirm the backend is running on port 8000 and that `web/.env` contains:

```dotenv
VITE_API_URL=http://localhost:8000/api
```

Restart Vite after changing `.env` values.

### No investigations appear

Regenerate and run detection:

```bash
python3 -m claimtrace generate --seed 20261022 --scale full
python3 -m claimtrace detect
```

### Validation reports the missing policy exception

That is intentional. The exception is required by the specification and is represented by `issue_type=missing_policy` and a corresponding ground-truth row.

## Data safety and provenance

This repository generates synthetic records locally and does not use external data. No access controls are bypassed and no confidential or personal data is collected. If external reference data is added later, record its URL, version, retrieval date, license, attribution, transformations, and discarded fields in the source manifest before using it.
