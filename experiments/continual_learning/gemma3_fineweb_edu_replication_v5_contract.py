#!/usr/bin/env python3
"""V5 contract primitives for a sealed Gemma3 FineWeb-Edu replication.

State slice: continual-learning-gemma3-fineweb-edu-replication-v5.
This module is intentionally independent of the rejected V1-V4 validators.
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
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-v5"
CLAIM_CEILING = "LocalDevelopmentGemma3FineWebEduReplicationV5"
RAW_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1")
R1_SOURCE_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1")
SOURCE_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v5-source")
CORPUS_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v5-corpus")
RESULT_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v5-result")
MODEL_PATH = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
PROTOCOL_PATH = REPO_ROOT / "docs/research/continual-learning/154-gemma3-fineweb-edu-replication-v5-protocol.md"
REVIEW_PACKET_PATH = REPO_ROOT / "docs/research/continual-learning/155-gemma3-fineweb-edu-replication-v5-review-packet.md"
REVIEW_RECEIPT_PATH = REPO_ROOT / "docs/research/continual-learning/156-gemma3-fineweb-edu-replication-v5-independent-review-2026-08-30.json"
PROTOCOL_SHA256 = "366e2511b65769e904a560bd7db5deddfd102cfa647efa99b89fb03f7293cbef"
SOURCE_SCHEMA = "gemma3-fineweb-edu-replication-v5-source"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-v5-corpus"
RESULT_SCHEMA = "gemma3-fineweb-edu-replication-v5-result"
REVIEW_SCHEMA = "gemma3-fineweb-edu-replication-v5-independent-review"
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
FRESH_ROW_START = 2_048
FRESH_ROW_COUNT = 16_384
FRESH_ROW_END = FRESH_ROW_START + FRESH_ROW_COUNT
WINDOW_TOKENS = 1_024
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
BOOTSTRAP_SEED = 2_026_0829
BOOTSTRAP_CONFIDENCE = 0.95
BOOTSTRAP_PRNG = "sha256-counter-v1"
BOOTSTRAP_STATISTIC = "mean paired per-document NLL delta selected_minus_baseline"
BOOTSTRAP_PERCENTILE = "nearest-rank-1-indexed"
BOOTSTRAP_NONFINITE = "reject"
CONTROL_NAMES = (
    "native_baseline", "zero_alpha_identity", "all_candidate_evaluations",
    "temperature_1.20_baseline", "temperature_1.20_intervention",
    "deterministic_repeat", "frozen_model_manifest", "frozen_model_parameters",
)
REVIEW_FINDINGS = (
    "custody_exact_pinned_data_identity",
    "fit_assessment_prior_pilot_disjointness",
    "locked_configuration_and_paper_target_treatment",
    "controls_and_frozen_weight_behavior",
    "exact_bootstrap_and_uncertainty_rule",
    "aggregate_per_document_retention_and_validator_behavior",
    "v1_v2_v3_v4_rejections_preserved_and_prohibited_actions_enforced",
)
IMPLEMENTATION_FILES = (
    PROTOCOL_PATH,
    REVIEW_PACKET_PATH,
    REPO_ROOT / "experiments/continual_learning/gemma3_fineweb_edu_replication_v5_contract.py",
    REPO_ROOT / "experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v5.py",
    REPO_ROOT / "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v5.py",
    REPO_ROOT / "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v5.py",
    REPO_ROOT / "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v5.py",
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
            raise ValueError(f"{label} contains symlink component: {current}")


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
    prefix = f".{expected.name}.staging-"
    if supplied.parent != expected.parent or not supplied.name.startswith(prefix):
        raise ValueError(f"{label} must equal exact path {expected} or a V5 staging sibling: {supplied}")
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
                raise ValueError(f"{label} contains symlink: {candidate}")


def exact_file_set(root: Path, expected: set[str], label: str, allow_cache: bool = False) -> None:
    root = root.absolute()
    if not root.is_dir():
        raise ValueError(f"{label} must be a directory: {root}")
    reject_tree_symlinks(root, label)
    actual: set[str] = set()
    allowed_dirs = {Path(relative).parent.as_posix() for relative in expected}
    allowed_dirs.update(parent.as_posix() for relative in expected for parent in Path(relative).parents if parent != Path("."))
    for candidate in root.rglob("*"):
        relative = candidate.relative_to(root).as_posix()
        if candidate.is_file():
            if allow_cache and relative.startswith(".cache/"):
                continue
            actual.add(relative)
        elif candidate.is_dir():
            if relative not in allowed_dirs and not (allow_cache and (relative == ".cache" or relative.startswith(".cache/"))):
                raise ValueError(f"{label} contains unsupported directory: {relative}")
        else:
            raise ValueError(f"{label} contains unsupported entry: {relative}")
    if actual != expected:
        raise ValueError(f"{label} exact file set mismatch: expected {sorted(expected)}, observed {sorted(actual)}")


def model_manifest(model_path: Path) -> dict[str, Any]:
    model_path = exact_path(model_path, MODEL_PATH, "model path")
    if not model_path.is_dir():
        raise ValueError(f"model path must be a directory: {model_path}")
    reject_tree_symlinks(model_path, "model tree")
    files = []
    for candidate in sorted(model_path.rglob("*")):
        relative = candidate.relative_to(model_path).as_posix()
        if candidate.is_file() and not relative.startswith(".cache/"):
            files.append({"path": relative, "byte_len": candidate.stat().st_size, "sha256": sha256_file(candidate)})
    if not files:
        raise ValueError("cached model has no stable files")
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


def require_native_network_denial() -> None:
    if not native_network_denied():
        raise RuntimeError("V5 requires native network-outbound denial; sandbox-exec re-entry was not applied")


@contextlib.contextmanager
def network_block() -> Iterator[None]:
    old_env = {key: os.environ.get(key) for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")}
    for key in old_env:
        os.environ[key] = "1"

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("network access is disabled for V5 offline execution")

    original_socket = socket.socket
    original_connect = socket.create_connection
    original_getaddrinfo = socket.getaddrinfo
    original_urlopen = urllib.request.urlopen
    original_popen = subprocess.Popen
    original_run = subprocess.run
    original_check_call = subprocess.check_call
    original_check_output = subprocess.check_output
    original_system = os.system
    original_popen_shell = os.popen
    original_spawn = {name: getattr(os, name, None) for name in ("spawnl", "spawnle", "spawnv", "spawnve", "posix_spawn", "posix_spawnp")}

    class OfflineSocket(original_socket):
        def connect(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("network access is disabled for V5 offline execution")

        def connect_ex(self, *_args: Any, **_kwargs: Any) -> int:
            raise RuntimeError("network access is disabled for V5 offline execution")

        def sendto(self, *_args: Any, **_kwargs: Any) -> int:
            raise RuntimeError("network access is disabled for V5 offline execution")

        def send(self, *_args: Any, **_kwargs: Any) -> int:
            raise RuntimeError("network access is disabled for V5 offline execution")

        def sendall(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("network access is disabled for V5 offline execution")

        def sendmsg(self, *_args: Any, **_kwargs: Any) -> int:
            raise RuntimeError("network access is disabled for V5 offline execution")

    socket.socket = OfflineSocket
    socket.create_connection = forbidden
    socket.getaddrinfo = forbidden
    urllib.request.urlopen = forbidden
    subprocess.Popen = forbidden
    subprocess.run = forbidden
    subprocess.check_call = forbidden
    subprocess.check_output = forbidden
    os.system = forbidden
    os.popen = forbidden
    for name in original_spawn:
        if original_spawn[name] is not None:
            setattr(os, name, forbidden)
    try:
        yield
    finally:
        socket.socket = original_socket
        socket.create_connection = original_connect
        socket.getaddrinfo = original_getaddrinfo
        urllib.request.urlopen = original_urlopen
        subprocess.Popen = original_popen
        subprocess.run = original_run
        subprocess.check_call = original_check_call
        subprocess.check_output = original_check_output
        os.system = original_system
        os.popen = original_popen_shell
        for name, original in original_spawn.items():
            if original is not None:
                setattr(os, name, original)
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def bootstrap_mean_ci(deltas: list[float]) -> dict[str, Any]:
    if not deltas:
        raise ValueError("bootstrap requires at least one delta")
    values: list[float] = []
    for value in deltas:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError("bootstrap input must be finite non-boolean numbers")
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
        index = max(1, min(BOOTSTRAP_RESAMPLES, math.ceil(q * BOOTSTRAP_RESAMPLES))) - 1
        return samples[index]

    mean = sum(values) / n
    if not math.isfinite(mean):
        raise ValueError("bootstrap mean must be finite")
    return {"mean_delta": mean, "lower": nearest_rank(0.025), "upper": nearest_rank(0.975), "resamples": BOOTSTRAP_RESAMPLES, "seed": BOOTSTRAP_SEED, "confidence": BOOTSTRAP_CONFIDENCE, "prng": BOOTSTRAP_PRNG, "statistic": BOOTSTRAP_STATISTIC, "percentile": BOOTSTRAP_PERCENTILE, "nonfinite": BOOTSTRAP_NONFINITE}


def decide_replication(bootstrap: dict[str, Any]) -> str:
    mean = bootstrap.get("mean_delta")
    upper = bootstrap.get("upper")
    if isinstance(mean, bool) or isinstance(upper, bool) or not isinstance(mean, (int, float)) or not isinstance(upper, (int, float)) or not math.isfinite(float(mean)) or not math.isfinite(float(upper)):
        raise ValueError("decision requires finite bootstrap values")
    return "ReplicationCandidate" if mean < 0 and upper < 0 else "NoCandidate"


def runtime_versions() -> dict[str, str]:
    return {name: (version(name) if _installed(name) else "unavailable") for name in RUNTIME_VERSIONS}


def _installed(name: str) -> bool:
    try:
        version(name)
    except Exception:
        return False
    return True


def review_file_list() -> list[str]:
    return [path.relative_to(REPO_ROOT).as_posix() for path in IMPLEMENTATION_FILES]


def implementation_manifest() -> dict[str, Any]:
    files = []
    for path in IMPLEMENTATION_FILES:
        files.append({"path": path.relative_to(REPO_ROOT).as_posix(), "byte_len": regular(path, "V5 implementation file").stat().st_size, "sha256": sha256_file(path)})
    body = {"state_slice": STATE_SLICE, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def validate_review_receipt(path: Path) -> dict[str, Any]:
    path = exact_path(path, REVIEW_RECEIPT_PATH, "V5 review receipt")
    value = json.loads(regular(path, "V5 review receipt").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("V5 review receipt must be an object")
    stored = value.get("receipt_sha256")
    if not isinstance(stored, str) or digest({key: item for key, item in value.items() if key != "receipt_sha256"}) != stored:
        raise ValueError("V5 review receipt self-digest mismatch")
    timestamp = value.get("reviewed_at_utc")
    if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
        raise ValueError("V5 review receipt timestamp is missing")
    try:
        from datetime import datetime
        parsed = datetime.fromisoformat(timestamp[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("V5 review receipt timestamp is not ISO-8601") from exc
    if parsed.microsecond != 0 or timestamp != parsed.strftime("%Y-%m-%dT%H:%M:%SZ"):
        raise ValueError("V5 review receipt timestamp is not canonical")
    if value.get("schema") != REVIEW_SCHEMA or not isinstance(value.get("reviewer"), str) or not value["reviewer"].strip() or value.get("review_decision") != "ACCEPT" or value.get("effects_run") is not False or value.get("state_slice") != STATE_SLICE or value.get("protocol_sha256") != sha256_file(PROTOCOL_PATH) or value.get("protocol_sha256") != PROTOCOL_SHA256 or value.get("review_packet_sha256") != sha256_file(REVIEW_PACKET_PATH) or value.get("implementation_manifest_sha256") != implementation_manifest()["manifest_sha256"] or value.get("reviewed_files") != review_file_list():
        raise ValueError("V5 review receipt binding mismatch")
    findings = value.get("findings")
    if findings != {name: True for name in REVIEW_FINDINGS}:
        raise ValueError("V5 review receipt must contain exactly seven true findings")
    return value


def snapshot_files(root: Path, expected: set[str], label: str, allow_cache: bool = False) -> list[dict[str, Any]]:
    exact_file_set(root, expected, label, allow_cache=allow_cache)
    result = []
    for relative in sorted(expected):
        path = safe_relative(root, relative, f"{label} snapshot file")
        result.append({"path": relative, "byte_len": path.stat().st_size, "sha256": sha256_file(path)})
    return result


def snapshot_code_and_review() -> dict[str, Any]:
    return {
        "protocol_bytes": regular(PROTOCOL_PATH, "V5 protocol").read_bytes(),
        "packet_bytes": regular(REVIEW_PACKET_PATH, "V5 review packet").read_bytes(),
        "review_bytes": regular(REVIEW_RECEIPT_PATH, "V5 review receipt").read_bytes(),
        "implementation_manifest": implementation_manifest(),
    }


def assert_code_and_review_snapshot(snapshot: dict[str, Any]) -> None:
    if regular(PROTOCOL_PATH, "V5 protocol").read_bytes() != snapshot["protocol_bytes"] or regular(REVIEW_PACKET_PATH, "V5 review packet").read_bytes() != snapshot["packet_bytes"] or regular(REVIEW_RECEIPT_PATH, "V5 review receipt").read_bytes() != snapshot["review_bytes"] or implementation_manifest() != snapshot["implementation_manifest"]:
        raise RuntimeError("V5 reviewed code or receipt changed after sealing")


def publish_no_replace(staging: Path, final: Path, label: str, expected_files: set[str] | None = None) -> None:
    staging = staging.absolute()
    final = final.absolute()
    _reject_symlink_components(staging, label)
    _reject_symlink_components(final, label)
    if not staging.is_dir():
        raise ValueError(f"{label} staging root is missing: {staging}")
    expected_snapshot = None
    if expected_files is not None:
        exact_file_set(staging, expected_files, f"{label} final publication staging")
        expected_snapshot = snapshot_files(staging, expected_files, f"{label} final publication staging")
    if final.exists():
        raise FileExistsError(f"{label} final root already exists; refusing overwrite: {final}")
    os.mkdir(final)
    for child in sorted(staging.iterdir()):
        os.rename(child, final / child.name)
    if any(staging.iterdir()):
        raise RuntimeError(f"{label} staging root was not emptied")
    if expected_files is not None:
        observed_snapshot = snapshot_files(final, expected_files, f"{label} final publication")
        if observed_snapshot != expected_snapshot:
            raise RuntimeError(f"{label} staging contents changed during publication")
    staging.rmdir()
