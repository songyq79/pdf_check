# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> For a full directory tree and a detailed file-by-file functional breakdown (especially the plagiarism subsystem), see [CLAUDE-MAP.md](CLAUDE-MAP.md). This file focuses on commands, conventions, and the things that will trip you up.

## Project Overview

This is a **论文评价检验系统** (Academic Paper Evaluation and Checking System), a full-stack web app with four core academic-paper features plus a full account/billing layer:

1. **智能评价 (Evaluation)** — AI multi-dimensional scoring of a paper (5 weighted dimensions), Word report export with radar chart
2. **论文校对 (Proofread)** — AI spell/grammar/logic checking, output as a Word document with Track Changes markup
3. **模板排版 (Formatter)** — Apply a Word template's styles (built-in or user-uploaded) to a paper via ZIP-level style injection
4. **论文查重 (Plagiarism)** — Chinese (LLM-driven) and English (local FAISS + Semantic Scholar/CORE/PubMed + n-gram + LLM) duplicate-content detection

Supporting systems: **auth** (account/password, SMS, WeChat & Alipay OAuth login, admin approval gate), **billing** (quota/subscription/per-use credits, WeChat Pay & Alipay orders, refunds, invite codes), **admin** (user/order/refund management, local paper-library management).

**Tech Stack:**
- Backend: FastAPI + Python 3.9+, SQLAlchemy (SQLite for dev / MySQL for prod)
- Async tasks: Celery + Redis (4 dedicated queues: evaluation/proofread/formatter/plagiarism)
- Frontend: Vue 3 + Vite + Element Plus + Pinia + ECharts
- AI: Alibaba Bailian (通义千问, primary) with automatic fallback to DeepSeek — see `app/core/ai_client.py`
- Document processing: python-docx, pdfplumber (PDF), LibreOffice headless (WPS docx normalization)
- Plagiarism-specific: sentence-transformers (semantic embeddings), faiss-cpu (local vector index), langdetect, simhash
- Payments/Comms: WeChat Pay, Alipay, Aliyun SMS

## Development Commands

### Backend

```bash
cd backend

# Setup (first time)
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate         # Linux/Mac
pip install -r requirements.txt

# Configure: copy .env.example to .env and set at least one AI key
copy .env.example .env             # Windows; `cp` on Linux/Mac
# Edit backend/.env: BAILIAN_API_KEY and/or DEEPSEEK_API_KEY

# Run dev server (creates SQLite DB + admin user automatically on first boot)
python -m app.main
# Or with uvicorn directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run a Celery worker (required for evaluation/proofread/formatter/plagiarism —
# these are all async; without a worker, tasks submit but never complete)
celery -A app.workers.celery_app worker --loglevel=info --pool=threads -Q evaluation,proofread,formatter,plagiarism,default

# Diagnose Redis/Celery/FastAPI connectivity
python check_services.py

# Run tests
pytest
pytest tests/test_billing.py -v
pytest tests/test_plagiarism_english/ -v
```

**Backend runs at:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

Redis is **required** even for local dev (Celery broker/result backend). Default `.env.example` points at a non-standard port (`26301`) with a password — adjust `REDIS_*`/`CELERY_*` vars to match your local Redis, or run one with matching config.

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run build         # production build (alias: build:prod)
npm run build:dev     # development-mode build
npm run preview
```

### Docker Deployment

```bash
copy backend\.env.example backend\.env
# Edit backend\.env with real configuration

docker-compose -f docker/docker-compose.yml up -d
docker-compose -f docker/docker-compose.yml logs -f
docker-compose -f docker/docker-compose.yml down
```

### Production (reference: `backend/start.sh`)

Production runs Gunicorn (`gunicorn -c gunicorn_config.py app.main:app`) plus **three separate Celery workers** split by queue (proofread / evaluation / formatter+plagiarism+default), each with its own concurrency tuned for that workload. Don't assume a single worker process is the deployment target when reasoning about scaling or queue isolation.

## Architecture & Key Patterns

### Configuration System

**Pydantic Settings**, env loaded from `backend/.env` (or `.env.production` when `APP_ENV=production`):

- Class: `backend/app/config.py` → `Settings`. Access via `from app.config import settings`.
- `DATABASE_URL` defaults to `sqlite:///./storage/app.db` if unset; set a `mysql+pymysql://...` URL for production.
- At least one of `BAILIAN_API_KEY` / `DEEPSEEK_API_KEY` must be set or AI features raise at call time.
- Storage subdirectories (uploads/outputs/temp/proofread/formatter/wechat/alipay) are auto-created by a validator — don't manually `mkdir` them.

