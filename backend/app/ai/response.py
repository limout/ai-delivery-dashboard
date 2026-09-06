from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AIRisk(BaseModel):
    title: str
    severity: str

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"low", "medium", "high"}:
            raise ValueError("severity must be one of: low, medium, high")
        return normalized


class AIStructuredResponse(BaseModel):
    risk: AIRisk
    facts: list[str]
    interpretation: list[str]
    impact: list[str] = Field(default_factory=list)
    investigate: list[str] = Field(default_factory=list)
    recommendations: list[str]
    data_gaps: list[str]
