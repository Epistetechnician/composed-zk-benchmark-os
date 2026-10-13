"""Frozen local BillSum same-roster order experiment.

State slice: aligned-rsi-billsum-same-roster-order-curriculum-v9.
Governance slice: global-experiment-assurance-lifecycle-v1.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import platform
import random
import resource
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from experiments.continual_learning import aligned_rsi_billsum_length_matched_v8 as h


STATE_SLICE = "aligned-rsi-billsum-same-roster-order-curriculum-v9"
GOVERNANCE_SLICE = "global-experiment-assurance-lifecycle-v1"
PROTOCOL_ID = "aligned-rsi-billsum-same-roster-order-v9"
CLAIM_CEILING = "LocalDevelopmentBillSumSameRosterCurriculumOrderQualificationV9"
MODEL_ID = "Qwen/Qwen3-0.6B"
MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
DATASET_ID = "FiscalNote/billsum"
DATASET_REVISION = "3d8510441c06a3d9dfb32eb0d7f80151730bcc4f"
FIT_COUNT = 128
ASSESSMENT_COUNT = 120
SEEDS = (607, 701, 809, 907)
TRAINING_BATCH_SIZE = 4
OPTIMIZER_STEPS = 32
ORDER_SEED_XOR = 0x4F524439
TRAINED_ARMS = ("easy_to_hard_order", "random_order_control")
ALL_ARMS = ("untouched_base", *TRAINED_ARMS)
PRIMARY_ARM = "easy_to_hard_order"
CONTROL_ARM = "random_order_control"
MECHANISTIC_ROWS = 16
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261011
MIN_EFFECT = 0.02
IDENTITY_PATCH_TOLERANCE = 1e-5
MAX_SOURCE_TOKENS = 1280
MAX_TARGET_TOKENS = 512
WALL_CLOCK_LIMIT_SECONDS = 8 * 60 * 60
V8_MODULE_SHA256 = "a283132b28161dea1c6e1b389267f18b618f76d77cb3c1d213a1b237d7192e89"
V8_LOCK_SHA256 = "e8c11d4a260328b27732188d1080891dd9da8cf253a6477e486b256fedcba085"
MANIFEST_SHA256 = "825a656ad262ca3977c4a8e762f50ea237d54289e815b61a84a6308b61a1be2b"

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = REPO_ROOT / "docs/research/continual-learning/328-aligned-rsi-billsum-same-roster-order-curriculum-v9.md"
MANIFEST_PATH = Path(__file__).with_name("aligned_rsi_billsum_same_roster_order_v9.json")
TEST_PATH = Path(__file__).parent / "tests/test_aligned_rsi_billsum_same_roster_order_v9.py"
V8_MODULE_PATH = Path(h.__file__).resolve()
V8_MANIFEST_PATH = V8_MODULE_PATH.with_name("aligned_rsi_billsum_length_matched_v8.json")
V8_LOCK_PATH = V8_MODULE_PATH.with_name("aligned_rsi_billsum_length_matched_v8_requirements.lock")
V1_OWNER_ROOT = Path.home() / ".local/share/aligned-rsi-local-billsum-adaptation-v1"
MODEL_ROOT = V1_OWNER_ROOT / "inputs/model"
DATASET_ROOT = V1_OWNER_ROOT / "inputs/billsum"
OWNER_ROOT = Path.home() / ".local/share/aligned-rsi-billsum-same-roster-order-v9"
PREPARED_PATH = OWNER_ROOT / "prepared_inputs.json"
RUNS_ROOT = OWNER_ROOT / "runs"
RELEASE_ROOT = REPO_ROOT / "release/aligned_rsi_billsum_same_roster_order_v9"
PUBLIC_REPORT_PATH = RELEASE_ROOT / "evaluation_report.json"


class ExperimentError(ValueError):
    """Raised when the frozen V9 contract or local evidence is invalid."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ExperimentError(f"non-standard JSON value: {token}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"cannot read JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise ExperimentError(f"expected JSON object: {path.name}")
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ExperimentError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def save_json(path: Path, value: Any, *, private: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700 if private else 0o755)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(
        json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False).encode("utf-8")
        + b"\n"
    )
    temporary.chmod(0o600 if private else 0o644)
    temporary.replace(path)


