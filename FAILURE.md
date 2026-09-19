# Failure story

## A real model error, preserved

In the first working live evaluation, the policy said:

> Unused items may be returned within 30 days. Return shipping is paid by the customer.

The question was “Who pays for return shipping?” The controlled draft said:

> Unused items may be returned within 30 days.

That is evasive, but every factual assertion is supported. The Gemini verifier confidently returned `passed: false`, labelled the claim a fabricated fact, and explained:

> The draft fails to answer the question about who pays for return shipping, omitting a key factual claim from the policy.

This is the wrong diagnosis for this tool's one failure type. I caught it with a predeclared expected status and by reading the source, rather than accepting an attractive corrected answer as proof the checker was right. The complete run remains in `results/before-scope-fix.json`; its evaluator exited nonzero, with 5/6 matching statuses.

I clarified that the checker judges claims actually made, and that a true but incomplete answer is outside this check. I reran the same six cases rather than changing the expected result. The final run is in `results/live.json`. This is a scope correction, not a claim that prompting solves reliability. The remaining weakness is deliberate and visible: an unhelpful true answer can pass. I did not add another completeness checker because the assignment asks for one narrow failure type.

## A plausible wrong answer caught and repaired

The policy gives **14 days to request a return**, then **30 days after approval to ship it**. The controlled AI-authored draft was:

> You have 30 days after delivery to request a return.

It sounds plausible because 30 days really appears in the policy. The real verifier identified the incorrect relationship, quoted the 14-day rule, and corrected the answer. It checked the repair again before releasing it. See the exact recorded before/after in `RESULTS.md` and `results/live.json`.

This draft was deliberately injected to test a known failure. The two ordinary live generation cases did not spontaneously hallucinate in the recorded run. I am not presenting the planted error as an observed natural generation failure.

## My AI-assisted code also failed

I initially passed a strict Pydantic model through Gemini's `response_schema`. This SDK/endpoint combination rejected `additional_properties` with HTTP 400. All six cases returned `flagged`; offline mocked tests had not exposed the integration error. I preserved `results/initial-schema-failure.json`, diagnosed the actual provider response, and switched to `response_json_schema` with `model_json_schema()`, keeping local strict validation. Real network execution, not the AI's confidence or mocked tests, established that the integration worked.

These records use the runtime UTC clock, which may differ from the surrounding session's displayed date. They are observations of these runs, not a general accuracy estimate.
