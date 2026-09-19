from fastapi import FastAPI
from app.pipeline import run
from app.schemas import CheckRequest, CheckResponse, VerifyRequest

app = FastAPI(title="FactGuard: refund-policy answers", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/check", response_model=CheckResponse)
def check_answer(request: CheckRequest, audit: bool = False):
    result = run(request.source, request.question)
    if not audit:
        result.draft = None
    return result


@app.post("/verify", response_model=CheckResponse)
def verify_answer(request: VerifyRequest):
    """Developer evaluation endpoint for explicitly supplied drafts."""
    return run(request.source, request.question, request.draft)
