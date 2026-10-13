"""Run the bounded local synthetic FHE inference demonstration.

State slice: private-decision-model-fhe-inference-v1.
This command contacts no network service and reads no user data.
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

import decision_model

ROOT = Path(__file__).resolve().parents[2]
WORKER = Path(__file__).with_name("server_worker.py")
BASE_REVISION = "62bf2bfb5b6775327eb635d722bd2a715a2c6a42"
_WORKER_ENV_ALLOWLIST = frozenset({"LANG", "LC_ALL", "PATH", "TMP", "TEMP", "TMPDIR"})


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def _worker_environment() -> dict[str, str]:
    """Pass only basic runtime variables, never inherited credentials/config."""
    return {
        key: value
        for key, value in os.environ.items()
        if key in _WORKER_ENV_ALLOWLIST
    }


def _source_digest() -> str:
    digest = hashlib.sha256()
    for path in (Path(__file__), WORKER, Path(decision_model.__file__)):
        digest.update(path.name.encode("utf-8"))
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
            f"local FHE server worker failed with exit {process.returncode}: "
            f"{process.stderr.strip() or 'no diagnostic'}"
        )
    return process.stdout


def _verify_server_rejects_cleartext_payload(bundle: Path) -> None:
    payload = {
        "evaluation_keys": "not-a-key",
        "encrypted_arguments": ["not-a-ciphertext"],
        "clear_features": "synthetic red-team sentinel",
        "client_secret_key": "synthetic red-team sentinel",
    }
    process = subprocess.run(
        [sys.executable, str(WORKER), "evaluate", str(bundle)],
        input=json.dumps(payload, sort_keys=True),
        text=True,
        capture_output=True,
        check=False,
        timeout=900,
        close_fds=True,
        env=_worker_environment(),
    )
    if process.returncode == 0 or "only evaluation keys and encrypted arguments" not in process.stderr:
        raise RuntimeError("server worker did not reject extra cleartext/key fields")


def execute() -> dict[str, Any]:
    calibration = decision_model.synthetic_calibration_requests()
    evaluation = decision_model.synthetic_evaluation_requests()
    decision_model.validate_request_batch(
        calibration, expected_count=decision_model.CALIBRATION_REQUESTS
    )
    decision_model.validate_request_batch(
        evaluation, expected_count=decision_model.EVALUATION_REQUESTS
    )

    compiler = fhe.Compiler(decision_model.option_scores, {"features": "encrypted"})
    inputset = [(request,) for request in calibration]
    circuit = compiler.compile(inputset)

    score_matches = 0
    top_choice_matches = 0
    with tempfile.TemporaryDirectory(prefix="private-decision-fhe-v1-") as temporary_root:
        server_bundle = Path(temporary_root) / "server.zip"
        circuit.server.save(str(server_bundle))

        _verify_server_rejects_cleartext_payload(server_bundle)
        serialized_specs = _run_worker("client-specs", server_bundle)
        client_specs = fhe.ClientSpecs.deserialize(_decode(serialized_specs))
        client = fhe.Client(client_specs)
        client.keys.generate()

        encrypted_arguments = [
            _encode(client.encrypt(request).serialize()) for request in evaluation
        ]
        serialized_evaluation_keys = _encode(client.evaluation_keys.serialize())
        response = json.loads(
            _run_worker(
                "evaluate",
                server_bundle,
                {
                    "evaluation_keys": serialized_evaluation_keys,
                    "encrypted_arguments": encrypted_arguments,
                },
            )
        )

        encrypted_results = response["encrypted_results"]
        if len(encrypted_results) != len(evaluation):
            raise RuntimeError("server returned a different number of encrypted results")

        for request, serialized_result in zip(evaluation, encrypted_results, strict=True):
            decrypted = client.decrypt(fhe.Value.deserialize(_decode(serialized_result)))
            actual_scores = np.asarray(decrypted, dtype=np.int64).reshape(
                decision_model.OPTIONS_PER_REQUEST
            )
            expected_scores = decision_model.option_scores(request)
            if not np.array_equal(actual_scores, expected_scores):
                raise RuntimeError("decrypted FHE scores differ from the clear scorer")
            score_matches += int(actual_scores.size)
            top_choice_matches += int(np.argmax(actual_scores) == np.argmax(expected_scores))

    if score_matches != decision_model.EVALUATION_REQUESTS * decision_model.OPTIONS_PER_REQUEST:
        raise RuntimeError("not every synthetic option score was checked")
    if top_choice_matches != decision_model.EVALUATION_REQUESTS:
        raise RuntimeError("not every synthetic request preserved the top-ranked option")

    return {
        "schema": "private-decision-model-fhe-inference-result-v1",
        "state_slice": decision_model.STATE_SLICE,
        "assurance": "INTERNAL_PASS",
        "reviewer_status": "NOT_REQUESTED",
        "reproducibility_status": "single local execution; not REPRODUCED_LOCAL",
        "base_revision": BASE_REVISION,
        "source_sha256": _source_digest(),
        "claim_ceiling": "LocalDevelopmentSyntheticFHEInferenceV1",
        "runtime": {
            "python": platform.python_version(),
            "concrete_python": importlib.metadata.version("concrete-python"),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "fixture": {
            "kind": "deterministic synthetic only",
            "sha256": decision_model.synthetic_fixture_sha256(),
            "training_rows": decision_model.TRAIN_ROWS,
            "calibration_requests": decision_model.CALIBRATION_REQUESTS,
            "evaluation_requests": decision_model.EVALUATION_REQUESTS,
            "features_per_option": decision_model.FEATURE_COUNT,
            "options_per_request": decision_model.OPTIONS_PER_REQUEST,
        },
        "execution": {
            "encrypted_scores_exactly_matching_clear_scores": score_matches,
            "top_ranked_options_matching": top_choice_matches,
            "client_secret_key_sent_to_server_process": False,
            "clear_features_sent_to_server_process": False,
            "server_rejected_extra_cleartext_and_secret_key_fields": True,
            "unapproved_parent_environment_inherited": False,
            "server_process_receives": [
                "compiled server circuit",
                "encrypted feature tensors",
                "public evaluation keys",
            ],
            "client_decrypts_result": True,
            "network_during_execution": False,
        },
        "custody": "keys, circuit bundle, ciphertexts, and synthetic arrays were transient and removed at process exit",
        "known_limitations": [
            "the model is a small linear scorer trained only on a planted synthetic utility function",
            "model weights are clear in the compiled server circuit",
            "the server and client are local processes; this does not qualify a remote service",
            "no real-data utility, formal security, independent review, or production claim is established",
        ],
        "next_blocked_authority_gate": "a fresh slice and its required review and owner authorization are required before any real data, remote service, paid execution, or public claim",
    }


def main() -> int:
    result = execute()
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