def _verify_contract() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    if MANIFEST_SHA256 == "TO_BE_FROZEN" or sha256_file(MANIFEST_PATH) != MANIFEST_SHA256:
        raise ExperimentError("V9 machine-contract bytes are not frozen to the runner")
    expected = {
        "schema_version": "aligned-rsi-billsum-same-roster-order-v9-protocol",
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "governance_slice": GOVERNANCE_SLICE,
        "status": "LOCAL_EXECUTION_AUTHORIZED_BY_USER",
        "assurance_target": "INTERNAL_PASS",
        "claim_ceiling": CLAIM_CEILING,
        "independent_acceptance_requested": False,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ExperimentError(f"V9 machine-contract mismatch: {key}")
    if manifest.get("runtime") != h._runtime_manifest():
        raise ExperimentError("installed packages differ from the frozen V8 resolved runtime")
    dependency = manifest.get("implementation_dependency", {})
    if (
        dependency.get("module") != "experiments/continual_learning/aligned_rsi_billsum_length_matched_v8.py"
        or dependency.get("sha256") != V8_MODULE_SHA256
        or dependency.get("resolved_runtime_lock_sha256") != V8_LOCK_SHA256
        or sha256_file(V8_MODULE_PATH) != V8_MODULE_SHA256
        or sha256_file(V8_LOCK_PATH) != V8_LOCK_SHA256
    ):
        raise ExperimentError("pinned V8 helper or resolved-runtime lock changed")
    model = manifest.get("model", {})
    if (
        model.get("repo_id") != MODEL_ID
        or model.get("revision") != MODEL_REVISION
        or model.get("chat_template_sha256") != h.CHAT_TEMPLATE_SHA256
        or model.get("base_weights_mutable") is not False
        or model.get("adapter_package") != "peft==0.21.2"
    ):
        raise ExperimentError("V9 model identity differs from its frozen contract")
    dataset = manifest.get("dataset", {})
    if (
        dataset.get("repo_id") != DATASET_ID
        or dataset.get("revision") != DATASET_REVISION
        or dataset.get("included_splits") != ["train", "test"]
        or dataset.get("excluded_splits") != ["ca_test"]
        or dataset.get("prompt", {}).get("source_truncation") is not False
        or dataset.get("prompt", {}).get("assistant_target_truncation") is not False
    ):
        raise ExperimentError("V9 dataset identity or no-truncation rule differs")
    cohorts = manifest.get("cohorts", {})
    if (
        cohorts.get("fit_count") != FIT_COUNT
        or cohorts.get("assessment_count") != ASSESSMENT_COUNT
        or cohorts.get("minimum_fit_count") != FIT_COUNT
        or cohorts.get("minimum_assessment_count") != ASSESSMENT_COUNT
        or cohorts.get("fit_roster_sha256") != "7beba247d474ca17858aa7b156c863bf869ee3bec3f0f98ed045bcf2152771aa"
        or cohorts.get("assessment_roster_sha256") != "a0d2608ccc9af7aeaede2e13a07df0e6b29abaff7b831835211116d5411d1f09"
        or cohorts.get("fresh_fit_assessment_overlap") != 0
    ):
        raise ExperimentError("V9 fresh cohort differs from the read-only frozen feasibility audit")
    training = manifest.get("training", {})
    if (
        training.get("seeds") != list(SEEDS)
        or training.get("training_examples_per_updated_arm_per_seed") != FIT_COUNT
        or training.get("equal_optimizer_steps_per_updated_arm") != OPTIMIZER_STEPS
        or training.get("total_optimizer_steps") != len(SEEDS) * len(TRAINED_ARMS) * OPTIMIZER_STEPS
        or training.get("roster_identity_across_arms")
        != "exact_same_128_source_ids_and_token_sequences_for_every_seed_and_arm"
    ):
        raise ExperimentError("V9 training budget or matched-roster rule differs")
    if manifest.get("primary_metric", {}).get("bootstrap_resamples") != BOOTSTRAP_RESAMPLES:
        raise ExperimentError("V9 bootstrap count differs from the frozen protocol")
    if manifest.get("primary_metric", {}).get("bootstrap_seed") != BOOTSTRAP_SEED:
        raise ExperimentError("V9 bootstrap seed differs from the frozen protocol")
    if manifest.get("execution", {}).get("wall_clock_limit_minutes") != 480:
        raise ExperimentError("V9 local execution ceiling differs from the frozen protocol")
    if manifest.get("execution", {}).get("output_root") != "$HOME/.local/share/aligned-rsi-billsum-same-roster-order-v9":
        raise ExperimentError("V9 private custody root differs from the frozen protocol")
    return manifest


def _source_manifest() -> dict[str, str]:
    paths = {
        "runner": Path(__file__).resolve(),
        "protocol": PROTOCOL_PATH,
        "machine_contract": MANIFEST_PATH,
        "focused_tests": TEST_PATH,
        "repository_instructions": REPO_ROOT / "AGENTS.md",
        "pinned_v8_helper": V8_MODULE_PATH,
        "pinned_v8_resolved_runtime_lock": V8_LOCK_PATH,
    }
    if any(not path.is_file() for path in paths.values()):
        missing = [name for name, path in paths.items() if not path.is_file()]
        raise ExperimentError(f"V9 source packet is incomplete: {missing}")
    return {name: sha256_file(path) for name, path in paths.items()}


def _check_dir(root: Path, *, create: bool = False) -> None:
    if root.is_symlink():
        raise ExperimentError(f"owner-only custody root cannot be a symlink: {root.name}")
    if not root.exists():
        if not create:
            raise ExperimentError(f"owner-only custody root is missing: {root.name}")
        root.mkdir(parents=True, mode=0o700)
    if not root.is_dir():
        raise ExperimentError(f"owner-only custody path is not a directory: {root.name}")
    root.chmod(0o700)
    if root.stat().st_mode & 0o777 != 0o700:
        raise ExperimentError(f"owner-only custody root must have mode 0700: {root.name}")


def _assert_private_dir(root: Path) -> None:
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o777 != 0o700:
        raise ExperimentError(f"prior owner-only custody root is unavailable or has wrong mode: {root.name}")


def _check_private_tree(root: Path) -> None:
    _check_dir(root)
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ExperimentError(f"owner-only custody contains a symlink: {path.relative_to(root)}")
        if path.is_dir() and path.stat().st_mode & 0o777 != 0o700:
            raise ExperimentError(f"owner-only directory mode is invalid: {path.relative_to(root)}")
        if path.is_file() and path.stat().st_mode & 0o777 != 0o600:
            raise ExperimentError(f"owner-only file mode is invalid: {path.relative_to(root)}")


def _read_pinned_receipt(path: Path, expected_sha: str, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o777 != 0o600:
        raise ExperimentError(f"prior {label} prepared-input receipt is unavailable")
    receipt = load_json(path)
    digest = receipt.get("prepared_inputs_sha256")
    unsigned = {key: value for key, value in receipt.items() if key != "prepared_inputs_sha256"}
    if digest != sha256_bytes(canonical_bytes(unsigned)) or digest != expected_sha:
        raise ExperimentError(f"prior {label} prepared-input receipt digest differs")
    return receipt


def _verify_v1_receipt(model_files: list[dict[str, str]], dataset_files: list[dict[str, str]]) -> dict[str, Any]:
    _assert_private_dir(V1_OWNER_ROOT)
    path = V1_OWNER_ROOT / "prepared_inputs.json"
    expected = _verify_contract()["immutable_inputs"]
    if path.is_symlink() or not path.is_file() or sha256_file(path) != expected["v1_prepared_receipt_file_sha256"]:
        raise ExperimentError("V1 pinned-input receipt bytes differ from the V9 contract")
    receipt = load_json(path)
    digest = receipt.get("prepared_inputs_sha256")
    unsigned = {key: value for key, value in receipt.items() if key != "prepared_inputs_sha256"}
    if digest != sha256_bytes(canonical_bytes(unsigned)) or digest != expected["v1_prepared_payload_sha256"]:
        raise ExperimentError("V1 prepared-input payload digest is invalid")
    if (
        receipt.get("state_slice") != "aligned-rsi-local-billsum-adaptation-internal-v1"
        or receipt.get("model_repo_id") != MODEL_ID
        or receipt.get("model_revision") != MODEL_REVISION
        or receipt.get("dataset_repo_id") != DATASET_ID
        or receipt.get("dataset_revision") != DATASET_REVISION
        or receipt.get("model_files") != model_files
        or receipt.get("dataset_files") != dataset_files
        or receipt.get("included_dataset_files") != list(h.DATA_FILES)
        or receipt.get("excluded_split") != "ca_test"
    ):
        raise ExperimentError("V1 prepared-input receipt does not bind the frozen V9 model and data")
    return receipt


def _load_prior_rosters(
    model_files_sha256: str,
    dataset_files_sha256: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]], dict[str, set[str]]]:
    v8_contract = h._verify_protocol()
    frozen_prior = v8_contract["prepared_identity"]["prior_rosters"]
    contract = _verify_contract()
    expected = contract["cohorts"]["prior_rosters"]
    fit_sets: dict[str, set[str]] = {}
    assessment_sets: dict[str, set[str]] = {}
    summaries: dict[str, dict[str, Any]] = {}
    for version in range(4, 8):
        key = f"v{version}"
        root = Path.home() / f".local/share/aligned-rsi-billsum-chat-template-adaptation-{key}"
        _assert_private_dir(root)
        receipt = _read_pinned_receipt(root / "prepared_inputs.json", expected[key]["receipt_sha256"], key)
        fit_ids = receipt.get("fit_ids")
        assessment_ids = receipt.get("assessment_ids")
        if not isinstance(fit_ids, list) or not isinstance(assessment_ids, list):
            raise ExperimentError(f"prior {key} receipt has no complete source rosters")
        frozen = frozen_prior[key]
        if (
            receipt.get("state_slice") != f"aligned-rsi-billsum-chat-template-adaptation-{key}"
            or receipt.get("model_repo_id") != MODEL_ID
            or receipt.get("model_revision") != MODEL_REVISION
            or receipt.get("dataset_repo_id") != DATASET_ID
            or receipt.get("dataset_revision") != DATASET_REVISION
            or receipt.get("model_files_sha256") != model_files_sha256
            or receipt.get("dataset_files_sha256") != dataset_files_sha256
            or len(fit_ids) != frozen["fit_count"]
            or len(assessment_ids) != frozen["assessment_count"]
            or len(set(fit_ids)) != len(fit_ids)
            or len(set(assessment_ids)) != len(assessment_ids)
            or sha256_bytes(canonical_bytes(sorted(fit_ids))) != frozen["fit_source_ids_sha256"]
            or sha256_bytes(canonical_bytes(sorted(assessment_ids))) != frozen["assessment_source_ids_sha256"]
        ):
            raise ExperimentError(f"prior {key} receipt roster or input identity differs")
        fit_sets[key] = set(fit_ids)
        assessment_sets[key] = set(assessment_ids)
        summaries[key] = {
            "receipt_sha256": receipt["prepared_inputs_sha256"],
            "fit_count": len(fit_ids),
            "assessment_count": len(assessment_ids),
            "fit_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(fit_ids))),
            "assessment_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(assessment_ids))),
        }

    root_v8 = Path.home() / ".local/share/aligned-rsi-billsum-length-matched-curriculum-v8"
    _assert_private_dir(root_v8)
    receipt_v8 = _read_pinned_receipt(
        root_v8 / "prepared_inputs.json",
        expected["v8"]["receipt_sha256"],
        "v8",
    )
    fit_ids = receipt_v8.get("fit_ids")
    assessment_ids = receipt_v8.get("assessment_ids")
    v8_identity = v8_contract["prepared_identity"]
    if (
        receipt_v8.get("state_slice") != "aligned-rsi-billsum-length-matched-curriculum-v8"
        or receipt_v8.get("model_repo_id") != MODEL_ID
        or receipt_v8.get("model_revision") != MODEL_REVISION
        or receipt_v8.get("dataset_repo_id") != DATASET_ID
        or receipt_v8.get("dataset_revision") != DATASET_REVISION
        or receipt_v8.get("model_files_sha256") != model_files_sha256
        or receipt_v8.get("dataset_files_sha256") != dataset_files_sha256
        or not isinstance(fit_ids, list)
        or not isinstance(assessment_ids, list)
        or len(fit_ids) != expected["v8"]["fit_count"]
        or len(assessment_ids) != expected["v8"]["assessment_count"]
        or len(set(fit_ids)) != len(fit_ids)
        or len(set(assessment_ids)) != len(assessment_ids)
        or receipt_v8.get("fit_roster_sha256") != v8_identity["fit_roster_sha256"]
        or receipt_v8.get("assessment_roster_sha256") != v8_identity["assessment_roster_sha256"]
        or sha256_bytes(canonical_bytes(sorted(fit_ids))) != expected["v8"]["fit_source_ids_sha256"]
        or sha256_bytes(canonical_bytes(sorted(assessment_ids))) != expected["v8"]["assessment_source_ids_sha256"]
        or receipt_v8.get("model_files") is None
        or receipt_v8.get("dataset_files") is None
    ):
        raise ExperimentError("prior V8 prepared-input receipt does not match its frozen roster identity")
    if h._tree_digest(receipt_v8["model_files"]) != model_files_sha256 or h._tree_digest(receipt_v8["dataset_files"]) != dataset_files_sha256:
        raise ExperimentError("prior V8 prepared-input receipt does not bind the V9 input bytes")
    fit_sets["v8"] = set(fit_ids)
    assessment_sets["v8"] = set(assessment_ids)
    summaries["v8"] = {
        "receipt_sha256": receipt_v8["prepared_inputs_sha256"],
        "fit_count": len(fit_ids),
        "assessment_count": len(assessment_ids),
        "fit_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(fit_ids))),
        "assessment_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(assessment_ids))),
    }
    if summaries != expected:
        raise ExperimentError("verified V4-V8 receipt summaries differ from the frozen V9 contract")
    return summaries, fit_sets, assessment_sets


