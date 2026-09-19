# FactGuard

FactGuard is a small backend tool for **refund-policy question answering** that checks one specific failure type: factual claims that contradict or are unsupported by the supplied policy.

The project is intentionally narrow. It does not include search, a database, a frontend UI, RAG, or general-purpose fact checking.

Gemini first drafts an answer. A separate Gemini call then verifies the factual claims in that draft against the supplied policy. If the verifier proposes a correction, the correction is checked once more before it can be returned.

Invalid JSON, inconsistent verdicts, invented evidence quotes, provider failures, or failed repair checks result in:

```json
{
  "status": "flagged",
  "final_answer": null
}
```

The pipeline does not retry indefinitely. A passing model verdict is evidence that a verification step occurred, not proof that the answer is universally correct.

## How it works

```text
Policy + Question
       |
       v
 Gemini Draft
       |
       v
Factual Verification
       |
       +---- supported ----> Final Answer
       |
       +---- error found --> Correction
                                |
                                v
                         Repair Recheck
                                |
                    +-----------+-----------+
                    |                       |
                  passes                  fails
                    |                       |
                    v                       v
               Final Answer              Flagged
```

The checker focuses on one failure type:

> **Fabricated factual claims** — claims that contradict or are unsupported by the supplied refund policy.

## Run

### Requirements

- Python 3.11+ (tested with Python 3.13)
- Gemini API key with available quota

Create the environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `.env`. Do not commit the real API key.

Start the API:

```powershell
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000/docs
```

On macOS/Linux, use `.venv/bin/python` and `cp` instead of the Windows commands.

Model selection is configurable through `GEMINI_MODEL`; the recorded evaluation used `gemini-3.5-flash-lite`.

## API

### `POST /check`

Normal workflow. Gemini generates the first draft and FactGuard verifies it.

By default, the original draft is hidden from the response.

For developer inspection:

```text
POST /check?audit=true
```

includes the original draft.

Example input:

```json
{
  "source": "Unused items may be returned within 30 days of delivery with a receipt.",
  "question": "When can I return an unused item?"
}
```

### `POST /verify`

Developer evaluation endpoint.

It accepts a supplied draft so that known mistakes can be injected reproducibly and the verifier can be tested against them.

Example:

```json
{
  "source": "Return requests must be submitted within 14 days of delivery. After approval, customers have 30 days to ship the item back.",
  "question": "How long after delivery do I have to request a return?",
  "draft": "You have 30 days after delivery to request a return."
}
```

Both endpoints return a status, final answer, verification result, and an optional repair verification result.

Consumer applications should use only `final_answer`, or show a review-needed message when the status is `flagged`. Audit fields can intentionally contain incorrect claims.

These are local developer endpoints and do not include production authentication.

## Tests and recorded evidence

Run the offline tests with:

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

Run the live evaluation with:

```powershell
.venv\Scripts\python evaluate.py
```

The unit tests run offline. The evaluation makes real Gemini requests using six synthetic refund policies and writes the results to `results/live.json`.

See [RESULTS.md](RESULTS.md) for the complete recorded evaluation and exact before/after outputs.

The final recorded evaluation produced:

- **6/6 expected statuses matched**
- **3 passed**
- **3 corrected**
- **6 offline tests passed**

Six cases are a small evaluation set, not an accuracy benchmark.

Two evaluation cases use normal live Gemini generation. Four use controlled AI-authored drafts for reproducible fault injection. These controlled drafts are **not presented as spontaneous Gemini mistakes**.

All six recorded cases use the real Gemini verifier.

### Example: plausible but wrong deadline

Policy:

> Return requests must be submitted within 14 days of delivery. After approval, customers have 30 days to ship the item back.

Question:

> How long after delivery do I have to request a return?

Controlled draft:

> You have 30 days after delivery to request a return.

FactGuard detected that the draft confused the **14-day request deadline** with the **30-day shipping window**.

Before:

> You have 30 days after delivery to request a return.

After:

> You have 14 days after delivery to request a return.

The corrected answer was then checked again before being released.

## Key decisions and why

### One task and one failure type

I deliberately limited FactGuard to one narrow task: answering questions from a supplied refund policy.

I also limited verification to one failure type: **fabricated factual claims**.

I chose this failure because policy answers can sound plausible while confusing similar deadlines, conditions, fees, or exceptions.

### Factuality is separate from relevance

FactGuard checks whether factual claims are supported by the supplied policy. It does not determine whether an answer is complete or useful.

For example, given:

> Unused items may be returned within 30 days. Return shipping is paid by the customer.

and the question:

> Who pays for return shipping?

the answer:

> Unused items may be returned within 30 days.

is factually supported but does not answer the question.

FactGuard can pass this answer because completeness and relevance are outside the selected failure type.

I deliberately kept this limitation instead of adding another checker because the goal was to implement and evaluate one failure type clearly rather than expand the project unnecessarily.

### Corrections are not automatically trusted

When the verifier detects a factual error and proposes a correction, FactGuard performs one additional verification pass on the corrected answer.

A model-generated correction should not automatically be assumed correct.

If that repair fails verification, the answer is withheld instead of being released.

### Controlled fault injection

The evaluation uses controlled AI-authored drafts alongside normal live Gemini generation.

This makes specific mistakes reproducible and allows the checker to be tested consistently without presenting planted errors as spontaneous model failures.

## Where AI failed and how I caught it

During evaluation, the real Gemini verifier itself made a mistake.

The policy was:

> Unused items may be returned within 30 days. Return shipping is paid by the customer.

The question was:

> Who pays for return shipping?

The controlled draft was:

> Unused items may be returned within 30 days.

The draft is evasive and does not answer the question, but the factual statement it makes is explicitly supported by the policy.

The verifier initially classified this as a fabricated factual claim.

### How I caught it

The evaluation case had a predefined expected status. When the actual result did not match it, I manually compared the verifier's claimed problem with the supplied policy.

The statement appeared directly in the policy, so calling it fabricated was incorrect.

I preserved this failing run instead of changing the expected result to match the model.

### How I fixed it

I clarified the verifier instructions so that it judges only the factual claims actually made in the draft.

An incomplete or irrelevant statement is therefore not classified as fabricated merely because it fails to answer the question.

I then reran the same six evaluation cases without changing their expected statuses.

After the scope fix, all six expected statuses matched.

The original failure and the exact fix are documented in [FAILURE.md](FAILURE.md).

## Another AI-assisted development failure

During implementation, an AI-assisted version of the Gemini integration selected an incompatible structured-output schema option.

The offline mocked tests passed, but the first real integration run failed because the provider rejected the schema configuration.

The live run exposed the problem. I changed the integration to use the supported JSON schema configuration while retaining local validation.

The failed integration result is preserved with the project rather than hidden.

## Limitations

FactGuard intentionally has several limitations:

- The draft generator and verifier use the same model, so they can share mistakes.
- A passing verifier verdict is not a guarantee of truth.
- Exact evidence validation can confirm that quoted evidence exists without proving that the model interpreted it correctly.
- FactGuard checks agreement with the supplied source; the source itself may be incorrect.
- It does not check answer completeness or relevance.
- It does not perform general-purpose fact checking.
- It does not claim to eliminate hallucinations.
- Untrusted text is separated from verifier instructions, but this prototype does not claim complete prompt-injection resistance.

The project is intentionally kept small so that the selected failure mode, its evaluation, and its limitations remain clear.