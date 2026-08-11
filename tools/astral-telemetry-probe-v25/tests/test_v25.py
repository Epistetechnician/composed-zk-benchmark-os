import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]

SPEC = importlib.util.spec_from_file_location("astral_v25_tested", HERE / "v25.py")
V25 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V25
SPEC.loader.exec_module(V25)

VSPEC = importlib.util.spec_from_file_location("astral_v25_validator_tested", HERE / "validator_v25.py")
VALIDATOR = importlib.util.module_from_spec(VSPEC)
sys.modules[VSPEC.name] = VALIDATOR
VSPEC.loader.exec_module(VALIDATOR)


def test_fresh_corpus_census_and_disjointness():
    rows = V25.V22.build_trials()
    assert len(rows) == 192
    assert Counter(row.split for row in rows) == {"fit": 96, "tune": 48, "assessment": 48}
    frozen = set(V25.V22_FROZEN_CONCEPTS) | set(V25.V23_FROZEN_CONCEPTS) | set(V25.V24_FROZEN_CONCEPTS)
    assert set(V25.CONCEPTS).isdisjoint(frozen)
    assert len(set(V25.CONCEPTS)) == 16


def test_activation_none_identity_and_label_balance():
    rows = V25.V22.build_trials()
    for concept in V25.CONCEPTS:
        for wrapper in range(4):
            selected = {row.condition: row for row in rows if row.concept == concept and row.wrapper == wrapper}
            assert selected["activation"].prompt == selected["none"].prompt
    assert set(row.correct_token for row in rows) == set(V25.V22.TOKENS)


def test_contract_constants():
    assert V25.SITES == (10, 21, 32)
    assert V25.FIT_PROBE_GATE == 0.70
    assert V25.TUNE_PROBE_GATE == 0.65
    assert V25.ASSESS_PROBE_GATE == 0.75
    assert V25.SHUFFLED_LABEL_FLOOR == 0.55
    assert V25.TEXT_SANITY_FLOOR == 0.90
    assert V25.FORK_MARGIN == 0.15
    assert V25.CLAIM == "LocalDevelopmentPrivilegedTelemetryInformationPresence"


def _synthetic_cell(n_pairs: int, dim: int, signal: float, seed: int) -> tuple[list, list]:
    rng = np.random.default_rng(seed)
    captures, rows = [], []
    for index in range(n_pairs):
        base = rng.normal(0.0, 1.0, size=(dim,)).astype(np.float32)
        concept = V25.CONCEPTS[index % 8]
        for condition, offset in (("activation", signal), ("none", 0.0), ("text", 0.0)):
            vector = base + (offset if condition == "activation" else 0.0)
            captures.append({0: vector.astype(np.float16)})
            rows.append({
                "trial_id": f"syn-{index}-{condition}", "split": "fit",
                "concept": concept, "wrapper": index % 4, "condition": condition,
                "correct_token": " A", "prompt": "syn",
                "token": " A", "probabilities": [1.0, 0.0, 0.0],
                "logits": [1.0, 0.0, 0.0],
            })
    return captures, rows


def test_fisher_probe_separable_and_degenerate():
    captures, rows = _synthetic_cell(32, 16, signal=4.0, seed=7)
    probe = V25.fisher_probe(captures, rows, layer=0)
    assert probe is not None
    assert probe["accuracy"] == 1.0
    assert probe["separation"] > 0

    flat_captures = [{0: np.zeros(16, dtype=np.float16)} for _ in range(12)]
    flat_rows = [
        {"condition": "activation" if i % 2 == 0 else "none", "concept": V25.CONCEPTS[i % 8], "wrapper": 0}
        for i in range(12)
    ]
    assert V25.fisher_probe(flat_captures, flat_rows, layer=0) is None


def test_fisher_probe_no_signal_is_near_chance():
    rng = np.random.default_rng(11)
    captures, rows = [], []
    for index in range(64):
        concept = V25.CONCEPTS[index % 8]
        for condition in ("activation", "none"):
            vector = rng.normal(0.0, 1.0, size=(16,))
            captures.append({0: vector.astype(np.float16)})
            rows.append({
                "trial_id": f"syn-{index}-{condition}", "split": "fit",
                "concept": concept, "wrapper": index % 4, "condition": condition,
                "correct_token": " A", "prompt": "syn",
                "token": " A", "probabilities": [1.0, 0.0, 0.0],
                "logits": [1.0, 0.0, 0.0],
            })
    probe = V25.fisher_probe(captures, rows, layer=0)
    assert probe is not None
    assert abs(probe["accuracy"] - 0.5) < 0.2


def test_fisher_probe_degenerate_identical_data_returns_none():
    captures, rows = _synthetic_cell(8, 16, signal=0.0, seed=3)
    assert V25.fisher_probe(captures, rows, layer=0) is None