def _eligible_rows(
    tokenizer: Any,
    rows: list[dict[str, str]],
    excluded: set[str],
    duplicate_ids: set[str],
    label: str,
) -> list[dict[str, str]]:
    eligible: list[dict[str, str]] = []
    for row in sorted(rows, key=lambda item: item["doc_id"]):
        if row["doc_id"] in excluded or row["doc_id"] in duplicate_ids:
            continue
        messages = h._messages(row)
        prompt_ids = h._template_token_ids(tokenizer, messages, add_generation_prompt=True)
        if len(prompt_ids) > MAX_SOURCE_TOKENS:
            continue
        full_ids = h._template_token_ids(
            tokenizer,
            [*messages, {"role": "assistant", "content": row["summary"]}],
            add_generation_prompt=False,
        )
        if full_ids[: len(prompt_ids)] != prompt_ids:
            raise ExperimentError(f"assistant prefix changed during V9 {label} eligibility")
        if len(full_ids) < 2 or full_ids[-2:] != [h.ASSISTANT_END_TOKEN_ID, h.TEMPLATE_TRAILER_TOKEN_ID]:
            raise ExperimentError(f"assistant end marker or trailer changed during V9 {label} eligibility")
        target_ids = full_ids[len(prompt_ids) : -1]
        if len(target_ids) > MAX_TARGET_TOKENS:
            continue
        eligible.append(row)
    return eligible


def _build_prepared_payload() -> dict[str, Any]:
    contract = _verify_contract()
    _check_dir(V1_OWNER_ROOT)
    model_files = h.tree_manifest(MODEL_ROOT)
    dataset_files = h.tree_manifest(DATASET_ROOT)
    immutable = contract["immutable_inputs"]
    model_sha = h._tree_digest(model_files)
    dataset_sha = h._tree_digest(dataset_files)
    if model_sha != immutable["model_tree_sha256"] or dataset_sha != immutable["dataset_tree_sha256"]:
        raise ExperimentError("immutable pinned model or BillSum bytes changed")
    if sorted(item["path"] for item in dataset_files) != sorted(["README.md", *h.DATA_FILES]):
        raise ExperimentError("V9 may read only the pinned federal train and test files")
    v1_receipt = _verify_v1_receipt(model_files, dataset_files)
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ExperimentError("Transformers is required for local tokenizer preparation") from exc
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ROOT, local_files_only=True, trust_remote_code=False)
    if (
        h.sha256_bytes(tokenizer.chat_template.encode("utf-8")) != h.CHAT_TEMPLATE_SHA256
        or tokenizer.convert_tokens_to_ids("<|im_end|>") != h.ASSISTANT_END_TOKEN_ID
        or tokenizer("\n", add_special_tokens=False)["input_ids"] != [h.TEMPLATE_TRAILER_TOKEN_ID]
        or tokenizer.pad_token_id != h.PAD_TOKEN_ID
    ):
        raise ExperimentError("local Qwen3 tokenizer differs from the pinned chat-template contract")
    train_rows = h._load_federal_rows("train")
    test_rows = h._load_federal_rows("test")
    train_counts = Counter(row["doc_id"] for row in train_rows)
    test_counts = Counter(row["doc_id"] for row in test_rows)
    duplicate_train = {key for key, count in train_counts.items() if count > 1}
    duplicate_test = {key for key, count in test_counts.items() if count > 1}
    v1_train_ids = {
        row["doc_id"] for row in sorted(train_rows, key=lambda row: row["legacy_v1_doc_id"])[: h.V1_FIT_PREFIX]
    }
    v1_test_ids = {
        row["doc_id"] for row in sorted(test_rows, key=lambda row: row["legacy_v1_doc_id"])[: h.V1_ASSESSMENT_PREFIX]
    }
    v8_contract = h._verify_protocol()
    if (
        len(v1_train_ids) != contract["cohorts"]["v1_excluded"]["fit_count"]
        or len(v1_test_ids) != contract["cohorts"]["v1_excluded"]["assessment_count"]
        or h.sha256_bytes(canonical_bytes(sorted(v1_train_ids)))
        != contract["cohorts"]["v1_excluded"]["fit_source_ids_sha256"]
        or h.sha256_bytes(canonical_bytes(sorted(v1_test_ids)))
        != contract["cohorts"]["v1_excluded"]["assessment_source_ids_sha256"]
        or h.sha256_bytes(canonical_bytes(sorted(v1_train_ids)))
        != v8_contract["prepared_identity"]["v1_excluded"]["fit_source_ids_sha256"]
        or h.sha256_bytes(canonical_bytes(sorted(v1_test_ids)))
        != v8_contract["prepared_identity"]["v1_excluded"]["assessment_source_ids_sha256"]
    ):
        raise ExperimentError("reconstructed V1 exclusions differ from the pinned historical roster")
    prior_summaries, prior_fit, prior_assessment = _load_prior_rosters(model_sha, dataset_sha)
    excluded_train = v1_train_ids | set().union(*prior_fit.values())
    excluded_test = v1_test_ids | set().union(*prior_assessment.values())
    fresh_fit = _eligible_rows(tokenizer, train_rows, excluded_train, duplicate_train, "fit")
    fresh_assessment = _eligible_rows(tokenizer, test_rows, excluded_test, duplicate_test, "assessment")
    fit_rows = fresh_fit[:FIT_COUNT]
    assessment_rows = fresh_assessment[:ASSESSMENT_COUNT]
    if len(fresh_fit) != contract["cohorts"]["eligibility_audit"]["fresh_fit_eligible"]:
        raise ExperimentError("V9 fresh fit eligibility count differs from its read-only audit")
    if len(fresh_assessment) != contract["cohorts"]["eligibility_audit"]["fresh_assessment_eligible"]:
        raise ExperimentError("V9 fresh assessment eligibility count differs from its read-only audit")
    fit_ids = [row["doc_id"] for row in fit_rows]
    assessment_ids = [row["doc_id"] for row in assessment_rows]
    if (
        len(fit_ids) != FIT_COUNT
        or len(assessment_ids) != ASSESSMENT_COUNT
        or set(fit_ids) & set(assessment_ids)
        or set(fit_ids) & excluded_train
        or set(assessment_ids) & excluded_test
        or len(set(fit_ids)) != FIT_COUNT
        or len(set(assessment_ids)) != ASSESSMENT_COUNT
    ):
        raise ExperimentError("V9 fresh cohort size, uniqueness, or split-disjointness gate failed")
    fit_samples = [h._tokenize_row(tokenizer, row) for row in fit_rows]
    assessment_samples = [h._tokenize_row(tokenizer, row) for row in assessment_rows]
    fit_source_tokens = sum(int(row["prompt_token_count"]) for row in fit_samples)
    fit_target_tokens = sum(int(row["target_token_count"]) for row in fit_samples)
    if any(
        int(row["prompt_token_count"]) > MAX_SOURCE_TOKENS or int(row["target_token_count"]) > MAX_TARGET_TOKENS
        for row in (*fit_samples, *assessment_samples)
    ):
        raise ExperimentError("V9 selected row violates the no-truncation tokenizer limits")
    identity = {
        "model_tree_sha256": model_sha,
        "dataset_tree_sha256": dataset_sha,
        "v1_prepared_payload_sha256": v1_receipt["prepared_inputs_sha256"],
        "prior_rosters": prior_summaries,
        "v1_excluded": contract["cohorts"]["v1_excluded"],
        "duplicate_source_groups_excluded": {
            "train_groups": len(duplicate_train),
            "train_rows": sum(train_counts[key] for key in duplicate_train),
            "test_groups": len(duplicate_test),
            "test_rows": sum(test_counts[key] for key in duplicate_test),
        },
        "fresh_eligible": {"fit": len(fresh_fit), "assessment": len(fresh_assessment)},
        "fit_ids": fit_ids,
        "assessment_ids": assessment_ids,
        "fit_roster_sha256": h.sha256_bytes(canonical_bytes(fit_ids)),
        "assessment_roster_sha256": h.sha256_bytes(canonical_bytes(assessment_ids)),
        "fit_source_tokens": fit_source_tokens,
        "fit_assistant_target_tokens": fit_target_tokens,
        "fit_combined_tokens": fit_source_tokens + fit_target_tokens,
    }
    for key, value in (
        ("fit_roster_sha256", contract["cohorts"]["fit_roster_sha256"]),
        ("assessment_roster_sha256", contract["cohorts"]["assessment_roster_sha256"]),
        ("fit_source_tokens", contract["cohorts"]["fit_source_tokens"]),
        ("fit_assistant_target_tokens", contract["cohorts"]["fit_assistant_target_tokens"]),
        ("fit_combined_tokens", contract["cohorts"]["fit_combined_tokens"]),
    ):
        if identity[key] != value:
            raise ExperimentError(f"V9 prepared identity differs from frozen audit: {key}")
    return {
        "schema_version": "aligned-rsi-billsum-same-roster-order-v9-prepared-inputs",
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "governance_slice": GOVERNANCE_SLICE,
        "model_repo_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_files": model_files,
        "model_files_sha256": model_sha,
        "dataset_repo_id": DATASET_ID,
        "dataset_revision": DATASET_REVISION,
        "dataset_files": dataset_files,
        "dataset_files_sha256": dataset_sha,
        "v1_receipt_file_sha256": sha256_file(V1_OWNER_ROOT / "prepared_inputs.json"),
        "v1_receipt_payload_sha256": v1_receipt["prepared_inputs_sha256"],
        "chat_template_sha256": h.CHAT_TEMPLATE_SHA256,
        "runtime": contract["runtime"],
        "source_digests": _source_manifest(),
        **identity,
        "fit_samples": fit_samples,
        "assessment_samples": assessment_samples,
    }


