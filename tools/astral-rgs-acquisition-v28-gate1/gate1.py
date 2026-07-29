from __future__ import annotations

import hashlib
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


STATE_SLICE = "astral-rgs-v28-gate1-acquisition-qualification-implementation"
PACKET_VERSION = "mesh.astral_v28_gate1_packet.v1"
CELL_VERSION = "mesh.astral_v28_gate1_cell.v1"
FACT_KINDS = ("nonce_fact", "entity_relation", "changed_rule", "opaque_mapping")
QUERY_CLASSES = ("paraphrase", "multi_hop", "withheld_composition")
LABELS = ("A", "B", "C", "D")
SEEDS = (280301, 280303, 280307)
TASK_ORDERS = ("order-abcd", "order-acdb", "order-bdac")
NONPERSISTENT_ARMS = ("context_only", "retrieval")
PERSISTENT_ARMS = (
    "naive_sequential_lora",
    "replay_lora",
    "scol_style_sparse_lora",
    "nested_multiscale_lora",
    "modular_ghost_state",
    "compressed_adapter_recollection",
    "representation_time_distillation",
)
V28R2_PACKET_SHA256 = "sha256:5e830ee437e8d67faa9dedc667db35114fa5ccf84809a9b2874c60a1ed622ddc"
V28R2_CORPUS_MANIFEST_SHA256 = "sha256:0264b3c922e567f53f539e09582cea1becb60156b1a92dbbe7906f3541b460a2"
V28R2_NO_UPDATE_ACCURACY = 0.2500678168402778
V28R2_BASELINE_OBSERVATIONS_SHA256 = "sha256:7739c7afd1d2ca52f8e8c1acd7c01594201fbec1c7fba9500da036da5ce099d2"
V28R2_BASELINE_FAMILY_SCORES_SHA256 = "sha256:52f1da63e9446e43a927713f95168371137bf49d0e4287dfae9ff1c3fb604705"
OVERALL_FLOOR = 0.70
DIMENSION_FLOOR = 0.60
GAIN_FLOOR = 0.20
CRITICAL = 5.0
SUPERBLOCK_QUERIES = 96 * 12
TOTAL_QUERIES = 73728
EXPECTED_BUDGET = {
    "lora_rank": 8,
    "num_layers": 6,
    "gradient_steps": 768,
    "examples_per_step": 8,
    "tokens_per_example": 128,
    "update_tokens": 786432,
    "learning_rate": 0.0001,
    "persistent_state_bytes_max": 67108864,
}
SHA256 = re.compile(r"sha256:[0-9a-f]{64}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def without_hash(value: dict[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def error(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def load_protocol(path: str | Path) -> dict[str, Any]:
    protocol = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(protocol, dict):
        raise ValueError("protocol must be a JSON object")
    return protocol


def validate_protocol(protocol: Any, errors: list[str]) -> None:
    if not isinstance(protocol, dict):
        error(errors, "protocol:not_object")
        return
    expected = {
        "version": "mesh.astral_v28_gate1_protocol.v1",
        "state_slice": STATE_SLICE,
        "v28r2_packet_sha256": V28R2_PACKET_SHA256,
        "v28r2_corpus_manifest_sha256": V28R2_CORPUS_MANIFEST_SHA256,
        "v28r2_no_update_accuracy": V28R2_NO_UPDATE_ACCURACY,
        "v28r2_baseline_observations_sha256": V28R2_BASELINE_OBSERVATIONS_SHA256,
        "v28r2_baseline_family_scores_sha256": V28R2_BASELINE_FAMILY_SCORES_SHA256,
        "fact_kinds": list(FACT_KINDS),
        "query_classes": list(QUERY_CLASSES),
        "seeds": list(SEEDS),
        "nonpersistent_arms": list(NONPERSISTENT_ARMS),
        "persistent_arms": list(PERSISTENT_ARMS),
        "budget": EXPECTED_BUDGET,
        "assessment_opened": False,
        "retention_recovery_run": False,
        "selection_run": False,
    }
    for key, value in expected.items():
        if protocol.get(key) != value:
            error(errors, f"protocol:{key}")
    if protocol.get("protocol_sha256") != stable_hash(without_hash(protocol, "protocol_sha256")):
        error(errors, "protocol:hash")
    local_protocol = Path(__file__).with_name("protocol.json")
    if protocol.get("astral_protocol_sha256") != sha256_file(local_protocol):
        error(errors, "protocol:astral_source")
    task_orders = protocol.get("task_orders")
    if not isinstance(task_orders, dict) or tuple(task_orders) != TASK_ORDERS:
        error(errors, "protocol:task_orders")
    futility = protocol.get("futility") or {}
    if futility != {
        "families_per_superblock": 96,
        "families_per_kind_per_superblock": 24,
        "overall_floor": OVERALL_FLOOR,
        "dimension_floor": DIMENSION_FLOOR,
        "strict_comparison": True,
    }:
        error(errors, "protocol:futility")
    statistics = protocol.get("statistics") or {}
    if statistics != {
        "gain_floor": GAIN_FLOOR,
        "cell_critical_value": CRITICAL,
        "bootstrap_draws": 10000,
        "familywise_alpha": 0.05,
        "bonferroni_arm_count": 7,
    }:
        error(errors, "protocol:statistics")


def recompute_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("metrics require observations")

    def metric(subset: list[dict[str, Any]], floor: float) -> dict[str, Any]:
        if not subset:
            raise ValueError("metric dimension is empty")
        clustered: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in subset:
            clustered[row["family_id"]].append(row)
        values = [sum(bool(item["correct"]) for item in items) / len(items) for items in clustered.values()]
        accuracy = sum(bool(row["correct"]) for row in subset) / len(subset)
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1)
        standard_error = math.sqrt(variance / len(values))
        lower = mean - CRITICAL * standard_error
        return {
            "accuracy": accuracy,
            "floor": floor,
            "family_count": len(values),
            "standard_error": standard_error,
            "critical_value": CRITICAL,
            "lower_bound": lower,
            "passes": accuracy >= floor and lower > floor,
        }

    result = {"overall": metric(rows, OVERALL_FLOOR)}
    result["fact_kinds"] = {
        kind: metric([row for row in rows if row["fact_kind"] == kind], DIMENSION_FLOOR)
        for kind in FACT_KINDS
    }
    result["query_classes"] = {
        query_class: metric(
            [row for row in rows if row["query_class"] == query_class], DIMENSION_FLOOR
        )
        for query_class in QUERY_CLASSES
    }
    family_scores = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["family_id"]].append(row)
    for items in grouped.values():
        family_scores.append(sum(bool(item["correct"]) for item in items) / len(items))
    result["gain_over_no_update"] = result["overall"]["accuracy"] - V28R2_NO_UPDATE_ACCURACY
    result["family_score_sha256"] = stable_hash(sorted(family_scores))
    result["passes_cell_gate"] = (
        result["overall"]["passes"]
        and all(item["passes"] for item in result["fact_kinds"].values())
        and all(item["passes"] for item in result["query_classes"].values())
        and result["gain_over_no_update"] >= GAIN_FLOOR
    )
    return result