### API Structure (Backend)

Routes live flat under `app/api/v1/` (not in an `endpoints/` subfolder) and are aggregated in `app/api/v1/router.py`, included in `app/main.py` under `/api/v1`:

| Module | Prefix | Covers |
|---|---|---|
| `evaluation.py` | `/evaluation` | upload, status, result, report download |
| `proofread.py` | `/proofread` | upload, status, download, cancel |
| `formatter.py` | `/formatter` | format, templates CRUD (incl. 2-step custom upload), status, download, preview |
| `plagiarism.py` | `/plagiarism` | config, upload (zh/en/auto), status, report |
| `auth.py` | `/auth` | login/register, SMS login, WeChat/Alipay OAuth, admin user approval |
| `billing.py` | `/billing` | pricing, quota, orders, payment callbacks, usage, invite codes |
| `admin.py` | `/admin` | system settings, users, orders, refund approval |
| `admin_papers.py` | `/admin/local-papers` | local plagiarism-corpus CRUD + FAISS rebuild |

Each sub-router is loaded inside a try/except in `router.py` — a broken module logs ❌ but does not take down the rest of the API.

### Async Task Model (Celery)

Evaluation, proofreading, formatting, and plagiarism are **all async**: the HTTP endpoint saves the file, submits a Celery task, and returns a `task_id` immediately. The frontend polls a `/status/{task_id}` endpoint. Task code lives in `app/workers/*_tasks.py`, routed to 4 named queues defined in `app/workers/celery_app.py`. Celery results live in Redis (7-day TTL) and are mirrored into MySQL (`app/services/task_store.py` / `TaskRecord` model) so results survive past Redis expiry.

**If you add or change behavior in evaluation/proofread/formatter/plagiarism, the actual logic is in `app/core/<module>/` — the `app/workers/*_tasks.py` file is just a thin Celery wrapper around it.**

### Core Business Logic (`backend/app/core/`)

1. **`ai_client.py`** — unified `call_ai()` / `call_ai_sync()`: tries Bailian first, falls back to DeepSeek on failure, retries each. Use this rather than calling either SDK directly.
2. **`evaluator/`** — `prompts.py` has 5 weighted dimensions (选题意义/写作安排/逻辑构建/专业能力/学术规范, weights 10/10/20/40/20), each with paper-type-specific (humanities/science_engineering/arts) prompt variants. `report_generator.py` + `chart_generator.py` produce the Word report with radar chart.
3. **`formatter/`** — `structure_analyzer.py` classifies document sections (16 `SectionType`s) via keyword → numbering pattern → style → optional-AI priority chain; `format_engine.py` injects template styles at the ZIP level (`styles.xml`/`theme1.xml` replaced, `numbering.xml` merged); `template_manager.py` handles template metadata CRUD.
4. **`proofreadme/`** — `pipeline.py` walks paragraphs concurrently (semaphore-bounded AI calls), then writes Word Track-Changes nodes (`word_patch.py`) serially; `chunk.py` placeholder-protects proper nouns/formulas before sending text to the LLM.
5. **`plagiarism/`** — by far the largest subsystem (language detection → engine routing → local FAISS / external academic APIs → n-gram + semantic matching → confidence scoring → tiered risk classification). See the "查重子系统" section (§3.5) in [CLAUDE-MAP.md](CLAUDE-MAP.md) before touching this — it has a lot of moving parts and a deliberate English-checker → Chinese-checker fallback path.

### Quota / Billing Model

