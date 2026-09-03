#!/usr/bin/env python3
"""CUDA/PyTorch Gemma3 FineWeb-Edu replication runner.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v6.

This module is deliberately independent of the MLX V31 implementation.  It
loads only a sealed local model bundle, applies the one-token recurrence with
PyTorch module hooks, and emits aggregate-only publication results. A
temporary, digest-bound scalar ledger is retained outside the result root
only until independent validation. It does not submit provider jobs or
acquire data.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import platform
import re
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence


STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-h100-v6"
SCHEMA = "gemma3-fineweb-edu-replication-h100-v6-result"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-h100-v6-corpus"
WINDOW_TOKENS = 1024
EXPECTED_WINDOWS = 64
FIT_ALPHA, FIT_BETA = 0.10, 0.90
EVALUATION_ALPHA, EVALUATION_BETA = 0.15, 0.85
TEMPERATURE_CONTROL = 1.20
EPSILON = 1e-6
PARITY_TOLERANCE = 1e-5
CANDIDATE_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, BOOTSTRAP_CONFIDENCE = 10_000, 2_026_0829, 0.95
CONTROL_NAMES = (
    "native_baseline",
    "zero_alpha_identity",
    "all_candidate_evaluations",
    "temperature_1.20_baseline",
    "temperature_1.20_intervention",
    "deterministic_repeat",
    "frozen_model_manifest",
    "frozen_model_parameters",
)
MODEL_ID = "google/gemma-3-1b-pt"
MODEL_ARCHITECTURE = "Gemma3ForCausalLM"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value: dict[str, Any], field: str) -> str:
    return hashlib.sha256(
        canonical({key: item for key, item in value.items() if key != field})
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _external_runtime_path(path: Path, repo_root: Path, label: str) -> Path:
    path = path.expanduser()
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink")
    resolved = path.resolve()
    repository = repo_root.expanduser().resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the provider code root")
    if not resolved.is_absolute():
        raise ValueError(f"{label} must be absolute")
    return resolved


def _hex(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError(f"{label} must be a SHA-256 hex digest") from error
    return value


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _safe_files(root: Path, label: str) -> list[str]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"{label} must be a real directory")
    files: list[str] = []
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise ValueError(f"{label} contains a symlink: {candidate}")
        if candidate.is_file():
            relative = candidate.relative_to(root)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"{label} contains an unsafe path")
            files.append(relative.as_posix())
    if not files:
        raise ValueError(f"{label} is empty")
    return sorted(files)


def _require_read_only_tree(root: Path, label: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"{label} must be a real directory")
    if root.stat().st_mode & 0o222:
        raise ValueError(f"{label} root is mutable")
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise ValueError(f"{label} contains a symlink")
        if candidate.stat().st_mode & 0o222:
            raise ValueError(f"{label} contains a mutable entry: {candidate}")


def tree_manifest(root: Path, label: str) -> dict[str, Any]:
    files = _safe_files(root, label)
    entries = [
        {
            "path": relative,
            "byte_len": (root / relative).stat().st_size,
            "sha256": sha256_file(root / relative),
        }
        for relative in files
    ]
    body = {"schema": "sealed-file-tree-v1", "files": entries}
    return {**body, "manifest_sha256": digest(body, "manifest_sha256")}


def validate_tree_manifest(root: Path, label: str) -> dict[str, Any]:
    _require_read_only_tree(root, label)
    manifest_path = root / "model-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError(f"{label} model-manifest.json is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema", "model_id", "model_revision", "architecture", "files", "manifest_sha256"
    }:
        raise ValueError(f"{label} manifest schema is not closed")
    if manifest["schema"] != "gemma3-model-manifest-v6" or manifest["model_id"] != MODEL_ID or manifest["architecture"] != MODEL_ARCHITECTURE or re.fullmatch(r"[0-9a-f]{40}", manifest["model_revision"]) is None:
        raise ValueError(f"{label} manifest schema mismatch")
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError(f"{label} manifest digest mismatch")
    entries = manifest["files"]
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"{label} manifest files missing")
    expected = {item["path"] for item in entries if isinstance(item, dict)}
    actual = set(_safe_files(root, label)) - {"model-manifest.json"}
    if expected != actual or len(expected) != len(entries):
        raise ValueError(f"{label} file set mismatch")
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"path", "byte_len", "sha256"}:
            raise ValueError(f"{label} manifest entry invalid")
        path = root / item["path"]
        if path.is_symlink() or not path.is_file() or ".." in Path(item["path"]).parts:
            raise ValueError(f"{label} manifest path invalid")
        _hex(item["sha256"], f"{label} file digest")
        if path.stat().st_size != item["byte_len"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"{label} file digest mismatch: {item['path']}")
    config_path = root / "config.json"
    if not config_path.is_file() or config_path.is_symlink():
        raise ValueError(f"{label} config.json is missing")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("model_type") != "gemma3" or MODEL_ARCHITECTURE not in config.get("architectures", []):
        raise ValueError(f"{label} architecture identity mismatch")
    return manifest


@dataclass(frozen=True)
class Window:
    dataset: str
    document_id: str
    relative_path: str
    window_ordinal: int
    text: str
    source_sha256: str
    source_row_sha256: str
    source_row_index: int
    source_row_id: str
    text_sha256: str
    token_ids: tuple[int, ...]


def _window(value: Any, label: str, source_rows: dict[str, dict[str, Any]]) -> Window:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    expected = {
        "dataset", "document_id", "relative_path", "window_ordinal", "text",
        "source_sha256", "source_row_sha256", "source_row_index", "source_row_id",
        "text_sha256", "token_count", "token_ids",
    }
    if set(value) != expected:
        raise ValueError(f"{label} schema is not closed")
    if not all(isinstance(value[key], str) and value[key].strip() for key in (
        "dataset", "document_id", "relative_path", "text"
    )):
        raise ValueError(f"{label} string field invalid")
    if isinstance(value["window_ordinal"], bool) or value["window_ordinal"] != 0:
        raise ValueError(f"{label} window ordinal invalid")
    if isinstance(value["token_count"], bool) or not isinstance(value["token_count"], int) or value["token_count"] != WINDOW_TOKENS:
        raise ValueError(f"{label} token count invalid")
    token_ids = value["token_ids"]
    if (
        not isinstance(token_ids, list)
        or len(token_ids) != WINDOW_TOKENS
        or any(isinstance(item, bool) or not isinstance(item, int) for item in token_ids)
    ):
        raise ValueError(f"{label} token ids invalid")
    _hex(value["source_sha256"], f"{label} source digest")
    _hex(value["source_row_sha256"], f"{label} source row digest")
    _hex(value["text_sha256"], f"{label} text digest")
    if hashlib.sha256(value["text"].encode()).hexdigest() != value["text_sha256"]:
        raise ValueError(f"{label} text digest mismatch")
    if (
        isinstance(value["source_row_index"], bool)
        or not isinstance(value["source_row_index"], int)
        or not isinstance(value["source_row_id"], str)
        or not value["source_row_id"]
    ):
        raise ValueError(f"{label} source row identity invalid")
    source = source_rows.get(value["document_id"])
    if source is None or any(
        value[key] != source[key]
        for key in ("source_sha256", "source_row_sha256", "source_row_index", "source_row_id")
    ):
        raise ValueError(f"{label} source row binding mismatch")
    return Window(
        dataset=value["dataset"],
        document_id=value["document_id"],
        relative_path=value["relative_path"],
        window_ordinal=0,
        text=value["text"],
        source_sha256=value["source_sha256"],
        source_row_sha256=value["source_row_sha256"],
        source_row_index=value["source_row_index"],
        source_row_id=value["source_row_id"],
        text_sha256=value["text_sha256"],
        token_ids=tuple(token_ids),
    )


def _jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{label} blank line {number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{label} line {number} is not an object")
            rows.append(value)
    return rows


def load_corpus(
    root: Path,
    tokenizer: Any | None = None,
    source_rows: dict[str, dict[str, Any]] | None = None,
    source_manifest_sha256: str | None = None,
) -> tuple[list[Window], list[Window], str]:
    _require_read_only_tree(root, "corpus")
    expected_paths = {"manifest.json", "fit/windows.jsonl", "assessment/windows.jsonl"}
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("corpus contains a symlink")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != expected_paths:
        raise ValueError(f"corpus exact file set mismatch: {sorted(actual)}")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema", "state_slice", "source_manifest_sha256", "model_bundle_path",
        "model_manifest_sha256", "fit_sha256", "assessment_sha256", "window_tokens",
        "fit_window_count", "assessment_window_count", "manifest_sha256",
    }:
        raise ValueError("corpus manifest schema is not closed")
    if (
        manifest["schema"] != CORPUS_SCHEMA
        or manifest["state_slice"] != STATE_SLICE
        or manifest["source_manifest_sha256"] != source_manifest_sha256
        or manifest["model_bundle_path"] != "model"
        or manifest["window_tokens"] != WINDOW_TOKENS
        or manifest["fit_window_count"] != EXPECTED_WINDOWS
        or manifest["assessment_window_count"] != EXPECTED_WINDOWS
    ):
        raise ValueError("corpus identity mismatch")
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError("corpus manifest digest mismatch")
    for split in ("fit", "assessment"):
        _hex(manifest[f"{split}_sha256"], f"corpus {split} digest")
        if sha256_file(root / f"{split}/windows.jsonl") != manifest[f"{split}_sha256"]:
            raise ValueError(f"corpus {split} digest mismatch")
    if source_rows is None:
        raise ValueError("source rows are required")
    fit = [_window(row, f"fit window {index}", source_rows) for index, row in enumerate(
        _jsonl(root / "fit/windows.jsonl", "fit windows")
    )]
    assessment = [_window(row, f"assessment window {index}", source_rows) for index, row in enumerate(
        _jsonl(root / "assessment/windows.jsonl", "assessment windows")
    )]
    if len(fit) != EXPECTED_WINDOWS or len(assessment) != EXPECTED_WINDOWS:
        raise ValueError("corpus window count mismatch")
    fit_ids, assessment_ids = {row.document_id for row in fit}, {row.document_id for row in assessment}
    if len(fit_ids) != EXPECTED_WINDOWS or len(assessment_ids) != EXPECTED_WINDOWS:
        raise ValueError("corpus document ids are not unique")
    if fit_ids & assessment_ids:
        raise ValueError("corpus fit/assessment overlap")
    if tokenizer is not None:
        for split, rows in (("fit", fit), ("assessment", assessment)):
            for index, row in enumerate(rows):
                if row.dataset != "fineweb_edu" or row.relative_path != f"{split}/window-{index:06d}.txt":
                    raise ValueError(f"corpus window location changed: {row.document_id}")
                token_ids = tuple(tokenizer.encode(row.text, add_special_tokens=False))
                if token_ids != row.token_ids or len(token_ids) != WINDOW_TOKENS:
                    raise ValueError(f"tokenizer changed corpus window: {row.document_id}")
                source = source_rows[row.document_id]
                source_ids = tuple(tokenizer.encode(source["text"], add_special_tokens=False))
                if source_ids[:WINDOW_TOKENS] != row.token_ids:
                    raise ValueError(f"corpus window is not the source prefix: {row.document_id}")
    return fit, assessment, manifest["manifest_sha256"]


@contextlib.contextmanager
def network_block() -> Iterator[None]:
    old_env = {key: os.environ.get(key) for key in (
        "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"
    )}
    old_socket = socket.socket
    old_functions = {name: getattr(socket, name) for name in (
        "create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex"
    )}
    blocked_os_names = (
        "system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp",
        "spawnv", "spawnve", "spawnvp", "spawnvpe", "execv", "execve",
        "execvp", "execvpe", "execl", "execle", "execlp", "execlpe",
    )
    old_os_functions = {
        name: getattr(os, name)
        for name in blocked_os_names
        if hasattr(os, name)
    }
    old_subprocess_functions = {
        name: getattr(subprocess, name)
        for name in ("Popen", "run", "call", "check_call", "check_output")
        if hasattr(subprocess, name)
    }
    old_fork_exec = getattr(subprocess, "_fork_exec", None)

    def denied(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("H100 model execution network access denied")

    try:
        for key in old_env:
            os.environ[key] = "1"
        socket.socket = denied  # type: ignore[assignment]
        for name in old_functions:
            setattr(socket, name, denied)
        for name in old_os_functions:
            setattr(os, name, denied)
        for name in old_subprocess_functions:
            setattr(subprocess, name, denied)
        if old_fork_exec is not None:
            subprocess._fork_exec = denied  # type: ignore[attr-defined]
        yield
    finally:
        socket.socket = old_socket  # type: ignore[assignment]
        for name, value in old_functions.items():
            setattr(socket, name, value)
        for name, value in old_os_functions.items():
            setattr(os, name, value)
        for name, value in old_subprocess_functions.items():
            setattr(subprocess, name, value)
        if old_fork_exec is not None:
            subprocess._fork_exec = old_fork_exec  # type: ignore[attr-defined]
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def require_network_none() -> None:
    interfaces = {name for _index, name in __import__("socket").if_nameindex()}
    if interfaces != {"lo"}:
        raise RuntimeError(f"network namespace is not sealed: {sorted(interfaces)}")
    proc_net_dev = Path("/proc/net/dev")
    if proc_net_dev.is_file():
        names = {
            line.split(":", 1)[0].strip()
            for line in proc_net_dev.read_text(encoding="utf-8").splitlines()
            if ":" in line
        }
        if names != {"lo"}:
            raise RuntimeError(f"network device proof failed: {sorted(names)}")
    for route_path in (Path("/proc/net/route"), Path("/proc/net/ipv6_route")):
        if not route_path.is_file():
            raise RuntimeError(f"network route proof is unavailable: {route_path}")
        lines = [line for line in route_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if route_path.name == "route":
            if len(lines) != 1:
                raise RuntimeError(f"network IPv4 route proof failed: {route_path}")
        elif lines:
            raise RuntimeError(f"network IPv6 route proof failed: {route_path}")


def validate_runtime_lock(repo_root: Path, launch: dict[str, Any], torch: Any) -> dict[str, Any]:
    import importlib.metadata

    if launch.get("runtime_lock_path") != "runtime-lock.json":
        raise RuntimeError("runtime lock path is not the reviewed container lock")
    path = repo_root / "runtime-lock.json"
    if path.is_symlink() or not path.is_file() or sha256_file(path) != launch["runtime_lock_sha256"]:
        raise RuntimeError("runtime lock custody mismatch")
    lock = json.loads(path.read_text(encoding="utf-8"))
    expected_keys = {
        "schema", "state_slice", "python", "accelerate", "cryptography", "pytorch", "transformers", "safetensors",
        "tokenizers", "pyarrow", "cuda_runtime", "dtype", "gpu_required",
        "network_policy", "package_install_at_runtime",
    }
    if not isinstance(lock, dict) or set(lock) != expected_keys or lock["schema"] != "gemma3-fineweb-edu-replication-h100-v6-runtime-lock" or lock["state_slice"] != STATE_SLICE:
        raise RuntimeError("runtime lock schema mismatch")
    installed = {
        "python": ".".join(platform.python_version().split(".")[:2]),
        "accelerate": importlib.metadata.version("accelerate").split("+", 1)[0],
        "cryptography": importlib.metadata.version("cryptography").split("+", 1)[0],
        "pytorch": str(torch.__version__).split("+", 1)[0],
        "transformers": importlib.metadata.version("transformers").split("+", 1)[0],
        "safetensors": importlib.metadata.version("safetensors").split("+", 1)[0],
        "tokenizers": importlib.metadata.version("tokenizers").split("+", 1)[0],
        "pyarrow": importlib.metadata.version("pyarrow").split("+", 1)[0],
        "cuda_runtime": str(torch.version.cuda),
    }
    for field, value in installed.items():
        if value != lock[field]:
            raise RuntimeError(f"runtime lock mismatch: {field}")
    if lock["dtype"] != "bfloat16" or lock["gpu_required"] != "NVIDIA H100" or lock["network_policy"] != "network-none-v6" or lock["package_install_at_runtime"] is not False:
        raise RuntimeError("runtime lock safety contract mismatch")
    return installed


def cuda_driver_version() -> str:
    version_path = Path("/proc/driver/nvidia/version")
    if not version_path.is_file():
        raise RuntimeError("NVIDIA driver version proof is unavailable")
    match = re.search(r"Kernel Module\s+([0-9][0-9.]*)", version_path.read_text(encoding="utf-8"))
    if match is None:
        raise RuntimeError("NVIDIA driver version proof is invalid")
    return match.group(1)


def model_parameter_digest(model: Any) -> str:
    hasher = hashlib.sha256()
    for name, parameter in model.named_parameters():
        value = parameter.detach().to(device="cpu", dtype=getattr(__import__("torch"), "float32"))
        hasher.update(name.encode())
        hasher.update(str(tuple(value.shape)).encode())
        hasher.update(str(parameter.dtype).encode())
        hasher.update(value.numpy().tobytes(order="C"))
    return hasher.hexdigest()


@dataclass(frozen=True)
class RecirculationConfig:
    source_layer: int
    destination_layer: int
    alpha: float
    beta: float
    epsilon: float = EPSILON

    def validate(self, layer_count: int) -> None:
        if (
            isinstance(self.source_layer, bool)
            or not isinstance(self.source_layer, int)
            or isinstance(self.destination_layer, bool)
            or not isinstance(self.destination_layer, int)
            or not 0 <= self.destination_layer < self.source_layer < layer_count
        ):
            raise ValueError("recirculation layer pair invalid")
        if (
            any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))
                for value in (self.alpha, self.beta, self.epsilon))
            or not 0 <= self.alpha <= 1
            or self.beta != 1 - self.alpha
            or self.epsilon <= 0
        ):
            raise ValueError("recirculation parameters invalid")

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_layer": self.source_layer,
            "destination_layer": self.destination_layer,
            "alpha": self.alpha,
            "beta": self.beta,
            "epsilon": self.epsilon,
        }


def mix_hidden(torch: Any, source: Any, destination: Any, config: RecirculationConfig) -> Any:
    source_norm = torch.linalg.vector_norm(source.float(), dim=-1, keepdim=True)
    destination_norm = torch.linalg.vector_norm(destination.float(), dim=-1, keepdim=True)
    scale = destination_norm / torch.clamp(source_norm, min=config.epsilon)
    mixed = config.beta * destination.float() + config.alpha * source.float() * scale
    return mixed.to(dtype=destination.dtype)


class RecirculationHooks:
    def __init__(self, model: Any, config: RecirculationConfig) -> None:
        self.model = model
        self.config = config
        self.previous_source: Any | None = None
        self.current_source: Any | None = None
        layers = getattr(getattr(model, "model", None), "layers", None)
        if layers is None:
            raise TypeError("Gemma3 text layer seam unavailable")
        config.validate(len(layers))
        self.handles = [
            layers[config.source_layer].register_forward_hook(self._source_hook),
            layers[config.destination_layer].register_forward_hook(self._destination_hook),
        ]

    @staticmethod
    def _tensor(output: Any) -> Any:
        if not hasattr(output, "dtype") or not hasattr(output, "shape"):
            raise TypeError("Gemma3 layer output is not a tensor")
        return output

    def _source_hook(self, _module: Any, _inputs: Any, output: Any) -> Any:
        self.current_source = self._tensor(output).detach().clone()
        return output

    def _destination_hook(self, _module: Any, _inputs: Any, output: Any) -> Any:
        output = self._tensor(output)
        if self.previous_source is None or self.config.alpha == 0:
            return output
        return mix_hidden(__import__("torch"), self.previous_source, output, self.config)

    def begin_token(self) -> None:
        self.current_source = None

    def end_token(self) -> None:
        if self.current_source is None:
            raise RuntimeError("source activation was not captured")
        self.previous_source = self.current_source

    def close(self) -> None:
        for handle in self.handles:
            handle.remove()
        self.handles.clear()


def _forward_logits(model: Any, token_ids: Sequence[int], config: RecirculationConfig | None) -> list[Any]:
    torch = __import__("torch")
    device = next(model.parameters()).device
    cache: Any | None = None
    hooks = RecirculationHooks(model, config) if config is not None else None
    logits: list[Any] = []
    try:
        with torch.inference_mode():
            for token_id in token_ids:
                if hooks is not None:
                    hooks.begin_token()
                inputs = torch.tensor([[int(token_id)]], dtype=torch.long, device=device)
                output = model(
                    input_ids=inputs,
                    past_key_values=cache,
                    use_cache=True,
                    logits_to_keep=1,
                )
                cache = output.past_key_values
                logits.append(output.logits[0, -1].float().detach().cpu())
                if hooks is not None:
                    hooks.end_token()
        return logits
    finally:
        if hooks is not None:
            hooks.close()


def evaluate_windows(model: Any, tokenizer: Any, windows: Sequence[Window], config: RecirculationConfig | None,
                     temperature: float = 1.0) -> dict[str, Any]:
    torch = __import__("torch")
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(float(temperature)) or temperature <= 0:
        raise ValueError("temperature invalid")
    rows: list[dict[str, Any]] = []
    for window in windows:
        ids = tuple(tokenizer.encode(window.text, add_special_tokens=False))
        if ids != window.token_ids or len(ids) != WINDOW_TOKENS:
            raise ValueError(f"tokenizer changed corpus window: {window.document_id}")
        values = _forward_logits(model, ids[:-1], config)
        total = 0.0
        for value, target in zip(values, ids[1:], strict=True):
            total += float(-torch.log_softmax(value / float(temperature), dim=-1)[target])
        if not math.isfinite(total):
            raise ValueError("NLL is nonfinite")
        rows.append({
            "dataset": window.dataset,
            "document_id": window.document_id,
            "relative_path": window.relative_path,
            "window_ordinal": 0,
            "source_sha256": window.source_sha256,
            "source_row_sha256": window.source_row_sha256,
            "source_row_index": window.source_row_index,
            "source_row_id": window.source_row_id,
            "text_sha256": window.text_sha256,
            "token_count": WINDOW_TOKENS,
            "target_count": WINDOW_TOKENS - 1,
            "nll": round(total, 9),
        })
    target_tokens = sum(row["target_count"] for row in rows)
    mean_nll = sum(row["nll"] for row in rows) / target_tokens
    return {
        "temperature": float(temperature),
        "evaluation_config": config.as_dict() if config is not None else None,
        "mean_nll": round(mean_nll, 9),
        "perplexity": round(math.exp(mean_nll), 9),
        "target_tokens": target_tokens,
        "rows": rows,
    }


def aggregate_metrics(metrics: dict[str, Any], windows: Sequence[Window]) -> dict[str, Any]:
    """Remove per-document scalars while retaining independently checkable aggregates."""
    expected_ids = [window.document_id for window in windows]
    if [row["document_id"] for row in metrics["rows"]] != expected_ids:
        raise ValueError("metric document order does not match the locked corpus")
    return {
        "temperature": metrics["temperature"],
        "evaluation_config": metrics["evaluation_config"],
        "mean_nll": metrics["mean_nll"],
        "perplexity": metrics["perplexity"],
        "target_tokens": metrics["target_tokens"],
        "document_count": len(expected_ids),
        "document_ids_sha256": hashlib.sha256(canonical(expected_ids)).hexdigest(),
    }


def bootstrap_mean_ci(deltas: Sequence[float]) -> dict[str, Any]:
    if not deltas:
        raise ValueError("bootstrap requires data")
    values = [_finite(value, "bootstrap value") for value in deltas]
    n = len(values)
    samples: list[float] = []
    for resample in range(BOOTSTRAP_RESAMPLES):
        total = 0.0
        for position in range(n):
            counter = f"{BOOTSTRAP_SEED}:{resample}:{position}".encode()
            total += values[int.from_bytes(hashlib.sha256(counter).digest()[:8], "big") % n]
        samples.append(total / n)
    samples.sort()

    def rank(q: float) -> float:
        return samples[max(1, min(BOOTSTRAP_RESAMPLES, math.ceil(q * BOOTSTRAP_RESAMPLES))) - 1]

    mean = sum(values) / n
    return {
        "mean_delta": mean,
        "lower": rank(0.025),
        "upper": rank(0.975),
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
        "confidence": BOOTSTRAP_CONFIDENCE,
        "prng": "sha256-counter-v1",
        "statistic": "mean paired per-document NLL delta selected_minus_baseline",
        "percentile": "nearest-rank-1-indexed",
        "nonfinite": "reject",
    }


def decision(bootstrap: dict[str, Any]) -> str:
    mean, upper = _finite(bootstrap["mean_delta"], "bootstrap mean"), _finite(bootstrap["upper"], "bootstrap upper")
    return "ReplicationCandidate" if mean < 0 and upper < 0 else "NoCandidate"


def _mean(rows: Sequence[dict[str, Any]]) -> float:
    return sum(row["nll"] for row in rows) / sum(row["target_count"] for row in rows)


def run(model_root: Path, raw_root: Path, source_root: Path, corpus_root: Path, result_root: Path, launch_manifest: Path, repo_root: Path | None = None, tokenizer: Any | None = None) -> dict[str, Any]:
    torch = __import__("torch")
    from experiments.continual_learning import (
        gemma3_fineweb_edu_replication_h100_v6_preflight as preflight,
    )

    provider_root = (repo_root or Path(__file__).resolve().parents[2]).expanduser().resolve()
    model_root = _external_runtime_path(model_root, provider_root, "model root")
    raw_root = _external_runtime_path(raw_root, provider_root, "raw root")
    source_root = _external_runtime_path(source_root, provider_root, "source root")
    corpus_root = _external_runtime_path(corpus_root, provider_root, "corpus root")
    result_root = _external_runtime_path(result_root, provider_root, "result root")
    if not result_root.is_dir() or result_root.is_symlink():
        raise RuntimeError("result root must be a real pre-created directory")
    if result_root.stat().st_mode & 0o777 != 0o700:
        raise RuntimeError("result root must be owner-only mode 0700 before execution")
    launch = preflight.validate_launch_manifest(launch_manifest, repo_root)
    launch_file_sha256 = sha256_file(launch_manifest)
    launch_manifest_sha256 = launch["manifest_sha256"]
    launch_model_path = Path(launch["model_bundle_path"]).expanduser()
    if launch_model_path.is_symlink():
        raise RuntimeError("launch-manifest model bundle must not be a symlink")
    if launch_manifest.is_symlink() or launch_manifest.stat().st_mode & 0o222:
        raise RuntimeError("launch manifest must be a read-only regular file")
    expected_model_root = launch_model_path.resolve()
    if model_root.expanduser().resolve() != expected_model_root:
        raise RuntimeError("model path is not the exact launch-manifest model bundle")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; H100 qualification is unverified")
    if torch.cuda.device_count() != 1:
        raise RuntimeError("exactly one CUDA device is required")
    if "H100" not in torch.cuda.get_device_name(0).upper():
        raise RuntimeError("the active CUDA device is not an H100")
    driver_version = cuda_driver_version()
    if launch.get("cuda_driver_version") != driver_version:
        raise RuntimeError("CUDA driver version is not the exact launch-manifest driver")
    require_network_none()
    runtime = validate_runtime_lock(provider_root, launch, torch)
    provider_receipt_path = result_root / "provider-receipt.json"
    result_entries = {
        path.relative_to(result_root).as_posix()
        for path in result_root.rglob("*")
    } if result_root.is_dir() and not result_root.is_symlink() else set()
    if result_entries != {"provider-receipt.json"}:
        raise RuntimeError("result root must contain only the pre-issued provider receipt")
    if provider_receipt_path.is_symlink() or provider_receipt_path.stat().st_mode & 0o222:
        raise RuntimeError("provider receipt must be a read-only regular file")
    from experiments.continual_learning import validate_gemma3_fineweb_edu_replication_h100_v6 as validator
    provider_receipt = validator.validate_provider_receipt(provider_receipt_path, launch, launch_file_sha256)
    model_manifest = validate_tree_manifest(model_root, "model bundle")
    if (
        model_manifest["manifest_sha256"] != launch["model_manifest_sha256"]
        or model_manifest["model_id"] != launch["model_id"]
        or model_manifest["model_revision"] != launch["model_revision"]
        or model_manifest["architecture"] != launch["model_architecture"]
    ):
        raise RuntimeError("model bundle is not the launch-manifest model")
    if tokenizer is None:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_root, local_files_only=True, use_fast=True)
    from experiments.continual_learning import (
        pack_gemma3_fineweb_edu_replication_h100_v6 as packer,
    )
    source_manifest, source_rows_by_split = packer.validate_source_bundle(raw_root, source_root)
    source_rows = {row["document_id"]: row for rows in source_rows_by_split.values() for row in rows}
    fit, assessment, corpus_manifest_sha256 = load_corpus(
        corpus_root, tokenizer, source_rows, source_manifest["manifest_sha256"]
    )
    corpus_manifest = json.loads((corpus_root / "manifest.json").read_text(encoding="utf-8"))
    if corpus_manifest["model_manifest_sha256"] != model_manifest["manifest_sha256"]:
        raise RuntimeError("corpus is not bound to the launch-manifest model")
    if corpus_manifest_sha256 != launch["data_manifest_sha256"]:
        raise RuntimeError("corpus bundle is not the launch-manifest data bundle")
    if source_manifest["manifest_sha256"] != launch["source_manifest_sha256"]:
        raise RuntimeError("source bundle is not the launch-manifest data source")
    from transformers import AutoModelForCausalLM
    model = AutoModelForCausalLM.from_pretrained(
        model_root,
        local_files_only=True,
        torch_dtype=torch.bfloat16,
        use_safetensors=True,
    ).cuda()
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    parameter_before = model_parameter_digest(model)
    started = time.monotonic()
    with network_block():
        fit_baseline_raw = evaluate_windows(model, tokenizer, fit, None)
        candidates_raw: list[dict[str, Any]] = []
        for source_layer, destination_layer in CANDIDATE_PAIRS:
            config = RecirculationConfig(source_layer, destination_layer, FIT_ALPHA, FIT_BETA)
            candidates_raw.append({"config": config.as_dict(), "metrics": evaluate_windows(model, tokenizer, fit, config)})
        selected = min(
            (item["metrics"]["mean_nll"], index, item)
            for index, item in enumerate(candidates_raw)
        )[2]
        selected_fit = selected["config"]
        locked = RecirculationConfig(selected_fit["source_layer"], selected_fit["destination_layer"], EVALUATION_ALPHA, EVALUATION_BETA)
        assessment_baseline_raw = evaluate_windows(model, tokenizer, assessment, None)
        assessment_selected_raw = evaluate_windows(model, tokenizer, assessment, locked)
        temperature_baseline_raw = evaluate_windows(model, tokenizer, assessment, None, TEMPERATURE_CONTROL)
        temperature_selected_raw = evaluate_windows(model, tokenizer, assessment, locked, TEMPERATURE_CONTROL)
        repeat_raw = evaluate_windows(model, tokenizer, assessment, locked)
        zero_raw = {}
        for source_layer, destination_layer in CANDIDATE_PAIRS:
            pair = f"{source_layer}->{destination_layer}"
            metrics = evaluate_windows(
                model,
                tokenizer,
                assessment,
                RecirculationConfig(source_layer, destination_layer, 0.0, 1.0),
            )
            zero_raw[pair] = {"metrics": metrics, "max_abs_nll_delta": max(abs(metrics["rows"][i]["nll"] - assessment_baseline_raw["rows"][i]["nll"]) for i in range(EXPECTED_WINDOWS))}
    parameter_after = model_parameter_digest(model)
    if parameter_before != parameter_after:
        raise RuntimeError("model parameter digest changed")
    fit_baseline = aggregate_metrics(fit_baseline_raw, fit)
    candidates = [{"config": item["config"], "metrics": aggregate_metrics(item["metrics"], fit)} for item in candidates_raw]
    assessment_baseline = aggregate_metrics(assessment_baseline_raw, assessment)
    assessment_selected = aggregate_metrics(assessment_selected_raw, assessment)
    temperature_baseline = aggregate_metrics(temperature_baseline_raw, assessment)
    temperature_selected = aggregate_metrics(temperature_selected_raw, assessment)
    repeat = aggregate_metrics(repeat_raw, assessment)
    zero = {
        pair: {"metrics": aggregate_metrics(item["metrics"], assessment), "max_abs_nll_delta": item["max_abs_nll_delta"]}
        for pair, item in zero_raw.items()
    }
    base = {row["document_id"]: row for row in assessment_baseline_raw["rows"]}
    chosen = {row["document_id"]: row for row in assessment_selected_raw["rows"]}
    ledger_rows = []
    for window in assessment:
        before, after = base[window.document_id], chosen[window.document_id]
        ledger_rows.append({
            "document_id": window.document_id,
            "baseline_nll": before["nll"],
            "selected_nll": after["nll"],
            "delta_selected_minus_baseline": after["nll"] / 1023 - before["nll"] / 1023,
        })
    reach: list[dict[str, Any]] = []
    fit_base_rows = {row["document_id"]: row for row in fit_baseline_raw["rows"]}
    for pair, candidate in zip(CANDIDATE_PAIRS, candidates_raw, strict=True):
        candidate_rows = {row["document_id"]: row for row in candidate["metrics"]["rows"]}
        maximum = max(abs(candidate_rows[key]["nll"] - fit_base_rows[key]["nll"]) for key in fit_base_rows)
        reach.append({"source_layer": pair[0], "destination_layer": pair[1], "max_abs_fit_nll_delta": maximum, "reached": maximum != 0.0})
    if not all(item["reached"] for item in reach):
        raise RuntimeError("nonzero intervention reach failed for a candidate")
    parity = max(item["max_abs_nll_delta"] for item in zero_raw.values())
    if parity > PARITY_TOLERANCE or any(item["max_abs_nll_delta"] > PARITY_TOLERANCE for item in zero_raw.values()):
        raise RuntimeError("zero-alpha identity failed")
    if repeat_raw != assessment_selected_raw:
        raise RuntimeError("deterministic repeat failed")
    if sha256_file(launch_manifest) != launch_file_sha256:
        raise RuntimeError("launch manifest changed during execution")
    preflight.validate_launch_manifest(launch_manifest, repo_root)
    ledger_path = result_root.parent / f".{result_root.name}.assessment-ledger.jsonl"
    if ledger_path.exists() or ledger_path.is_symlink():
        raise RuntimeError("temporary assessment ledger already exists")
    with ledger_path.open("x", encoding="utf-8") as handle:
        for row in ledger_rows:
            handle.write(canonical(row).decode())
    ledger_path.chmod(0o600)
    ledger_sha256 = sha256_file(ledger_path)
    bootstrap = bootstrap_mean_ci([row["delta_selected_minus_baseline"] for row in ledger_rows])
    elapsed = time.monotonic() - started
    result = {
        "schema": SCHEMA,
        "state_slice": STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentGemma3FineWebEduReplicationH100V6",
        "launch_manifest_sha256": launch_manifest_sha256,
        "hard_usd_ceiling": launch["hard_usd_ceiling"],
        "estimated_max_total_usd": launch["estimated_max_total_usd"],
        "provider_receipt_sha256": provider_receipt["receipt_sha256"],
        "provider_job_id": provider_receipt["job_id"],
        "provider_allocation_id": provider_receipt["allocation_id"],
        "provider_node_id": provider_receipt["node_id"],
        "provider_charged_usd": provider_receipt["charged_usd"],
        "provider_stop_reason": provider_receipt["stop_reason"],
        "protocol_sha256": launch["protocol_sha256"],
        "packet_sha256": launch["packet_sha256"],
        "review_receipt_sha256": launch["review_receipt_sha256"],
        "implementation_manifest_sha256": launch["implementation_manifest_sha256"],
        "code_bundle_sha256": launch["code_bundle_sha256"],
        "runtime_lock_sha256": launch["runtime_lock_sha256"],
        "data_manifest_sha256": launch["data_manifest_sha256"],
        "source_manifest_sha256": source_manifest["manifest_sha256"],
        "container_digest": launch["container_digest"],
        "provider": launch["provider"],
        "provider_project": launch["provider_project"],
        "node_type": launch["node_type"],
        "job_mode": launch["job_mode"],
        "launch_manifest_path": str(launch_manifest.resolve()),
        "model_bundle_path": str(Path(launch["model_bundle_path"]).expanduser().resolve()),
        "data_bundle_path": str(Path(launch["data_bundle_path"]).expanduser().resolve()),
        "source_bundle_path": str(Path(launch["source_bundle_path"]).expanduser().resolve()),
        "raw_bundle_path": str(Path(launch["raw_bundle_path"]).expanduser().resolve()),
        "model_id": launch["model_id"],
        "model_revision": launch["model_revision"],
        "model_architecture": launch["model_architecture"],
        "runtime": {
            **runtime,
            "cuda_driver_version": driver_version,
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_count": torch.cuda.device_count(),
            "dtype": "bfloat16",
            "network": "offline-process-block-v6",
        },
        "model_manifest_sha256": model_manifest["manifest_sha256"],
        "model_parameter_digest_before": parameter_before,
        "model_parameter_digest_after": parameter_after,
        "corpus_manifest_sha256": corpus_manifest_sha256,
        "candidate_pairs": [list(pair) for pair in CANDIDATE_PAIRS],
        "fit_alpha": FIT_ALPHA,
        "fit_beta": FIT_BETA,
        "evaluation_alpha": EVALUATION_ALPHA,
        "evaluation_beta": EVALUATION_BETA,
        "temperature_control": TEMPERATURE_CONTROL,
        "normalization": "source_l2_norm_to_destination_l2_norm",
        "selected_fit_config": selected_fit,
        "locked_evaluation_config": locked.as_dict(),
        "paper_expected_pair": {"source_layer": 11, "destination_layer": 4},
        "paper_expected_pair_recovered": selected_fit["source_layer"] == 11 and selected_fit["destination_layer"] == 4,
        "fit_baseline": fit_baseline,
        "fit_candidates": candidates,
        "assessment_baseline": assessment_baseline,
        "assessment_selected": assessment_selected,
        "assessment_temperature_baseline": temperature_baseline,
        "assessment_temperature_selected": temperature_selected,
        "assessment_repeat": repeat,
        "assessment_ledger_sha256": ledger_sha256,
        "controls": {
            "names": list(CONTROL_NAMES),
            "native_baseline": assessment_baseline,
            "zero_alpha_identity": zero,
            "all_candidate_evaluations": candidates,
            "temperature_1.20_baseline": temperature_baseline,
            "temperature_1.20_intervention": temperature_selected,
            "deterministic_repeat": repeat,
            "frozen_model_manifest": {"manifest_sha256": model_manifest["manifest_sha256"]},
            "frozen_model_parameters": {"before": parameter_before, "after": parameter_after},
        },
        "qualification": {"nonzero_intervention_reach": True, "reach_evidence": reach, "zero_alpha_identity_passed": True, "parity_tolerance": PARITY_TOLERANCE},
        "bootstrap": bootstrap,
        "decision": decision(bootstrap),
        "training": False,
        "weights_frozen": True,
        "network_access": False,
        "evidence_ledger_mutation": False,
        "effects_run": True,
        "assessment_authorized_by_review": True,
        "assessment_windows_per_h100_minute": (EXPECTED_WINDOWS / (elapsed / 60)) if elapsed > 0 else 0.0,
        "elapsed_seconds": elapsed,
    }
    result["results_sha256"] = digest(result, "results_sha256")
    try:
        destination = result_root / "result.json"
        with destination.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
        receipt = {"schema": "gemma3-fineweb-edu-replication-h100-v6-result-receipt", "state_slice": STATE_SLICE, "result_sha256": result["results_sha256"], "result_file_sha256": sha256_file(destination)}
        receipt["receipt_sha256"] = digest(receipt, "receipt_sha256")
        with (result_root / "result-receipt.json").open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2, sort_keys=True)
            handle.write("\n")
        (result_root / "result.json").chmod(0o444)
        (result_root / "result-receipt.json").chmod(0o444)
    except Exception:
        for name in ("result.json", "result-receipt.json"):
            path = result_root / name
            if path.exists():
                path.unlink()
        raise
    return {"result_root": str(result_root), "results_sha256": result["results_sha256"], "decision": result["decision"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--launch-manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args()
    try:
        with network_block():
            outcome = run(args.model_root, args.raw_root, args.source_root, args.corpus_root, args.result_root, args.launch_manifest, args.repo_root)
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(outcome, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
