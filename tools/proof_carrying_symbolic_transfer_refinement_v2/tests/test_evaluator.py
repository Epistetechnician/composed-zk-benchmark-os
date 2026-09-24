"""Behavioral tests for the proof-carrying symbolic transfer V2 slice."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.proof_carrying_symbolic_transfer_refinement_v2.evaluator import (
    EvaluationError,
    evaluate_episode,
    identity_candidate,
    load_fixture,
    run_protocol,
    synthesize_candidate,
    verify_receipt,
)
from tools.proof_carrying_symbolic_transfer_refinement_v2.model import (
    Discovery,
    canonical_json,
)


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "tools/proof_carrying_symbolic_transfer_refinement_v2/fixtures.json"


class EvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.episodes = load_fixture(FIXTURE)
        self.episode = self.episodes[0]

    def test_public_only_synthesizer_passes_and_is_truth_invariant(self) -> None:
        result = evaluate_episode(synthesize_candidate, self.episode)
        self.assertEqual(result.correct, result.task_count)
        self.assertEqual(result.accuracy, 1.0)

    def test_candidate_cannot_read_hidden_truth(self) -> None:
        def leaking_candidate(tasks):
            return tuple(
                Discovery(task.task_id, f"leak:{task.task_id}", tuple(getattr(task, "hidden_program")))
                for task in tasks
            )

        with self.assertRaises(EvaluationError):
            evaluate_episode(leaking_candidate, self.episode)

    def test_duplicate_discoveries_are_rejected(self) -> None:
        def duplicate_candidate(tasks):
            return tuple(Discovery(task.task_id, "same-id", ()) for task in tasks)

        with self.assertRaisesRegex(EvaluationError, "duplicated"):
            evaluate_episode(duplicate_candidate, self.episode)

    def test_metric_gaming_is_rejected_and_score_is_not_candidate_supplied(self) -> None:
        def gaming_candidate(tasks):
            return tuple(
                Discovery(task.task_id, f"metric:{task.task_id}", (), reported_metric=1.0)
                for task in tasks
            )

        with self.assertRaisesRegex(EvaluationError, "reported metrics"):
            evaluate_episode(gaming_candidate, self.episode)
        self.assertEqual(evaluate_episode(identity_candidate, self.episode).accuracy, 0.0)

    def test_protocol_runs_multiple_seeds_and_emits_deterministic_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = run_protocol(FIXTURE, Path(first_dir))
            second = run_protocol(FIXTURE, Path(second_dir))
            self.assertEqual(first, second)
            verify_receipt(first)
            self.assertEqual({row["seed"] for row in first["episodes"]}, {101, 202})
            self.assertEqual({row["split"] for row in first["episodes"]}, {"fit", "tune", "held_out"})
            receipt_text = (Path(first_dir) / "receipt.json").read_text(encoding="utf-8")
            self.assertEqual(receipt_text, canonical_json(first) + "\n")

    def test_malformed_digest_and_unknown_receipt_field_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            receipt = run_protocol(FIXTURE, Path(output_dir))
        malformed = dict(receipt)
        malformed["fixture_digest"] = "not-a-digest"
        with self.assertRaises(EvaluationError):
            verify_receipt(malformed)
        unknown = dict(receipt)
        unknown["unexpected"] = True
        with self.assertRaises(EvaluationError):
            verify_receipt(unknown)

    def test_fixture_unknown_field_fails_closed(self) -> None:
        value = json.loads(FIXTURE.read_text(encoding="utf-8"))
        value["episodes"][0]["unexpected"] = True
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as handle:
            json.dump(value, handle)
            handle.flush()
            with self.assertRaises((EvaluationError, ValueError)):
                load_fixture(Path(handle.name))


if __name__ == "__main__":
    unittest.main()
