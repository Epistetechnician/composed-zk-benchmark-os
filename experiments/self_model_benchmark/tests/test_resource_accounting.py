import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.self_model_benchmark.protocol import digest_json
from experiments.self_model_benchmark.repository_change_capture import load_capture, write_jsonl
from experiments.self_model_benchmark.resource_accounting import (
    CLAIM_CEILING,
    ResourceAccountingError,
    build_report_from_capture,
    main as resource_accounting_main,
    validate_report,
)
from experiments.self_model_benchmark.tests.test_repository_change_capture import _live_capture_records


class ResourceAccountingTests(unittest.TestCase):
    # State slice: verified-self-model-benchmark-resource-accounting-v1.
    def test_live_capture_preserves_resource_summary_by_variant(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            manifest, _ = load_capture(capture_path)
            report = build_report_from_capture(capture_path)

        validate_report(report, manifest)
        self.assertEqual(report["claim_ceiling"], CLAIM_CEILING)
        self.assertEqual(report["observation_count"], 300)
        self.assertEqual(report["overall"]["failure_count"], 120)
        self.assertEqual(report["overall"]["failure_rate"], 0.4)
        self.assertEqual(report["overall"]["max_latency_ms"], 700.0)
        self.assertEqual(report["overall"]["max_compute_units"], 70.0)
        self.assertEqual(report["overall"]["max_tool_calls"], 3.0)
        self.assertEqual(report["overall"]["max_attempts"], 2.0)
        self.assertEqual(report["by_variant"]["base"]["failure_count"], 0)
        self.assertEqual(report["by_variant"]["memory_reset"]["failure_count"], 60)
        self.assertEqual(report["by_variant"]["policy_restricted"]["failure_count"], 60)
        for field in ("scientific_evidence", "authority_granted", "network_access", "raw_reasoning_retained"):
            self.assertFalse(report[field])

    def test_cli_emits_digest_bound_smoke_resource_report(self):
        fixture = Path("experiments/self_model_benchmark/fixtures/repository_change_capture_smoke.jsonl")
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "resource-report.json"
            with patch.object(
                sys,
                "argv",
                ["resource-accounting", "--input", str(fixture), "--output", str(output_path)],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(resource_accounting_main(), 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
        validate_report(report)
        self.assertEqual(report["source_type"], "contract_smoke_fixture")
        self.assertEqual(report["observation_count"], 5)
        self.assertEqual(report["claim_ceiling"], CLAIM_CEILING)

    def test_recomputed_report_digest_cannot_forge_budget_headroom(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            manifest, _ = load_capture(capture_path)
            report = build_report_from_capture(capture_path)

        tampered = dict(report)
        tampered["overall"] = dict(report["overall"])
        tampered["overall"]["max_compute_units"] = manifest["budget"]["max_compute_units"] + 1.0
        tampered["report_digest"] = digest_json({key: value for key, value in tampered.items() if key != "report_digest"})
        with self.assertRaisesRegex(ResourceAccountingError, "exceeds fixed budget"):
            validate_report(tampered, manifest)

    def test_incomplete_variant_set_fails_closed(self):
        records = _live_capture_records()
        records = [records[0], *[record for record in records[1:] if record["variant"] != "policy_restricted"]]
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            write_jsonl(capture_path, records)
            with self.assertRaisesRegex(ResourceAccountingError, "every frozen variant"):
                build_report_from_capture(capture_path)


if __name__ == "__main__":
    unittest.main()
