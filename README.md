# IndusIntel AI

**AI-Powered Product Intelligence for Industrial Commerce**

Turns fragmented, unstructured industrial product information (PDF
datasheets, CSVs, free text) into structured, validated, and enriched
commerce-ready product data — with full source traceability and confidence
scoring on every field.

> **Status: Day 2 of 5 complete.** Document ingestion, AI extraction, and
> AI structuring into the standardized product schema all work end-to-end.
> Enrichment and validation (confidence-driven quality scoring, PASS/
> WARNING/FAIL checks, conflict detection) land on Day 3. See
> [`docs/architecture.md`](docs/architecture.md) for the full pipeline
> design and what's implemented vs. planned.

## Problem

Industrial manufacturers have product information scattered across PDFs,
technical datasheets, catalogs, images, spreadsheets, and free-text
descriptions. Manually converting this into accurate, structured,
commerce-ready product data is slow and error-prone.

## Solution

**Extract → Structure → Enrich → Validate → Trace.**

1. Upload a product PDF/datasheet, CSV, or raw text.
2. AI extracts product information and preserves source references.
3. Information is converted into a standardized, category-aware product
   schema.
4. Missing fields are identified.
5. The product is enriched using trusted knowledge — clearly labeled as
   `AI Enrichment`, never presented as manufacturer-confirmed data.
6. Specifications are validated (unit checks, conflicts, impossible values)
   and marked `PASS` / `WARNING` / `FAIL`.
7. Every important field shows its **source, confidence score, and
   validation status**.
8. Users review/edit the result and export it as JSON, CSV, or a
   commerce-ready product sheet.
9. A dashboard shows a transparent **IndusIntel Data Quality Score**.

## Features

- [x] PDF / CSV / manual text ingestion with page-level source preservation
- [x] Product catalog, dashboard, and upload UI
- [x] Category-aware, extensible product schema (pumps, motors, valves,
      sensors, bearings, compressors, ...)
- [x] Demo dataset — 5 realistic industrial products, load-instantly for
      evaluators who don't want to upload their own file
- [x] AI Extraction Agent — pulls only explicitly-stated facts + page refs
- [x] AI Structuring Agent — converts facts into the standardized,
      category-aware product schema (strict Pydantic validation, no
      arbitrary AI output ever persisted)
- [x] Deterministic unit/category/field-name normalization (Stage 2), kept
      outside the LLM
- [x] Product Intelligence page — spec table with confidence, source,
      status, and a click-through source detail panel
- [ ] AI enrichment with explicit `AI Enriched` labeling (Day 3)
- [ ] Deterministic + AI validation rules (PASS/WARNING/FAIL), conflict
      detection, full weighted quality score (Day 3)
- [ ] Export (JSON/CSV/product sheet), analytics charts, deployment (Day 4)

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full diagram and
pipeline stage breakdown.

## AI Pipeline

Specialized, single-purpose prompts/agents rather than one giant system
prompt:

- **Extraction Agent** (`backend/app/services/agents.py`) — reads raw
  document text and pulls out only facts explicitly stated, with page
  references. Never infers or fills gaps.
- **Structuring Agent** — converts those facts into the standardized
  `ProductIntelligenceSchema`, strictly validated with Pydantic. A
  deterministic normalization pass (`backend/app/services/normalize.py`)
  runs first — unit spelling (`10 Bar` → `10 bar`), category matching, and
  field-name snake_casing are handled in plain code, not left to the LLM,
  per the spec's "keep deterministic rules outside the LLM" principle.
- **Enrichment, Validation, Explanation agents** — Day 3.

All agents run behind a swappable `AIProvider` abstraction
(`backend/app/services/ai_provider.py`) so the LLM backend (Claude or
Gemini) can be changed via one `.env` variable without touching the rest of
the app. `complete_json()` strips markdown fences and repairs common
formatting issues before parsing — but if the model still doesn't return
valid JSON, the request fails loudly (`AgentError` → HTTP 502) rather than
silently persisting garbage.

## Tech Stack

**Frontend:** Next.js (App Router) · TypeScript · Tailwind CSS · Recharts ·
lucide-react

