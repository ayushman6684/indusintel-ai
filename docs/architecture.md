# Architecture — IndusIntel AI

```
                    ┌──────────────────────┐
                    │      Next.js UI      │
                    │ Dashboard / Upload   │
                    │ Product Intelligence │
                    └──────────┬───────────┘
                               │  REST (JSON / multipart)
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI         │
                    │      REST API        │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
          ┌────────────┐ ┌───────────┐ ┌───────────┐
          │ Document   │ │ AI Engine │ │ Validation│
          │ Processor  │ │ (Day 2+)  │ │ (Day 3+)  │
          └─────┬──────┘ └─────┬─────┘ └─────┬─────┘
                │              │             │
                └──────────────┼─────────────┘
                               ▼
                     ┌──────────────────┐
                     │   PostgreSQL /   │
                     │   SQLite (dev)   │
                     │ Products         │
                     │ Specifications   │
                     │ Documents        │
                     │ ValidationResult │
                     └──────────────────┘
```

## Request flow (Day 1 — implemented)

1. User uploads a PDF/CSV/text file (or pastes raw text) on `/upload`.
2. Frontend sends `multipart/form-data` to `POST /api/products/upload`.
3. FastAPI dispatches to `app/services/pdf_extractor.py`, which detects the
   file type and extracts text (PyMuPDF for PDFs, pandas for CSV, plain
   decode for text). PDF text is tagged per page (`[PAGE N]`) to preserve
   traceability for later stages.
4. A `Product` (draft/processing) and `Document` row are created and the
   extracted text is stored and returned to the UI.
5. On the product page, `POST /api/products/{id}/process` runs the
   Extraction Agent (pulls facts + page refs from the combined document
   text) then the Structuring Agent (converts facts into
   `ProductIntelligenceSchema`, running unit/category/field-name
   normalization first). The result is flattened into `ProductSpecification`
   rows and the parent `Product`'s summary fields are updated; `status`
   becomes `completed` and a provisional `quality_score` (average field
   confidence) is set.

## Pipeline stages (spec Section 5) and where they live

| Stage | Status | Where |
|---|---|---|
| 1. Extract | ✅ Day 1 | `app/services/pdf_extractor.py` |
| 1b. Extraction Agent | ✅ Day 2 | `app/services/agents.py::run_extraction_agent` |
| 2. Normalize | ✅ Day 2 | `app/services/normalize.py` (deterministic, outside the LLM) |
| 3. Structure | ✅ Day 2 | `app/services/agents.py::run_structuring_agent` → `ProductIntelligenceSchema` |
| 4. Enrich | 🔜 Day 3 | Enrichment Agent (`AI_ENRICHED` sourced fields) |
| 5. Validate | 🔜 Day 3 | Validation Agent + deterministic rules (PASS/WARNING/FAIL) |
| 6. Confidence | ✅ Day 2 (partial) | AI-assigned per field, stored on `ProductSpecification`; full weighted quality score is Day 3 |
| 7. Traceability | ✅ Day 2 | `source` / `source_page` on `ProductSpecification`, click-through detail panel in the UI |

The `AIProvider` abstraction (`app/services/ai_provider.py`) is the seam
where Anthropic Claude or Gemini gets wired in for stages 2–7, so the rest
of the app never talks to a specific LLM SDK directly.

## Data model

- **Product** — top-level record (name, code, manufacturer, category,
  quality_score, status).
- **ProductSpecification** — one row per technical field, carrying value,
  normalized_value, unit, confidence, status (PASS/WARNING/FAIL/UNKNOWN),
  source (SOURCE_VERIFIED/AI_ENRICHED/USER_PROVIDED/INFERRED/UNKNOWN), and
  source_page.
- **Document** — an uploaded file and its extracted text, linked to a
  product.
- **ValidationResult** — one row per validation finding (severity, message,
  status), linked to a product.

## Why SQLite for local dev

The MVP targets PostgreSQL in production (`DATABASE_URL` in `.env`), but
defaults to SQLite locally so `npm run dev` / `uvicorn` work with zero
external setup. Switching is a one-line env var change — no code changes
required, since SQLAlchemy abstracts the dialect.
