"""Strict data contracts shared by generation, validation, and the API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Claim(StrictModel):
    text: str = Field(min_length=10, max_length=400)
    source_id: str = Field(min_length=1, max_length=32)
    quote: str = Field(min_length=20, max_length=1000)


class Draft(StrictModel):
    claims: list[Claim] = Field(max_length=5)
    abstain: bool
    reason: str = Field(max_length=300)


class GateCheck(StrictModel):
    name: str
    passed: bool
    detail: str


class Source(StrictModel):
    source_id: str
    title: str
    quote: str
    score: float


class AnswerResponse(StrictModel):
    status: Literal["answered", "abstained", "blocked"]
    answer: str
    sources: list[Source]
    checks: list[GateCheck]
    mode: Literal["offline", "claude"]


class AskRequest(StrictModel):
    question: str = Field(min_length=3, max_length=500)

    @field_validator("question")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if len(value.strip()) < 3:
            raise ValueError("Question must contain at least three non-space characters")
        return value.strip()
