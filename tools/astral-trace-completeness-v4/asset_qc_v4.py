"""Asset-only quality gate for the V4 L0-big affine transcoder.

State slice: astral-trace-completeness-gemma3-end-to-end-v4.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import protocol_v4 as protocol

PARAMETER_SPECS = {
    "affine_skip_connection": ((protocol.HIDDEN_WIDTH, protocol.HIDDEN_WIDTH), "torch.float32"),
    "b_dec": ((protocol.HIDDEN_WIDTH,), "torch.float32"),
    "b_enc": ((protocol.FEATURE_WIDTH,), "torch.float32"),
    "threshold": ((protocol.FEATURE_WIDTH,), "torch.float32"),
    "w_dec": ((protocol.FEATURE_WIDTH, protocol.HIDDEN_WIDTH), "torch.float32"),
    "w_enc": ((protocol.HIDDEN_WIDTH, protocol.FEATURE_WIDTH), "torch.float32"),
}
EXAMPLE_SPECS = {
    "activations": ((protocol.FEATURE_WIDTH, 1000), "torch.float32"),
    "bottom_logits": ((protocol.FEATURE_WIDTH, 10), "torch.float32"),
    "bottom_tokens": ((protocol.FEATURE_WIDTH, 10), "torch.int32"),
    "feature_frequencies": ((protocol.FEATURE_WIDTH,), "torch.float64"),
    "logit_effects": ((protocol.FEATURE_WIDTH, 1000), "torch.float32"),
    "positions": ((protocol.FEATURE_WIDTH, 1000), "torch.int32"),
    "seq_ids": ((protocol.FEATURE_WIDTH, 1000), "torch.int64"),
    "tokens": ((392802, 256), "torch.int32"),
    "top_logits": ((protocol.FEATURE_WIDTH, 10), "torch.float32"),
    "top_tokens": ((protocol.FEATURE_WIDTH, 10), "torch.int32"),
}


def _write_private(path: Path, value: dict[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(protocol.canonical_bytes(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _tensor_specs(path: Path, expected: dict[str, tuple[tuple[int, ...], str]]) -> dict[str, Any]:
    from safetensors import safe_open

    with safe_open(str(path), framework="pt", device="cpu") as handle:
        observed = {}
        for key in handle.keys():
            tensor = handle.get_tensor(key)
            finite = bool(tensor.isfinite().all().item()) if tensor.is_floating_point() else True
            observed[key] = {"shape": tuple(int(item) for item in tensor.shape), "dtype": str(tensor.dtype), "finite": finite}
        if set(observed) != set(expected):
            raise protocol.ProtocolError(f"tensor key set mismatch for {path.name}")
        for key, (shape, dtype) in expected.items():
            actual = observed[key]
            if actual["shape"] != shape or actual["dtype"] != dtype or actual["finite"] is False:
                raise protocol.ProtocolError(f"tensor schema or finiteness mismatch: {path.name}:{key}")
    return {"keys": observed, "sha256": protocol.sha256_file(path), "bytes": path.stat().st_size}


def inspect_asset(asset_root: Path, *, repository_root: Path) -> dict[str, Any]:
    receipt = protocol.custody_receipt(protocol.CUSTODY_ROOT, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError(f"invalid V4 custody root: {receipt['errors']}")
    asset_dir = asset_root / protocol.ASSET_VARIANT
    config_path, params_path, examples_path = (asset_dir / name for name in ("config.json", "params.safetensors", "examples.safetensors"))
    for path in (config_path, params_path, examples_path):
        if not path.is_file() or path.is_symlink():
            raise protocol.ProtocolError(f"missing or symlinked asset: {path.name}")
    config = protocol.strict_json(config_path)
    expected_config = {
        "hf_hook_point_in": "model.layers.12.pre_feedforward_layernorm.output",
        "hf_hook_point_out": "model.layers.12.post_feedforward_layernorm.output",
        "width": protocol.FEATURE_WIDTH,
        "model_name": protocol.MODEL_ID,
        "architecture": "jump_relu",
        "l0": 120,
        "affine_connection": True,
        "type": "transcoder",
    }
    if config != expected_config:
        raise protocol.ProtocolError(f"asset config mismatch: {config}")
    params = _tensor_specs(params_path, PARAMETER_SPECS)
    examples = _tensor_specs(examples_path, EXAMPLE_SPECS)
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "asset_repository": protocol.ASSET_REPOSITORY,
        "asset_revision": protocol.ASSET_REVISION,
        "asset_variant": protocol.ASSET_VARIANT,
        "config_sha256": protocol.sha256_file(config_path),
        "params": params,
        "examples": examples,
        "examples_are_metadata_only": True,
        "reconstruction_target_source": "fresh_model_qualification_fit_rows",
        "valid": True,
        "model_execution": False,
        "assessment_opened": False,
        "custody": receipt,
    }
    protocol.reject_raw_fields(value)
    return {**value, "asset_qc_sha256": protocol.digest_json(value)}


def execute(repository_root: Path, custody_root: Path) -> dict[str, Any]:
    if custody_root.resolve() != protocol.CUSTODY_ROOT.resolve():
        raise protocol.ProtocolError("V4 custody identity is fixed")
    result = inspect_asset(custody_root / "assets" / "gemma-scope-2-1b-pt", repository_root=repository_root)
    output = custody_root / "aggregate" / "preload-asset-qc.json"
    _write_private(output, result)
    return {**result, "aggregate_path": str(output)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--custody-root", type=Path, default=protocol.CUSTODY_ROOT)
    args = parser.parse_args(argv)
    print(json.dumps(execute(args.repository_root.resolve(), args.custody_root.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