def recompute_futility(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows or len(rows) % SUPERBLOCK_QUERIES:
        raise ValueError("futility prefix is not superblock-complete")
    dimensions: dict[str, tuple[list[dict[str, Any]], int, float]] = {
        "overall": (rows, TOTAL_QUERIES, OVERALL_FLOOR)
    }
    dimensions.update(
        {
            f"fact_kind:{kind}": (
                [row for row in rows if row["fact_kind"] == kind],
                TOTAL_QUERIES // 4,
                DIMENSION_FLOOR,
            )
            for kind in FACT_KINDS
        }
    )
    dimensions.update(
        {
            f"query_class:{query_class}": (
                [row for row in rows if row["query_class"] == query_class],
                TOTAL_QUERIES // 3,
                DIMENSION_FLOOR,
            )
            for query_class in QUERY_CLASSES
        }
    )
    calculations = {}
    failed = []
    for name, (subset, total, floor) in dimensions.items():
        correct = sum(bool(row["correct"]) for row in subset)
        upper = (correct + total - len(subset)) / total
        calculations[name] = {
            "correct_so_far": correct,
            "scored": len(subset),
            "remaining": total - len(subset),
            "total": total,
            "floor": floor,
            "maximum_final_accuracy": upper,
            "strictly_below_floor": upper < floor,
        }
        if upper < floor:
            failed.append(name)
    return {
        "futile": bool(failed),
        "failed_dimensions": failed,
        "calculations": calculations,
        "scored_query_count": len(rows),
    }


def validate_observations(
    rows: Any, *, errors: list[str], prefix: str, allow_prefix: bool
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or not rows:
        error(errors, f"{prefix}:observations")
        return []
    if (allow_prefix and len(rows) % SUPERBLOCK_QUERIES) or (not allow_prefix and len(rows) != TOTAL_QUERIES):
        error(errors, f"{prefix}:observation_count")
    query_ids = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            error(errors, f"{prefix}:row_not_object")
            continue
        query_id = row.get("query_id")
        if not isinstance(query_id, str) or query_id in query_ids:
            error(errors, f"{prefix}:query_ids")
        query_ids.add(query_id)
        scores = row.get("label_scores")
        if (
            not isinstance(scores, list)
            or len(scores) != 4
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in scores)
        ):
            error(errors, f"{prefix}:scores")
            continue
        selected = max(range(4), key=lambda choice: (float(scores[choice]), -choice))
        predicted = LABELS[selected]
        if row.get("predicted_label") != predicted:
            error(errors, f"{prefix}:argmax")
        expected = row.get("expected_label")
        if expected not in LABELS or row.get("correct") is not (predicted == expected):
            error(errors, f"{prefix}:correctness")
        token_ids = row.get("token_ids")
        if not isinstance(token_ids, list) or not token_ids or any(not isinstance(token, int) for token in token_ids):
            error(errors, f"{prefix}:token_ids")
        elif row.get("tokenized_input_sha256") != stable_hash(token_ids):
            error(errors, f"{prefix}:token_hash")
        if row.get("fact_kind") not in FACT_KINDS or row.get("query_class") not in QUERY_CLASSES:
            error(errors, f"{prefix}:dimensions")
    return rows


def validate_control(control: Any, *, errors: list[str]) -> None:
    if not isinstance(control, dict):
        error(errors, "control:not_object")
        return
    arm = control.get("arm_id")
    prefix = f"control:{arm}"
    if arm not in NONPERSISTENT_ARMS:
        error(errors, "control:arm")
    if control.get("qualifies_persistent_acquisition") is not False:
        error(errors, f"{prefix}:claim_boundary")
    rows = validate_observations(
        control.get("observations"), errors=errors, prefix=prefix, allow_prefix=False
    )
    if control.get("observations_sha256") != stable_hash(rows):
        error(errors, f"{prefix}:observations_hash")
    if rows:
        try:
            metrics = recompute_metrics(rows)
            if control.get("metrics") != metrics:
                error(errors, f"{prefix}:metrics")
        except Exception:
            error(errors, f"{prefix}:metrics_exception")
    if control.get("control_sha256") != stable_hash(without_hash(control, "control_sha256")):
        error(errors, f"{prefix}:hash")


def validate_cell(cell: Any, *, errors: list[str]) -> bool:
    if not isinstance(cell, dict):
        error(errors, "cell:not_object")
        return False
    arm = cell.get("arm_id")
    seed = cell.get("seed")
    order = cell.get("order_id")
    prefix = f"cell:{arm}:{seed}:{order}"
    if arm not in PERSISTENT_ARMS or seed not in SEEDS or order not in TASK_ORDERS:
        error(errors, f"{prefix}:identity")
    status = cell.get("status")
    if status == "NotRunByPreregisteredArmFutility":
        if set(cell) != {"arm_id", "seed", "order_id", "status"}:
            error(errors, f"{prefix}:skipped_shape")
        return False
    if status == "AcquisitionCellCrashed":
        return False
    if cell.get("version") != CELL_VERSION or cell.get("state_slice") != STATE_SLICE:
        error(errors, f"{prefix}:version")
    if cell.get("cell_sha256") != stable_hash(without_hash(cell, "cell_sha256")):
        error(errors, f"{prefix}:hash")
    process_ids = [
        cell.get("preparation_process_id"),
        cell.get("update_process_id"),
        cell.get("evaluation_process_id"),
    ]
    if any(not isinstance(value, str) for value in process_ids) or len(set(process_ids)) != 3:
        error(errors, f"{prefix}:process_isolation")
    if cell.get("source_material_present") is not False or cell.get("retrieval_index_present") is not False:
        error(errors, f"{prefix}:source_isolation")
    rows = validate_observations(
        cell.get("observations"), errors=errors, prefix=prefix, allow_prefix=True
    )
    if cell.get("observations_sha256") != stable_hash(rows):
        error(errors, f"{prefix}:observations_hash")
    if rows:
        try:
            futility = recompute_futility(rows)
            if cell.get("futility") != futility:
                error(errors, f"{prefix}:futility")
            complete = len(rows) == TOTAL_QUERIES
            metrics = recompute_metrics(rows) if complete else None
            if cell.get("metrics") != metrics:
                error(errors, f"{prefix}:metrics")
            expected_status = (
                "AcquisitionCellFutile"
                if futility["futile"]
                else "AcquisitionCellPassed"
                if metrics and metrics["passes_cell_gate"]
                else "AcquisitionCellFailed"
            )
            if status != expected_status:
                error(errors, f"{prefix}:status")
        except Exception:
            error(errors, f"{prefix}:recompute_exception")
    return status == "AcquisitionCellPassed"


def validate_cell_artifacts(cell: dict[str, Any], *, root: Path, errors: list[str]) -> None:
    status = cell.get("status")
    if status in {"NotRunByPreregisteredArmFutility", "AcquisitionCellCrashed"}:
        return
    arm = cell["arm_id"]
    seed = cell["seed"]
    order = cell["order_id"]
    prefix = f"cell:{arm}:{seed}:{order}:artifact"
    cell_root = root / "cells" / arm / str(seed) / order
    prep_path = cell_root / "preparation.json"
    update_root = cell_root / "update"
    receipt_path = update_root / "update-receipt.json"
    try:
        prep = json.loads(prep_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception:
        error(errors, f"{prefix}:receipt_missing")
        return
    if prep.get("receipt_sha256") != stable_hash(without_hash(prep, "receipt_sha256")):
        error(errors, f"{prefix}:preparation_hash")
    if receipt.get("receipt_sha256") != stable_hash(without_hash(receipt, "receipt_sha256")):
        error(errors, f"{prefix}:update_hash")
    if (
        prep.get("arm_id") != arm
        or prep.get("seed") != seed
        or prep.get("order_id") != order
        or receipt.get("arm_id") != arm
        or receipt.get("seed") != seed
        or receipt.get("order_id") != order
    ):
        error(errors, f"{prefix}:identity")
    if (
        receipt.get("preparation_process_id") != prep.get("preparation_process_id")
        or receipt.get("preparation_process_id") != cell.get("preparation_process_id")
        or receipt.get("update_process_id") != cell.get("update_process_id")
        or receipt.get("receipt_sha256") != cell.get("update_receipt_sha256")
    ):
        error(errors, f"{prefix}:process_binding")
    if receipt.get("budget") != EXPECTED_BUDGET:
        error(errors, f"{prefix}:budget_lock")
    if (
        receipt.get("gradient_steps") != 768
        or receipt.get("training_examples") != 6144
        or receipt.get("update_tokens") != 786432
        or receipt.get("evaluation_material_present") is not False
    ):
        error(errors, f"{prefix}:budget_observed")
    inventory = receipt.get("state_inventory")
    if not isinstance(inventory, list) or receipt.get("state_inventory_sha256") != stable_hash(inventory):
        error(errors, f"{prefix}:state_inventory_hash")
        return
    if receipt.get("state_inventory_sha256") != cell.get("state_inventory_sha256"):
        error(errors, f"{prefix}:cell_state_binding")
    state_root = update_root / "state"
    actual = []
    for path in sorted(state_root.rglob("*")) if state_root.is_dir() else []:
        if path.is_symlink():
            error(errors, f"{prefix}:state_symlink")
        elif path.is_file():
            actual.append(
                {
                    "path": path.relative_to(state_root).as_posix(),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    if actual != inventory:
        error(errors, f"{prefix}:state_census")
    state_bytes = sum(row.get("size_bytes", 0) for row in inventory if isinstance(row, dict))
    if receipt.get("state_bytes") != state_bytes or state_bytes > 67108864:
        error(errors, f"{prefix}:state_bytes")
    trace_path = update_root / "loss-trace.json"
    token_path = update_root / "token-window-receipts.json"
    try:
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        tokens = json.loads(token_path.read_text(encoding="utf-8"))
        if stable_hash(trace) != receipt.get("loss_trace_sha256") or len(trace) != 768:
            error(errors, f"{prefix}:loss_trace")
        if stable_hash(tokens) != receipt.get("token_window_receipts_sha256") or len(tokens) != 6144:
            error(errors, f"{prefix}:token_receipts")
    except Exception:
        error(errors, f"{prefix}:trace_missing")


def recompute_bootstrap(
    cell_rows: list[list[dict[str, Any]]],
    *,
    baseline_scores: dict[str, float],
    seed_material: str,
    draws: int = 10000,
) -> dict[str, Any]:
    if len(cell_rows) != 9:
        raise ValueError("bootstrap requires nine cells")
    family_scores: dict[str, list[float]] = defaultdict(list)
    kinds: dict[str, str] = {}
    for rows in cell_rows:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["family_id"]].append(row)
            kinds[row["family_id"]] = row["fact_kind"]
        for family_id, items in grouped.items():
            family_scores[family_id].append(
                sum(bool(item["correct"]) for item in items) / len(items)
            )
    if any(len(values) != 9 for values in family_scores.values()):
        raise ValueError("bootstrap cell coverage is incomplete")
    if set(family_scores) != set(baseline_scores):
        raise ValueError("bootstrap baseline coverage is incomplete")
    strata = {
        kind: sorted(family_id for family_id in family_scores if kinds[family_id] == kind)
        for kind in FACT_KINDS
    }
    seed = int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    gains = []
    for _ in range(draws):
        selected = [
            family_id
            for kind in FACT_KINDS
            for family_id in (rng.choice(strata[kind]) for _ in range(len(strata[kind])))
        ]
        gains.append(
            sum(
                sum(family_scores[family_id]) / 9 - baseline_scores[family_id]
                for family_id in selected
            )
            / len(selected)
        )
    gains.sort()
    alpha = 0.05 / len(PERSISTENT_ARMS)
    lower = gains[max(0, math.floor(alpha * draws) - 1)]
    return {
        "draws": draws,
        "seed_sha256": stable_hash(seed_material),
        "familywise_alpha": 0.05,
        "bonferroni_arm_count": len(PERSISTENT_ARMS),
        "one_sided_alpha": alpha,
        "lower_bound": lower,
        "gain_floor": GAIN_FLOOR,
        "passes": lower > GAIN_FLOOR,
        "draws_sha256": stable_hash(gains),
    }


def validate_manifest(root: Path, errors: list[str]) -> None:
    path = root / "artifact-manifest.json"
    if not path.is_file():
        error(errors, "artifact:manifest_missing")
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, list) or manifest.get("manifest_sha256") != stable_hash(files):
        error(errors, "artifact:manifest_hash")
        return
    listed = set()
    for row in files:
        relative = row.get("path")
        if not isinstance(relative, str) or relative.startswith("/") or ".." in Path(relative).parts:
            error(errors, "artifact:path")
            continue
        candidate = root / relative
        listed.add(relative)
        if not candidate.is_file() or candidate.is_symlink():
            error(errors, "artifact:file_missing")
        elif sha256_file(candidate) != row.get("sha256") or candidate.stat().st_size != row.get("size_bytes"):
            error(errors, "artifact:file_digest")
    allowed_late = {
        "artifact-manifest.json",
        "astral-validation-report.json",
        "astral-validation-process.json",
    }
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() not in allowed_late
    }
    if actual != listed:
        error(errors, "artifact:census")


def validate_packet(packet: Any, *, artifact_root: str | Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(packet, dict):
        return report(errors=["packet:not_object"], packet_sha256=None)
    if packet.get("version") != PACKET_VERSION or packet.get("state_slice") != STATE_SLICE:
        error(errors, "packet:version")
    if packet.get("packet_sha256") != stable_hash(without_hash(packet, "packet_sha256")):
        error(errors, "packet:hash")
    validate_protocol(packet.get("protocol"), errors)
    receipt = packet.get("immutable_input_receipt") or {}
    if receipt.get("v28r2_packet_sha256") != V28R2_PACKET_SHA256:
        error(errors, "packet:v28r2_packet")
    if receipt.get("v28r2_corpus_manifest_sha256") != V28R2_CORPUS_MANIFEST_SHA256:
        error(errors, "packet:v28r2_corpus")
    if receipt.get("family_count") != 6144 or receipt.get("query_count") != TOTAL_QUERIES:
        error(errors, "packet:v28r2_census")
    baseline_scores = packet.get("baseline_family_scores")
    if (
        not isinstance(baseline_scores, dict)
        or len(baseline_scores) != 6144
        or stable_hash(baseline_scores) != V28R2_BASELINE_FAMILY_SCORES_SHA256
        or packet.get("baseline_family_scores_sha256") != V28R2_BASELINE_FAMILY_SCORES_SHA256
    ):
        error(errors, "packet:baseline_family_scores")
        baseline_scores = {}
    for boundary in (
        "retention_recovery_run",
        "selection_run",
        "assessment_opened",
        "confirmation_run",
        "independent_replication",
    ):
        if packet.get(boundary) is not False:
            error(errors, f"packet:{boundary}")
    source_bindings = packet.get("source_bindings")
    if not isinstance(source_bindings, dict) or set(source_bindings) != {"rgs", "astral"}:
        error(errors, "packet:source_bindings")
    else:
        for name, binding in source_bindings.items():
            if (
                not isinstance(binding, dict)
                or binding.get("dirty") is not False
                or not isinstance(binding.get("commit"), str)
                or not re.fullmatch(r"[0-9a-f]{40}", binding["commit"])
                or not isinstance(binding.get("tree"), str)
                or not re.fullmatch(r"[0-9a-f]{40}", binding["tree"])
            ):
                error(errors, f"packet:source_binding:{name}")
    controls = packet.get("controls")
    if not isinstance(controls, list) or [row.get("arm_id") for row in controls if isinstance(row, dict)] != list(NONPERSISTENT_ARMS):
        error(errors, "packet:controls")
    else:
        for control in controls:
            validate_control(control, errors=errors)
    cells = packet.get("cells")
    expected_cells = [(arm, seed, order) for arm in PERSISTENT_ARMS for seed in SEEDS for order in TASK_ORDERS]
    if not isinstance(cells, list) or len(cells) != len(expected_cells):
        error(errors, "packet:cell_count")
        cells = []
    actual_cells = [
        (cell.get("arm_id"), cell.get("seed"), cell.get("order_id"))
        for cell in cells
        if isinstance(cell, dict)
    ]
    if actual_cells != expected_cells:
        error(errors, "packet:cell_order")
    passed_counts = {arm: 0 for arm in PERSISTENT_ARMS}
    passed_rows: dict[str, list[list[dict[str, Any]]]] = {arm: [] for arm in PERSISTENT_ARMS}
    stopped = {arm: False for arm in PERSISTENT_ARMS}
    for cell in cells:
        arm = cell.get("arm_id") if isinstance(cell, dict) else None
        skipped = isinstance(cell, dict) and cell.get("status") == "NotRunByPreregisteredArmFutility"
        if arm in stopped and stopped[arm] and not skipped:
            error(errors, f"packet:{arm}:post_stop_execution")
        passed = validate_cell(cell, errors=errors)
        if artifact_root is not None and isinstance(cell, dict):
            validate_cell_artifacts(cell, root=Path(artifact_root), errors=errors)
        if arm in stopped:
            if passed:
                passed_counts[arm] += 1
                passed_rows[arm].append(cell["observations"])
            elif not skipped:
                stopped[arm] = True
    summaries = packet.get("arm_summaries")
    if not isinstance(summaries, list) or [row.get("arm_id") for row in summaries if isinstance(row, dict)] != list(PERSISTENT_ARMS):
        error(errors, "packet:arm_summaries")
        summaries = []
    qualifying = []
    for summary in summaries:
        arm = summary["arm_id"]
        if summary.get("completed_cell_count") != passed_counts[arm]:
            error(errors, f"packet:{arm}:completed_count")
        bootstrap = summary.get("bootstrap")
        qualifies = bool(summary.get("qualifies"))
        if passed_counts[arm] != 9:
            if bootstrap is not None or qualifies:
                error(errors, f"packet:{arm}:premature_qualification")
        else:
            try:
                expected_bootstrap = recompute_bootstrap(
                    passed_rows[arm],
                    baseline_scores=baseline_scores,
                    seed_material=packet["protocol"]["protocol_sha256"] + arm,
                )
                if bootstrap != expected_bootstrap:
                    error(errors, f"packet:{arm}:bootstrap")
                if qualifies is not bool(expected_bootstrap["passes"]):
                    error(errors, f"packet:{arm}:qualifies")
            except Exception:
                error(errors, f"packet:{arm}:bootstrap_exception")
        if qualifies:
            qualifying.append(arm)
    if packet.get("qualifying_arms") != qualifying:
        error(errors, "packet:qualifying_arms")
    expected_status = (
        "AcquisitionQualifiedCandidates"
        if len(qualifying) >= 2
        else "AcquisitionSingleCandidate"
        if len(qualifying) == 1
        else "AcquisitionNoCandidate"
    )
    if packet.get("status") != expected_status:
        error(errors, "packet:status")
    if artifact_root is not None:
        validate_manifest(Path(artifact_root), errors)
    return report(errors=errors, packet_sha256=packet.get("packet_sha256"))


def report(*, errors: list[str], packet_sha256: Any) -> dict[str, Any]:
    valid = not errors
    return {
        "version": "astral.v28_gate1_validation_report.v1",
        "state_slice": STATE_SLICE,
        "valid": valid,
        "status": "ValidatedGate1Packet" if valid else "Invalid",
        "errors": errors,
        "packet_sha256": packet_sha256,
        "claim_ceiling": (
            "LocalModelBackedAcquisitionQualificationV28Gate1"
            if valid
            else "NoGate1Claim"
        ),
        "retention_recovery_validated": False,
        "selection_validated": False,
        "assessment_validated": False,
        "independent_replication_validated": False,
    }
