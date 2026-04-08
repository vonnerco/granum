# Granun Project Execution Report

Date: April 8, 2026

This document summarizes what was redone so the project matches the **AI Engineer Take-Home Assignment** requirements.

## What Was Reworked

1. Rebuilt the implementation as Python/FastAPI (assessment-aligned)
- Added a complete FastAPI app under `src/`.
- Implemented app factory + lifespan-managed startup/shutdown.
- Added root and health routes for quick runtime verification.

2. Implemented required endpoints
- `POST /enhance`
  - Validates `text` input.
  - Calls an LLM client abstraction.
  - Returns enhanced text, model used, token usage, and latency.
- `GET /history`
  - Returns interaction logs.
  - Supports `page` and `page_size` pagination.

3. Added robust SQLite interaction logging
- Created SQLAlchemy model for `interactions`.
- Logs all success/failure outcomes with:
  - input text
  - enhanced output
  - model used
  - prompt/completion tokens
  - latency
  - error details when failures occur

4. Added required error handling behavior
- LLM runtime failures:
  - return clear `502` response payloads
  - are persisted in SQLite log
- Malformed request payloads:
  - rejected with `422` before LLM call
  - logged via global validation exception handler

5. Added meaningful tests with mocked LLM
- `tests/test_api.py`
  - success response and log verification
  - LLM failure path + log verification
  - payload validation rejection + log verification
  - history pagination
- `tests/test_service.py`
  - service-level success logging
  - service-level failure logging

6. Updated run/setup artifacts
- `requirements.txt` finalized for Python stack.
- `run.sh` updated to start FastAPI via `uvicorn` in one command.
- `README.md` rewritten with setup, run, test, and API usage instructions.

7. Added pre-populated SQLite DB (required deliverable)
- Added `src/database/seed_db.py` and executed it.
- `data/text_enhancer.db` now contains **5 interactions**:
  - **3 success**
  - **2 failure**

## Verification Results

1. Automated tests
- Command run: `pytest -q`
- Result: `6 passed`

2. Runtime smoke check
- `GET /health` returns `200` with `{ "status": "ok" }`
- `GET /history?page=1&page_size=2` returns paginated data from pre-populated DB

## Files Added/Updated (Core)

- `src/main.py`
- `src/api/endpoints.py`
- `src/core/enhancer_service.py`
- `src/llm/client.py`
- `src/database/connection.py`
- `src/database/models.py`
- `src/database/seed_db.py`
- `src/schemas/interaction.py`
- `tests/test_api.py`
- `tests/test_service.py`
- `requirements.txt`
- `run.sh`
- `README.md`
- `data/text_enhancer.db` (seeded)

## Final Status

The project now executes the assignment requirements end-to-end with working API behavior, persistent audit logging, mocked-LLM test coverage, and a pre-populated SQLite database deliverable.
