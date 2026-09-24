"""First contract test for the pinned Jevlike adapter.

State slice: proof-carrying-nano-interp-jevlike-adapter-v1.
"""

from pathlib import Path
from copy import deepcopy
from dataclasses import replace

import pytest

from tools.proof_carrying_nano_interp_v1.ranking import (
    HypothesisOption,
    HypothesisOptionSet,
    context_digest,
)

from tools.proof_carrying_nano_interp_jevlike_adapter_v1.adapter import (
    AdapterError,
    JevlikeAdapterConfig,
    JevlikeHypothesisRankingNano,
    JevlikeOptionScorer,
    PinnedJevlikeRunner,
)
from tools.proof_carrying_nano_interp_jevlike_adapter_v1.proof import (
    JevlikeLeanProofEngine,
)
from tools.proof_carrying_nano_interp_jevlike_adapter_v1.store import (
    StoreError,
    JevlikeHypothesisStore,
)
from tools.proof_carrying_nano_interp_v1.protocol import ProtocolError, canonical_digest
from tools.proof_carrying_nano_interp_v1.runtime import ToyHostSlice


UPSTREAM_REVISION = "94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452"


class FakeRunner:
    def __init__(self, scores: tuple[object, ...] = (0.2, 0.7, 0.1)) -> None:
        self.validated = False
        self.calls: list[tuple[str, tuple[str, ...]]] = []
        self.scores = scores

    def validate(self, config: JevlikeAdapterConfig) -> None:
        self.validated = config.upstream_revision == UPSTREAM_REVISION

    def score(
        self,
        context: str,
        options: tuple[str, ...],
        *,
        config: JevlikeAdapterConfig,
    ) -> tuple[float, ...]:
        self.calls.append((context, options))
        return self.scores


def _option_set(identity: str, context: str) -> HypothesisOptionSet:
    return HypothesisOptionSet.create(
        context_digest=context_digest(context),
        scorer_identity=identity,
        options=(
            HypothesisOption(candidate_id="feature:0", kind="feature"),
            HypothesisOption(candidate_id="circuit:7", kind="circuit"),
            HypothesisOption(candidate_id="intervention:replace", kind="intervention"),
        ),
    )


def _action_fixture(
    *, scores: tuple[object, ...] = (0.2, 0.7, 0.1)
) -> tuple[object, object, FakeRunner, HypothesisOptionSet, str]:
    identity = "jevlike-tiny-pinned-v1"
    context = "layer 3 residual activation: [3, 1]"
    option_set = _option_set(identity, context)
    runner = FakeRunner(scores)
    config = JevlikeAdapterConfig(
        upstream_revision=UPSTREAM_REVISION,
        checkout_path=Path("/external/jevlike"),
        scorer_checkpoint_digest="sha256:" + "1" * 64,
        encoder_identity="tiny-byte-v1",
        runtime_identity="torch-pinned-test-v1",
        device="cpu",
        seed=7,
        quantization_scale=1000,
    )
    nano = JevlikeHypothesisRankingNano(
        identity=identity,
        scorer=JevlikeOptionScorer(identity=identity, config=config, runner=runner),
    )
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = nano.attach(host, layer=3, site="residual")
    trace = host.capture(
        prompt="alpha",
        activation=(3, 1),
        seed=7,
        layer=3,
        site="residual",
    )
    return (
        attachment.run(
            trace,
            option_set,
            context=context,
            timestamp="2026-09-16T12:00:00Z",
        ),
        attachment,
        runner,
        option_set,
        context,
    )


def test_pinned_scores_become_exact_weights_and_select_in_order() -> None:
    identity = "jevlike-tiny-pinned-v1"
    context = "layer 3 residual activation: [3, 1]"
    option_set = HypothesisOptionSet.create(
        context_digest=context_digest(context),
        scorer_identity=identity,
        options=(
            HypothesisOption(candidate_id="feature:0", kind="feature"),
            HypothesisOption(candidate_id="circuit:7", kind="circuit"),
            HypothesisOption(candidate_id="intervention:replace", kind="intervention"),
        ),
    )
    runner = FakeRunner()
    config = JevlikeAdapterConfig(
        upstream_revision=UPSTREAM_REVISION,
        checkout_path=Path("/external/jevlike"),
        scorer_checkpoint_digest="sha256:" + "1" * 64,
        encoder_identity="tiny-byte-v1",
        runtime_identity="torch-pinned-test-v1",
        device="cpu",
        seed=7,
        quantization_scale=1000,
    )

    result = JevlikeOptionScorer(
        identity=identity,
        config=config,
        runner=runner,
    ).rank(context=context, option_set=option_set)

    assert runner.validated is True
    assert runner.calls == [
        (
            context,
            ("feature:0", "circuit:7", "intervention:replace"),
        )
    ]
    assert result.quantized_scores == (200, 700, 100)
    assert result.denominator == 1000
    assert result.probabilities == (
        {"denominator": 1000, "numerator": 200},
        {"denominator": 1000, "numerator": 700},
        {"denominator": 1000, "numerator": 100},
    )
    assert result.selected_index == 1
    assert result.selected_option == "circuit:7"


