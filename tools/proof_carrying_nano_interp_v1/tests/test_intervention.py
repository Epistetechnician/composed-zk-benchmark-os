"""Causal intervention behavior for the proof-carrying nano V1 slice."""

from dataclasses import replace

import pytest

from tools.proof_carrying_nano_interp_v1.intervention import (
    CausalInterventionNano,
    InterventionSpec,
)
from tools.proof_carrying_nano_interp_v1.proof import LeanProofEngine
from tools.proof_carrying_nano_interp_v1.protocol import canonical_digest
from tools.proof_carrying_nano_interp_v1.ranking import (
    DeterministicOptionScorer,
    HypothesisOption,
    HypothesisOptionSet,
    HypothesisRankingNano,
    context_digest,
)
from tools.proof_carrying_nano_interp_v1.runtime import ToyHostSlice
from tools.proof_carrying_nano_interp_v1.store import ConcurrentStore, StoreError


def test_intervention_action_records_exact_effect_and_noop_control():
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = CausalInterventionNano(identity="causal-intervention-nano-v1").attach(
        host, layer=1, site="residual"
    )
    trace = host.capture(
        prompt="alpha",
        activation=(3, 1),
        seed=7,
        layer=1,
        site="residual",
    )
    spec = InterventionSpec.create(
        context_digest=trace.host_context_hash,
        intervention_id="replace-feature-0",
        index=0,
        replacement=9,
    )

    action = attachment.run(
        trace,
        spec,
        timestamp="2026-09-16T12:00:00Z",
    )

    assert action.outputs == {
        "control": {
            "delta": [0, 0],
            "effect": 0,
            "kind": "no_op",
            "post_activation": [3, 1],
        },
        "delta": [6, 0],
        "effect": 6,
        "effect_index": 0,
        "post_activation": [9, 1],
        "pre_activation": [3, 1],
        "status": "InterventionObserved",
    }
    assert action.claim["intervention_spec_digest"] == spec.spec_digest
    assert action.claim["type"] == "intervention_effect_exact"


def test_intervention_effect_proof_is_kernel_checked():
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = CausalInterventionNano(identity="causal-intervention-nano-v1").attach(
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
        InterventionSpec.create(
            context_digest=trace.host_context_hash,
            intervention_id="replace-feature-0",
            index=0,
            replacement=9,
        ),
        timestamp="2026-09-16T12:00:00Z",
    )

    proof = LeanProofEngine().attempt(action)

    assert proof.status == "checked", proof.diagnostics
    assert "replaceAt" in proof.source
    assert "vectorDelta" in proof.source
    assert "[6, 0]" in proof.statement
    assert "[0, 0]" in proof.statement


def test_intervention_composes_with_ranking_in_store_and_bundle(tmp_path):
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    trace = host.capture(
        prompt="alpha",
        activation=(3, 1),
        seed=7,
        layer=1,
        site="residual",
    )
    scorer = DeterministicOptionScorer(identity="deterministic-option-scorer-v1")
    option_set = HypothesisOptionSet.create(
        context_digest=context_digest({"prompt": "alpha", "layer": 1}),
        scorer_identity=scorer.identity,
        options=(
            HypothesisOption(candidate_id="feature:0", kind="feature"),
            HypothesisOption(candidate_id="circuit:7", kind="circuit"),
        ),
    )
    ranking = HypothesisRankingNano(identity="ranking-nano-v1", scorer=scorer).attach(
        host, layer=1, site="residual"
    ).run(
        trace,
        option_set,
        scores=(2, 7),
        timestamp="2026-09-16T12:00:00Z",
    )
    intervention = CausalInterventionNano(identity="causal-intervention-nano-v1").attach(
        host, layer=1, site="residual"
    )
    spec = InterventionSpec.create(
        context_digest=trace.host_context_hash,
        intervention_id="replace-feature-0",
        index=0,
        replacement=9,
    )

    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        store.commit_action(ranking)
        with pytest.raises(StoreError, match="no checked proof"):
            intervention.run_and_record(
                trace,
                spec,
                hypothesis_action=ranking,
                store=store,
                timestamp="2026-09-16T12:00:01Z",
            )
        store.commit_proof(LeanProofEngine().attempt(ranking))
        action, proof = intervention.run_and_record(
            trace,
            spec,
            hypothesis_action=ranking,
            store=store,
            timestamp="2026-09-16T12:00:01Z",
        )
        observations = store.query_interventions(layer=1, intervention_id=spec.intervention_id)
        bundle = store.export_bundle(action_digest=action.action_digest)
        validation = store.validate_bundle(bundle)

    assert proof.status == "checked", proof.diagnostics
    assert len(observations) == 1
    assert observations[0]["action"]["inputs"]["hypothesis_action_digest"] == ranking.action_digest
    assert bundle["status"] == "InterventionObserved"
    assert validation["checked_proofs"] == 1
    assert intervention.replay(action, hypothesis_action=ranking).action_digest == action.action_digest


