import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]

SPEC = importlib.util.spec_from_file_location("astral_v24_tested", HERE / "v24.py")
V24 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V24
SPEC.loader.exec_module(V24)

VSPEC = importlib.util.spec_from_file_location("astral_v24_validator_tested", HERE / "validator_v24.py")
VALIDATOR = importlib.util.module_from_spec(VSPEC)
sys.modules[VSPEC.name] = VALIDATOR
VSPEC.loader.exec_module(VALIDATOR)


def test_fresh_corpus_census():
    rows = V24.V22.build_trials()
    assert len(rows) == 192
    assert Counter(row.split for row in rows) == {"fit": 96, "tune": 48, "assessment": 48}
    assert set(V24.CONCEPTS).isdisjoint(V24.V22_FROZEN_CONCEPTS)
    assert set(V24.CONCEPTS).isdisjoint(V24.V23_FROZEN_CONCEPTS)
    assert len(set(V24.CONCEPTS)) == 16


def test_activation_none_identity_and_label_balance():
    rows = V24.V22.build_trials()
    for concept in V24.CONCEPTS:
        for wrapper in range(4):
            selected = {row.condition: row for row in rows if row.concept == concept and row.wrapper == wrapper}
            assert selected["activation"].prompt == selected["none"].prompt
    assert set(row.correct_token for row in rows) == set(V24.V22.TOKENS)


def test_model_contract_is_proportional_and_distinct():
    assert V24.SITES == (10, 21, 32)
    assert V24.HIDDEN_SIZE == 3136
    assert V24.EXPECTED_LAYER_COUNT == 42
    assert V24.MODEL_PATH != V24.V22.V17.MODEL_PATH
    assert str(V24.MODEL_PATH) != str(V24.V22_PATH.parent)
    assert V24.CLAIM == "LocalDevelopmentHybridInstrumentCapabilityTierReplication"


def test_pattern_coverage_and_layer_types():
    pattern = list(V24.EXPECTED_PATTERN)
    assert len(pattern) == V24.EXPECTED_LAYER_COUNT
    for site in V24.SITES:
        assert site < len(pattern)
    site_types = {site: pattern[site] for site in V24.SITES}
    assert site_types == {10: "-", 21: "M", 32: "*"}
    attention_indices = [index for index, symbol in enumerate(pattern) if symbol == "*"]
    assert attention_indices == [12, 17, 24, 32]


def _fit_rows(logits_by_key: dict) -> list[dict]:
    rows = []
    for trial in V24.V22.build_trials():
        if trial.split != "fit":
            continue
        logits = logits_by_key[(trial.concept, trial.wrapper, trial.condition)]
        rows.append({
            "trial_id": trial.trial_id, "split": trial.split, "concept": trial.concept,
            "wrapper": trial.wrapper, "condition": trial.condition,
            "correct_token": trial.correct_token, "prompt": trial.prompt,
            "token": V24.V22.TOKENS[int(max(range(3), key=lambda i: logits[i]))],
            "probabilities": [0.0, 0.0, 0.0], "logits": logits,
        })
    return rows


def test_behavioral_effect_silent_cell():
    base = [1.0, 0.5, 0.25]
    rows = _fit_rows({
        (concept, wrapper, condition): base
        for concept in list(V24.CONCEPTS)[:8] for wrapper in range(4)
        for condition in ("activation", "text", "none")
    })
    cell = V24.behavioral_effect(rows, site=10, strength=2.0)
    assert cell["pair_count"] == 32
    assert cell["max_abs_logit_shift"] == 0.0
    assert cell["top1_token_change_rate"] == 0.0
    assert cell["silent"] is True


