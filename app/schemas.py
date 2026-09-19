from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class CheckRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    source: str = Field(min_length=1, max_length=12000)
    question: str = Field(min_length=1, max_length=1000)


class VerifyRequest(CheckRequest):
    draft: str = Field(min_length=1, max_length=4000)


class Issue(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    claim: str = Field(min_length=1)
    evidence: str
    reason: str = Field(min_length=1)


class VerificationResult(BaseModel):
    passed: bool | None
    failure_type: Literal["fabricated_fact"] = "fabricated_fact"
    issues: list[Issue] = Field(default_factory=list)
    error: str | None = None


class CheckResponse(BaseModel):
    draft: str | None = None
    check: VerificationResult
    repair_check: VerificationResult | None = None
    final_answer: str | None
    status: Literal["passed", "corrected", "flagged"]
