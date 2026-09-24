"""End-to-end ranking action, proof, store, replay, and export coverage."""

from tools.proof_carrying_nano_interp_v1.ranking import (
    DeterministicOptionScorer,
    HypothesisOption,
    HypothesisOptionSet,
    HypothesisRankingNano,
    context_digest,
)
from tools.proof_carrying_nano_interp_v1.runtime import ToyHostSlice
from tools.proof_carrying_nano_interp_v1.store import ConcurrentStore


def test_ranking_action_is_stored_checked_replayable_and_exportable(tmp_path):
    scorer = DeterministicOptionScorer(identity="deterministic-option-scorer-v1")
    option_set = HypothesisOptionSet.create(
        context_digest=context_digest({"prompt": "alpha", "layer": 1}),
        scorer_identity=scorer.identity,
        options=(
            HypothesisOption(candidate_id="feature:0", kind="feature"),
            HypothesisOption(candidate_id="circuit:7", kind="circuit"),
        ),
    )
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = HypothesisRankingNano(
        identity="ranking-nano-v1", scorer=scorer
    ).attach(host, layer=1, site="residual")
    trace = host.capture(
        prompt="alpha",
        activation=(3, 1),
        seed=7,
        layer=1,
        site="residual",
    )

    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        action, proof = attachment.run_and_record(
            trace,
            option_set,
            scores=(2, 7),
            store=store,
            timestamp="2026-09-16T12:00:00Z",
        )
        proven = store.query_proven_claims(layer=1)
        bundle = store.export_bundle(action_digest=action.action_digest)
        integrity = store.validate_integrity()

    assert proof.status == "checked", proof.diagnostics
    assert proven[0]["action_digest"] == action.action_digest
    assert attachment.replay(action).action_digest == action.action_digest
    assert bundle["summary"].startswith("hypothesis_ranking at layer 1 residual observed value")
    assert integrity == {
        "state_slice": "proof-carrying-nano-interp-v1",
        "actions": 1,
        "proof_attempts": 1,
        "checked_proofs": 1,
    }
