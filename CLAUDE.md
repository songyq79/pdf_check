# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **论文评价检验系统** (Academic Paper Evaluation and Checking System), a full-stack web application that provides:
1. Spell and punctuation checking for academic papers
2. AI-powered multi-dimensional paper evaluation using Alibaba's Bailian (通义千问) API
3. Template-based document formatting (planned for V2.0)

**Tech Stack:**
- Backend: FastAPI + Python 3.9+
- Frontend: Vue 3 + Vite + Element Plus
- AI: Alibaba Bailian API (阿里云百炼大模型)
- Document Processing: python-docx
- Optional: MySQL, Redis, Celery (for production)

## Development Commands

### Backend

```bash
cd backend

# Setup (first time)
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate         # Linux/Mac
pip install -r requirements.txt

# Configure API key
# Edit backend/.env and set BAILIAN_API_KEY=your_key

# Run development server
python -m my_app.main
# Or with uvicorn:
uvicorn my_app.main:my_app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest
pytest tests/test_evaluation.py -v    # Single test file
```

**Backend runs at:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

**Frontend runs at:** http://localhost:5173

### Docker Deployment

```bash
# Configure environment
copy backend\.env.example backend\.env
# Edit backend\.env with real configuration

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

## Architecture & Key Patterns

### Configuration System

The app uses **Pydantic Settings** with environment variables loaded from `backend/.env`:

- Configuration class: `backend/app/config.py` → `Settings` class
- Access globally via: `from app.config import settings`
- Critical setting: `BAILIAN_API_KEY` - **must be configured** for AI evaluation to work

### API Structure (Backend)

```
app/api/v1/endpoints/
├── evaluation.py      # POST /api/v1/evaluation/upload - Main AI evaluation endpoint
├── spell_check.py     # POST /api/v1/spell-check/upload - Spell checking (skeleton)
└── formatting.py      # POST /api/v1/formatting/upload - Template formatting (skeleton)
```

Routes are aggregated in `app/api/v1/router.py` and included in `app/main.py`.

### Core Business Logic

**Located in:** `backend/app/core/`

1. **Evaluator Module** (`core/evaluator/`)
   - `prompts.py`: Contains 4 hardcoded evaluation dimension prompts:
     - `academic_standard` (学术规范性)
     - `logic_innovation` (逻辑与创新性)
     - `language_quality` (语言质量)
     - `citation_standard` (文献引用规范性)
   - `bailian_client.py`: API client for Alibaba Bailian with retry logic
   - `report_generator.py`: Generate Word/PDF reports (to be implemented)
   - `chart_generator.py`: Radar chart generation (to be implemented)

2. **Spell Checker Module** (`core/spell_checker/`) - Currently skeleton code
   - Should use `pycorrector` library (already in requirements.txt)
   - Should generate Word revision markup (Track Changes mode)

3. **Formatter Module** (`core/formatter/`) - Currently skeleton code
   - Template-based document formatting

### Evaluation Flow

```
User uploads .docx → validate_file() → save_upload_file()
→ Extract title & content from Word → For each dimension:
  → Generate prompt from prompts.py
  → Call Bailian API via bailian_client.py
  → Parse JSON response {score, strengths, weaknesses, suggestions}
