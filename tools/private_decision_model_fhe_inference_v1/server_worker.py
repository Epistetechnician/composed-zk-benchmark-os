"""Ciphertext-only local server process for the private-decision FHE V1 slice.

State slice: private-decision-model-fhe-inference-v1.
The worker receives no client secret key and no clear feature array.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any

from concrete import fhe


def _decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _validate_evaluation_request(request: Any) -> None:
    if not isinstance(request, dict) or set(request) != {
        "evaluation_keys",
        "encrypted_arguments",
    }:
        raise ValueError("evaluation request must contain only evaluation keys and encrypted arguments")
    if not isinstance(request["evaluation_keys"], str):
        raise ValueError("evaluation keys must be serialized ciphertext-compatible bytes")
    if not isinstance(request["encrypted_arguments"], list) or not request[
        "encrypted_arguments"
    ]:
        raise ValueError("evaluation request must contain encrypted arguments")
    if len(request["encrypted_arguments"]) > 16 or not all(
        isinstance(argument, str) for argument in request["encrypted_arguments"]
    ):
        raise ValueError("evaluation request contains an invalid encrypted-argument list")


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: server_worker.py <client-specs|evaluate> <server-bundle>")

    mode, bundle = sys.argv[1:]
    if not Path(bundle).is_file():
        raise SystemExit("server bundle is missing")

    server = fhe.Server.load(bundle)
    if mode == "client-specs":
        sys.stdout.write(_encode(server.client_specs.serialize()))
        return 0
    if mode != "evaluate":
        raise SystemExit("unknown worker mode")

    request = json.load(sys.stdin)
    _validate_evaluation_request(request)
    evaluation_keys = fhe.EvaluationKeys.deserialize(_decode(request["evaluation_keys"]))
    results: list[str] = []
    for serialized_argument in request["encrypted_arguments"]:
        encrypted_argument = fhe.Value.deserialize(_decode(serialized_argument))
        encrypted_result = server.run(encrypted_argument, evaluation_keys=evaluation_keys)
        results.append(_encode(encrypted_result.serialize()))

    json.dump({"encrypted_results": results}, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
