# FactGuard

FactGuard answers questions about supplied refund policies and checks **one failure type: fabricated factual claims** unsupported by or contradictory to the policy. Confusing a request deadline with a shipping window can sound plausible while giving a customer the wrong answer.

The flow is **Gemini draft → factual check → correction or flag**. Any proposed correction gets one recheck before release. Invalid model output, inconsistent verdicts, invented evidence quotes, provider failures, or a failed repair check produce `status: "flagged"` and `final_answer: null`. The loop is bounded; a passing verdict is not proof of correctness.

## Run

Requires Python 3.11+ (tested with 3.13) and a Gemini API key with available quota.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `.env`; never commit it. Then start the API:

```powershell
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs. On macOS/Linux use `.venv/bin/python` and `cp`. If using the existing project environment, substitute `venv` for `.venv`. `GEMINI_MODEL` selects the model; the recorded evaluation used `gemini-3.5-flash-lite`.

## API

`POST /check` generates and checks an answer:

```json
{
  "source": "Unused items may be returned within 30 days of delivery with a receipt.",
  "question": "When can I return an unused item?"
}
```

Responses contain `status` (`passed`, `corrected`, or `flagged`), `final_answer`, `check` (verdict, claims, evidence, reasons), and an optional `repair_check`.

The `draft` field is null by default; `/check?audit=true` includes it. Check findings may still quote incorrect claims. Consumer applications should display only `final_answer`, or a review-needed message when flagged.

`POST /verify` accepts the same input plus a `draft` string for controlled verifier evaluation. These are local developer endpoints without authentication.

## Tests and recorded results

Offline tests:

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

Live evaluation (uses Gemini quota and overwrites `results/live.json`):

```powershell
.venv\Scripts\python evaluate.py
```

The evaluation contains **six synthetic refund-policy cases using four distinct policy texts**. The saved run matched **6/6 expected statuses: three passed, three corrected**. All three repairs passed their rechecks. **Six offline tests passed.** These examples are not a general accuracy benchmark.

Two cases use normal live Gemini drafting; four use controlled AI-authored drafts. All six use the real Gemini checker. Controlled errors are **fault injection, not spontaneous Gemini hallucinations**. See [RESULTS.md](RESULTS.md) and [results/live.json](results/live.json) for all cases and exact outputs.

### Controlled before and after

Policy: requests must be submitted within **14 days of delivery**; after approval, customers have **30 days to ship the item back**.

Question: How long after delivery do I have to request a return?

- **Before:** "You have 30 days after delivery to request a return."
- **After:** "You have 14 days after delivery to request a return."

The checker identified the confused deadlines, quoted the 14-day rule, and rechecked the correction.

## Where the model failed

The real verifier initially labelled a true but irrelevant answer as fabricated. Asked who pays return shipping, the controlled draft said, "Unused items may be returned within 30 days." That sentence was explicitly supported by the source, although it did not answer the question.

The predefined expected status exposed the mismatch; comparing the verdict with the source confirmed it. The verifier is now instructed not to classify a supported statement as fabricated solely because it is incomplete or irrelevant. The recorded rerun matched that expectation without changing the cases or expected statuses. This does not guarantee future verdicts.

[FAILURE.md](FAILURE.md) preserves the original failure and fix, plus an AI-assisted schema-integration mistake that live testing caught while mocked tests passed.

## Limitations

- A supported but irrelevant or incomplete answer may pass; completeness and relevance are outside this check.
- The generator and verifier use the same model and can share mistakes.
- Evidence matching confirms that a quote exists, not that it logically supports the verdict.
- The supplied policy may itself be incorrect or outdated; FactGuard does not verify it against the real world.
- This is refund-policy Q&A, not general-purpose fact checking. It claims neither universal hallucination prevention nor complete prompt-injection resistance.
