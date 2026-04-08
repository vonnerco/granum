from __future__ import annotations

import time
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database.models import Interaction
from src.llm.client import LLMClient, LLMResult
from src.schemas.interaction import EnhanceResponse, HistoryItem, HistoryResponse, TokenUsage


class EnhancementError(Exception):
    pass


@dataclass
class Pagination:
    page: int = 1
    page_size: int = 10


class EnhancerService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        llm_client: LLMClient,
    ) -> None:
        self._session_factory = session_factory
        self._llm_client = llm_client

    async def enhance_text(self, raw_text: str) -> EnhanceResponse:
        started_at = time.perf_counter()

        try:
            result: LLMResult = self._llm_client.enhance(raw_text)
            latency_ms = int((time.perf_counter() - started_at) * 1000)

            await self._log_interaction(
                input_text=raw_text,
                enhanced_text=result.enhanced_text,
                model_used=result.model_used,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                latency_ms=latency_ms,
                status='success',
                error_message=None,
            )

            return EnhanceResponse(
                enhanced_text=result.enhanced_text,
                model_used=result.model_used,
                token_usage=TokenUsage(
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                ),
                latency_ms=latency_ms,
            )

        except Exception as exc:
            latency_ms = int((time.perf_counter() - started_at) * 1000)

            await self._log_interaction(
                input_text=raw_text,
                enhanced_text=None,
                model_used='llm_unavailable',
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=latency_ms,
                status='failure',
                error_message=str(exc),
            )
            raise EnhancementError('Failed to enhance text. Please try again.') from exc

    async def log_validation_failure(self, raw_payload: str, reason: str) -> None:
        await self._log_interaction(
            input_text=raw_payload,
            enhanced_text=None,
            model_used='validation',
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=0,
            status='failure',
            error_message=f'Validation failed: {reason}',
        )

    async def get_history(self, page: int = 1, page_size: int = 10) -> HistoryResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        async with self._session_factory() as session:
            total_stmt = select(func.count(Interaction.id))
            total = int((await session.execute(total_stmt)).scalar_one())

            stmt = (
                select(Interaction)
                .order_by(Interaction.created_at.desc(), Interaction.id.desc())
                .offset(offset)
                .limit(page_size)
            )
            rows = (await session.execute(stmt)).scalars().all()

        items = [
            HistoryItem(
                id=row.id,
                input_text=row.input_text,
                enhanced_text=row.enhanced_text,
                model_used=row.model_used,
                prompt_tokens=row.prompt_tokens,
                completion_tokens=row.completion_tokens,
                latency_ms=row.latency_ms,
                status=row.status,
                error_message=row.error_message,
                created_at=row.created_at,
            )
            for row in rows
        ]

        return HistoryResponse(page=page, page_size=page_size, total=total, items=items)

    async def _log_interaction(
        self,
        *,
        input_text: str | None,
        enhanced_text: str | None,
        model_used: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        status: str,
        error_message: str | None,
    ) -> None:
        async with self._session_factory() as session:
            session.add(
                Interaction(
                    input_text=input_text,
                    enhanced_text=enhanced_text,
                    model_used=model_used,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_ms=latency_ms,
                    status=status,
                    error_message=error_message,
                )
            )
            await session.commit()
