"""Strict-schema local FHE server worker for the V3 synthetic continuation.

State slices: private-decision-model-fhe-local-ipc-contract-v3 and
global-experiment-assurance-lifecycle-v1. No network interface is opened.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from concrete import fhe

from ipc_contract import ContractError, decode_canonical_base64, parse_evaluation_request

STATE_SLICE = "private-decision-model-fhe-local-ipc-contract-v3"


def _encode(value: bytes) -> str:
    import base64

    return base64.b64encode(value).decode("ascii")


def main() -> int:
    if len(sys.argv) != 3:
        sys.stderr.write("usage: server_worker_v3.py <client-specs|evaluate> <server-bundle>\n")
        return 2

    mode, bundle = sys.argv[1:]
    request: dict[str, object] | None = None
    if mode == "evaluate":
        try:
            request = parse_evaluation_request(sys.stdin.read())
        except (ContractError, UnicodeError) as error:
            sys.stderr.write(f"invalid evaluation request: {error}\n")
            return 2
    elif mode != "client-specs":
        sys.stderr.write("unknown worker mode\n")
        return 2

    bundle_path = Path(bundle)
    if not bundle_path.is_file():
        sys.stderr.write("server bundle is missing\n")
        return 2

    try:
        server = fhe.Server.load(str(bundle_path))
        if mode == "client-specs":
            sys.stdout.write(_encode(server.client_specs.serialize()))
            return 0

        assert request is not None
        evaluation_keys = fhe.EvaluationKeys.deserialize(
            decode_canonical_base64(request["evaluation_keys"], "evaluation_keys")
        )
        encrypted_results: list[str] = []
        for index, serialized_argument in enumerate(request["encrypted_arguments"]):
            encrypted_argument = fhe.Value.deserialize(
                decode_canonical_base64(serialized_argument, f"encrypted_arguments[{index}]")
            )
            encrypted_result = server.run(
                encrypted_argument,
                evaluation_keys=evaluation_keys,
            )
            encrypted_results.append(_encode(encrypted_result.serialize()))

        json.dump({"encrypted_results": encrypted_results}, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except Exception as error:
        sys.stderr.write(f"worker operation failed: {type(error).__name__}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
