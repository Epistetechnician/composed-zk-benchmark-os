"""Hermetic tests for private-decision-model-fhe-local-ipc-contract-v3.

State slices: private-decision-model-fhe-local-ipc-contract-v3 and
global-experiment-assurance-lifecycle-v1.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
V1_DIR = ROOT.parent / "private_decision_model_fhe_inference_v1"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(V1_DIR))

from ipc_contract import (  # noqa: E402
    ContractError,
    parse_evaluation_request,
    parse_evaluation_response,
    strict_json_loads,
    validate_evaluation_request,
    validate_evaluation_response,
)
import run_v3  # noqa: E402


def _encoded(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _request() -> dict[str, object]:
    return {
        "evaluation_keys": _encoded(b"evaluation-keys"),
        "encrypted_arguments": [_encoded(f"ciphertext-{index}".encode()) for index in range(8)],
    }


def _response() -> dict[str, object]:
    return {"encrypted_results": [_encoded(f"result-{index}".encode()) for index in range(8)]}


class StrictJsonTests(unittest.TestCase):
    def test_accepts_object_roots_with_nested_schema_values(self) -> None:
        self.assertEqual(strict_json_loads('{"values":[],"enabled":true,"empty":null}'),
                         {"values": [], "enabled": True, "empty": None})

    def test_rejects_duplicate_keys_at_root_and_nested_depth(self) -> None:
        for raw in ('{"key":1,"key":2}', '{"outer":{"key":1,"key":2}}'):
            with self.subTest(raw=raw), self.assertRaisesRegex(
                ContractError, "duplicate JSON object key"
            ):
                strict_json_loads(raw)

    def test_rejects_invalid_json_non_object_roots_and_nonstandard_constants(self) -> None:
        for raw in (
            "{broken", "[]", '"text"', "1", "true", "false", "null", "NaN",
            '{"value":Infinity}',
        ):
            with self.subTest(raw=raw), self.assertRaises(ContractError):
                strict_json_loads(raw)


class EvaluationRequestContractTests(unittest.TestCase):
    def test_accepts_exact_fixed_request(self) -> None:
        self.assertEqual(validate_evaluation_request(_request()), _request())
        self.assertEqual(parse_evaluation_request(json.dumps(_request())), _request())

    def test_rejects_missing_or_extra_fields(self) -> None:
        request = _request()
        with self.assertRaisesRegex(ContractError, "only evaluation keys"):
            validate_evaluation_request({"encrypted_arguments": request["encrypted_arguments"]})
        request["clear_features"] = "sentinel"
        with self.assertRaisesRegex(ContractError, "only evaluation keys"):
            validate_evaluation_request(request)

    def test_rejects_wrong_field_types_and_argument_counts(self) -> None:
        for bad in (
            {"evaluation_keys": 1, "encrypted_arguments": _request()["encrypted_arguments"]},
            {"evaluation_keys": _encoded(b"keys"), "encrypted_arguments": "not-a-list"},
            {"evaluation_keys": _encoded(b"keys"), "encrypted_arguments": []},
            {"evaluation_keys": _encoded(b"keys"), "encrypted_arguments": _request()["encrypted_arguments"][:7]},
        ):
            with self.subTest(bad=bad), self.assertRaises(ContractError):
                validate_evaluation_request(bad)

    def test_rejects_empty_invalid_and_noncanonical_base64(self) -> None:
        valid = _request()
        cases = [
            dict(valid, evaluation_keys=""),
            dict(valid, evaluation_keys="%%%="),
            dict(valid, encrypted_arguments=["Zh=="] + valid["encrypted_arguments"][1:]),
            dict(valid, encrypted_arguments=[""] + valid["encrypted_arguments"][1:]),
        ]
        for bad in cases:
            with self.subTest(bad=bad), self.assertRaises(ContractError):
                validate_evaluation_request(bad)

    def test_parse_rejects_duplicate_field_before_contract_validation(self) -> None:
        arguments = ",".join('"YQ=="' for _ in range(8))
        raw = (
            '{"evaluation_keys":"YQ==","evaluation_keys":"Yg==",'
            f'"encrypted_arguments":[{arguments}]}}'
        )
        with self.assertRaisesRegex(ContractError, "duplicate JSON object key"):
            parse_evaluation_request(raw)


class EvaluationResponseContractTests(unittest.TestCase):
    def test_accepts_exact_fixed_response(self) -> None:
        self.assertEqual(validate_evaluation_response(_response()), _response())
        self.assertEqual(parse_evaluation_response(json.dumps(_response())), _response())

    def test_rejects_missing_or_extra_fields(self) -> None:
        with self.assertRaisesRegex(ContractError, "only encrypted_results"):
            validate_evaluation_response({})
        with self.assertRaisesRegex(ContractError, "only encrypted_results"):
            validate_evaluation_response(dict(_response(), diagnostics="unexpected"))

    def test_rejects_wrong_result_type_count_and_encoding(self) -> None:
        for bad in (
            {"encrypted_results": "not-a-list"},
            {"encrypted_results": _response()["encrypted_results"][:7]},
            {"encrypted_results": [1] * 8},
            {"encrypted_results": [""] + _response()["encrypted_results"][1:]},
            {"encrypted_results": ["%%%="] + _response()["encrypted_results"][1:]},
            {"encrypted_results": ["Zh=="] + _response()["encrypted_results"][1:]},
        ):
            with self.subTest(bad=bad), self.assertRaises(ContractError):
                validate_evaluation_response(bad)

    def test_parse_rejects_duplicate_result_field(self) -> None:
        encoded_results = ",".join('"YQ=="' for _ in range(8))
        raw = f'{{"encrypted_results":[{encoded_results}],"encrypted_results":[{encoded_results}]}}'
        with self.assertRaisesRegex(ContractError, "duplicate JSON object key"):
            parse_evaluation_response(raw)


class WorkerBoundaryTests(unittest.TestCase):
    def test_worker_rejects_non_object_root_before_loading_bundle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fhe-ipc-v3-test-") as temp:
            missing_bundle = Path(temp) / "does-not-exist.zip"
            process = subprocess.run(
                [sys.executable, str(ROOT / "server_worker_v3.py"), "evaluate", str(missing_bundle)],
                input="[]",
                text=True,
                capture_output=True,
                check=False,
                timeout=30,
                close_fds=True,
                env=run_v3._worker_environment(),
            )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(process.stdout, "")
        self.assertIn("JSON root must be an object", process.stderr)
        self.assertNotIn("server bundle is missing", process.stderr)

    def test_worker_environment_omits_credentials_and_parent_configuration(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "AWS_SECRET_ACCESS_KEY": "synthetic-sentinel",
                "OPENAI_API_KEY": "synthetic-sentinel",
                "TMPDIR": "/tmp",
            },
            clear=True,
        ):
            self.assertEqual(run_v3._worker_environment(), {"TMPDIR": "/tmp"})


if __name__ == "__main__":
    unittest.main()
