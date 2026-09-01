#!/usr/bin/env python3
"""Independently validate the plasticity-guard replication artifact.

State slice: continual-learning-plasticity-guard-replication-v1.

This validator uses only manifests, receipts, aggregate metrics, and adapter
file digests. It does not import or execute the replication runner and does
not load the model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "continual-learning-plasticity-guard-replication-v1"
PRIOR_STATE_SLICE = "continual-learning-plasticity-guard-reversible-adapter-v1"
PRIOR_RESULTS_DIGEST = "46d0654b199205b2957e5a1fb758c1989c377db7d6ab86eaa0f6440de3bd8316"
PRIOR_RECEIPT_DIGEST = "ed707b95864627dbefb00b277dda41bc23ec6ecaa51f36677ff503c0be6798b6"
PRIOR_RESULTS_FILE_SHA256 = "e2c15c2bafa0e6fa1fc5519267ccd51a1d0dabcabf551596b3b7e8a8426aa4ed"
PRIOR_RECEIPT_FILE_SHA256 = "569d1b7f340867f8cd52803c4ff6be0ca09be55e02f18121189a8d9dd84b7a02"
WINDOW_TOKENS = 256
PRIOR_SELECTION_OFFSET = 8
PRIOR_SELECTED_DOCUMENT_COUNT = 12
SELECTION_OFFSET = 20
FIT_DOCUMENT_COUNT = 6
TUNE_DOCUMENT_COUNT = 3
ASSESSMENT_DOCUMENT_COUNT = 3
SEEDS = (1747, 1749)
ORDERS = {
    "interleave": (0, 3, 1, 4, 2, 5),
    "outer_in": (0, 5, 1, 4, 2, 3),
}
ARMS = ("no_update", "fixed_cadence", "plasticity_guard")
TRAIN_ITERS = 3
TRAIN_ROWS = 4
TRAIN_NUM_LAYERS = 4
ABSOLUTE_EFFECT_THRESHOLD = 0.010
SECONDARY_EFFECT_THRESHOLD = 0.010
PRIMARY_WIN_COUNT = 3
MIN_CURRENT_GAIN = 0.001
MAX_PROTECTED_DEGRADATION = 0.010
MAX_FORGETTING_FRACTION = 0.05
MAX_CALIBRATION_ECE_DELTA = 0.05
REPEAT_TOLERANCE = 1e-8
PARITY_TOLERANCE = 1e-5
ADAPTER_RESTORE_TOLERANCE = 1e-6
BOOTSTRAP_SEED = 20260829
BOOTSTRAP_REPLICATES = 10_000
CLAIM_CEILING = "LocalDevelopmentPlasticityGuardReplication"


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


def require_file(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"required artifact is missing or unsafe: {relative}")
    return path


def validate_frozen_prior(config: dict[str, Any]) -> None:
    prior = config.get("prior_frozen_result")
    if not isinstance(prior, dict):
        raise ValueError("frozen prior result receipt is missing")
    if prior.get("state_slice") != PRIOR_STATE_SLICE:
        raise ValueError("frozen prior state slice mismatch")
    root = Path(str(prior.get("artifact_root"))).resolve()
    artifact_root_is_external(root)
    if sha256_file(require_file(root, "results.json")) != PRIOR_RESULTS_FILE_SHA256:
        raise ValueError("frozen prior results digest mismatch")
    if sha256_file(require_file(root, "receipt.json")) != PRIOR_RECEIPT_FILE_SHA256:
        raise ValueError("frozen prior receipt digest mismatch")
    if prior.get("results_sha256") != PRIOR_RESULTS_DIGEST or prior.get("receipt_sha256") != PRIOR_RECEIPT_DIGEST:
        raise ValueError("frozen prior digest receipt mismatch")
    if prior.get("results_file_sha256") != PRIOR_RESULTS_FILE_SHA256 or prior.get("receipt_file_sha256") != PRIOR_RECEIPT_FILE_SHA256:
        raise ValueError("frozen prior file digest receipt mismatch")
    results = read_json(root / "results.json")
    receipt = read_json(root / "receipt.json")
    if results.get("results_sha256") != PRIOR_RESULTS_DIGEST or receipt.get("receipt_sha256") != PRIOR_RECEIPT_DIGEST:
        raise ValueError("frozen prior body digest mismatch")


def validate(root: Path, model_path: Path) -> dict[str, Any]:
    root = root.resolve()
    model_path = model_path.resolve()
    artifact_root_is_external(root)
    for relative in (
        "config.json",
        "input-manifest.json",
        "model-manifest.json",
        "qualification.json",
        "prediction-lock.json",
        "results.json",
        "receipt.json",
        "corpus/manifest.json",
    ):
        require_file(root, relative)

    config = read_json(root / "config.json")
    if config.get("state_slice") != STATE_SLICE or config.get("claim_ceiling") != CLAIM_CEILING:
        raise ValueError("config identity mismatch")
    config_digest = config.get("config_sha256")
    config_body = dict(config)
    config_body.pop("config_sha256", None)
    if config_digest != digest(config_body):
        raise ValueError("config digest mismatch")
    if config.get("network_access") is not False:
        raise ValueError("network access must be false")
    if config.get("astral_integration", {}).get("status") != "not_run":
        raise ValueError("Astral integration escaped the boundary")
    if config.get("zk_pqc", {}).get("status") != "not_run":
        raise ValueError("ZK/PQC integration escaped the boundary")
    training = config.get("training", {})
    if training.get("base_weights_updated") is not False or training.get("adapter_merge") is not False:
        raise ValueError("base-weight mutation or adapter merge was authorized")
    if training.get("reversible_adapter") is not True or training.get("fine_tune_type") != "lora":
        raise ValueError("adapter contract mismatch")
    if training.get("iters_per_update") != TRAIN_ITERS or training.get("rows_per_update") != TRAIN_ROWS:
        raise ValueError("equal update budget mismatch")
    if training.get("num_layers") != TRAIN_NUM_LAYERS or training.get("updates_per_case") != FIT_DOCUMENT_COUNT:
        raise ValueError("training shape mismatch")
    validate_frozen_prior(config)

    input_manifest = read_json(root / "input-manifest.json")
    input_body = input_manifest.get("manifest", {})
    if input_body.get("state_slice") != STATE_SLICE or input_manifest.get("manifest_sha256") != digest(input_body):
        raise ValueError("input manifest identity or digest mismatch")
    selected = input_body.get("selected_documents")
    expected_documents = FIT_DOCUMENT_COUNT + TUNE_DOCUMENT_COUNT + ASSESSMENT_DOCUMENT_COUNT
    if not isinstance(selected, list) or len(selected) != expected_documents:
        raise ValueError("selected document count mismatch")
    selected_ids = [item.get("document_id") for item in selected]
    if any(not isinstance(value, str) for value in selected_ids) or len(selected_ids) != len(set(selected_ids)):
        raise ValueError("selected document identities are not unique")
    if input_body.get("selection_offset") != SELECTION_OFFSET:
        raise ValueError("fresh cohort selection offset mismatch")
    prior_selection = input_body.get("prior_frozen_selection", {})
    prior_ids = prior_selection.get("document_ids")
    if (
        prior_selection.get("state_slice") != PRIOR_STATE_SLICE
        or prior_selection.get("selection_offset") != PRIOR_SELECTION_OFFSET
        or prior_selection.get("selected_document_count") != PRIOR_SELECTED_DOCUMENT_COUNT
        or not isinstance(prior_ids, list)
        or len(prior_ids) != PRIOR_SELECTED_DOCUMENT_COUNT
        or set(prior_ids) & set(selected_ids)
    ):
        raise ValueError("fresh cohort overlaps or misstates the frozen prior cohort")
    raw_path = root / str(input_body.get("raw_path"))
    if not raw_path.is_file() or raw_path.is_symlink():
        raise ValueError("raw source copy missing")
    if raw_path.stat().st_size != input_body.get("raw_byte_len") or sha256_file(raw_path) != input_body.get("raw_sha256"):
        raise ValueError("raw source digest mismatch")

    corpus = read_json(root / "corpus/manifest.json")
    corpus_body = corpus.get("manifest", {})
    if corpus_body.get("state_slice") != STATE_SLICE or corpus.get("manifest_sha256") != digest(corpus_body):
        raise ValueError("corpus manifest identity or digest mismatch")
    split_counts = {"fit": FIT_DOCUMENT_COUNT, "tune": TUNE_DOCUMENT_COUNT, "assessment": ASSESSMENT_DOCUMENT_COUNT}
    split_ids: dict[str, set[str]] = {}
    for split, expected_count in split_counts.items():
        entries = corpus_body.get(split)
        if not isinstance(entries, list) or len(entries) != expected_count:
            raise ValueError(f"{split} corpus count mismatch")
        split_ids[split] = set()
        for entry in entries:
            if entry.get("token_count") != WINDOW_TOKENS:
                raise ValueError(f"{split} token count mismatch")
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
    for flag in ("native_reload_passed", "zero_adapter_passed", "candidate_nonzero_passed", "adapter_restore_passed"):
        if qualification.get(flag) is not True:
            raise ValueError(f"qualification flag failed: {flag}")
    if qualification.get("native_reload_max_abs_logit_delta", 1.0) > PARITY_TOLERANCE or qualification.get("zero_adapter_max_abs_logit_delta", 1.0) > PARITY_TOLERANCE:
        raise ValueError("native or zero-adapter parity exceeds tolerance")
    if qualification.get("adapter_restore_max_abs_logit_delta", 1.0) > ADAPTER_RESTORE_TOLERANCE:
        raise ValueError("adapter restore exceeds tolerance")
    qualification_training = qualification.get("training", {})
    qualification_adapter = qualification_training.get("adapter_file")
    if not isinstance(qualification_adapter, str) or not (root / qualification_adapter).is_file():
        raise ValueError("qualification adapter file missing")
    for relative in ("qualification/zero_adapter/adapters.safetensors", "qualification/restored_adapter/adapters.safetensors"):
        require_file(root, relative)

    lock = read_json(root / "prediction-lock.json")
    lock_body = lock.get("lock", {})
    if lock.get("lock_sha256") != digest(lock_body):
        raise ValueError("prediction lock digest mismatch")
    if lock_body.get("state_slice") != STATE_SLICE or lock_body.get("config_sha256") != config_digest:
        raise ValueError("prediction lock identity mismatch")
    if lock_body.get("assessment_started") is not False:
        raise ValueError("prediction lock was mutable at assessment")
    expected_case_count = len(SEEDS) * len(ORDERS) * len(ARMS)
    locked_cases = lock_body.get("cases")
    if not isinstance(locked_cases, list) or len(locked_cases) != expected_case_count:
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
    if not isinstance(case_results, list) or len(case_results) != len(expected_keys):
        raise ValueError("case result count mismatch")
    observed_keys = set()
    fit_ids = [entry["document_id"] for entry in corpus_body["fit"]]
    for result in case_results:
        key = (result.get("seed"), result.get("order_name"), result.get("arm"))
        if key in observed_keys or key not in expected_keys:
            raise ValueError(f"unexpected or duplicate case: {key}")
        observed_keys.add(key)
        order_name = result["order_name"]
        if result.get("order") != list(ORDERS[order_name]):
            raise ValueError("case order mismatch")
        if result.get("assessment_started") is not True:
            raise ValueError("assessment result was not marked after lock")
        updates = result.get("updates")
        if not isinstance(updates, list) or len(updates) != FIT_DOCUMENT_COUNT:
            raise ValueError("update count mismatch")
        arm = result["arm"]
        if arm == "no_update":
            if result.get("final_adapter") is not None or result.get("final_model_reference") != "untouched_base":
                raise ValueError("no-update arm applied an adapter")
            if result.get("commit_count") != 0 or result.get("rollback_count") != 0 or result.get("discard_count") != FIT_DOCUMENT_COUNT:
                raise ValueError("no-update accounting mismatch")
        elif arm == "fixed_cadence":
            if result.get("commit_count") != FIT_DOCUMENT_COUNT or result.get("rollback_count") != 0 or result.get("discard_count") != 0:
                raise ValueError("fixed-cadence accounting mismatch")
        else:
            if result.get("commit_count", 0) + result.get("rollback_count", 0) != FIT_DOCUMENT_COUNT or result.get("discard_count") != 0:
                raise ValueError("plasticity-guard accounting mismatch")
        final_adapter = result.get("final_adapter")
        if final_adapter is not None and not (root / final_adapter / "adapters.safetensors").is_file():
            raise ValueError("final adapter missing")
        for step, update in enumerate(updates):
            if update.get("step") != step or update.get("fit_index") != ORDERS[order_name][step]:
                raise ValueError("update order receipt mismatch")
            if update.get("document_id") != fit_ids[update["fit_index"]]:
                raise ValueError("update document receipt mismatch")
            candidate = update.get("candidate_adapter")
            if not isinstance(candidate, str) or not (root / candidate / "adapters.safetensors").is_file():
                raise ValueError("candidate adapter missing")
            candidate_file = root / candidate / "adapters.safetensors"
            if sha256_file(candidate_file) != update.get("candidate_adapter_sha256"):
                raise ValueError("candidate adapter digest mismatch")
            training_receipt = update.get("training", {})
            if training_receipt.get("returncode") != 0 or training_receipt.get("iters") != TRAIN_ITERS or training_receipt.get("rows") != TRAIN_ROWS:
                raise ValueError("training receipt mismatch")
            if training_receipt.get("num_layers") != TRAIN_NUM_LAYERS or training_receipt.get("batch_size") != 1:
                raise ValueError("training compute contract mismatch")
            receipt_adapter = training_receipt.get("adapter_file")
            expected_receipt_adapter = f"{candidate}/adapters.safetensors"
            if receipt_adapter != expected_receipt_adapter or sha256_file(root / receipt_adapter) != training_receipt.get("adapter_sha256"):
                raise ValueError("training adapter receipt mismatch")
            compute = update.get("equal_compute_update", {})
            if compute != {"rows": TRAIN_ROWS, "iters": TRAIN_ITERS, "num_layers": TRAIN_NUM_LAYERS, "batch_size": 1}:
                raise ValueError("equal-compute receipt mismatch")
            expected_guard = step == 0 or (
                float(update["current_gain"]) >= MIN_CURRENT_GAIN
                and float(update["protected_delta"]) <= MAX_PROTECTED_DEGRADATION
            )
            if update.get("guard_would_accept") is not expected_guard:
                raise ValueError("plasticity guard decision was not recomputed")
            expected_decision = "discard" if arm == "no_update" else "commit" if arm == "fixed_cadence" or expected_guard else "rollback"
            if update.get("decision") != expected_decision:
                raise ValueError("update decision mismatch")
        if result.get("fit_forgetting_fraction", math.inf) > MAX_FORGETTING_FRACTION or result.get("tune_ece_delta", math.inf) > MAX_CALIBRATION_ECE_DELTA:
            raise ValueError("fit or calibration guard failed")
        if result.get("assessment_repeat_mean_nll_delta", math.inf) > REPEAT_TOLERANCE:
            raise ValueError("assessment repeat guard failed")
        if result.get("calibration_guard_passed") is not True or result.get("forgetting_guard_passed") is not True or result.get("repeat_guard_passed") is not True:
            raise ValueError("hard guard receipt is false")
        if arm == "no_update":
            if result.get("base_equivalence_mean_nll_delta", math.inf) > REPEAT_TOLERANCE or result.get("base_equivalence_passed") is not True:
                raise ValueError("no-update baseline is not equivalent to the untouched base")

    by_key = {(result["seed"], result["order_name"], result["arm"]): result for result in case_results}
    guard_gains = []
    guard_vs_no_update = []
    guard_vs_fixed = []
    primary_rows = []
    secondary_rows = []
    for seed in SEEDS:
        for order_name in ORDERS:
            no_update = by_key[(seed, order_name, "no_update")]
            fixed = by_key[(seed, order_name, "fixed_cadence")]
            guarded = by_key[(seed, order_name, "plasticity_guard")]
            guard_gain = float(guarded["assessment_adaptation_improvement"])
            no_update_gain = float(no_update["assessment_adaptation_improvement"])
            fixed_gain = float(fixed["assessment_adaptation_improvement"])
            no_update_delta = guard_gain - no_update_gain
            fixed_delta = guard_gain - fixed_gain
            guard_gains.append(guard_gain)
            guard_vs_no_update.append(no_update_delta)
            guard_vs_fixed.append(fixed_delta)
            case_name = f"seed-{seed}-{order_name}"
            primary_rows.append({"case": case_name, "plasticity_guard": guard_gain, "no_update": no_update_gain, "delta": round(no_update_delta, 9)})
            secondary_rows.append({"case": case_name, "fixed": fixed_gain, "plasticity_guard": guard_gain, "delta": round(fixed_delta, 9)})
    primary_lower, primary_upper = bootstrap_interval(guard_gains, BOOTSTRAP_SEED, BOOTSTRAP_REPLICATES)
    secondary_lower, secondary_upper = bootstrap_interval(guard_vs_fixed, BOOTSTRAP_SEED, BOOTSTRAP_REPLICATES)
    primary_wins = sum(delta > 0 for delta in guard_vs_no_update)
    secondary_wins = sum(delta > 0 for delta in guard_vs_fixed)
    hard_guards_passed = results.get("hard_guards", {}).get("all_passed") is True
    primary = results.get("primary_endpoint", {})
    secondary = results.get("secondary_endpoint", {})
    if primary.get("case_values") != primary_rows:
        raise ValueError("primary case values mismatch")
    if secondary.get("case_deltas") != secondary_rows:
        raise ValueError("secondary case deltas mismatch")
    if not math.isclose(float(primary.get("mean_guard_gain")), sum(guard_gains) / len(guard_gains), abs_tol=1e-8):
        raise ValueError("primary mean mismatch")
    if primary.get("bootstrap_95_percent_interval") != [round(primary_lower, 9), round(primary_upper, 9)]:
        raise ValueError("primary interval mismatch")
    if primary.get("positive_case_wins_vs_no_update") != primary_wins:
        raise ValueError("primary wins mismatch")
    if not math.isclose(float(secondary.get("mean_delta")), sum(guard_vs_fixed) / len(guard_vs_fixed), abs_tol=1e-8):
        raise ValueError("secondary mean mismatch")
    if secondary.get("bootstrap_95_percent_interval") != [round(secondary_lower, 9), round(secondary_upper, 9)]:
        raise ValueError("secondary interval mismatch")
    if secondary.get("positive_case_wins") != secondary_wins:
        raise ValueError("secondary wins mismatch")
    expected_primary = sum(guard_gains) / len(guard_gains) >= ABSOLUTE_EFFECT_THRESHOLD and primary_lower >= 0.0 and primary_wins >= PRIMARY_WIN_COUNT and hard_guards_passed
    expected_secondary = sum(guard_vs_fixed) / len(guard_vs_fixed) >= SECONDARY_EFFECT_THRESHOLD and secondary_lower >= 0.0 and secondary_wins >= PRIMARY_WIN_COUNT
    if primary.get("passed") is not expected_primary or secondary.get("passed") is not expected_secondary:
        raise ValueError("endpoint decision mismatch")
    expected_classification = "DevelopmentCandidate" if expected_primary and expected_secondary else "RollbackInfrastructureOnly" if expected_secondary and not expected_primary else "ReplicationFailureClosed"
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
    if receipt.get("primary_endpoint_passed") is not expected_primary or receipt.get("secondary_endpoint_passed") is not expected_secondary:
        raise ValueError("receipt endpoint status mismatch")

    return {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "valid": True,
        "classification": results["classification"],
        "case_count": len(case_results),
        "primary_mean_guard_gain": primary["mean_guard_gain"],
        "primary_bootstrap_95_percent_interval": primary["bootstrap_95_percent_interval"],
        "secondary_mean_delta": secondary["mean_delta"],
        "secondary_bootstrap_95_percent_interval": secondary["bootstrap_95_percent_interval"],
        "hard_guards_passed": hard_guards_passed,
        "base_weights_unchanged": receipt["base_weights_unchanged"],
        "validator": "independent-aggregate-only-replication-v1",
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
