# Requirements

This document explains the dependencies used in `requirements.txt` and why each is included for the Granum take-home project.

## Core Application

- `fastapi`: API framework for implementing `/enhance` and `/history` endpoints.
- `uvicorn[standard]`: ASGI server used to run the FastAPI app.
- `python-dotenv`: Loads environment variables from `.env` (for API keys and config).
- `pydantic-settings`: Typed settings/config management for FastAPI projects.

## Database

- `SQLAlchemy`: ORM and SQL toolkit for modeling and querying SQLite data.
- `aiosqlite`: Async SQLite driver for non-blocking DB access in async FastAPI routes.

## LLM Clients

- `google-generativeai`: Official Gemini SDK.
- `openai`: OpenAI SDK (also useful for OpenAI-compatible providers).

## Testing

- `pytest`: Test runner/framework.pi
- `httpx`: HTTP client used for API endpoint testing.

## Setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```
