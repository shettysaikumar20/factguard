import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.llm import ModelUnavailable
from app.pipeline import run
from app.schemas import Issue
from app.verifier import VerifierOutput, verify_draft


def verdict(passed=True, answer="Within 14 days."):
    return VerifierOutput(passed=passed, corrected_answer=answer, issues=[] if passed else [
        Issue(claim="30 days", evidence="14 days", reason="Wrong request deadline")])


class SafetyTests(unittest.TestCase):
    def test_pass_preserves_draft(self):
        with patch("app.pipeline.verify_draft", return_value=verdict(answer="Changed text")):
            self.assertEqual(run("14 days", "Deadline?", "Within 14 days.").final_answer, "Within 14 days.")

    def test_correction_is_rechecked(self):
        with patch("app.pipeline.verify_draft", side_effect=[verdict(False), verdict()]) as checker:
            result = run("14 days", "Deadline?", "Within 30 days.")
            self.assertEqual(result.status, "corrected")
            self.assertEqual(result.final_answer, "Within 14 days.")
            self.assertEqual(checker.call_args.args[2], "Within 14 days.")

    def test_bad_repair_is_withheld(self):
        with patch("app.pipeline.verify_draft", side_effect=[verdict(False), verdict(False)]):
            result = run("14 days", "Deadline?", "Within 30 days.")
            self.assertEqual(result.status, "flagged")
            self.assertIsNone(result.final_answer)

    def test_outage_at_each_stage_is_withheld(self):
        for replies in ([ModelUnavailable()], [verdict(False), ModelUnavailable()]):
            with self.subTest(replies=replies), patch("app.pipeline.verify_draft", side_effect=replies):
                result = run("14 days", "Deadline?", "Within 30 days.")
                self.assertEqual(result.status, "flagged")
                self.assertIsNone(result.final_answer)
        with patch("app.pipeline.generate_draft", side_effect=ModelUnavailable()):
            self.assertEqual(run("14 days", "Deadline?").status, "flagged")

    def test_invalid_verdict_and_fabricated_evidence(self):
        bad = ["not json", json.dumps({"passed": True, "issues": [
            {"claim": "30", "evidence": "14 days", "reason": "wrong"}], "corrected_answer": "14"}),
            json.dumps({"passed": False, "issues": [
            {"claim": "30", "evidence": "Made up quote", "reason": "wrong"}], "corrected_answer": "14"})]
        bad.append(json.dumps({"passed": False, "issues": [
            {"claim": "30", "evidence": "14 days", "reason": "wrong"}],
            "corrected_answer": " \t\n"}))
        for raw in bad:
            with self.subTest(raw=raw), patch("app.verifier.complete", return_value=raw):
                with self.assertRaises(ValueError):
                    verify_draft("14 days", "Deadline?", "30 days")
                self.assertEqual(run("14 days", "Deadline?", "30 days").status, "flagged")

    def test_api_validation_and_draft_privacy(self):
        client = TestClient(app)
        self.assertEqual(client.get("/health").status_code, 200)
        self.assertEqual(client.post("/check", json={"source": " ", "question": "?"}).status_code, 422)
        with patch("app.pipeline.generate_draft", return_value="Within 14 days."), patch(
            "app.pipeline.verify_draft", return_value=verdict()
        ):
            for audit in (False, True):
                response = client.post(f"/check?audit={str(audit).lower()}", json={"source": "14 days", "question": "Deadline?"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["draft"], "Within 14 days." if audit else None)


if __name__ == "__main__":
    unittest.main()
