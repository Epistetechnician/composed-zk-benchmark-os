"""Model-matched Gemma Scope 2 transcoder loader for V3.

State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import protocol_v3_slice as protocol


def load(*, root: Path, device: str = "cpu", dtype: Any = None) -> Any:
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


def encode_features(transcoder: Any, input_activation: Any) -> Any:
    with _no_grad():
        features = transcoder.encode(input_activation.to(transcoder.dtype))
        if not bool(_torch().isfinite(features).all().item()):
            raise protocol.ProtocolError("nonfinite feature activation")
        return features


def _torch() -> Any:
    import torch

    return torch


class _no_grad:
    def __enter__(self) -> None:
        self._context = _torch().no_grad()
        self._context.__enter__()

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self._context.__exit__(exc_type, exc, tb)