`app/services/billing_service.py` is the single source of truth for quota logic. Priority order when checking/consuming quota: **admin (bypass) > subscription > purchase > referral > free**. `consume_quota()` uses a raw SQL `UPDATE` (not ORM read-then-write) specifically to avoid race conditions under concurrent requests — don't refactor that into an ORM round-trip. Plagiarism checks cost differently: **1 credit for Chinese, 2 for English** (`api/v1/plagiarism.py`).

### File Handling

**Service:** `backend/app/services/file_service.py` — `validate_file()` (type/size), `save_upload_file()` (UUID-named), `clean_old_files()` (by `FILE_RETENTION_HOURS`).

WPS-generated `.docx` files often have non-standard internals that break `python-docx`; `app/services/docx_normalizer.py` detects this and shells out to LibreOffice (`soffice --headless --convert-to docx`) to normalize. If `soffice` isn't installed, it transparently returns the original file and lets the caller's own fallback path handle parsing failures — don't add a hard dependency on LibreOffice being present.

**Storage paths** (auto-created under `backend/storage/`): `uploads/`, `outputs/`, `temp/`, plus per-feature dirs `proofread/`, `formatter/`, `plagiarism/`, `wechat/`, `alipay/`.

### Logging

**loguru**, configured in `app/main.py`: colorized stdout + daily-rotated file at `backend/logs/app_{date}.log`, 30-day retention, UTF-8.

### Data Models

- **ORM** (`app/models/`): `User`, `billing.py` (`SystemConfig`/`Subscription`/`QuotaBalance`/`Order`/`UsageRecord`/`TaskRecord`/`InviteCode`), `local_paper.py` (`LocalPaper` — plagiarism corpus with a 384-dim embedding BLOB).
- **Pydantic** (`app/schemas/`): `evaluation.py` (`EvaluationResponse`/`EvaluationResult`), `billing.py`, `formatting.py`, `spell_check.py`.

## Important Constraints & Behaviors

### AI Key Configuration

