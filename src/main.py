from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.endpoints import router
from src.config import Settings, get_settings
from src.core.enhancer_service import EnhancerService
from src.database.connection import DatabaseManager
from src.llm.client import GeminiLLMClient, LLMClient


def _build_llm_client(settings: Settings) -> LLMClient:
    return GeminiLLMClient(
        api_key=settings.google_generative_ai_api_key or '',
        model_name=settings.llm_model,
    )


def create_app(settings: Settings | None = None, llm_client: LLMClient | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db_manager = DatabaseManager(app_settings.database_url)
        await db_manager.init_models()

        app.state.db_manager = db_manager
        app.state.enhancer_service = EnhancerService(
            session_factory=db_manager.session_factory,
            llm_client=llm_client or _build_llm_client(app_settings),
        )
        yield
        await db_manager.close()

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        lifespan=lifespan,
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        if request.url.path == '/enhance' and hasattr(request.app.state, 'enhancer_service'):
            raw_body = (await request.body()).decode('utf-8', errors='replace')
            if not raw_body:
                raw_body = '<empty body>'

            try:
                parsed_errors = json.dumps(exc.errors(), default=str)
            except Exception:
                parsed_errors = str(exc)

            await request.app.state.enhancer_service.log_validation_failure(
                raw_payload=raw_body,
                reason=parsed_errors,
            )

        return JSONResponse(
            status_code=422,
            content={
                'detail': 'Invalid request payload.',
                'errors': exc.errors(),
            },
        )

    @app.get('/')
    async def root() -> dict[str, str]:
        return {'message': 'Granum AI Text Enhancement API is running.'}

    @app.get('/health')
    async def health() -> dict[str, str]:
        return {'status': 'ok'}

    app.include_router(router)
    return app


app = create_app()
