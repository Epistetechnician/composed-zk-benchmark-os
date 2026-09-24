"""Hypothesis-ranking behavior for the proof-carrying nano V1 slice."""

import pytest

from tools.proof_carrying_nano_interp_v1.ranking import (
    DeterministicOptionScorer,
    HypothesisOption,
    HypothesisOptionSet,
    HypothesisRankingNano,
    context_digest,
)
from tools.proof_carrying_nano_interp_v1.proof import LeanProofEngine
from tools.proof_carrying_nano_interp_v1.runtime import ToyHostSlice
from tools.proof_carrying_nano_interp_v1.store import ConcurrentStore


def _option_set(scorer):
    return HypothesisOptionSet.create(
        context_digest=context_digest({"prompt": "alpha", "layer": 1}),
        scorer_identity=scorer.identity,
        options=(
            HypothesisOption(candidate_id="feature:0", kind="feature"),
            HypothesisOption(candidate_id="circuit:7", kind="circuit"),
            HypothesisOption(candidate_id="intervention:2", kind="intervention"),
        ),
    )


def test_ranking_nano_emits_exact_probabilities_and_hypothesis_status():
    scorer = DeterministicOptionScorer(identity="deterministic-option-scorer-v1")
    option_set = _option_set(scorer)
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = HypothesisRankingNano(identity="ranking-nano-v1", scorer=scorer).attach(
        host, layer=1, site="residual"
    )
    trace = host.capture(
        prompt="alpha",
        activation=(3, 1),
        seed=7,
        layer=1,
        site="residual",
    )

    action = attachment.run(
        trace,
        option_set,
        scores=(2, 7, 1),
        timestamp="2026-09-16T12:00:00Z",
    )

    assert action.outputs["status"] == "HypothesisOnly"
    assert action.outputs["selected_option"] == "circuit:7"
    assert action.outputs["selected_index"] == 1
    assert action.outputs["probabilities"] == [
        {"denominator": 10, "numerator": 2},
        {"denominator": 10, "numerator": 7},
        {"denominator": 10, "numerator": 1},
    ]
    assert action.claim["option_set_digest"] == option_set.option_set_digest
    assert action.claim["type"] == "hypothesis_ranking"


def test_option_order_and_payload_tampering_change_or_break_identity():
    scorer = DeterministicOptionScorer(identity="deterministic-option-scorer-v1")
    option_set = _option_set(scorer)
    reordered = HypothesisOptionSet.create(
        context_digest=option_set.context_digest,
        scorer_identity=scorer.identity,
        options=tuple(reversed(option_set.options)),
    )

    assert reordered.option_set_digest != option_set.option_set_digest
    tampered = option_set.to_dict()
    tampered["options"][0]["candidate_id"] = "circuit:forged"
    with pytest.raises(ValueError, match="option set digest mismatch"):
        HypothesisOptionSet.from_dict(tampered)

    with pytest.raises(ValueError, match="supported kind"):
        HypothesisOption(candidate_id="unknown:1", kind="unknown")


def test_deterministic_adapter_is_stable_and_order_sensitive():
    scorer = DeterministicOptionScorer(identity="deterministic-option-scorer-v1")
    option_set = _option_set(scorer)

    first = scorer.rank(option_set)
    second = scorer.rank(HypothesisOptionSet.from_dict(option_set.to_dict()))

    assert first == second
    assert len(first["probabilities"]) == len(option_set.options)
    assert all(
        probability["denominator"] > 0
        and probability["numerator"] > 0
        for probability in first["probabilities"]
    )


def test_action_selection_tampering_is_digest_bound():
    scorer = DeterministicOptionScorer(identity="deterministic-option-scorer-v1")
    option_set = _option_set(scorer)
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = HypothesisRankingNano(identity="ranking-nano-v1", scorer=scorer).attach(
        host, layer=1, site="residual"
    )
    action = attachment.run(
        host.capture(
            prompt="alpha", activation=(3, 1), seed=7, layer=1, site="residual"
        ),
        option_set,
        scores=(2, 7, 1),
        timestamp="2026-09-16T12:00:00Z",
    )
    tampered = action.to_dict()
    tampered["outputs"] = {**tampered["outputs"], "selected_option": "feature:forged"}

    with pytest.raises(ValueError, match="action digest mismatch"):
        ConcurrentStore.assert_action_digest(tampered)


@pytest.mark.parametrize("scores", [(-1, 2, 1), (float("nan"), 2, 1), (1.0, 2, 1), (0, 0, 0)])
def test_scorer_rejects_nonfinite_negative_or_zero_score_vectors(scores):
    scorer = DeterministicOptionScorer(identity="deterministic-option-scorer-v1")
    with pytest.raises(ValueError, match="scores|score weights"):
        scorer.rank(_option_set(scorer), scores=scores)


def test_ranking_replay_is_digest_stable_and_host_remains_read_only():
    scorer = DeterministicOptionScorer(identity="deterministic-option-scorer-v1")
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = HypothesisRankingNano(identity="ranking-nano-v1", scorer=scorer).attach(
        host, layer=1, site="residual"
    )
    trace = host.capture(
        prompt="alpha",
        activation=(3, 1),
        seed=7,
        layer=1,
        site="residual",
    )
    before = host.snapshot()

    first = attachment.run(
        trace,
        _option_set(scorer),
        scores=(2, 7, 1),
        timestamp="2026-09-16T12:00:00Z",
    )
    second = attachment.replay(first)

    assert first.action_digest == second.action_digest
    assert host.snapshot() == before


def test_store_flags_contradictory_checked_rankings_separately(tmp_path):
    scorer = DeterministicOptionScorer(identity="deterministic-option-scorer-v1")
    option_set = _option_set(scorer)
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = HypothesisRankingNano(identity="ranking-nano-v1", scorer=scorer).attach(
        host, layer=1, site="residual"
    )
    trace = host.capture(
        prompt="alpha", activation=(3, 1), seed=7, layer=1, site="residual"
    )
    actions = [
        attachment.run(
            trace,
            option_set,
            scores=scores,
            timestamp=timestamp,
        )
        for scores, timestamp in [
            ((2, 7, 1), "2026-09-16T12:00:00Z"),
            ((8, 1, 1), "2026-09-16T12:00:01Z"),
        ]
    ]

    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        for action in actions:
            store.commit_action(action)
            proof = LeanProofEngine().attempt(action)
            assert proof.status == "checked", proof.diagnostics
            store.commit_proof(proof)
        hypotheses = store.query_hypotheses(
            layer=1, option_set_digest=option_set.option_set_digest
        )
        conflicts = store.detect_hypothesis_conflicts()
        bundle = store.export_bundle(action_digest=actions[0].action_digest)
        bundle_validation = store.validate_bundle(bundle)

    assert len(hypotheses) == 2
    assert {item["action"]["outputs"]["status"] for item in hypotheses} == {"HypothesisOnly"}
    assert len(conflicts) == 1
    assert conflicts[0]["values"] == ["circuit:7", "feature:0"]
    assert bundle["status"] == "HypothesisOnly"
    assert bundle_validation["checked_proofs"] == 1
    assert ConcurrentStore(tmp_path / "store.sqlite3").detect_conflicts() == []
