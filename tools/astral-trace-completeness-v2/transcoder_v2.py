"""Model-matched Gemma Scope 2 transcoder loading and qualification metrics.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import protocol_v2 as protocol


@dataclass(frozen=True)
class AssetRecord:
    layer_index: int
    config_path: Path
    params_path: Path
    config_sha256: str
    params_sha256: str

    def public_identity(self) -> dict[str, Any]:
        return {
            "layer_index": self.layer_index,
            "config_sha256": self.config_sha256,
            "params_sha256": self.params_sha256,
        }


@lru_cache(maxsize=2)
def asset_records(root: Path = protocol.ASSET_ROOT) -> tuple[AssetRecord, ...]:
    records = []
    for layer in range(protocol.LAYER_COUNT):
        folder = root / "transcoder_all" / f"layer_{layer}_width_16k_l0_small"
        config_path = folder / "config.json"
        params_path = folder / "params.safetensors"
        if not config_path.is_file() or not params_path.is_file():
            raise protocol.ProtocolError(f"missing transcoder asset for layer {layer}")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        expected = {
            "hf_hook_point_in": f"model.layers.{layer}.pre_feedforward_layernorm.output",
            "hf_hook_point_out": f"model.layers.{layer}.post_feedforward_layernorm.output",
            "width": protocol.FEATURE_WIDTH,
            "model_name": protocol.MODEL_ID,
            "architecture": "jump_relu",
            "affine_connection": False,
            "type": "transcoder",
        }
        if any(config.get(key) != value for key, value in expected.items()):
            raise protocol.ProtocolError(f"transcoder config mismatch for layer {layer}")
        records.append(
            AssetRecord(
                layer,
                config_path,
                params_path,
                protocol.sha256_file(config_path),
                protocol.sha256_file(params_path),
            )
        )
    return tuple(records)


def asset_manifest(root: Path = protocol.ASSET_ROOT) -> dict[str, Any]:
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "repository": protocol.ASSET_REPOSITORY,
        "revision": protocol.ASSET_REVISION,
        "variant": "transcoder_all/width_16k_l0_small",
        "records": [record.public_identity() for record in asset_records(root)],
    }
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def load_transcoder(layer_index: int, *, root: Path = protocol.ASSET_ROOT, device: Any = None, dtype: Any = None) -> Any:
    if not 0 <= layer_index < protocol.LAYER_COUNT:
        raise protocol.ProtocolError("transcoder layer is outside the frozen registry")
    import torch
    from circuit_tracer.transcoder.single_layer_transcoder import load_gemma_scope_2_transcoder

    record = asset_records(root)[layer_index]
    return load_gemma_scope_2_transcoder(
        str(record.params_path),
        layer_index,
        device=torch.device(device or "cpu"),
        dtype=dtype or torch.float32,
    )


def normalized_reconstruction_mse(transcoder: Any, input_acts: Any, target_acts: Any) -> float:
    import torch

    with torch.no_grad():
        reconstruction = transcoder(input_acts)
        numerator = torch.mean((reconstruction.float() - target_acts.float()) ** 2)
        baseline = torch.mean((target_acts.float() - target_acts.float().mean(dim=-1, keepdim=True)) ** 2)
        if float(baseline.item()) <= 0:
            raise protocol.ProtocolError("zero-variance reconstruction target")
        return float((numerator / baseline).item())


def feature_stability_cosine(transcoder: Any, first: Any, second: Any) -> float:
    import torch
    import torch.nn.functional as functional

    with torch.no_grad():
        first_features = transcoder.encode(first).float().reshape(-1)
        second_features = transcoder.encode(second).float().reshape(-1)
        if not torch.any(first_features) or not torch.any(second_features):
            return 0.0
        return float(functional.cosine_similarity(first_features, second_features, dim=0).item())


def top_feature(transcoder: Any, input_acts: Any) -> tuple[int, float]:
    import torch

    with torch.no_grad():
        features = transcoder.encode(input_acts).float()
        reduced = features.reshape(-1, features.shape[-1]).mean(dim=0)
        value, index = torch.max(reduced, dim=0)
        return int(index.item()), float(value.item())


def ablated_reconstruction(transcoder: Any, input_acts: Any, feature_index: int) -> Any:
    import torch

    if not 0 <= feature_index < protocol.FEATURE_WIDTH:
        raise protocol.ProtocolError("feature index outside frozen transcoder width")
    with torch.no_grad():
        features = transcoder.encode(input_acts)
        ablated = features.clone()
        ablated[..., feature_index] = 0
        return transcoder.decode(ablated, input_acts)
