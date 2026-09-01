#!/usr/bin/env python3
"""Shared V4 contract and fail-closed custody primitives.

State slice: continual-learning-gemma3-fineweb-edu-replication-v4.
"""

from __future__ import annotations

import contextlib
import ctypes
import hashlib
import json
import math
import os
import socket
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-v4"
CLAIM_CEILING = "LocalDevelopmentGemma3FineWebEduReplicationV4"
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
RAW_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1")
R1_SOURCE_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1")
SOURCE_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v4-source")
CORPUS_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v4-corpus")
RESULT_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v4-result")
MODEL_PATH = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
REVIEW_RECEIPT_PATH = REPO_ROOT / "docs/research/continual-learning/153-gemma3-fineweb-edu-replication-v4-independent-review-2026-08-30.json"
PROTOCOL_PATH = REPO_ROOT / "docs/research/continual-learning/151-gemma3-fineweb-edu-replication-v4-protocol.md"
REVIEW_PACKET_PATH = REPO_ROOT / "docs/research/continual-learning/152-gemma3-fineweb-edu-replication-v4-review-packet.md"
PROTOCOL_SHA256 = "b7007d4cdc7e986b01b6b69ac196454d555e2b2704f2a73e1875b317e3751e2e"
SOURCE_SCHEMA = "gemma3-fineweb-edu-replication-v4-source"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-v4-corpus"
RESULT_SCHEMA = "gemma3-fineweb-edu-replication-v4-result"
REVIEW_SCHEMA = "gemma3-fineweb-edu-replication-v4-independent-review"
DATASET_REPO = "HuggingFaceFW/fineweb-edu"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
DATASET_SOURCE = f"https://huggingface.co/datasets/{DATASET_REPO}"
DATASET_CONFIG = "fineweb-edu-crawl-shards"
DATASET_SPLIT = "train"
DATASET_FILES = (
    {"crawl": "CC-MAIN-2013-20", "path": "data/CC-MAIN-2013-20/train-00000-of-00014.parquet", "byte_len": 2_369_456_837, "sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03"},
    {"crawl": "CC-MAIN-2024-10", "path": "data/CC-MAIN-2024-10/000_00000.parquet", "byte_len": 1_911_528_585, "sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484"},
)
DATASET_BYTE_COUNT = sum(item["byte_len"] for item in DATASET_FILES)
R1_SOURCE_MANIFEST_SHA256 = "9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3"
EXPECTED_MODEL_MANIFEST_SHA256 = "69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256"
RUNTIME_VERSIONS = {"mlx": "0.31.2", "mlx-lm": "0.31.3", "pyarrow": "24.0.0"}
FRESH_ROW_START = 2048
FRESH_ROW_COUNT = 16_384
FRESH_ROW_END = FRESH_ROW_START + FRESH_ROW_COUNT
WINDOW_TOKENS = 1024
FIT_WINDOW_COUNT = 64
ASSESSMENT_WINDOW_COUNT = 64
FIT_ALPHA = 0.10
FIT_BETA = 0.90
EVALUATION_ALPHA = 0.15
EVALUATION_BETA = 0.85
TEMPERATURE_CONTROL = 1.20
CANDIDATE_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
EPSILON = 1e-6
PARITY_TOLERANCE = 1e-5
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260829
BOOTSTRAP_CONFIDENCE = 0.95
BOOTSTRAP_PRNG = "sha256-counter-v1"
BOOTSTRAP_STATISTIC = "mean paired per-document NLL delta selected_minus_baseline"
BOOTSTRAP_PERCENTILE = "nearest-rank-1-indexed"
BOOTSTRAP_NONFINITE = "reject"
SELECTION_POLICY = "first-64-eligible-1024-token-windows-per-disjoint-v4-source-split"
CONTROL_NAMES = ("native_baseline", "zero_alpha_identity", "all_candidate_evaluations", "temperature_1.20_baseline", "temperature_1.20_intervention", "deterministic_repeat", "frozen_model_manifest", "frozen_model_parameters")
REVIEW_FINDINGS = ("custody_exact_pinned_data_identity", "fit_assessment_prior_pilot_disjointness", "locked_configuration_and_paper_target_treatment", "controls_and_frozen_weight_behavior", "exact_bootstrap_and_uncertainty_rule", "aggregate_per_document_retention_and_validator_behavior", "v1_v2_v3_rejections_preserved_and_prohibited_actions_enforced")
IMPLEMENTATION_FILES = (
    PROTOCOL_PATH,
    REVIEW_PACKET_PATH,
    REPO_ROOT / "experiments/continual_learning/gemma3_fineweb_edu_replication_v4_contract.py",
    REPO_ROOT / "experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v4.py",
    REPO_ROOT / "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v4.py",
    REPO_ROOT / "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v4.py",
    REPO_ROOT / "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v4.py",
)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _reject_symlink_components(path: Path, label: str) -> None:
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        if current.is_symlink():
            raise ValueError(f"{label} contains a symlink component: {current}")