def audit() -> dict[str, Any]:
    """Read-only tokenizer/cohort feasibility audit before the one-shot run."""
    contract = _verify_contract()
    prepared = _build_prepared_payload()
    try:
        import torch
    except ImportError as exc:
        raise ExperimentError("PyTorch is required for the local MPS target") from exc
    mps_available = bool(torch.backends.mps.is_available())
    if not mps_available:
        raise ExperimentError("the frozen V9 execution requires local Apple MPS")
    if RELEASE_ROOT.exists() or (OWNER_ROOT.exists() and PREPARED_PATH.exists()):
        raise ExperimentError("V9 release or prepared receipt already exists; refusing identity reuse")
    return {
        "read_only_audit": True,
        "state_slice": STATE_SLICE,
        "governance_slice": GOVERNANCE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_tree_sha256": prepared["model_files_sha256"],
        "dataset_tree_sha256": prepared["dataset_files_sha256"],
        "fresh_fit_eligible": prepared["fresh_eligible"]["fit"],
        "fresh_assessment_eligible": prepared["fresh_eligible"]["assessment"],
        "fit_documents": len(prepared["fit_ids"]),
        "assessment_documents": len(prepared["assessment_ids"]),
        "fit_roster_sha256": prepared["fit_roster_sha256"],
        "assessment_roster_sha256": prepared["assessment_roster_sha256"],
        "fit_source_tokens": prepared["fit_source_tokens"],
        "fit_assistant_target_tokens": prepared["fit_assistant_target_tokens"],
        "fit_combined_tokens": prepared["fit_combined_tokens"],
        "duplicate_source_groups_excluded": prepared["duplicate_source_groups_excluded"],
        "local_mps_available": mps_available,
        "runtime": contract["runtime"],
        "independent_acceptance": False,
    }


def prepare() -> dict[str, Any]:
    """Freeze V9 source, runtime, raw inputs, and prepared private cohorts."""
    _verify_contract()
    _check_dir(OWNER_ROOT, create=True)
    if PREPARED_PATH.exists() or RELEASE_ROOT.exists():
        raise ExperimentError("V9 preparation is one-shot; prepared input or release already exists")
    RUNS_ROOT.mkdir(parents=True, mode=0o700, exist_ok=False)
    RUNS_ROOT.chmod(0o700)
    payload = _build_prepared_payload()
    payload["prepared_inputs_sha256"] = sha256_bytes(canonical_bytes(payload))
    save_json(PREPARED_PATH, payload)
    _check_private_tree(OWNER_ROOT)
    return {
        "prepared": True,
        "state_slice": STATE_SLICE,
        "governance_slice": GOVERNANCE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "fit_documents": len(payload["fit_ids"]),
        "assessment_documents": len(payload["assessment_ids"]),
        "fit_roster_sha256": payload["fit_roster_sha256"],
        "assessment_roster_sha256": payload["assessment_roster_sha256"],
        "prepared_inputs_sha256": payload["prepared_inputs_sha256"],
        "independent_acceptance": False,
    }


def _validate_prepared() -> dict[str, Any]:
    _check_dir(OWNER_ROOT)
    if PREPARED_PATH.is_symlink() or not PREPARED_PATH.is_file() or PREPARED_PATH.stat().st_mode & 0o777 != 0o600:
        raise ExperimentError("V9 prepared-input receipt is not an owner-only regular file")
    stored = load_json(PREPARED_PATH)
    digest = stored.get("prepared_inputs_sha256")
    unsigned = {key: value for key, value in stored.items() if key != "prepared_inputs_sha256"}
    if digest != sha256_bytes(canonical_bytes(unsigned)):
        raise ExperimentError("V9 prepared-input receipt digest mismatch")
    current = _build_prepared_payload()
    if canonical_bytes(current) != canonical_bytes(unsigned):
        raise ExperimentError("V9 source, input, prior receipt, or cohort identity changed after freeze")
    _check_private_tree(OWNER_ROOT)
    return stored


def _make_orders(
    fit_samples: Sequence[Mapping[str, Any]],
    base_nll_by_id: Mapping[str, float],
    seed: int,
) -> dict[str, list[Mapping[str, Any]]]:
    by_id = {str(row["doc_id"]): row for row in fit_samples}
    if len(by_id) != FIT_COUNT or set(base_nll_by_id) != set(by_id):
        raise ExperimentError("V9 order input does not bind the complete exact fit roster")
    if any(not math.isfinite(float(value)) for value in base_nll_by_id.values()):
        raise ExperimentError("V9 base-NLL curriculum contains a non-finite score")
    easy = sorted(by_id, key=lambda identifier: (float(base_nll_by_id[identifier]), identifier))
    shuffled = list(by_id)
    random.Random(seed ^ ORDER_SEED_XOR).shuffle(shuffled)
    orders = {
        PRIMARY_ARM: [by_id[identifier] for identifier in easy],
        CONTROL_ARM: [by_id[identifier] for identifier in shuffled],
    }
    if set(easy) != set(shuffled) or len(easy) != FIT_COUNT or len(shuffled) != FIT_COUNT:
        raise ExperimentError("V9 order arms do not contain the same 128 source IDs")
    source_totals = {
        arm: sum(int(row["prompt_token_count"]) for row in rows) for arm, rows in orders.items()
    }
    target_totals = {
        arm: sum(int(row["target_token_count"]) for row in rows) for arm, rows in orders.items()
    }
    if len(set(source_totals.values())) != 1 or len(set(target_totals.values())) != 1:
        raise ExperimentError("V9 arms do not have identical source and assistant-target token totals")
    return orders