def test_intervention_spec_tampering_and_context_mismatch_fail_closed(tmp_path):
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    trace = host.capture(
        prompt="alpha", activation=(3, 1), seed=7, layer=1, site="residual"
    )
    spec = InterventionSpec.create(
        context_digest=trace.host_context_hash,
        intervention_id="replace-feature-0",
        index=0,
        replacement=9,
    )
    tampered = spec.to_dict()
    tampered["replacement"] = 99

    with pytest.raises(ValueError, match="digest mismatch"):
        InterventionSpec.from_dict(tampered)

    attachment = CausalInterventionNano(identity="causal-intervention-nano-v1").attach(
        host, layer=1, site="residual"
    )
    wrong_context = InterventionSpec.create(
        context_digest=canonical_digest({"different": True}),
        intervention_id="replace-feature-0",
        index=0,
        replacement=9,
    )
    with pytest.raises(ValueError, match="context does not match"):
        attachment.run(
            trace,
            wrong_context,
            timestamp="2026-09-16T12:00:00Z",
        )

    with pytest.raises(StoreError, match="reference is unknown"):
        with ConcurrentStore(tmp_path / "unknown-reference.sqlite3") as store:
            action = attachment.run(
                trace,
                spec,
                hypothesis_action=None,
                timestamp="2026-09-16T12:00:00Z",
            )
            unknown_digest = "sha256:" + "f" * 64
            action_inputs = {**action.inputs, "hypothesis_action_digest": unknown_digest}
            action_claim = {**action.claim, "hypothesis_action_digest": unknown_digest}
            forged = replace(action, inputs=action_inputs, claim=action_claim)
            forged = replace(forged, action_digest=canonical_digest(forged.unsigned_dict()))
            store.commit_action(forged)


def test_store_flags_contradictory_intervention_effects(tmp_path):
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = CausalInterventionNano(identity="causal-intervention-nano-v1").attach(
        host, layer=1, site="residual"
    )
    spec = None
    actions = []
    for activation, timestamp in [
        ((3, 1), "2026-09-16T12:00:00Z"),
        ((5, 1), "2026-09-16T12:00:01Z"),
    ]:
        trace = host.capture(
            prompt="alpha",
            activation=activation,
            seed=7,
            layer=1,
            site="residual",
        )
        spec = spec or InterventionSpec.create(
            context_digest=trace.host_context_hash,
            intervention_id="replace-feature-0",
            index=0,
            replacement=9,
        )
        actions.append(
            attachment.run(trace, spec, timestamp=timestamp)
        )

    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        for action in actions:
            store.commit_action(action)
            proof = LeanProofEngine().attempt(action)
            assert proof.status == "checked", proof.diagnostics
            store.commit_proof(proof)
        conflicts = store.detect_intervention_conflicts()

    assert len(conflicts) == 1
    assert conflicts[0]["values"] == [4, 6]
