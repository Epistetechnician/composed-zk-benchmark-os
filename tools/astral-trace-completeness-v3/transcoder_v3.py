"""V3 fixed affine Gemma Scope 2 transcoder loader.

State slice: astral-trace-completeness-gemma3-end-to-end-v3.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import protocol_v3 as protocol


def load(*, root: Path = protocol.ASSET_ROOT, device: str = "cpu", dtype: Any = None) -> Any:
    import torch
    from circuit_tracer.transcoder.single_layer_transcoder import load_gemma_scope_2_transcoder

    path = root / protocol.ASSET_VARIANT / "params.safetensors"
    if not path.is_file() or path.is_symlink():
        raise protocol.ProtocolError("V3 transcoder parameters are missing")
    return load_gemma_scope_2_transcoder(
        str(path),
        12,
        device=torch.device(device),
        dtype=dtype or torch.float32,
    )


def pooled_sufficient_statistics(transcoder: Any, input_acts: Any, target_acts: Any) -> dict[str, float | int]:
    import torch

    with torch.no_grad():
        transcoder_input = input_acts.to(transcoder.dtype)
        reconstruction = transcoder(transcoder_input)
        target = target_acts.float()
        error = reconstruction.float() - target
        if not bool(torch.isfinite(target).all().item()) or not bool(torch.isfinite(reconstruction).all().item()):
            raise protocol.ProtocolError("nonfinite reconstruction input or output")
        return {
            "sum_squared_error": float(torch.sum(error * error).item()),
            "target_sum": float(torch.sum(target).item()),
            "target_squared_sum": float(torch.sum(target * target).item()),
            "coordinate_count": int(target.numel()),
        }


def pooled_global_centered_nmse(statistics: list[dict[str, float | int]]) -> float:
    import math

    if not statistics:
        raise protocol.ProtocolError("empty reconstruction statistics")
    numerator = sum(float(item["sum_squared_error"]) for item in statistics)
    target_sum = sum(float(item["target_sum"]) for item in statistics)
    target_squared_sum = sum(float(item["target_squared_sum"]) for item in statistics)
    coordinate_count = sum(int(item["coordinate_count"]) for item in statistics)
    if coordinate_count <= 0:
        raise protocol.ProtocolError("empty reconstruction coordinate set")
    denominator = target_squared_sum - (target_sum * target_sum / coordinate_count)
    if not math.isfinite(denominator) or denominator <= 0:
        raise protocol.ProtocolError("zero or nonfinite pooled target variance")
    value = numerator / denominator
    if not math.isfinite(value):
        raise protocol.ProtocolError("nonfinite pooled reconstruction metric")
    return value


def feature_cosine(transcoder: Any, first: Any, second: Any) -> float:
    import torch
    import torch.nn.functional as functional

    with torch.no_grad():
        a = transcoder.encode(first.to(transcoder.dtype)).float().reshape(-1)
        b = transcoder.encode(second.to(transcoder.dtype)).float().reshape(-1)
        if not torch.any(a) or not torch.any(b):
            return 0.0
        return float(functional.cosine_similarity(a, b, dim=0).item())


def feature_vector_cosine(first: Any, second: Any) -> float:
    import torch
    import torch.nn.functional as functional

    with torch.no_grad():
        a = first.float().reshape(-1)
        b = second.float().reshape(-1)
        if not torch.any(a) or not torch.any(b):
            return 0.0
        return float(functional.cosine_similarity(a, b, dim=0).item())
