#!/usr/bin/env python3
"""V8 custody and statistical contract.

State slice: continual-learning-gemma3-fineweb-edu-replication-v8.
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
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-v8"
CLAIM_CEILING = "LocalDevelopmentGemma3FineWebEduReplicationV8"
RAW_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1"
)
PRIOR_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1"
)
SOURCE_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v8-source"
)
CORPUS_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v8-corpus"
)
RESULT_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v8-result"
)
MODEL_PATH = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
PROTOCOL_PATH = (
    REPO_ROOT
    / "docs/research/continual-learning/163-gemma3-fineweb-edu-replication-v8-protocol.md"
)
PACKET_PATH = (
    REPO_ROOT
    / "docs/research/continual-learning/164-gemma3-fineweb-edu-replication-v8-review-packet.md"
)
RECEIPT_PATH = (
    REPO_ROOT
    / "docs/research/continual-learning/165-gemma3-fineweb-edu-replication-v8-independent-review-2026-08-30.json"
)
PROTOCOL_SHA256 = "bb700fec755b53cf0470ccefb3dea6fb70f3b9b40c1db9d7a04d0733a2c534ab"
SOURCE_SCHEMA = "gemma3-fineweb-edu-replication-v8-source"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-v8-corpus"
RESULT_SCHEMA = "gemma3-fineweb-edu-replication-v8-result"
REVIEW_SCHEMA = "gemma3-fineweb-edu-replication-v8-independent-review"
DATASET_REPO = "HuggingFaceFW/fineweb-edu"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
DATASET_SOURCE = f"https://huggingface.co/datasets/{DATASET_REPO}"
DATASET_CONFIG, DATASET_SPLIT = "fineweb-edu-crawl-shards", "train"
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
PRIOR_MANIFEST_SHA256 = (
    "9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3"
)
MODEL_STABLE_MANIFEST_SHA256 = (
    "69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256"
)
MODEL_CACHE_MANIFEST_SHA256 = (
    "ba026071c4026cdc5b4692c2d43b3859d1211b97c3c3a5f7cae5cffd058f6485"
)
MODEL_STABLE_FILES = (
    ".gitattributes",
    "README.md",
    "added_tokens.json",
    "config.json",
    "model.safetensors",
    "model.safetensors.index.json",
    "preprocessor_config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
)
MODEL_CACHE_FILES = (
    ".cache/huggingface/.gitignore",
    ".cache/huggingface/CACHEDIR.TAG",
    ".cache/huggingface/download/.gitattributes.metadata",
    ".cache/huggingface/download/README.md.metadata",
    ".cache/huggingface/download/added_tokens.json.metadata",
    ".cache/huggingface/download/config.json.metadata",
    ".cache/huggingface/download/model.safetensors.index.json.metadata",
    ".cache/huggingface/download/model.safetensors.metadata",
    ".cache/huggingface/download/preprocessor_config.json.metadata",
    ".cache/huggingface/download/special_tokens_map.json.metadata",
    ".cache/huggingface/download/tokenizer.json.metadata",
    ".cache/huggingface/download/tokenizer.model.metadata",
    ".cache/huggingface/download/tokenizer_config.json.metadata",
)
PRIOR_HISTORY = (
    {
        "path": "docs/research/continual-learning/145-gemma3-fineweb-edu-replication-v1-independent-review-rejection-2026-08-30.json",
        "sha256": "126b3cced429d52fda6ec6cee7f63a7b87eb7d897d24f9b286f38de642ab8249",
    },
    {
        "path": "docs/research/continual-learning/146-gemma3-fineweb-edu-replication-v2-protocol.md",
        "sha256": "580d3890668303e870184e910e0c0cd2098ddb6064b89da565385489e7e71564",
    },
    {
        "path": "docs/research/continual-learning/147-gemma3-fineweb-edu-replication-v2-review-packet.md",
        "sha256": "b706f7c699838e22c702e6af0725dfe640fd724d778d09828dd292770f625483",
    },
    {
        "path": "docs/research/continual-learning/148-gemma3-fineweb-edu-replication-v3-protocol.md",
        "sha256": "5c9c8e0b6ede43bde9fa66a98fb515b597fafa2f3ebcd811c1925ca5a457b8f7",
    },
    {
        "path": "docs/research/continual-learning/149-gemma3-fineweb-edu-replication-v3-review-packet.md",
        "sha256": "ce745e40260cc6dce814cbba0d7706c35207c38bc19622186813c4800e7a140b",
    },
    {
        "path": "docs/research/continual-learning/151-gemma3-fineweb-edu-replication-v4-protocol.md",
        "sha256": "b7007d4cdc7e986b01b6b69ac196454d555e2b2704f2a73e1875b317e3751e2e",
    },
    {
        "path": "docs/research/continual-learning/152-gemma3-fineweb-edu-replication-v4-review-packet.md",
        "sha256": "5ea9a8485b18e4107bebb5a53798983628738dd75f5b454b829e41244759347b",
    },
    {
        "path": "docs/research/continual-learning/154-gemma3-fineweb-edu-replication-v5-protocol.md",
        "sha256": "366e2511b65769e904a560bd7db5deddfd102cfa647efa99b89fb03f7293cbef",
    },
    {
        "path": "docs/research/continual-learning/155-gemma3-fineweb-edu-replication-v5-review-packet.md",
        "sha256": "57025b835ae99c739b6a30f66d0106e3549535591f295e0cae8c240f162a22bb",
    },
    {
        "path": "docs/research/continual-learning/157-gemma3-fineweb-edu-replication-v6-protocol.md",
        "sha256": "90fcbd2602ca215f392faa924316a9d5c34ae1ccb504716b00e1f58ed274c507",
    },
    {
        "path": "docs/research/continual-learning/158-gemma3-fineweb-edu-replication-v6-review-packet.md",
        "sha256": "cc5aab926501c3dbd6eccac5a8ba62347a056dc7ec9a2802be5b2c1d948effd7",
    },
    {
        "path": "docs/research/continual-learning/160-gemma3-fineweb-edu-replication-v7-protocol.md",
        "sha256": "f973c8798b9add05c53f0149b47716ee58b8ea232de88d73dd67b6d110b8da08",
    },
    {
        "path": "docs/research/continual-learning/161-gemma3-fineweb-edu-replication-v7-review-packet.md",
        "sha256": "7a5bacf8fb726d1645e7a24b9cda4158d8f0e8b9610a75499e5cbedd08d3bd5d",
    },
    {
        "path": "docs/research/continual-learning/162-gemma3-fineweb-edu-replication-v7-independent-review-2026-08-30.json",
        "sha256": "48ff180efa579bcbcc94562d8569937939dc96962da56b3e291e84fdfa35cee1",
    },
)
RUNTIME_VERSIONS = {"mlx": "0.31.2", "mlx-lm": "0.31.3", "pyarrow": "24.0.0"}
FRESH_ROW_START, FRESH_ROW_COUNT, WINDOW_TOKENS = 2_048, 16_384, 1_024
FRESH_ROW_END = FRESH_ROW_START + FRESH_ROW_COUNT
FIT_WINDOW_COUNT = ASSESSMENT_WINDOW_COUNT = 64
FIT_ALPHA, FIT_BETA, EVALUATION_ALPHA, EVALUATION_BETA = 0.10, 0.90, 0.15, 0.85
TEMPERATURE_CONTROL = 1.20
CANDIDATE_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
EPSILON, PARITY_TOLERANCE = 1e-6, 1e-5
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
    PACKET_PATH,
    REPO_ROOT
    / "experiments/continual_learning/gemma3_fineweb_edu_replication_v8_contract.py",
    REPO_ROOT
    / "experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v8.py",
    REPO_ROOT
    / "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v8.py",
    REPO_ROOT
    / "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v8.py",
    REPO_ROOT
    / "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v8.py",
)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def reject_symlink_components(path: Path, label: str) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError(f"{label} contains symlink component: {current}")


def exact_path(path: Path, expected: Path, label: str) -> Path:
    supplied = path.expanduser().absolute()
    if supplied != expected:
        raise ValueError(f"{label} must equal {expected}: {supplied}")
    reject_symlink_components(supplied, label)
    return supplied


def exact_or_staging(path: Path, expected: Path, label: str) -> Path:
    supplied = path.expanduser().absolute()
    if supplied != expected and (
        supplied.parent != expected.parent
        or not supplied.name.startswith(f".{expected.name}.staging-")
    ):
        raise ValueError(f"{label} is not the V8 root or staging sibling")
    reject_symlink_components(supplied, label)
    return supplied


def regular(path: Path, label: str) -> Path:
    reject_symlink_components(path.absolute(), label)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    return path


def safe_relative(root: Path, relative: Any, label: str) -> Path:
    if (
        not isinstance(relative, str)
        or not relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
    ):
        raise ValueError(f"{label} must be safe relative")
    candidate = root / relative
    reject_symlink_components(candidate.absolute(), label)
    resolved = candidate.absolute()
    root_abs = root.absolute()
    if resolved == root_abs or root_abs not in resolved.parents:
        raise ValueError(f"{label} escapes root")
    return regular(resolved, label)


def exact_file_set(root: Path, expected: set[str], label: str) -> None:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"{label} must be a real directory")
    reject_symlink_components(root.absolute(), label)
    actual = set()
    allowed_dirs = {
        parent.as_posix()
        for item in expected
        for parent in Path(item).parents
        if parent != Path(".")
    }
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise ValueError(f"{label} contains symlink")
        relative = candidate.relative_to(root).as_posix()
        if candidate.is_file():
            actual.add(relative)
        elif not candidate.is_dir() or relative not in allowed_dirs:
            raise ValueError(f"{label} contains unsupported entry: {relative}")
    if actual != expected:
        raise ValueError(f"{label} exact file set mismatch")


def model_manifest(model_path: Path) -> dict[str, Any]:
    root = exact_path(model_path, MODEL_PATH, "model path")
    if not root.is_dir():
        raise ValueError("model path must be a directory")
    reject_symlink_components(root, "model tree")
    expected = set(MODEL_STABLE_FILES) | set(MODEL_CACHE_FILES)
    allowed_dirs = {
        parent.as_posix()
        for item in expected
        for parent in Path(item).parents
        if parent != Path(".")
    }
    actual = set()
    for candidate in root.rglob("*"):
        relative = candidate.relative_to(root).as_posix()
        if candidate.is_symlink():
            raise ValueError(f"model tree contains symlink: {relative}")
        if candidate.is_file():
            if relative not in expected:
                raise ValueError(f"model tree contains unsupported file: {relative}")
            actual.add(relative)
        elif not candidate.is_dir() or relative not in allowed_dirs:
            raise ValueError(f"model tree contains unsupported entry: {relative}")
    if actual != expected:
        raise ValueError("model tree exact file set mismatch")

    def file_list(names: tuple[str, ...]) -> list[dict[str, Any]]:
        return [
            {
                "path": name,
                "byte_len": (root / name).stat().st_size,
                "sha256": sha256_file(root / name),
            }
            for name in names
        ]

    stable, cache = (
        {"model_name": root.name, "files": file_list(MODEL_STABLE_FILES)},
        {"model_name": root.name, "files": file_list(MODEL_CACHE_FILES)},
    )
    return {
        "manifest": stable,
        "manifest_sha256": digest(stable),
        "cache_manifest": cache,
        "cache_manifest_sha256": digest(cache),
    }


def validate_prior_history() -> list[dict[str, str]]:
    result = []
    for item in PRIOR_HISTORY:
        path = REPO_ROOT / item["path"]
        regular(path, "prior rejection history")
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"prior history changed: {item['path']}")
        result.append(dict(item))
    return result


def native_network_denied() -> bool:
    if os.sys.platform != "darwin":
        return False
    try:
        check = ctypes.CDLL(None).sandbox_check
        check.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        check.restype = ctypes.c_int
        return check(os.getpid(), b"network-outbound", 0) == 1
    except (AttributeError, OSError):
        return False


def require_native_network_denial() -> None:
    if not native_network_denied():
        raise RuntimeError("V8 native outbound network denial is not proven")


@contextlib.contextmanager
def network_block() -> Iterator[None]:
    old_env = {
        key: os.environ.get(key)
        for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")
    }
    for key in old_env:
        os.environ[key] = "1"

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("V8 network/process escape denied")

    original_socket = socket.socket
    original_socket_functions = {
        name: getattr(socket, name)
        for name in (
            "create_connection",
            "getaddrinfo",
            "gethostbyname",
            "gethostbyname_ex",
            "gethostbyaddr",
            "getnameinfo",
            "getfqdn",
        )
    }
    original_urlopen = urllib.request.urlopen
    original_subprocess = {
        name: getattr(subprocess, name)
        for name in ("Popen", "run", "check_call", "check_output")
    }
    original_os = {name: getattr(os, name) for name in ("system", "popen")}
    process_names = (
        "spawnl",
        "spawnle",
        "spawnv",
        "spawnve",
        "posix_spawn",
        "posix_spawnp",
        "execv",
        "execve",
        "execvpe",
        "fork",
        "forkpty",
        "startfile",
    )
    original_process = {name: getattr(os, name, None) for name in process_names}

    class OfflineSocket(original_socket):
        connect = forbidden
        connect_ex = forbidden
        sendto = forbidden
        send = forbidden
        sendall = forbidden
        sendmsg = forbidden
        sendfile = forbidden

    socket.socket = OfflineSocket
    for name in original_socket_functions:
        setattr(socket, name, forbidden)
    urllib.request.urlopen = forbidden
    for name in original_subprocess:
        setattr(subprocess, name, forbidden)
    for name in original_os:
        setattr(os, name, forbidden)
    for name, value in original_process.items():
        if value is not None:
            setattr(os, name, forbidden)
    try:
        yield
    finally:
        socket.socket = original_socket
        for name, value in original_socket_functions.items():
            setattr(socket, name, value)
        urllib.request.urlopen = original_urlopen
        for name, value in original_subprocess.items():
            setattr(subprocess, name, value)
        for name, value in original_os.items():
            setattr(os, name, value)
        for name, value in original_process.items():
            if value is not None:
                setattr(os, name, value)
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def model_parameter_digest(model: Any) -> str:
    import numpy as np
    import mlx.core as mx

    root = model.parameters() if hasattr(model, "parameters") else None
    if root is None:
        raise ValueError("model exposes no parameters")
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
            hasher.update(path.encode())
            hasher.update(str(array.shape).encode())
            hasher.update(str(array.dtype).encode())
            hasher.update(array.tobytes(order="C"))
        else:
            raise ValueError(f"unsupported parameter at {path}")

    visit(root, "root")
    return hasher.hexdigest()


def bootstrap_mean_ci(deltas: list[float]) -> dict[str, Any]:
    if not deltas:
        raise ValueError("bootstrap requires data")
    values = []
    for value in deltas:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise ValueError("bootstrap input must be finite non-boolean")
        values.append(float(value))
    n, samples = len(values), []
    for resample in range(BOOTSTRAP_RESAMPLES):
        total = 0.0
        for position in range(n):
            counter = f"{BOOTSTRAP_SEED}:{resample}:{position}".encode()
            total += values[
                int.from_bytes(hashlib.sha256(counter).digest()[:8], "big") % n
            ]
        samples.append(total / n)
    samples.sort()

    def rank(q: float) -> float:
        return samples[
            max(1, min(BOOTSTRAP_RESAMPLES, math.ceil(q * BOOTSTRAP_RESAMPLES))) - 1
        ]

    mean = sum(values) / n
    if not math.isfinite(mean):
        raise ValueError("bootstrap mean is nonfinite")
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


def decide_replication(value: dict[str, Any]) -> str:
    mean, upper = value.get("mean_delta"), value.get("upper")
    if any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(float(item))
        for item in (mean, upper)
    ):
        raise ValueError("decision values invalid")
    return "ReplicationCandidate" if mean < 0 and upper < 0 else "NoCandidate"


def implementation_manifest() -> dict[str, Any]:
    files = []
    for path in IMPLEMENTATION_FILES:
        reject_symlink_components(path.absolute(), "V8 implementation file")
        item = regular(path, "V8 implementation file")
        files.append(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "byte_len": item.stat().st_size,
                "sha256": sha256_file(item),
            }
        )
    body = {"state_slice": STATE_SLICE, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def review_file_list() -> list[str]:
    return [path.relative_to(REPO_ROOT).as_posix() for path in IMPLEMENTATION_FILES]


def validate_review_receipt(path: Path) -> dict[str, Any]:
    path = exact_path(path, RECEIPT_PATH, "V8 review receipt")
    value = json.loads(regular(path, "V8 review receipt").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("V8 review receipt must be an object")
    stored = value.get("receipt_sha256")
    if (
        not isinstance(stored, str)
        or digest({key: item for key, item in value.items() if key != "receipt_sha256"})
        != stored
    ):
        raise ValueError("V8 review receipt self-digest mismatch")
    timestamp = value.get("reviewed_at_utc")
    if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
        raise ValueError("V8 review timestamp missing")
    parsed = datetime.fromisoformat(timestamp[:-1] + "+00:00")
    if parsed.microsecond or timestamp != parsed.strftime("%Y-%m-%dT%H:%M:%SZ"):
        raise ValueError("V8 review timestamp noncanonical")
    if (
        value.get("schema") != REVIEW_SCHEMA
        or not isinstance(value.get("reviewer"), str)
        or not value["reviewer"].strip()
        or value.get("review_decision") != "ACCEPT"
        or value.get("effects_run") is not False
        or value.get("state_slice") != STATE_SLICE
        or value.get("protocol_sha256") != sha256_file(PROTOCOL_PATH)
        or value.get("protocol_sha256") != PROTOCOL_SHA256
        or value.get("review_packet_sha256") != sha256_file(PACKET_PATH)
        or value.get("implementation_manifest_sha256")
        != implementation_manifest()["manifest_sha256"]
        or value.get("reviewed_files") != review_file_list()
    ):
        raise ValueError("V8 review receipt binding mismatch")
    if value.get("findings") != {name: True for name in REVIEW_FINDINGS}:
        raise ValueError("V8 receipt requires seven true findings")
    return value


def snapshot_files(root: Path, expected: set[str], label: str) -> list[dict[str, Any]]:
    exact_file_set(root, expected, label)
    result = []
    for relative in sorted(expected):
        path = safe_relative(root, relative, f"{label} file")
        result.append(
            {
                "path": relative,
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return result


def snapshot_code() -> dict[str, Any]:
    return {
        "protocol": regular(PROTOCOL_PATH, "V8 protocol").read_bytes(),
        "packet": regular(PACKET_PATH, "V8 packet").read_bytes(),
        "receipt": regular(RECEIPT_PATH, "V8 receipt").read_bytes(),
        "implementation": implementation_manifest(),
        "history": validate_prior_history(),
    }


def assert_code_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot_code() != snapshot:
        raise RuntimeError("V8 reviewed bytes or history changed")


def publish_no_replace(
    staging: Path, final: Path, expected: set[str], label: str
) -> None:
    if final.exists():
        raise FileExistsError(f"{label} final root exists")
    exact_file_set(staging, expected, f"{label} staging")
    before = snapshot_files(staging, expected, f"{label} staging")
    os.mkdir(final)
    for child in sorted(staging.iterdir()):
        os.rename(child, final / child.name)
    if (
        list(staging.iterdir())
        or snapshot_files(final, expected, f"{label} final") != before
    ):
        raise RuntimeError(f"{label} publication changed bytes")
    staging.rmdir()


def runtime_versions() -> dict[str, str]:
    return {
        name: (version(name) if installed(name) else "unavailable")
        for name in RUNTIME_VERSIONS
    }


def installed(name: str) -> bool:
    try:
        version(name)
    except Exception:
        return False
    return True
