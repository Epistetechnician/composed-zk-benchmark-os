"""Run one local synthetic FHE execution through the strict V2 IPC contract.

State slices: private-decision-model-fhe-local-ipc-contract-v2 and
global-experiment-assurance-lifecycle-v1. The V1 model and fixture are frozen
dependencies; no user data or network service is used.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from concrete import fhe

ROOT = Path(__file__).resolve().parents[2]
V1_DIR = ROOT / "tools" / "private_decision_model_fhe_inference_v1"
sys.path.insert(0, str(V1_DIR))
import decision_model  # noqa: E402  (pinned, frozen V1 fixture dependency)

from ipc_contract import (  # noqa: E402
    decode_canonical_base64,
    parse_evaluation_response,
    validate_evaluation_request,
)

STATE_SLICE = "private-decision-model-fhe-local-ipc-contract-v2"
BASE_REVISION = "62bf2bfb5b6775327eb635d722bd2a715a2c6a42"
V1_SOURCE_SHA256 = "41bdd10bd882d7f7174fdfadae4f8b9688a28dab2bb839f11a93bbf660d5ad47"
V1_LOCK_SHA256 = "cf9852e2b16da1d6dabb13fd9fbcf368e36822043907aa0a5154589504b0a8b2"
V1_FIXTURE_SHA256 = "7144207ead235b20cea7a26b899c42fc7249a66b9dfc12a1f02d68fe2da534f7"
WORKER = Path(__file__).with_name("server_worker_v2.py")
_WORKER_ENV_ALLOWLIST = frozenset({"LANG", "LC_ALL", "PATH", "TMP", "TEMP", "TMPDIR"})
_SOURCE_FILES = (
    Path(__file__),
    WORKER,
    Path(__file__).with_name("ipc_contract.py"),
    Path(__file__).with_name("tests") / "test_ipc_contract.py",
    V1_DIR / "decision_model.py",
)


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _worker_environment() -> dict[str, str]:
    """Pass only basic runtime variables to the local worker process."""
    return {
        key: value
        for key, value in os.environ.items()
        if key in _WORKER_ENV_ALLOWLIST
    }


def _source_digest() -> str:
    digest = hashlib.sha256()
    for path in _SOURCE_FILES:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _run_worker(mode: str, bundle: Path, payload: dict[str, Any] | None = None) -> str:
    process = subprocess.run(
        [sys.executable, str(WORKER), mode, str(bundle)],
        input=None if payload is None else json.dumps(payload, sort_keys=True),
        text=True,
        capture_output=True,
        check=False,
        timeout=900,
        close_fds=True,
        env=_worker_environment(),
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"local V2 FHE worker failed with exit {process.returncode}: "
            f"{process.stderr.strip() or 'no diagnostic'}"
        )
    return process.stdout


def execute() -> dict[str, Any]:
    fixture_sha256 = decision_model.synthetic_fixture_sha256()
    if fixture_sha256 != V1_FIXTURE_SHA256:
        raise RuntimeError("the frozen V1 synthetic fixture digest changed")

    calibration = decision_model.synthetic_calibration_requests()
    evaluation = decision_model.synthetic_evaluation_requests()
    decision_model.validate_request_batch(
        calibration, expected_count=decision_model.CALIBRATION_REQUESTS
    )
    decision_model.validate_request_batch(
        evaluation, expected_count=decision_model.EVALUATION_REQUESTS
    )

    compiler = fhe.Compiler(decision_model.option_scores, {"features": "encrypted"})
    circuit = compiler.compile([(request,) for request in calibration])

    score_matches = 0
    top_choice_matches = 0
    temporary_path: Path | None = None
    with tempfile.TemporaryDirectory(prefix="private-decision-fhe-ipc-v2-") as temporary_root:
        temporary_path = Path(temporary_root)
        server_bundle = temporary_path / "server.zip"
        circuit.server.save(str(server_bundle))

        client_specs_bytes = decode_canonical_base64(
            _run_worker("client-specs", server_bundle).strip(),
            "client_specs",
        )
        client = fhe.Client(fhe.ClientSpecs.deserialize(client_specs_bytes))
        client.keys.generate()

        request_payload = {
            "evaluation_keys": _encode(client.evaluation_keys.serialize()),
            "encrypted_arguments": [
                _encode(client.encrypt(request).serialize()) for request in evaluation
            ],
        }
        validate_evaluation_request(request_payload)
        raw_response = _run_worker("evaluate", server_bundle, request_payload)
        response = parse_evaluation_response(raw_response)
        encrypted_results = response["encrypted_results"]

        for request, serialized_result in zip(evaluation, encrypted_results, strict=True):
            decrypted = client.decrypt(
                fhe.Value.deserialize(
                    decode_canonical_base64(serialized_result, "encrypted_result")
                )
            )
            actual_scores = np.asarray(decrypted, dtype=np.int64).reshape(
                decision_model.OPTIONS_PER_REQUEST
            )
            expected_scores = decision_model.option_scores(request)
            if not np.array_equal(actual_scores, expected_scores):
                raise RuntimeError("V2 encrypted scores differ from the frozen clear scorer")
            score_matches += int(actual_scores.size)
            top_choice_matches += int(np.argmax(actual_scores) == np.argmax(expected_scores))

    temporary_files_removed = temporary_path is not None and not temporary_path.exists()
    if not temporary_files_removed:
        raise RuntimeError("V2 temporary FHE artifacts were not removed")
    if score_matches != decision_model.EVALUATION_REQUESTS * decision_model.OPTIONS_PER_REQUEST:
        raise RuntimeError("V2 did not check every frozen synthetic option score")
    if top_choice_matches != decision_model.EVALUATION_REQUESTS:
        raise RuntimeError("V2 did not preserve every frozen top-ranked option")

    return {
        "schema": "private-decision-model-fhe-local-ipc-contract-v2-result",
        "state_slice": STATE_SLICE,
        "governance_state_slice": "global-experiment-assurance-lifecycle-v1",
        "assurance": "INTERNAL_PASS",
        "reviewer_status": "EXTERNAL_REVIEW_UNAVAILABLE",
        "reproducibility_status": "single local V2 qualification; not REPRODUCED_LOCAL",
        "baseline_revision": BASE_REVISION,
        "v1_source_sha256": V1_SOURCE_SHA256,
        "v2_source_sha256": _source_digest(),
        "v1_dependency_lock_sha256": V1_LOCK_SHA256,
        "claim_ceiling": "LocalDevelopmentSyntheticFHEIPCContractQualificationV2",
        "runtime": {
            "python": platform.python_version(),
            "concrete_python": importlib.metadata.version("concrete-python"),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "fixture": {
            "sha256": fixture_sha256,
            "expected_sha256": V1_FIXTURE_SHA256,
            "evaluation_requests": decision_model.EVALUATION_REQUESTS,
            "options_per_request": decision_model.OPTIONS_PER_REQUEST,
            "features_per_option": decision_model.FEATURE_COUNT,
        },
        "execution": {
            "strict_request_schema": True,
            "strict_response_schema": True,
            "duplicate_json_keys_rejected_by_contract": True,
            "encrypted_scores_matching_clear_scores": score_matches,
            "top_ranked_options_matching": top_choice_matches,
            "client_secret_key_sent_to_worker": False,
            "clear_features_sent_to_worker": False,
            "network_during_execution": False,
            "temporary_fhe_files_removed": temporary_files_removed,
        },
        "custody": "V1 synthetic fixture only; temporary keys, bundle, ciphertexts, responses, and arrays removed",
        "known_limitations": [
            "same-host and same-user local process boundary",
            "model weights are clear in the compiled server circuit",
            "no real-data utility or remote-service behavior was measured",
            "no cryptographic security or production claim is made",
            "external review was not performed",
        ],
        "next_blocked_authority_gate": "fresh scope and packet plus any required owner or independent authority before real data, remote service, paid execution, or public claims",
    }


def main() -> int:
    result = execute()
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