def test_jevlike_action_replays_proves_stores_and_exports_hypothesis_only(tmp_path) -> None:
    identity = "jevlike-tiny-pinned-v1"
    context = "layer 3 residual activation: [3, 1]"
    option_set = HypothesisOptionSet.create(
        context_digest=context_digest(context),
        scorer_identity=identity,
        options=(
            HypothesisOption(candidate_id="feature:0", kind="feature"),
            HypothesisOption(candidate_id="circuit:7", kind="circuit"),
            HypothesisOption(candidate_id="intervention:replace", kind="intervention"),
        ),
    )
    config = JevlikeAdapterConfig(
        upstream_revision=UPSTREAM_REVISION,
        checkout_path=Path("/external/jevlike"),
        scorer_checkpoint_digest="sha256:" + "1" * 64,
        encoder_identity="tiny-byte-v1",
        runtime_identity="torch-pinned-test-v1",
        device="cpu",
        seed=7,
        quantization_scale=1000,
    )
    nano = JevlikeHypothesisRankingNano(
        identity=identity,
        scorer=JevlikeOptionScorer(
            identity=identity,
            config=config,
            runner=FakeRunner(),
        ),
    )
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = nano.attach(host, layer=3, site="residual")
    trace = host.capture(
        prompt="alpha",
        activation=(3, 1),
        seed=7,
        layer=3,
        site="residual",
    )

    action = attachment.run(
        trace,
        option_set,
        context=context,
        timestamp="2026-09-16T12:00:00Z",
    )
    proof = JevlikeLeanProofEngine().attempt(action)

    assert action.outputs["status"] == "HypothesisOnly"
    assert action.inputs["quantized_scores"] == [200, 700, 100]
    assert attachment.replay(action).action_digest == action.action_digest
    assert proof.status == "checked", proof.diagnostics
    with JevlikeHypothesisStore(tmp_path / "store.sqlite3") as store:
        store.commit_action(action)
        store.commit_proof(proof)
        hypotheses = store.query_hypotheses(
            layer=3,
            candidate_id="circuit:7",
            option_set_digest=option_set.option_set_digest,
        )
        bundle = store.export_bundle(action_digest=action.action_digest)
        integrity = store.validate_integrity()

    assert bundle["status"] == "HypothesisOnly"
    assert [item["action_digest"] for item in hypotheses] == [action.action_digest]
    assert JevlikeHypothesisStore.validate_bundle(bundle)["checked_proofs"] == 1
    assert integrity == {
        "state_slice": "proof-carrying-nano-interp-jevlike-adapter-v1",
        "actions": 1,
        "proof_attempts": 1,
        "checked_proofs": 1,
    }


@pytest.mark.parametrize("scores", [(float("nan"), 0.7, 0.1), (-0.2, 0.7, 0.1)])
def test_jevlike_rejects_nonfinite_and_negative_scores(scores) -> None:
    identity = "jevlike-tiny-pinned-v1"
    context = "layer 3 residual activation: [3, 1]"
    option_set = _option_set(identity, context)
    config = JevlikeAdapterConfig(
        upstream_revision=UPSTREAM_REVISION,
        checkout_path=Path("/external/jevlike"),
        scorer_checkpoint_digest="sha256:" + "1" * 64,
        encoder_identity="tiny-byte-v1",
        runtime_identity="torch-pinned-test-v1",
        device="cpu",
        seed=7,
        quantization_scale=1000,
    )
    scorer = JevlikeOptionScorer(
        identity=identity,
        config=config,
        runner=FakeRunner(scores),
    )

    with pytest.raises(AdapterError, match="finite and non-negative"):
        scorer.rank(context=context, option_set=option_set)


def test_replay_uses_recorded_scores_and_rejects_reordered_options() -> None:
    action, attachment, runner, option_set, _context = _action_fixture()

    replayed = attachment.replay(action)
    assert replayed.action_digest == action.action_digest
    assert len(runner.calls) == 1

    forged = deepcopy(action.to_dict())
    forged["inputs"]["option_set"]["options"] = list(
        reversed(forged["inputs"]["option_set"]["options"])
    )
    forged_unsigned = {key: value for key, value in forged.items() if key != "action_digest"}
    reordered = replace(
        action,
        inputs=forged["inputs"],
        action_digest=canonical_digest(forged_unsigned),
    )
    with pytest.raises(AdapterError, match="action inputs cannot be replayed"):
        attachment.replay(reordered)