def _adapter_initialization_digest(model: Any) -> str:
    digest = hashlib.sha256()
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            value = parameter.detach().to(device="cpu").contiguous()
            digest.update(name.encode("utf-8") + b"\0")
            digest.update(str(value.dtype).encode("ascii") + b"\0")
            digest.update(canonical_bytes(list(value.shape)))
            digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def _train_in_order(
    model: Any,
    lora_layers: Sequence[Any],
    samples: Sequence[Mapping[str, Any]],
    seed: int,
    *,
    deadline: float,
    arm_name: str,
) -> tuple[list[float], str]:
    import torch

    if len(samples) != FIT_COUNT or len(samples) % TRAINING_BATCH_SIZE:
        raise ExperimentError("V9 training order must contain 128 rows and 32 full update groups")
    parameters = h._reset_adapter(model, lora_layers, seed)
    initialization_sha = _adapter_initialization_digest(model)
    optimizer = torch.optim.AdamW(
        parameters,
        lr=1e-4,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.01,
    )
    device = torch.device("mps")
    base = model.get_base_model()
    model.train()
    model.config.use_cache = False
    base.config.use_cache = False
    base.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    losses: list[float] = []
    for step, offset in enumerate(range(0, FIT_COUNT, TRAINING_BATCH_SIZE), start=1):
        if time.monotonic() > deadline:
            raise ExperimentError("480-minute wall-clock limit reached during V9 adapter training")
        group = samples[offset : offset + TRAINING_BATCH_SIZE]
        token_count = sum(len(row["target_ids"]) for row in group)
        if token_count < 1:
            raise ExperimentError("V9 optimizer group contains no assistant-target tokens")
        optimizer.zero_grad(set_to_none=True)
        loss_sum_float = 0.0
        for sample in group:
            loss_sum, target_count = h._assistant_target_loss_sum(model, sample, device)
            if target_count != len(sample["target_ids"]) or not bool(torch.isfinite(loss_sum).item()):
                raise ExperimentError("V9 assistant-only loss is non-finite or token-count inconsistent")
            (loss_sum / token_count).backward()
            loss_sum_float += float(loss_sum.detach().cpu())
            del loss_sum
        if time.monotonic() > deadline:
            raise ExperimentError("480-minute wall-clock limit reached during V9 gradient accumulation")
        torch.nn.utils.clip_grad_norm_(parameters, max_norm=1.0)
        optimizer.step()
        if time.monotonic() > deadline:
            raise ExperimentError("480-minute wall-clock limit reached during V9 optimizer step")
        losses.append(loss_sum_float / token_count)
        torch.mps.synchronize()
        torch.mps.empty_cache()
        print(
            f"phase=training arm={arm_name} seed={seed} completed_steps={step}/{OPTIMIZER_STEPS}",
            flush=True,
        )
    model.eval()
    base.gradient_checkpointing_disable()
    return losses, initialization_sha


def _write_status(run_root: Path, run_id: str, status: str, phase: str, error: str | None = None) -> None:
    value: dict[str, Any] = {
        "schema_version": "aligned-rsi-billsum-same-roster-order-v9-execution-status",
        "state_slice": STATE_SLICE,
        "governance_slice": GOVERNANCE_SLICE,
        "run_id": run_id,
        "status": status,
        "phase": phase,
        "updated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if error:
        value["error"] = error
    save_json(run_root / "execution_status.json", value)


def _offline_environment() -> None:
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
        }
    )


def run() -> dict[str, Any]:
    """Execute the single offline V9 local MPS run; any attempt is terminal."""
    manifest = _verify_contract()
    prepared = _validate_prepared()
    if RELEASE_ROOT.exists() or any(RUNS_ROOT.iterdir()):
        raise ExperimentError("V9 is one-shot and already has a run or release artifact")
    _offline_environment()
    torch, _ = h._import_torch()
    started = time.monotonic()
    deadline = started + WALL_CLOCK_LIMIT_SECONDS
    run_id = dt.datetime.now(dt.timezone.utc).strftime("run-%Y%m%dT%H%M%S%fZ")
    run_root = RUNS_ROOT / run_id
    run_root.mkdir(parents=True, mode=0o700, exist_ok=False)
    run_root.chmod(0o700)
    _write_status(run_root, run_id, "RUNNING", "source_and_roster_validation")
    try:
        source_digests = _source_manifest()
        fit_pool = prepared["fit_samples"]
        assessment = prepared["assessment_samples"]
        if len(fit_pool) != FIT_COUNT or len(assessment) != ASSESSMENT_COUNT:
            raise ExperimentError("V9 prepared input has an incomplete training or assessment roster")
        model, tokenizer, lora_layers, device_name = h._create_model_and_tokenizer(MODEL_ROOT)
        device = torch.device("mps")
        _write_status(run_root, run_id, "RUNNING", "untouched_base_fit_scoring")
        fit_nll_by_id: dict[str, float] = {}
        with model.disable_adapter():
            for index, sample in enumerate(fit_pool, start=1):
                if time.monotonic() > deadline:
                    raise ExperimentError("480-minute wall-clock limit reached during V9 fit scoring")
                fit_nll_by_id[sample["doc_id"]], _ = h._target_nll(model, sample, device=device)
                if not math.isfinite(fit_nll_by_id[sample["doc_id"]]):
                    raise ExperimentError("non-finite untouched-base fit score in V9")
                if index % 32 == 0:
                    print(f"phase=fit_loss completed={index}/{FIT_COUNT}", flush=True)
        order_rosters = {seed: _make_orders(fit_pool, fit_nll_by_id, seed) for seed in SEEDS}
        arms: dict[str, list[dict[str, Any]]] = {name: [] for name in ALL_ARMS}
        diagnostics: list[dict[str, Any]] = []
        for seed in SEEDS:
            if time.monotonic() > deadline:
                raise ExperimentError("480-minute wall-clock limit reached before V9 base assessment")
            _write_status(run_root, run_id, "RUNNING", f"untouched_base_assessment_seed_{seed}")
            with model.disable_adapter():
                evaluation = h._evaluate_arm(model, tokenizer, assessment, device, seed=seed, deadline=deadline)
            arms["untouched_base"].append(
                {
                    "seed": seed,
                    "selection_ids": [],
                    "training_order_ids": [],
                    "adapter_sha256": None,
                    "adapter_files": [],
                    "initialization_sha256": None,
                    "train_steps": 0,
                    "train_loss_mean": None,
                    "training_source_tokens": 0,
                    "training_target_tokens": 0,
                    **evaluation,
                }
            )
        for seed in SEEDS:
            for arm_name in TRAINED_ARMS:
                if time.monotonic() > deadline:
                    raise ExperimentError("480-minute wall-clock limit reached before V9 arm training")
                ordered = list(order_rosters[seed][arm_name])
                _write_status(run_root, run_id, "RUNNING", f"train_{arm_name}_seed_{seed}")
                print(f"phase=training arm={arm_name} seed={seed} rows={len(ordered)}", flush=True)
                losses, init_sha = _train_in_order(
                    model,
                    lora_layers,
                    ordered,
                    seed,
                    deadline=deadline,
                    arm_name=arm_name,
                )
                adapter = h._save_adapter(model, run_root / "adapters" / f"{arm_name}-seed-{seed}")
                _write_status(run_root, run_id, "RUNNING", f"assessment_{arm_name}_seed_{seed}")
                evaluation = h._evaluate_arm(model, tokenizer, assessment, device, seed=seed, deadline=deadline)
                arms[arm_name].append(
                    {
                        "seed": seed,
                        "selection_ids": sorted(row["doc_id"] for row in ordered),
                        "training_order_ids": [row["doc_id"] for row in ordered],
                        "adapter_sha256": adapter["sha256"],
                        "adapter_files": adapter["files"],
                        "initialization_sha256": init_sha,
                        "train_steps": len(losses),
                        "train_loss_mean": h._mean(losses),
                        "training_source_tokens": sum(int(row["prompt_token_count"]) for row in ordered),
                        "training_target_tokens": sum(int(row["target_token_count"]) for row in ordered),
                        **evaluation,
                    }
                )
                for sample in assessment[:MECHANISTIC_ROWS]:
                    if time.monotonic() > deadline:
                        raise ExperimentError("480-minute wall-clock limit reached during V9 residual intervention")
                    diagnostic = h._mechanistic_row(model, sample, device)
                    diagnostic.update({"arm": arm_name, "seed": seed})
                    diagnostics.append(diagnostic)
        if h.tree_manifest(MODEL_ROOT) != prepared["model_files"]:
            raise ExperimentError("immutable Qwen3 model bytes changed during the V9 run")
        elapsed = time.monotonic() - started
        usage = resource.getrusage(resource.RUSAGE_SELF)
        resources = {
            "elapsed_seconds": elapsed,
            "wall_clock_limit_seconds": WALL_CLOCK_LIMIT_SECONDS,
            "peak_process_rss_bytes": int(usage.ru_maxrss),
            "mps_current_allocated_bytes": int(torch.mps.current_allocated_memory()),
            "mps_driver_allocated_bytes": int(torch.mps.driver_allocated_memory()),
            "energy_measurement": "not_measured",
            "local_compute_cost": "not_measured",
            "provider_calls": 0,
            "provider_spend": "none",
        }
        private = {
            "schema_version": "aligned-rsi-billsum-same-roster-order-v9-private-run",
            "protocol_id": PROTOCOL_ID,
            "state_slice": STATE_SLICE,
            "governance_slice": GOVERNANCE_SLICE,
            "run_id": run_id,
            "protocol_sha256": sha256_file(PROTOCOL_PATH),
            "manifest_sha256": sha256_file(MANIFEST_PATH),
            "protocol_snapshot": manifest,
            "runner_sha256": sha256_file(Path(__file__).resolve()),
            "focused_tests_sha256": sha256_file(TEST_PATH),
            "source_revision": subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
            ).stdout.strip(),
            "source_worktree_dirty": bool(
                subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.strip()
            ),
            "source_digests": source_digests,
            "prepared_inputs_sha256": prepared["prepared_inputs_sha256"],
            "model_weights_manifest_sha256": prepared["model_files_sha256"],
            "base_checkpoint_unchanged": True,
            "device": device_name,
            "runtime": manifest["runtime"],
            "fit_ids": prepared["fit_ids"],
            "assessment_ids": prepared["assessment_ids"],
            "fit_nll_by_id": fit_nll_by_id,
            "arms": arms,
            "mechanistic": diagnostics,
            "reference_token_counts": {
                row["doc_id"]: int(row["reference_token_count"]) for row in assessment
            },
            "resources": resources,
        }
        private_path = run_root / "private_run.json"
        save_json(private_path, private)
        references = {row["doc_id"]: row["summary"] for row in assessment}
        report = _report_from_private(private, references, private_run_sha256=sha256_file(private_path), prepared=prepared)
        RELEASE_ROOT.mkdir(parents=True, exist_ok=False)
        save_json(PUBLIC_REPORT_PATH, report, private=False)
        save_json(
            RELEASE_ROOT / "release_manifest.json",
            {
                "schema_version": "aligned-rsi-billsum-same-roster-order-v9-aggregate-release",
                "state_slice": STATE_SLICE,
                "governance_slice": GOVERNANCE_SLICE,
                "files": [{"path": "evaluation_report.json", "sha256": sha256_file(PUBLIC_REPORT_PATH)}],
                "raw_data_included": False,
                "model_weights_included": False,
                "generated_summaries_included": False,
                "adapter_weights_included": False,
                "independent_acceptance": False,
            },
            private=False,
        )
        _write_status(run_root, run_id, "COMPLETE", "pending_local_report_reconstruction")
        _check_private_tree(OWNER_ROOT)
        return report
    except Exception as exc:
        _write_status(run_root, run_id, "FAILED", "local_execution_failed", error=f"{type(exc).__name__}: {exc}")
        raise


