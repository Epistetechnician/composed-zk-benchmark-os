from __future__ import annotations

import copy
import ast
import importlib.util
import itertools
import json
import subprocess
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parents[1]


def _module(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


V28 = _module("astral_v28r2_test_core", HERE / "v28r2.py")
BUILDER = _module(
    "astral_v28r2_test_fingerprint_builder",
    HERE / "build_retired_v28r1_fingerprint.py",
)
PROTOCOL = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
SEED_HEX = "42" * 32
SCORER_CONFIGURATION = {
    "choice_labels": ["A", "B", "C", "D"],
    "choice_token_ids": [32, 33, 34, 35],
    "tie_break": "lowest_option_index",
}


def _sha(label: str) -> str:
    return V28.sha256_bytes(label.encode("utf-8"))


def _self_hashed(value: dict, key: str) -> dict:
    result = dict(value)
    result[key] = V28.canonical_sha256(result)
    return result


def _write_canonical(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(V28.canonical_json_bytes(value) + b"\n")


def _refresh_bundle_manifest(root: Path, packet: dict) -> None:
    entries = [
        {
            "path": path_text,
            "bytes": (root / path_text).stat().st_size,
            "sha256": V28.sha256_file(root / path_text),
        }
        for path_text in sorted(V28.BUNDLE_DATA_PATHS)
    ]
    manifest = _self_hashed(
        {
            "version": "synthetic.artifact-manifest.v1",
            "state_slice": V28.PACKET_STATE_SLICE,
            "entries": entries,
        },
        "manifest_sha256",
    )
    packet["artifact_manifest_sha256"] = manifest["manifest_sha256"]
    _write_canonical(root / "artifact-manifest.json", manifest)
    _write_canonical(root / "acquisition-packet.json", packet)


def _empty_fingerprint() -> dict:
    manifest = {
        "version": "astral.rgs_v28r1_retired_fingerprint.v1",
        "state_slice": "astral-rgs-v28r2-retired-r1-fingerprint",
        "source_bundle": {
            "packet_sha256": V28.R1_PACKET_SHA256,
            "validation_report_sha256": V28.R1_REPORT_SHA256,
            "artifact_manifest_sha256": V28.R1_MANIFEST_SHA256,
            "packet_file_sha256": V28.R1_PACKET_FILE_SHA256,
            "validation_report_file_sha256": V28.R1_REPORT_FILE_SHA256,
            "artifact_manifest_file_sha256": V28.R1_MANIFEST_FILE_SHA256,
            "generator_sha256": _sha("r1-generator"),
            "seed_commitment_sha256": _sha("r1-seed"),
            "corpus_manifest_sha256": _sha("r1-corpus"),
            "future_assessment_commitment_sha256": _sha("r1-future"),
            "disposition": "CorpusNotNovel",
        },
        "normalization_profile": {
            "unicode": "NFC",
            "case": "lowercase",
            "generated_values": "typed_placeholders_from_semantic_ast",
            "whitespace": "collapse_ascii_whitespace",
            "structural_ngram_size": 8,
        },
        "fingerprint_sets": {
            name: {
                "count": 0,
                "items": [],
                "set_sha256": V28.canonical_sha256([]),
            }
            for name in V28.FINGERPRINT_SET_NAMES
        },
        "model_outcomes_included": False,
        "paths_sorted": True,
    }
    manifest["manifest_sha256"] = V28.canonical_sha256(manifest)
    return manifest


def _synthetic_r1_builder_inputs() -> tuple[dict, ...]:
    receipt = _self_hashed(
        {
            "version": "synthetic.r1.receipt.v1",
            "state_slice": "synthetic-r1",
        },
        "receipt_sha256",
    )
    seed_hex = "24" * 32
    seed_material = {
        "version": "synthetic.r1.seed.v1",
        "state_slice": "synthetic-r1",
        "receipt_sha256": receipt["receipt_sha256"],
        "seed_hex": seed_hex,
    }
    seed_commitment = _self_hashed(
        {
            "version": "synthetic.r1.seed-commitment.v1",
            "state_slice": "synthetic-r1",
            "receipt_sha256": receipt["receipt_sha256"],
            "seed_sha256": BUILDER.sha256_bytes(bytes.fromhex(seed_hex)),
        },
        "seed_commitment_sha256",
    )
    raw_families = []
    protocol_items = []
    fact_kinds = (
        "nonce_fact",
        "entity_relation",
        "changed_rule",
        "opaque_mapping",
    )
    for family_ordinal in range(96):
        fact_kind = fact_kinds[family_ordinal // 24]
        family_id = f"family-secret-{family_ordinal:03d}"
        item_id = f"item-secret-{family_ordinal:03d}"
        namespace = f"ns-secret-{family_ordinal:03d}"
        rows = []
        semantic_records = []
        answer_options = []
        for row_index in range(4):
            anchor = f"ent-secret-{family_ordinal:03d}-{row_index}"
            value = f"val-secret-{family_ordinal:03d}-{row_index}"
            aliases = [
                f"als-secret-{family_ordinal:03d}-{row_index}-{index}"
                for index in range(4)
            ]
            wrappers = [
                f"hdl-secret-{family_ordinal:03d}-{row_index}-{index}"
                for index in range(4)
            ]
            rows.append(
                {
                    "aliases": aliases,
                    "anchor": anchor,
                    "row_index": row_index,
                    "value": value,
                    "wrappers": wrappers,
                }
            )
            semantic_records.append(
                {
                    "aliases": aliases,
                    "anchor": anchor,
                    "current_value": value,
                    "row_index": row_index,
                    "wrappers": wrappers,
                }
            )
            answer_options.append(
                {
                    "license_id": "CC0-1.0",
                    "sha256": BUILDER.sha256_bytes(value.encode("utf-8")),
                    "text": value,
                }
            )
        source_text = (
            f"Registry {namespace} binds {rows[0]['anchor']} to "
            f"{rows[0]['value']} and retains three distractor rows."
        )
        support_text = (
            f"Alias {rows[0]['aliases'][0]} resolves to "
            f"{rows[0]['anchor']}; handle {rows[0]['wrappers'][0]} "
            f"unwraps to {rows[0]['aliases'][0]}."
        )
        source_hash = BUILDER.sha256_bytes(source_text.encode("utf-8"))
        support_hash = BUILDER.sha256_bytes(support_text.encode("utf-8"))
        raw_queries = []
        protocol_queries = []
        for query_ordinal in range(12):
            evaluation_kind = V28.REQUIRED_EVALUATION_KINDS[
                query_ordinal // 4
            ]
            variant = query_ordinal % 4
            query_id = (
                f"query-secret-{family_ordinal:03d}-{query_ordinal:02d}"
            )
            question = (
                f"Resolve {rows[0]['aliases'][0]} for sealed query "
                f"{query_ordinal}; which terminal is current?"
            )
            prompt = (
                "Choose A, B, C, or D.\n"
                + question
                + "\n"
                + "\n".join(
                    f"{label}. {option['text']}"
                    for label, option in zip("ABCD", answer_options)
                )
                + "\nAnswer:\n"
            )
            prompt_hash = BUILDER.sha256_bytes(prompt.encode("utf-8"))
            template_id = f"eval-{evaluation_kind}-v{variant}"
            dependency_hashes = (
                [source_hash]
                if evaluation_kind == "paraphrase"
                else [source_hash, support_hash]
            )
            raw_query = {
                "answer_options": answer_options,
                "dependency_source_sha256s": dependency_hashes,
                "evaluation_kind": evaluation_kind,
                "expected_answer_sha256": answer_options[0]["sha256"],
                "expected_choice": 0,
                "expected_label": "A",
                "prompt": prompt,
                "prompt_sha256": prompt_hash,
                "query_id": query_id,
                "question": question,
                "template_family_id": template_id,
                "variant": variant,
                "withheld_from_training": True,
            }
            protocol_query = {
                "answer_mapping_sha256": _sha(
                    f"r1-answer-{family_ordinal}-{query_ordinal}"
                ),
                "answer_option_sha256s": [
                    option["sha256"] for option in answer_options
                ],
                "dependency_source_sha256s": dependency_hashes,
                "derivation_manifest_sha256": _sha(
                    f"r1-derivation-{family_ordinal}-{query_ordinal}"
                ),
                "prompt_sha256": prompt_hash,
                "query_id": query_id,
                "template_family_id": template_id,
            }
            raw_queries.append(raw_query)
            protocol_queries.append(protocol_query)
        semantic_ast = {
            "version": "synthetic.r1.semantic-ast.v1",
            "fact_kind": fact_kind,
            "namespace": namespace,
            "records": semantic_records,
            "resolution_chain": [
                "wrapper",
                "alias",
                "anchor",
                "current_value",
            ],
            "target_row": 0,
        }
        training_template_id = f"train-{fact_kind}-declarative-v1"
        raw_families.append(
            {
                "answer_options": answer_options,
                "expected_answer_sha256": answer_options[0]["sha256"],
                "fact_kind": fact_kind,
                "family_id": family_id,
                "item_id": item_id,
                "namespace": namespace,
                "queries": raw_queries,
                "row_order": [0, 1, 2, 3],
                "rows": rows,
                "semantic_ast": semantic_ast,
                "source_form": {
                    "license_id": "CC0-1.0",
                    "sha256": source_hash,
                    "text": source_text,
                },
                "support_source": {
                    "license_id": "CC0-1.0",
                    "sha256": support_hash,
                    "text": support_text,
                },
                "target_row": 0,
                "training_template_family_id": training_template_id,
            }
        )
        protocol_items.append(
            {
                "answer_option_sha256s": [
                    option["sha256"] for option in answer_options
                ],
                "fact_kind": fact_kind,
                "family_id": family_id,
                "item_id": item_id,
                "queries": protocol_queries,
                "source_form_sha256": source_hash,
                "support_source_sha256s": [support_hash],
                "training_template_family_id": training_template_id,
            }
        )
    raw_corpus = _self_hashed(
        {
            "version": "synthetic.r1.raw-corpus.v1",
            "state_slice": "synthetic-r1",
            "receipt_sha256": receipt["receipt_sha256"],
            "seed_commitment_sha256": seed_commitment[
                "seed_commitment_sha256"
            ],
            "families": raw_families,
        },
        "raw_corpus_sha256",
    )
    protocol_corpus = {
        "version": "synthetic.r1.protocol-corpus.v1",
        "items": protocol_items,
    }
    protocol_corpus["manifest_sha256"] = BUILDER.canonical_sha256(
        protocol_items
    )
    future = _self_hashed(
        {
            "version": "synthetic.r1.future.v1",
            "state_slice": "synthetic-r1",
            "receipt_sha256": receipt["receipt_sha256"],
            "family_ids": [
                f"future-secret-{index:03d}" for index in range(96)
            ],
        },
        "future_assessment_family_commitment_sha256",
    )
    configuration = _self_hashed(
        {
            "version": "synthetic.r1.configuration.v1",
            "state_slice": "synthetic-r1",
            "receipt_sha256": receipt["receipt_sha256"],
        },
        "configuration_lock_sha256",
    )
    one_shot = {
        "version": "synthetic.r1.one-shot.v1",
        "state_slice": "synthetic-r1",
        "receipt_sha256": receipt["receipt_sha256"],
        "output_directory": "/repository-external/synthetic-r1",
        "source_commit": "c" * 40,
    }
    packet = {
        "version": "synthetic.r1.packet.v1",
        "state_slice": "synthetic-r1",
        "corpus": {"items": protocol_items},
        "provenance": {
            "generator_sha256": _sha("synthetic-r1-generator"),
            "seed_commitment_sha256": seed_commitment[
                "seed_commitment_sha256"
            ],
            "corpus_manifest_sha256": protocol_corpus[
                "manifest_sha256"
            ],
            "future_assessment_family_commitment_sha256": future[
                "future_assessment_family_commitment_sha256"
            ],
            "configuration_lock_sha256": configuration[
                "configuration_lock_sha256"
            ],
        },
    }
    packet["packet_sha256"] = BUILDER.canonical_sha256(packet)
    report = {
        "version": "synthetic.r1.report.v1",
        "status": "CorpusNotNovel",
        "errors": [],
        "open_gates": ["acquisition.new_corpus_required"],
    }
    report["report_sha256"] = BUILDER.canonical_sha256(report)
    return (
        packet,
        report,
        receipt,
        seed_material,
        seed_commitment,
        raw_corpus,
        protocol_corpus,
        future,
        configuration,
        one_shot,
    )


def _score_row(query: dict, observed_choice: int) -> dict:
    scores = [-4.0, -4.0, -4.0, -4.0]
    scores[observed_choice] = -1.0
    token_ids = [101, 202, 303]
    return {
        "query_id": query["query_id"],
        "prompt_sha256": query["prompt_sha256"],
        "input_token_ids": token_ids,
        "tokenized_input_sha256": V28.canonical_sha256(token_ids),
        "input_token_count": len(token_ids),
        "choice_labels": ["A", "B", "C", "D"],
        "choice_token_ids": [32, 33, 34, 35],
        "label_log_probability_scores": scores,
        "observed_choice": observed_choice,
        "tie_break": "lowest_option_index",
    }


def _run(
    arm_id: str,
    rows: list[dict],
    queries: list[dict],
    process_offset: int,
) -> dict:
    observations = [
        {
            "query_id": query["query_id"],
            "expected_choice": query["expected_choice"],
            "observed_choice": row["observed_choice"],
        }
        for row, query in zip(rows, queries)
    ]
    return {
        "arm_id": arm_id,
        "run_id": f"test-{arm_id}",
        "persistence_class": "unchanged_checkpoint",
        "preparation_implementation_sha256": _sha(
            f"preparation-implementation-{arm_id}"
        ),
        "preparation_configuration_sha256": _sha(
            f"preparation-configuration-{arm_id}"
        ),
        "evaluator_implementation_sha256": _sha("evaluator-implementation"),
        "evaluator_configuration_sha256": _sha("evaluator-configuration"),
        "prep_process_id": _sha(f"process-{process_offset}"),
        "evaluation_process_id": _sha(f"process-{process_offset + 1}"),
        "starting_state_sha256": _sha("checkpoint"),
        "post_preparation_state_sha256": _sha("checkpoint"),
        "restart_loaded_state_sha256": _sha("checkpoint"),
        "runtime_inventory_sha256": _sha("runtime"),
        "tokenizer_inventory_sha256": _sha("tokenizer-inventory"),
        "scorer_configuration_sha256": _sha("scorer-configuration"),
        "source_removal_manifest_sha256": _sha(f"source-removal-{arm_id}"),
        "prep_receipt_sha256": _sha(f"prep-receipt-{arm_id}"),
        "process_receipt_sha256": _sha(f"process-receipt-{arm_id}"),
        "source_context_present": False,
        "retrieval_enabled": False,
        "source_removal_verified": True,
        "fresh_checkpoint_load": True,
        "stage_order": (
            ["checkpoint_load", "evaluation"]
            if arm_id == "pre_update"
            else [
                "no_op_preparation",
                "source_removal",
                "checkpoint_load",
                "evaluation",
            ]
        ),
        "update_budget": {
            "update_tokens": 0,
            "gradient_steps": 0,
            "adapter_rank": 0,
        },
        "query_count": 73728,
        "raw_scores_sha256": V28.canonical_sha256(rows),
        "observations_sha256": V28.canonical_sha256(observations),
        "run_manifest_sha256": _sha(f"run-{arm_id}"),
        "score_rows": rows,
    }


@pytest.fixture(scope="session")
def full_packet():
    protocol = copy.deepcopy(PROTOCOL)
    fingerprint = _empty_fingerprint()
    protocol["nonreuse_contract"][
        "retired_r1_fingerprint_manifest_sha256"
    ] = fingerprint["manifest_sha256"]
    families: list[dict] = []
    queries: list[dict] = []
    for fact_kind in V28.REQUIRED_FACT_KINDS:
        for ordinal in range(1536):
            family = V28.reconstruct_family(SEED_HEX, fact_kind, ordinal, protocol)
            families.append(family)
            queries.extend(family["queries"])
    rows: list[dict] = []
    for family_index, family in enumerate(families):
        count = 0 if family_index % 24 < 4 else 2 if family_index % 24 < 8 else 1
        by_kind = {kind: 0 for kind in V28.REQUIRED_EVALUATION_KINDS}
        for query in family["queries"]:
            kind = query["evaluation_kind"]
            correct = by_kind[kind] < count
            by_kind[kind] += 1
            observed = (
                query["expected_choice"]
                if correct
                else (query["expected_choice"] + 1) % 4
            )
            rows.append(_score_row(query, observed))
    packet = {
        "version": V28.PACKET_VERSION,
        "state_slice": V28.PACKET_STATE_SLICE,
        "protocol_sha256": V28.canonical_sha256(protocol),
        "campaign": {
            "campaign_id": "test-v28r2-full-census",
            "ledger_id": "test-v28r2-full-census-ledger",
            "seed_hex": SEED_HEX,
            "seed_draw_count": 1,
            "candidate_corpus_count": 1,
            "discarded_candidate_count": 0,
            "adaptive_expansion": False,
            "post_seed_power_change": False,
            "replacement_seed_allowed": False,
            "ledger_exclusive_create": True,
            "ledger_file_synced": True,
            "ledger_parent_synced": True,
            "post_claim_failure_recovery_allowed": False,
            "generator_input_allowlist_sha256": V28.canonical_sha256(
                protocol["generator_input_allowlist"]
            ),
            "generator_input_keys": protocol["generator_input_allowlist"],
        },
        "provenance": {
            "source_commit": "a" * 40,
            "source_tree": "b" * 40,
            "source_clean": True,
            "checkpoint_inventory_sha256": _sha("checkpoint-inventory"),
            "tokenizer_inventory_sha256": _sha("tokenizer-inventory"),
            "runtime_sha256": _sha("runtime"),
            "generator_inventory_sha256": _sha("generator-inventory"),
            "validator_inventory_sha256": _sha("validator-inventory"),
            "pre_generation_receipt_sha256": _sha("pre-generation-receipt"),
            "output_root": "/repository-external/test-v28r2-full-census",
        },
        "ordering": protocol["ordering_contract"],
        "locks": {
            "power_profile_sha256": _sha("power-profile"),
            "concept_catalog_sha256": _sha("concept-catalog"),
            "template_ast_catalog_sha256": _sha("template-ast-catalog"),
            "derivation_grammar_sha256": _sha("derivation-grammar"),
            "domain_tags_sha256": _sha("domain-tags"),
            "scorer_contract_sha256": _sha("scorer-contract"),
            "scorer_configuration_sha256": _sha("scorer-configuration"),
            "prompt_shell_sha256": _sha("prompt-shell"),
            "future_assessment_identity_commitment_sha256": _sha(
                "future-assessment"
            ),
            "configuration_lock_sha256": _sha("configuration-lock"),
            "one_shot_execution_claim_sha256": _sha("one-shot-claim"),
            "seed_commitment_sha256": _sha("seed-commitment"),
        },
        "corpus": {
            "family_count": 6144,
            "queries_per_family": 12,
            "query_count": 73728,
            "families": families,
            "corpus_sha256": V28.canonical_sha256(families),
        },
        "baseline_runs": [
            _run("pre_update", rows, queries, 1),
            _run("no_update", list(rows), queries, 3),
        ],
        "later_gates": {
            "update_arms": None,
            "retention_recovery": None,
            "selection": None,
            "assessment": None,
        },
        "claim_boundary": {
            claim: False for claim in protocol["required_false_claims"]
        },
        "artifact_manifest_sha256": _sha("artifact-manifest"),
    }
    packet["packet_sha256"] = V28.canonical_sha256(packet)
    return packet, protocol, fingerprint


def _canonical_bundle(tmp_path: Path) -> tuple[dict, Path]:
    root = tmp_path / "bundle"
    root.mkdir()
    seed_hex = SEED_HEX
    campaign = {
        "campaign_id": "synthetic-campaign",
        "ledger_id": "synthetic-ledger",
        "seed_hex": seed_hex,
        "generator_input_allowlist_sha256": V28.canonical_sha256(
            PROTOCOL["generator_input_allowlist"]
        ),
    }
    inventories = {
        "checkpoint-inventory.json": {
            "version": V28.ARTIFACT_VERSIONS["checkpoint-inventory.json"],
            "state_slice": V28.PACKET_STATE_SLICE,
            "checkpoint_state_sha256": _sha("bundle-starting-state"),
        },
        "tokenizer-inventory.json": {
            "version": V28.ARTIFACT_VERSIONS["tokenizer-inventory.json"],
            "state_slice": V28.PACKET_STATE_SLICE,
            "tokenizer_content_sha256": _sha("tokenizer-content"),
        },
        "runtime-inventory.json": {
            "version": V28.ARTIFACT_VERSIONS["runtime-inventory.json"],
            "state_slice": V28.PACKET_STATE_SLICE,
            "runtime_content_sha256": _sha("runtime-content"),
        },
        "generator-inventory.json": {
            "version": V28.ARTIFACT_VERSIONS["generator-inventory.json"],
            "state_slice": V28.PACKET_STATE_SLICE,
            "implementation_sha256": _sha("generator-implementation"),
        },
        "validator-inventory.json": {
            "version": V28.ARTIFACT_VERSIONS["validator-inventory.json"],
            "state_slice": V28.PACKET_STATE_SLICE,
            "implementation_sha256": _sha("validator-implementation"),
        },
    }
    provenance = {
        "source_commit": "a" * 40,
        "source_tree": "b" * 40,
        "output_root": "/repository-external/synthetic-campaign",
        "checkpoint_inventory_sha256": V28.canonical_sha256(
            inventories["checkpoint-inventory.json"]
        ),
        "tokenizer_inventory_sha256": V28.canonical_sha256(
            inventories["tokenizer-inventory.json"]
        ),
        "runtime_sha256": V28.canonical_sha256(
            inventories["runtime-inventory.json"]
        ),
        "generator_inventory_sha256": V28.canonical_sha256(
            inventories["generator-inventory.json"]
        ),
        "validator_inventory_sha256": V28.canonical_sha256(
            inventories["validator-inventory.json"]
        ),
    }
    scorer = _self_hashed(
        {
            "version": "synthetic.scorer.v1",
            "scorer_contract_sha256": V28.canonical_sha256(
                PROTOCOL["scorer_contract"]
            ),
            "tokenizer_inventory_sha256": provenance[
                "tokenizer_inventory_sha256"
            ],
            "choice_labels": ["A", "B", "C", "D"],
            "choice_token_ids": [32, 33, 34, 35],
            "contextual_tokenization_verified": True,
            "tie_break": "lowest_option_index",
        },
        "scorer_configuration_sha256",
    )
    seed_commitment = _self_hashed(
        {
            "version": V28.ARTIFACT_VERSIONS["seed-commitment.json"],
            "state_slice": V28.PACKET_STATE_SLICE,
            "campaign_id": campaign["campaign_id"],
            "ledger_id": campaign["ledger_id"],
            "checkpoint_inventory_sha256": provenance[
                "checkpoint_inventory_sha256"
            ],
            "pre_generation_receipt_sha256": None,
            "one_shot_execution_claim_sha256": None,
            "seed_sha256": V28.sha256_bytes(bytes.fromhex(seed_hex)),
        },
        "seed_commitment_sha256",
    )
    future = _self_hashed(
        {
            "version": V28.ARTIFACT_VERSIONS[
                "future-assessment-identity-commitment.json"
            ],
            "state_slice": V28.PACKET_STATE_SLICE,
            "campaign_id": campaign["campaign_id"],
            "ledger_id": campaign["ledger_id"],
            "family_ids": ["future-synthetic-family"],
            "assessment_content_generated": False,
            "assessment_opened": False,
        },
        "future_assessment_identity_commitment_sha256",
    )
    one_shot = _self_hashed(
        {
            "version": V28.ARTIFACT_VERSIONS[
                "one-shot-execution-claim.json"
            ],
            "state_slice": V28.PACKET_STATE_SLICE,
            "campaign_id": campaign["campaign_id"],
            "ledger_id": campaign["ledger_id"],
            "output_root": provenance["output_root"],
            "source_commit": provenance["source_commit"],
            "source_tree": provenance["source_tree"],
            "ledger_exclusive_create": True,
            "ledger_file_synced": True,
            "ledger_parent_synced": True,
            "seed_draw_count": 1,
            "candidate_corpus_count": 1,
            "permanently_retired_after_failure": True,
            "ledger_claim_order": PROTOCOL["ordering_contract"][
                "ledger_claim_order"
            ],
            "seed_draw_order": PROTOCOL["ordering_contract"][
                "seed_draw_order"
            ],
        },
        "one_shot_execution_claim_sha256",
    )
    locks = {
        "power_profile_sha256": V28.canonical_sha256(
            PROTOCOL["power_profile"]
        ),
        "concept_catalog_sha256": V28.canonical_sha256(
            {
                "version": PROTOCOL["derivation_grammar"]["version"],
                "fact_kinds": PROTOCOL["derivation_grammar"]["fact_kinds"],
            }
        ),
        "template_ast_catalog_sha256": V28.canonical_sha256(
            PROTOCOL["template_ast_catalog"]
        ),
        "derivation_grammar_sha256": V28.canonical_sha256(
            PROTOCOL["derivation_grammar"]
        ),
        "domain_tags_sha256": V28.canonical_sha256(PROTOCOL["domain_tags"]),
        "scorer_contract_sha256": V28.canonical_sha256(
            PROTOCOL["scorer_contract"]
        ),
        "scorer_configuration_sha256": scorer[
            "scorer_configuration_sha256"
        ],
        "prompt_shell_sha256": V28.canonical_sha256(PROTOCOL["prompt_shell"]),
        "future_assessment_identity_commitment_sha256": future[
            "future_assessment_identity_commitment_sha256"
        ],
        "one_shot_execution_claim_sha256": one_shot[
            "one_shot_execution_claim_sha256"
        ],
        "seed_commitment_sha256": seed_commitment[
            "seed_commitment_sha256"
        ],
    }
    one_shot = V28._without(
        one_shot, "one_shot_execution_claim_sha256"
    )
    one_shot["locked_input_sha256s"] = {
        key: value
        for key, value in locks.items()
        if key
        not in {
            "configuration_lock_sha256",
            "one_shot_execution_claim_sha256",
            "seed_commitment_sha256",
        }
    }
    one_shot["one_shot_execution_claim_sha256"] = V28.canonical_sha256(
        one_shot
    )
    locks["one_shot_execution_claim_sha256"] = one_shot[
        "one_shot_execution_claim_sha256"
    ]
    configuration = _self_hashed(
        {
            "version": V28.ARTIFACT_VERSIONS["configuration-lock.json"],
            "state_slice": V28.PACKET_STATE_SLICE,
            "protocol_sha256": V28.EXPECTED_PROTOCOL_SHA256,
            "campaign_id": campaign["campaign_id"],
            "output_root": provenance["output_root"],
            "checkpoint_inventory_sha256": provenance[
                "checkpoint_inventory_sha256"
            ],
            "tokenizer_inventory_sha256": provenance[
                "tokenizer_inventory_sha256"
            ],
            "runtime_sha256": provenance["runtime_sha256"],
            "generator_inventory_sha256": provenance[
                "generator_inventory_sha256"
            ],
            "validator_inventory_sha256": provenance[
                "validator_inventory_sha256"
            ],
            "seed_commitment_sha256": locks["seed_commitment_sha256"],
            "scorer_configuration_sha256": locks[
                "scorer_configuration_sha256"
            ],
            "retired_r1_fingerprint_manifest_sha256": "not-built",
            **{
                key: value
                for key, value in locks.items()
                if key != "configuration_lock_sha256"
            },
            "corpus_sha256": V28.canonical_sha256([]),
        },
        "configuration_lock_sha256",
    )
    locks["configuration_lock_sha256"] = configuration[
        "configuration_lock_sha256"
    ]
    pre_generation = _self_hashed(
        {
            "version": V28.ARTIFACT_VERSIONS[
                "pre-generation-receipt.json"
            ],
            "state_slice": V28.PACKET_STATE_SLICE,
            "protocol_sha256": V28.EXPECTED_PROTOCOL_SHA256,
            "campaign_id": campaign["campaign_id"],
            "ledger_id": campaign["ledger_id"],
            "source_commit": provenance["source_commit"],
            "source_tree": provenance["source_tree"],
            "output_root": provenance["output_root"],
            "checkpoint_inventory_sha256": provenance[
                "checkpoint_inventory_sha256"
            ],
            "tokenizer_inventory_sha256": provenance[
                "tokenizer_inventory_sha256"
            ],
            "runtime_sha256": provenance["runtime_sha256"],
            "generator_inventory_sha256": provenance[
                "generator_inventory_sha256"
            ],
            "validator_inventory_sha256": provenance[
                "validator_inventory_sha256"
            ],
            "power_profile_sha256": locks["power_profile_sha256"],
            "concept_catalog_sha256": locks["concept_catalog_sha256"],
            "template_ast_catalog_sha256": locks[
                "template_ast_catalog_sha256"
            ],
            "derivation_grammar_sha256": locks[
                "derivation_grammar_sha256"
            ],
            "domain_tags_sha256": locks["domain_tags_sha256"],
            "scorer_contract_sha256": locks["scorer_contract_sha256"],
            "prompt_shell_sha256": locks["prompt_shell_sha256"],
            "future_assessment_identity_commitment_sha256": locks[
                "future_assessment_identity_commitment_sha256"
            ],
            "generator_input_allowlist_sha256": campaign[
                "generator_input_allowlist_sha256"
            ],
            "inputs_locked_before_ledger_claim": True,
            "seed_material_absent": True,
        },
        "receipt_sha256",
    )
    provenance["pre_generation_receipt_sha256"] = pre_generation[
        "receipt_sha256"
    ]
    seed_commitment = _self_hashed(
        {
            **V28._without(seed_commitment, "seed_commitment_sha256"),
            "pre_generation_receipt_sha256": provenance[
                "pre_generation_receipt_sha256"
            ],
            "one_shot_execution_claim_sha256": locks[
                "one_shot_execution_claim_sha256"
            ],
        },
        "seed_commitment_sha256",
    )
    locks["seed_commitment_sha256"] = seed_commitment[
        "seed_commitment_sha256"
    ]
    configuration = _self_hashed(
        {
            **V28._without(configuration, "configuration_lock_sha256"),
            "seed_commitment_sha256": locks["seed_commitment_sha256"],
        },
        "configuration_lock_sha256",
    )
    locks["configuration_lock_sha256"] = configuration[
        "configuration_lock_sha256"
    ]
    corpus = {
        "family_count": 0,
        "queries_per_family": 12,
        "query_count": 0,
        "families": [],
        "corpus_sha256": V28.canonical_sha256([]),
    }
    runs = []
    run_artifacts: dict[str, dict] = {}
    for index, arm_id in enumerate(("pre_update", "no_update")):
        starting_state = _sha("bundle-starting-state")
        update_budget = {
            "update_tokens": 0,
            "gradient_steps": 0,
            "adapter_rank": 0,
        }
        stage_order = (
            ["checkpoint_load", "evaluation"]
            if arm_id == "pre_update"
            else [
                "no_op_preparation",
                "source_removal",
                "checkpoint_load",
                "evaluation",
            ]
        )
        prep = _self_hashed(
            {
                "version": V28.ARTIFACT_VERSIONS["prep-receipt.json"],
                "state_slice": V28.PACKET_STATE_SLICE,
                "arm_id": arm_id,
                "process_id": _sha(f"bundle-prep-{index}"),
                "implementation_sha256": _sha(f"bundle-prep-impl-{arm_id}"),
                "configuration_sha256": _sha(f"bundle-prep-config-{arm_id}"),
                "starting_state_sha256": starting_state,
                "post_preparation_state_sha256": starting_state,
                "update_budget": update_budget,
            },
            "prep_receipt_sha256",
        )
        source_removal = _self_hashed(
            {
                "version": V28.ARTIFACT_VERSIONS[
                    "source-removal-manifest.json"
                ],
                "state_slice": V28.PACKET_STATE_SLICE,
                "arm_id": arm_id,
                "source_context_present": False,
                "retrieval_enabled": False,
                "source_context_removed": True,
                "retrieval_material_removed": True,
            },
            "source_removal_manifest_sha256",
        )
        process = _self_hashed(
            {
                "version": V28.ARTIFACT_VERSIONS[
                    "process-receipt.json"
                ],
                "state_slice": V28.PACKET_STATE_SLICE,
                "arm_id": arm_id,
                "process_id": _sha(f"bundle-eval-{index}"),
                "implementation_sha256": _sha("bundle-evaluator"),
                "configuration_sha256": _sha("bundle-evaluator-config"),
                "restart_loaded_state_sha256": starting_state,
                "runtime_inventory_sha256": provenance["runtime_sha256"],
                "tokenizer_inventory_sha256": provenance[
                    "tokenizer_inventory_sha256"
                ],
                "scorer_configuration_sha256": locks[
                    "scorer_configuration_sha256"
                ],
                "source_removal_manifest_sha256": source_removal[
                    "source_removal_manifest_sha256"
                ],
                "source_context_present": False,
                "retrieval_enabled": False,
            },
            "process_receipt_sha256",
        )
        observations: list[dict] = []
        run_manifest_base = {
            "version": V28.ARTIFACT_VERSIONS["run-manifest.json"],
            "state_slice": V28.PACKET_STATE_SLICE,
            "arm_id": arm_id,
            "run_id": f"synthetic-{arm_id}",
            "runtime_inventory_sha256": provenance["runtime_sha256"],
            "tokenizer_inventory_sha256": provenance[
                "tokenizer_inventory_sha256"
            ],
            "scorer_configuration_sha256": locks[
                "scorer_configuration_sha256"
            ],
            "raw_scores_sha256": V28.canonical_sha256([]),
            "observations_sha256": V28.canonical_sha256(observations),
            "prep_receipt_sha256": prep["prep_receipt_sha256"],
            "process_receipt_sha256": process["process_receipt_sha256"],
            "source_removal_manifest_sha256": source_removal[
                "source_removal_manifest_sha256"
            ],
            "starting_state_sha256": starting_state,
            "restart_loaded_state_sha256": starting_state,
            "stage_order": stage_order,
            "query_count": 0,
        }
        run_manifest = _self_hashed(
            run_manifest_base, "run_manifest_sha256"
        )
        run = {
            "arm_id": arm_id,
            "run_id": f"synthetic-{arm_id}",
            "prep_process_id": prep["process_id"],
            "evaluation_process_id": process["process_id"],
            "preparation_implementation_sha256": prep[
                "implementation_sha256"
            ],
            "preparation_configuration_sha256": prep[
                "configuration_sha256"
            ],
            "evaluator_implementation_sha256": process[
                "implementation_sha256"
            ],
            "evaluator_configuration_sha256": process[
                "configuration_sha256"
            ],
            "runtime_inventory_sha256": provenance["runtime_sha256"],
            "tokenizer_inventory_sha256": provenance[
                "tokenizer_inventory_sha256"
            ],
            "scorer_configuration_sha256": locks[
                "scorer_configuration_sha256"
            ],
            "source_removal_manifest_sha256": source_removal[
                "source_removal_manifest_sha256"
            ],
            "prep_receipt_sha256": prep["prep_receipt_sha256"],
            "process_receipt_sha256": process["process_receipt_sha256"],
            "raw_scores_sha256": V28.canonical_sha256([]),
            "observations_sha256": V28.canonical_sha256(observations),
            "run_manifest_sha256": run_manifest["run_manifest_sha256"],
            "score_rows": [],
            "starting_state_sha256": starting_state,
            "post_preparation_state_sha256": starting_state,
            "restart_loaded_state_sha256": starting_state,
            "update_budget": update_budget,
            "stage_order": stage_order,
            "query_count": 0,
        }
        runs.append(run)
        base = f"runs/{arm_id}"
        run_artifacts.update(
            {
                f"{base}/prep-receipt.json": prep,
                f"{base}/source-removal-manifest.json": source_removal,
                f"{base}/evaluation/raw-scores.json": {"score_rows": []},
                f"{base}/evaluation/observations.json": {
                    "observations": observations
                },
                f"{base}/evaluation/process-receipt.json": process,
                f"{base}/evaluation/run-manifest.json": run_manifest,
            }
        )
    packet = {
        "campaign": campaign,
        "provenance": provenance,
        "locks": locks,
        "corpus": corpus,
        "baseline_runs": runs,
    }
    artifacts = {
        **inventories,
        "power-profile.json": PROTOCOL["power_profile"],
        "concept-catalog.json": {
            "version": PROTOCOL["derivation_grammar"]["version"],
            "fact_kinds": PROTOCOL["derivation_grammar"]["fact_kinds"],
        },
        "template-ast-catalog.json": PROTOCOL["template_ast_catalog"],
        "derivation-grammar.json": PROTOCOL["derivation_grammar"],
        "domain-tags.json": PROTOCOL["domain_tags"],
        "scorer-configuration.json": scorer,
        "prompt-shell.json": PROTOCOL["prompt_shell"],
        "future-assessment-identity-commitment.json": future,
        "one-shot-execution-claim.json": one_shot,
        "seed-material.json": {
            "version": V28.ARTIFACT_VERSIONS["seed-material.json"],
            "state_slice": V28.PACKET_STATE_SLICE,
            "seed_hex": seed_hex,
        },
        "seed-commitment.json": seed_commitment,
        "configuration-lock.json": configuration,
        "pre-generation-receipt.json": pre_generation,
        "corpus/raw-corpus.json": corpus,
        "corpus/protocol-corpus.json": {
            "version": "synthetic.protocol-corpus.v1",
            "state_slice": V28.PACKET_STATE_SLICE,
            "corpus_sha256": corpus["corpus_sha256"],
            "family_count": 0,
        },
        **run_artifacts,
    }
    assert set(artifacts) == V28.BUNDLE_DATA_PATHS
    for path_text, value in artifacts.items():
        _write_canonical(root / path_text, value)
    _refresh_bundle_manifest(root, packet)
    return packet, root


def test_protocol_constants_are_exact_and_not_reduced() -> None:
    assert V28._validate_protocol(PROTOCOL) == []
    assert PROTOCOL["power_profile"]["families_per_fact_kind"] == 1536
    assert PROTOCOL["power_profile"]["family_count"] == 6144
    assert PROTOCOL["power_profile"]["queries_per_run"] == 73728
    assert PROTOCOL["power_profile"]["baseline_run_count"] == 2
    assert PROTOCOL["power_profile"]["two_sided_comparison_count"] == 16
    assert PROTOCOL["power_profile"]["adjusted_alpha"] == 0.003125
    assert PROTOCOL["power_profile"]["minimum_student_t_critical_value"] == 5.0


def test_missing_packet_is_not_run_before_real_fingerprint_exists() -> None:
    report = V28.validate_packet(None, PROTOCOL, None)
    assert report["status"] == "NotRun"
    assert report["open_gates"] == ["acquisition.packet_not_supplied"]
    assert report["gate_state"]["assessment"] == "SealedNotAuthorized"


def test_permutation_schedule_uses_all_24_mappings_per_block() -> None:
    expected = {tuple(value) for value in itertools.permutations(range(4))}
    for fact_kind in V28.REQUIRED_FACT_KINDS:
        observed = {
            tuple(
                V28.reconstruct_family(SEED_HEX, fact_kind, ordinal, PROTOCOL)[
                    "template_to_answer_permutation"
                ]
            )
            for ordinal in range(24)
        }
        assert observed == expected


def test_family_reconstruction_is_deterministic_and_query_balanced() -> None:
    first = V28.reconstruct_family(SEED_HEX, "opaque_mapping", 1523, PROTOCOL)
    second = V28.reconstruct_family(SEED_HEX, "opaque_mapping", 1523, PROTOCOL)
    assert first == second
    assert len(first["queries"]) == 12
    for evaluation_kind in V28.REQUIRED_EVALUATION_KINDS:
        choices = [
            query["expected_choice"]
            for query in first["queries"]
            if query["evaluation_kind"] == evaluation_kind
        ]
        assert sorted(choices) == [0, 1, 2, 3]


def test_score_binding_recomputes_argmax_and_token_hash() -> None:
    family = V28.reconstruct_family(SEED_HEX, "nonce_fact", 0, PROTOCOL)
    query = family["queries"][0]
    row = _score_row(query, 2)
    errors, choice = V28._validate_score_row(
        row, query, "row", SCORER_CONFIGURATION
    )
    assert errors == []
    assert choice == 2
    row["tokenized_input_sha256"] = _sha("wrong")
    assert "row.tokenized_input_sha256" in V28._validate_score_row(
        row, query, "row", SCORER_CONFIGURATION
    )[0]


def test_point_near_chance_can_fail_the_interval() -> None:
    counts = {
        f"family-{index}": (
            "opaque_mapping",
            [0, 0, 0] if index < 12 else [2, 2, 2],
        )
        for index in range(24)
    }
    intervals = V28._family_accuracy_intervals(counts, 5.0)
    overall = intervals["overall"]
    assert abs(overall["mean_chance_normalized_lift"]) < 1e-12
    assert overall["lower_bound"] < -0.05
    assert overall["upper_bound"] > 0.05


def test_fact_kind_failure_cannot_hide_inside_overall_pass() -> None:
    counts = {}
    for fact_kind in V28.REQUIRED_FACT_KINDS:
        for index in range(1536):
            per_kind = [1, 1, 1]
            if fact_kind == "opaque_mapping":
                per_kind[index % 3] = 2
            counts[f"{fact_kind}-{index}"] = (fact_kind, per_kind)
    intervals = V28._family_accuracy_intervals(counts, 5.0)
    assert intervals["overall"]["lower_bound"] >= -0.05
    assert intervals["overall"]["upper_bound"] <= 0.05
    for evaluation_kind in V28.REQUIRED_EVALUATION_KINDS:
        assert intervals[f"evaluation_kind:{evaluation_kind}"][
            "lower_bound"
        ] >= -0.05
        assert intervals[f"evaluation_kind:{evaluation_kind}"][
            "upper_bound"
        ] <= 0.05
    assert intervals["fact_kind:opaque_mapping"]["upper_bound"] > 0.05


def test_fingerprint_builder_typed_normalization_never_emits_raw_text() -> None:
    identifiers = {
        "namespace": {"ns-secret"},
        "anchor": {"ent-secret"},
        "value": {"val-secret"},
        "alias": {"als-secret"},
        "wrapper": {"hdl-secret"},
    }
    normalized = BUILDER._typed_normalize(
        "Registry ns-secret maps als-secret through ent-secret to val-secret.",
        identifiers,
    )
    assert normalized == (
        "registry <namespace> maps <alias> through <anchor> to <value>."
    )
    assert "secret" not in normalized


def test_real_protocol_fails_closed_until_r1_fingerprint_is_built() -> None:
    fingerprint = _empty_fingerprint()
    errors, _ = V28._validate_fingerprint_manifest(fingerprint, PROTOCOL)
    assert "r1_fingerprint.real_manifest_not_built" in errors


def test_exact_full_census_component_path_is_bundle_gated(
    full_packet, monkeypatch
) -> None:
    packet, protocol, fingerprint = full_packet
    monkeypatch.setattr(
        V28, "EXPECTED_PROTOCOL_SHA256", V28.canonical_sha256(protocol)
    )
    report = V28.validate_packet(packet, protocol, fingerprint)
    assert report["status"] == "NotRun"
    assert report["errors"] == []
    assert report["open_gates"] == [
        "acquisition.canonical_bundle_not_supplied"
    ]
    for arm in ("pre_update", "no_update"):
        intervals = report["baseline_equivalence_intervals"][arm]
        assert intervals["overall"]["cluster_count"] == 6144
        for fact_kind in V28.REQUIRED_FACT_KINDS:
            assert intervals[f"fact_kind:{fact_kind}"]["cluster_count"] == 1536
        for evaluation_kind in V28.REQUIRED_EVALUATION_KINDS:
            assert (
                intervals[f"evaluation_kind:{evaluation_kind}"]["cluster_count"]
                == 6144
            )
            assert intervals[f"evaluation_kind:{evaluation_kind}"][
                "lower_bound"
            ] >= -0.05
            assert intervals[f"evaluation_kind:{evaluation_kind}"][
                "upper_bound"
            ] <= 0.05


def test_true_later_gate_claim_is_invalid() -> None:
    changed = {
        "later_gates": {
            "update_arms": None,
            "retention_recovery": None,
            "selection": None,
            "assessment": None,
        },
        "claim_boundary": {
            claim: False for claim in PROTOCOL["required_false_claims"]
        },
    }
    changed["claim_boundary"]["model_backed_acquisition"] = True
    assert V28._validate_later_gates(changed, PROTOCOL) == ["claim_boundary"]


def test_reduced_power_profile_is_rejected() -> None:
    changed = copy.deepcopy(PROTOCOL)
    changed["power_profile"]["families_per_fact_kind"] = 192
    assert V28._validate_protocol(changed) == ["protocol.pinned_sha256"]


def test_generator_input_allowlist_denies_outcome_inputs() -> None:
    changed = copy.deepcopy(PROTOCOL)
    changed["generator_input_allowlist"].append("r1_observations")
    errors = V28._validate_protocol(changed)
    assert errors == ["protocol.pinned_sha256"]


def test_one_shot_second_seed_and_unsynced_ledger_fail() -> None:
    packet = {
        "campaign": {
            "campaign_id": "test",
            "ledger_id": "test-ledger",
            "seed_hex": SEED_HEX,
            "seed_draw_count": 2,
            "candidate_corpus_count": 1,
            "discarded_candidate_count": 0,
            "adaptive_expansion": False,
            "post_seed_power_change": False,
            "replacement_seed_allowed": False,
            "ledger_exclusive_create": True,
            "ledger_file_synced": False,
            "ledger_parent_synced": True,
            "post_claim_failure_recovery_allowed": False,
            "generator_input_allowlist_sha256": V28.canonical_sha256(
                PROTOCOL["generator_input_allowlist"]
            ),
            "generator_input_keys": PROTOCOL["generator_input_allowlist"],
        },
        "ordering": PROTOCOL["ordering_contract"],
    }
    errors = V28._validate_campaign(packet, PROTOCOL)
    assert "campaign.seed_draw_count" in errors
    assert "campaign.ledger_file_synced" in errors


def test_reused_process_identity_is_rejected() -> None:
    shared = _sha("shared-process")
    runs = {
        "pre_update": {
            "prep_process_id": shared,
            "evaluation_process_id": _sha("pre-eval"),
        },
        "no_update": {
            "prep_process_id": _sha("no-prep"),
            "evaluation_process_id": shared,
        },
    }
    assert V28._validate_process_identity_distinctness(runs) == [
        "runs.process_identity_distinctness"
    ]


def test_wrong_no_update_order_and_retained_source_fail() -> None:
    query = V28.reconstruct_family(SEED_HEX, "nonce_fact", 0, PROTOCOL)[
        "queries"
    ][0]
    run = _run("no_update", [_score_row(query, 0)], [query], 10)
    run["query_count"] = 73728
    run["source_context_present"] = True
    run["stage_order"] = ["checkpoint_load", "evaluation"]
    errors = V28._validate_run_shape(run, "no_update", PROTOCOL)
    assert "runs.no_update.source_context_present" in errors
    assert "runs.no_update.stage_order" in errors


@pytest.mark.parametrize(
    "mutation, expected",
    [
        (lambda row: row["label_log_probability_scores"].__setitem__(0, True), "row.scores"),
        (
            lambda row: row["label_log_probability_scores"].__setitem__(
                0, float("nan")
            ),
            "row.scores",
        ),
        (lambda row: row.__setitem__("tie_break", "highest"), "row.tie_break"),
        (lambda row: row.__setitem__("observed_choice", 3), "row.observed_choice"),
    ],
)
def test_score_rows_fail_closed(mutation, expected: str) -> None:
    query = V28.reconstruct_family(SEED_HEX, "entity_relation", 0, PROTOCOL)[
        "queries"
    ][0]
    row = _score_row(query, 0)
    mutation(row)
    assert expected in V28._validate_score_row(
        row, query, "row", SCORER_CONFIGURATION
    )[0]


def test_retired_fingerprint_detects_exact_reuse() -> None:
    family = V28.reconstruct_family(SEED_HEX, "changed_rule", 7, PROTOCOL)
    values = V28._family_nonreuse_values(family)
    reused = V28.retired_fingerprint("family_ids", family["family_id"])
    assert reused in {
        V28.retired_fingerprint("family_ids", value)
        for value in values["family_ids"]
    }


def test_fingerprint_builder_is_deterministic() -> None:
    identifiers = {
        "namespace": set(),
        "anchor": set(),
        "value": set(),
        "alias": set(),
        "wrapper": set(),
    }
    value = "Nonce 123 is value 456."
    assert BUILDER._typed_normalize(
        value, identifiers
    ) == BUILDER._typed_normalize(value, identifiers)


def test_production_import_graph_has_no_generator_model_or_network_imports() -> None:
    source = (HERE / "v28r2.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    forbidden = {
        "v28_acquisition",
        "v28r2_acquisition",
        "mlx",
        "transformers",
        "subprocess",
        "socket",
        "urllib",
        "http.client",
    }
    assert not imported & forbidden


def test_public_validator_cli_exclusively_writes_not_run_report(
    tmp_path: Path,
) -> None:
    protocol_path = tmp_path / "protocol.json"
    fingerprint_path = tmp_path / "fingerprint.json"
    packet_path = tmp_path / "acquisition-packet.json"
    output_path = tmp_path / "report.json"
    protocol_path.write_text(json.dumps(PROTOCOL), encoding="utf-8")
    fingerprint_path.write_text("{}\n", encoding="utf-8")
    packet_path.write_text("null\n", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(HERE / "validate_packet.py"),
            "--protocol",
            str(protocol_path),
            "--r1-fingerprint",
            str(fingerprint_path),
            "--bundle-root",
            str(tmp_path),
            "--packet",
            str(packet_path),
            "--output",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == "NotRun"
    second = subprocess.run(
        [
            sys.executable,
            str(HERE / "validate_packet.py"),
            "--protocol",
            str(protocol_path),
            "--r1-fingerprint",
            str(fingerprint_path),
            "--bundle-root",
            str(tmp_path),
            "--packet",
            str(packet_path),
            "--output",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert second.returncode == 1
    assert "output must be a new absolute path" in second.stderr


def test_reduced_full_packet_is_invalid_without_statistical_interpretation(
    full_packet, monkeypatch
) -> None:
    packet, protocol, fingerprint = full_packet
    monkeypatch.setattr(
        V28, "EXPECTED_PROTOCOL_SHA256", V28.canonical_sha256(protocol)
    )
    changed = dict(packet)
    changed["corpus"] = dict(packet["corpus"])
    changed["corpus"]["families"] = packet["corpus"]["families"][:-1]
    changed["packet_sha256"] = V28.canonical_sha256(
        V28._without(changed, "packet_sha256")
    )
    report = V28.validate_packet(changed, protocol, fingerprint)
    assert report["status"] == "Invalid"
    assert "corpus.family_census" in report["errors"]


def test_late_swapped_row_and_cross_arm_mismatch_fail_public_path(
    full_packet, monkeypatch
) -> None:
    packet, protocol, fingerprint = full_packet
    monkeypatch.setattr(
        V28, "EXPECTED_PROTOCOL_SHA256", V28.canonical_sha256(protocol)
    )
    changed = dict(packet)
    changed_runs = list(packet["baseline_runs"])
    changed_no_update = dict(changed_runs[1])
    changed_rows = list(changed_no_update["score_rows"])
    changed_rows[-2], changed_rows[-1] = changed_rows[-1], changed_rows[-2]
    changed_no_update["score_rows"] = changed_rows
    changed_no_update["raw_scores_sha256"] = V28.canonical_sha256(changed_rows)
    queries = [
        query
        for family in packet["corpus"]["families"]
        for query in family["queries"]
    ]
    changed_observations = [
        {
            "query_id": query["query_id"],
            "expected_choice": query["expected_choice"],
            "observed_choice": row["observed_choice"],
        }
        for row, query in zip(changed_rows, queries)
    ]
    changed_no_update["observations_sha256"] = V28.canonical_sha256(
        changed_observations
    )
    changed_runs[1] = changed_no_update
    changed["baseline_runs"] = changed_runs
    changed["packet_sha256"] = V28.canonical_sha256(
        V28._without(changed, "packet_sha256")
    )
    report = V28.validate_packet(changed, protocol, fingerprint)
    assert report["status"] == "Invalid"
    assert "runs.cross_arm_parity.score_rows" in report["errors"]
    assert any(error.endswith(".query_id") for error in report["errors"])


def test_all_fact_kinds_have_valid_three_level_semantics() -> None:
    for fact_kind in V28.REQUIRED_FACT_KINDS:
        family = V28.reconstruct_family(SEED_HEX, fact_kind, 0, PROTOCOL)
        assert V28._validate_family_semantics(family, PROTOCOL) == []
        assert family["source_text"] in family["training_text"]
        assert family["support_text"] in family["training_text"]
        assert [
            len(family["concept_ast"]["evaluation_paths"][kind])
            for kind in V28.REQUIRED_EVALUATION_KINDS
        ] == [1, 2, 3]


@pytest.mark.parametrize(
    "section",
    [
        "baseline_contract",
        "derivation_contract",
        "derivation_grammar",
        "domain_tags",
        "ordering_contract",
        "prompt_shell",
        "scorer_contract",
        "template_ast_catalog",
        "required_false_claims",
    ],
)
def test_every_nested_protocol_section_is_digest_pinned(section: str) -> None:
    changed = copy.deepcopy(PROTOCOL)
    changed[section] = None
    assert V28._validate_protocol(changed) == ["protocol.pinned_sha256"]


@pytest.mark.parametrize(
    "mutation, expected",
    [
        (
            lambda protocol: protocol["derivation_grammar"][
                "evaluation_kinds"
            ]["multi_hop"].__setitem__(
                "path", ["bogus", "$fact.value_edge"]
            ),
            "protocol.derivation_grammar.multi_hop",
        ),
        (
            lambda protocol: protocol["derivation_grammar"].__setitem__(
                "correct_candidate_index", 3
            ),
            "protocol.derivation_grammar.core",
        ),
        (
            lambda protocol: protocol["template_ast_catalog"]["evaluation"][
                "paraphrase"
            ][0].__setitem__("derivation", "withheld_composition"),
            "protocol.template_ast_catalog.evaluation.paraphrase",
        ),
        (
            lambda protocol: protocol["prompt_shell"].__setitem__(
                "allowed_slots", ["source"]
            ),
            "protocol.prompt_shell.policy",
        ),
        (
            lambda protocol: protocol["scorer_contract"].__setitem__(
                "method", "random_generation"
            ),
            "protocol.scorer_contract",
        ),
        (
            lambda protocol: protocol["template_ast_catalog"]["training"].__setitem__(
                1,
                copy.deepcopy(
                    protocol["template_ast_catalog"]["training"][0]
                ),
            ),
            "protocol.template_ast_catalog.training_uniqueness",
        ),
        (
            lambda protocol: protocol["template_ast_catalog"]["evaluation"][
                "paraphrase"
            ].__setitem__(
                1,
                copy.deepcopy(
                    protocol["template_ast_catalog"]["evaluation"][
                        "paraphrase"
                    ][0]
                ),
            ),
            "protocol.template_ast_catalog.paraphrase.uniqueness",
        ),
        (
            lambda protocol: protocol["prompt_shell"]["ast"]["children"][
                2
            ].__setitem__("format", "{option}"),
            "protocol.prompt_shell.policy",
        ),
    ],
)
def test_repinning_cannot_bypass_executable_protocol_invariants(
    monkeypatch, mutation, expected: str
) -> None:
    changed = copy.deepcopy(PROTOCOL)
    mutation(changed)
    monkeypatch.setattr(
        V28, "EXPECTED_PROTOCOL_SHA256", V28.canonical_sha256(changed)
    )
    assert expected in V28._validate_protocol(changed)


def test_duplicate_or_reordered_choice_token_ids_are_rejected() -> None:
    query = V28.reconstruct_family(SEED_HEX, "nonce_fact", 0, PROTOCOL)[
        "queries"
    ][0]
    for token_ids in ([32, 32, 34, 35], [35, 34, 33, 32]):
        row = _score_row(query, 0)
        row["choice_token_ids"] = token_ids
        errors, _ = V28._validate_score_row(
            row, query, "row", SCORER_CONFIGURATION
        )
        assert "row.choice_token_ids" in errors


@pytest.mark.parametrize(
    "field",
    [
        "evaluator_implementation_sha256",
        "evaluator_configuration_sha256",
        "starting_state_sha256",
        "post_preparation_state_sha256",
        "restart_loaded_state_sha256",
        "runtime_inventory_sha256",
        "tokenizer_inventory_sha256",
        "scorer_configuration_sha256",
        "query_count",
        "raw_scores_sha256",
        "observations_sha256",
        "score_rows",
    ],
)
def test_cross_arm_parity_is_field_complete(field: str) -> None:
    query = V28.reconstruct_family(SEED_HEX, "nonce_fact", 0, PROTOCOL)[
        "queries"
    ][0]
    rows = [_score_row(query, 0)]
    runs = {
        "pre_update": _run("pre_update", rows, [query], 20),
        "no_update": _run("no_update", list(rows), [query], 30),
    }
    if field == "score_rows":
        runs["no_update"][field] = []
    elif field == "query_count":
        runs["no_update"][field] = 1
    else:
        runs["no_update"][field] = _sha(f"changed-{field}")
    assert f"runs.cross_arm_parity.{field}" in V28._validate_cross_arm_parity(
        runs
    )


def test_canonical_bundle_has_exact_packet_and_lock_bindings(
    tmp_path: Path,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    assert V28.validate_bundle_root(
        root,
        packet,
        PROTOCOL,
        root / "acquisition-packet.json",
    ) == []


@pytest.mark.parametrize(
    ("path_text", "hash_key", "expected"),
    [
        (
            "one-shot-execution-claim.json",
            "one_shot_execution_claim_sha256",
            "bundle.binding.one_shot.shape",
        ),
        (
            "runs/no_update/source-removal-manifest.json",
            "source_removal_manifest_sha256",
            "bundle.binding.no_update.source_removal.shape",
        ),
    ],
)
def test_lifecycle_artifacts_reject_rehashed_unknown_fields(
    tmp_path: Path,
    path_text: str,
    hash_key: str,
    expected: str,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    artifacts = {
        path: json.loads((root / path).read_text(encoding="utf-8"))
        for path in V28.BUNDLE_DATA_PATHS
    }
    artifact = artifacts[path_text]
    artifact["contradictory_unknown_field"] = True
    artifact[hash_key] = V28.canonical_sha256(
        V28._without(artifact, hash_key)
    )
    errors = V28._validate_bundle_artifact_bindings(
        packet, PROTOCOL, artifacts
    )
    assert expected in errors


@pytest.mark.parametrize(
    ("path_text", "digest_field"),
    list(V28.INVENTORY_DIGEST_FIELDS.items()),
)
def test_inventory_payload_digests_are_sha256(
    tmp_path: Path,
    path_text: str,
    digest_field: str,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    artifacts = {
        path: json.loads((root / path).read_text(encoding="utf-8"))
        for path in V28.BUNDLE_DATA_PATHS
    }
    artifacts[path_text][digest_field] = "not-a-sha256"
    errors = V28._validate_bundle_artifact_bindings(
        packet, PROTOCOL, artifacts
    )
    assert f"bundle.binding.{path_text}.shape" in errors


@pytest.mark.parametrize("field", ["version", "state_slice"])
def test_seed_material_pins_version_and_state_slice(
    tmp_path: Path,
    field: str,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    artifacts = {
        path: json.loads((root / path).read_text(encoding="utf-8"))
        for path in V28.BUNDLE_DATA_PATHS
    }
    artifacts["seed-material.json"][field] = "wrong"
    errors = V28._validate_bundle_artifact_bindings(
        packet, PROTOCOL, artifacts
    )
    assert "bundle.binding.seed_material" in errors


def test_run_receipts_bind_to_sealed_runtime_and_checkpoint(
    tmp_path: Path,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    artifacts = {
        path: json.loads((root / path).read_text(encoding="utf-8"))
        for path in V28.BUNDLE_DATA_PATHS
    }
    for run in packet["baseline_runs"]:
        run["runtime_inventory_sha256"] = _sha("unsealed-runtime")
        run["starting_state_sha256"] = _sha("unsealed-checkpoint")
        run["post_preparation_state_sha256"] = _sha("unsealed-checkpoint")
        run["restart_loaded_state_sha256"] = _sha("unsealed-checkpoint")
        arm_id = run["arm_id"]
        prep = artifacts[f"runs/{arm_id}/prep-receipt.json"]
        prep["starting_state_sha256"] = run["starting_state_sha256"]
        prep["post_preparation_state_sha256"] = run[
            "post_preparation_state_sha256"
        ]
        prep["prep_receipt_sha256"] = V28.canonical_sha256(
            V28._without(prep, "prep_receipt_sha256")
        )
        run["prep_receipt_sha256"] = prep["prep_receipt_sha256"]
        process = artifacts[f"runs/{arm_id}/evaluation/process-receipt.json"]
        process["runtime_inventory_sha256"] = run[
            "runtime_inventory_sha256"
        ]
        process["restart_loaded_state_sha256"] = run[
            "restart_loaded_state_sha256"
        ]
        process["process_receipt_sha256"] = V28.canonical_sha256(
            V28._without(process, "process_receipt_sha256")
        )
        run["process_receipt_sha256"] = process["process_receipt_sha256"]
        manifest = artifacts[f"runs/{arm_id}/evaluation/run-manifest.json"]
        for key in (
            "runtime_inventory_sha256",
            "starting_state_sha256",
            "restart_loaded_state_sha256",
            "prep_receipt_sha256",
            "process_receipt_sha256",
        ):
            manifest[key] = run[key]
        manifest["run_manifest_sha256"] = V28.canonical_sha256(
            V28._without(manifest, "run_manifest_sha256")
        )
        run["run_manifest_sha256"] = manifest["run_manifest_sha256"]
    errors = V28._validate_bundle_artifact_bindings(
        packet, PROTOCOL, artifacts
    )
    assert "bundle.binding.pre_update.sealed.runtime_inventory_sha256" in errors
    assert "bundle.binding.pre_update.sealed.starting_state_sha256" in errors
    assert (
        "bundle.binding.pre_update.sealed.restart_loaded_state_sha256"
        in errors
    )


@pytest.mark.parametrize(
    "field",
    [
        "checkpoint_inventory_sha256",
        "pre_generation_receipt_sha256",
        "one_shot_execution_claim_sha256",
    ],
)
def test_seed_commitment_is_checkpoint_and_lifecycle_bound(
    tmp_path: Path,
    field: str,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    artifacts = {
        path: json.loads((root / path).read_text(encoding="utf-8"))
        for path in V28.BUNDLE_DATA_PATHS
    }
    seed = artifacts["seed-commitment.json"]
    seed[field] = _sha(f"wrong-{field}")
    seed["seed_commitment_sha256"] = V28.canonical_sha256(
        V28._without(seed, "seed_commitment_sha256")
    )
    errors = V28._validate_bundle_artifact_bindings(
        packet, PROTOCOL, artifacts
    )
    assert "bundle.binding.seed_commitment" in errors


def test_future_assessment_ids_are_unique_and_r1_disjoint(
    tmp_path: Path,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    artifacts = {
        path: json.loads((root / path).read_text(encoding="utf-8"))
        for path in V28.BUNDLE_DATA_PATHS
    }
    future = artifacts["future-assessment-identity-commitment.json"]
    future["family_ids"] = ["duplicate", "duplicate"]
    future["future_assessment_identity_commitment_sha256"] = (
        V28.canonical_sha256(
            V28._without(
                future, "future_assessment_identity_commitment_sha256"
            )
        )
    )
    errors = V28._validate_bundle_artifact_bindings(
        packet, PROTOCOL, artifacts
    )
    assert "bundle.binding.future_assessment.shape" in errors
    retired_sets = {name: set() for name in V28.FINGERPRINT_SET_NAMES}
    retired_sets["future_assessment_family_ids"].add(
        V28.retired_fingerprint(
            "future_assessment_family_ids", "retired-r1-family"
        )
    )
    assert V28._validate_future_assessment_nonreuse(
        {"family_ids": ["retired-r1-family"]}, retired_sets
    ) == ["bundle.binding.future_assessment.r1_reuse"]


def test_bundle_rejects_extra_file_and_external_packet_path(
    tmp_path: Path,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    extra = root / "extra.json"
    _write_canonical(extra, {})
    errors = V28.validate_bundle_root(
        root,
        packet,
        PROTOCOL,
        root / "acquisition-packet.json",
    )
    assert "bundle.file_census" in errors
    external = tmp_path / "acquisition-packet.json"
    _write_canonical(external, packet)
    assert V28.validate_bundle_root(
        root,
        packet,
        PROTOCOL,
        external,
    ) == ["bundle.packet_path_binding"]


def test_bundle_rejects_rehashed_scorer_token_drift(tmp_path: Path) -> None:
    packet, root = _canonical_bundle(tmp_path)
    scorer_path = root / "scorer-configuration.json"
    scorer = json.loads(scorer_path.read_text(encoding="utf-8"))
    scorer["choice_token_ids"] = [32, 32, 34, 35]
    scorer["scorer_configuration_sha256"] = V28.canonical_sha256(
        V28._without(scorer, "scorer_configuration_sha256")
    )
    _write_canonical(scorer_path, scorer)
    manifest_path = root / "artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["entries"]:
        if entry["path"] == "scorer-configuration.json":
            entry["bytes"] = scorer_path.stat().st_size
            entry["sha256"] = V28.sha256_file(scorer_path)
    manifest["manifest_sha256"] = V28.canonical_sha256(
        V28._without(manifest, "manifest_sha256")
    )
    _write_canonical(manifest_path, manifest)
    packet["artifact_manifest_sha256"] = manifest["manifest_sha256"]
    _write_canonical(root / "acquisition-packet.json", packet)
    errors = V28.validate_bundle_root(
        root,
        packet,
        PROTOCOL,
        root / "acquisition-packet.json",
    )
    assert "bundle.binding.scorer_configuration.contract" in errors
    assert "bundle.binding.scorer_configuration.locks" in errors


def test_bundle_rejects_rehashed_false_pre_generation_protocol(
    tmp_path: Path,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    receipt_path = root / "pre-generation-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["protocol_sha256"] = _sha("bogus-protocol")
    receipt["receipt_sha256"] = V28.canonical_sha256(
        V28._without(receipt, "receipt_sha256")
    )
    packet["provenance"]["pre_generation_receipt_sha256"] = receipt[
        "receipt_sha256"
    ]
    _write_canonical(receipt_path, receipt)
    _refresh_bundle_manifest(root, packet)
    errors = V28.validate_bundle_root(
        root,
        packet,
        PROTOCOL,
        root / "acquisition-packet.json",
    )
    assert "bundle.binding.pre_generation.protocol_sha256" in errors


def test_bundle_rejects_rehashed_false_source_removal(
    tmp_path: Path,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    arm_id = "no_update"
    source_path = root / f"runs/{arm_id}/source-removal-manifest.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    source["source_context_removed"] = False
    source["source_removal_manifest_sha256"] = V28.canonical_sha256(
        V28._without(source, "source_removal_manifest_sha256")
    )
    _write_canonical(source_path, source)
    run = next(
        value
        for value in packet["baseline_runs"]
        if value["arm_id"] == arm_id
    )
    run["source_removal_manifest_sha256"] = source[
        "source_removal_manifest_sha256"
    ]
    process_path = root / f"runs/{arm_id}/evaluation/process-receipt.json"
    process = json.loads(process_path.read_text(encoding="utf-8"))
    process["source_removal_manifest_sha256"] = source[
        "source_removal_manifest_sha256"
    ]
    process["process_receipt_sha256"] = V28.canonical_sha256(
        V28._without(process, "process_receipt_sha256")
    )
    run["process_receipt_sha256"] = process["process_receipt_sha256"]
    _write_canonical(process_path, process)
    manifest_path = root / f"runs/{arm_id}/evaluation/run-manifest.json"
    run_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_manifest["source_removal_manifest_sha256"] = source[
        "source_removal_manifest_sha256"
    ]
    run_manifest["process_receipt_sha256"] = process[
        "process_receipt_sha256"
    ]
    run_manifest["run_manifest_sha256"] = V28.canonical_sha256(
        V28._without(run_manifest, "run_manifest_sha256")
    )
    run["run_manifest_sha256"] = run_manifest["run_manifest_sha256"]
    _write_canonical(manifest_path, run_manifest)
    _refresh_bundle_manifest(root, packet)
    errors = V28.validate_bundle_root(
        root,
        packet,
        PROTOCOL,
        root / "acquisition-packet.json",
    )
    assert (
        "bundle.binding.no_update.source_removal.source_context_removed"
        in errors
    )


def test_malformed_bundled_packet_returns_invalid_without_exception(
    tmp_path: Path,
) -> None:
    packet, root = _canonical_bundle(tmp_path)
    packet["corpus"] = []
    report = V28.validate_packet(
        packet,
        PROTOCOL,
        _empty_fingerprint(),
        root,
        root / "acquisition-packet.json",
    )
    assert report["status"] == "Invalid"
    assert "corpus.object" in report["errors"]


def test_report_emits_complete_false_claim_census() -> None:
    report = V28._report("NotRun", [])
    expected = {
        "local_acquisition_validator_v28r2",
        *PROTOCOL["required_false_claims"],
    }
    assert set(report["claim_boundary"]) == expected
    assert report["claim_boundary"]["local_acquisition_validator_v28r2"]
    assert not any(
        value
        for key, value in report["claim_boundary"].items()
        if key != "local_acquisition_validator_v28r2"
    )


def test_missing_bundle_precedes_scientific_failure_disposition() -> None:
    report = V28._baseline_disposition(
        passed=False,
        bundle_missing=True,
        interval_reports={"synthetic": {}},
    )
    assert report["status"] == "NotRun"
    assert report["open_gates"] == [
        "acquisition.canonical_bundle_not_supplied"
    ]
    retired = V28._baseline_disposition(
        passed=False,
        bundle_missing=False,
        interval_reports={"synthetic": {}},
    )
    assert retired["status"] == "CorpusNotNovel"
    assert retired["open_gates"] == [
        "acquisition.v28r2_permanently_retired_corpus_not_novel"
    ]


def test_structural_eight_grams_are_line_bounded_and_exact() -> None:
    identifiers = {
        "namespace": set(),
        "anchor": set(),
        "value": set(),
        "alias": set(),
        "wrapper": set(),
    }
    for token_count, expected in ((7, 0), (8, 1), (9, 2)):
        sets = {name: set() for name in BUILDER.SET_NAMES}
        BUILDER._add_structural_surfaces(
            sets,
            " ".join(f"word{index}" for index in range(token_count)),
            identifiers,
        )
        assert len(sets["structural_ngram_hashes"]) == expected
    sets = {name: set() for name in BUILDER.SET_NAMES}
    BUILDER._add_structural_surfaces(
        sets,
        "one two three four\nfive six seven eight",
        identifiers,
    )
    assert sets["structural_ngram_hashes"] == set()


def test_builder_and_validator_share_typed_normalization() -> None:
    family = V28.reconstruct_family(SEED_HEX, "nonce_fact", 0, PROTOCOL)
    identifiers = {
        "namespace": {family["namespace"]},
        "anchor": {family["anchor_id"]},
        "value": set(family["value_ids"]),
        "alias": {family["alias_id"]},
        "wrapper": {family["wrapper_id"]},
    }
    surface = (
        f"Registry {family['namespace']} maps {family['alias_id']} through "
        f"{family['anchor_id']} to {family['value_ids'][0]}."
    )
    assert BUILDER._typed_normalize(
        surface, identifiers
    ) == V28._normalize_family_typed(family, surface)


def test_answer_and_derivation_mapping_hashes_use_one_encoding() -> None:
    family = V28.reconstruct_family(SEED_HEX, "nonce_fact", 0, PROTOCOL)
    query = family["queries"][0]
    values = V28._family_nonreuse_values(family)
    assert query["answer_mapping_sha256"] in values["mapping_hashes"]
    assert query["derivation_manifest_sha256"] in values["mapping_hashes"]


def test_synthetic_r1_schema_extraction_is_hash_only_and_validator_compatible(
    monkeypatch,
) -> None:
    inputs = _synthetic_r1_builder_inputs()
    packet, report = inputs[:2]
    monkeypatch.setattr(
        BUILDER, "R1_PACKET_SHA256", packet["packet_sha256"]
    )
    monkeypatch.setattr(
        BUILDER, "R1_REPORT_SHA256", report["report_sha256"]
    )
    result = BUILDER._extract_manifest(*inputs)
    serialized = json.dumps(result, sort_keys=True)
    assert "secret" not in serialized
    assert result["model_outcomes_included"] is False
    assert result["fingerprint_sets"]["family_ids"]["count"] == 96
    assert result["fingerprint_sets"]["query_ids"]["count"] == 1152
    assert result["fingerprint_sets"]["anchor_ids"]["count"] == 384
    assert result["fingerprint_sets"]["alias_ids"]["count"] == 1536
    assert result["fingerprint_sets"]["wrapper_ids"]["count"] == 1536
    protocol = copy.deepcopy(PROTOCOL)
    protocol["nonreuse_contract"][
        "retired_r1_fingerprint_manifest_sha256"
    ] = result["manifest_sha256"]
    monkeypatch.setattr(
        V28, "EXPECTED_PROTOCOL_SHA256", V28.canonical_sha256(protocol)
    )
    monkeypatch.setattr(
        V28, "R1_PACKET_SHA256", packet["packet_sha256"]
    )
    monkeypatch.setattr(
        V28, "R1_REPORT_SHA256", report["report_sha256"]
    )
    errors, _ = V28._validate_fingerprint_manifest(result, protocol)
    assert errors == []


def test_cross_version_reduced_projections_are_id_agnostic_and_comparable() -> None:
    r2_family = V28.reconstruct_family(
        SEED_HEX, "nonce_fact", 0, PROTOCOL
    )
    r1_family = copy.deepcopy(_synthetic_r1_builder_inputs()[5]["families"][0])
    r1_family["fact_kind"] = r2_family["fact_kind"]
    target = r1_family["semantic_ast"]["records"][0]
    target["aliases"] = [r2_family["alias_id"]]
    target["wrappers"] = [r2_family["wrapper_id"]]
    assert BUILDER._reduced_concept_projection(
        r1_family
    ) == V28._reduced_concept_projection(r2_family)
    identifiers = {
        "namespace": {r2_family["namespace"]},
        "anchor": {r2_family["anchor_id"]},
        "value": set(r2_family["value_ids"]),
        "alias": {r2_family["alias_id"]},
        "wrapper": {r2_family["wrapper_id"]},
    }
    assert BUILDER._reduced_training_template_projection(
        {"fact_kind": r2_family["fact_kind"]},
        identifiers,
        r2_family["source_text"],
        r2_family["support_text"],
    ) == V28._reduced_training_template_projection(r2_family)
    query = r2_family["queries"][0]
    r1_query = {
        "evaluation_kind": query["evaluation_kind"],
        "variant": query["template_ordinal"],
        "question": query["question_text"],
        "prompt": query["prompt_text"],
        "template_family_id": "renamed-r1-template-id",
    }
    assert BUILDER._reduced_evaluation_template_projection(
        r1_query, identifiers
    ) == V28._reduced_evaluation_template_projection(r2_family, query)


def test_protocol_binds_the_exact_retired_r1_manifest_identity(
    monkeypatch,
) -> None:
    changed = copy.deepcopy(PROTOCOL)
    changed["nonreuse_contract"][
        "retired_r1_artifact_manifest_sha256"
    ] = _sha("wrong-r1-manifest")
    monkeypatch.setattr(
        V28, "EXPECTED_PROTOCOL_SHA256", V28.canonical_sha256(changed)
    )
    assert (
        "protocol.nonreuse_contract.r1_source_identity"
        in V28._validate_protocol(changed)
    )


def test_builder_write_all_handles_short_writes(monkeypatch) -> None:
    writes: list[bytes] = []

    def short_write(_descriptor: int, payload: bytes) -> int:
        count = min(3, len(payload))
        writes.append(payload[:count])
        return count

    monkeypatch.setattr(BUILDER.os, "write", short_write)
    BUILDER._write_all(7, b"abcdefghij")
    assert b"".join(writes) == b"abcdefghij"


def test_builder_validates_closed_r1_manifest_census_and_raw_identity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "synthetic-r1-bundle"
    root.mkdir()
    entries = []
    for path_text in sorted(
        BUILDER.REQUIRED_ROOT_PATHS - {"artifact-manifest.json"}
    ):
        path = root / path_text
        _write_canonical(path, {})
        entries.append(
            {
                "path": path_text,
                "sha256": BUILDER.sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    manifest = {
        "version": "synthetic.r1.manifest.v1",
        "state_slice": "synthetic-r1",
        "files": entries,
        "manifest_sha256": BUILDER.canonical_sha256(entries),
    }
    manifest_path = root / "artifact-manifest.json"
    _write_canonical(manifest_path, manifest)
    monkeypatch.setattr(
        BUILDER, "R1_MANIFEST_SHA256", manifest["manifest_sha256"]
    )
    monkeypatch.setattr(
        BUILDER,
        "R1_MANIFEST_FILE_SHA256",
        BUILDER.sha256_file(manifest_path),
    )
    declared = BUILDER._validate_root_and_manifest(root, manifest)
    assert set(declared) == (
        BUILDER.REQUIRED_ROOT_PATHS - {"artifact-manifest.json"}
    )
    _write_canonical(root / "undeclared.json", {})
    with pytest.raises(ValueError, match="file census"):
        BUILDER._validate_root_and_manifest(root, manifest)
    (root / "undeclared.json").unlink()
    monkeypatch.setattr(
        BUILDER, "R1_MANIFEST_FILE_SHA256", _sha("wrong-raw-manifest")
    )
    with pytest.raises(ValueError, match="raw digest mismatch"):
        BUILDER._validate_root_and_manifest(root, manifest)


def test_family_semantics_rejects_short_line_and_eight_gram_overlap() -> None:
    family = V28.reconstruct_family(SEED_HEX, "nonce_fact", 0, PROTOCOL)
    short_collision = copy.deepcopy(family)
    short_collision["queries"][0][
        "question_text"
    ] = "Store these atomic declarations:"
    assert (
        "semantic.training_evaluation_skeleton_overlap"
        in V28._validate_family_semantics(short_collision, PROTOCOL)
    )
    eight_collision = copy.deepcopy(family)
    eight_words = (
        "sealed atomic fact for <generated> is exactly <generated>."
    )
    eight_collision["training_text"] += "\n" + eight_words + " extra"
    eight_collision["queries"][0]["question_text"] = "prefix " + eight_words
    assert (
        "semantic.training_evaluation_ngram_overlap"
        in V28._validate_family_semantics(eight_collision, PROTOCOL)
    )


def test_family_semantics_keeps_seven_token_and_cross_line_boundary() -> None:
    family = V28.reconstruct_family(SEED_HEX, "nonce_fact", 0, PROTOCOL)
    changed = copy.deepcopy(family)
    changed["training_text"] += (
        "\none two three four\nfive six seven eight"
    )
    changed["queries"][0][
        "question_text"
    ] = "one two three four five six seven eight"
    errors = V28._validate_family_semantics(changed, PROTOCOL)
    assert "semantic.training_evaluation_ngram_overlap" not in errors
