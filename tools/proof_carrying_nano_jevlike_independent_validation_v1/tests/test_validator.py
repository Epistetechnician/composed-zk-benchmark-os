"""Independent Jevlike bundle validation tests.

State slice: proof-carrying-nano-jevlike-independent-validation-v1.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.proof_carrying_nano_interp_v1.protocol import canonical_digest
from tools.proof_carrying_nano_interp_v1.ranking import (
    HypothesisOption,
    HypothesisOptionSet,
    context_digest,
)
from tools.proof_carrying_nano_interp_v1.runtime import ToyHostSlice
from tools.proof_carrying_nano_interp_jevlike_adapter_v1.adapter import (
    JevlikeAdapterConfig,
    JevlikeHypothesisRankingNano,
    JevlikeOptionScorer,
)
from tools.proof_carrying_nano_interp_jevlike_adapter_v1.proof import (
    JevlikeLeanProofEngine,
)
from tools.proof_carrying_nano_interp_jevlike_adapter_v1.store import (
    JevlikeHypothesisStore,
)
from tools.proof_carrying_nano_jevlike_independent_validation_v1.validator import (
    IndependentBundleValidationError,
    validate_bundle,
    validate_bundle_path,
)


UPSTREAM_REVISION = "94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452"


class _FakeRunner:
    def validate(self, _config: JevlikeAdapterConfig) -> None:
        return None

    def score(self, _context: str, _options: tuple[str, ...], *, config: JevlikeAdapterConfig):
        return (0.2, 0.7, 0.1)


def _bundle(tmp_path: Path) -> dict:
    identity = "jevlike-tiny-pinned-v1"
    context = "layer 3 residual activation: [3, 1]"
    options = HypothesisOptionSet.create(
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
            runner=_FakeRunner(),
        ),
    )
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    trace = host.capture(
        prompt="alpha",
        activation=(3, 1),
        seed=7,
        layer=3,
        site="residual",
    )
    action = nano.attach(host, layer=3, site="residual").run(
        trace,
        options,
        context=context,
        timestamp="2026-09-16T12:00:00Z",
    )
    proof = JevlikeLeanProofEngine().attempt(action)
    assert proof.status == "checked", proof.diagnostics
    with JevlikeHypothesisStore(tmp_path / "store.sqlite3") as store:
        store.commit_action(action)
        store.commit_proof(proof)
        return store.export_bundle(action_digest=action.action_digest)


def _rebind_bundle(bundle: dict) -> dict:
    action = bundle["action"]
    action["action_digest"] = canonical_digest(
        {key: value for key, value in action.items() if key != "action_digest"}
    )
    for proof in bundle["proofs"]:
        proof["action_digest"] = action["action_digest"]
        proof["proof_digest"] = canonical_digest(
            {key: value for key, value in proof.items() if key != "proof_digest"}
        )
    bundle["bundle_digest"] = canonical_digest(
        {key: value for key, value in bundle.items() if key != "bundle_digest"}
    )
    return bundle


def test_independent_validator_accepts_checked_hypothesis_bundle(tmp_path: Path) -> None:
    report = validate_bundle(_bundle(tmp_path))
    assert report.valid is True
    assert report.checked_proofs == 1
    assert report.status == "HypothesisOnly"
    assert report.claim_ceiling == "LocalExternalJevlikeQuantizedHypothesisRankingOnly"


def test_validator_is_independently_implemented() -> None:
    source = Path(__file__).parents[1] / "validator.py"
    text = source.read_text(encoding="utf-8")
    assert "JevlikeLeanProofEngine" not in text
    assert "JevlikeHypothesisStore" not in text
    assert "proof_carrying_nano_interp_jevlike_adapter_v1" not in text


def test_validator_rejects_status_tampering_even_with_rebound_digest(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    bundle["status"] = "Proven"
    _rebind_bundle(bundle)
    with pytest.raises(IndependentBundleValidationError, match="HypothesisOnly"):
        validate_bundle(bundle)


def test_validator_rejects_option_reordering_and_context_tampering(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    option_set = bundle["action"]["inputs"]["option_set"]
    option_set["options"].reverse()
    option_set["option_set_digest"] = canonical_digest(
        {key: value for key, value in option_set.items() if key != "option_set_digest"}
    )
    _rebind_bundle(bundle)
    with pytest.raises(IndependentBundleValidationError, match="option ordering|option binding"):
        validate_bundle(bundle)

    bundle = _bundle(tmp_path)
    bundle["action"]["inputs"]["context"] = "tampered context"
    _rebind_bundle(bundle)
    with pytest.raises(IndependentBundleValidationError, match="context"):
        validate_bundle(bundle)


def test_validator_rejects_proof_rebinding_and_forged_checked_source(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    _rebind_bundle(bundle)
    bundle["proofs"][0]["action_digest"] = "sha256:" + "f" * 64
    bundle["proofs"][0]["proof_digest"] = canonical_digest(
        {key: value for key, value in bundle["proofs"][0].items() if key != "proof_digest"}
    )
    bundle["bundle_digest"] = canonical_digest(
        {key: value for key, value in bundle.items() if key != "bundle_digest"}
    )
    with pytest.raises(IndependentBundleValidationError, match="action binding"):
        validate_bundle(bundle)

    bundle = _bundle(tmp_path)
    bundle["proofs"][0]["source"] = bundle["proofs"][0]["source"].replace(
        "by\n  decide", "by\n  trivial"
    )
    bundle["proofs"][0]["proof_digest"] = canonical_digest(
        {key: value for key, value in bundle["proofs"][0].items() if key != "proof_digest"}
    )
    _rebind_bundle(bundle)
    with pytest.raises(IndependentBundleValidationError, match="proof artifact"):
        validate_bundle(bundle)


def test_validator_rejects_probability_and_digest_tampering(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    bundle["action"]["outputs"]["probabilities"][1]["numerator"] = -1
    _rebind_bundle(bundle)
    with pytest.raises(IndependentBundleValidationError, match="probabilit|normalization"):
        validate_bundle(bundle)

    bundle = _bundle(tmp_path)
    bundle["bundle_digest"] = "sha256:" + "0" * 64
    with pytest.raises(IndependentBundleValidationError, match="bundle digest"):
        validate_bundle(bundle)


def test_validator_path_requires_canonical_bundle_bytes(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    path = tmp_path / "bundle.json"
    path.write_bytes(
        json.dumps(
            bundle,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    assert validate_bundle_path(path, check_lean=False).valid is True
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(IndependentBundleValidationError, match="canonical"):
        validate_bundle_path(path, check_lean=False)
