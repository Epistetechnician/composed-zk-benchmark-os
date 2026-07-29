from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v28r3", ROOT / "v28r3.py")
assert SPEC and SPEC.loader
v28r3 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = v28r3
SPEC.loader.exec_module(v28r3)


def fingerprint() -> dict:
    body = {
        "version": "mesh.astral_v28r3_predecessor_fingerprint.v1",
        "source_manifest_sha256s": [],
        "exact_string_sha256s": [],
        "normalized_surface_skeleton_sha256s": [],
        "structural_seven_gram_sha256s": [],
        "semantic_ast_sha256s": [],
        "template_ids": [],
    }
    return {**body, "fingerprint_sha256": v28r3.stable_hash(body)}


def corpus(seed: bytes) -> dict:
    value = {
        "version": v28r3.PROTOCOL["corpus_version"],
        "families": [
            v28r3.expected_family(seed, kind, ordinal)
            for kind in v28r3.FACT_KINDS
            for ordinal in range(24)
        ],
    }
    return {**value, "manifest_sha256": v28r3.stable_hash(value)}


def run(arm: str, value: dict, *, always_correct: bool) -> dict:
    observations = []
    for family in value["families"]:
        for query in family["queries"]:
            choice = query["expected_choice"] if always_correct else 0
            scores = [0.0, 0.0, 0.0, 0.0]
            scores[choice] = 1.0
            tokens = [17, 19, len(observations)]
            observations.append(
                {
                    "query_id": query["query_id"],
                    "prompt_sha256": query["prompt_sha256"],
                    "token_ids": tokens,
                    "tokenized_input_sha256": v28r3.stable_hash(tokens),
                    "label_scores": scores,
                    "predicted_label": v28r3.LABELS[choice],
                }
            )
    return {
        "arm_id": arm,
        "preparation_process_id": f"prep-{arm}",
        "evaluation_process_id": f"eval-{arm}",
        "fresh_checkpoint_reload": True,
        "checkpoint_sha256": "checkpoint",
        "tokenizer_sha256": "tokenizer",
        "implementation_sha256": "implementation",
        "shared_scorer_sha256": "scorer",
        "observations": observations,
        "observations_sha256": v28r3.stable_hash(observations),
    }


def campaign(*, always_correct: bool) -> dict:
    seed = bytes(range(32))
    value = corpus(seed)
    core = {
        "version": "mesh.astral_v28r3_integrated_campaign.v1",
        "state_slice": v28r3.PROTOCOL["execution_state_slice"],
        "status": "CorpusNotNovel",
        "seed_hex": seed.hex(),
        "seed_commitment": v28r3.sha256_text(seed.hex()),
        "corpus": value,
        "novelty_runs": [
            run("pre_update", value, always_correct=always_correct),
            run("no_update", value, always_correct=always_correct),
        ],
        "acquisition_packet": None,
    }
    return {**core, "campaign_sha256": v28r3.stable_hash(core)}


def test_independent_rederivation_accepts_exact_small_corpus() -> None:
    errors: list[str] = []
    families, queries = v28r3.validate_corpus(
        corpus(bytes(range(32))),
        seed=bytes(range(32)),
        fingerprint=fingerprint(),
        errors=errors,
        families_per_kind=24,
    )
    assert errors == []
    assert len(families) == 96
    assert len(queries) == 1152


def test_non_novel_campaign_is_a_valid_retained_negative() -> None:
    result = v28r3.validate_campaign(
        campaign(always_correct=True),
        fingerprint=fingerprint(),
        families_per_kind=24,
    )
    assert result["valid"] is True
    assert result["status"] == "CorpusNotNovel"
    assert result["claim_ceiling"] == "LocalModelBackedAcquisitionNoveltyPreflightV28R3"


def test_malformed_campaign_returns_invalid_report() -> None:
    result = v28r3.validate_campaign(
        {"version": "mesh.astral_v28r3_integrated_campaign.v1", "novelty_runs": [None]},
        fingerprint=fingerprint(),
        families_per_kind=24,
    )
    assert result["valid"] is False
    assert result["status"] == "Invalid"


def test_seed_and_corpus_tampering_fail_closed() -> None:
    value = campaign(always_correct=True)
    value["seed_hex"] = bytes(reversed(range(32))).hex()
    value["campaign_sha256"] = v28r3.stable_hash(
        v28r3.without_hash(value, "campaign_sha256")
    )
    result = v28r3.validate_campaign(
        value, fingerprint=fingerprint(), families_per_kind=24
    )
    assert result["valid"] is False
    assert any(error.startswith("campaign.seed") or error.startswith("corpus.rederivation") for error in result["errors"])


def test_chance_balanced_observations_pass_equivalence() -> None:
    value = corpus(bytes(range(32)))
    errors: list[str] = []
    families, query_map = v28r3.validate_corpus(
        value,
        seed=bytes(range(32)),
        fingerprint=fingerprint(),
        errors=errors,
        families_per_kind=24,
    )
    _, metrics = v28r3.validate_baseline_run(
        run("pre_update", value, always_correct=False),
        arm_id="pre_update",
        families=families,
        query_map=query_map,
        errors=errors,
    )
    assert errors == []
    assert metrics["equivalence_passed"] is True