→ Calculate average score → Return EvaluationResponse
```

**Key implementation:** `backend/app/api/v1/endpoints/evaluation.py:evaluate_paper()`

### File Handling

**Service:** `backend/app/services/file_service.py`

- `validate_file()`: Checks file type (.docx only) and size (max 20MB by default)
- `save_upload_file()`: Saves with UUID filename to prevent conflicts
- `clean_old_files()`: Removes files older than `FILE_RETENTION_HOURS` (24h default)

**Storage paths** (auto-created):
- Uploads: `backend/storage/uploads/`
- Outputs: `backend/storage/outputs/`
- Temp: `backend/storage/temp/`

### Logging

Uses **loguru** configured in `app/main.py`:
- Console output: Colorized, configured log level
- File logs: `backend/logs/app_{date}.log`, 30-day retention, UTF-8 encoding

### Data Models (Pydantic)

**Located in:** `backend/app/schemas/`

- `evaluation.py`: Contains `EvaluationResponse`, `EvaluationResult` models
- Models validate API responses and enforce JSON structure

## Important Constraints & Behaviors

### API Key Configuration

**The system will NOT work without a valid Bailian API key.** Get one from:
https://dashscope.aliyun.com/

Error when missing: `APIError: Invalid API-key provided`

### Content Length Limits

- Document content truncated to **10,000 characters** before sending to API (see `extract_content()`)
- Title limited to **100 characters**
- This prevents exceeding Bailian API token limits

### Prompt Response Format

All evaluation prompts expect **strict JSON** responses:
```json
{
  "score": 85,
  "strengths": ["优点1", "优点2", "优点3"],
  "weaknesses": ["问题1", "问题2"],
  "suggestions": ["改进建议1", "改进建议2"]
}
```

If AI returns non-JSON, parsing will fail. Handle in `bailian_client.py:evaluate_paper()`.

### Word Document Parsing

- Uses `python-docx` library
- Title extraction: First non-empty paragraph (up to 100 chars)
- Content extraction: All paragraphs joined with `\n`
- Formulas/tables are skipped in text extraction

### Deprecation Warnings

FastAPI `@app.on_event()` is deprecated. Current code uses it but should migrate to **lifespan** context managers:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    yield
    # Shutdown logic

app = FastAPI(lifespan=lifespan)
```

## Current Project Status

**Completed:**
- ✅ FastAPI backend framework
- ✅ File upload and validation
- ✅ Word document parsing
- ✅ Bailian API integration
- ✅ 4-dimension evaluation with prompts
- ✅ Configuration management
- ✅ Logging system
- ✅ Frontend scaffolding (Vue 3 structure exists)

**TODO (High Priority):**
- ⏳ Test evaluation with real API key (currently fails with invalid key)
- ⏳ Implement report generation (Word/PDF export)
- ⏳ Complete frontend UI for evaluation display
- ⏳ Implement spell checking functionality
- ⏳ Add radar chart visualization

**TODO (Future - V2.0):**
- Template formatting feature
- User authentication system
- Task history and management
- Celery async processing for large files

## Testing

Test reports available:
- `TEST_REPORT.md`: Manual API testing results
- `BACKEND_COMPLETE_REPORT.md`: Backend development summary

Manual API testing script: `test_api.py`, `test_bailian_api.py`

## Common Issues

1. **"Invalid API-key provided"**: Edit `backend/.env` and set real `BAILIAN_API_KEY`
2. **Import errors**: Ensure virtual environment is activated and `pip install -r requirements.txt` is run
3. **File size errors**: Default max is 20MB, configurable via `MAX_FILE_SIZE` in `.env`
4. **CORS errors**: Frontend origin must be in `CORS_ORIGINS` list in `config.py`

## File Naming Conventions

- API endpoints: Use underscores (e.g., `spell_check.py`)
- Classes: PascalCase (e.g., `BailianAPIClient`)
- Functions: snake_case (e.g., `extract_title()`)
- Config keys: UPPERCASE (e.g., `BAILIAN_API_KEY`)

## Key Files Reference

- `backend/app/main.py` - FastAPI app entry point
- `backend/app/config.py` - All configuration settings
- `backend/app/core/evaluator/prompts.py` - **Evaluation dimension prompts (core logic)**
- `backend/app/core/evaluator/bailian_client.py` - AI API client
- `backend/app/api/v1/endpoints/evaluation.py` - Main evaluation endpoint
- `backend/app/services/file_service.py` - File handling utilities
- `PRD_论文评价检验系统.md` - Complete product requirements
- `PROJECT_STRUCTURE.md` - Detailed directory structure

## Environment Variables Required

```env
# Mandatory for AI features
BAILIAN_API_KEY=sk-xxxxx

# Optional (have defaults)
APP_NAME=论文评价检验系统
APP_VERSION=1.0.0
DEBUG=True
MAX_FILE_SIZE=20
FILE_RETENTION_HOURS=24
LOG_LEVEL=INFO
```