def test_apply_probe_transfers_to_fresh_data():
    fit_captures, fit_rows = _synthetic_cell(32, 16, signal=4.0, seed=7)
    held_captures, held_rows = _synthetic_cell(16, 16, signal=4.0, seed=99)
    probe = V25.fisher_probe(fit_captures, fit_rows, layer=0)
    assert V25.apply_probe(probe, held_captures, held_rows, layer=0) == 1.0


def test_concept_cross_validation_generalizes():
    captures, rows = _synthetic_cell(32, 16, signal=4.0, seed=7)
    accuracy = V25.concept_cross_validated_accuracy(captures, rows, layer=0)
    assert accuracy == 1.0
    flat_captures, flat_rows = _synthetic_cell(32, 16, signal=0.0, seed=8)
    flat_accuracy = V25.concept_cross_validated_accuracy(flat_captures, flat_rows, layer=0)
    assert abs(flat_accuracy - 0.5) < 0.25


def test_shuffled_label_floor_destroys_condition_leakage():
    captures, rows = _synthetic_cell(32, 16, signal=4.0, seed=7)
    shuffled = V25.shuffled_label_accuracy(captures, rows, layer=0)
    assert shuffled < V25.SHUFFLED_LABEL_FLOOR


def test_cell_analysis_selects_signal_layer():
    rng = np.random.default_rng(13)
    captures, rows = [], []
    for index in range(32):
        base = rng.normal(0.0, 1.0, size=(8,)).astype(np.float32)
        concept = V25.CONCEPTS[index % 8]
        for condition in ("activation", "none", "text"):
            noise_layer = base
            signal_layer = base + (6.0 if condition == "activation" else 0.0)
            text_layer = base + (6.0 if condition == "text" else 0.0)
            captures.append({
                **{layer: noise_layer.astype(np.float16) for layer in range(10)},
                5: signal_layer.astype(np.float16),
                9: text_layer.astype(np.float16),
            })
            rows.append({
                "trial_id": f"syn-{index}-{condition}", "split": "fit",
                "concept": concept, "wrapper": index % 4, "condition": condition,
                "correct_token": " A", "prompt": "syn",
                "token": " A", "probabilities": [1.0, 0.0, 0.0],
                "logits": [1.0, 0.0, 0.0],
            })
    original_layer_count = V25.LAYER_COUNT
    V25.LAYER_COUNT = 10
    try:
        analysis = V25.cell_analysis(captures, rows)
    finally:
        V25.LAYER_COUNT = original_layer_count
    assert analysis["best_layer"] == 5
    assert analysis["fit_probe_accuracy"] == 1.0
    assert analysis["text_vs_none_accuracy"] == 1.0
    assert analysis["text_vs_none_best_layer"] == 9
    assert analysis["shuffled_label_accuracy"] < V25.SHUFFLED_LABEL_FLOOR
    assert len(analysis["layer_accuracies"]) == 10


def test_behavioral_effect_silent_and_active_cells():
    def make_rows(activation_logits):
        rows = []
        for index in range(32):
            concept = V25.CONCEPTS[index % 8]
            for condition in ("activation", "none", "text"):
                logits = activation_logits if condition == "activation" else [1.0, 0.5, 0.25]
                rows.append({
                    "trial_id": f"syn-{index}-{condition}", "split": "fit",
                    "concept": concept, "wrapper": index % 4, "condition": condition,
                    "correct_token": " A", "prompt": "syn",
                    "token": " A", "probabilities": [1.0, 0.0, 0.0],
                    "logits": logits,
                })
        return rows

    silent = V25.behavioral_effect(make_rows([1.0, 0.5, 0.25]), site=10, strength=2.0)
    assert silent["silent"] is True
    active = V25.behavioral_effect(make_rows([0.0, 2.5, 0.5]), site=21, strength=2.0)
    assert active["silent"] is False
    assert active["top1_token_change_rate"] == 1.0


def test_bootstrap_binary_perfect_and_chance():
    def scored_rows(prob: float) -> list[dict]:
        return [
            {"concept": concept, "probe_correct": (index % 100) / 100.0 < prob}
            for concept in V25.CONCEPTS[12:] for index in range(100)
        ]

    perfect = V25.bootstrap_binary(scored_rows(1.0))
    assert perfect["lower_95"] > 0
    chance = V25.bootstrap_binary(scored_rows(0.5))
    assert chance["lower_95"] <= 0


def _fork_result(classification: str, probe: float, report: float, lower: float) -> dict:
    return {
        "classification": classification,
        "probe_accuracy": probe,
        "self_report_accuracy": report,
        "fork_margin_observed": probe - report,
        "bootstrap": {"lower_95": lower, "mean_over_chance": 0.0, "upper_95": 0.0},
    }


