from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int = 0


class NewsItem(BaseModel):
    title: str
    publisher: str = "Unknown"
    link: str | None = None
    published_at: str | None = None
    summary: str | None = None


class AttributionEvidence(BaseModel):
    label: str
    detail: str
    source: str | None = None


class AttributionResult(BaseModel):
    ticker: str
    timeframe: str
    narrative: str
    evidence: list[AttributionEvidence] = Field(default_factory=list)
    llm_used: bool = False


class CritiqueView(BaseModel):
    name: str
    commentary: str
    llm_used: bool = False


class CritiqueResult(BaseModel):
    views: list[CritiqueView] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
