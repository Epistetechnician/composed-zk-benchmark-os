"""Closed-world local FHE IPC contract for V2.

State slices: private-decision-model-fhe-local-ipc-contract-v2 and
global-experiment-assurance-lifecycle-v1. V1 inputs remain frozen.
"""

from __future__ import annotations

import base64
import binascii
import json
from typing import Any

STATE_SLICE = "private-decision-model-fhe-local-ipc-contract-v2"
EVALUATION_REQUEST_COUNT = 8


class ContractError(ValueError):
    """Raised when an IPC envelope violates the frozen V2 contract."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ContractError(f"non-standard JSON constant: {value}")


def strict_json_loads(raw: str) -> Any:
    """Parse JSON while rejecting duplicate keys and non-standard constants."""
    if not isinstance(raw, str):
        raise ContractError("JSON input must be text")
    try:
        return json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ContractError("invalid JSON input") from error


def decode_canonical_base64(value: Any, field: str) -> bytes:
    """Decode a non-empty canonical standard-Base64 string."""
    if not isinstance(value, str) or not value:
        raise ContractError(f"{field} must be a non-empty Base64 string")
    try:
        encoded = value.encode("ascii")
        decoded = base64.b64decode(encoded, validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError) as error:
        raise ContractError(f"{field} is not valid Base64") from error
    if not decoded or base64.b64encode(decoded).decode("ascii") != value:
        raise ContractError(f"{field} is empty or non-canonical Base64")
    return decoded


def validate_evaluation_request(
    value: Any,
    expected_count: int = EVALUATION_REQUEST_COUNT,
) -> dict[str, Any]:
    """Validate the fixed-shape server request and return its parsed object."""
    if not isinstance(value, dict) or set(value) != {
        "evaluation_keys",
        "encrypted_arguments",
    }:
        raise ContractError(
            "evaluation request must contain only evaluation keys and encrypted arguments"
        )
    decode_canonical_base64(value["evaluation_keys"], "evaluation_keys")
    arguments = value["encrypted_arguments"]
    if not isinstance(arguments, list) or len(arguments) != expected_count:
        raise ContractError(
            f"encrypted_arguments must contain exactly {expected_count} items"
        )
    for index, argument in enumerate(arguments):
        decode_canonical_base64(argument, f"encrypted_arguments[{index}]")
    return value


def validate_evaluation_response(
    value: Any,
    expected_count: int = EVALUATION_REQUEST_COUNT,
) -> dict[str, Any]:
    """Validate the fixed-shape client response and return its parsed object."""
    if not isinstance(value, dict) or set(value) != {"encrypted_results"}:
        raise ContractError("evaluation response must contain only encrypted_results")
    results = value["encrypted_results"]
    if not isinstance(results, list) or len(results) != expected_count:
        raise ContractError(
            f"encrypted_results must contain exactly {expected_count} items"
        )
    for index, result in enumerate(results):
        decode_canonical_base64(result, f"encrypted_results[{index}]")
    return value


def parse_evaluation_request(raw: str) -> dict[str, Any]:
    return validate_evaluation_request(strict_json_loads(raw))


def parse_evaluation_response(raw: str) -> dict[str, Any]:
    return validate_evaluation_response(strict_json_loads(raw))
