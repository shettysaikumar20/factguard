# FactGuard

A small backend tool for **refund-policy questions**, checking one failure type: claims that contradict or are unsupported by the supplied policy. No search, database, UI, or general-purpose fact checking.

Gemini drafts an answer, a separate Gemini call checks its claims, and any proposed correction gets one further check. Invalid JSON, inconsistent verdicts, invented evidence quotes, provider failures, or failed repair checks produce `flagged` with `final_answer: null`. The loop never retries indefinitely. A passing model verdict is evidence of a check, not proof of truth.

## Run

Python 3.11+ (tested with 3.13), a Gemini API key with available quota:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set GEMINI_API_KEY in .env; do not commit it.
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs. On macOS/Linux use `.venv/bin/python` and `cp`. The existing workspace also has a usable `venv` environment. Model selection is configurable through `GEMINI_MODEL`; recorded runs used `gemini-3.5-flash-lite` after the original model exhausted its quota.

```powershell
$body = @{
  source = 'Return requests must be submitted within 14 days of delivery. After approval, customers have 30 days to ship the item back.'
  question = 'How long after delivery do I have to request a return?'
} | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/check -Method Post -ContentType 'application/json' -Body $body
```

`POST /check` generates and checks. `POST /check?audit=true` includes the original draft for developer inspection. `POST /verify` accepts the same fields plus `draft` to exercise a controlled failure. Both return `status`, `final_answer`, `check` (verdict, claims, evidence, reasons), and optional `repair_check`. Consumer applications should display only `final_answer`, or a review-needed message for `flagged`; the audit fields can contain incorrect claims. These local developer endpoints have no authentication and are not a hosted production service.

## Tests and recorded evidence

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python evaluate.py
```

Unit tests run offline. Evaluation makes real Gemini requests, sends only the six synthetic policies in `evaluate.py`, requires quota, and writes `results/live.json`. Nonmatching statuses exit nonzero and remain recorded. Inspect answer meaning as well as status; six cases are not an accuracy benchmark.

See [RESULTS.md](RESULTS.md) for all six cases and the clear before/after. Two cases use normal live Gemini drafting. Four use controlled AI-authored drafts; these are fault injection, **not claimed as spontaneous Gemini mistakes**. All six recorded cases used the real model checker; the three planted factual errors required model-generated repairs and repair rechecks. No private customer data was used.

Recorded result: **6/6 expected statuses matched** (three passed, three corrected); **six offline tests passed**. Controlled fault injection for the return-request deadline:

- Before: "You have 30 days after delivery to request a return."
- After: "You have 14 days after delivery to request a return."

The checker distinguished the 14-day request deadline from the 30-day shipping window and rechecked the correction.

## Where AI failed

The real verifier initially called a source-supported but irrelevant sentence a fabricated fact. I caught it by comparing the claim with the source and preserving the failing result, then explicitly limited the checker to assertions actually made. See [FAILURE.md](FAILURE.md) for the original output, fix, and remaining weakness. My AI-assisted implementation also initially chose an incompatible Gemini schema option; the live run caught this while offline mocked tests passed.

The draft and verifier use the same model and can share mistakes. Exact quote validation proves only that evidence exists, not that it supports the verdict. The source itself may be false; this tool checks agreement with it. It does not ensure completeness or helpfulness, and untrusted-text instructions are mitigated by separation, not proven safe. No claim of universal hallucination prevention is made.
