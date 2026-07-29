from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v28r2", HERE / "v28r2.py")
assert SPEC and SPEC.loader
V28R2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V28R2)


def fingerprint() -> dict:
    body = {
        "version": "astral.v28r2.retired_r1_fingerprint.v1",
        "state_slice": "astral-rgs-v28r2-powered-acquisition-novelty-implementation",
        "retired_campaign": "V28R1",
        "source_raw_corpus_sha256": "sha256:" + "1" * 64,
        "source_raw_corpus_receipt_sha256": "sha256:" + "2" * 64,
        "source_seed_commitment_sha256": "sha256:" + "3" * 64,
        "family_count": 96,
        "exact_string_sha256s": [],
        "normalized_surface_skeleton_sha256s": [],
        "structural_seven_gram_sha256s": [],
        "semantic_ast_sha256s": [],
        "normalized_semantic_ast_sha256s": [],
    }
    body["fingerprint_sha256"] = V28R2.content_hash(body)
    return body


def family(fact_kind: str, kind_ordinal: int) -> dict:
    family_id = f"r2family-{fact_kind}-{kind_ordinal:04d}"
    records = [
        {
            "subject": f"r2s-{fact_kind}-{kind_ordinal:04d}-{row}",
            "alias": f"r2a-{fact_kind}-{kind_ordinal:04d}-{row}",
            "bridge": f"r2b-{fact_kind}-{kind_ordinal:04d}-{row}",
            "value": f"r2v-{fact_kind}-{kind_ordinal:04d}-{row}",
        }
        for row in range(4)
    ]
    result = {
        "family_id": family_id,
        "namespace_id": f"r2ns-{fact_kind}-{kind_ordinal:04d}",
        "fact_kind": fact_kind,
        "block_index": kind_ordinal // 24,
        "family_in_block": kind_ordinal % 24,
        "records": records,
        "target_index": kind_ordinal % 4,
        "source_document": f"R2 source chamber {family_id}.",
        "support_document": f"R2 support chamber {family_id}.",
        "queries": [],
    }
    result["source_sha256"] = V28R2.sha256_text(result["source_document"])
    result["support_sha256"] = V28R2.sha256_text(result["support_document"])
    result["semantic_ast_sha256"] = V28R2.content_hash(V28R2.semantic_ast(result))
    for evaluation_index, evaluation_kind in enumerate(V28R2.EVALUATION_KINDS):
        for variant in range(4):
            question = V28R2.question_for(
                fact_kind,
                evaluation_kind,
                variant,
                records[result["target_index"]],
            )
            options = V28R2.expected_options(result, evaluation_index, variant)
            expected_choice = V28R2.PERMUTATIONS[
                (result["family_in_block"] + 7 * evaluation_index) % 24
            ][variant]
            prompt = V28R2.render_prompt(question, options)
            result["queries"].append(
                {
                    "query_id": V28R2.tag_id("r2query", family_id, evaluation_kind, variant),
                    "evaluation_kind": evaluation_kind,
                    "variant": variant,
                    "template_id": f"r2-{fact_kind}-{evaluation_kind}-surface-{variant}",
                    "question": question,
                    "options": options,
                    "expected_choice": expected_choice,
                    "expected_label": V28R2.LABELS[expected_choice],
                    "prompt": prompt,
                    "prompt_sha256": V28R2.sha256_text(prompt),
                }
            )
    return result


def corpus() -> dict:
    value = {
        "version": "mesh.astral_v28r2_corpus.v1",
        "families": [
            family(fact_kind, ordinal)
            for fact_kind in V28R2.FACT_KINDS
            for ordinal in range(24)
        ],
    }
    value["manifest_sha256"] = V28R2.content_hash(value)
    return value


def test_not_run_and_non_object_fail_closed() -> None:
    assert V28R2.validate_packet(None, None)["status"] == "NotRun"
    assert V28R2.validate_packet([], fingerprint())["errors"] == ["packet.object"]


def test_small_exact_permutation_census_passes_internal_validator() -> None:
    errors: list[str] = []
    families, query_order = V28R2.validate_corpus(
        corpus(), fingerprint(), errors, families_per_kind=24
    )

    assert errors == []
    assert len(families) == 96
    assert len(query_order) == 1152


def test_swapped_answer_position_fails_permutation_and_row_binding() -> None:
    value = corpus()
    value["families"][0]["queries"][0]["expected_choice"] = 3
    value["manifest_sha256"] = V28R2.content_hash(
        V28R2.without_hash(value, "manifest_sha256")
    )
    errors: list[str] = []
    V28R2.validate_corpus(value, fingerprint(), errors, families_per_kind=24)

    assert any(code.endswith("expected_choice") for code in errors)
    assert any("permutation_block" in code for code in errors)


def test_retired_skeleton_and_ngram_overlap_fail() -> None:
    value = corpus()
    retired = fingerprint()
    text = value["families"][0]["queries"][0]["prompt"]
    retired["normalized_surface_skeleton_sha256s"] = [
        V28R2.sha256_text(V28R2.normalize_skeleton(text))
    ]
    retired["structural_seven_gram_sha256s"] = sorted(V28R2.structural_ngrams(text))
    retired["fingerprint_sha256"] = V28R2.content_hash(
        V28R2.without_hash(retired, "fingerprint_sha256")
    )
    errors: list[str] = []
    V28R2.validate_corpus(value, retired, errors, families_per_kind=24)

    assert "corpus.r1_normalized_skeleton_overlap" in errors
    assert "corpus.r1_structural_ngram_overlap" in errors


def test_argmax_tie_uses_first_label_and_token_hash_is_recomputed() -> None:
    value = corpus()
    query = value["families"][0]["queries"][0]
    observation = {
        "query_id": query["query_id"],
        "prompt_sha256": query["prompt_sha256"],
        "token_ids": [7, 11],
        "tokenized_input_sha256": V28R2.content_hash([7, 11]),
        "label_scores": [1.0, 1.0, 0.0, -1.0],
        "predicted_label": "A",
        "correct": query["expected_choice"] == 0,
    }
    errors: list[str] = []
    result = V28R2.validate_run(
        {
            "arm_id": "pre_update",
            "seed_id": 280201,
            "task_order_id": "full-corpus",
            "persistence_class": "unchanged_checkpoint",
            "observations": [observation],
            "observations_sha256": V28R2.content_hash([observation]),
        },
        "pre_update",
        {query["query_id"]: query},
        [query["query_id"]],
        errors,
    )

    assert errors == []
    assert result[query["query_id"]]["predicted_label"] == "A"


def test_cli_rejects_null_packet_and_writes_report(tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.json"
    fingerprint_path = tmp_path / "fingerprint.json"
    output_path = tmp_path / "report.json"
    packet_path.write_text("null\n", encoding="utf-8")
    fingerprint_path.write_text(json.dumps(fingerprint()) + "\n", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(HERE / "validate_packet.py"),
            "--packet",
            str(packet_path),
            "--retired-r1-fingerprint",
            str(fingerprint_path),
            "--output",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert json.loads(output_path.read_text())["status"] == "NotRun"


def test_interval_near_chance_can_fail_precision_gate() -> None:
    result = V28R2.interval([1.0, -1.0] * 12)

    assert result["mean_chance_normalized_lift"] == 0.0
    assert result["equivalence_passed"] is False