At least one of `BAILIAN_API_KEY` or `DEEPSEEK_API_KEY` must be valid for AI-dependent features (evaluation, proofread, plagiarism's LLM steps) to work. `ai_client.call_ai()` tries Bailian then DeepSeek and only raises once both fail — a missing/invalid key surfaces as a `RuntimeError` from that call, not an immediate startup error.

### Content Length Limits

- Evaluation: paper content truncated before sending to the AI (title ≤100 chars; body capped — see `_extract_structure()` in `api/v1/evaluation.py`) to control token usage.
- Plagiarism: never sends full-paper text to the LLM — it chunks (Chinese: 400-char windows) or extracts key sentences (English: 8–15 heuristically-scored sentences) instead.

### Prompt Response Format

Evaluation and proofreading prompts expect **strict JSON** (e.g. `{"score": 85, "strengths": [...], "weaknesses": [...], "suggestions": [...]}`). `ai_client.parse_json_response()` strips Markdown code fences before parsing and falls back to a caller-supplied default dict on failure — always pass a sensible fallback rather than letting a parse error propagate.

### Word Document Parsing

`python-docx` is the primary path; PDFs go through `pdfplumber` (`services/pdf_extractor.py`); WPS-flavored docx go through the LibreOffice normalizer above. Tables/images are skipped during text extraction for evaluation/proofreading.

### Registration & Approval

New users register with `is_approved=False` by default — they cannot use the app until an admin approves them via `/auth/admin/users/{id}/approve`. Don't assume registration alone grants access when testing auth flows.

## Current Project Status

All four core features (evaluation, proofread, formatter, plagiarism) plus auth/billing/admin are implemented end-to-end, not skeletons — this expands well past the original PRD scope. Known rough edges to be aware of:

- Plagiarism's English path depends on three external APIs (Semantic Scholar/CORE/PubMed) that are rate-limited on free tiers; it has a deliberate fallback to the Chinese hybrid checker if all three fail.
- Local plagiarism corpus (FAISS) starts empty until papers are ingested (`backend/scripts/ingest_openalex.py`) or accumulated via the English checker's write-back path.
- Repo root has many historical `*.md` diagnosis/implementation-report files from past debugging sessions — they document past incidents, not current architecture. Prefer this file and [CLAUDE-MAP.md](CLAUDE-MAP.md) over them.

## Testing

```bash
cd backend
pytest                                   # all tests
pytest tests/test_billing.py -v
pytest tests/test_plagiarism_english/ -v # confidence_scorer/language_detector/levels_en/ngram_matcher/reference_stripper
```

`backend/tests/conftest.py` holds shared fixtures. There is no dedicated test file per feature for evaluation/proofread/formatter yet — `test_billing.py` and the `test_plagiarism_english/` suite are the most thorough.

## Common Issues

1. **AI calls fail / "Invalid API-key"**: set a real `BAILIAN_API_KEY` and/or `DEEPSEEK_API_KEY` in `backend/.env`.
2. **Task submits but never completes**: no Celery worker is running, or it's not listening on the right queue — start one with `-Q evaluation,proofread,formatter,plagiarism,default`.
3. **Celery can't connect / tasks silently vanish**: Redis isn't reachable at the configured `REDIS_HOST`/`REDIS_PORT`/`REDIS_PASSWORD` — run `python check_services.py` to diagnose.
4. **Import errors**: virtual environment not activated, or `pip install -r requirements.txt` not run (note `bcrypt==4.0.1` is pinned — newer bcrypt breaks `passlib`).
5. **File size errors**: default max is 20MB, via `MAX_FILE_SIZE` in `.env`.
6. **CORS errors**: frontend origin must be in `CORS_ORIGINS` in `config.py`.
7. **WPS-format .docx fails to parse**: install LibreOffice so `docx_normalizer.py` can convert it; otherwise the fallback text-extraction path kicks in but loses structure.
8. **Logged-in user can't access features**: check `is_approved` — registration doesn't auto-approve.
9. **402 errors on a feature**: out of quota — check `QuotaBalance` for that user, or that `billing_enabled` is set as expected in `SystemConfig`.

## File Naming Conventions

- API endpoints: snake_case filenames (e.g., `admin_papers.py`)
- Classes: PascalCase (e.g., `FormatEngine`, `EnglishAcademicChecker`)
- Functions: snake_case (e.g., `extract_title()`)
- Config keys: UPPERCASE (e.g., `BAILIAN_API_KEY`)

## Key Files Reference

- `backend/app/main.py` — FastAPI app entry point (lifespan, CORS, exception handler)
- `backend/app/config.py` — all configuration settings
- `backend/app/core/ai_client.py` — unified AI client with Bailian→DeepSeek fallback
- `backend/app/core/evaluator/prompts.py` — evaluation dimension prompts/weights (core logic)
- `backend/app/core/plagiarism/checker_context.py` — entry point into the plagiarism engine selection
- `backend/app/workers/celery_app.py` — Celery queue/concurrency/timeout configuration
- `backend/app/services/billing_service.py` — quota/order/refund business logic
- `backend/app/services/file_service.py` — file handling utilities
- [CLAUDE-MAP.md](CLAUDE-MAP.md) — full directory tree + detailed functional breakdown of every module

## Environment Variables Required

See `backend/.env.example` for the complete, authoritative list (AI keys, Redis/Celery, JWT secret, WeChat/Alipay payment + login, Aliyun SMS, CORE/Semantic Scholar API keys). Minimal set to get a dev server running:

```env
# At least one AI key
BAILIAN_API_KEY=sk-xxxxx
DEEPSEEK_API_KEY=sk-xxxxx

# Redis (required even in dev — Celery broker/backend)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Optional — defaults shown
DEBUG=True
USE_AI=False
MAX_FILE_SIZE=20
FILE_RETENTION_HOURS=24
LOG_LEVEL=INFO
PLAGIARISM_ENGINE=hybrid
SECRET_KEY=change-me-in-production-use-a-long-random-string
```

Payment (`WECHAT_*`/`ALIPAY_*`), SMS (`ALIYUN_SMS_*`), and plagiarism external-API keys (`CORE_API_KEY`/`SEMANTIC_SCHOLAR_API_KEY`) are optional for local dev of the core 4 features but required for billing/auth/English-plagiarism to fully function.
