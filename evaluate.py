"""Six live cases. Controlled drafts are explicitly labelled, never natural errors."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.pipeline import run


CASES = [
    dict(id="supported", source="Unused items may be returned within 30 days of delivery with a receipt.",
         question="When can I return an unused item?", expected="passed", draft=None),
    dict(id="unknown", source="Unused items may be returned within 30 days of delivery with a receipt.",
         question="How much is the restocking fee?", expected="passed", draft=None),
    dict(id="plausible_wrong_deadline", source="Return requests must be submitted within 14 days of delivery. After approval, customers have 30 days to ship the item back.",
         question="How long after delivery do I have to request a return?", expected="corrected",
         draft="You have 30 days after delivery to request a return."),
    dict(id="invented_fee", source="Unused items may be returned within 30 days of delivery with a receipt.",
         question="Is there a restocking fee?", expected="corrected",
         draft="Yes. A standard 15% restocking fee is deducted from your refund."),
    dict(id="exception", source="Most unused items can be returned within 30 days. Personalized items are final sale and cannot be returned, even if unused.",
         question="Can I return an unused personalized mug within 30 days?", expected="corrected",
         draft="Yes, your unused personalized mug qualifies for a return within 30 days."),
    dict(id="known_blind_spot", source="Unused items may be returned within 30 days. Return shipping is paid by the customer.",
         question="Who pays for return shipping?", expected="passed",
         draft="Unused items may be returned within 30 days.",
         limitation="True but evasive answer: factuality checking does not ensure the question was answered."),
]


def main():
    results = []
    for case in CASES:
        result = run(case["source"], case["question"], case["draft"])
        results.append({**case,
            "draft_origin": "live Gemini generation" if case["draft"] is None else "controlled AI-authored fixture (fault injection)",
            "result": result.model_dump(),
            "matches_expected_status": result.status == case["expected"],
        })
        print(case["id"], result.status, flush=True)
        # Preserve partial evidence if a later call is interrupted.
        Path("results").mkdir(exist_ok=True)
        Path("results/live.json").write_text(json.dumps({
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            "cases": results,
        }, indent=2), encoding="utf-8")
    if not all(row["matches_expected_status"] for row in results):
        raise SystemExit("Unexpected results recorded; inspect results/live.json")


if __name__ == "__main__":
    main()
