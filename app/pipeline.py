"""Bounded loop: draft, verify, and at most one repair plus recheck."""
from app.generator import generate_draft
from app.verifier import verify_draft
from app.schemas import CheckResponse, VerificationResult
from app.llm import ModelUnavailable


def run(source: str, question: str, draft: str | None = None) -> CheckResponse:
    check = VerificationResult(passed=None)
    repair_check = None
    try:
        if draft is None:
            draft = generate_draft(source, question)
        verdict = verify_draft(source, question, draft)
        check = VerificationResult(passed=verdict.passed, issues=verdict.issues)
        if verdict.passed:
            return CheckResponse(draft=draft, check=check, final_answer=draft, status="passed")
        repair_check = VerificationResult(passed=None)
        repaired = verify_draft(source, question, verdict.corrected_answer)
        repair_check = VerificationResult(passed=repaired.passed, issues=repaired.issues)
        if repaired.passed:
            return CheckResponse(draft=draft, check=check, repair_check=repair_check,
                                 final_answer=verdict.corrected_answer, status="corrected")
    except (ModelUnavailable, ValueError):
        target = repair_check if repair_check is not None else check
        target.error = "Verification unavailable or invalid; answer withheld."
    return CheckResponse(draft=draft, check=check, repair_check=repair_check,
                         final_answer=None, status="flagged")