def test_validator_fork_semantics():
    VALIDATOR._validate_fork(_fork_result("InformationPresenceReportGapObserved", 0.90, 0.50, 0.6))
    VALIDATOR._validate_fork(_fork_result("InformationPresenceParityObserved", 0.90, 0.80, 0.6))
    VALIDATOR._validate_fork(_fork_result("InformationPresenceNoCandidate", 0.60, 0.50, -0.1))
    for bad in (
        _fork_result("InformationPresenceReportGapObserved", 0.90, 0.85, 0.6),
        _fork_result("InformationPresenceParityObserved", 0.90, 0.50, 0.6),
        _fork_result("InformationPresenceNoCandidate", 0.90, 0.50, 0.6),
        _fork_result("InformationPresenceReportGapObserved", 0.60, 0.30, -0.1),
        _fork_result("InformationPresenceReportGapObserved", 0.90, 0.50, 0.1),
    ):
        try:
            VALIDATOR._validate_fork(bad)
        except ValueError:
            continue
        raise AssertionError(f"validator accepted unsupported fork result: {bad['classification']}")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_stop_bundle(root: Path, result: dict, behavioral: list) -> None:
    root.mkdir(parents=True)
    (root / "behavioral-effect.json").write_text(json.dumps(behavioral, indent=2, sort_keys=True) + "\n")
    (root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    files = {path.name: _sha(path) for path in sorted(root.glob("*")) if path.is_file()}
    (root / "manifest.json").write_text(json.dumps({"files": files}, indent=2, sort_keys=True) + "\n")


def test_validator_accepts_silent_stop_bundle(tmp_path):
    cell = {
        "site": 21, "strength": 2.0, "pair_count": 32,
        "mean_abs_logit_shift": 0.0, "max_abs_logit_shift": 0.0,
        "top1_token_change_rate": 0.0, "silent": True,
    }
    result = {
        "classification": "ProbeTargetBehaviorallySilent",
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C", "claim_ceiling": V25.CLAIM,
        "assessment_unopened": True,
        "selected_configuration": {"site": 21, "strength": 2.0, "layer": 5},
        "selected_behavioral_effect": cell,
    }
    bundle = tmp_path / "silent"
    _write_stop_bundle(bundle, result, [cell])
    outcome = VALIDATOR.validate(bundle)
    assert outcome["valid"] is True


def test_validator_rejects_floor_stop_without_violations(tmp_path):
    cell = {
        "site": 21, "strength": 2.0, "pair_count": 32,
        "mean_abs_logit_shift": 1.0, "max_abs_logit_shift": 2.0,
        "top1_token_change_rate": 0.5, "silent": False,
    }
    result = {
        "classification": "ProbeControlFloorViolation",
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C", "claim_ceiling": V25.CLAIM,
        "assessment_unopened": True,
        "violations": [],
        "selected_configuration": {"site": 21, "strength": 2.0, "layer": 5},
        "shuffled_label_accuracy": 0.9,
        "text_vs_none_accuracy": 0.95,
    }
    bundle = tmp_path / "bad-floor"
    _write_stop_bundle(bundle, result, [cell])
    try:
        VALIDATOR.validate(bundle)
    except ValueError as exc:
        assert "without violations" in str(exc)
    else:
        raise AssertionError("validator accepted a floor stop without violations")


def test_validator_rejects_unknown_classification(tmp_path):
    cell = {
        "site": 21, "strength": 2.0, "pair_count": 32,
        "mean_abs_logit_shift": 0.0, "max_abs_logit_shift": 0.0,
        "top1_token_change_rate": 0.0, "silent": True,
    }
    result = {
        "classification": "UnexpectedFutureOutcome",
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C", "claim_ceiling": V25.CLAIM,
        "assessment_unopened": True,
    }
    bundle = tmp_path / "unknown-classification"
    _write_stop_bundle(bundle, result, [cell])
    manifest = json.loads((bundle / "manifest.json").read_text())
    manifest["files"]["result.json"] = _sha(bundle / "result.json")
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    try:
        VALIDATOR.validate(bundle)
    except ValueError as exc:
        assert "unknown classification" in str(exc)
    else:
        raise AssertionError("validator accepted an unknown classification")


def test_validator_rejects_fork_marked_assessment_unopened(tmp_path):
    result = _fork_result("InformationPresenceParityObserved", 0.90, 0.80, 0.2)
    result.update({
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C", "claim_ceiling": V25.CLAIM,
        "assessment_unopened": True,
    })
    bundle = tmp_path / "fork-marked-unopened"
    _write_stop_bundle(bundle, result, [])
    (bundle / "assessment-results.json").write_text(json.dumps({"rows": []}) + "\n")
    files = {path.name: _sha(path) for path in sorted(bundle.glob("*")) if path.name != "manifest.json"}
    (bundle / "manifest.json").write_text(json.dumps({"files": files}, indent=2, sort_keys=True) + "\n")
    try:
        VALIDATOR.validate(bundle)
    except ValueError as exc:
        assert "assessment marked unopened" in str(exc)
    else:
        raise AssertionError("validator accepted a fork result marked assessment unopened")