def _mean(values: Sequence[float]) -> float:
    if not values or any(not math.isfinite(float(value)) for value in values):
        raise ExperimentError("aggregate metric input is empty or non-finite")
    return sum(float(value) for value in values) / len(values)


def _bootstrap_interval(values: Sequence[float]) -> tuple[float, float]:
    if not values or any(not math.isfinite(float(value)) for value in values):
        raise ExperimentError("paired-document bootstrap input is empty or non-finite")
    rng = random.Random(BOOTSTRAP_SEED)
    samples = sorted(
        sum(float(values[rng.randrange(len(values))]) for _ in values) / len(values)
        for _ in range(BOOTSTRAP_RESAMPLES)
    )
    return samples[int(0.025 * len(samples))], samples[min(len(samples) - 1, int(0.975 * len(samples)))]


def _candidate_gates(
    *,
    effect_mean: float,
    ci_low: float,
    selected_rouge_l: float,
    base_rouge_l: float,
    selected_nll: float,
    base_nll: float,
    outputs_finite_and_complete: bool,
    identity_patch_max_error: float,
) -> dict[str, bool]:
    values = (
        effect_mean,
        ci_low,
        selected_rouge_l,
        base_rouge_l,
        selected_nll,
        base_nll,
        identity_patch_max_error,
    )
    if any(not math.isfinite(float(value)) for value in values):
        raise ExperimentError("candidate gate input is non-finite")
    return {
        "mean_effect_at_least_0_02": effect_mean >= MIN_EFFECT,
        "bootstrap_95_percent_lower_bound_positive": ci_low > 0,
        "easy_to_hard_not_below_untouched_base": selected_rouge_l >= base_rouge_l,
        "easy_to_hard_target_nll_at_most_0_05_above_base": selected_nll - base_nll <= 0.05,
        "all_outputs_finite_and_complete": outputs_finite_and_complete,
        "identity_patch_error_within_1e_5": identity_patch_max_error <= IDENTITY_PATCH_TOLERANCE,
    }