def test_behavioral_effect_active_cell():
    none_logits = [1.0, 0.5, 0.25]
    activation_logits = [0.0, 2.5, 0.5]

    def pick(concept, wrapper, condition):
        return activation_logits if condition == "activation" else none_logits

    rows = _fit_rows({
        (concept, wrapper, condition): pick(concept, wrapper, condition)
        for concept in list(V24.CONCEPTS)[:8] for wrapper in range(4)
        for condition in ("activation", "text", "none")
    })
    cell = V24.behavioral_effect(rows, site=21, strength=1.0)
    assert cell["pair_count"] == 32
    assert cell["max_abs_logit_shift"] == 2.0
    assert cell["top1_token_change_rate"] == 1.0
    assert cell["silent"] is False


def test_behavioral_effect_shift_without_top1_change_is_not_silent():
    # A shift at or above the threshold rescues silence even when the top-1
    # report token never changes.
    threshold = V24.BEHAVIORAL_SILENCE_LOGIT_SHIFT

    def pick(condition):
        return [1.0 + 2 * threshold, 0.5, 0.25] if condition == "activation" else [1.0, 0.5, 0.25]

    rows = _fit_rows({
        (concept, wrapper, condition): pick(condition)
        for concept in list(V24.CONCEPTS)[:8] for wrapper in range(4)
        for condition in ("activation", "text", "none")
    })
    cell = V24.behavioral_effect(rows, site=32, strength=0.5)
    assert cell["max_abs_logit_shift"] >= threshold
    assert cell["top1_token_change_rate"] == 0.0
    assert cell["silent"] is False


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_silent_bundle(root: Path, cell: dict) -> None:
    root.mkdir(parents=True)
    (root / "behavioral-effect.json").write_text(json.dumps([cell], indent=2, sort_keys=True) + "\n")
    (root / "result.json").write_text(json.dumps({
        "classification": "InstrumentBehaviorallySilent",
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C",
        "claim_ceiling": V24.CLAIM,
        "assessment_unopened": True,
        "selected_configuration": {"site": cell["site"], "strength": cell["strength"]},
        "selected_behavioral_effect": cell,
    }, indent=2, sort_keys=True) + "\n")
    files = {path.name: _sha(path) for path in sorted(root.glob("*")) if path.is_file()}
    (root / "manifest.json").write_text(json.dumps({"files": files}, indent=2, sort_keys=True) + "\n")


def test_validator_accepts_silent_stop(tmp_path):
    cell = {
        "site": 10, "strength": 2.0, "pair_count": 32,
        "mean_abs_logit_shift": 0.0, "max_abs_logit_shift": 0.0,
        "top1_token_change_rate": 0.0, "silent": True,
    }
    bundle = tmp_path / "silent-bundle"
    _write_silent_bundle(bundle, cell)
    outcome = VALIDATOR.validate(bundle)
    assert outcome["valid"] is True
    assert outcome["classification"] == "InstrumentBehaviorallySilent"


def test_validator_rejects_non_silent_selected_cell(tmp_path):
    cell = {
        "site": 10, "strength": 2.0, "pair_count": 32,
        "mean_abs_logit_shift": 0.5, "max_abs_logit_shift": 0.9,
        "top1_token_change_rate": 0.5, "silent": False,
    }
    bundle = tmp_path / "bad-bundle"
    _write_silent_bundle(bundle, cell)
    try:
        VALIDATOR.validate(bundle)
    except ValueError as exc:
        assert "silent selected cell" in str(exc)
    else:
        raise AssertionError("validator accepted a non-silent silent stop")


def test_validator_rejects_census_drift(tmp_path):
    cell = {
        "site": 10, "strength": 2.0, "pair_count": 32,
        "mean_abs_logit_shift": 0.0, "max_abs_logit_shift": 0.0,
        "top1_token_change_rate": 0.0, "silent": True,
    }
    bundle = tmp_path / "drift-bundle"
    _write_silent_bundle(bundle, cell)
    (bundle / "stray.json").write_text("{}\n")
    try:
        VALIDATOR.validate(bundle)
    except ValueError as exc:
        assert "census" in str(exc)
    else:
        raise AssertionError("validator accepted a drifted census")