def test_store_rejects_digest_tampering_and_proof_rejects_rebound_selection(tmp_path) -> None:
    action, _attachment, _runner, _option_set, _context = _action_fixture()
    tampered = deepcopy(action.to_dict())
    tampered["inputs"]["quantized_scores"][1] = 1
    tampered_action = replace(
        action,
        inputs=tampered["inputs"],
        action_digest=action.action_digest,
    )
    with JevlikeHypothesisStore(tmp_path / "tamper.sqlite3") as store:
        with pytest.raises(StoreError, match="action digest mismatch"):
            store.commit_action(tampered_action)

    rebound = deepcopy(action.to_dict())
    rebound["outputs"]["selected_index"] = 0
    rebound["outputs"]["selected_option"] = "feature:0"
    rebound["outputs"]["selected_option_kind"] = "feature"
    rebound["claim"]["selected_index"] = 0
    rebound["claim"]["selected_option"] = "feature:0"
    rebound["claim"]["selected_option_kind"] = "feature"
    unsigned = {key: value for key, value in rebound.items() if key != "action_digest"}
    rebound_action = replace(
        action,
        outputs=rebound["outputs"],
        claim=rebound["claim"],
        action_digest=canonical_digest(unsigned),
    )
    with pytest.raises(ProtocolError, match="selected option"):
        JevlikeLeanProofEngine().attempt(rebound_action)

    forged_scores = deepcopy(action.to_dict())
    forged_scores["inputs"]["external_scores"][0] = "NaN"
    forged_scores_unsigned = {
        key: value for key, value in forged_scores.items() if key != "action_digest"
    }
    forged_score_action = replace(
        action,
        inputs=forged_scores["inputs"],
        action_digest=canonical_digest(forged_scores_unsigned),
    )
    with pytest.raises(ProtocolError, match="finite and non-negative"):
        JevlikeLeanProofEngine().attempt(forged_score_action)


def test_contradictory_checked_rankings_are_reported_under_same_claim_key(tmp_path) -> None:
    first, attachment, _runner, option_set, context = _action_fixture(scores=(0.2, 0.7, 0.1))
    second_runner = FakeRunner((0.8, 0.1, 0.1))
    second_scorer = JevlikeOptionScorer(
        identity=attachment.nano.identity,
        config=attachment.nano.scorer.config,
        runner=second_runner,
    )
    second_nano = JevlikeHypothesisRankingNano(
        identity=attachment.nano.identity,
        scorer=second_scorer,
    )
    second = second_nano.attach(attachment.host, layer=3, site="residual").run(
        attachment.host.capture(
            prompt="alpha",
            activation=(3, 1),
            seed=7,
            layer=3,
            site="residual",
        ),
        option_set,
        context=context,
        timestamp="2026-09-16T12:00:01Z",
    )
    with JevlikeHypothesisStore(tmp_path / "conflict.sqlite3") as store:
        for action in (first, second):
            store.commit_action(action)
            proof = JevlikeLeanProofEngine().attempt(action)
            assert proof.status == "checked", proof.diagnostics
            store.commit_proof(proof)
        conflicts = store.detect_hypothesis_conflicts()

    assert len(conflicts) == 1
    assert conflicts[0]["values"] == ["circuit:7", "feature:0"]


def test_unavailable_lean_checker_is_recorded_as_a_failed_attempt() -> None:
    action, _attachment, _runner, _option_set, _context = _action_fixture()

    attempt = JevlikeLeanProofEngine(command=("lean-executable-not-installed",)).attempt(action)

    assert attempt.status == "failed"
    assert attempt.diagnostics == ("executable not found: lean-executable-not-installed",)


def test_pinned_runner_rejects_wrong_checkout_revision_without_loading_jevlike(
    tmp_path, monkeypatch
) -> None:
    checkpoint = tmp_path / "scorer.pt"
    checkpoint.write_bytes(b"test checkpoint")
    config = JevlikeAdapterConfig(
        upstream_revision=UPSTREAM_REVISION,
        checkout_path=tmp_path / "checkout",
        scorer_checkpoint_digest="sha256:" + "1" * 64,
        encoder_identity="tiny-byte-v1",
        runtime_identity="torch-pinned-test-v1",
        device="cpu",
        seed=7,
        scorer_checkpoint_path=checkpoint,
    )
    (config.checkout_path / ".git").mkdir(parents=True)
    monkeypatch.setattr(
        "tools.proof_carrying_nano_interp_jevlike_adapter_v1.adapter.subprocess.run",
        lambda *args, **kwargs: type("Result", (), {"stdout": "deadbeef\n"})(),
    )

    with pytest.raises(AdapterError, match="unexpected Jevlike revision"):
        PinnedJevlikeRunner().validate(config)