def _report_from_private(
    private: Mapping[str, Any],
    references: Mapping[str, str],
    *,
    private_run_sha256: str,
    prepared: Mapping[str, Any],
) -> dict[str, Any]:
    assessment_ids = private["assessment_ids"]
    arms = private["arms"]
    if assessment_ids != prepared["assessment_ids"] or set(references) != set(assessment_ids):
        raise ExperimentError("V9 private and prepared assessment rosters differ")
    for name in ALL_ARMS:
        repeats = arms.get(name)
        if not isinstance(repeats, list) or [row.get("seed") for row in repeats] != list(SEEDS):
            raise ExperimentError(f"V9 assessment repeats are incomplete for {name}")
        for repeat in repeats:
            for field in ("generation", "generation_seed", "generation_tokens", "nll"):
                if set(repeat.get(field, {})) != set(assessment_ids):
                    raise ExperimentError(f"V9 {field} cells are incomplete for {name}")
            if any(not isinstance(text, str) or not text.strip() for text in repeat["generation"].values()):
                raise ExperimentError(f"V9 empty generated summary in {name}")
            if any(not math.isfinite(float(value)) for value in repeat["nll"].values()):
                raise ExperimentError(f"V9 non-finite assessment NLL in {name}")
            if any(not isinstance(value, int) or value < 1 for value in repeat["generation_tokens"].values()):
                raise ExperimentError(f"V9 invalid generation token count in {name}")
            if name != "untouched_base" and not math.isfinite(float(repeat.get("train_loss_mean", float("nan")))):
                raise ExperimentError(f"V9 non-finite training loss in {name}")
    score_by_arm: dict[str, dict[int, dict[str, dict[str, float]]]] = {}
    for name in ALL_ARMS:
        score_by_arm[name] = {}
        for repeat in arms[name]:
            score_by_arm[name][int(repeat["seed"])] = h._rouge_rows(repeat["generation"], references)
    rouge_means: dict[str, dict[str, float]] = {m: {} for m in ("rouge1", "rouge2", "rougeL")}
    for metric in rouge_means:
        for name in ALL_ARMS:
            values = [score_by_arm[name][seed][doc_id][metric] for seed in SEEDS for doc_id in assessment_ids]
            rouge_means[metric][name] = _mean(values)
    per_document_effect = [
        _mean([score_by_arm[PRIMARY_ARM][seed][doc_id]["rougeL"] for seed in SEEDS])
        - _mean([score_by_arm[CONTROL_ARM][seed][doc_id]["rougeL"] for seed in SEEDS])
        for doc_id in assessment_ids
    ]
    effect_mean = _mean(per_document_effect)
    ci_low, ci_high = _bootstrap_interval(per_document_effect)
    nll_means = {
        name: _mean([float(repeat["nll"][doc_id]) for repeat in arms[name] for doc_id in assessment_ids])
        for name in ALL_ARMS
    }
    token_ratio = {
        name: _mean(
            [
                float(repeat["generation_tokens"][doc_id]) / max(1, int(private["reference_token_counts"][doc_id]))
                for repeat in arms[name]
                for doc_id in assessment_ids
            ]
        )
        for name in ALL_ARMS
    }
    diagnostic_rows = private.get("mechanistic", [])
    expected_diagnostic = {
        (arm, seed, doc_id)
        for arm in TRAINED_ARMS
        for seed in SEEDS
        for doc_id in assessment_ids[:MECHANISTIC_ROWS]
    }
    observed_diagnostic = {
        (row.get("arm"), row.get("seed"), row.get("doc_id")) for row in diagnostic_rows
    }
    if observed_diagnostic != expected_diagnostic or len(diagnostic_rows) != len(expected_diagnostic):
        raise ExperimentError("V9 layer diagnostic coverage differs from the frozen 128-row design")
    identity_error = max(float(row["identity_patch_abs_error"]) for row in diagnostic_rows)
    gates = _candidate_gates(
        effect_mean=effect_mean,
        ci_low=ci_low,
        selected_rouge_l=rouge_means["rougeL"][PRIMARY_ARM],
        base_rouge_l=rouge_means["rougeL"]["untouched_base"],
        selected_nll=nll_means[PRIMARY_ARM],
        base_nll=nll_means["untouched_base"],
        outputs_finite_and_complete=True,
        identity_patch_max_error=identity_error,
    )
    disposition = "Candidate" if all(gates.values()) else "NoCandidate"
    source_digests = private["source_digests"]
    return {
        "schema_version": "aligned-rsi-billsum-same-roster-order-v9-evaluation-report",
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "governance_slice": GOVERNANCE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "run_id": private["run_id"],
        "source_revision": private["source_revision"],
        "source_worktree_dirty": private["source_worktree_dirty"],
        "assurance_level": "PENDING_LOCAL_VERIFICATION",
        "local_acceptance": "PENDING_LOCAL_VERIFICATION",
        "reviewer_status": "LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT",
        "independent_acceptance": False,
        "reproducibility_status": "SINGLE_LOCAL_EXECUTION",
        "candidate_disposition": disposition,
        "candidate_gates": gates,
        "primary_metric": {
            "name": "paired_document_bootstrap_rougeL_easy_to_hard_minus_random_order",
            "n_documents": len(assessment_ids),
            "n_seed_pairs": len(SEEDS),
            "mean_effect": effect_mean,
            "ci95_low": ci_low,
            "ci95_high": ci_high,
            "minimum_meaningful_effect": MIN_EFFECT,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "mean_rouge_f1": rouge_means,
        "mean_assistant_target_nll": nll_means,
        "mean_output_reference_token_ratio": token_ratio,
        "per_seed_rougeL_f1": {
            name: {
                str(seed): _mean([score_by_arm[name][seed][doc_id]["rougeL"] for doc_id in assessment_ids])
                for seed in SEEDS
            }
            for name in ALL_ARMS
        },
        "training": {
            "fit_documents": FIT_COUNT,
            "steps_per_arm_seed": OPTIMIZER_STEPS,
            "total_optimizer_steps": len(SEEDS) * len(TRAINED_ARMS) * OPTIMIZER_STEPS,
            "fit_roster_sha256": prepared["fit_roster_sha256"],
            "fit_source_tokens_per_arm_seed": prepared["fit_source_tokens"],
            "fit_assistant_target_tokens_per_arm_seed": prepared["fit_assistant_target_tokens"],
            "fit_combined_tokens_per_arm_seed": prepared["fit_combined_tokens"],
            "same_source_ids_and_token_sequences_across_arms": True,
            "paired_initialization_per_seed": True,
        },
        "assessment": {
            "documents": ASSESSMENT_COUNT,
            "arms": list(ALL_ARMS),
            "repeats_per_arm": len(SEEDS),
            "held_out_completions": len(ALL_ARMS) * len(SEEDS) * ASSESSMENT_COUNT,
            "assessment_roster_sha256": prepared["assessment_roster_sha256"],
        },
        "layer_activation_patch_diagnostic": {
            "kind": "layer_14_residual_activation_patch_secondary_only",
            "rows": len(diagnostic_rows),
            "identity_patch_max_abs_nll_error": identity_error,
            "mean_activation_patch_delta_nll": _mean(
                [float(row["activation_patch_delta_nll"]) for row in diagnostic_rows]
            ),
            "feature_level_mechanism_claim": False,
        },
        "resources": private["resources"],
        "custody": {
            "raw_inputs_and_private_run_owner_only": True,
            "repository_release_aggregate_only": True,
            "model_weights_in_release": False,
            "adapter_weights_in_release": False,
            "generated_summaries_in_release": False,
            "data_and_artifact_custody": "pinned source bytes plus owner-only 0700 local V9 root; private files 0600",
        },
        "source_digests": source_digests,
        "source_manifest_sha256": sha256_bytes(canonical_bytes(source_digests)),
        "model_weights_manifest_sha256": prepared["model_files_sha256"],
        "dataset_manifest_sha256": prepared["dataset_files_sha256"],
        "prepared_inputs_sha256": prepared["prepared_inputs_sha256"],
        "private_run_sha256": private_run_sha256,
        "assurance": {
            "reviewer_status": "LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT",
            "reproducibility_status": "SINGLE_LOCAL_EXECUTION",
            "next_blocked_authority_gate": "independent acceptance or any claim above the local qualification ceiling requires a fresh packet and applicable authority",
        },
        "nonclaims": [
            "independent acceptance",
            "general alignment",
            "general recursive self-improvement",
            "feature-level mechanism",
            "benchmark leaderboard result",
            "production readiness",
            "user-data evidence",
            "clean second-environment reproduction",
        ],
    }


def _validate_private_run(
    run_root: Path,
    run_id: str,
    private: dict[str, Any],
    prepared: dict[str, Any],
) -> None:
    if (
        private.get("protocol_id") != PROTOCOL_ID
        or private.get("state_slice") != STATE_SLICE
        or private.get("governance_slice") != GOVERNANCE_SLICE
        or private.get("run_id") != run_id
        or private.get("prepared_inputs_sha256") != prepared["prepared_inputs_sha256"]
        or private.get("protocol_sha256") != sha256_file(PROTOCOL_PATH)
        or private.get("manifest_sha256") != sha256_file(MANIFEST_PATH)
        or private.get("runner_sha256") != sha256_file(Path(__file__).resolve())
        or private.get("focused_tests_sha256") != sha256_file(TEST_PATH)
        or private.get("source_digests") != _source_manifest()
        or private.get("model_weights_manifest_sha256") != prepared["model_files_sha256"]
        or private.get("base_checkpoint_unchanged") is not True
    ):
        raise ExperimentError("V9 private run does not bind the frozen source, inputs, and execution")
    if h.tree_manifest(MODEL_ROOT) != prepared["model_files"]:
        raise ExperimentError("pinned model bytes changed after V9 execution")
    fit_ids = prepared["fit_ids"]
    assessment_ids = prepared["assessment_ids"]
    if private.get("fit_ids") != fit_ids or private.get("assessment_ids") != assessment_ids:
        raise ExperimentError("V9 private run roster differs from the prepared-input receipt")
    fit_nll = private.get("fit_nll_by_id", {})
    if set(fit_nll) != set(fit_ids) or any(not math.isfinite(float(value)) for value in fit_nll.values()):
        raise ExperimentError("V9 untouched-base fit NLL roster is missing or non-finite")
    for seed in SEEDS:
        expected = _make_orders(prepared["fit_samples"], fit_nll, seed)
        initializations: list[str] = []
        for arm_name in TRAINED_ARMS:
            repeats = private["arms"].get(arm_name)
            if not isinstance(repeats, list) or len(repeats) != len(SEEDS):
                raise ExperimentError(f"V9 arm repeats are incomplete: {arm_name}")
            repeat = next((item for item in repeats if item.get("seed") == seed), None)
            if repeat is None:
                raise ExperimentError(f"V9 arm seed is missing: {arm_name} seed {seed}")
            ordered_ids = [row["doc_id"] for row in expected[arm_name]]
            if (
                repeat.get("selection_ids") != sorted(fit_ids)
                or repeat.get("training_order_ids") != ordered_ids
                or repeat.get("train_steps") != OPTIMIZER_STEPS
                or repeat.get("training_source_tokens") != prepared["fit_source_tokens"]
                or repeat.get("training_target_tokens") != prepared["fit_assistant_target_tokens"]
                or not math.isfinite(float(repeat.get("train_loss_mean", float("nan"))))
            ):
                raise ExperimentError(f"V9 exact same-roster or training budget check failed: {arm_name} seed {seed}")
            initializations.append(str(repeat.get("initialization_sha256")))
            adapter_dir = run_root / "adapters" / f"{arm_name}-seed-{seed}"
            files = h._adapter_manifest(adapter_dir)
            if files != repeat.get("adapter_files") or h._tree_digest(files) != repeat.get("adapter_sha256"):
                raise ExperimentError(f"V9 adapter manifest differs: {arm_name} seed {seed}")
        if len(set(initializations)) != 1:
            raise ExperimentError(f"V9 paired LoRA initialization differs for seed {seed}")
    for arm_name in ALL_ARMS:
        repeats = private["arms"].get(arm_name)
        if not isinstance(repeats, list) or [item.get("seed") for item in repeats] != list(SEEDS):
            raise ExperimentError(f"V9 seed roster differs for arm {arm_name}")
        for repeat in repeats:
            for field in ("generation", "nll", "generation_seed", "generation_tokens"):
                if set(repeat.get(field, {})) != set(assessment_ids):
                    raise ExperimentError(f"V9 {field} cells are incomplete for {arm_name}")
            expected_seeds = {doc_id: h._generation_seed(int(repeat["seed"]), doc_id) for doc_id in assessment_ids}
            if repeat["generation_seed"] != expected_seeds:
                raise ExperimentError(f"V9 per-document generation seeds are not paired for {arm_name}")
    base_repeats = private["arms"]["untouched_base"]
    if any(
        row.get("selection_ids") != []
        or row.get("training_order_ids") != []
        or row.get("train_steps") != 0
        or row.get("adapter_sha256") is not None
        for row in base_repeats
    ):
        raise ExperimentError("V9 untouched-base arm contains training or adapter artifacts")
    expected_diagnostic = {
        (arm, seed, doc_id)
        for arm in TRAINED_ARMS
        for seed in SEEDS
        for doc_id in assessment_ids[:MECHANISTIC_ROWS]
    }
    observed = {
        (row.get("arm"), row.get("seed"), row.get("doc_id")) for row in private.get("mechanistic", [])
    }
    if observed != expected_diagnostic or len(private.get("mechanistic", [])) != len(expected_diagnostic):
        raise ExperimentError("V9 residual-patch diagnostic roster is incomplete")
    if any(not math.isfinite(float(row.get("identity_patch_abs_error", float("nan")))) for row in private["mechanistic"]):
        raise ExperimentError("V9 identity patch contains a non-finite result")


def verify() -> dict[str, Any]:
    """Reconstruct the aggregate report and issue local-only INTERNAL_PASS."""
    _verify_contract()
    prepared = _validate_prepared()
    report = load_json(PUBLIC_REPORT_PATH)
    if report.get("state_slice") != STATE_SLICE or report.get("claim_ceiling") != CLAIM_CEILING:
        raise ExperimentError("V9 public report identity mismatch")
    run_id = report.get("run_id")
    if not isinstance(run_id, str) or not run_id.startswith("run-"):
        raise ExperimentError("V9 report run identifier is invalid")
    run_root = RUNS_ROOT / run_id
    _check_private_tree(OWNER_ROOT)
    status = load_json(run_root / "execution_status.json")
    if status.get("status") not in {"COMPLETE", "LOCAL_ACCEPTED"}:
        raise ExperimentError("V9 execution did not reach complete local execution")
    private_path = run_root / "private_run.json"
    private_sha = sha256_file(private_path)
    private = load_json(private_path)
    _validate_private_run(run_root, run_id, private, prepared)
    assessment = prepared["assessment_samples"]
    references = {row["doc_id"]: row["summary"] for row in assessment}
    reconstructed = _report_from_private(private, references, private_run_sha256=private_sha, prepared=prepared)
    normalized = dict(report)
    normalized["assurance_level"] = "PENDING_LOCAL_VERIFICATION"
    normalized["local_acceptance"] = "PENDING_LOCAL_VERIFICATION"
    normalized.pop("local_acceptance_receipt_sha256", None)
    if canonical_bytes(reconstructed) != canonical_bytes(normalized):
        raise ExperimentError("V9 aggregate report does not reconstruct from private evidence and pinned references")
    if report.get("reviewer_status") != "LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT" or report.get("independent_acceptance") is not False:
        raise ExperimentError("V9 report exceeds the local-only authority boundary")
    release_manifest_path = RELEASE_ROOT / "release_manifest.json"
    release = load_json(release_manifest_path)
    if release.get("state_slice") != STATE_SLICE or release.get("governance_slice") != GOVERNANCE_SLICE:
        raise ExperimentError("V9 release manifest state slice mismatch")
    expected_paths = {"evaluation_report.json", "release_manifest.json"}
    if {item.name for item in RELEASE_ROOT.iterdir()} not in (expected_paths, expected_paths | {"local_acceptance.json"}):
        raise ExperimentError("V9 aggregate release contains an unapproved file")
    files = release.get("files")
    if not isinstance(files, list) or {item.get("path") for item in files} not in (
        {"evaluation_report.json"}, {"evaluation_report.json", "local_acceptance.json"}
    ):
        raise ExperimentError("V9 release manifest file list is invalid")
    for item in files:
        path = RELEASE_ROOT / item["path"]
        if not path.is_file() or sha256_file(path) != item.get("sha256"):
            raise ExperimentError("V9 aggregate release file digest mismatch")
    for flag in ("raw_data_included", "model_weights_included", "generated_summaries_included", "adapter_weights_included", "independent_acceptance"):
        if release.get(flag) is not False:
            raise ExperimentError(f"V9 release manifest violates aggregate-only rule: {flag}")
    acceptance = {
        "schema_version": "aligned-rsi-billsum-same-roster-order-v9-local-acceptance",
        "state_slice": STATE_SLICE,
        "governance_slice": GOVERNANCE_SLICE,
        "assurance_level": "INTERNAL_PASS",
        "reviewer_status": "LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT",
        "local_acceptance": "INTERNAL_PASS",
        "independent_acceptance": False,
        "claim_ceiling": CLAIM_CEILING,
        "candidate_disposition": reconstructed["candidate_disposition"],
        "accepted_report_core_sha256": sha256_bytes(canonical_bytes(reconstructed)),
        "private_run_sha256": private_sha,
        "prepared_inputs_sha256": prepared["prepared_inputs_sha256"],
        "source_manifest_sha256": reconstructed["source_manifest_sha256"],
        "source_digests": reconstructed["source_digests"],
    }
    acceptance_path = RELEASE_ROOT / "local_acceptance.json"
    if acceptance_path.exists() and sha256_file(acceptance_path) != report.get("local_acceptance_receipt_sha256"):
        raise ExperimentError("existing V9 local acceptance receipt digest differs")
    save_json(acceptance_path, acceptance, private=False)
    report["assurance_level"] = "INTERNAL_PASS"
    report["local_acceptance"] = "INTERNAL_PASS"
    report["local_acceptance_receipt_sha256"] = sha256_file(acceptance_path)
    save_json(PUBLIC_REPORT_PATH, report, private=False)
    release["files"] = [
        {"path": "evaluation_report.json", "sha256": sha256_file(PUBLIC_REPORT_PATH)},
        {"path": "local_acceptance.json", "sha256": sha256_file(acceptance_path)},
    ]
    save_json(release_manifest_path, release, private=False)
    _write_status(run_root, run_id, "LOCAL_ACCEPTED", "local_report_reconstruction_passed")
    _check_private_tree(OWNER_ROOT)
    return {
        "valid": True,
        "assurance_level": "INTERNAL_PASS",
        "local_acceptance": "INTERNAL_PASS",
        "candidate_disposition": reconstructed["candidate_disposition"],
        "run_id": run_id,
        "claim_ceiling": CLAIM_CEILING,
        "independent_acceptance": False,
        "public_report_sha256": sha256_file(PUBLIC_REPORT_PATH),
        "private_run_sha256": private_sha,
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description="local BillSum same-roster curriculum order V9")
    parser.add_argument("command", choices=("audit", "prepare", "run", "verify"))
    command = parser.parse_args().command
    result = {"audit": audit, "prepare": prepare, "run": run, "verify": verify}[command]()
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
