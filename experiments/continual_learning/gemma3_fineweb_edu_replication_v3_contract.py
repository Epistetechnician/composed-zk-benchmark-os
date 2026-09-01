#!/usr/bin/env python3
"""Shared mechanical constants for V3 only.

State slice: continual-learning-gemma3-fineweb-edu-replication-v3.

This file contains no protocol execution and no data access. The V3 validator
still independently re-derives source and corpus lineage rather than trusting
these helpers as evidence.
"""

from __future__ import annotations

import contextlib
import hashlib
import math
import os
import socket
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-v3"
CLAIM_CEILING = "LocalDevelopmentGemma3FineWebEduReplicationV3"
SOURCE_SCHEMA = "gemma3-fineweb-edu-replication-v3-source"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-v3-corpus"
RESULT_SCHEMA = "gemma3-fineweb-edu-replication-v3-result"
REVIEW_SCHEMA = "gemma3-fineweb-edu-replication-v3-independent-review"
PROTOCOL_PATH = REPO_ROOT / "docs/research/continual-learning/148-gemma3-fineweb-edu-replication-v3-protocol.md"
REVIEW_PACKET_PATH = REPO_ROOT / "docs/research/continual-learning/149-gemma3-fineweb-edu-replication-v3-review-packet.md"
PROTOCOL_SHA256 = "5c9c8e0b6ede43bde9fa66a98fb515b597fafa2f3ebcd811c1925ca5a457b8f7"
DATASET_REPO = "HuggingFaceFW/fineweb-edu"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
DATASET_SOURCE = f"https://huggingface.co/datasets/{DATASET_REPO}"
DATASET_CONFIG = "fineweb-edu-crawl-shards"
DATASET_SPLIT = "train"
DATASET_FILES = (
    {
        "crawl": "CC-MAIN-2013-20",
        "path": "data/CC-MAIN-2013-20/train-00000-of-00014.parquet",
        "byte_len": 2_369_456_837,
        "sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03",
    },
    {
        "crawl": "CC-MAIN-2024-10",
        "path": "data/CC-MAIN-2024-10/000_00000.parquet",
        "byte_len": 1_911_528_585,
        "sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484",
    },
)
DATASET_BYTE_COUNT = sum(item["byte_len"] for item in DATASET_FILES)
R1_SOURCE_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1")
R1_SOURCE_MANIFEST_SHA256 = "9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3"
MODEL_PATH = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
EXPECTED_MODEL_MANIFEST_SHA256 = "69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256"
FRESH_ROW_START = 2048
FRESH_ROW_COUNT = 16_384
FRESH_ROW_END = FRESH_ROW_START + FRESH_ROW_COUNT
WINDOW_TOKENS = 1024
FIT_WINDOW_COUNT = 64
ASSESSMENT_WINDOW_COUNT = 64
FIT_ALPHA = 0.10
EVALUATION_ALPHA = 0.15
EVALUATION_BETA = 0.85
TEMPERATURE_CONTROL = 1.20
CANDIDATE_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
PARITY_TOLERANCE = 1e-5
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260829
BOOTSTRAP_CONFIDENCE = 0.95
BOOTSTRAP_PRNG = "sha256-counter-v1"
BOOTSTRAP_STATISTIC = "mean paired per-document NLL delta selected_minus_baseline"
BOOTSTRAP_PERCENTILE = "nearest-rank-1-indexed"
BOOTSTRAP_NONFINITE = "reject"
SELECTION_POLICY = "first-64-eligible-1024-token-windows-per-disjoint-v3-source-split"
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
REVIEW_FINDINGS = (
    "custody_exact_pinned_data_identity",
    "fit_assessment_prior_pilot_disjointness",
    "locked_configuration_and_paper_target_treatment",
    "controls_and_frozen_weight_behavior",
    "exact_bootstrap_and_uncertainty_rule",
    "aggregate_per_document_retention_and_validator_behavior",
    "v1_v2_rejections_preserved_and_prohibited_actions_enforced",
)
IMPLEMENTATION_FILES = (
    PROTOCOL_PATH,
    REVIEW_PACKET_PATH,
    REPO_ROOT / "experiments/continual_learning/gemma3_fineweb_edu_replication_v3_contract.py",
    REPO_ROOT / "experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v3.py",
    REPO_ROOT / "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v3.py",
    REPO_ROOT / "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v3.py",
    REPO_ROOT / "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v3.py",
)