def exact_path(path: Path, expected: Path, label: str) -> Path:
    supplied = path.expanduser().absolute()
    if supplied != expected:
        raise ValueError(f"{label} must equal exact path {expected}: {supplied}")
    _reject_symlink_components(supplied, label)
    return supplied


def exact_or_staging_path(path: Path, expected: Path, label: str) -> Path:
    supplied = path.expanduser().absolute()
    if supplied == expected:
        _reject_symlink_components(supplied, label)
        return supplied
    staging_prefix = f".{expected.name}.staging-"
    if supplied.parent != expected.parent or not supplied.name.startswith(staging_prefix):
        raise ValueError(f"{label} must equal exact path {expected} or its V4 staging sibling: {supplied}")
    _reject_symlink_components(supplied, label)
    return supplied


def external(path: Path, label: str) -> Path:
    supplied = path.expanduser().absolute()
    _reject_symlink_components(supplied, label)
    repository = REPO_ROOT.absolute()
    if supplied == repository or repository in supplied.parents:
        raise ValueError(f"{label} must be outside the repository: {supplied}")
    return supplied


def regular(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    return path


def safe_relative(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"{label} must be a safe relative path")
    candidate = root / relative
    _reject_symlink_components(candidate, label)
    resolved = candidate.absolute()
    root_abs = root.absolute()
    if resolved == root_abs or root_abs not in resolved.parents:
        raise ValueError(f"{label} escapes its root: {relative}")
    return regular(resolved, label)


def reject_tree_symlinks(root: Path, label: str) -> None:
    _reject_symlink_components(root, label)
    if root.is_symlink():
        raise ValueError(f"{label} is a symlink")
    if root.exists():
        for candidate in root.rglob("*"):
            if candidate.is_symlink():
                raise ValueError(f"{label} contains a symlink: {candidate}")


def model_manifest(model_path: Path) -> dict[str, Any]:
    model_path = exact_path(model_path, MODEL_PATH, "model path")
    if not model_path.is_dir():
        raise ValueError(f"model path must be a real directory: {model_path}")
    reject_tree_symlinks(model_path, "model tree")
    files = []
    for candidate in sorted(model_path.rglob("*")):
        if candidate.is_file() and ".cache" not in candidate.relative_to(model_path).parts:
            files.append({"path": candidate.relative_to(model_path).as_posix(), "byte_len": candidate.stat().st_size, "sha256": sha256_file(candidate)})
    if not files:
        raise ValueError("cached model directory has no stable files")
    body = {"model_name": model_path.name, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def model_parameter_digest(model: Any) -> str:
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
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                visit(item, f"{path}/{index}")
        elif hasattr(value, "shape"):
            mx.eval(value)
            array = np.asarray(value)
            hasher.update(path.encode("utf-8"))
            hasher.update(str(array.shape).encode("ascii"))
            hasher.update(str(array.dtype).encode("ascii"))
            hasher.update(array.tobytes(order="C"))
        else:
            raise ValueError(f"unsupported model parameter at {path}")

    visit(root, "root")
    return hasher.hexdigest()


def native_network_denied() -> bool:
    if os.sys.platform != "darwin":
        return True
    try:
        check = ctypes.CDLL(None).sandbox_check
        check.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        check.restype = ctypes.c_int
        return check(os.getpid(), b"network-outbound", 0) == 1
    except (AttributeError, OSError):
        return False


@contextlib.contextmanager
def network_block() -> Iterator[None]:
    old_env = {key: os.environ.get(key) for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")}
    for key in old_env:
        os.environ[key] = "1"

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("network access is disabled for V4 offline execution")

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
            raise RuntimeError("network access is disabled for V4 offline execution")

        def connect_ex(self, *_args: Any, **_kwargs: Any) -> int:
            raise RuntimeError("network access is disabled for V4 offline execution")

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
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
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

    return {"mean_delta": sum(values) / n, "lower": nearest_rank(0.025), "upper": nearest_rank(0.975), "resamples": BOOTSTRAP_RESAMPLES, "seed": BOOTSTRAP_SEED, "confidence": BOOTSTRAP_CONFIDENCE, "prng": BOOTSTRAP_PRNG, "statistic": BOOTSTRAP_STATISTIC, "percentile": BOOTSTRAP_PERCENTILE, "nonfinite": BOOTSTRAP_NONFINITE}


def decide_replication(bootstrap: dict[str, Any]) -> str:
    mean = bootstrap.get("mean_delta")
    upper = bootstrap.get("upper")
    if isinstance(mean, bool) or isinstance(upper, bool) or not isinstance(mean, (int, float)) or not isinstance(upper, (int, float)) or not math.isfinite(float(mean)) or not math.isfinite(float(upper)):
        raise ValueError("decision requires finite bootstrap values")
    return "ReplicationCandidate" if mean < 0 and upper < 0 else "NoCandidate"


def runtime_versions() -> dict[str, str]:
    from importlib.metadata import version

    result = {}
    for name in RUNTIME_VERSIONS:
        try:
            result[name] = version(name)
        except Exception:
            result[name] = "unavailable"
    return result
