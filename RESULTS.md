# Recorded results

Model: `gemini-3.5-flash-lite`. Runtime timestamp: `2026-09-18T19:05:43.911215+00:00`.

Six live cases; 6/6 expected statuses after the scope fix. This includes a known product limitation, not six universally good answers. All final answers below were manually compared with their synthetic sources.

| Case | Draft origin | Expected / actual | Review |
|---|---|---|---|
| supported | live Gemini generation | passed / passed | Supported answer; condition and deadline retained. |
| unknown | live Gemini generation | passed / passed | Does not invent an unspecified fee. |
| plausible_wrong_deadline | controlled AI-authored fixture (fault injection) | corrected / corrected | Confuses shipping and request deadlines; corrected to 14 days. |
| invented_fee | controlled AI-authored fixture (fault injection) | corrected / corrected | Invented 15% fee removed; policy silence acknowledged. |
| exception | controlled AI-authored fixture (fault injection) | corrected / corrected | Personalized-item exception restored. |
| known_blind_spot | controlled AI-authored fixture (fault injection) | passed / passed | True but evasive answer passes: completeness is not checked. |

## Exact before and after

### supported

Policy: Unused items may be returned within 30 days of delivery with a receipt.

Question: When can I return an unused item?

Before: You can return an unused item within 30 days of delivery, provided you have a receipt.

After: You can return an unused item within 30 days of delivery, provided you have a receipt.

Status: `passed`.

### unknown

Policy: Unused items may be returned within 30 days of delivery with a receipt.

Question: How much is the restocking fee?

Before: The policy does not say.

After: The policy does not say.

Status: `passed`.

### plausible_wrong_deadline

Policy: Return requests must be submitted within 14 days of delivery. After approval, customers have 30 days to ship the item back.

Question: How long after delivery do I have to request a return?

Before: You have 30 days after delivery to request a return.

After: You have 14 days after delivery to request a return.

Status: `corrected`.

Check: The draft states the return request window is 30 days, whereas the policy explicitly states it must be within 14 days of delivery.

Evidence: Return requests must be submitted within 14 days of delivery.

Repair recheck passed: `True`.

### invented_fee

Policy: Unused items may be returned within 30 days of delivery with a receipt.

Question: Is there a restocking fee?

Before: Yes. A standard 15% restocking fee is deducted from your refund.

After: The policy does not mention whether there is a restocking fee.

Status: `corrected`.

Check: The policy does not mention any restocking fee; this claim is fabricated using outside knowledge.

Evidence: (No supporting evidence in policy.)

Repair recheck passed: `True`.

### exception

Policy: Most unused items can be returned within 30 days. Personalized items are final sale and cannot be returned, even if unused.

Question: Can I return an unused personalized mug within 30 days?

Before: Yes, your unused personalized mug qualifies for a return within 30 days.

After: No, personalized items are final sale and cannot be returned, even if unused.

Status: `corrected`.

Check: The draft states that unused personalized items can be returned, which directly contradicts the policy stating they are final sale and cannot be returned even if unused.

Evidence: Personalized items are final sale and cannot be returned, even if unused.

Repair recheck passed: `True`.

### known_blind_spot

Policy: Unused items may be returned within 30 days. Return shipping is paid by the customer.

Question: Who pays for return shipping?

Before: Unused items may be returned within 30 days.

After: Unused items may be returned within 30 days.

Status: `passed`.

## Safety and integration checks

The final offline run passed all six existing unittest methods (6 tests in 0.089s, OK). The retained earlier offline log is [results/unit-tests.txt](results/unit-tests.txt). They cover preserving accepted drafts, rechecking corrections, withholding failed repairs, outages at each stage, malformed/inconsistent verdicts and invented evidence, HTTP input validation and draft visibility.

The first integration run failed all six cases because of an incompatible schema argument; no answer was released. After fixing that, 5/6 expected statuses matched: the verifier falsely labelled an irrelevant true claim a fabrication. After clarifying scope, the same six cases matched 6/6. Original failed runs are retained; see [FAILURE.md](FAILURE.md).

The default endpoint hides the draft; audit mode and /verify expose it intentionally for developer evaluation. No API key is included in any report.

In this final live run, all three proposed repairs passed their rechecks; no provider errors or failed repair checks occurred. Withholding on failure was exercised by the offline tests, not by a provider failure in this live run. The invented-fee verdict correctly identifies an unsupported fee, but its phrase "using outside knowledge" is the model's unverified explanation of the claim's origin. The draft was a controlled fixture.
