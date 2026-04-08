from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EnhanceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int


class EnhanceResponse(BaseModel):
    enhanced_text: str
    model_used: str
    token_usage: TokenUsage
    latency_ms: int


class HistoryItem(BaseModel):
    id: int
    input_text: str | None
    enhanced_text: str | None
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    status: str
    error_message: str | None
    created_at: datetime


class HistoryResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[HistoryItem]