**Backend:** Python · FastAPI · Pydantic · SQLAlchemy

**AI:** Configurable via `AIProvider` — Anthropic Claude or Gemini

**Database:** PostgreSQL in production, SQLite for zero-setup local dev

**Document processing:** PyMuPDF, pdfplumber, pandas

## Project Structure

```
indusintel-ai/
├── frontend/            Next.js app (dashboard, upload, products, analytics)
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI entrypoint
│   │   ├── config.py          Settings from .env
│   │   ├── database.py        SQLAlchemy engine/session
│   │   ├── models.py          Product, ProductSpecification, Document, ValidationResult
│   │   ├── schemas.py         Pydantic request/response + Product Intelligence Schema
│   │   ├── routers/           health.py, products.py
│   │   └── services/
│   │       ├── pdf_extractor.py    Stage 1 — PDF/CSV/text extraction
│   │       ├── ai_provider.py      Anthropic/Gemini abstraction + JSON-mode helper
│   │       ├── agents.py           Extraction Agent + Structuring Agent
│   │       ├── normalize.py        Deterministic unit/category/field normalization
│   │       └── schema_registry.py  Category-aware expected spec fields
│   ├── seed_demo_data.py      Loads 5 demo products
│   └── sample_data/           Sample datasheet text for 2 demo products
├── docs/
│   └── architecture.md
└── README.md
```

## Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- (Optional for local dev) PostgreSQL — SQLite is used by default

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit if using Postgres / adding API keys
python seed_demo_data.py        # loads 5 demo products
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

App available at `http://localhost:3000`.

## Environment Variables

**`backend/.env`**

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./indusintel.db` |
| `AI_PROVIDER` | `anthropic` or `gemini` | `anthropic` |
| `ANTHROPIC_API_KEY` | Claude API key (Day 2+) | — |
| `GEMINI_API_KEY` | Gemini API key (Day 2+) | — |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |

**`frontend/.env.local`**

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend base URL | `http://localhost:8000` |

## API Documentation

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/products` | List products (filter by `category`, `search`) |
| POST | `/api/products` | Create a product |
| GET | `/api/products/{id}` | Get product detail (specs, documents, validation) |
| POST | `/api/products/upload` | Upload a file or manual text → extracted text + draft product |
| GET | `/api/products/dashboard/summary` | Dashboard metrics |
| GET | `/api/products/{id}/specifications` | Product specification rows |
| GET | `/api/products/{id}/validation` | Validation results |
| POST | `/api/products/{id}/process` | Run Extraction + Structuring agents over the product's documents, persist specifications |
| POST | `/api/products/{id}/enrich` | Run enrichment *(Day 3 milestone)* |
| POST | `/api/products/{id}/validate` | Run validation *(Day 3 milestone)* |
| GET | `/api/products/{id}/export/json` | Export JSON *(Day 4 milestone)* |
| GET | `/api/products/{id}/export/csv` | Export CSV *(Day 4 milestone)* |

Full interactive docs (Swagger UI) at `/docs` once the backend is running.

## Demo

1. Run backend + frontend as above.
2. Add your `ANTHROPIC_API_KEY` (or `GEMINI_API_KEY` + set `AI_PROVIDER=gemini`)
   to `backend/.env` and restart the backend — the Structuring Agent needs
   it to run. Text/PDF upload and extraction work without a key; AI
   structuring does not.
3. Open `http://localhost:3000`.
4. Go to **Upload** → click **Load Demo Product** → **Run Extraction**.
5. Click **View Product & Run AI Structuring** → **Run AI Structuring**.
6. The Product Intelligence page fills in with a specifications table —
   click any row to see its source, confidence, and validation status.
7. Or upload one of the sample datasheets in `backend/sample_data/`.

## Screenshots

_Add screenshots from your running instance here before submission — the
hackathon rules require real, not mocked, UI screenshots._

## Future Scope

Vision-language extraction from product images, knowledge graph, multi-agent
orchestration, ERP/PLM integration, supplier data verification, automated
catalog generation, multilingual product intelligence, human approval
workflows, large-scale batch processing, semantic product search, duplicate
product detection.
