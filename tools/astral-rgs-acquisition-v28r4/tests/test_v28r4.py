from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v28r4", ROOT / "v28r4.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def test_fixed_fixture_rederives_to_frozen_census() -> None:
    errors: list[str] = []
    seed = bytes.fromhex(module.PROTOCOL["fixture_seed_hex"])
    fingerprint = module.empty_fingerprint()
    families = [
        module.V28R3.expected_family(seed, kind, ordinal)
        for kind in module.PROTOCOL["fact_kinds"]
        for ordinal in range(module.PROTOCOL["families_per_fact_kind"])
    ]
    corpus_body = {"version": "mesh.astral_v28r3_corpus.v1", "families": families}
    corpus = {**corpus_body, "manifest_sha256": module.stable_hash(corpus_body)}
    validated, _ = module.V28R3.validate_corpus(
        corpus,
        seed=seed,
        fingerprint=fingerprint,
        errors=errors,
        families_per_kind=module.PROTOCOL["families_per_fact_kind"],
    )
    assert errors == []
    assert len(validated) == module.PROTOCOL["family_count"]
    assert len(module.expected_order(validated)) == module.PROTOCOL["family_count"]


def test_comparison_rejects_semantic_or_score_drift() -> None:
    base = {
        "query_id": "q",
        "family_id": "f",
        "retrieved_family_id": "f",
        "fact_kind": "nonce_fact",
        "query_class": "paraphrase",
        "prompt_sha256": "p",
        "token_ids": [1],
        "tokenized_input_sha256": "t",
        "predicted_label": "A",
        "expected_label": "A",
        "correct": True,
        "external_source_sha256": "s",
        "external_support_sha256": "u",
        "label_scores": [1.0, 0.0, -1.0, -2.0],
    }
    close = {**base, "label_scores": [1.000001, 0.0, -1.0, -2.0]}
    far = {**base, "label_scores": [1.001, 0.0, -1.0, -2.0]}
    changed = {**base, "predicted_label": "B"}
    assert module.compare({"observations": [base]}, {"observations": [close]})["passes"]
    assert not module.compare({"observations": [base]}, {"observations": [far]})["passes"]
    assert not module.compare({"observations": [base]}, {"observations": [changed]})["passes"]


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    report = module.validate(tmp_path)
    assert not report["valid"]
    assert not report["qualified"]
