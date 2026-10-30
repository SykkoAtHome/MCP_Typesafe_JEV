"""Runner checks belong to evals, not the application-only tests directory."""

import unittest
import os
import tempfile
import json
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch, AsyncMock

from .bridge import arithmetic, compute
from .grading import iou, grade, parse_final, behavior
from .rpc import CodexRPC
from .agent import AgentTrial
from .storage import latest, assert_same_measurement
from .robustness import replay_response
from .run import run


class RunnerChecks(unittest.TestCase):
    def test_iou_rejects_valid_but_wrong_box(self):
        target = {"top": .1, "bottom": .3, "left": .1, "right": .3}
        wrong = {"top": .7, "bottom": .9, "left": .7, "right": .9}
        self.assertEqual(iou(wrong, target), 0)
        self.assertAlmostEqual(iou(target, target), 1)
        self.assertEqual(iou({**target, "top": float("nan")}, target), 0)

    def test_wrong_json_answer_fails(self):
        case = {"expected": {"answer": True}, "grading": "exact"}
        self.assertFalse(grade(case, {"answer": False})["passed"])
        self.assertFalse(grade(case, {"answer": 1})["passed"])
        self.assertTrue(grade(case, {"answer": True})["passed"])
        self.assertEqual(parse_final("not JSON"), {})
        self.assertEqual(parse_final("```"), {})

    def test_deterministic_alternative(self):
        self.assertEqual(arithmetic("17 * (23 + 9)"), 544)
        self.assertEqual(compute("date_difference", ["2024-02-28", "2024-03-01"]), 2)
        with self.assertRaises(ValueError):
            arithmetic("__import__('os')")

    def test_optional_omission_and_low_confidence(self):
        case = {"jev": "optional"}
        self.assertFalse(behavior(case, [], {}, "descriptions")["required_call_omitted"])
        call = {"tool": "jev_choice", "success": True, "response": {"confidence": .1}}
        result = behavior(case, [call], {}, "descriptions")
        self.assertTrue(result["low_confidence_observed"])
        self.assertEqual(result["low_confidence_or_error_handling"], "manual_review")

    def test_exact_numeric_tolerance_and_regex_error(self):
        case = {"expected": {"answer": 18}, "grading": "numeric", "tolerance": 0}
        self.assertFalse(grade(case, {"answer": 18.5})["passed"])
        self.assertTrue(grade(case, {"answer": 18.0})["passed"])
        trial = AgentTrial(None, None, [], Path.cwd(), "synthetic", "low")
        result = trial._compute({"operation": "regex", "data": {"pattern": "[", "text": "x"}})
        self.assertFalse(result["success"])

    def test_checkpoint_identity_and_latest_attempt(self):
        rows = [{"case_id": "a", "repeat": 0, "success": False},
                {"case_id": "a", "repeat": 0, "success": True}]
        self.assertTrue(latest(rows, ("case_id", "repeat"))[0]["success"])
        metadata = {k: 1 for k in ("model", "effort", "repeats", "arms", "manifest_sha256", "source_hashes", "runner_hashes", "phase")}
        with self.assertRaises(ValueError):
            assert_same_measurement(metadata, {**metadata, "model": 2})

    def test_replay_matches_selected_primitive(self):
        template = {"confidence": .02}
        result = replay_response(template, "jev_evaluate", {"questions": {
            "pick": {"type": "choice", "criteria": {"A": "first", "B": "second"}},
            "present": {"type": "noul"}}})
        self.assertEqual(result["answers"]["pick"]["choice"], "A")
        self.assertAlmostEqual(result["answers"]["present"]["noul"], .51)
        score = replay_response(template, "jev_score", {"criteria": ["low", "high"]})
        self.assertEqual(score["legend"], {"0": "low", "1": "high"})
        self.assertAlmostEqual(sum(score["probabilities"].values()), 1)
        self.assertAlmostEqual(score["score"], .49)

    def test_declared_equivalent_formats(self):
        numbered = {"expected": {"answer": "3", "accepted_answers": ["3", 3]}, "grading": "exact"}
        self.assertTrue(grade(numbered, {"answer": 3})["passed"])
        self.assertFalse(grade(numbered, {"answer": 2})["passed"])
        missing = {"expected": {"answer": "unknown", "accepted_answers": ["unknown", None], "abstain": True}, "grading": "exact"}
        self.assertTrue(grade(missing, {"answer": None, "abstain": True})["passed"])
        self.assertFalse(grade(missing, {}, require_behavior=False)["passed"])
        color = {"expected": {"answer": "yellow", "normalization": "casefold"}, "grading": "exact"}
        self.assertTrue(grade(color, {"answer": "Yellow"})["passed"])
        self.assertFalse(grade(color, {"answer": "red"})["passed"])


class LifecycleChecks(unittest.IsolatedAsyncioTestCase):
    async def test_rejected_resume_does_not_regenerate_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            image = output / "original.png"
            image.write_bytes(b"original-evidence")
            (output / "manifest.json").write_text(json.dumps([{"id": "synthetic"}]))
            previous = {k: 1 for k in ("model", "effort", "repeats", "arms", "manifest_sha256", "source_hashes", "runner_hashes", "phase")}
            metadata_file = output / "metadata.json"
            metadata_file.write_text(json.dumps(previous))
            args = SimpleNamespace(output=str(output), resume=True, cases=None)
            with patch("evals.run.snapshot", return_value={**previous, "model": 2}), patch(
                "evals.run.build_cases", side_effect=AssertionError("Must not regenerate")):
                with self.assertRaisesRegex(ValueError, "changed model"):
                    await run(args)
            self.assertEqual(image.read_bytes(), b"original-evidence")
            self.assertEqual(json.loads(metadata_file.read_text()), previous)

    async def test_start_failure_removes_temporary_auth(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            auth_home, runtime = root / "original", root / "runtime"
            auth_home.mkdir()
            runtime.mkdir()
            (auth_home / "auth.json").write_text('{"test": "synthetic-token"}')
            with patch.dict(os.environ, {"CODEX_HOME": str(auth_home)}):
                with patch("evals.rpc.codex_binary", return_value="synthetic"), patch(
                    "asyncio.create_subprocess_exec", new=AsyncMock(side_effect=OSError("synthetic failure"))):
                    with self.assertRaises(OSError):
                        async with CodexRPC(runtime):
                            self.fail("Should not enter")
            self.assertEqual(list(runtime.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
