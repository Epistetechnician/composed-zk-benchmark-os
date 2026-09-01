#!/usr/bin/env python3
"""Independently validate the plasticity-guard adapter artifact.

State slice: continual-learning-plasticity-guard-reversible-adapter-v1.

This validator reads manifests, aggregate metrics, lock receipts, and adapter
files. It does not import or execute the experiment runner and does not load
the model, which keeps the validation path aggregate-only and independent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "continual-learning-plasticity-guard-reversible-adapter-v1"
WINDOW_TOKENS = 256
FIT_DOCUMENT_COUNT = 6
TUNE_DOCUMENT_COUNT = 3
ASSESSMENT_DOCUMENT_COUNT = 3
SEEDS = (1739, 1741)
ORDERS = {
    "forward": tuple(range(FIT_DOCUMENT_COUNT)),
    "reverse": tuple(reversed(range(FIT_DOCUMENT_COUNT))),
}
ARMS = ("fixed_cadence", "plasticity_guard")
TRAIN_ITERS = 3
TRAIN_ROWS = 4
TRAIN_NUM_LAYERS = 4
PRIMARY_EFFECT_THRESHOLD = 0.010
MIN_CURRENT_GAIN = 0.001
MAX_PROTECTED_DEGRADATION = 0.010
MAX_FORGETTING_FRACTION = 0.05
MAX_CALIBRATION_ECE_DELTA = 0.05
REPEAT_TOLERANCE = 1e-8
PARITY_TOLERANCE = 1e-5
ADAPTER_RESTORE_TOLERANCE = 1e-6
BOOTSTRAP_SEED = 20260828
BOOTSTRAP_REPLICATES = 10_000
CLAIM_CEILING = "LocalDevelopmentPlasticityGuardReversibleAdapterFeasibility"


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def model_manifest(model_path: Path) -> dict[str, Any]:
    files = []
    for path in sorted(
        candidate
        for candidate in model_path.rglob("*")
        if candidate.is_file()
        and not candidate.is_symlink()
        and ".cache" not in candidate.relative_to(model_path).parts
    ):
        files.append(
            {
                "path": path.relative_to(model_path).as_posix(),
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    body = {"model_name": model_path.name, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def artifact_root_is_external(root: Path) -> None:
    resolved = root.resolve()
    repo = REPO_ROOT.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ValueError("artifact root must be outside the repository")


def bootstrap_interval(values: Sequence[float], seed: int, replicates: int) -> tuple[float, float]:
    if not values:
        raise ValueError("bootstrap requires non-empty values")
    rng = random.Random(seed)
    means = [
        sum(values[rng.randrange(len(values))] for _ in values) / len(values)
        for _ in range(replicates)
    ]
    means.sort()

    def percentile(percent: float) -> float:
        position = (len(means) - 1) * percent
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return means[lower]
        return means[lower] + (means[upper] - means[lower]) * (position - lower)

    return percentile(0.025), percentile(0.975)


def validate(root: Path, model_path: Path) -> dict[str, Any]:
    root = root.resolve()
    model_path = model_path.resolve()
    artifact_root_is_external(root)
    required = (
        "config.json",
        "input-manifest.json",
        "model-manifest.json",
        "qualification.json",
        "prediction-lock.json",
        "results.json",
        "receipt.json",
        "corpus/manifest.json",
    )
    for relative in required:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"required artifact is missing or unsafe: {relative}")

    config = read_json(root / "config.json")
    if config.get("state_slice") != STATE_SLICE:
        raise ValueError("config state slice mismatch")
    if config.get("claim_ceiling") != CLAIM_CEILING:
        raise ValueError("claim ceiling mismatch")
    config_digest = config.get("config_sha256")
    config_body = dict(config)
    config_body.pop("config_sha256", None)
    if config_digest != digest(config_body):
        raise ValueError("config digest mismatch")
    if config.get("network_access") is not False:
        raise ValueError("network access must be false")
    if config.get("astral_integration", {}).get("status") != "not_run":
        raise ValueError("Astral integration escaped the authorized boundary")
    if config.get("zk_pqc", {}).get("status") != "not_run":
        raise ValueError("ZK/PQC integration escaped the authorized boundary")
    training = config.get("training", {})
    if training.get("base_weights_updated") is not False or training.get("adapter_merge") is not False:
        raise ValueError("base-weight mutation or adapter merge was authorized")
    if training.get("reversible_adapter") is not True or training.get("fine_tune_type") != "lora":
        raise ValueError("adapter contract mismatch")
    if training.get("iters_per_update") != TRAIN_ITERS or training.get("rows_per_update") != TRAIN_ROWS:
        raise ValueError("equal update budget mismatch")
    if training.get("num_layers") != TRAIN_NUM_LAYERS:
        raise ValueError("trainable layer count mismatch")

    input_manifest = read_json(root / "input-manifest.json")
    if input_manifest.get("manifest", {}).get("state_slice") != STATE_SLICE:
        raise ValueError("input state slice mismatch")
    input_body = input_manifest.get("manifest", {})
    if input_manifest.get("manifest_sha256") != digest(input_body):
        raise ValueError("input manifest digest mismatch")
    selected = input_body.get("selected_documents")
    if not isinstance(selected, list) or len(selected) != FIT_DOCUMENT_COUNT + TUNE_DOCUMENT_COUNT + ASSESSMENT_DOCUMENT_COUNT:
        raise ValueError("selected document count mismatch")
    ids = [item.get("document_id") for item in selected]
    if any(not isinstance(value, str) for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("selected document identities are not unique")
    if input_body.get("selection_offset") != 8:
        raise ValueError("successor cohort offset mismatch")
    raw_path = root / str(input_body.get("raw_path"))
    if not raw_path.is_file() or raw_path.is_symlink():
        raise ValueError("raw source copy missing")
    if raw_path.stat().st_size != input_body.get("raw_byte_len") or sha256_file(raw_path) != input_body.get("raw_sha256"):
        raise ValueError("raw source digest mismatch")

    corpus = read_json(root / "corpus/manifest.json")
    corpus_body = corpus.get("manifest", {})
    if corpus_body.get("state_slice") != STATE_SLICE or corpus.get("manifest_sha256") != digest(corpus_body):
        raise ValueError("corpus manifest identity or digest mismatch")
    splits = {
        "fit": FIT_DOCUMENT_COUNT,
        "tune": TUNE_DOCUMENT_COUNT,
        "assessment": ASSESSMENT_DOCUMENT_COUNT,
    }
    split_ids: dict[str, set[str]] = {}
    for split, expected_count in splits.items():
        entries = corpus_body.get(split)
        if not isinstance(entries, list) or len(entries) != expected_count:
            raise ValueError(f"{split} corpus count mismatch")
        split_ids[split] = set()
        for entry in entries:
            if entry.get("token_count") != WINDOW_TOKENS:
                raise ValueError(f"{split} window token count mismatch")
            identifier = entry.get("document_id")
            if not isinstance(identifier, str) or identifier in split_ids[split]:
                raise ValueError(f"{split} document identity mismatch")
            split_ids[split].add(identifier)
            path = root / "corpus" / str(entry.get("path"))
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"corpus window missing: {path}")
            if path.stat().st_size != entry.get("byte_len") or sha256_file(path) != entry.get("text_sha256"):
                raise ValueError(f"corpus window digest mismatch: {path}")
    if split_ids["fit"] & split_ids["tune"] or split_ids["fit"] & split_ids["assessment"] or split_ids["tune"] & split_ids["assessment"]:
        raise ValueError("document identity crosses a split")

    recorded_model_manifest = read_json(root / "model-manifest.json")
    if recorded_model_manifest != model_manifest(model_path):
        raise ValueError("cached base model manifest changed or was not recorded exactly")
    if config.get("model_manifest_sha256") != recorded_model_manifest.get("manifest_sha256"):
        raise ValueError("config/model manifest mismatch")

    qualification = read_json(root / "qualification.json")
    if qualification.get("state_slice") != STATE_SLICE or qualification.get("qualification_passed") is not True:
        raise ValueError("qualification did not pass")
    if qualification.get("native_reload_passed") is not True or qualification.get("zero_adapter_passed") is not True:
        raise ValueError("native or zero-adapter parity failed")
    if qualification.get("candidate_nonzero_passed") is not True or qualification.get("adapter_restore_passed") is not True:
        raise ValueError("candidate or adapter restore qualification failed")
    if qualification.get("native_reload_max_abs_logit_delta", 1.0) > PARITY_TOLERANCE:
        raise ValueError("native reload parity exceeds tolerance")
    if qualification.get("zero_adapter_max_abs_logit_delta", 1.0) > PARITY_TOLERANCE:
        raise ValueError("zero adapter parity exceeds tolerance")
    if qualification.get("adapter_restore_max_abs_logit_delta", 1.0) > ADAPTER_RESTORE_TOLERANCE:
        raise ValueError("adapter restore exceeds tolerance")
    for relative in (
        qualification.get("training", {}).get("adapter_file"),
        "qualification/zero_adapter/adapters.safetensors",
        "qualification/restored_adapter/adapters.safetensors",
    ):
        if not isinstance(relative, str) or not (root / relative).is_file():
            raise ValueError("qualification adapter file missing")

    lock = read_json(root / "prediction-lock.json")
    lock_body = lock.get("lock", {})
    if lock.get("lock_sha256") != digest(lock_body):
        raise ValueError("prediction lock digest mismatch")
    if lock_body.get("state_slice") != STATE_SLICE or lock_body.get("config_sha256") != config_digest:
        raise ValueError("prediction lock identity mismatch")
    if lock_body.get("assessment_started") is not False:
        raise ValueError("prediction lock was mutable at assessment")
    locked_cases = lock_body.get("cases")
    if not isinstance(locked_cases, list) or len(locked_cases) != len(SEEDS) * len(ORDERS) * len(ARMS):
        raise ValueError("prediction lock case count mismatch")
    for locked in locked_cases:
        if "assessment_after" in locked or "results" in locked:
            raise ValueError("assessment data entered prediction lock")

    results = read_json(root / "results.json")
    if results.get("state_slice") != STATE_SLICE or results.get("claim_ceiling") != CLAIM_CEILING:
        raise ValueError("results identity mismatch")
    result_digest = results.get("results_sha256")
    result_body = dict(results)
    result_body.pop("results_sha256", None)
    if result_digest != digest(result_body):
        raise ValueError("results digest mismatch")
    case_results = results.get("case_results")
    expected_keys = {(seed, order_name, arm) for seed in SEEDS for order_name in ORDERS for arm in ARMS}
    observed_keys = set()
    if not isinstance(case_results, list) or len(case_results) != len(expected_keys):
        raise ValueError("case result count mismatch")
    for result in case_results:
        key = (result.get("seed"), result.get("order_name"), result.get("arm"))
        if key in observed_keys or key not in expected_keys:
            raise ValueError(f"unexpected or duplicate case: {key}")
        observed_keys.add(key)
        if result.get("assessment_started") is not True:
            raise ValueError("assessment result was not marked after lock")
        if result.get("order") != list(ORDERS[result["order_name"]]):
            raise ValueError("case order mismatch")
        updates = result.get("updates")
        if not isinstance(updates, list) or len(updates) != FIT_DOCUMENT_COUNT:
            raise ValueError("update count mismatch")
        if result.get("commit_count", 0) + result.get("rollback_count", 0) != FIT_DOCUMENT_COUNT:
            raise ValueError("commit/rollback accounting mismatch")
        final_adapter = result.get("final_adapter")
        if not isinstance(final_adapter, str) or not (root / final_adapter / "adapters.safetensors").is_file():
            raise ValueError("final adapter missing")
        for update in updates:
            candidate = update.get("candidate_adapter")
            if not isinstance(candidate, str) or not (root / candidate / "adapters.safetensors").is_file():
                raise ValueError("candidate adapter missing")
            if sha256_file(root / candidate / "adapters.safetensors") != update.get("candidate_adapter_sha256"):
                raise ValueError("candidate adapter digest mismatch")
            if update.get("training", {}).get("returncode") != 0:
                raise ValueError("training return code mismatch")
            compute = update.get("equal_compute_update", {})
            if compute.get("iters") != TRAIN_ITERS:
                raise ValueError("training iteration receipt mismatch")
            if compute.get("rows") != TRAIN_ROWS:
                raise ValueError("training row receipt mismatch")
            if compute.get("num_layers") != TRAIN_NUM_LAYERS or compute.get("batch_size") != 1:
                raise ValueError("training compute contract mismatch")
        if result.get("fit_forgetting_fraction", math.inf) > MAX_FORGETTING_FRACTION:
            raise ValueError("forgetting guard failed")
        if result.get("tune_ece_delta", math.inf) > MAX_CALIBRATION_ECE_DELTA:
            raise ValueError("calibration guard failed")
        if result.get("assessment_repeat_mean_nll_delta", math.inf) > REPEAT_TOLERANCE:
            raise ValueError("assessment repeat guard failed")
        if result.get("calibration_guard_passed") is not True or result.get("forgetting_guard_passed") is not True or result.get("repeat_guard_passed") is not True:
            raise ValueError("hard guard receipt is false")

    by_key = {(result["seed"], result["order_name"], result["arm"]): result for result in case_results}
    deltas = []
    paired = []
    for seed in SEEDS:
        for order_name in ORDERS:
            fixed = by_key[(seed, order_name, "fixed_cadence")]
            guarded = by_key[(seed, order_name, "plasticity_guard")]
            fixed_gain = float(fixed["assessment_adaptation_improvement"])
            guarded_gain = float(guarded["assessment_adaptation_improvement"])
            delta = guarded_gain - fixed_gain
            deltas.append(delta)
            paired.append({"case": f"seed-{seed}-{order_name}", "delta": round(delta, 9)})
    primary = results.get("primary_endpoint", {})
    lower, upper = bootstrap_interval(deltas, BOOTSTRAP_SEED, BOOTSTRAP_REPLICATES)
    if primary.get("case_deltas") != [
        {
            "case": item["case"],
            "fixed": by_key[(int(item["case"].split("-")[1]), item["case"].split("-")[2], "fixed_cadence")]["assessment_adaptation_improvement"],
            "plasticity_guard": by_key[(int(item["case"].split("-")[1]), item["case"].split("-")[2], "plasticity_guard")]["assessment_adaptation_improvement"],
            "delta": item["delta"],
        }
        for item in primary.get("case_deltas", [])
    ]:
        raise ValueError("primary case delta receipt mismatch")
    if not math.isclose(float(primary.get("mean_delta")), sum(deltas) / len(deltas), abs_tol=1e-8):
        raise ValueError("primary mean delta mismatch")
    interval = primary.get("bootstrap_95_percent_interval")
    if interval != [round(lower, 9), round(upper, 9)]:
        raise ValueError("bootstrap interval mismatch")
    wins = sum(delta > 0 for delta in deltas)
    if primary.get("positive_case_wins") != wins:
        raise ValueError("positive-win count mismatch")
    expected_pass = (
        sum(deltas) / len(deltas) >= PRIMARY_EFFECT_THRESHOLD
        and lower >= 0.0
        and wins >= 3
        and results.get("hard_guards", {}).get("all_passed") is True
    )
    if primary.get("passed") is not expected_pass:
        raise ValueError("primary endpoint decision mismatch")
    expected_classification = "DevelopmentCandidate" if expected_pass else "DevelopmentNoCandidate"
    if results.get("classification") != expected_classification:
        raise ValueError("classification mismatch")
    receipt = read_json(root / "receipt.json")
    receipt_digest = receipt.get("receipt_sha256")
    receipt_body = dict(receipt)
    receipt_body.pop("receipt_sha256", None)
    if receipt_digest != digest(receipt_body):
        raise ValueError("receipt digest mismatch")
    if receipt.get("base_weights_unchanged") is not True or receipt.get("weights_frozen") is not True or receipt.get("adapter_only") is not True:
        raise ValueError("base-weight custody receipt failed")
    if receipt.get("results_sha256") != result_digest or receipt.get("prediction_lock_sha256") != lock.get("lock_sha256"):
        raise ValueError("receipt/result/lock linkage mismatch")

    return {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "valid": True,
        "classification": results["classification"],
        "case_count": len(case_results),
        "primary_mean_delta": primary["mean_delta"],
        "primary_bootstrap_95_percent_interval": interval,
        "hard_guards_passed": results.get("hard_guards", {}).get("all_passed"),
        "base_weights_unchanged": receipt["base_weights_unchanged"],
        "validator": "independent-aggregate-only-v1",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = validate(args.artifact_root, args.model)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