def digest(value: Any) -> str:
    return hashlib.sha256(
        __import__("json").dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def external(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    repository = REPO_ROOT.resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the repository: {resolved}")
    return resolved


def primary(path: Path, label: str) -> Path:
    resolved = external(path, label)
    volume = PRIMARY_VOLUME.resolve()
    if not volume.is_dir():
        raise FileNotFoundError(f"required external volume is not mounted: {volume}")
    if resolved != volume and volume not in resolved.parents:
        raise ValueError(f"{label} must be under {volume}: {resolved}")
    return resolved


def regular(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    return path


def safe_relative(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError(f"{label} must be a relative path")
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    if candidate == resolved_root or resolved_root not in candidate.parents:
        raise ValueError(f"{label} escapes its root: {relative}")
    return regular(candidate, label)


def model_manifest(model_path: Path) -> dict[str, Any]:
    supplied = model_path.expanduser()
    if supplied.is_symlink():
        raise ValueError(f"model path must not be a symlink: {supplied}")
    model_path = external(supplied, "model path")
    if model_path != MODEL_PATH:
        raise ValueError(f"V3 model path mismatch: {model_path}")
    if not model_path.is_dir() or model_path.is_symlink():
        raise ValueError(f"model path must be a real directory: {model_path}")
    files = []
    for candidate in sorted(model_path.rglob("*")):
        if candidate.is_symlink():
            raise ValueError(f"model tree contains a symlink: {candidate}")
        if candidate.is_file() and ".cache" not in candidate.relative_to(model_path).parts:
            files.append({"path": candidate.relative_to(model_path).as_posix(), "byte_len": candidate.stat().st_size, "sha256": sha256_file(candidate)})
    if not files:
        raise ValueError("cached model directory has no stable files")
    body = {"model_name": model_path.name, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def model_parameter_digest(model: Any) -> str:
    """Hash every loaded parameter tensor in a deterministic tree traversal."""

    import numpy as np
    import mlx.core as mx

    root = model.parameters() if hasattr(model, "parameters") else None
    if root is None:
        raise ValueError("loaded model does not expose parameters()")
    hasher = hashlib.sha256()

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key in sorted(value):
                visit(value[key], f"{path}/{key}")
            return
        if isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                visit(item, f"{path}/{index}")
            return
        if not hasattr(value, "shape"):
            raise ValueError(f"unsupported model parameter at {path}")
        mx.eval(value)
        array = np.asarray(value)
        hasher.update(path.encode("utf-8"))
        hasher.update(str(array.shape).encode("ascii"))
        hasher.update(str(array.dtype).encode("ascii"))
        hasher.update(array.tobytes(order="C"))

    visit(root, "root")
    return hasher.hexdigest()


@contextlib.contextmanager
def network_block() -> Iterator[None]:
    """Deny Python network, URL, and child-process creation while active."""

    old_env = {key: os.environ.get(key) for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")}
    for key in old_env:
        os.environ[key] = "1"

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("network access is disabled for V3 offline execution")

    original_socket = socket.socket
    original_create_connection = socket.create_connection
    original_getaddrinfo = socket.getaddrinfo
    original_urlopen = urllib.request.urlopen
    original_popen = subprocess.Popen
    original_run = subprocess.run
    original_check_call = subprocess.check_call
    original_check_output = subprocess.check_output

    class OfflineSocket(original_socket):
        def connect(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("network access is disabled for V3 offline execution")

        def connect_ex(self, *_args: Any, **_kwargs: Any) -> int:
            raise RuntimeError("network access is disabled for V3 offline execution")

    socket.socket = OfflineSocket
    socket.create_connection = forbidden
    socket.getaddrinfo = forbidden
    urllib.request.urlopen = forbidden
    subprocess.Popen = forbidden
    subprocess.run = forbidden
    subprocess.check_call = forbidden
    subprocess.check_output = forbidden
    try:
        yield
    finally:
        socket.socket = original_socket
        socket.create_connection = original_create_connection
        socket.getaddrinfo = original_getaddrinfo
        urllib.request.urlopen = original_urlopen
        subprocess.Popen = original_popen
        subprocess.run = original_run
        subprocess.check_call = original_check_call
        subprocess.check_output = original_check_output
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def bootstrap_mean_ci(deltas: list[float]) -> dict[str, Any]:
    if not deltas:
        raise ValueError("bootstrap requires at least one delta")
    values = []
    for value in deltas:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
            raise ValueError("bootstrap input must be finite")
        values.append(float(value))
    n = len(values)
    samples = []
    for resample in range(BOOTSTRAP_RESAMPLES):
        total = 0.0
        for position in range(n):
            counter = f"{BOOTSTRAP_SEED}:{resample}:{position}".encode("utf-8")
            index = int.from_bytes(hashlib.sha256(counter).digest()[:8], "big") % n
            total += values[index]
        sample = total / n
        if not math.isfinite(sample):
            raise ValueError("bootstrap output must be finite")
        samples.append(sample)
    samples.sort()

    def nearest_rank(q: float) -> float:
        return samples[max(1, math.ceil(q * BOOTSTRAP_RESAMPLES)) - 1]

    return {
        "mean_delta": sum(values) / n,
        "lower": nearest_rank(0.025),
        "upper": nearest_rank(0.975),
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
        "confidence": BOOTSTRAP_CONFIDENCE,
        "prng": BOOTSTRAP_PRNG,
        "statistic": BOOTSTRAP_STATISTIC,
        "percentile": BOOTSTRAP_PERCENTILE,
        "nonfinite": BOOTSTRAP_NONFINITE,
    }


def decide_replication(bootstrap: dict[str, Any]) -> str:
    if not math.isfinite(float(bootstrap["mean_delta"])) or not math.isfinite(float(bootstrap["upper"])):
        raise ValueError("decision requires finite bootstrap values")
    return "ReplicationCandidate" if bootstrap["mean_delta"] < 0 and bootstrap["upper"] < 0 else "NoCandidate"
