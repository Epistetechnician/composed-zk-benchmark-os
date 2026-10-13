"""Frozen local BillSum chat-template and adaptive-curriculum experiment.

State slice: aligned-rsi-billsum-length-matched-curriculum-v8.
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


STATE_SLICE = "aligned-rsi-billsum-length-matched-curriculum-v8"
GOVERNANCE_SLICE = "global-experiment-assurance-lifecycle-v1"
PROTOCOL_ID = "aligned-rsi-billsum-length-matched-curriculum-v8"
CLAIM_CEILING = "LocalDevelopmentBillSumLengthMatchedCurriculumQualificationV8"
MODEL_ID = "Qwen/Qwen3-0.6B"
MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
DATASET_ID = "FiscalNote/billsum"
DATASET_REVISION = "3d8510441c06a3d9dfb32eb0d7f80151730bcc4f"
DATA_FILES = (
    "data/train-00000-of-00001.parquet",
    "data/test-00000-of-00001.parquet",
)
V1_STATE_SLICE = "aligned-rsi-local-billsum-adaptation-internal-v1"
V1_FIT_PREFIX = 512
V1_ASSESSMENT_PREFIX = 128
PRIOR_VERSIONS = (4, 5, 6, 7)
FIT_POOL_SIZE = 768
ARM_EXAMPLES = 128
ASSESSMENT_SIZE = 128
SEEDS = (211, 307, 401, 503)
LENGTH_BIN_COUNT = 8
LENGTH_BIN_SIZE = FIT_POOL_SIZE // LENGTH_BIN_COUNT
STRATIFIED_PER_BIN = ARM_EXAMPLES // LENGTH_BIN_COUNT
STRATIFIED_RANDOM_SEED_XOR = 0x53545241
TRAINED_ARMS = (
    "global_loss_selected",
    "global_random_control",
    "length_stratified_loss_selected",
    "length_stratified_random_control",
)
ALL_ARMS = ("untouched_base", *TRAINED_ARMS)
PRIMARY_SELECTED_ARM = "length_stratified_loss_selected"
PRIMARY_CONTROL_ARM = "length_stratified_random_control"
MAX_SOURCE_TOKENS = 1280
MAX_TARGET_TOKENS = 512
MAX_NEW_TOKENS = 512
TRAINING_BATCH_SIZE = 4
PAD_TOKEN_ID = 151643
LORA_RANK = 8
LORA_ALPHA = 16
LEARNING_RATE = 1e-4
ADAM_BETAS = (0.9, 0.999)
ADAM_EPSILON = 1e-8
WEIGHT_DECAY = 0.01
MAX_GRAD_NORM = 1.0
LAYER_INDEX = 13
MECHANISTIC_ROWS = 16
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261010
MIN_EFFECT = 0.02
IDENTITY_PATCH_TOLERANCE = 1e-5
WALL_CLOCK_LIMIT_SECONDS = 480 * 60
PROTOCOL_MANIFEST_SHA256 = "bf92cb8468a3d1647f357217ec92f376753ffee50942e312d9afb663454c2626"
CHAT_TEMPLATE_SHA256 = "a55ee1b1660128b7098723e0abcd92caa0788061051c62d51cbe87d9cf1974d8"
ASSISTANT_END_TOKEN_ID = 151645
TEMPLATE_TRAILER_TOKEN_ID = 198
SYSTEM_PROMPT = (
    "You are a concise U.S. federal bill summarization assistant. "
    "State the bill's main purpose and key provisions. Do not add unsupported claims."
)
USER_PROMPT_PREFIX = "Summarize this U.S. federal bill.\n\nBILL:\n"
REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = REPO_ROOT / "docs/research/continual-learning/326-aligned-rsi-billsum-length-matched-curriculum-v8.md"
MANIFEST_PATH = Path(__file__).with_name("aligned_rsi_billsum_length_matched_v8.json")
TEST_PATH = Path(__file__).parent / "tests/test_aligned_rsi_billsum_length_matched_v8.py"
LOCK_PATH = Path(__file__).with_name("aligned_rsi_billsum_length_matched_v8_requirements.lock")
V1_OWNER_ROOT = Path.home() / ".local/share/aligned-rsi-local-billsum-adaptation-v1"
MODEL_ROOT = V1_OWNER_ROOT / "inputs/model"
DATASET_ROOT = V1_OWNER_ROOT / "inputs/billsum"
OWNER_ROOT = Path.home() / ".local/share/aligned-rsi-billsum-length-matched-curriculum-v8"
PREPARED_PATH = OWNER_ROOT / "prepared_inputs.json"
RUNS_ROOT = OWNER_ROOT / "runs"
RELEASE_ROOT = REPO_ROOT / "release/aligned_rsi_billsum_length_matched_v8"
PUBLIC_REPORT_PATH = RELEASE_ROOT / "evaluation_report.json"


class ExperimentError(ValueError):
    """Raised when the frozen local experiment contract is invalid."""


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


def load_json(path: Path) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ExperimentError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ExperimentError(f"non-standard JSON value: {token}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ExperimentError(f"expected JSON object: {path}")
    return value


def save_json(path: Path, value: Any, *, private: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700 if private else 0o755)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(
        json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n"
    )
    temporary.chmod(0o600 if private else 0o644)
    temporary.replace(path)


def _document_id(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def _legacy_v1_document_id(text: str, summary: str) -> str:
    return sha256_bytes(text.encode("utf-8") + b"\0" + summary.encode("utf-8"))


def tree_manifest(root: Path) -> list[dict[str, str]]:
    if root.is_symlink() or not root.is_dir():
        raise ExperimentError(f"expected regular input directory: {root}")
    files: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".cache" in relative.parts:
            continue
        if path.is_symlink():
            raise ExperimentError(f"input tree contains symlink: {relative}")
        if path.is_file():
            files.append({"path": relative.as_posix(), "sha256": sha256_file(path)})
    if not files:
        raise ExperimentError(f"input tree is empty: {root}")
    return files


def _tree_digest(files: list[dict[str, str]]) -> str:
    return sha256_bytes(canonical_bytes(files))


def _ensure_private_root(root: Path, *, create: bool) -> None:
    if root.is_symlink():
        raise ExperimentError(f"private root cannot be a symlink: {root.name}")
    if not root.exists():
        if not create:
            raise ExperimentError(f"private root is missing: {root.name}")
        root.mkdir(parents=True, mode=0o700)
    if not root.is_dir():
        raise ExperimentError(f"private root is not a directory: {root.name}")
    root.chmod(0o700)
    if root.stat().st_mode & 0o777 != 0o700:
        raise ExperimentError(f"private root must have mode 0700: {root.name}")


def _check_private_tree(root: Path) -> None:
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o777 != 0o700:
        raise ExperimentError(f"private custody root is not owner-only: {root.name}")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ExperimentError(f"private custody tree contains symlink: {path.relative_to(root)}")
        if path.is_dir() and path.stat().st_mode & 0o777 != 0o700:
            raise ExperimentError(f"private directory is not owner-only: {path.relative_to(root)}")


def _secure_private_directories(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_symlink():
            raise ExperimentError(f"private tree contains symlink: {path.relative_to(root)}")
        if path.is_dir():
            path.chmod(0o700)
        elif path.is_file():
            path.chmod(0o600)
    root.chmod(0o700)


def _adapter_manifest(directory: Path) -> list[dict[str, str]]:
    expected = {"README.md", "adapter_config.json", "adapter_model.safetensors"}
    if directory.is_symlink() or not directory.is_dir():
        raise ExperimentError("PEFT adapter output is not a regular directory")
    files: list[dict[str, str]] = []
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink():
            raise ExperimentError(f"PEFT adapter tree contains a symlink: {relative}")
        if path.is_dir():
            raise ExperimentError(f"PEFT adapter tree contains a nested directory: {relative}")
        if path.is_file():
            files.append({"path": relative, "sha256": sha256_file(path)})
    paths = {item["path"] for item in files}
    if paths != expected:
        raise ExperimentError(f"unexpected PEFT adapter files: {sorted(paths)}")
    readme_path = directory / "README.md"
    if readme_path.stat().st_size > 65_536:
        raise ExperimentError("PEFT adapter README.md exceeds the frozen private metadata size bound")
    try:
        readme_path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ExperimentError("PEFT adapter README.md is not valid UTF-8 metadata") from exc
    return files


def _runtime_manifest() -> dict[str, str]:
    try:
        from importlib.metadata import version

        packages = {
            "python": ".".join(map(str, sys.version_info[:3])),
            "platform": f"{sys.platform}-{platform.machine()}",
            "torch": version("torch"),
            "transformers": version("transformers"),
            "datasets": version("datasets"),
            "huggingface-hub": version("huggingface-hub"),
            "safetensors": version("safetensors"),
            "numpy": version("numpy"),
            "pyarrow": version("pyarrow"),
            "peft": version("peft"),
            "accelerate": version("accelerate"),
            "rouge-score": version("rouge-score"),
            "absl-py": version("absl-py"),
            "nltk": version("nltk"),
            "tokenizers": version("tokenizers"),
        }
    except Exception as exc:
        raise ExperimentError("runtime package inventory is incomplete") from exc
    expected = {
        "python": "3.14.5",
        "platform": "darwin-arm64",
        "torch": "2.13.0",
        "transformers": "5.14.1",
        "datasets": "5.0.1",
        "huggingface-hub": "1.27.0",
        "safetensors": "0.8.0",
        "numpy": "2.5.1",
        "pyarrow": "25.0.0",
        "peft": "0.21.2",
        "accelerate": "1.14.0",
        "rouge-score": "0.1.2",
        "absl-py": "2.5.0",
        "nltk": "3.10.2",
        "tokenizers": "0.22.2",
    }
    if packages != expected:
        raise ExperimentError(f"runtime differs from frozen V8 lock: {packages}")
    return packages


def _verify_protocol() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    if sha256_file(MANIFEST_PATH) != PROTOCOL_MANIFEST_SHA256:
        raise ExperimentError("machine contract bytes differ from the frozen V8 manifest digest")
    required = {
        "schema_version": "aligned-rsi-billsum-length-matched-curriculum-v8-protocol",
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "governance_slice": GOVERNANCE_SLICE,
        "status": "LOCAL_EXECUTION_AUTHORIZED_BY_USER",
        "assurance_target": "INTERNAL_PASS",
        "claim_ceiling": CLAIM_CEILING,
        "independent_acceptance_requested": False,
    }
    for key, expected in required.items():
        if manifest.get(key) != expected:
            raise ExperimentError(f"protocol manifest mismatch: {key}")
    if manifest.get("runtime") != _runtime_manifest():
        raise ExperimentError("runtime differs from the frozen protocol manifest")
    expected_model = {
        "repo_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "license": "apache-2.0",
        "chat_template_sha256": CHAT_TEMPLATE_SHA256,
        "enable_thinking": False,
        "base_weights_mutable": False,
        "adapter_implementation": "huggingface-peft",
        "adapter_package": "peft==0.21.2",
    }
    expected_prompt = {
        "system_message": SYSTEM_PROMPT,
        "user_message_prefix": USER_PROMPT_PREFIX,
        "assistant_target": "the exact BillSum summary field",
        "source_truncation": False,
        "assistant_target_truncation": False,
    }
    expected_dataset = {
        "repo_id": DATASET_ID,
        "revision": DATASET_REVISION,
        "license": "cc0-1.0",
        "included_splits": ["train", "test"],
        "excluded_splits": ["ca_test"],
        "source_boundary": "US_federal_GPO_bills_only",
        "new_document_id": "sha256(utf8(text))",
    }
    if manifest.get("model") != expected_model or manifest.get("prompt") != expected_prompt:
        raise ExperimentError("model or prompt differs from the frozen V8 semantics")
    if manifest.get("dataset") != expected_dataset:
        raise ExperimentError("dataset differs from the frozen V8 semantics")
    cohorts = manifest.get("cohorts", {})
    expected_cohorts = {
        "fit_pool_size": FIT_POOL_SIZE,
        "assessment_size": ASSESSMENT_SIZE,
        "fit_split": "train",
        "assessment_split": "test",
        "duplicate_source_rule": "exclude_all_rows_for_source_hash_appearing_more_than_once_within_each_split",
        "source_eligibility": "chat-template prompt at most 1280 tokens and assistant target at most 512 tokens; no source or target truncation",
        "assistant_target_truncation": False,
        "split_disjointness_required": True,
        "ca_test_access": False,
        "length_strata": {
            "sort": "ascending(prompt_token_count+assistant_target_token_count,source_id)",
            "bin_count": LENGTH_BIN_COUNT,
            "documents_per_bin": LENGTH_BIN_SIZE,
            "selected_per_bin": STRATIFIED_PER_BIN,
            "random_sampling": "python_random_Random_sample_without_replacement_in_bin_order",
            "random_seed": "training_seed_xor_0x53545241",
        },
    }
    for key, expected in expected_cohorts.items():
        if cohorts.get(key) != expected:
            raise ExperimentError(f"cohort contract differs from the frozen V8 semantics: {key}")
    if any(cohorts.get(f"v{version}_scientific_outputs_reused") is not False for version in range(1, 8)):
        raise ExperimentError("V8 must not reuse prior scientific outputs")
    expected_arms = [
        {"id": "untouched_base", "training_examples": 0, "assessment_repeats": len(SEEDS)},
        {"id": "global_loss_selected", "selection": "top_128_fit_pool_assistant_target_nll", "training_examples": ARM_EXAMPLES, "assessment_repeats": len(SEEDS)},
        {"id": "global_random_control", "selection": "uniform_128_fit_pool_per_seed", "training_examples": ARM_EXAMPLES, "assessment_repeats": len(SEEDS)},
        {"id": PRIMARY_SELECTED_ARM, "selection": "top_16_assistant_target_nll_from_each_of_8_total_token_length_bins", "training_examples": ARM_EXAMPLES, "assessment_repeats": len(SEEDS)},
        {"id": PRIMARY_CONTROL_ARM, "selection": "uniform_16_fit_documents_from_each_of_8_total_token_length_bins_per_seed", "training_examples": ARM_EXAMPLES, "assessment_repeats": len(SEEDS)},
    ]
    if manifest.get("arms") != expected_arms:
        raise ExperimentError("arm roster differs from the frozen V8 design")
    training = manifest.get("training", {})
    expected_training = {
        "seeds": list(SEEDS),
        "optimizer": "AdamW",
        "learning_rate": LEARNING_RATE,
        "betas": list(ADAM_BETAS),
        "epsilon": ADAM_EPSILON,
        "weight_decay": WEIGHT_DECAY,
        "batch_size": TRAINING_BATCH_SIZE,
        "microbatch_size": 1,
        "gradient_accumulation_examples": TRAINING_BATCH_SIZE,
        "epochs": 1,
        "lora_rank": LORA_RANK,
        "lora_alpha": LORA_ALPHA,
        "lora_dropout": 0,
        "lora_target_modules": ["q_proj", "v_proj"],
        "adapter_library": "PEFT",
        "max_source_tokens": MAX_SOURCE_TOKENS,
        "max_assistant_target_tokens": MAX_TARGET_TOKENS,
        "assistant_only_loss": True,
        "gradient_clip_norm": MAX_GRAD_NORM,
        "base_weights_mutable": False,
        "equal_optimizer_steps_per_updated_arm": ARM_EXAMPLES // TRAINING_BATCH_SIZE,
        "generation_pad_token_id": PAD_TOKEN_ID,
        "training_examples_per_updated_arm_per_seed": ARM_EXAMPLES,
        "total_optimizer_steps": len(TRAINED_ARMS) * len(SEEDS) * (ARM_EXAMPLES // TRAINING_BATCH_SIZE),
        "example_order": "python_random_Random_seed_xor_0x5A17_shuffle_once_before_batching",
        "batch_padding": "one_unpadded_sequence_per_forward",
        "loss_reduction": "token_weighted_mean_assistant_cross_entropy_over_each_four_example_accumulation_group",
        "logits_projection": "apply_lm_head_only_to_assistant_target_prediction_positions",
        "gradient_checkpointing": "transformer_layer_checkpointing_non_reentrant",
    }
    for key, expected in expected_training.items():
        if training.get(key) != expected:
            raise ExperimentError(f"training contract differs from the frozen V8 semantics: {key}")
    metric = manifest.get("primary_metric", {})
    expected_metric = {
        "name": "paired_document_bootstrap_rougeL_length_stratified_loss_minus_length_stratified_random",
        "implementation": "rouge-score==0.1.2",
        "use_stemmer": False,
        "minimum_meaningful_effect": MIN_EFFECT,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "candidate_rule": "mean_effect>=0.02_and_ci95_lower>0_and_length_stratified_loss_not_below_base_and_length_stratified_loss_target_nll_no_more_than_0.05_above_base_and_all_locked_outputs_finite_and_identity_patch_error_within_1e-5",
    }
    if metric != expected_metric:
        raise ExperimentError("primary metric or candidate rule differs from the frozen V8 design")
    decoding = manifest.get("decoding", {})
    if decoding.get("generation_seed_constants", {}).get("protocol_constant") != "0xA17E2029":
        raise ExperimentError("V8 decoding seed protocol constant differs")
    diagnostic = manifest.get("mechanistic_diagnostic", {})
    if diagnostic.get("layer_index_zero_based") != LAYER_INDEX or diagnostic.get("assessment_documents") != MECHANISTIC_ROWS:
        raise ExperimentError("layer diagnostic differs from the frozen V8 scope")
    execution = manifest.get("execution", {})
    if execution.get("device") != "Apple_MPS_local" or execution.get("network_during_run") is not False:
        raise ExperimentError("V8 must run offline on local Apple MPS")
    if execution.get("wall_clock_limit_minutes") != WALL_CLOCK_LIMIT_SECONDS // 60:
        raise ExperimentError("V8 wall-clock ceiling differs from the frozen packet")
    if execution.get("output_root") != "$HOME/.local/share/aligned-rsi-billsum-length-matched-curriculum-v8":
        raise ExperimentError("V8 private custody root differs from the frozen packet")
    return manifest




def _load_federal_rows(split: str) -> list[dict[str, str]]:
    if split not in {"train", "test"}:
        raise ExperimentError("only the federal train and test splits are permitted")
    path = DATASET_ROOT / f"data/{split}-00000-of-00001.parquet"
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise ExperimentError("PyArrow is required to read the pinned BillSum files") from exc
    table = parquet.read_table(path, columns=["text", "summary"])
    result: list[dict[str, str]] = []
    for row in table.to_pylist():
        text = row.get("text")
        summary = row.get("summary")
        if not isinstance(text, str) or not text.strip() or not isinstance(summary, str) or not summary.strip():
            raise ExperimentError(f"federal {split} row has missing text or summary")
        doc_id = _document_id(text)
        result.append(
            {
                "doc_id": doc_id,
                "legacy_v1_doc_id": _legacy_v1_document_id(text, summary),
                "text": text,
                "summary": summary,
            }
        )
    return result


def _messages(row: Mapping[str, str]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_PREFIX + row["text"]},
    ]


def _template_token_ids(tokenizer: Any, messages: list[dict[str, str]], *, add_generation_prompt: bool) -> list[int]:
    try:
        token_ids = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=add_generation_prompt,
            enable_thinking=False,
            return_dict=False,
        )
    except Exception as exc:
        raise ExperimentError("pinned Qwen3 chat template could not encode the frozen conversation") from exc
    if not isinstance(token_ids, list) or not token_ids or any(not isinstance(item, int) for item in token_ids):
        raise ExperimentError("chat template returned an invalid token sequence")
    return token_ids


def _tokenize_row(tokenizer: Any, row: dict[str, str]) -> dict[str, Any]:
    prompt_ids = _template_token_ids(tokenizer, _messages(row), add_generation_prompt=True)
    full_ids = _template_token_ids(
        tokenizer,
        [*_messages(row), {"role": "assistant", "content": row["summary"]}],
        add_generation_prompt=False,
    )
    if full_ids[: len(prompt_ids)] != prompt_ids:
        raise ExperimentError(f"Qwen3 assistant prefix changed during template continuation: {row['doc_id']}")
    target_ids = full_ids[len(prompt_ids) :]
    if not target_ids or len(prompt_ids) > MAX_SOURCE_TOKENS:
        raise ExperimentError(f"tokenized row violates the frozen length bounds: {row['doc_id']}")
    expected_suffix = [ASSISTANT_END_TOKEN_ID, TEMPLATE_TRAILER_TOKEN_ID]
    if len(target_ids) < len(expected_suffix) or target_ids[-len(expected_suffix) :] != expected_suffix:
        raise ExperimentError(f"assistant template terminator or trailer differs from the frozen V8 tokens: {row['doc_id']}")
    target_ids = target_ids[:-1]
    if target_ids[-1] != ASSISTANT_END_TOKEN_ID or len(target_ids) > MAX_TARGET_TOKENS:
        raise ExperimentError(f"assistant target violates the frozen end-marker or length contract: {row['doc_id']}")
    full_conversation_ids = [*prompt_ids, *target_ids]
    labels = [-100] * len(prompt_ids) + target_ids
    reference_tokens = tokenizer(row["summary"], add_special_tokens=False)["input_ids"]
    return {
        "doc_id": row["doc_id"],
        "text": row["text"],
        "summary": row["summary"],
        "prompt_ids": prompt_ids,
        "target_ids": target_ids,
        "input_ids": full_conversation_ids,
        "labels": labels,
        "target_start": len(prompt_ids),
        "prompt_token_count": len(prompt_ids),
        "target_token_count": len(target_ids),
        "reference_token_count": len(reference_tokens),
    }


def _fresh_rosters(
    tokenizer: Any,
    train_rows: list[dict[str, str]],
    test_rows: list[dict[str, str]],
) -> dict[str, Any]:
    contract = load_json(MANIFEST_PATH)
    expected_prior = contract["prepared_identity"]["prior_rosters"]
    legacy_train = sorted(train_rows, key=lambda row: row["legacy_v1_doc_id"])
    legacy_test = sorted(test_rows, key=lambda row: row["legacy_v1_doc_id"])
    excluded_v1_train = {row["doc_id"] for row in legacy_train[:V1_FIT_PREFIX]}
    excluded_v1_test = {row["doc_id"] for row in legacy_test[:V1_ASSESSMENT_PREFIX]}
    train_counts = Counter(row["doc_id"] for row in train_rows)
    test_counts = Counter(row["doc_id"] for row in test_rows)
    duplicate_train = {identifier for identifier, count in train_counts.items() if count > 1}
    duplicate_test = {identifier for identifier, count in test_counts.items() if count > 1}
    excluded_train = set(excluded_v1_train)
    excluded_test = set(excluded_v1_test)
    prior_rosters: dict[str, Any] = {}
    prior_fit_ids: dict[int, set[str]] = {}
    prior_assessment_ids: dict[int, set[str]] = {}

    for version in PRIOR_VERSIONS:
        key = f"v{version}"
        root = Path.home() / f".local/share/aligned-rsi-billsum-chat-template-adaptation-{key}"
        receipt_path = root / "prepared_inputs.json"
        if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o777 != 0o700:
            raise ExperimentError(f"prior {key} custody root is not owner-only")
        if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.stat().st_mode & 0o777 != 0o600:
            raise ExperimentError(f"prior {key} prepared-input receipt is not an owner-only regular file")
        receipt = load_json(receipt_path)
        receipt_digest = receipt.get("prepared_inputs_sha256")
        unsigned = {name: value for name, value in receipt.items() if name != "prepared_inputs_sha256"}
        if receipt_digest != sha256_bytes(canonical_bytes(unsigned)):
            raise ExperimentError(f"prior {key} prepared-input receipt digest is invalid")
        if receipt_digest != expected_prior[key]["receipt_sha256"]:
            raise ExperimentError(f"prior {key} prepared-input receipt differs from the frozen V8 contract")
        if receipt.get("state_slice") != f"aligned-rsi-billsum-chat-template-adaptation-{key}":
            raise ExperimentError(f"prior {key} receipt has the wrong state slice")
        if (
            receipt.get("model_repo_id") != MODEL_ID
            or receipt.get("model_revision") != MODEL_REVISION
            or receipt.get("dataset_repo_id") != DATASET_ID
            or receipt.get("dataset_revision") != DATASET_REVISION
            or receipt.get("model_files_sha256") != contract["prepared_identity"]["model_files_sha256"]
            or receipt.get("dataset_files_sha256") != contract["prepared_identity"]["dataset_files_sha256"]
        ):
            raise ExperimentError(f"prior {key} receipt does not bind the pinned V8 model and data")
        fit_ids = receipt.get("fit_ids")
        assessment_ids = receipt.get("assessment_ids")
        if not isinstance(fit_ids, list) or not isinstance(assessment_ids, list):
            raise ExperimentError(f"prior {key} receipt has no complete source rosters")
        if len(fit_ids) != len(set(fit_ids)) or len(assessment_ids) != len(set(assessment_ids)):
            raise ExperimentError(f"prior {key} receipt contains duplicate source IDs")
        if (
            len(fit_ids) != expected_prior[key]["fit_count"]
            or len(assessment_ids) != expected_prior[key]["assessment_count"]
            or receipt.get("fit_roster_sha256") != sha256_bytes(canonical_bytes(fit_ids))
            or receipt.get("assessment_roster_sha256") != sha256_bytes(canonical_bytes(assessment_ids))
            or sha256_bytes(canonical_bytes(sorted(fit_ids))) != expected_prior[key]["fit_source_ids_sha256"]
            or sha256_bytes(canonical_bytes(sorted(assessment_ids))) != expected_prior[key]["assessment_source_ids_sha256"]
        ):
            raise ExperimentError(f"prior {key} roster identity differs from the frozen V8 contract")
        if any(not isinstance(identifier, str) or len(identifier) != 64 for identifier in (*fit_ids, *assessment_ids)):
            raise ExperimentError(f"prior {key} receipt contains an invalid source ID")
        prior_fit_ids[version] = set(fit_ids)
        prior_assessment_ids[version] = set(assessment_ids)
        excluded_train.update(fit_ids)
        excluded_test.update(assessment_ids)
        prior_rosters[key] = {
            "receipt_sha256": receipt_digest,
            "fit_count": len(fit_ids),
            "assessment_count": len(assessment_ids),
            "fit_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(fit_ids))),
            "assessment_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(assessment_ids))),
        }

    def eligible_rows(
        rows: list[dict[str, str]],
        excluded: set[str],
        duplicates: set[str],
        label: str,
    ) -> list[dict[str, str]]:
        eligible: list[dict[str, str]] = []
        for row in sorted(rows, key=lambda item: item["doc_id"]):
            if row["doc_id"] in excluded or row["doc_id"] in duplicates:
                continue
            prompt_ids = _template_token_ids(tokenizer, _messages(row), add_generation_prompt=True)
            if len(prompt_ids) > MAX_SOURCE_TOKENS:
                continue
            full_ids = _template_token_ids(
                tokenizer,
                [*_messages(row), {"role": "assistant", "content": row["summary"]}],
                add_generation_prompt=False,
            )
            if full_ids[: len(prompt_ids)] != prompt_ids:
                raise ExperimentError(f"assistant prefix changed while checking V8 {label} eligibility")
            expected_suffix = [ASSISTANT_END_TOKEN_ID, TEMPLATE_TRAILER_TOKEN_ID]
            if len(full_ids) < 2 or full_ids[-2:] != expected_suffix:
                raise ExperimentError(f"assistant terminator/trailer changed while checking V8 {label} eligibility")
            target_ids = full_ids[len(prompt_ids) : -1]
            if len(target_ids) > MAX_TARGET_TOKENS:
                continue
            eligible.append(row)
        return eligible

    eligible_fit = eligible_rows(train_rows, excluded_train, duplicate_train, "fit")
    eligible_assessment = eligible_rows(test_rows, excluded_test, duplicate_test, "assessment")
    if len(eligible_fit) < FIT_POOL_SIZE or len(eligible_assessment) < ASSESSMENT_SIZE:
        raise ExperimentError("not enough fresh V8 rows remain after all frozen exclusions and tokenizer rules")
    fit = eligible_fit[:FIT_POOL_SIZE]
    assessment = eligible_assessment[:ASSESSMENT_SIZE]
    fit_ids = [row["doc_id"] for row in fit]
    assessment_ids = [row["doc_id"] for row in assessment]
    if set(fit_ids) & set(assessment_ids):
        raise ExperimentError("V8 fit and assessment source rosters overlap")
    if any(identifier in excluded_train or identifier in duplicate_train for identifier in fit_ids):
        raise ExperimentError("V8 fit roster overlaps a previous or duplicate source")
    if any(identifier in excluded_test or identifier in duplicate_test for identifier in assessment_ids):
        raise ExperimentError("V8 assessment roster overlaps a previous or duplicate source")
    prior_fit_union = set().union(*prior_fit_ids.values())
    prior_assessment_union = set().union(*prior_assessment_ids.values())
    all_fit_union = excluded_v1_train | prior_fit_union
    all_assessment_union = excluded_v1_test | prior_assessment_union
    return {
        "v1_excluded": {
            "fit_count": V1_FIT_PREFIX,
            "assessment_count": V1_ASSESSMENT_PREFIX,
            "fit_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(excluded_v1_train))),
            "assessment_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(excluded_v1_test))),
        },
        "prior_rosters": prior_rosters,
        "prior_union": {
            "v4_to_v7_fit_count": len(prior_fit_union),
            "v4_to_v7_assessment_count": len(prior_assessment_union),
            "v4_to_v7_fit_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(prior_fit_union))),
            "v4_to_v7_assessment_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(prior_assessment_union))),
            "all_fit_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(all_fit_union))),
            "all_assessment_source_ids_sha256": sha256_bytes(canonical_bytes(sorted(all_assessment_union))),
        },
        "eligible_after_prior_exclusions": {"fit": len(eligible_fit), "assessment": len(eligible_assessment)},
        "duplicate_source_groups_excluded": {
            "train_groups": len(duplicate_train),
            "train_rows": sum(train_counts[identifier] for identifier in duplicate_train),
            "test_groups": len(duplicate_test),
            "test_rows": sum(test_counts[identifier] for identifier in duplicate_test),
        },
        "fit_rows": fit,
        "assessment_rows": assessment,
        "fit_ids": fit_ids,
        "assessment_ids": assessment_ids,
    }





def _build_prepared_payload() -> dict[str, Any]:
    contract = _verify_protocol()
    _check_private_tree(V1_OWNER_ROOT)
    for root in (MODEL_ROOT, DATASET_ROOT):
        if root.is_symlink() or not root.is_dir():
            raise ExperimentError("pinned V1 raw input directory is unavailable")
    model_files = tree_manifest(MODEL_ROOT)
    dataset_files = tree_manifest(DATASET_ROOT)
    expected_dataset_files = sorted(["README.md", *DATA_FILES])
    if sorted(item["path"] for item in dataset_files) != expected_dataset_files:
        raise ExperimentError("V8 may read only the pinned federal train/test files and dataset README")
    model_config = load_json(MODEL_ROOT / "config.json")
    if model_config.get("model_type") != "qwen3" or model_config.get("num_hidden_layers") != 28:
        raise ExperimentError("cached model configuration differs from the frozen Qwen3-0.6B architecture")
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ExperimentError("Transformers is required for local tokenizer preparation") from exc
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ROOT, local_files_only=True, trust_remote_code=False)
    template_sha = sha256_bytes(tokenizer.chat_template.encode("utf-8"))
    if template_sha != CHAT_TEMPLATE_SHA256:
        raise ExperimentError("local chat-template bytes differ from the frozen Qwen3 template")
    if tokenizer.convert_tokens_to_ids("<|im_end|>") != ASSISTANT_END_TOKEN_ID:
        raise ExperimentError("local assistant end-marker token ID differs from the frozen protocol")
    if tokenizer("\n", add_special_tokens=False)["input_ids"] != [TEMPLATE_TRAILER_TOKEN_ID]:
        raise ExperimentError("local assistant template trailer token differs from the frozen protocol")
    if tokenizer.pad_token_id != PAD_TOKEN_ID:
        raise ExperimentError("local Qwen3 padding token ID differs from the frozen V8 batch protocol")
    train_rows = _load_federal_rows("train")
    test_rows = _load_federal_rows("test")
    rosters = _fresh_rosters(tokenizer, train_rows, test_rows)
    fit_encoded = [_tokenize_row(tokenizer, row) for row in rosters["fit_rows"]]
    assessment_encoded = [_tokenize_row(tokenizer, row) for row in rosters["assessment_rows"]]
    if any(row["target_token_count"] > MAX_TARGET_TOKENS for row in (*fit_encoded, *assessment_encoded)):
        raise ExperimentError("fresh V8 cohort contains an oversized assistant target")
    fit_length_order = sorted(
        fit_encoded,
        key=lambda row: (row["prompt_token_count"] + row["target_token_count"], row["doc_id"]),
    )
    length_bins = [
        {
            "count": len(rows),
            "total_tokens_min": min(row["prompt_token_count"] + row["target_token_count"] for row in rows),
            "total_tokens_max": max(row["prompt_token_count"] + row["target_token_count"] for row in rows),
        }
        for start in range(0, len(fit_length_order), LENGTH_BIN_SIZE)
        for rows in (fit_length_order[start : start + LENGTH_BIN_SIZE],)
    ]
    actual_identity = {
        "model_files_sha256": _tree_digest(model_files),
        "dataset_files_sha256": _tree_digest(dataset_files),
        "v1_excluded": rosters["v1_excluded"],
        "prior_rosters": rosters["prior_rosters"],
        "prior_union": rosters["prior_union"],
        "duplicate_source_groups_excluded": rosters["duplicate_source_groups_excluded"],
        "eligible_after_prior_exclusions": rosters["eligible_after_prior_exclusions"],
        "fit_roster_sha256": sha256_bytes(canonical_bytes(rosters["fit_ids"])),
        "assessment_roster_sha256": sha256_bytes(canonical_bytes(rosters["assessment_ids"])),
        "fit_prompt_token_count_min_max": [
            min(row["prompt_token_count"] for row in fit_encoded),
            max(row["prompt_token_count"] for row in fit_encoded),
        ],
        "fit_assistant_token_count_min_max": [
            min(row["target_token_count"] for row in fit_encoded),
            max(row["target_token_count"] for row in fit_encoded),
        ],
        "assessment_prompt_token_count_min_max": [
            min(row["prompt_token_count"] for row in assessment_encoded),
            max(row["prompt_token_count"] for row in assessment_encoded),
        ],
        "assessment_assistant_token_count_min_max": [
            min(row["target_token_count"] for row in assessment_encoded),
            max(row["target_token_count"] for row in assessment_encoded),
        ],
        "length_bins": length_bins,
    }
    if actual_identity != contract["prepared_identity"]:
        raise ExperimentError("raw input manifests or reconstructed V8 cohort identity differ from the frozen contract")
    return {
        "schema_version": "aligned-rsi-billsum-length-matched-curriculum-v8-prepared-inputs",
        "state_slice": STATE_SLICE,
        "model_repo_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_files": model_files,
        "model_files_sha256": actual_identity["model_files_sha256"],
        "model_config_sha256": sha256_file(MODEL_ROOT / "config.json"),
        "dataset_repo_id": DATASET_ID,
        "dataset_revision": DATASET_REVISION,
        "dataset_files": dataset_files,
        "dataset_files_sha256": actual_identity["dataset_files_sha256"],
        "included_dataset_files": list(DATA_FILES),
        "excluded_split": "ca_test",
        "chat_template_sha256": template_sha,
        "assistant_end_token_id": int(tokenizer.convert_tokens_to_ids("<|im_end|>")),
        "pad_token_id": int(tokenizer.pad_token_id),
        "runtime": _runtime_manifest(),
        "source_digests": _source_manifest(),
        "v1_excluded": rosters["v1_excluded"],
        "prior_rosters": rosters["prior_rosters"],
        "prior_union": rosters["prior_union"],
        "eligible_after_prior_exclusions": rosters["eligible_after_prior_exclusions"],
        "duplicate_source_groups_excluded": rosters["duplicate_source_groups_excluded"],
        "fit_ids": rosters["fit_ids"],
        "assessment_ids": rosters["assessment_ids"],
        "fit_roster_sha256": actual_identity["fit_roster_sha256"],
        "assessment_roster_sha256": actual_identity["assessment_roster_sha256"],
        "fit_prompt_token_count_min_max": actual_identity["fit_prompt_token_count_min_max"],
        "fit_assistant_token_count_min_max": actual_identity["fit_assistant_token_count_min_max"],
        "assessment_prompt_token_count_min_max": actual_identity["assessment_prompt_token_count_min_max"],
        "assessment_assistant_token_count_min_max": actual_identity["assessment_assistant_token_count_min_max"],
        "length_bins": length_bins,
    }





def prepare() -> dict[str, Any]:
    """Freeze the exact local model/data bytes and fresh V8 rosters."""
    _verify_protocol()
    _ensure_private_root(OWNER_ROOT, create=True)
    RUNS_ROOT.mkdir(parents=True, mode=0o700, exist_ok=True)
    RUNS_ROOT.chmod(0o700)
    payload = _build_prepared_payload()
    payload["prepared_inputs_sha256"] = sha256_bytes(canonical_bytes(payload))
    save_json(PREPARED_PATH, payload)
    _check_private_tree(OWNER_ROOT)
    return {
        "prepared": True,
        "state_slice": STATE_SLICE,
        "model_revision": MODEL_REVISION,
        "dataset_revision": DATASET_REVISION,
        "fit_documents": len(payload["fit_ids"]),
        "assessment_documents": len(payload["assessment_ids"]),
        "fit_roster_sha256": payload["fit_roster_sha256"],
        "assessment_roster_sha256": payload["assessment_roster_sha256"],
        "prepared_inputs_sha256": payload["prepared_inputs_sha256"],
        "independent_acceptance": False,
    }


def _validate_prepared() -> dict[str, Any]:
    _ensure_private_root(OWNER_ROOT, create=False)
    stored = load_json(PREPARED_PATH)
    digest = stored.get("prepared_inputs_sha256")
    unsigned = {key: value for key, value in stored.items() if key != "prepared_inputs_sha256"}
    if digest != sha256_bytes(canonical_bytes(unsigned)):
        raise ExperimentError("prepared-input digest mismatch")
    current = _build_prepared_payload()
    if canonical_bytes(current) != canonical_bytes(unsigned):
        raise ExperimentError("current local inputs or fresh rosters differ from the frozen prepared packet")
    _check_private_tree(OWNER_ROOT)
    return stored


def _source_manifest() -> dict[str, str]:
    paths = {
        "runner": Path(__file__).resolve(),
        "protocol": PROTOCOL_PATH,
        "protocol_manifest": MANIFEST_PATH,
        "focused_tests": TEST_PATH,
        "requirements_lock": LOCK_PATH,
        "repository_instructions": REPO_ROOT / "AGENTS.md",
    }
    return {name: sha256_file(path) for name, path in paths.items()}


def _import_torch() -> tuple[Any, Any]:
    try:
        import torch
        import torch.nn.functional as functional
    except ImportError as exc:
        raise ExperimentError("PyTorch is required for local PEFT training") from exc
    if sys.platform != "darwin" or platform.machine() != "arm64" or not torch.backends.mps.is_available():
        raise ExperimentError("the frozen V8 execution target is Apple Silicon macOS with MPS")
    return torch, functional


def _create_model_and_tokenizer(model_root: Path) -> tuple[Any, Any, Any, str]:
    torch, _ = _import_torch()
    try:
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise ExperimentError("Transformers and PEFT are required for local V8 model execution") from exc
    tokenizer = AutoTokenizer.from_pretrained(
        model_root,
        local_files_only=True,
        trust_remote_code=False,
    )
    base = AutoModelForCausalLM.from_pretrained(
        model_root,
        local_files_only=True,
        trust_remote_code=False,
        dtype=torch.float16,
        attn_implementation="eager",
    )
    if not hasattr(base, "model") or not hasattr(base.model, "layers") or len(base.model.layers) != 28:
        raise ExperimentError("loaded base model differs from the frozen Qwen3 decoder shape")
    if len(base.model.layers) <= LAYER_INDEX:
        raise ExperimentError("fixed mechanistic layer is outside the model")
    for parameter in base.parameters():
        parameter.requires_grad_(False)
    config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=0.0,
        bias="none",
        target_modules=["q_proj", "v_proj"],
        task_type=TaskType.CAUSAL_LM,
        init_lora_weights=True,
    )
    model = get_peft_model(base, config)
    model.to(torch.device("mps"))
    model.config.use_cache = False
    model.peft_config["default"].base_model_name_or_path = MODEL_ID
    from peft.tuners.lora.layer import LoraLayer

    lora_layers = [module for module in model.modules() if isinstance(module, LoraLayer)]
    if len(lora_layers) != 56:
        raise ExperimentError(f"expected 56 PEFT LoRA layers, found {len(lora_layers)}")
    trainable = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
    if not trainable or any("lora_" not in name for name, _ in trainable):
        raise ExperimentError("PEFT trainable set contains missing or non-LoRA parameters")
    model.eval()
    return model, tokenizer, lora_layers, str(torch.device("mps"))


def _reset_adapter(model: Any, lora_layers: Sequence[Any], seed: int) -> list[Any]:
    torch, _ = _import_torch()
    torch.manual_seed(seed)
    torch.mps.manual_seed(seed)
    return _reset_peft_adapter_for_seed(model, lora_layers, seed)


def _reset_peft_adapter_for_seed(model: Any, lora_layers: Sequence[Any], seed: int) -> list[Any]:
    try:
        import torch
        from peft.tuners.lora.layer import LoraLayer
    except ImportError as exc:
        raise ExperimentError("PEFT and PyTorch are required to initialize a LoRA adapter") from exc
    if not lora_layers or any(not isinstance(layer, LoraLayer) for layer in lora_layers):
        raise ExperimentError("PEFT LoRA layer roster is invalid")
    torch.manual_seed(seed)
    for layer in lora_layers:
        layer.reset_lora_parameters("default", init_lora_weights=True)
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    if not parameters:
        raise ExperimentError("PEFT adapter exposes no trainable parameters")
    return parameters


def _tensor_batch(sample: Mapping[str, Any], device: Any) -> tuple[Any, Any]:
    torch, _ = _import_torch()
    inputs = torch.tensor([sample["input_ids"]], dtype=torch.long, device=device)
    return inputs, torch.ones_like(inputs)


def _target_nll(
    model: Any,
    sample: Mapping[str, Any],
    *,
    device: Any,
    layer_patch: Any | None = None,
    capture_layer: bool = False,
) -> tuple[float, Any | None]:
    torch, functional = _import_torch()
    inputs, mask = _tensor_batch(sample, device)
    base = model.get_base_model()
    layer = base.model.layers[LAYER_INDEX]
    captured: dict[str, Any] = {}
    target_start = int(sample["target_start"])
    target_count = len(sample["target_ids"])
    patch_start = max(0, target_start - 1)
    patch_end = patch_start + target_count

    def hook(_module: Any, _arguments: Any, output: Any) -> Any:
        hidden = output[0] if isinstance(output, tuple) else output
        if capture_layer:
            captured["hidden"] = hidden.detach().to(device="cpu", dtype=torch.float32)
        if layer_patch is None:
            return output
        replacement = hidden.clone()
        patch = layer_patch.to(device=hidden.device, dtype=hidden.dtype)
        replacement[:, patch_start:patch_end, :] = patch[:, patch_start:patch_end, :]
        if isinstance(output, tuple):
            return (replacement, *output[1:])
        return replacement

    handle = layer.register_forward_hook(hook)
    try:
        with torch.inference_mode():
            output = base.model(
                input_ids=inputs,
                attention_mask=mask,
                use_cache=False,
                return_dict=True,
            )
            target_hidden = output.last_hidden_state[:, patch_start:patch_end, :]
            logits = base.lm_head(target_hidden)[0].float()
            target = torch.tensor(sample["target_ids"], dtype=torch.long, device=device)
            value = float(functional.cross_entropy(logits, target, reduction="mean").detach().cpu())
    finally:
        handle.remove()
    if not math.isfinite(value):
        raise ExperimentError(f"non-finite assistant-target NLL for {sample['doc_id']}")
    return value, captured.get("hidden")


def _assistant_target_loss_sum(model: Any, sample: Mapping[str, Any], device: Any) -> tuple[Any, int]:
    """Return summed next-token CE for assistant tokens without prompt-position logits."""
    import torch
    import torch.nn.functional as functional

    target_start = int(sample["target_start"])
    target_ids = sample["target_ids"]
    target_count = len(target_ids)
    if target_start < 1 or target_count < 1:
        raise ExperimentError("assistant target has no causal prediction positions")
    inputs = torch.tensor([sample["input_ids"]], dtype=torch.long, device=device)
    mask = torch.ones_like(inputs)
    base = model.get_base_model()
    output = base.model(
        input_ids=inputs,
        attention_mask=mask,
        use_cache=False,
        return_dict=True,
    )
    prediction_hidden = output.last_hidden_state[:, target_start - 1 : target_start + target_count - 1, :]
    logits = base.lm_head(prediction_hidden)[0].float()
    targets = torch.tensor(target_ids, dtype=torch.long, device=device)
    loss_sum = functional.cross_entropy(logits, targets, reduction="sum")
    del output, prediction_hidden, logits, targets, inputs, mask
    return loss_sum, target_count


def _generation_seed(training_seed: int, doc_id: str) -> int:
    return (int(doc_id[:16], 16) ^ (training_seed * 0x9E3779B1) ^ 0xA17E2029) & 0x7FFFFFFF


def _generate(
    model: Any,
    tokenizer: Any,
    sample: Mapping[str, Any],
    device: Any,
    *,
    seed: int,
) -> tuple[str, int]:
    torch, _ = _import_torch()
    generation_seed = _generation_seed(seed, str(sample["doc_id"]))
    torch.manual_seed(generation_seed)
    torch.mps.manual_seed(generation_seed)
    prompt_ids = sample["prompt_ids"]
    inputs = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    mask = torch.ones_like(inputs)
    model.eval()
    with torch.inference_mode():
        generated = model.generate(
            input_ids=inputs,
            attention_mask=mask,
            do_sample=True,
            temperature=0.7,
            top_p=0.8,
            top_k=20,
            repetition_penalty=1.0,
            max_new_tokens=MAX_NEW_TOKENS,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )
    output_ids = generated[0, inputs.shape[1] :].detach().cpu().tolist()
    text = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
    if not text:
        raise ExperimentError(f"empty held-out completion for {sample['doc_id']}")
    return text, generation_seed


def _evaluate_arm(
    model: Any,
    tokenizer: Any,
    rows: list[dict[str, Any]],
    device: Any,
    *,
    seed: int,
    deadline: float,
) -> dict[str, Any]:
    result: dict[str, Any] = {"generation": {}, "generation_seed": {}, "generation_tokens": {}, "nll": {}}
    for index, sample in enumerate(rows, start=1):
        if time.monotonic() > deadline:
            raise ExperimentError("480-minute wall-clock limit reached during held-out evaluation")
        text, generation_seed = _generate(model, tokenizer, sample, device, seed=seed)
        result["generation"][sample["doc_id"]] = text
        result["generation_seed"][sample["doc_id"]] = generation_seed
        result["generation_tokens"][sample["doc_id"]] = len(
            tokenizer(text, add_special_tokens=False)["input_ids"]
        )
        nll, _ = _target_nll(model, sample, device=device)
        result["nll"][sample["doc_id"]] = nll
        if index % 32 == 0:
            print(f"phase=assessment seed={seed} completed={index}/{len(rows)}", flush=True)
    return result


def _train_one_epoch(
    model: Any,
    lora_layers: Sequence[Any],
    samples: list[dict[str, Any]],
    seed: int,
    *,
    deadline: float,
) -> list[float]:
    torch, _ = _import_torch()
    parameters = _reset_adapter(model, lora_layers, seed)
    optimizer = torch.optim.AdamW(
        parameters,
        lr=LEARNING_RATE,
        betas=ADAM_BETAS,
        eps=ADAM_EPSILON,
        weight_decay=WEIGHT_DECAY,
    )
    device = torch.device("mps")
    base = model.get_base_model()
    losses: list[float] = []
    order = list(samples)
    random.Random(seed ^ 0x5A17).shuffle(order)
    if len(order) != ARM_EXAMPLES or len(order) % TRAINING_BATCH_SIZE != 0:
        raise ExperimentError("V8 arm examples must be a complete fixed-size batch roster")
    total_steps = len(order) // TRAINING_BATCH_SIZE
    model.train()
    model.config.use_cache = False
    base.config.use_cache = False
    base.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    for step_index, offset in enumerate(range(0, len(order), TRAINING_BATCH_SIZE), start=1):
        if time.monotonic() > deadline:
            raise ExperimentError("480-minute wall-clock limit reached during adapter training")
        batch = order[offset : offset + TRAINING_BATCH_SIZE]
        token_count = sum(len(sample["target_ids"]) for sample in batch)
        if token_count < 1:
            raise ExperimentError("V8 gradient-accumulation group has no assistant target tokens")
        optimizer.zero_grad(set_to_none=True)
        summed_loss = 0.0
        for sample in batch:
            loss_sum, target_count = _assistant_target_loss_sum(model, sample, device)
            if not bool(torch.isfinite(loss_sum).item()):
                raise ExperimentError("non-finite assistant-only training loss in V8 microbatch")
            (loss_sum / token_count).backward()
            summed_loss += float(loss_sum.detach().cpu())
            del loss_sum
        if time.monotonic() > deadline:
            raise ExperimentError("480-minute wall-clock limit reached during adapter training")
        torch.nn.utils.clip_grad_norm_(parameters, max_norm=MAX_GRAD_NORM)
        optimizer.step()
        if time.monotonic() > deadline:
            raise ExperimentError("480-minute wall-clock limit reached during adapter training")
        losses.append(summed_loss / token_count)
        torch.mps.synchronize()
        torch.mps.empty_cache()
        print(
            f"phase=training seed={seed} completed_steps={step_index}/{total_steps} "
            f"completed_examples={offset + len(batch)}/{len(order)}",
            flush=True,
        )
    model.eval()
    base.gradient_checkpointing_disable()
    return losses


def _save_adapter(model: Any, directory: Path) -> dict[str, Any]:
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    model.save_pretrained(directory, safe_serialization=True)
    _secure_private_directories(directory)
    files = _adapter_manifest(directory)
    return {"files": files, "sha256": _tree_digest(files)}


def _mean(values: Sequence[float]) -> float:
    if not values or any(not math.isfinite(float(value)) for value in values):
        raise ExperimentError("mean input is empty or non-finite")
    return sum(float(value) for value in values) / len(values)


def _bootstrap_interval(values: list[float]) -> tuple[float, float]:
    if not values or any(not math.isfinite(value) for value in values):
        raise ExperimentError("bootstrap input is empty or non-finite")
    generator = random.Random(BOOTSTRAP_SEED)
    means = sorted(
        sum(values[generator.randrange(len(values))] for _ in values) / len(values)
        for _ in range(BOOTSTRAP_RESAMPLES)
    )
    return means[int(0.025 * len(means))], means[min(len(means) - 1, int(0.975 * len(means)))]


def _mechanistic_row(model: Any, sample: dict[str, Any], device: Any) -> dict[str, Any]:
    with model.disable_adapter():
        base_nll, base_hidden = _target_nll(model, sample, device=device, capture_layer=True)
    if base_hidden is None:
        raise ExperimentError("base residual-stream capture is missing")
    adapted_nll, adapted_hidden = _target_nll(model, sample, device=device, capture_layer=True)
    if adapted_hidden is None:
        raise ExperimentError("adapted residual-stream capture is missing")
    identity_nll, _ = _target_nll(model, sample, device=device, layer_patch=adapted_hidden)
    base_patch_nll, _ = _target_nll(model, sample, device=device, layer_patch=base_hidden)
    return {
        "doc_id": sample["doc_id"],
        "base_nll": base_nll,
        "adapted_nll": adapted_nll,
        "identity_patch_nll": identity_nll,
        "base_activation_patch_nll": base_patch_nll,
        "identity_patch_abs_error": abs(identity_nll - adapted_nll),
        "activation_patch_delta_nll": base_patch_nll - adapted_nll,
    }


def _rouge_rows(generations: Mapping[str, str], references: Mapping[str, str]) -> dict[str, dict[str, float]]:
    try:
        from rouge_score.rouge_scorer import RougeScorer
    except ImportError as exc:
        raise ExperimentError("Google rouge-score is required for standardized evaluation") from exc
    scorer = RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=False)
    output: dict[str, dict[str, float]] = {}
    for doc_id, prediction in generations.items():
        if doc_id not in references:
            raise ExperimentError(f"generation lacks a frozen reference: {doc_id}")
        score = scorer.score(references[doc_id], prediction)
        output[doc_id] = {
            "rouge1": float(score["rouge1"].fmeasure),
            "rouge2": float(score["rouge2"].fmeasure),
            "rougeL": float(score["rougeL"].fmeasure),
        }
    return output


def _length_strata(fit_pool: Sequence[Mapping[str, Any]]) -> list[list[Mapping[str, Any]]]:
    if len(fit_pool) != FIT_POOL_SIZE or FIT_POOL_SIZE % LENGTH_BIN_COUNT != 0:
        raise ExperimentError("V8 fit pool cannot be divided into the frozen equal-size length strata")
    ordered = sorted(
        fit_pool,
        key=lambda row: (int(row["prompt_token_count"]) + int(row["target_token_count"]), str(row["doc_id"])),
    )
    bins = [ordered[start : start + LENGTH_BIN_SIZE] for start in range(0, len(ordered), LENGTH_BIN_SIZE)]
    if len(bins) != LENGTH_BIN_COUNT or any(len(rows) != LENGTH_BIN_SIZE for rows in bins):
        raise ExperimentError("V8 fit length strata are incomplete")
    return bins


def _selection_rosters(
    fit_pool: Sequence[Mapping[str, Any]],
    fit_nll_by_id: Mapping[str, float],
    seed: int,
) -> dict[str, list[Mapping[str, Any]]]:
    by_id = {str(row["doc_id"]): row for row in fit_pool}
    if set(fit_nll_by_id) != set(by_id):
        raise ExperimentError("fit-pool NLL table does not bind the complete V8 roster")
    global_loss_ids = sorted(by_id, key=lambda identifier: (-float(fit_nll_by_id[identifier]), identifier))[:ARM_EXAMPLES]
    bins = _length_strata(fit_pool)
    stratified_loss_rows: list[Mapping[str, Any]] = []
    for rows in bins:
        ranked = sorted(rows, key=lambda row: (-float(fit_nll_by_id[str(row["doc_id"])]), str(row["doc_id"])))
        stratified_loss_rows.extend(ranked[:STRATIFIED_PER_BIN])
    global_random_rows = random.Random(seed).sample(list(fit_pool), ARM_EXAMPLES)
    stratified_rng = random.Random(seed ^ STRATIFIED_RANDOM_SEED_XOR)
    stratified_random_rows = [
        row
        for rows in bins
        for row in stratified_rng.sample(list(rows), STRATIFIED_PER_BIN)
    ]
    result = {
        "global_loss_selected": [by_id[identifier] for identifier in global_loss_ids],
        "global_random_control": global_random_rows,
        "length_stratified_loss_selected": stratified_loss_rows,
        "length_stratified_random_control": stratified_random_rows,
    }
    if any(len(rows) != ARM_EXAMPLES for rows in result.values()):
        raise ExperimentError("one or more V8 training rosters have the wrong size")
    for name in ("length_stratified_loss_selected", "length_stratified_random_control"):
        counts = Counter(
            index
            for index, group in enumerate(bins)
            for row in result[name]
            if str(row["doc_id"]) in {str(item["doc_id"]) for item in group}
        )
        if counts != Counter({index: STRATIFIED_PER_BIN for index in range(LENGTH_BIN_COUNT)}):
            raise ExperimentError(f"{name} does not meet the frozen per-bin allocation")
    return result


def _report_from_private(
    private: Mapping[str, Any],
    references: Mapping[str, str],
    *,
    private_run_sha256: str,
) -> dict[str, Any]:
    assessment_ids = private["assessment_ids"]
    arms = private["arms"]
    expected_seeds = list(SEEDS)
    for arm_name in ALL_ARMS:
        repeats = arms.get(arm_name)
        if not isinstance(repeats, list) or len(repeats) != len(SEEDS):
            raise ExperimentError(f"assessment seed roster is incomplete: {arm_name}")
        if [item.get("seed") for item in repeats] != expected_seeds:
            raise ExperimentError(f"assessment seeds differ from the frozen roster: {arm_name}")
        for repeat in repeats:
            if set(repeat.get("generation", {})) != set(assessment_ids):
                raise ExperimentError(f"generation assessment cells are incomplete: {arm_name}")
            if set(repeat.get("nll", {})) != set(assessment_ids):
                raise ExperimentError(f"NLL assessment cells are incomplete: {arm_name}")
            if set(repeat.get("generation_seed", {})) != set(assessment_ids):
                raise ExperimentError(f"generation seed cells are incomplete: {arm_name}")
            if set(repeat.get("generation_tokens", {})) != set(assessment_ids):
                raise ExperimentError(f"generation token counts are incomplete: {arm_name}")
            if any(not isinstance(text, str) or not text.strip() for text in repeat["generation"].values()):
                raise ExperimentError(f"empty assessment generation: {arm_name}")
            if any(not math.isfinite(float(value)) for value in repeat["nll"].values()):
                raise ExperimentError(f"non-finite assessment NLL: {arm_name}")
            if arm_name != "untouched_base" and not math.isfinite(float(repeat.get("train_loss_mean", float("nan")))):
                raise ExperimentError(f"non-finite training loss: {arm_name}")

    rouge: dict[str, dict[int, dict[str, dict[str, float]]]] = {}
    for arm_name in ALL_ARMS:
        rouge[arm_name] = {}
        for repeat in arms[arm_name]:
            rouge[arm_name][int(repeat["seed"])] = _rouge_rows(repeat["generation"], references)
    metric_means: dict[str, dict[str, float]] = {metric: {} for metric in ("rouge1", "rouge2", "rougeL")}
    for metric in metric_means:
        for arm_name in ALL_ARMS:
            values = [
                rouge[arm_name][seed][doc_id][metric]
                for seed in SEEDS
                for doc_id in assessment_ids
            ]
            if any(not math.isfinite(value) for value in values):
                raise ExperimentError(f"non-finite {metric} score for {arm_name}")
            metric_means[metric][arm_name] = _mean(values)

    def paired_document_effect(selected_arm: str, control_arm: str) -> list[float]:
        return [
            _mean([rouge[selected_arm][seed][doc_id]["rougeL"] for seed in SEEDS])
            - _mean([rouge[control_arm][seed][doc_id]["rougeL"] for seed in SEEDS])
            for doc_id in assessment_ids
        ]

    primary_effects = paired_document_effect(PRIMARY_SELECTED_ARM, PRIMARY_CONTROL_ARM)
    primary_effect = _mean(primary_effects)
    primary_ci = _bootstrap_interval(primary_effects)
    global_effects = paired_document_effect("global_loss_selected", "global_random_control")
    global_effect = _mean(global_effects)
    global_ci = _bootstrap_interval(global_effects)
    base_nll = _mean([float(value) for repeat in arms["untouched_base"] for value in repeat["nll"].values()])
    selected_nll = _mean([float(value) for repeat in arms[PRIMARY_SELECTED_ARM] for value in repeat["nll"].values()])
    reference_token_counts = private["reference_token_counts"]
    if set(reference_token_counts) != set(assessment_ids):
        raise ExperimentError("assessment reference-token roster is incomplete")
    output_token_counts = [
        int(value)
        for arm_name in ALL_ARMS
        for repeat in arms[arm_name]
        for value in repeat["generation_tokens"].values()
    ]
    reference_counts = [
        int(reference_token_counts[doc_id])
        for _arm in ALL_ARMS
        for _seed in SEEDS
        for doc_id in assessment_ids
    ]
    output_reference_ratio = _mean(output_token_counts) / _mean(reference_counts)
    mechanism = private["mechanistic"]
    expected_mechanism = {
        (arm_name, seed, doc_id)
        for arm_name in TRAINED_ARMS
        for seed in SEEDS
        for doc_id in assessment_ids[:MECHANISTIC_ROWS]
    }
    observed_mechanism = {(row.get("arm"), row.get("seed"), row.get("doc_id")) for row in mechanism}
    if observed_mechanism != expected_mechanism or len(mechanism) != len(expected_mechanism):
        raise ExperimentError("V8 layer diagnostic roster is incomplete or duplicated")
    max_identity_error = max(float(row["identity_patch_abs_error"]) for row in mechanism)
    if max_identity_error > IDENTITY_PATCH_TOLERANCE:
        raise ExperimentError("V8 layer activation identity-patch control failed")
    patch_values = [
        float(row[key])
        for row in mechanism
        for key in ("identity_patch_abs_error", "activation_patch_delta_nll", "base_nll", "adapted_nll", "base_activation_patch_nll")
    ]
    if any(not math.isfinite(value) for value in patch_values):
        raise ExperimentError("V8 layer diagnostic contains a non-finite value")
    patch_denominators = [
        float(row["base_nll"]) - float(row["adapted_nll"])
        for row in mechanism
        if abs(float(row["base_nll"]) - float(row["adapted_nll"])) > 1e-12
    ]
    patch_fraction = (
        _mean([
            (float(row["base_activation_patch_nll"]) - float(row["adapted_nll"]))
            / (float(row["base_nll"]) - float(row["adapted_nll"]))
            for row in mechanism
            if abs(float(row["base_nll"]) - float(row["adapted_nll"])) > 1e-12
        ])
        if patch_denominators
        else None
    )
    complete_outputs = all(
        isinstance(text, str) and bool(text.strip())
        for arm_name in ALL_ARMS
        for repeat in arms[arm_name]
        for text in repeat["generation"].values()
    )
    complete_adapter_receipts = all(
        bool(repeat.get("adapter_sha256")) and bool(repeat.get("adapter_files"))
        for arm_name in TRAINED_ARMS
        for repeat in arms[arm_name]
    )
    candidate = (
        primary_effect >= MIN_EFFECT
        and primary_ci[0] > 0.0
        and metric_means["rougeL"][PRIMARY_SELECTED_ARM] >= metric_means["rougeL"]["untouched_base"]
        and selected_nll - base_nll <= 0.05
        and complete_outputs
        and complete_adapter_receipts
        and max_identity_error <= IDENTITY_PATCH_TOLERANCE
    )
    per_seed = [
        {
            "seed": seed,
            **{
                f"{arm_name}_rouge_l": _mean([rouge[arm_name][seed][doc_id]["rougeL"] for doc_id in assessment_ids])
                for arm_name in ALL_ARMS
            },
        }
        for seed in SEEDS
    ]
    training_token_totals = {
        arm_name: [
            {
                "seed": repeat["seed"],
                "source_tokens": repeat["training_source_tokens"],
                "assistant_target_tokens": repeat["training_target_tokens"],
                "combined_tokens": repeat["training_source_tokens"] + repeat["training_target_tokens"],
            }
            for repeat in arms[arm_name]
        ]
        for arm_name in TRAINED_ARMS
    }
    return {
        "schema_version": "aligned-rsi-billsum-length-matched-curriculum-v8-evaluation-report",
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "run_id": private["run_id"],
        "assurance_level": "PENDING_LOCAL_VERIFICATION",
        "reviewer_status": "LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT",
        "reproducibility_status": "SINGLE_LOCAL_EXECUTION",
        "local_acceptance": "PENDING_LOCAL_VERIFICATION",
        "independent_acceptance": False,
        "candidate_disposition": "Candidate" if candidate else "NoCandidate",
        "claim_ceiling": CLAIM_CEILING,
        "model": {"repo_id": MODEL_ID, "revision": MODEL_REVISION},
        "dataset": {"repo_id": DATASET_ID, "revision": DATASET_REVISION, "included_splits": ["train", "test"], "excluded_splits": ["ca_test"]},
        "source_revision": private["source_revision"],
        "source_worktree_dirty": private["source_worktree_dirty"],
        "source_digests": private["source_digests"],
        "source_manifest_sha256": sha256_bytes(canonical_bytes(private["source_digests"])),
        "protocol_sha256": private["protocol_sha256"],
        "protocol_manifest_sha256": private["manifest_sha256"],
        "frozen_protocol": private["protocol_snapshot"],
        "prepared_inputs_sha256": private["prepared_inputs_sha256"],
        "model_weights_manifest_sha256": private["model_weights_manifest_sha256"],
        "private_run_sha256": private_run_sha256,
        "runtime": private["runtime"],
        "device": private["device"],
        "cohorts": {
            "fit_pool_documents": len(private["fit_pool_ids"]),
            "assessment_documents": len(assessment_ids),
            "fit_roster_sha256": sha256_bytes(canonical_bytes(private["fit_pool_ids"])),
            "assessment_roster_sha256": sha256_bytes(canonical_bytes(assessment_ids)),
            "v1_excluded": private["v1_excluded"],
            "prior_rosters": private["prior_rosters"],
            "prior_union": private["prior_union"],
            "eligible_after_prior_exclusions": private["eligible_after_prior_exclusions"],
            "duplicate_source_groups_excluded": private["duplicate_source_groups_excluded"],
            "fresh_fit_assessment_overlap": 0,
        },
        "counts": {
            "training_seeds": list(SEEDS),
            "trained_arms": list(TRAINED_ARMS),
            "training_examples_per_arm_per_seed": ARM_EXAMPLES,
            "training_steps_per_updated_arm_per_seed": ARM_EXAMPLES // TRAINING_BATCH_SIZE,
            "total_optimizer_steps": len(TRAINED_ARMS) * len(SEEDS) * (ARM_EXAMPLES // TRAINING_BATCH_SIZE),
            "held_out_completions": len(output_token_counts),
            "mechanistic_rows": len(mechanism),
        },
        "primary": {
            "metric": "paired_document_bootstrap_rougeL_length_stratified_loss_minus_length_stratified_random",
            "mean_effect": primary_effect,
            "ci95_lower": primary_ci[0],
            "ci95_upper": primary_ci[1],
            "minimum_meaningful_effect": MIN_EFFECT,
            "length_stratified_loss_selected_mean_rouge_l_f1": metric_means["rougeL"][PRIMARY_SELECTED_ARM],
            "length_stratified_random_control_mean_rouge_l_f1": metric_means["rougeL"][PRIMARY_CONTROL_ARM],
            "untouched_base_mean_rouge_l_f1": metric_means["rougeL"]["untouched_base"],
            "length_stratified_loss_selected_minus_base_mean_target_nll": selected_nll - base_nll,
        },
        "secondary": {
            "rouge1_f1_by_arm": metric_means["rouge1"],
            "rouge2_f1_by_arm": metric_means["rouge2"],
            "rougeL_f1_by_arm": metric_means["rougeL"],
            "global_loss_minus_global_random_mean_rouge_l": global_effect,
            "global_loss_minus_global_random_ci95": [global_ci[0], global_ci[1]],
            "mean_output_reference_token_ratio": output_reference_ratio,
            "identity_patch_max_abs_nll_error": max_identity_error,
            "mean_activation_patch_delta_nll": _mean([float(row["activation_patch_delta_nll"]) for row in mechanism]),
            "mean_fraction_base_activation_recovered": patch_fraction,
            "training_token_totals_by_arm_and_seed": training_token_totals,
            "complete_finite_outputs": complete_outputs,
            "complete_adapter_receipts": complete_adapter_receipts,
            "per_seed_rouge_l": per_seed,
        },
        "resources": private["resources"],
        "cost": {"paid_provider_calls": False, "provider_spend": "none_no_provider_calls", "local_compute_cost": "not_measured", "energy_measurement": "not_measured"},
        "custody": {
            "pinned_model_and_dataset_external_owner_only": True,
            "raw_rows_generations_and_adapter_weights_external_owner_only": True,
            "repository_release_aggregate_only": True,
            "automatic_expiry": False,
        },
        "next_blocked_authority_gate": "No independent acceptance requested; any claim above this local qualification ceiling requires a fresh evidence packet and applicable authority.",
        "nonclaims": [
            "independent_acceptance",
            "general_alignment",
            "general_recursive_self_improvement",
            "feature_level_mechanistic_explanation",
            "benchmark_leaderboard_result",
            "production_readiness",
            "user_data_evidence",
            "clean_second_environment_reproduction",
        ],
    }





def _write_run_status(run_root: Path, run_id: str, status: str, phase: str, error: str | None = None) -> None:
    payload: dict[str, Any] = {
        "schema_version": "aligned-rsi-billsum-chat-template-v8-run-status",
        "state_slice": STATE_SLICE,
        "run_id": run_id,
        "status": status,
        "phase": phase,
        "updated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if error is not None:
        payload["error"] = error
    save_json(run_root / "execution_status.json", payload)


def run() -> dict[str, Any]:
    """Execute the single frozen local-only V8 fit and held-out evaluation."""
    manifest = _verify_protocol()
    prepared = _validate_prepared()
    if RELEASE_ROOT.exists():
        raise ExperimentError("refusing to overwrite an existing V8 release directory")
    os.environ.update({
        "HF_HUB_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
    })
    torch, _ = _import_torch()
    start = time.monotonic()
    deadline = start + WALL_CLOCK_LIMIT_SECONDS
    run_id = dt.datetime.now(dt.timezone.utc).strftime("run-%Y%m%dT%H%M%S%fZ")
    run_root = RUNS_ROOT / run_id
    run_root.mkdir(parents=True, mode=0o700, exist_ok=False)
    run_root.chmod(0o700)
    _write_run_status(run_root, run_id, "RUNNING", "roster_and_token_validation")
    source_digests = _source_manifest()
    train_rows = _load_federal_rows("train")
    test_rows = _load_federal_rows("test")
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ROOT, local_files_only=True, trust_remote_code=False)
        fresh = _fresh_rosters(tokenizer, train_rows, test_rows)
        if fresh["fit_ids"] != prepared["fit_ids"] or fresh["assessment_ids"] != prepared["assessment_ids"]:
            raise ExperimentError("V8 cohort rosters differ from the frozen prepared-input receipt")
        row_by_id = {row["doc_id"]: row for row in (*train_rows, *test_rows)}
        fit_pool = [_tokenize_row(tokenizer, row_by_id[identifier]) for identifier in prepared["fit_ids"]]
        assessment = [_tokenize_row(tokenizer, row_by_id[identifier]) for identifier in prepared["assessment_ids"]]
        if any(len(row["prompt_ids"]) > MAX_SOURCE_TOKENS for row in (*fit_pool, *assessment)):
            raise ExperimentError("V8 prompt token limit exceeded without truncation")
        if any(len(row["target_ids"]) > MAX_TARGET_TOKENS for row in (*fit_pool, *assessment)):
            raise ExperimentError("V8 assistant target token limit exceeded without truncation")
        _length_strata(fit_pool)
        _write_run_status(run_root, run_id, "RUNNING", "local_model_loading")
        print(f"run_id={run_id} phase=model_load device=Apple_MPS fit={len(fit_pool)} assessment={len(assessment)}", flush=True)
        model, tokenizer, lora_layers, device_name = _create_model_and_tokenizer(MODEL_ROOT)
        model_weights_sha256 = _tree_digest(prepared["model_files"])
        device = torch.device("mps")
        _write_run_status(run_root, run_id, "RUNNING", "fit_loss_scoring")
        fit_nll_by_id: dict[str, float] = {}
        with model.disable_adapter():
            for index, sample in enumerate(fit_pool, start=1):
                if time.monotonic() > deadline:
                    raise ExperimentError("480-minute wall-clock limit reached during fit-pool scoring")
                fit_nll_by_id[sample["doc_id"]], _ = _target_nll(model, sample, device=device)
                if not math.isfinite(fit_nll_by_id[sample["doc_id"]]):
                    raise ExperimentError("non-finite untouched-base fit-pool NLL")
                if index % 64 == 0:
                    print(f"phase=fit_loss completed={index}/{len(fit_pool)}", flush=True)
        selection_rosters = {seed: _selection_rosters(fit_pool, fit_nll_by_id, seed) for seed in SEEDS}
        references = {sample["doc_id"]: sample["summary"] for sample in assessment}
        reference_token_counts = {sample["doc_id"]: sample["reference_token_count"] for sample in assessment}
        mechanistic_assessment = assessment[:MECHANISTIC_ROWS]
        arms: dict[str, Any] = {arm_name: [] for arm_name in ALL_ARMS}
        mechanistic: list[dict[str, Any]] = []

        _write_run_status(run_root, run_id, "RUNNING", "untouched_base_assessment")
        for seed in SEEDS:
            if time.monotonic() > deadline:
                raise ExperimentError("480-minute wall-clock limit reached before untouched-base assessment")
            with model.disable_adapter():
                base_eval = _evaluate_arm(model, tokenizer, assessment, device, seed=seed, deadline=deadline)
            arms["untouched_base"].append({
                "seed": seed,
                "selection_ids": [],
                "adapter_sha256": None,
                "adapter_files": [],
                "train_steps": 0,
                "train_loss_mean": None,
                "training_source_tokens": 0,
                "training_target_tokens": 0,
                **base_eval,
            })

        for seed in SEEDS:
            for arm_name in TRAINED_ARMS:
                if time.monotonic() > deadline:
                    raise ExperimentError("480-minute wall-clock limit reached before the locked assessment completed")
                selected_rows = list(selection_rosters[seed][arm_name])
                _write_run_status(run_root, run_id, "RUNNING", f"train_{arm_name}_seed_{seed}")
                print(f"run_id={run_id} phase=train arm={arm_name} seed={seed} rows={len(selected_rows)}", flush=True)
                train_losses = _train_one_epoch(model, lora_layers, selected_rows, seed, deadline=deadline)
                adapter = _save_adapter(model, run_root / "adapters" / f"{arm_name}-seed-{seed}")
                _write_run_status(run_root, run_id, "RUNNING", f"assessment_{arm_name}_seed_{seed}")
                evaluation = _evaluate_arm(model, tokenizer, assessment, device, seed=seed, deadline=deadline)
                arms[arm_name].append({
                    "seed": seed,
                    "selection_ids": [row["doc_id"] for row in selected_rows],
                    "adapter_sha256": adapter["sha256"],
                    "adapter_files": adapter["files"],
                    "train_loss_mean": _mean(train_losses),
                    "train_steps": len(train_losses),
                    "training_source_tokens": sum(int(row["prompt_token_count"]) for row in selected_rows),
                    "training_target_tokens": sum(int(row["target_token_count"]) for row in selected_rows),
                    **evaluation,
                })
                for sample in mechanistic_assessment:
                    if time.monotonic() > deadline:
                        raise ExperimentError("480-minute wall-clock limit reached during residual intervention")
                    diagnostic = _mechanistic_row(model, sample, device)
                    diagnostic.update({"arm": arm_name, "seed": seed})
                    mechanistic.append(diagnostic)

        if tree_manifest(MODEL_ROOT) != prepared["model_files"]:
            raise ExperimentError("immutable base checkpoint bytes changed during local adaptation")
        elapsed = time.monotonic() - start
        usage = resource.getrusage(resource.RUSAGE_SELF)
        resources = {
            "elapsed_seconds": elapsed,
            "wall_clock_limit_seconds": WALL_CLOCK_LIMIT_SECONDS,
            "peak_process_rss_bytes": int(usage.ru_maxrss),
            "mps_current_allocated_bytes": int(torch.mps.current_allocated_memory()),
            "mps_driver_allocated_bytes": int(torch.mps.driver_allocated_memory()),
            "energy_measurement": "not_measured",
        }
        private = {
            "schema_version": "aligned-rsi-billsum-length-matched-curriculum-v8-private-run",
            "protocol_id": PROTOCOL_ID,
            "state_slice": STATE_SLICE,
            "governance_slice": GOVERNANCE_SLICE,
            "run_id": run_id,
            "protocol_sha256": sha256_file(PROTOCOL_PATH),
            "manifest_sha256": sha256_file(MANIFEST_PATH),
            "protocol_snapshot": manifest,
            "runner_sha256": sha256_file(Path(__file__).resolve()),
            "focused_tests_sha256": sha256_file(TEST_PATH),
            "requirements_lock_sha256": sha256_file(LOCK_PATH),
            "source_revision": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.strip(),
            "source_worktree_dirty": bool(subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.strip()),
            "source_digests": source_digests,
            "prepared_inputs_sha256": prepared["prepared_inputs_sha256"],
            "model_weights_manifest_sha256": model_weights_sha256,
            "base_checkpoint_unchanged": True,
            "device": device_name,
            "runtime": manifest["runtime"],
            "fit_pool_ids": prepared["fit_ids"],
            "assessment_ids": prepared["assessment_ids"],
            "v1_excluded": prepared["v1_excluded"],
            "prior_rosters": prepared["prior_rosters"],
            "prior_union": prepared["prior_union"],
            "eligible_after_prior_exclusions": prepared["eligible_after_prior_exclusions"],
            "duplicate_source_groups_excluded": prepared["duplicate_source_groups_excluded"],
            "fit_nll_by_id": fit_nll_by_id,
            "arms": arms,
            "mechanistic": mechanistic,
            "reference_token_counts": reference_token_counts,
            "resources": resources,
        }
        private_path = run_root / "private_run.json"
        save_json(private_path, private)
        report = _report_from_private(private, references, private_run_sha256=sha256_file(private_path))
        RELEASE_ROOT.mkdir(parents=True, exist_ok=False)
        save_json(PUBLIC_REPORT_PATH, report, private=False)
        release_manifest = {
            "schema_version": "aligned-rsi-billsum-length-matched-curriculum-v8-aggregate-release",
            "state_slice": STATE_SLICE,
            "files": [{"path": "evaluation_report.json", "sha256": sha256_file(PUBLIC_REPORT_PATH)}],
            "raw_data_included": False,
            "model_weights_included": False,
            "generated_summaries_included": False,
            "adapter_weights_included": False,
            "independent_acceptance": False,
        }
        save_json(RELEASE_ROOT / "release_manifest.json", release_manifest, private=False)
        _write_run_status(run_root, run_id, "COMPLETE", "verified_pending_local_acceptance")
        _secure_private_directories(OWNER_ROOT)
        return report
    except Exception as exc:
        _write_run_status(run_root, run_id, "FAILED", "local_execution_failed", error=f"{type(exc).__name__}: {exc}")
        raise





def verify() -> dict[str, Any]:
    """Rebuild the frozen V8 aggregate report and issue a local-only receipt."""
    protocol_manifest = _verify_protocol()
    prepared = _validate_prepared()
    report = load_json(PUBLIC_REPORT_PATH)
    if report.get("state_slice") != STATE_SLICE or report.get("claim_ceiling") != CLAIM_CEILING:
        raise ExperimentError("public V8 report identity mismatch")
    run_id = report.get("run_id")
    if not isinstance(run_id, str) or not run_id.startswith("run-"):
        raise ExperimentError("public V8 report run identifier is invalid")
    run_root = RUNS_ROOT / run_id
    _check_private_tree(OWNER_ROOT)
    status = load_json(run_root / "execution_status.json")
    if status.get("status") not in {"COMPLETE", "LOCAL_ACCEPTED"}:
        raise ExperimentError("V8 execution status is not complete")
    private_path = run_root / "private_run.json"
    private_run_sha = sha256_file(private_path)
    private = load_json(private_path)
    if private.get("protocol_id") != PROTOCOL_ID or private.get("state_slice") != STATE_SLICE:
        raise ExperimentError("V8 private run identity mismatch")
    if canonical_bytes(private.get("protocol_snapshot")) != canonical_bytes(protocol_manifest):
        raise ExperimentError("V8 private run protocol snapshot differs from the frozen contract")
    if private.get("run_id") != run_id or private.get("prepared_inputs_sha256") != prepared.get("prepared_inputs_sha256"):
        raise ExperimentError("V8 private run does not bind the current run and prepared inputs")
    if private.get("protocol_sha256") != sha256_file(PROTOCOL_PATH) or private.get("manifest_sha256") != sha256_file(MANIFEST_PATH):
        raise ExperimentError("V8 protocol or machine-contract digest differs from the frozen run")
    if private.get("runner_sha256") != sha256_file(Path(__file__).resolve()):
        raise ExperimentError("V8 runner digest differs from the frozen run")
    if private.get("focused_tests_sha256") != sha256_file(TEST_PATH) or private.get("requirements_lock_sha256") != sha256_file(LOCK_PATH):
        raise ExperimentError("V8 focused-test or dependency-lock digest differs from the frozen run")
    if private.get("source_digests") != _source_manifest():
        raise ExperimentError("one or more frozen V8 source or instruction files changed after execution")
    if private.get("base_checkpoint_unchanged") is not True:
        raise ExperimentError("V8 immutable-base receipt is missing")
    if private.get("model_weights_manifest_sha256") != prepared.get("model_files_sha256"):
        raise ExperimentError("V8 private run model digest differs from prepared model bytes")
    if tree_manifest(MODEL_ROOT) != prepared.get("model_files"):
        raise ExperimentError("cached V8 base model changed after execution")
    for key in ("fit_ids", "assessment_ids", "v1_excluded", "prior_rosters", "prior_union", "eligible_after_prior_exclusions", "duplicate_source_groups_excluded"):
        private_key = {"fit_ids": "fit_pool_ids"}.get(key, key)
        if private.get(private_key) != prepared.get(key):
            raise ExperimentError(f"V8 private run {key} differs from the prepared-input receipt")
    fit_ids = prepared["fit_ids"]
    assessment_ids = prepared["assessment_ids"]
    fit_losses = private.get("fit_nll_by_id", {})
    if set(fit_losses) != set(fit_ids) or any(not math.isfinite(float(value)) for value in fit_losses.values()):
        raise ExperimentError("V8 fit-pool teacher-forced NLL table is incomplete or non-finite")
    train_rows = _load_federal_rows("train")
    train_by_id = {row["doc_id"]: row for row in train_rows}
    if any(identifier not in train_by_id for identifier in fit_ids):
        raise ExperimentError("V8 fit roster is absent from the pinned federal train split")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ROOT, local_files_only=True, trust_remote_code=False)
    fit_pool = [_tokenize_row(tokenizer, train_by_id[identifier]) for identifier in fit_ids]
    expected_rosters = {seed: _selection_rosters(fit_pool, fit_losses, seed) for seed in SEEDS}
    for arm_name in ALL_ARMS:
        repeats = private.get("arms", {}).get(arm_name)
        if not isinstance(repeats, list) or len(repeats) != len(SEEDS):
            raise ExperimentError(f"V8 private assessment repeats are incomplete: {arm_name}")
        if [repeat.get("seed") for repeat in repeats] != list(SEEDS):
            raise ExperimentError(f"V8 private assessment seeds differ for {arm_name}")
        for repeat, seed in zip(repeats, SEEDS, strict=True):
            if arm_name == "untouched_base":
                if repeat.get("selection_ids") != [] or repeat.get("train_steps") != 0 or repeat.get("adapter_sha256") is not None:
                    raise ExperimentError("V8 untouched-base arm contains an update or adapter")
            else:
                expected_rows = expected_rosters[seed][arm_name]
                expected_ids = [row["doc_id"] for row in expected_rows]
                if repeat.get("selection_ids") != expected_ids:
                    raise ExperimentError(f"V8 training roster differs for {arm_name} seed {seed}")
                if repeat.get("train_steps") != ARM_EXAMPLES // TRAINING_BATCH_SIZE:
                    raise ExperimentError(f"V8 optimizer step count differs for {arm_name} seed {seed}")
                if not math.isfinite(float(repeat.get("train_loss_mean", float("nan")))):
                    raise ExperimentError(f"V8 training loss is non-finite for {arm_name} seed {seed}")
                if repeat.get("training_source_tokens") != sum(int(row["prompt_token_count"]) for row in expected_rows):
                    raise ExperimentError(f"V8 source-token budget differs for {arm_name} seed {seed}")
                if repeat.get("training_target_tokens") != sum(int(row["target_token_count"]) for row in expected_rows):
                    raise ExperimentError(f"V8 target-token budget differs for {arm_name} seed {seed}")
                adapter_dir = run_root / "adapters" / f"{arm_name}-seed-{seed}"
                adapter_files = _adapter_manifest(adapter_dir)
                if adapter_files != repeat.get("adapter_files") or _tree_digest(adapter_files) != repeat.get("adapter_sha256"):
                    raise ExperimentError(f"V8 PEFT adapter files differ for {arm_name} seed {seed}")
            for field in ("generation", "nll", "generation_seed", "generation_tokens"):
                if set(repeat.get(field, {})) != set(assessment_ids):
                    raise ExperimentError(f"V8 {field} roster is incomplete for {arm_name} seed {seed}")
            if any(not isinstance(value, int) or value < 1 for value in repeat.get("generation_tokens", {}).values()):
                raise ExperimentError(f"V8 generation token counts are invalid for {arm_name} seed {seed}")
            if repeat.get("generation_seed") != {doc_id: _generation_seed(seed, doc_id) for doc_id in assessment_ids}:
                raise ExperimentError(f"V8 generation sampling seeds are not paired for {arm_name} seed {seed}")
    expected_mechanism = {
        (arm_name, seed, doc_id)
        for arm_name in TRAINED_ARMS
        for seed in SEEDS
        for doc_id in assessment_ids[:MECHANISTIC_ROWS]
    }
    observed_mechanism = {(row.get("arm"), row.get("seed"), row.get("doc_id")) for row in private.get("mechanistic", [])}
    if observed_mechanism != expected_mechanism or len(private.get("mechanistic", [])) != len(expected_mechanism):
        raise ExperimentError("V8 layer diagnostic roster differs from the frozen assessment subset")
    test_rows = _load_federal_rows("test")
    test_by_id = {row["doc_id"]: row for row in test_rows}
    if any(identifier not in test_by_id for identifier in assessment_ids):
        raise ExperimentError("V8 assessment roster is absent from the pinned federal test split")
    references = {identifier: test_by_id[identifier]["summary"] for identifier in assessment_ids}
    reconstructed = _report_from_private(private, references, private_run_sha256=private_run_sha)
    normalized_report = dict(report)
    normalized_report["assurance_level"] = "PENDING_LOCAL_VERIFICATION"
    normalized_report["local_acceptance"] = "PENDING_LOCAL_VERIFICATION"
    normalized_report.pop("local_acceptance_receipt_sha256", None)
    if canonical_bytes(reconstructed) != canonical_bytes(normalized_report):
        raise ExperimentError("V8 aggregate report does not reconstruct from the private run and pinned references")
    if report.get("reviewer_status") != "LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT" or report.get("independent_acceptance") is not False:
        raise ExperimentError("V8 reviewer status or authority claim exceeds the local-only boundary")
    release_manifest_path = RELEASE_ROOT / "release_manifest.json"
    release_manifest = load_json(release_manifest_path)
    if release_manifest.get("state_slice") != STATE_SLICE:
        raise ExperimentError("V8 aggregate release manifest state slice mismatch")
    files = release_manifest.get("files")
    if not isinstance(files, list) or not all(isinstance(item, dict) for item in files):
        raise ExperimentError("V8 aggregate release file list is invalid")
    expected_file_sets = ({"evaluation_report.json"}, {"evaluation_report.json", "local_acceptance.json"})
    if {item.get("path") for item in files} not in expected_file_sets:
        raise ExperimentError("V8 aggregate release contains an unapproved file")
    if {path.name for path in RELEASE_ROOT.iterdir()} != {item["path"] for item in files} | {"release_manifest.json"}:
        raise ExperimentError("V8 release directory contains unmanifested files")
    for item in files:
        path = RELEASE_ROOT / item.get("path", "")
        if not path.is_file() or sha256_file(path) != item.get("sha256"):
            raise ExperimentError("V8 aggregate release file digest mismatch")
    prohibited_flags = ("raw_data_included", "model_weights_included", "generated_summaries_included", "adapter_weights_included", "independent_acceptance")
    if any(release_manifest.get(flag) is not False for flag in prohibited_flags):
        raise ExperimentError("V8 release manifest includes prohibited data or an unsupported authority claim")
    core_sha = sha256_bytes(canonical_bytes(reconstructed))
    acceptance = {
        "schema_version": "aligned-rsi-billsum-length-matched-curriculum-v8-local-acceptance",
        "state_slice": STATE_SLICE,
        "governance_slice": GOVERNANCE_SLICE,
        "assurance_level": "INTERNAL_PASS",
        "reviewer_status": "LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT",
        "local_acceptance": "INTERNAL_PASS",
        "independent_acceptance": False,
        "claim_ceiling": CLAIM_CEILING,
        "candidate_disposition": reconstructed["candidate_disposition"],
        "accepted_report_core_sha256": core_sha,
        "private_run_sha256": private_run_sha,
        "prepared_inputs_sha256": prepared["prepared_inputs_sha256"],
        "source_manifest_sha256": reconstructed["source_manifest_sha256"],
        "source_digests": reconstructed["source_digests"],
    }
    acceptance_path = RELEASE_ROOT / "local_acceptance.json"
    if acceptance_path.exists() and report.get("local_acceptance") == "INTERNAL_PASS":
        if sha256_file(acceptance_path) != report.get("local_acceptance_receipt_sha256"):
            raise ExperimentError("existing V8 local acceptance receipt does not match the report")
        if canonical_bytes(load_json(acceptance_path)) != canonical_bytes(acceptance):
            raise ExperimentError("existing V8 local acceptance receipt differs from reconstructed evidence")
    save_json(acceptance_path, acceptance, private=False)
    report["assurance_level"] = "INTERNAL_PASS"
    report["local_acceptance"] = "INTERNAL_PASS"
    report["local_acceptance_receipt_sha256"] = sha256_file(acceptance_path)
    save_json(PUBLIC_REPORT_PATH, report, private=False)
    release_manifest["files"] = [
        {"path": "evaluation_report.json", "sha256": sha256_file(PUBLIC_REPORT_PATH)},
        {"path": "local_acceptance.json", "sha256": sha256_file(acceptance_path)},
    ]
    save_json(release_manifest_path, release_manifest, private=False)
    _write_run_status(run_root, run_id, "LOCAL_ACCEPTED", "local_verification_passed")
    _secure_private_directories(OWNER_ROOT)
    return {
        "valid": True,
        "assurance_level": "INTERNAL_PASS",
        "local_acceptance": "INTERNAL_PASS",
        "candidate_disposition": reconstructed["candidate_disposition"],
        "run_id": run_id,
        "claim_ceiling": CLAIM_CEILING,
        "independent_acceptance": False,
        "public_report_sha256": sha256_file(PUBLIC_REPORT_PATH),
        "private_run_sha256": private_run_sha,
    }





def _main() -> int:
    parser = argparse.ArgumentParser(description="local BillSum Qwen3 chat-template adaptation V8")
    parser.add_argument("command", choices=("prepare", "run", "verify"))
    args = parser.parse_args()
    actions = {"prepare": prepare, "run": run, "verify": verify}
    result = actions[args.command]()
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
