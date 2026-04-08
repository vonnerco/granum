# Granum AI Engineer Take-Home: Text Enhancement Microservice

This project implements the assessment requirements using **Python + FastAPI + SQLite**.

## Implemented Requirements

- `POST /enhance` endpoint:
  - Accepts raw technician note text.
  - Returns polished professional bullet-list output.
  - Includes `model_used`, token usage, and latency.
- `GET /history` endpoint:
  - Returns persisted interaction logs.
  - Supports basic pagination (`page`, `page_size`).
- Interaction logging:
  - Logs both successful and failed requests.
  - Persists input, output, model, token usage, latency, and outcome status.
- Error handling:
  - LLM failures return clear API errors (no stack traces) and are logged.
  - Malformed payloads are validation-rejected before LLM call and logged.
- Tests:
  - Meaningful coverage with mocked LLM client (no real API call in tests).
- Deliverable DB:
  - `data/text_enhancer.db` is pre-populated with 5 interactions (3 success, 2 failure).

## Architecture

- `src/main.py`:
  - FastAPI app factory, lifespan startup/shutdown, global validation handler.
- `src/api/endpoints.py`:
  - HTTP routes and request/response wiring.
- `src/core/enhancer_service.py`:
  - Business logic, latency calculation, logging orchestration.
- `src/llm/client.py`:
  - LLM abstraction and Gemini client implementation.
- `src/database/connection.py` and `src/database/models.py`:
  - SQLAlchemy async engine/session and `interactions` model.
- `src/schemas/interaction.py`:
  - Pydantic models for validation and API contracts.
- `tests/`:
  - API and service tests with mocked LLM behavior.

## Setup

1. Create and activate virtual environment (if not already active).

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

## Run (Single Command)

```bash
./run.sh
```

Alternative explicit command:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Run Tests

```bash
pytest -q
```

## API Usage

Health:

```bash
curl http://localhost:8000/health
```

Enhance:

```bash
curl -X POST http://localhost:8000/enhance \
  -H "Content-Type: application/json" \
  -d '{"text":"arrived on site lawn was a mess weeds everywhere did full mow edging and cleanup"}'
```

History:

```bash
curl "http://localhost:8000/history?page=1&page_size=10"
```

## Notes

- The project includes some legacy Node files from earlier iterations (`server.js`, `package.json`) but the delivered assessment implementation is the Python/FastAPI code under `src/`.
- The LLM integration uses the current Gemini Python SDK package: `google-genai`.
