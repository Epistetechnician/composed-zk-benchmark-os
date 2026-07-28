from __future__ import annotations

import hashlib
import hmac
import itertools
import json
import math
import os
import re
import statistics
import string
import unicodedata
from pathlib import Path
from typing import Any, Iterable


PROTOCOL_VERSION = "astral.rgs_acquisition_v28r2.protocol.v1"
PACKET_VERSION = "mesh.astral_v28r2_acquisition_packet.v1"
PACKET_STATE_SLICE = "astral-rgs-v28r2-powered-acquisition-novelty"
CLAIM_CEILING = "LocalAcquisitionQualificationValidatorV28R2"
PROTOCOL_STATE_SLICE = "astral-rgs-v28r2-acquisition-qualification-validator"
EXPECTED_PROTOCOL_SHA256 = (
    "sha256:236d7a2f4d8f81fdd1990c746cdfff0d3de85c191781bb7c3fde9d84d5b1aaf2"
)
R1_PACKET_SHA256 = (
    "sha256:2fd74b389907d3167518a0d91d9d63f18fda7c1231a51764657e791286ee2ad0"
)
R1_REPORT_SHA256 = (
    "sha256:3e24804dc84744a300bb11bc246fdfd40256459f97a68da0df7993d676b9ea3d"
)
R1_MANIFEST_SHA256 = (
    "sha256:5b01a32e1ba9d7d9ce84c8b301f29e0145962ac8c0eac0ec59b07cd5cfca846e"
)
R1_PACKET_FILE_SHA256 = (
    "sha256:f3b5217e725322d2cf964267b63af4fb956a0232507ac646f07fbaf12a31c121"
)
R1_REPORT_FILE_SHA256 = (
    "sha256:0ec4215734583566f593c6214eec2317523e0bc7471e6d9f837ca3e0337b53e9"
)
R1_MANIFEST_FILE_SHA256 = (
    "sha256:7ca7e09302aff508368d53335aa47c90564fa6393e262ecadc8db51e401ce5f7"
)
REQUIRED_FACT_KINDS = (
    "nonce_fact",
    "entity_relation",
    "changed_rule",
    "opaque_mapping",
)
REQUIRED_EVALUATION_KINDS = (
    "paraphrase",
    "multi_hop",
    "withheld_composition",
)
BUNDLE_DATA_PATHS = frozenset(
    {
        "pre-generation-receipt.json",
        "checkpoint-inventory.json",
        "tokenizer-inventory.json",
        "runtime-inventory.json",
        "generator-inventory.json",
        "validator-inventory.json",
        "power-profile.json",
        "concept-catalog.json",
        "template-ast-catalog.json",
        "derivation-grammar.json",
        "domain-tags.json",
        "scorer-configuration.json",
        "prompt-shell.json",
        "future-assessment-identity-commitment.json",
        "one-shot-execution-claim.json",
        "seed-material.json",
        "seed-commitment.json",
        "configuration-lock.json",
        "corpus/raw-corpus.json",
        "corpus/protocol-corpus.json",
        "runs/pre_update/prep-receipt.json",
        "runs/pre_update/source-removal-manifest.json",
        "runs/pre_update/evaluation/raw-scores.json",
        "runs/pre_update/evaluation/observations.json",
        "runs/pre_update/evaluation/process-receipt.json",
        "runs/pre_update/evaluation/run-manifest.json",
        "runs/no_update/prep-receipt.json",
        "runs/no_update/source-removal-manifest.json",
        "runs/no_update/evaluation/raw-scores.json",
        "runs/no_update/evaluation/observations.json",
        "runs/no_update/evaluation/process-receipt.json",
        "runs/no_update/evaluation/run-manifest.json",
    }
)
BUNDLE_ALL_PATHS = frozenset(
    {*BUNDLE_DATA_PATHS, "acquisition-packet.json", "artifact-manifest.json"}
)
PACKET_KEYS = frozenset(
    {
        "version",
        "state_slice",
        "protocol_sha256",
        "campaign",
        "provenance",
        "ordering",
        "locks",
        "corpus",
        "baseline_runs",
        "later_gates",
        "claim_boundary",
        "artifact_manifest_sha256",
        "packet_sha256",
    }
)
PROTOCOL_KEYS = frozenset(
    {
        "version",
        "packet_version",
        "state_slice",
        "packet_state_slice",
        "claim_ceiling",
        "choice_count",
        "choice_labels",
        "required_fact_kinds",
        "required_evaluation_kinds",
        "power_profile",
        "permutation_contract",
        "baseline_contract",
        "ordering_contract",
        "nonreuse_contract",
        "derivation_contract",
        "domain_tags",
        "derivation_grammar",
        "template_ast_catalog",
        "prompt_shell",
        "scorer_contract",
        "generator_input_allowlist",
        "required_false_claims",
    }
)
CAMPAIGN_KEYS = frozenset(
    {
        "campaign_id",
        "ledger_id",
        "seed_hex",
        "seed_draw_count",
        "candidate_corpus_count",
        "discarded_candidate_count",
        "adaptive_expansion",
        "post_seed_power_change",
        "replacement_seed_allowed",
        "ledger_exclusive_create",
        "ledger_file_synced",
        "ledger_parent_synced",
        "post_claim_failure_recovery_allowed",
        "generator_input_allowlist_sha256",
        "generator_input_keys",
    }
)
PROVENANCE_KEYS = frozenset(
    {
        "source_commit",
        "source_tree",
        "source_clean",
        "checkpoint_inventory_sha256",
        "tokenizer_inventory_sha256",
        "runtime_sha256",
        "generator_inventory_sha256",
        "validator_inventory_sha256",
        "pre_generation_receipt_sha256",
        "output_root",
    }
)
LOCK_KEYS = frozenset(
    {
        "power_profile_sha256",
        "concept_catalog_sha256",
        "template_ast_catalog_sha256",
        "derivation_grammar_sha256",
        "domain_tags_sha256",
        "scorer_contract_sha256",
        "scorer_configuration_sha256",
        "prompt_shell_sha256",
        "future_assessment_identity_commitment_sha256",
        "configuration_lock_sha256",
        "one_shot_execution_claim_sha256",
        "seed_commitment_sha256",
    }
)
CORPUS_KEYS = frozenset(
    {
        "family_count",
        "queries_per_family",
        "query_count",
        "families",
        "corpus_sha256",
    }
)
RUN_KEYS = frozenset(
    {
        "arm_id",
        "run_id",
        "persistence_class",
        "preparation_implementation_sha256",
        "preparation_configuration_sha256",
        "evaluator_implementation_sha256",
        "evaluator_configuration_sha256",
        "prep_process_id",
        "evaluation_process_id",
        "starting_state_sha256",
        "post_preparation_state_sha256",
        "restart_loaded_state_sha256",
        "runtime_inventory_sha256",
        "tokenizer_inventory_sha256",
        "scorer_configuration_sha256",
        "source_removal_manifest_sha256",
        "prep_receipt_sha256",
        "process_receipt_sha256",
        "source_context_present",
        "retrieval_enabled",
        "source_removal_verified",
        "fresh_checkpoint_load",
        "stage_order",
        "update_budget",
        "query_count",
        "raw_scores_sha256",
        "observations_sha256",
        "run_manifest_sha256",
        "score_rows",
    }
)
ARTIFACT_VERSIONS = {
    "checkpoint-inventory.json": "astral.rgs_v28r2.checkpoint_inventory.v1",
    "tokenizer-inventory.json": "astral.rgs_v28r2.tokenizer_inventory.v1",
    "runtime-inventory.json": "astral.rgs_v28r2.runtime_inventory.v1",
    "generator-inventory.json": "astral.rgs_v28r2.generator_inventory.v1",
    "validator-inventory.json": "astral.rgs_v28r2.validator_inventory.v1",
    "pre-generation-receipt.json": "astral.rgs_v28r2.pre_generation_receipt.v1",
    "one-shot-execution-claim.json": "astral.rgs_v28r2.one_shot_execution_claim.v1",
    "seed-material.json": "astral.rgs_v28r2.seed_material.v1",
    "seed-commitment.json": "astral.rgs_v28r2.seed_commitment.v1",
    "configuration-lock.json": "astral.rgs_v28r2.configuration_lock.v1",
    "future-assessment-identity-commitment.json": (
        "astral.rgs_v28r2.future_assessment_identity_commitment.v1"
    ),
    "prep-receipt.json": "astral.rgs_v28r2.prep_receipt.v1",
    "source-removal-manifest.json": (
        "astral.rgs_v28r2.source_removal_manifest.v1"
    ),
    "process-receipt.json": "astral.rgs_v28r2.process_receipt.v1",
    "run-manifest.json": "astral.rgs_v28r2.run_manifest.v1",
}
INVENTORY_KEYS = {
    "checkpoint-inventory.json": frozenset(
        {"version", "state_slice", "checkpoint_state_sha256"}
    ),
    "tokenizer-inventory.json": frozenset(
        {"version", "state_slice", "tokenizer_content_sha256"}
    ),
    "runtime-inventory.json": frozenset(
        {"version", "state_slice", "runtime_content_sha256"}
    ),
    "generator-inventory.json": frozenset(
        {"version", "state_slice", "implementation_sha256"}
    ),
    "validator-inventory.json": frozenset(
        {"version", "state_slice", "implementation_sha256"}
    ),
}
INVENTORY_DIGEST_FIELDS = {
    "checkpoint-inventory.json": "checkpoint_state_sha256",
    "tokenizer-inventory.json": "tokenizer_content_sha256",
    "runtime-inventory.json": "runtime_content_sha256",
    "generator-inventory.json": "implementation_sha256",
    "validator-inventory.json": "implementation_sha256",
}
PRE_GENERATION_KEYS = frozenset(
    {
        "version",
        "state_slice",
        "protocol_sha256",
        "campaign_id",
        "ledger_id",
        "source_commit",
        "source_tree",
        "output_root",
        "checkpoint_inventory_sha256",
        "tokenizer_inventory_sha256",
        "runtime_sha256",
        "generator_inventory_sha256",
        "validator_inventory_sha256",
        "power_profile_sha256",
        "concept_catalog_sha256",
        "template_ast_catalog_sha256",
        "derivation_grammar_sha256",
        "domain_tags_sha256",
        "scorer_contract_sha256",
        "prompt_shell_sha256",
        "future_assessment_identity_commitment_sha256",
        "generator_input_allowlist_sha256",
        "inputs_locked_before_ledger_claim",
        "seed_material_absent",
        "receipt_sha256",
    }
)
ONE_SHOT_KEYS = frozenset(
    {
        "version",
        "state_slice",
        "campaign_id",
        "ledger_id",
        "output_root",
        "source_commit",
        "source_tree",
        "ledger_exclusive_create",
        "ledger_file_synced",
        "ledger_parent_synced",
        "seed_draw_count",
        "candidate_corpus_count",
        "permanently_retired_after_failure",
        "ledger_claim_order",
        "seed_draw_order",
        "locked_input_sha256s",
        "one_shot_execution_claim_sha256",
    }
)
SEED_COMMITMENT_KEYS = frozenset(
    {
        "version",
        "state_slice",
        "campaign_id",
        "ledger_id",
        "checkpoint_inventory_sha256",
        "pre_generation_receipt_sha256",
        "one_shot_execution_claim_sha256",
        "seed_sha256",
        "seed_commitment_sha256",
    }
)
FUTURE_COMMITMENT_KEYS = frozenset(
    {
        "version",
        "state_slice",
        "campaign_id",
        "ledger_id",
        "family_ids",
        "assessment_content_generated",
        "assessment_opened",
        "future_assessment_identity_commitment_sha256",
    }
)
PREP_RECEIPT_KEYS = frozenset(
    {
        "version",
        "state_slice",
        "arm_id",
        "process_id",
        "implementation_sha256",
        "configuration_sha256",
        "starting_state_sha256",
        "post_preparation_state_sha256",
        "update_budget",
        "prep_receipt_sha256",
    }
)
SOURCE_REMOVAL_KEYS = frozenset(
    {
        "version",
        "state_slice",
        "arm_id",
        "source_context_present",
        "retrieval_enabled",
        "source_context_removed",
        "retrieval_material_removed",
        "source_removal_manifest_sha256",
    }
)
PROCESS_RECEIPT_KEYS = frozenset(
    {
        "version",
        "state_slice",
        "arm_id",
        "process_id",
        "implementation_sha256",
        "configuration_sha256",
        "restart_loaded_state_sha256",
        "runtime_inventory_sha256",
        "tokenizer_inventory_sha256",
        "scorer_configuration_sha256",
        "source_removal_manifest_sha256",
        "source_context_present",
        "retrieval_enabled",
        "process_receipt_sha256",
    }
)
RUN_MANIFEST_KEYS = frozenset(
    {
        "version",
        "state_slice",
        "arm_id",
        "run_id",
        "runtime_inventory_sha256",
        "tokenizer_inventory_sha256",
        "scorer_configuration_sha256",
        "raw_scores_sha256",
        "observations_sha256",
        "prep_receipt_sha256",
        "process_receipt_sha256",
        "source_removal_manifest_sha256",
        "starting_state_sha256",
        "restart_loaded_state_sha256",
        "stage_order",
        "query_count",
        "run_manifest_sha256",
    }
)
FINGERPRINT_SET_NAMES = (
    "seed_commitments",
    "campaign_ids",
    "ledger_ids",
    "namespace_ids",
    "family_ids",
    "item_ids",
    "query_ids",
    "concept_schema_ids",
    "anchor_ids",
    "value_ids",
    "alias_ids",
    "wrapper_ids",
    "source_hashes",
    "support_hashes",
    "question_hashes",
    "prompt_hashes",
    "option_hashes",
    "dependency_hashes",
    "mapping_hashes",
    "training_template_ids",
    "evaluation_template_ids",
    "concept_ast_hashes",
    "template_ast_hashes",
    "normalized_skeleton_hashes",
    "normalized_line_hashes",
    "structural_ngram_hashes",
    "future_assessment_family_ids",
    "future_assessment_commitments",
)


class DuplicateKeyError(ValueError):
    pass


def _object_pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def load_json_strict(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_object_pairs_no_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"nonfinite JSON constant: {value}")
        ),
    )


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _without(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    return {candidate: value for candidate, value in mapping.items() if candidate != key}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _exact_keys(value: Any, keys: Iterable[str]) -> bool:
    return isinstance(value, dict) and set(value) == set(keys)


def _derive(seed: bytes, domain: str, *parts: object) -> str:
    message = "\0".join((domain, *(str(part) for part in parts))).encode("utf-8")
    return hmac.new(seed, message, hashlib.sha256).hexdigest()


def _identifier(prefix: str, seed: bytes, domain: str, *parts: object) -> str:
    return f"{prefix}-{_derive(seed, domain, *parts)[:24]}"


def _text_token(seed: bytes, domain: str, *parts: object) -> str:
    return f"v{_derive(seed, domain, *parts)[:16]}"


def _render(template: str, values: dict[str, str]) -> str:
    return unicodedata.normalize("NFC", template.format(**values))


def _template_ast_hash(template_ast: dict[str, Any]) -> str:
    return canonical_sha256(template_ast)


def _prompt(
    question: str,
    options: list[str],
    prompt_shell: dict[str, Any],
) -> str:
    children = prompt_shell["ast"]["children"]
    lines = [
        children[0]["value"],
        question,
        *(
            children[2]["format"].format(label=label, option=option)
            for label, option in zip(children[2]["labels"], options)
        ),
        children[3]["value"],
    ]
    rendered = prompt_shell["line_separator"].join(lines)
    if prompt_shell["terminal_newline"]:
        rendered += prompt_shell["line_separator"]
    return unicodedata.normalize("NFC", rendered)


def _option_order(expected_choice: int) -> list[int]:
    order = [1, 2, 3]
    return [
        0 if position == expected_choice else order.pop(0)
        for position in range(4)
    ]


def reconstruct_family(
    seed_hex: str,
    fact_kind: str,
    family_ordinal: int,
    protocol: dict[str, Any],
) -> dict[str, Any]:
    if (
        len(seed_hex) != 64
        or any(character not in "0123456789abcdef" for character in seed_hex)
    ):
        raise ValueError("seed")
    if fact_kind not in REQUIRED_FACT_KINDS:
        raise ValueError("fact_kind")
    if not 0 <= family_ordinal < 1536:
        raise ValueError("family_ordinal")
    seed = bytes.fromhex(seed_hex)
    domain_prefix = protocol["domain_tags"]["hmac_domain_prefix"]
    tags = protocol["domain_tags"]["tags"]
    domain = lambda key: f"{domain_prefix}\0{tags[key]}"  # noqa: E731
    grammar = protocol["derivation_grammar"]
    permutations = list(itertools.permutations(range(4)))
    permutation_index = family_ordinal % 24
    permutation = permutations[permutation_index]
    block_index = family_ordinal // 24
    subject = _text_token(seed, domain("subject"), fact_kind, family_ordinal)
    alias = _text_token(seed, domain("alias"), fact_kind, family_ordinal)
    wrapper = _text_token(seed, domain("wrapper"), fact_kind, family_ordinal)
    relation_name = _text_token(
        seed, domain("relation_name"), fact_kind, family_ordinal
    )
    candidates = [
        _text_token(
            seed,
            domain("candidate_value"),
            fact_kind,
            family_ordinal,
            index,
        )
        for index in range(grammar["candidate_count"])
    ]
    correct_candidate_index = grammar["correct_candidate_index"]
    values = {
        "subject": subject,
        "alias": alias,
        "wrapper": wrapper,
        "relation_name": relation_name,
        "value": candidates[correct_candidate_index],
        "new_value": candidates[correct_candidate_index],
        "old_value": candidates[1],
    }
    concept = grammar["fact_kinds"][fact_kind]
    values["fact_descriptor"] = _render(concept["descriptor_surface"], values)
    source_text = _render(concept["source_surface"], values)
    support_text = _render(concept["support_surface"], values)
    premise_block = grammar["training_payload_separator"].join(
        (source_text, support_text)
    )
    family_id = _identifier(
        "r2fam", seed, domain("family_id"), fact_kind, family_ordinal
    )
    item_id = _identifier(
        "r2item", seed, domain("item_id"), fact_kind, family_ordinal
    )
    namespace = _identifier(
        "r2ns", seed, domain("namespace_id"), fact_kind, family_ordinal
    )
    concept_schema_id = f"v28r2-{fact_kind}-concept-v1"
    common_edges = grammar["common_edges"]
    evaluation_paths = {
        evaluation_kind: [
            (
                concept["value_edge"]["id"]
                if edge == "$fact.value_edge"
                else edge
            )
            for edge in grammar["evaluation_kinds"][evaluation_kind]["path"]
        ]
        for evaluation_kind in REQUIRED_EVALUATION_KINDS
    }
    training_premise_order: list[str] = []
    for entry in grammar["training_premise_order"]:
        if entry == "$fact.value_edge":
            training_premise_order.append(concept["value_edge"]["id"])
        elif entry == "$fact.superseded_edges":
            training_premise_order.extend(
                edge["id"] for edge in concept["superseded_edges"]
            )
        else:
            training_premise_order.append(entry)
    concept_ast = {
        "kind": fact_kind,
        "schema": concept_schema_id,
        "subject": subject,
        "alias": alias,
        "wrapper": wrapper,
        "relation_name": relation_name,
        "candidate_values": candidates,
        "correct_value_index": correct_candidate_index,
        "active_value_edge": concept["value_edge"],
        "superseded_edges": concept["superseded_edges"],
        "common_edges": common_edges,
        "evaluation_paths": evaluation_paths,
        "training_premise_order": training_premise_order,
    }
    training_template_ordinal = family_ordinal % 4
    training_template = protocol["template_ast_catalog"]["training"][
        training_template_ordinal
    ]
    training_template_id = training_template["id"]
    training_text = _render(
        training_template["surface"],
        {"premise_block": premise_block},
    )
    queries: list[dict[str, Any]] = []
    for evaluation_kind in REQUIRED_EVALUATION_KINDS:
        templates = protocol["template_ast_catalog"]["evaluation"][
            evaluation_kind
        ]
        for template_ordinal, template_ast in enumerate(templates):
            expected_choice = permutation[template_ordinal]
            option_order = _option_order(expected_choice)
            options = [candidates[index] for index in option_order]
            question_text = _render(template_ast["surface"], values)
            prompt_text = _prompt(
                question_text,
                options,
                protocol["prompt_shell"],
            )
            query_id = _identifier(
                "r2query",
                seed,
                domain("query_id"),
                fact_kind,
                family_ordinal,
                evaluation_kind,
                template_ordinal,
            )
            dependency_hashes = [
                sha256_bytes(source_text.encode("utf-8")),
                sha256_bytes(support_text.encode("utf-8")),
                canonical_sha256(concept_ast),
            ]
            mapping = {
                "expected_choice": expected_choice,
                "option_order": option_order,
                "semantic_correct_candidate_index": correct_candidate_index,
            }
            query = {
                "query_id": query_id,
                "family_id": family_id,
                "evaluation_kind": evaluation_kind,
                "template_ordinal": template_ordinal,
                "evaluation_template_id": template_ast["id"],
                "evaluation_template_ast_sha256": _template_ast_hash(
                    template_ast
                ),
                "expected_choice": expected_choice,
                "option_order": option_order,
                "options": options,
                "option_hashes": [
                    sha256_bytes(option.encode("utf-8")) for option in options
                ],
                "question_text": question_text,
                "question_sha256": sha256_bytes(question_text.encode("utf-8")),
                "prompt_text": prompt_text,
                "prompt_sha256": sha256_bytes(prompt_text.encode("utf-8")),
                "dependency_hashes": dependency_hashes,
                "answer_mapping_sha256": canonical_sha256(mapping),
                "derivation_manifest_sha256": canonical_sha256(
                    {
                        "resolved_edge_ids": evaluation_paths[evaluation_kind],
                        "start_slot": grammar["evaluation_kinds"][
                            evaluation_kind
                        ]["start_slot"],
                        "fact_kind": fact_kind,
                        "family_ordinal": family_ordinal,
                        "evaluation_kind": evaluation_kind,
                        "template_ordinal": template_ordinal,
                    }
                ),
                "withheld_from_training": True,
            }
            queries.append(query)
    return {
        "family_id": family_id,
        "item_id": item_id,
        "namespace": namespace,
        "fact_kind": fact_kind,
        "family_ordinal": family_ordinal,
        "block_index": block_index,
        "permutation_index": permutation_index,
        "template_to_answer_permutation": list(permutation),
        "concept_schema_id": concept_schema_id,
        "concept_ast": concept_ast,
        "concept_ast_sha256": canonical_sha256(concept_ast),
        "source_text": source_text,
        "source_sha256": sha256_bytes(source_text.encode("utf-8")),
        "support_text": support_text,
        "support_sha256": sha256_bytes(support_text.encode("utf-8")),
        "training_text": training_text,
        "training_sha256": sha256_bytes(training_text.encode("utf-8")),
        "training_template_id": training_template_id,
        "training_template_ast_sha256": _template_ast_hash(training_template),
        "anchor_id": subject,
        "value_ids": candidates,
        "alias_id": alias,
        "wrapper_id": wrapper,
        "queries": queries,
    }


def _normalize_typed(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value).lower()
    pieces = re.split(r"[ \t\r\n\f\v]+", normalized.strip(" \t\r\n\f\v"))
    return " ".join(
        "<generated>" if piece.startswith(("v", "r2")) else piece
        for piece in pieces
    )


def _normalize_family_typed(family: dict[str, Any], value: str) -> str:
    identifiers = {
        "namespace": {family["namespace"]},
        "anchor": {family["anchor_id"]},
        "value": set(family["value_ids"]),
        "alias": {family["alias_id"]},
        "wrapper": {family["wrapper_id"]},
    }
    normalized = unicodedata.normalize("NFC", value)
    replacements = [
        (identifier, f"<{kind}>")
        for kind, candidates in identifiers.items()
        for identifier in candidates
    ]
    for identifier, placeholder in sorted(
        replacements, key=lambda pair: (-len(pair[0]), pair[0])
    ):
        normalized = re.sub(
            rf"(?<![A-Za-z0-9_-]){re.escape(identifier)}(?![A-Za-z0-9_-])",
            placeholder,
            normalized,
        )
    return re.sub(r"[ \t\r\n\f\v]+", " ", normalized.lower()).strip(
        " \t\r\n\f\v"
    )


def _add_family_structural_values(
    values: dict[str, set[str]],
    family: dict[str, Any],
    surface: str,
) -> None:
    normalized_surface = _normalize_family_typed(family, surface)
    values["normalized_skeleton_hashes"].add(
        sha256_bytes(normalized_surface.encode("utf-8"))
    )
    for line in surface.splitlines():
        normalized_line = _normalize_family_typed(family, line)
        if not normalized_line:
            continue
        values["normalized_line_hashes"].add(
            sha256_bytes(normalized_line.encode("utf-8"))
        )
        tokens = normalized_line.split()
        for index in range(max(0, len(tokens) - 7)):
            values["structural_ngram_hashes"].add(
                sha256_bytes(
                    " ".join(tokens[index : index + 8]).encode("utf-8")
                )
            )


def retired_fingerprint(set_name: str, canonical_value: str) -> str:
    payload = (
        "v28r1-fingerprint-v1\0" + set_name + "\0" + canonical_value
    ).encode("utf-8")
    return sha256_bytes(payload)


def _reduced_concept_projection(
    family: dict[str, Any],
) -> dict[str, Any]:
    ast = family["concept_ast"]
    return {
        "fact_kind": family["fact_kind"],
        "candidate_value_count": len(ast["candidate_values"]),
        "target_alias_count": 1,
        "target_wrapper_count": 1,
        "evaluation_path_lengths": {
            kind: len(ast["evaluation_paths"][kind])
            for kind in REQUIRED_EVALUATION_KINDS
        },
    }


def _reduced_training_template_projection(
    family: dict[str, Any],
) -> dict[str, Any]:
    return {
        "fact_kind": family["fact_kind"],
        "source_skeleton": _normalize_family_typed(
            family, family["source_text"]
        ),
        "support_skeleton": _normalize_family_typed(
            family, family["support_text"]
        ),
    }


def _reduced_evaluation_template_projection(
    family: dict[str, Any],
    query: dict[str, Any],
) -> dict[str, Any]:
    return {
        "evaluation_kind": query["evaluation_kind"],
        "variant": query["template_ordinal"],
        "question_skeleton": _normalize_family_typed(
            family, query["question_text"]
        ),
        "prompt_skeleton": _normalize_family_typed(
            family, query["prompt_text"]
        ),
    }


def _family_nonreuse_values(family: dict[str, Any]) -> dict[str, set[str]]:
    values = {name: set() for name in FINGERPRINT_SET_NAMES}
    values["namespace_ids"].add(family["namespace"])
    values["family_ids"].add(family["family_id"])
    values["item_ids"].add(family["item_id"])
    values["concept_schema_ids"].add(family["concept_schema_id"])
    values["anchor_ids"].add(family["anchor_id"])
    values["value_ids"].update(family["value_ids"])
    values["alias_ids"].add(family["alias_id"])
    values["wrapper_ids"].add(family["wrapper_id"])
    values["source_hashes"].add(family["source_sha256"])
    values["support_hashes"].add(family["support_sha256"])
    values["training_template_ids"].add(family["training_template_id"])
    values["concept_ast_hashes"].add(family["concept_ast_sha256"])
    values["concept_ast_hashes"].add(
        canonical_sha256(_reduced_concept_projection(family))
    )
    values["template_ast_hashes"].add(family["training_template_ast_sha256"])
    values["template_ast_hashes"].add(
        canonical_sha256(_reduced_training_template_projection(family))
    )
    for surface in (
        family["source_text"],
        family["support_text"],
        family["training_text"],
    ):
        _add_family_structural_values(values, family, surface)
    for query in family["queries"]:
        values["query_ids"].add(query["query_id"])
        values["question_hashes"].add(query["question_sha256"])
        values["prompt_hashes"].add(query["prompt_sha256"])
        values["option_hashes"].update(query["option_hashes"])
        values["dependency_hashes"].update(query["dependency_hashes"])
        values["mapping_hashes"].add(query["answer_mapping_sha256"])
        values["mapping_hashes"].add(query["derivation_manifest_sha256"])
        values["evaluation_template_ids"].add(query["evaluation_template_id"])
        values["template_ast_hashes"].add(
            query["evaluation_template_ast_sha256"]
        )
        values["template_ast_hashes"].add(
            canonical_sha256(
                _reduced_evaluation_template_projection(family, query)
            )
        )
        for surface in (query["question_text"], query["prompt_text"]):
            _add_family_structural_values(values, family, surface)
    return values


def _surface_ngrams(surface: str) -> set[str]:
    result: set[str] = set()
    for line in surface.splitlines():
        tokens = _normalize_typed(line).split()
        for index in range(max(0, len(tokens) - 7)):
            result.add(" ".join(tokens[index : index + 8]))
    return result


def _validate_family_semantics(
    family: dict[str, Any],
    protocol: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    ast = family["concept_ast"]
    active_edge = ast["active_value_edge"]
    grammar = protocol["derivation_grammar"]
    if (
        active_edge.get("status") != "active"
        or active_edge.get("from_slot") != "subject"
        or active_edge.get("to_slot") != "candidate_values[0]"
    ):
        errors.append("semantic.active_value_edge")
    if family["fact_kind"] == "changed_rule":
        superseded = ast["superseded_edges"]
        if (
            len(superseded) != 1
            or superseded[0].get("status") != "superseded"
            or superseded[0].get("to_slot") != "candidate_values[1]"
        ):
            errors.append("semantic.changed_rule_supersession")
    elif ast["superseded_edges"]:
        errors.append("semantic.unexpected_supersession")
    common_edges = ast["common_edges"]
    edges = {
        edge["id"]: edge
        for edge in [*common_edges, active_edge, *ast["superseded_edges"]]
    }
    if (
        len(edges)
        != len(common_edges) + 1 + len(ast["superseded_edges"])
        or any(edge.get("status") != "active" for edge in common_edges)
    ):
        errors.append("semantic.edge_census")
    expected_training_order: list[str] = []
    for entry in grammar["training_premise_order"]:
        if entry == "$fact.value_edge":
            expected_training_order.append(active_edge["id"])
        elif entry == "$fact.superseded_edges":
            expected_training_order.extend(
                edge["id"] for edge in ast["superseded_edges"]
            )
        else:
            expected_training_order.append(entry)
    if ast["training_premise_order"] != expected_training_order:
        errors.append("semantic.training_premise_order")
    for kind in REQUIRED_EVALUATION_KINDS:
        grammar_path = grammar["evaluation_kinds"][kind]
        expected_path = [
            active_edge["id"] if edge == "$fact.value_edge" else edge
            for edge in grammar_path["path"]
        ]
        path = ast["evaluation_paths"].get(kind)
        if path != expected_path or len(path) != grammar_path[
            "required_edge_count"
        ]:
            errors.append(f"semantic.path.{kind}")
            continue
        current_slot = grammar_path["start_slot"]
        for edge_id in path:
            edge = edges.get(edge_id)
            if (
                edge is None
                or edge.get("status") != "active"
                or edge.get("from_slot") != current_slot
            ):
                errors.append(f"semantic.path.{kind}")
                break
            current_slot = edge["to_slot"]
        if current_slot != "candidate_values[0]":
            errors.append(f"semantic.path.{kind}")
    if (
        grammar["candidate_count"] != len(family["value_ids"])
        or grammar["correct_candidate_index"] != ast["correct_value_index"]
        or ast["correct_value_index"] != 0
        or grammar["withheld_composite_edges_forbidden"] is not True
    ):
        errors.append("semantic.grammar_contract")
    if (
        family["source_text"] not in family["training_text"]
        or family["support_text"] not in family["training_text"]
    ):
        errors.append("semantic.training_premises")
    training_skeleton = _normalize_typed(family["training_text"])
    training_ngrams = _surface_ngrams(family["training_text"])
    training_lines = {
        _normalize_typed(line)
        for line in family["training_text"].splitlines()
        if line.strip()
    }
    for query in family["queries"]:
        if (
            family["source_text"] in query["prompt_text"]
            or family["support_text"] in query["prompt_text"]
        ):
            errors.append("semantic.source_leak")
        evaluation_lines = {
            _normalize_typed(line)
            for line in query["question_text"].splitlines()
            if line.strip()
        }
        if (
            _normalize_typed(query["question_text"]) == training_skeleton
            or training_lines & evaluation_lines
        ):
            errors.append("semantic.training_evaluation_skeleton_overlap")
        if training_ngrams & _surface_ngrams(query["question_text"]):
            errors.append("semantic.training_evaluation_ngram_overlap")
    return errors


def _validate_protocol(protocol: Any) -> list[str]:
    if not isinstance(protocol, dict):
        return ["protocol.object"]
    if canonical_sha256(protocol) != EXPECTED_PROTOCOL_SHA256:
        return ["protocol.pinned_sha256"]
    errors: list[str] = []
    if set(protocol) != PROTOCOL_KEYS:
        errors.append("protocol.keys")
    for key, expected in {
        "version": PROTOCOL_VERSION,
        "packet_version": PACKET_VERSION,
        "state_slice": PROTOCOL_STATE_SLICE,
        "packet_state_slice": PACKET_STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "choice_count": 4,
        "choice_labels": ["A", "B", "C", "D"],
        "required_fact_kinds": list(REQUIRED_FACT_KINDS),
        "required_evaluation_kinds": list(REQUIRED_EVALUATION_KINDS),
    }.items():
        if protocol.get(key) != expected:
            errors.append(f"protocol.{key}")
    tags = protocol["domain_tags"]["tags"]
    if set(tags) != {
        "namespace_id",
        "family_id",
        "item_id",
        "subject",
        "alias",
        "wrapper",
        "relation_name",
        "candidate_value",
        "query_id",
    } or len(set(tags.values())) != 9:
        errors.append("protocol.domain_tags")
    grammar = protocol["derivation_grammar"]
    if set(grammar["fact_kinds"]) != set(REQUIRED_FACT_KINDS):
        errors.append("protocol.derivation_grammar.fact_kinds")
    if set(grammar["evaluation_kinds"]) != set(REQUIRED_EVALUATION_KINDS):
        errors.append("protocol.derivation_grammar.evaluation_kinds")
    expected_derivations = {
        "paraphrase": {
            "path": ["$fact.value_edge"],
            "required_edge_count": 1,
            "start_slot": "subject",
        },
        "multi_hop": {
            "path": ["alias_to_subject", "$fact.value_edge"],
            "required_edge_count": 2,
            "start_slot": "alias",
        },
        "withheld_composition": {
            "path": [
                "wrapper_to_alias",
                "alias_to_subject",
                "$fact.value_edge",
            ],
            "required_edge_count": 3,
            "start_slot": "wrapper",
        },
    }
    for kind, edge_count in zip(REQUIRED_EVALUATION_KINDS, (1, 2, 3)):
        derivation = grammar["evaluation_kinds"][kind]
        if (
            derivation["required_edge_count"] != edge_count
            or len(derivation["path"]) != edge_count
            or derivation != expected_derivations[kind]
        ):
            errors.append(f"protocol.derivation_grammar.{kind}")
    if (
        grammar["candidate_count"] != 4
        or grammar["correct_candidate_index"] != 0
        or grammar["training_premise_order"]
        != [
            "$fact.value_edge",
            "$fact.superseded_edges",
            "alias_to_subject",
            "wrapper_to_alias",
        ]
        or grammar["training_payload_separator"] != "\n"
        or grammar["withheld_composite_edges_forbidden"] is not True
        or grammar["common_edges"]
        != [
            {
                "from_slot": "alias",
                "id": "alias_to_subject",
                "predicate": "denotes",
                "status": "active",
                "to_slot": "subject",
            },
            {
                "from_slot": "wrapper",
                "id": "wrapper_to_alias",
                "predicate": "unwraps_to",
                "status": "active",
                "to_slot": "alias",
            },
        ]
    ):
        errors.append("protocol.derivation_grammar.core")
    for fact_kind, fact in grammar["fact_kinds"].items():
        value_edge = fact["value_edge"]
        if (
            value_edge.get("from_slot") != "subject"
            or value_edge.get("to_slot") != "candidate_values[0]"
            or value_edge.get("status") != "active"
        ):
            errors.append(
                f"protocol.derivation_grammar.{fact_kind}.value_edge"
            )
        superseded = fact["superseded_edges"]
        if fact_kind == "changed_rule":
            if (
                len(superseded) != 1
                or superseded[0].get("to_slot") != "candidate_values[1]"
                or superseded[0].get("status") != "superseded"
            ):
                errors.append(
                    "protocol.derivation_grammar.changed_rule.superseded"
                )
        elif superseded:
            errors.append(
                f"protocol.derivation_grammar.{fact_kind}.superseded"
            )
    templates = protocol["template_ast_catalog"]
    if (
        len(templates["training"]) != 4
        or set(templates["evaluation"]) != set(REQUIRED_EVALUATION_KINDS)
        or any(
            len(templates["evaluation"][kind]) != 4
            for kind in REQUIRED_EVALUATION_KINDS
        )
    ):
        errors.append("protocol.template_ast_catalog")
    training_operators = {
        template["operator"] for template in templates["training"]
    }
    evaluation_operators = {
        template["operator"]
        for kind in REQUIRED_EVALUATION_KINDS
        for template in templates["evaluation"][kind]
    }
    if training_operators & evaluation_operators:
        errors.append("protocol.template_operator_disjointness")
    training_ids = {template["id"] for template in templates["training"]}
    training_hashes = {
        canonical_sha256(template) for template in templates["training"]
    }
    training_surfaces = {
        _normalize_typed(template["surface"])
        for template in templates["training"]
    }
    if not all(
        len(values) == 4
        for values in (
            training_ids,
            training_operators,
            training_hashes,
            training_surfaces,
        )
    ):
        errors.append("protocol.template_ast_catalog.training_uniqueness")
    if templates["skeleton_projection"] != [
        "operator",
        "derivation",
        "ordered_typed_slots",
    ]:
        errors.append("protocol.template_ast_catalog.skeleton_projection")
    formatter = string.Formatter()
    training_skeletons: set[str] = set()
    evaluation_skeletons: set[str] = set()
    for template in templates["training"]:
        declared = [
            (slot["name"], slot["type"]) for slot in template["slots"]
        ]
        observed = {
            field_name
            for _, field_name, _, _ in formatter.parse(template["surface"])
            if field_name is not None
        }
        if (
            observed != {name for name, _ in declared}
            or not template["id"].startswith("v28r2-training-")
            or not template["operator"].startswith("training.")
        ):
            errors.append("protocol.template_ast_catalog.training")
        training_skeletons.add(
            canonical_sha256(
                {
                    "operator": template["operator"],
                    "derivation": None,
                    "ordered_typed_slots": declared,
                }
            )
        )
    for kind in REQUIRED_EVALUATION_KINDS:
        kind_templates = templates["evaluation"][kind]
        kind_ids = {template["id"] for template in kind_templates}
        kind_operators = {
            template["operator"] for template in kind_templates
        }
        kind_hashes = {
            canonical_sha256(template) for template in kind_templates
        }
        kind_surfaces = {
            _normalize_typed(template["surface"])
            for template in kind_templates
        }
        if not all(
            len(values) == 4
            for values in (
                kind_ids,
                kind_operators,
                kind_hashes,
                kind_surfaces,
            )
        ):
            errors.append(
                f"protocol.template_ast_catalog.{kind}.uniqueness"
            )
        for template in kind_templates:
            observed = {
                field_name
                for _, field_name, _, _ in formatter.parse(
                    template["surface"]
                )
                if field_name is not None
            }
            if (
                template["derivation"] != kind
                or observed != set(template["slots"])
                or not template["id"].startswith(f"v28r2-eval-{kind.replace('_', '-')}-")
                or not template["operator"].startswith("evaluation.")
            ):
                errors.append(
                    f"protocol.template_ast_catalog.evaluation.{kind}"
                )
            evaluation_skeletons.add(
                canonical_sha256(
                    {
                        "operator": template["operator"],
                        "derivation": template["derivation"],
                        "ordered_typed_slots": template["slots"],
                    }
                )
            )
    if training_skeletons & evaluation_skeletons:
        errors.append("protocol.template_ast_catalog.skeleton_overlap")
    prompt_shell = protocol["prompt_shell"]
    children = prompt_shell["ast"]["children"]
    if (
        prompt_shell["unicode"] != "NFC"
        or prompt_shell["line_separator"] != "\n"
        or prompt_shell["terminal_newline"] is not False
        or prompt_shell["allowed_slots"] != ["question", "options"]
        or prompt_shell["forbidden_slots"]
        != ["source", "support", "premise_block", "answer"]
        or prompt_shell["ast"]["operator"] != "prompt.sequence"
        or [child["operator"] for child in children]
        != ["literal", "slot", "zip_lines", "literal"]
        or children[1] != {
            "name": "question",
            "operator": "slot",
            "type": "question_text",
        }
        or children[0]
        != {
            "operator": "literal",
            "value": "Answer using exactly one label: A, B, C, or D.",
        }
        or children[2]
        != {
            "format": "{label}. {option}",
            "labels": ["A", "B", "C", "D"],
            "operator": "zip_lines",
            "slot": "options",
        }
        or children[3]
        != {
            "operator": "literal",
            "value": "Answer:",
        }
        or set(prompt_shell["allowed_slots"])
        & set(prompt_shell["forbidden_slots"])
    ):
        errors.append("protocol.prompt_shell.policy")
    scorer = protocol["scorer_contract"]
    if scorer != {
        "version": "astral.rgs_acquisition_v28r2.scorer_contract.v1",
        "method": "single_next_token_label_log_probability",
        "choice_labels": ["A", "B", "C", "D"],
        "label_surfaces": [" A", " B", " C", " D"],
        "contextual_tokenization_precondition": (
            "tokenize(prompt || label_surface) == "
            "tokenize(prompt) || [choice_token_id]"
        ),
        "ineligible_on_precondition_failure": True,
        "score": "log_softmax(final_prompt_logits)[choice_token_id]",
        "score_count": 4,
        "scores_must_be_finite_non_boolean": True,
        "observed_choice": "argmax(label_log_probability_scores)",
        "tie_break": "lowest_option_index",
        "generation_allowed": False,
        "sampling_allowed": False,
        "input_token_hash": "canonical_sha256(input_token_ids)",
        "prompt_binding": "sha256(utf8_nfc(prompt_text))",
    }:
        errors.append("protocol.scorer_contract")
    if protocol["generator_input_allowlist"] != sorted(
        protocol["generator_input_allowlist"]
    ):
        errors.append("protocol.generator_input_allowlist.sorted")
    nonreuse = protocol["nonreuse_contract"]
    if (
        nonreuse.get("retired_r1_packet_sha256") != R1_PACKET_SHA256
        or nonreuse.get("retired_r1_report_sha256") != R1_REPORT_SHA256
        or nonreuse.get("retired_r1_artifact_manifest_sha256")
        != R1_MANIFEST_SHA256
    ):
        errors.append("protocol.nonreuse_contract.r1_source_identity")
    return errors


def _validate_fingerprint_manifest(
    manifest: Any, protocol: dict[str, Any]
) -> tuple[list[str], dict[str, set[str]]]:
    errors: list[str] = []
    empty = {name: set() for name in FINGERPRINT_SET_NAMES}
    if not isinstance(manifest, dict):
        return ["r1_fingerprint.object"], empty
    if set(manifest) != {
        "version",
        "state_slice",
        "source_bundle",
        "normalization_profile",
        "fingerprint_sets",
        "model_outcomes_included",
        "paths_sorted",
        "manifest_sha256",
    }:
        errors.append("r1_fingerprint.keys")
    if manifest.get("version") != "astral.rgs_v28r1_retired_fingerprint.v1":
        errors.append("r1_fingerprint.version")
    if (
        manifest.get("state_slice")
        != "astral-rgs-v28r2-retired-r1-fingerprint"
    ):
        errors.append("r1_fingerprint.state_slice")
    source = manifest.get("source_bundle")
    source_keys = {
        "packet_sha256",
        "validation_report_sha256",
        "artifact_manifest_sha256",
        "packet_file_sha256",
        "validation_report_file_sha256",
        "artifact_manifest_file_sha256",
        "generator_sha256",
        "seed_commitment_sha256",
        "corpus_manifest_sha256",
        "future_assessment_commitment_sha256",
        "disposition",
    }
    if not _exact_keys(source, source_keys):
        errors.append("r1_fingerprint.source_bundle")
    else:
        for key, expected in {
            "packet_sha256": R1_PACKET_SHA256,
            "validation_report_sha256": R1_REPORT_SHA256,
            "artifact_manifest_sha256": R1_MANIFEST_SHA256,
            "packet_file_sha256": R1_PACKET_FILE_SHA256,
            "validation_report_file_sha256": R1_REPORT_FILE_SHA256,
            "artifact_manifest_file_sha256": R1_MANIFEST_FILE_SHA256,
            "disposition": "CorpusNotNovel",
        }.items():
            if source.get(key) != expected:
                errors.append(f"r1_fingerprint.source_bundle.{key}")
        for key in (
            "generator_sha256",
            "seed_commitment_sha256",
            "corpus_manifest_sha256",
            "future_assessment_commitment_sha256",
        ):
            if not _is_sha256(source.get(key)):
                errors.append(f"r1_fingerprint.source_bundle.{key}")
    if manifest.get("normalization_profile") != {
        "unicode": "NFC",
        "case": "lowercase",
        "generated_values": "typed_placeholders_from_semantic_ast",
        "whitespace": "collapse_ascii_whitespace",
        "structural_ngram_size": 8,
    }:
        errors.append("r1_fingerprint.normalization_profile")
    if manifest.get("model_outcomes_included") is not False:
        errors.append("r1_fingerprint.model_outcomes_included")
    if manifest.get("paths_sorted") is not True:
        errors.append("r1_fingerprint.paths_sorted")
    sets = manifest.get("fingerprint_sets")
    if not isinstance(sets, dict) or set(sets) != set(FINGERPRINT_SET_NAMES):
        errors.append("r1_fingerprint.set_census")
        return errors, empty
    parsed: dict[str, set[str]] = {}
    for name in FINGERPRINT_SET_NAMES:
        entry = sets.get(name)
        if not _exact_keys(entry, {"count", "items", "set_sha256"}):
            errors.append(f"r1_fingerprint.{name}.shape")
            parsed[name] = set()
            continue
        items = entry["items"]
        if (
            not isinstance(items, list)
            or items != sorted(items)
            or len(items) != len(set(items))
            or not all(_is_sha256(item) for item in items)
        ):
            errors.append(f"r1_fingerprint.{name}.items")
            parsed[name] = set()
            continue
        if entry["count"] != len(items):
            errors.append(f"r1_fingerprint.{name}.count")
        if entry["set_sha256"] != canonical_sha256(items):
            errors.append(f"r1_fingerprint.{name}.set_sha256")
        parsed[name] = set(items)
    if manifest.get("manifest_sha256") != canonical_sha256(
        _without(manifest, "manifest_sha256")
    ):
        errors.append("r1_fingerprint.manifest_sha256")
    expected_pin = protocol["nonreuse_contract"].get(
        "retired_r1_fingerprint_manifest_sha256"
    )
    if expected_pin == "not-built":
        errors.append("r1_fingerprint.real_manifest_not_built")
    elif expected_pin != manifest.get("manifest_sha256"):
        errors.append("r1_fingerprint.protocol_pin")
    return errors, parsed


def _validate_campaign(packet: dict[str, Any], protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    campaign = packet.get("campaign")
    if not isinstance(campaign, dict):
        return ["campaign.object"]
    if set(campaign) != CAMPAIGN_KEYS:
        errors.append("campaign.keys")
    for key in ("campaign_id", "ledger_id"):
        if not isinstance(campaign.get(key), str) or not campaign[key]:
            errors.append(f"campaign.{key}")
    for key, expected in {
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
    }.items():
        if campaign.get(key) != expected:
            errors.append(f"campaign.{key}")
    seed_hex = campaign.get("seed_hex")
    if (
        not isinstance(seed_hex, str)
        or len(seed_hex) != 64
        or any(character not in "0123456789abcdef" for character in seed_hex)
    ):
        errors.append("campaign.seed_hex")
    if not _is_sha256(campaign.get("generator_input_allowlist_sha256")):
        errors.append("campaign.generator_input_allowlist_sha256")
    elif campaign["generator_input_allowlist_sha256"] != canonical_sha256(
        protocol["generator_input_allowlist"]
    ):
        errors.append("campaign.generator_input_allowlist_binding")
    inputs = campaign.get("generator_input_keys")
    if inputs != protocol["generator_input_allowlist"]:
        errors.append("campaign.generator_input_keys")
    ordering = packet.get("ordering")
    expected_ordering = protocol.get("ordering_contract")
    if ordering != expected_ordering:
        errors.append("ordering")
    return errors


def _validate_provenance_and_locks(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    provenance = packet.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != PROVENANCE_KEYS:
        errors.append("provenance.shape")
    else:
        for key in ("source_commit", "source_tree"):
            value = provenance.get(key)
            if (
                not isinstance(value, str)
                or len(value) != 40
                or any(character not in "0123456789abcdef" for character in value)
            ):
                errors.append(f"provenance.{key}")
        if provenance.get("source_clean") is not True:
            errors.append("provenance.source_clean")
        for key in PROVENANCE_KEYS - {
            "source_commit",
            "source_tree",
            "source_clean",
            "output_root",
        }:
            if not _is_sha256(provenance.get(key)):
                errors.append(f"provenance.{key}")
        output_root = provenance.get("output_root")
        if (
            not isinstance(output_root, str)
            or not output_root.startswith("/")
            or "/../" in output_root
            or output_root.endswith("/..")
        ):
            errors.append("provenance.output_root")
    locks = packet.get("locks")
    if not isinstance(locks, dict) or set(locks) != LOCK_KEYS:
        errors.append("locks.shape")
    else:
        for key in LOCK_KEYS:
            if not _is_sha256(locks.get(key)):
                errors.append(f"locks.{key}")
    return errors


def _validate_later_gates(packet: dict[str, Any], protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("later_gates") != {
        "update_arms": None,
        "retention_recovery": None,
        "selection": None,
        "assessment": None,
    }:
        errors.append("later_gates")
    claims = packet.get("claim_boundary")
    expected_claims = {
        claim: False for claim in protocol.get("required_false_claims", [])
    }
    if claims != expected_claims:
        errors.append("claim_boundary")
    return errors


def _family_accuracy_intervals(
    family_correct: dict[str, tuple[str, list[int]]],
    critical_value: float,
) -> dict[str, Any]:
    dimensions: dict[str, list[float]] = {"overall": []}
    for fact_kind in REQUIRED_FACT_KINDS:
        dimensions[f"fact_kind:{fact_kind}"] = []
    for evaluation_kind in REQUIRED_EVALUATION_KINDS:
        dimensions[f"evaluation_kind:{evaluation_kind}"] = []
    for _, (fact_kind, counts) in sorted(family_correct.items()):
        dimensions["overall"].append(sum(counts) / 12.0)
        dimensions[f"fact_kind:{fact_kind}"].append(sum(counts) / 12.0)
        for index, evaluation_kind in enumerate(REQUIRED_EVALUATION_KINDS):
            dimensions[f"evaluation_kind:{evaluation_kind}"].append(
                counts[index] / 4.0
            )
    result: dict[str, Any] = {}
    for name, accuracies in dimensions.items():
        if not accuracies:
            continue
        lifts = [(accuracy - 0.25) / 0.75 for accuracy in accuracies]
        mean = statistics.fmean(lifts)
        standard_deviation = statistics.stdev(lifts)
        half_width = critical_value * standard_deviation / math.sqrt(len(lifts))
        result[name] = {
            "cluster_count": len(lifts),
            "mean_chance_normalized_lift": mean,
            "standard_deviation": standard_deviation,
            "lower_bound": mean - half_width,
            "upper_bound": mean + half_width,
        }
    return result


def _validate_run_shape(
    run: Any,
    arm_id: str,
    protocol: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(run, dict):
        return [f"runs.{arm_id}.object"]
    if set(run) != RUN_KEYS:
        errors.append(f"runs.{arm_id}.keys")
    if run.get("arm_id") != arm_id:
        errors.append(f"runs.{arm_id}.arm_id")
    for key in ("prep_process_id", "evaluation_process_id"):
        if not _is_sha256(run.get(key)):
            errors.append(f"runs.{arm_id}.{key}")
    for key in (
        "preparation_implementation_sha256",
        "preparation_configuration_sha256",
        "evaluator_implementation_sha256",
        "evaluator_configuration_sha256",
        "starting_state_sha256",
        "post_preparation_state_sha256",
        "restart_loaded_state_sha256",
        "runtime_inventory_sha256",
        "tokenizer_inventory_sha256",
        "scorer_configuration_sha256",
        "source_removal_manifest_sha256",
        "prep_receipt_sha256",
        "process_receipt_sha256",
        "raw_scores_sha256",
        "observations_sha256",
        "run_manifest_sha256",
    ):
        if not _is_sha256(run.get(key)):
            errors.append(f"runs.{arm_id}.{key}")
    start = run.get("starting_state_sha256")
    if (
        run.get("post_preparation_state_sha256") != start
        or run.get("restart_loaded_state_sha256") != start
    ):
        errors.append(f"runs.{arm_id}.state_parity")
    if run.get("persistence_class") != "unchanged_checkpoint":
        errors.append(f"runs.{arm_id}.persistence_class")
    if run.get("source_context_present") is not False:
        errors.append(f"runs.{arm_id}.source_context_present")
    if run.get("retrieval_enabled") is not False:
        errors.append(f"runs.{arm_id}.retrieval_enabled")
    if run.get("source_removal_verified") is not True:
        errors.append(f"runs.{arm_id}.source_removal_verified")
    if run.get("fresh_checkpoint_load") is not True:
        errors.append(f"runs.{arm_id}.fresh_checkpoint_load")
    expected_stage_order = (
        ["checkpoint_load", "evaluation"]
        if arm_id == "pre_update"
        else ["no_op_preparation", "source_removal", "checkpoint_load", "evaluation"]
    )
    if run.get("stage_order") != expected_stage_order:
        errors.append(f"runs.{arm_id}.stage_order")
    if run.get("update_budget") != protocol["baseline_contract"]["update_budget"]:
        errors.append(f"runs.{arm_id}.update_budget")
    if run.get("query_count") != 73728:
        errors.append(f"runs.{arm_id}.query_count")
    if not isinstance(run.get("score_rows"), list):
        errors.append(f"runs.{arm_id}.score_rows")
    return errors


def _validate_process_identity_distinctness(
    runs_by_arm: dict[str, dict[str, Any]]
) -> list[str]:
    process_ids = [
        runs_by_arm[arm_id].get(key)
        for arm_id in ("pre_update", "no_update")
        for key in ("prep_process_id", "evaluation_process_id")
    ]
    return (
        []
        if len(process_ids) == 4 and len(set(process_ids)) == 4
        else ["runs.process_identity_distinctness"]
    )


def _validate_cross_arm_parity(
    runs_by_arm: dict[str, dict[str, Any]],
) -> list[str]:
    pre_update = runs_by_arm["pre_update"]
    no_update = runs_by_arm["no_update"]
    errors: list[str] = []
    for key in (
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
    ):
        if pre_update.get(key) != no_update.get(key):
            errors.append(f"runs.cross_arm_parity.{key}")
    return errors


def _score_choice(scores: list[float]) -> int:
    return max(range(4), key=lambda index: (scores[index], -index))


def _validate_score_row(
    row: Any,
    query: dict[str, Any],
    prefix: str,
    scorer_configuration: dict[str, Any],
) -> tuple[list[str], int | None]:
    errors: list[str] = []
    keys = {
        "query_id",
        "prompt_sha256",
        "input_token_ids",
        "tokenized_input_sha256",
        "input_token_count",
        "choice_labels",
        "choice_token_ids",
        "label_log_probability_scores",
        "observed_choice",
        "tie_break",
    }
    if not _exact_keys(row, keys):
        return [f"{prefix}.shape"], None
    if row["query_id"] != query["query_id"]:
        errors.append(f"{prefix}.query_id")
    if row["prompt_sha256"] != query["prompt_sha256"]:
        errors.append(f"{prefix}.prompt_sha256")
    token_ids = row["input_token_ids"]
    if (
        not isinstance(token_ids, list)
        or not token_ids
        or not all(_is_int(token) and token >= 0 for token in token_ids)
    ):
        errors.append(f"{prefix}.input_token_ids")
    else:
        if row["input_token_count"] != len(token_ids):
            errors.append(f"{prefix}.input_token_count")
        if row["tokenized_input_sha256"] != canonical_sha256(token_ids):
            errors.append(f"{prefix}.tokenized_input_sha256")
    if row["choice_labels"] != scorer_configuration["choice_labels"]:
        errors.append(f"{prefix}.choice_labels")
    choice_token_ids = row["choice_token_ids"]
    if (
        not isinstance(choice_token_ids, list)
        or len(choice_token_ids) != 4
        or not all(_is_int(token) and token >= 0 for token in choice_token_ids)
        or len(set(choice_token_ids)) != 4
        or choice_token_ids != scorer_configuration["choice_token_ids"]
    ):
        errors.append(f"{prefix}.choice_token_ids")
    scores = row["label_log_probability_scores"]
    if (
        not isinstance(scores, list)
        or len(scores) != 4
        or not all(
            isinstance(score, (int, float))
            and not isinstance(score, bool)
            and math.isfinite(score)
            for score in scores
        )
    ):
        errors.append(f"{prefix}.scores")
        return errors, None
    observed_choice = _score_choice([float(score) for score in scores])
    if row["observed_choice"] != observed_choice:
        errors.append(f"{prefix}.observed_choice")
    if row["tie_break"] != scorer_configuration["tie_break"]:
        errors.append(f"{prefix}.tie_break")
    return errors, observed_choice


def _load_canonical_bundle_json(
    path: Path,
    prefix: str,
) -> tuple[list[str], dict[str, Any] | None]:
    try:
        loaded = load_json_strict(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return [f"{prefix}.json"], None
    if not isinstance(loaded, dict):
        return [f"{prefix}.object"], None
    if path.read_bytes() != canonical_json_bytes(loaded) + b"\n":
        return [f"{prefix}.canonical_bytes"], loaded
    return [], loaded


def _validate_self_hash(
    value: Any,
    key: str,
    prefix: str,
) -> list[str]:
    if not isinstance(value, dict):
        return [f"{prefix}.object"]
    return (
        []
        if value.get(key) == canonical_sha256(_without(value, key))
        else [f"{prefix}.{key}"]
    )


def _validate_bundle_artifact_bindings(
    packet: dict[str, Any],
    protocol: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    locks_value = packet.get("locks")
    provenance_value = packet.get("provenance")
    campaign_value = packet.get("campaign")
    locks = locks_value if isinstance(locks_value, dict) else {}
    provenance = (
        provenance_value if isinstance(provenance_value, dict) else {}
    )
    campaign = campaign_value if isinstance(campaign_value, dict) else {}
    for path, keys in INVENTORY_KEYS.items():
        value = artifacts.get(path)
        digest_field = INVENTORY_DIGEST_FIELDS[path]
        if (
            not _exact_keys(value, keys)
            or value.get("version") != ARTIFACT_VERSIONS[path]
            or value.get("state_slice") != PACKET_STATE_SLICE
            or not _is_sha256(value.get(digest_field))
        ):
            errors.append(f"bundle.binding.{path}.shape")
    checkpoint_inventory = artifacts.get("checkpoint-inventory.json", {})
    checkpoint_state_sha256 = (
        checkpoint_inventory.get("checkpoint_state_sha256")
        if isinstance(checkpoint_inventory, dict)
        else None
    )
    direct_bindings = {
        "power-profile.json": ("power_profile_sha256", protocol["power_profile"]),
        "template-ast-catalog.json": (
            "template_ast_catalog_sha256",
            protocol["template_ast_catalog"],
        ),
        "derivation-grammar.json": (
            "derivation_grammar_sha256",
            protocol["derivation_grammar"],
        ),
        "domain-tags.json": ("domain_tags_sha256", protocol["domain_tags"]),
        "prompt-shell.json": ("prompt_shell_sha256", protocol["prompt_shell"]),
    }
    concept_catalog = {
        "version": protocol["derivation_grammar"]["version"],
        "fact_kinds": protocol["derivation_grammar"]["fact_kinds"],
    }
    direct_bindings["concept-catalog.json"] = (
        "concept_catalog_sha256",
        concept_catalog,
    )
    for path, (lock_key, expected) in direct_bindings.items():
        actual = artifacts.get(path)
        if actual != expected:
            errors.append(f"bundle.binding.{path}")
        if locks.get(lock_key) != canonical_sha256(expected):
            errors.append(f"bundle.binding.locks.{lock_key}")
    scorer = artifacts.get("scorer-configuration.json")
    scorer_keys = {
        "version",
        "scorer_contract_sha256",
        "tokenizer_inventory_sha256",
        "choice_labels",
        "choice_token_ids",
        "contextual_tokenization_verified",
        "tie_break",
        "scorer_configuration_sha256",
    }
    if not _exact_keys(scorer, scorer_keys):
        errors.append("bundle.binding.scorer_configuration.shape")
    else:
        errors.extend(
            _validate_self_hash(
                scorer,
                "scorer_configuration_sha256",
                "bundle.binding.scorer_configuration",
            )
        )
        if (
            scorer["scorer_contract_sha256"]
            != canonical_sha256(protocol["scorer_contract"])
            or scorer["choice_labels"] != protocol["choice_labels"]
            or scorer["tie_break"] != protocol["scorer_contract"]["tie_break"]
            or scorer["contextual_tokenization_verified"] is not True
            or not isinstance(scorer["choice_token_ids"], list)
            or len(scorer["choice_token_ids"]) != 4
            or len(set(scorer["choice_token_ids"])) != 4
            or not all(
                _is_int(token) and token >= 0
                for token in scorer["choice_token_ids"]
            )
        ):
            errors.append("bundle.binding.scorer_configuration.contract")
        if (
            scorer["tokenizer_inventory_sha256"]
            != provenance.get("tokenizer_inventory_sha256")
        ):
            errors.append("bundle.binding.scorer_configuration.tokenizer")
        if (
            locks.get("scorer_contract_sha256")
            != scorer["scorer_contract_sha256"]
            or locks.get("scorer_configuration_sha256")
            != scorer["scorer_configuration_sha256"]
        ):
            errors.append("bundle.binding.scorer_configuration.locks")
    inventory_bindings = {
        "checkpoint-inventory.json": "checkpoint_inventory_sha256",
        "tokenizer-inventory.json": "tokenizer_inventory_sha256",
        "runtime-inventory.json": "runtime_sha256",
        "generator-inventory.json": "generator_inventory_sha256",
        "validator-inventory.json": "validator_inventory_sha256",
    }
    for path, provenance_key in inventory_bindings.items():
        value = artifacts.get(path)
        if (
            not isinstance(value, dict)
            or canonical_sha256(value) != provenance.get(provenance_key)
        ):
            errors.append(f"bundle.binding.{path}")
    self_hash_bindings = {
        "pre-generation-receipt.json": (
            "receipt_sha256",
            provenance.get("pre_generation_receipt_sha256"),
        ),
        "one-shot-execution-claim.json": (
            "one_shot_execution_claim_sha256",
            locks.get("one_shot_execution_claim_sha256"),
        ),
        "seed-commitment.json": (
            "seed_commitment_sha256",
            locks.get("seed_commitment_sha256"),
        ),
        "configuration-lock.json": (
            "configuration_lock_sha256",
            locks.get("configuration_lock_sha256"),
        ),
        "future-assessment-identity-commitment.json": (
            "future_assessment_identity_commitment_sha256",
            locks.get("future_assessment_identity_commitment_sha256"),
        ),
    }
    for path, (hash_key, expected) in self_hash_bindings.items():
        value = artifacts.get(path)
        errors.extend(_validate_self_hash(value, hash_key, f"bundle.binding.{path}"))
        if not isinstance(value, dict) or value.get(hash_key) != expected:
            errors.append(f"bundle.binding.{path}.packet")
    pre_generation = artifacts.get("pre-generation-receipt.json", {})
    if (
        not _exact_keys(pre_generation, PRE_GENERATION_KEYS)
        or pre_generation.get("version")
        != ARTIFACT_VERSIONS["pre-generation-receipt.json"]
        or pre_generation.get("state_slice") != PACKET_STATE_SLICE
    ):
        errors.append("bundle.binding.pre_generation.shape")
    expected_pre_generation = {
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "campaign_id": campaign.get("campaign_id"),
        "ledger_id": campaign.get("ledger_id"),
        "source_commit": provenance.get("source_commit"),
        "source_tree": provenance.get("source_tree"),
        "output_root": provenance.get("output_root"),
        "checkpoint_inventory_sha256": provenance.get(
            "checkpoint_inventory_sha256"
        ),
        "tokenizer_inventory_sha256": provenance.get(
            "tokenizer_inventory_sha256"
        ),
        "runtime_sha256": provenance.get("runtime_sha256"),
        "generator_inventory_sha256": provenance.get(
            "generator_inventory_sha256"
        ),
        "validator_inventory_sha256": provenance.get(
            "validator_inventory_sha256"
        ),
        "power_profile_sha256": locks.get("power_profile_sha256"),
        "concept_catalog_sha256": locks.get("concept_catalog_sha256"),
        "template_ast_catalog_sha256": locks.get(
            "template_ast_catalog_sha256"
        ),
        "derivation_grammar_sha256": locks.get(
            "derivation_grammar_sha256"
        ),
        "domain_tags_sha256": locks.get("domain_tags_sha256"),
        "scorer_contract_sha256": locks.get("scorer_contract_sha256"),
        "prompt_shell_sha256": locks.get("prompt_shell_sha256"),
        "future_assessment_identity_commitment_sha256": locks.get(
            "future_assessment_identity_commitment_sha256"
        ),
        "generator_input_allowlist_sha256": campaign.get(
            "generator_input_allowlist_sha256"
        ),
        "inputs_locked_before_ledger_claim": True,
        "seed_material_absent": True,
    }
    for key, expected in expected_pre_generation.items():
        if pre_generation.get(key) != expected:
            errors.append(f"bundle.binding.pre_generation.{key}")
    seed_material = artifacts.get("seed-material.json")
    if (
        not _exact_keys(seed_material, {"version", "state_slice", "seed_hex"})
        or seed_material.get("version")
        != ARTIFACT_VERSIONS["seed-material.json"]
        or seed_material.get("state_slice") != PACKET_STATE_SLICE
        or seed_material.get("seed_hex") != campaign.get("seed_hex")
    ):
        errors.append("bundle.binding.seed_material")
    seed_commitment = artifacts.get("seed-commitment.json", {})
    seed_hex = campaign.get("seed_hex")
    seed_digest = (
        sha256_bytes(bytes.fromhex(seed_hex))
        if isinstance(seed_hex, str)
        and len(seed_hex) == 64
        and all(character in "0123456789abcdef" for character in seed_hex)
        else None
    )
    if (
        not _exact_keys(seed_commitment, SEED_COMMITMENT_KEYS)
        or seed_commitment.get("version")
        != ARTIFACT_VERSIONS["seed-commitment.json"]
        or seed_commitment.get("state_slice") != PACKET_STATE_SLICE
        or seed_commitment.get("seed_sha256") != seed_digest
        or seed_commitment.get("campaign_id") != campaign.get("campaign_id")
        or seed_commitment.get("ledger_id") != campaign.get("ledger_id")
        or seed_commitment.get("checkpoint_inventory_sha256")
        != provenance.get("checkpoint_inventory_sha256")
        or seed_commitment.get("pre_generation_receipt_sha256")
        != provenance.get("pre_generation_receipt_sha256")
        or seed_commitment.get("one_shot_execution_claim_sha256")
        != locks.get("one_shot_execution_claim_sha256")
    ):
        errors.append("bundle.binding.seed_commitment")
    one_shot = artifacts.get("one-shot-execution-claim.json", {})
    if (
        not _exact_keys(one_shot, ONE_SHOT_KEYS)
        or one_shot.get("version")
        != ARTIFACT_VERSIONS["one-shot-execution-claim.json"]
        or one_shot.get("state_slice") != PACKET_STATE_SLICE
    ):
        errors.append("bundle.binding.one_shot.shape")
    for key, expected in {
        "campaign_id": campaign.get("campaign_id"),
        "ledger_id": campaign.get("ledger_id"),
        "output_root": provenance.get("output_root"),
        "source_commit": provenance.get("source_commit"),
        "source_tree": provenance.get("source_tree"),
        "ledger_exclusive_create": True,
        "ledger_file_synced": True,
        "ledger_parent_synced": True,
        "seed_draw_count": 1,
        "candidate_corpus_count": 1,
        "permanently_retired_after_failure": True,
        "ledger_claim_order": protocol["ordering_contract"][
            "ledger_claim_order"
        ],
        "seed_draw_order": protocol["ordering_contract"]["seed_draw_order"],
    }.items():
        if one_shot.get(key) != expected:
            errors.append(f"bundle.binding.one_shot.{key}")
    expected_one_shot_locks = {
        key: value
        for key, value in locks.items()
        if key
        not in {
            "configuration_lock_sha256",
            "one_shot_execution_claim_sha256",
            "seed_commitment_sha256",
        }
    }
    if one_shot.get("locked_input_sha256s") != expected_one_shot_locks:
        errors.append("bundle.binding.one_shot.locked_input_sha256s")
    configuration = artifacts.get("configuration-lock.json", {})
    expected_configuration_keys = {
        "version",
        "state_slice",
        "protocol_sha256",
        "campaign_id",
        "output_root",
        "checkpoint_inventory_sha256",
        "tokenizer_inventory_sha256",
        "runtime_sha256",
        "generator_inventory_sha256",
        "validator_inventory_sha256",
        "retired_r1_fingerprint_manifest_sha256",
        "corpus_sha256",
        "configuration_lock_sha256",
        *LOCK_KEYS.difference({"configuration_lock_sha256"}),
    }
    if (
        not _exact_keys(configuration, expected_configuration_keys)
        or configuration.get("version")
        != ARTIFACT_VERSIONS["configuration-lock.json"]
        or configuration.get("state_slice") != PACKET_STATE_SLICE
    ):
        errors.append("bundle.binding.configuration_lock.shape")
    expected_configuration_bindings = {
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "campaign_id": campaign.get("campaign_id"),
        "output_root": provenance.get("output_root"),
        "checkpoint_inventory_sha256": provenance.get(
            "checkpoint_inventory_sha256"
        ),
        "tokenizer_inventory_sha256": provenance.get(
            "tokenizer_inventory_sha256"
        ),
        "runtime_sha256": provenance.get("runtime_sha256"),
        "generator_inventory_sha256": provenance.get(
            "generator_inventory_sha256"
        ),
        "validator_inventory_sha256": provenance.get(
            "validator_inventory_sha256"
        ),
        "seed_commitment_sha256": locks.get("seed_commitment_sha256"),
        "scorer_configuration_sha256": locks.get(
            "scorer_configuration_sha256"
        ),
        "retired_r1_fingerprint_manifest_sha256": protocol[
            "nonreuse_contract"
        ]["retired_r1_fingerprint_manifest_sha256"],
    }
    for key, expected in expected_configuration_bindings.items():
        if configuration.get(key) != expected:
            errors.append(f"bundle.binding.configuration_lock.{key}")
    for key, expected in locks.items():
        if key == "configuration_lock_sha256":
            continue
        if configuration.get(key) != expected:
            errors.append(
                f"bundle.binding.configuration_lock.{key}"
            )
    packet_corpus = packet.get("corpus")
    expected_corpus_sha256 = (
        packet_corpus.get("corpus_sha256")
        if isinstance(packet_corpus, dict)
        else None
    )
    if configuration.get("corpus_sha256") != expected_corpus_sha256:
        errors.append("bundle.binding.configuration_lock.corpus_sha256")
    future = artifacts.get(
        "future-assessment-identity-commitment.json", {}
    )
    future_ids = future.get("family_ids")
    if (
        not _exact_keys(future, FUTURE_COMMITMENT_KEYS)
        or future.get("version")
        != ARTIFACT_VERSIONS[
            "future-assessment-identity-commitment.json"
        ]
        or future.get("state_slice") != PACKET_STATE_SLICE
        or not isinstance(future_ids, list)
        or not future_ids
        or not all(isinstance(value, str) and value for value in future_ids)
        or len(future_ids) != len(set(future_ids))
    ):
        errors.append("bundle.binding.future_assessment.shape")
    for key, expected in {
        "campaign_id": campaign.get("campaign_id"),
        "ledger_id": campaign.get("ledger_id"),
        "assessment_content_generated": False,
        "assessment_opened": False,
    }.items():
        if future.get(key) != expected:
            errors.append(f"bundle.binding.future_assessment.{key}")
    corpus_value = packet.get("corpus")
    corpus = corpus_value if isinstance(corpus_value, dict) else {}
    if artifacts.get("corpus/raw-corpus.json") != corpus:
        errors.append("bundle.binding.raw_corpus")
    protocol_corpus = artifacts.get("corpus/protocol-corpus.json")
    if (
        not _exact_keys(
            protocol_corpus,
            {"version", "state_slice", "corpus_sha256", "family_count"},
        )
        or protocol_corpus.get("corpus_sha256") != corpus.get("corpus_sha256")
        or protocol_corpus.get("family_count") != corpus.get("family_count")
    ):
        errors.append("bundle.binding.protocol_corpus")
    baseline_runs = packet.get("baseline_runs")
    for run in baseline_runs if isinstance(baseline_runs, list) else []:
        if not isinstance(run, dict):
            continue
        arm_id = run.get("arm_id")
        base = f"runs/{arm_id}"
        raw_scores = artifacts.get(f"{base}/evaluation/raw-scores.json")
        observations = artifacts.get(f"{base}/evaluation/observations.json")
        if (
            not _exact_keys(raw_scores, {"score_rows"})
            or raw_scores != {"score_rows": run.get("score_rows")}
        ):
            errors.append(f"bundle.binding.{arm_id}.raw_scores")
        if (
            not _exact_keys(observations, {"observations"})
            or canonical_sha256(observations.get("observations"))
            != run.get("observations_sha256")
        ):
            errors.append(f"bundle.binding.{arm_id}.observations")
        for suffix, hash_key in (
            ("prep-receipt.json", "prep_receipt_sha256"),
            ("source-removal-manifest.json", "source_removal_manifest_sha256"),
            ("evaluation/process-receipt.json", "process_receipt_sha256"),
            ("evaluation/run-manifest.json", "run_manifest_sha256"),
        ):
            value = artifacts.get(f"{base}/{suffix}")
            if not isinstance(value, dict):
                errors.append(f"bundle.binding.{arm_id}.{suffix}")
                continue
            if hash_key in run:
                expected = run[hash_key]
            elif hash_key == "run_manifest_sha256":
                expected = run.get(hash_key)
            elif hash_key == "source_removal_manifest_sha256":
                expected = run.get(hash_key)
            else:
                expected = value.get(hash_key)
            errors.extend(
                _validate_self_hash(
                    value,
                    hash_key,
                    f"bundle.binding.{arm_id}.{suffix}",
                )
            )
            if value.get(hash_key) != expected:
                errors.append(f"bundle.binding.{arm_id}.{suffix}.packet")
        prep = artifacts.get(f"{base}/prep-receipt.json", {})
        source_removal = artifacts.get(
            f"{base}/source-removal-manifest.json", {}
        )
        process = artifacts.get(f"{base}/evaluation/process-receipt.json", {})
        run_manifest = artifacts.get(f"{base}/evaluation/run-manifest.json", {})
        for artifact, name, keys, version_key in (
            (
                prep,
                "prep",
                PREP_RECEIPT_KEYS,
                "prep-receipt.json",
            ),
            (
                source_removal,
                "source_removal",
                SOURCE_REMOVAL_KEYS,
                "source-removal-manifest.json",
            ),
            (
                process,
                "process",
                PROCESS_RECEIPT_KEYS,
                "process-receipt.json",
            ),
            (
                run_manifest,
                "run_manifest",
                RUN_MANIFEST_KEYS,
                "run-manifest.json",
            ),
        ):
            if (
                not _exact_keys(artifact, keys)
                or artifact.get("version") != ARTIFACT_VERSIONS[version_key]
                or artifact.get("state_slice") != PACKET_STATE_SLICE
            ):
                errors.append(f"bundle.binding.{arm_id}.{name}.shape")
        for key, expected in {
            "arm_id": arm_id,
            "source_context_present": False,
            "retrieval_enabled": False,
            "source_context_removed": True,
            "retrieval_material_removed": True,
        }.items():
            if source_removal.get(key) != expected:
                errors.append(
                    f"bundle.binding.{arm_id}.source_removal.{key}"
                )
        for artifact, name, bindings in (
            (
                prep,
                "prep",
                {
                    "arm_id": arm_id,
                    "process_id": run.get("prep_process_id"),
                    "implementation_sha256": run.get(
                        "preparation_implementation_sha256"
                    ),
                    "configuration_sha256": run.get(
                        "preparation_configuration_sha256"
                    ),
                    "starting_state_sha256": run.get(
                        "starting_state_sha256"
                    ),
                    "post_preparation_state_sha256": run.get(
                        "post_preparation_state_sha256"
                    ),
                    "update_budget": run.get("update_budget"),
                },
            ),
            (
                process,
                "process",
                {
                    "arm_id": arm_id,
                    "process_id": run.get("evaluation_process_id"),
                    "implementation_sha256": run.get(
                        "evaluator_implementation_sha256"
                    ),
                    "configuration_sha256": run.get(
                        "evaluator_configuration_sha256"
                    ),
                    "restart_loaded_state_sha256": run.get(
                        "restart_loaded_state_sha256"
                    ),
                    "runtime_inventory_sha256": run.get(
                        "runtime_inventory_sha256"
                    ),
                    "tokenizer_inventory_sha256": run.get(
                        "tokenizer_inventory_sha256"
                    ),
                    "scorer_configuration_sha256": run.get(
                        "scorer_configuration_sha256"
                    ),
                    "source_removal_manifest_sha256": run.get(
                        "source_removal_manifest_sha256"
                    ),
                    "source_context_present": False,
                    "retrieval_enabled": False,
                },
            ),
            (
                run_manifest,
                "run_manifest",
                {
                    "arm_id": arm_id,
                    "run_id": run.get("run_id"),
                    "runtime_inventory_sha256": run.get(
                        "runtime_inventory_sha256"
                    ),
                    "tokenizer_inventory_sha256": run.get(
                        "tokenizer_inventory_sha256"
                    ),
                    "scorer_configuration_sha256": run.get(
                        "scorer_configuration_sha256"
                    ),
                    "raw_scores_sha256": run.get("raw_scores_sha256"),
                    "observations_sha256": run.get("observations_sha256"),
                    "prep_receipt_sha256": run.get(
                        "prep_receipt_sha256"
                    ),
                    "process_receipt_sha256": run.get(
                        "process_receipt_sha256"
                    ),
                    "source_removal_manifest_sha256": run.get(
                        "source_removal_manifest_sha256"
                    ),
                    "starting_state_sha256": run.get(
                        "starting_state_sha256"
                    ),
                    "restart_loaded_state_sha256": run.get(
                        "restart_loaded_state_sha256"
                    ),
                    "stage_order": run.get("stage_order"),
                    "query_count": run.get("query_count"),
                },
            ),
        ):
            for key, expected in bindings.items():
                if artifact.get(key) != expected:
                    errors.append(
                        f"bundle.binding.{arm_id}.{name}.{key}"
                    )
        for key, expected in {
            "runtime_inventory_sha256": provenance.get("runtime_sha256"),
            "tokenizer_inventory_sha256": provenance.get(
                "tokenizer_inventory_sha256"
            ),
            "scorer_configuration_sha256": locks.get(
                "scorer_configuration_sha256"
            ),
            "starting_state_sha256": checkpoint_state_sha256,
            "post_preparation_state_sha256": checkpoint_state_sha256,
            "restart_loaded_state_sha256": checkpoint_state_sha256,
        }.items():
            if run.get(key) != expected:
                errors.append(f"bundle.binding.{arm_id}.sealed.{key}")
    return errors


def _validate_bundle_root(
    bundle_root: Path,
    packet: dict[str, Any],
    protocol: dict[str, Any],
    packet_path: Path | None,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    errors: list[str] = []
    if (
        not bundle_root.is_absolute()
        or not bundle_root.is_dir()
        or bundle_root.is_symlink()
        or any(parent.is_symlink() for parent in bundle_root.parents)
    ):
        return ["bundle.root"], {}
    if packet_path is not None:
        expected_packet_path = bundle_root / "acquisition-packet.json"
        if (
            packet_path != expected_packet_path
            or packet_path.is_symlink()
            or not packet_path.is_file()
        ):
            return ["bundle.packet_path_binding"], {}
    manifest_path = bundle_root / "artifact-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return ["bundle.artifact_manifest"], {}
    manifest_errors, manifest = _load_canonical_bundle_json(
        manifest_path, "bundle.artifact_manifest"
    )
    errors.extend(manifest_errors)
    if manifest is None:
        return errors, {}
    if not _exact_keys(
        manifest, {"version", "state_slice", "entries", "manifest_sha256"}
    ):
        errors.append("bundle.artifact_manifest_shape")
    if manifest.get("manifest_sha256") != canonical_sha256(
        _without(manifest, "manifest_sha256")
    ):
        errors.append("bundle.artifact_manifest_self_hash")
    if packet.get("artifact_manifest_sha256") != manifest.get("manifest_sha256"):
        errors.append("bundle.artifact_manifest_packet_binding")
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        return [*errors, "bundle.entries"], {}
    declared: set[str] = set()
    declared_order: list[str] = []
    artifacts: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        if not _exact_keys(entry, {"path", "bytes", "sha256"}):
            errors.append(f"bundle.entries.{index}.shape")
            continue
        path_text = entry["path"]
        if (
            not isinstance(path_text, str)
            or path_text.startswith("/")
            or "\\" in path_text
            or any(part in ("", ".", "..") for part in path_text.split("/"))
            or path_text == "artifact-manifest.json"
        ):
            errors.append(f"bundle.entries.{index}.path")
            continue
        path = bundle_root / path_text
        if not path.is_file() or path.is_symlink():
            errors.append(f"bundle.entries.{index}.file")
            continue
        declared.add(path_text)
        declared_order.append(path_text)
        if (
            isinstance(entry["bytes"], bool)
            or not isinstance(entry["bytes"], int)
            or entry["bytes"] < 0
        ):
            errors.append(f"bundle.entries.{index}.bytes")
        if entry["bytes"] != path.stat().st_size:
            errors.append(f"bundle.entries.{index}.bytes")
        if entry["sha256"] != sha256_file(path):
            errors.append(f"bundle.entries.{index}.sha256")
        json_errors, loaded = _load_canonical_bundle_json(
            path, f"bundle.entries.{index}"
        )
        errors.extend(json_errors)
        if loaded is not None:
            artifacts[path_text] = loaded
    if declared_order != sorted(declared_order):
        errors.append("bundle.entry_order")
    if len(declared_order) != len(declared):
        errors.append("bundle.duplicate_path")
    observed: set[str] = set()
    observed_directories: set[str] = set()
    for root, directories, files in os.walk(bundle_root, followlinks=False):
        root_path = Path(root)
        for directory in directories:
            directory_path = root_path / directory
            if directory_path.is_symlink():
                errors.append("bundle.symlink")
            else:
                observed_directories.add(
                    directory_path.relative_to(bundle_root).as_posix()
                )
        for filename in files:
            path = root_path / filename
            relative = path.relative_to(bundle_root).as_posix()
            observed.add(relative)
    if observed != BUNDLE_ALL_PATHS:
        errors.append("bundle.file_census")
    expected_directories = {
        parent.as_posix()
        for path_text in BUNDLE_ALL_PATHS
        for parent in Path(path_text).parents
        if parent.as_posix() != "."
    }
    if observed_directories != expected_directories:
        errors.append("bundle.directory_census")
    if declared != BUNDLE_DATA_PATHS:
        errors.append("bundle.required_paths")
    packet_file = bundle_root / "acquisition-packet.json"
    if packet_file.is_symlink():
        errors.append("bundle.packet_symlink")
    packet_errors, packet_from_bundle = _load_canonical_bundle_json(
        packet_file, "bundle.packet"
    )
    errors.extend(packet_errors)
    if packet_from_bundle != packet:
        errors.append("bundle.packet_content_binding")
    errors.extend(_validate_bundle_artifact_bindings(packet, protocol, artifacts))
    return errors, artifacts


def _validate_future_assessment_nonreuse(
    future: Any,
    retired_sets: dict[str, set[str]],
) -> list[str]:
    if not isinstance(future, dict):
        return ["bundle.binding.future_assessment.object"]
    family_ids = future.get("family_ids")
    if not isinstance(family_ids, list):
        return ["bundle.binding.future_assessment.family_ids"]
    return (
        ["bundle.binding.future_assessment.r1_reuse"]
        if any(
            isinstance(family_id, str)
            and retired_fingerprint(
                "future_assessment_family_ids", family_id
            )
            in retired_sets["future_assessment_family_ids"]
            for family_id in family_ids
        )
        else []
    )


def validate_bundle_root(
    bundle_root: Path,
    packet: dict[str, Any],
    protocol: dict[str, Any],
    packet_path: Path | None = None,
) -> list[str]:
    return _validate_bundle_root(
        bundle_root, packet, protocol, packet_path
    )[0]


def validate_packet(
    packet: Any,
    protocol: Any,
    r1_fingerprint: Any,
    bundle_root: Path | None = None,
    packet_path: Path | None = None,
) -> dict[str, Any]:
    protocol_errors = _validate_protocol(protocol)
    if protocol_errors:
        return _report("Invalid", protocol_errors)
    if packet is None:
        return _report("NotRun", [], ["acquisition.packet_not_supplied"])
    if not isinstance(packet, dict):
        return _report("Invalid", ["packet.object"])
    errors: list[str] = []
    if set(packet) != PACKET_KEYS:
        errors.append("packet.keys")
    if packet.get("version") != PACKET_VERSION:
        errors.append("packet.version")
    if packet.get("state_slice") != PACKET_STATE_SLICE:
        errors.append("packet.state_slice")
    if packet.get("protocol_sha256") != EXPECTED_PROTOCOL_SHA256:
        errors.append("packet.protocol_sha256")
    if packet.get("packet_sha256") != canonical_sha256(
        _without(packet, "packet_sha256")
    ):
        errors.append("packet.packet_sha256")
    errors.extend(_validate_campaign(packet, protocol))
    errors.extend(_validate_provenance_and_locks(packet))
    errors.extend(_validate_later_gates(packet, protocol))
    fingerprint_errors, retired_sets = _validate_fingerprint_manifest(
        r1_fingerprint, protocol
    )
    errors.extend(fingerprint_errors)
    corpus = packet.get("corpus")
    baseline_runs = packet.get("baseline_runs")
    if not isinstance(corpus, dict):
        errors.append("corpus.object")
    if not isinstance(baseline_runs, list):
        errors.append("runs.census")
    if not isinstance(corpus, dict) or not isinstance(baseline_runs, list):
        return _report("Invalid", sorted(set(errors)))
    bundle_artifacts: dict[str, dict[str, Any]] = {}
    if bundle_root is not None:
        bundle_errors, bundle_artifacts = _validate_bundle_root(
            bundle_root,
            packet,
            protocol,
            packet_path,
        )
        errors.extend(bundle_errors)
        errors.extend(
            _validate_future_assessment_nonreuse(
                bundle_artifacts.get(
                    "future-assessment-identity-commitment.json"
                ),
                retired_sets,
            )
        )
    if set(corpus) != CORPUS_KEYS:
        errors.append("corpus.keys")
    for key, expected in {
        "family_count": 6144,
        "queries_per_family": 12,
        "query_count": 73728,
    }.items():
        if corpus.get(key) != expected:
            errors.append(f"corpus.{key}")
    families = corpus.get("families")
    if not isinstance(families, list) or len(families) != 6144:
        errors.append("corpus.family_census")
        return _report("Invalid", sorted(set(errors)))
    campaign_value = packet.get("campaign")
    campaign = campaign_value if isinstance(campaign_value, dict) else {}
    locks_value = packet.get("locks")
    locks = locks_value if isinstance(locks_value, dict) else {}
    seed_hex = campaign.get("seed_hex")
    for name, values in {
        "seed_commitments": {
            locks.get("seed_commitment_sha256"),
            (
                sha256_bytes(bytes.fromhex(seed_hex))
                if isinstance(seed_hex, str)
                and len(seed_hex) == 64
                and all(character in "0123456789abcdef" for character in seed_hex)
                else ""
            ),
        },
        "campaign_ids": {
            campaign.get("campaign_id"),
            packet.get("provenance", {}).get("output_root")
            if isinstance(packet.get("provenance"), dict)
            else None,
            packet.get("provenance", {}).get("source_commit")
            if isinstance(packet.get("provenance"), dict)
            else None,
        },
        "ledger_ids": {campaign.get("ledger_id")},
        "future_assessment_commitments": {
            locks.get(
                "future_assessment_identity_commitment_sha256"
            )
        },
    }.items():
        for value in values:
            if (
                isinstance(value, str)
                and retired_fingerprint(name, value) in retired_sets[name]
            ):
                errors.append(f"campaign.r1_reuse.{name}")
    expected_queries: list[dict[str, Any]] = []
    family_fact: dict[str, str] = {}
    nonreuse_seen = {name: set() for name in FINGERPRINT_SET_NAMES}
    for fact_index, fact_kind in enumerate(REQUIRED_FACT_KINDS):
        for family_ordinal in range(1536):
            index = fact_index * 1536 + family_ordinal
            try:
                expected = reconstruct_family(
                    seed_hex, fact_kind, family_ordinal, protocol
                )
            except (KeyError, TypeError, ValueError) as error:
                errors.append(f"corpus.reconstruction.{type(error).__name__}")
                return _report("Invalid", sorted(set(errors)))
            if families[index] != expected:
                errors.append(f"corpus.family.{index}")
                if len(errors) > 100:
                    return _report("Invalid", sorted(set(errors)))
            errors.extend(
                f"corpus.family.{index}.{error}"
                for error in _validate_family_semantics(
                    expected, protocol
                )
            )
            expected_queries.extend(expected["queries"])
            family_fact[expected["family_id"]] = fact_kind
            for name, values in _family_nonreuse_values(expected).items():
                for value in values:
                    fingerprint = retired_fingerprint(name, value)
                    if fingerprint in retired_sets[name]:
                        errors.append(f"corpus.r1_reuse.{name}")
                    nonreuse_seen[name].add(value)
    if corpus.get("corpus_sha256") != canonical_sha256(families):
        errors.append("corpus.corpus_sha256")
    runs = packet.get("baseline_runs")
    if not isinstance(runs, list) or len(runs) != 2:
        errors.append("runs.census")
        return _report("Invalid", sorted(set(errors)))
    by_arm = {
        run.get("arm_id"): run for run in runs if isinstance(run, dict)
    }
    if set(by_arm) != {"pre_update", "no_update"} or len(by_arm) != 2:
        errors.append("runs.arm_census")
        return _report("Invalid", sorted(set(errors)))
    for arm_id in ("pre_update", "no_update"):
        errors.extend(_validate_run_shape(by_arm[arm_id], arm_id, protocol))
    errors.extend(_validate_process_identity_distinctness(by_arm))
    errors.extend(_validate_cross_arm_parity(by_arm))
    scorer_configuration = bundle_artifacts.get("scorer-configuration.json")
    bundle_missing = scorer_configuration is None
    if scorer_configuration is None:
        first_rows = by_arm["pre_update"].get("score_rows")
        first_row = (
            first_rows[0]
            if isinstance(first_rows, list) and first_rows
            else {}
        )
        scorer_configuration = {
            "choice_labels": protocol["choice_labels"],
            "choice_token_ids": first_row.get("choice_token_ids", []),
            "tie_break": protocol["scorer_contract"]["tie_break"],
        }
    family_counts_by_arm: dict[str, dict[str, tuple[str, list[int]]]] = {}
    previous_rows: list[dict[str, Any]] | None = None
    for arm_id in ("pre_update", "no_update"):
        run = by_arm[arm_id]
        rows = run.get("score_rows")
        if not isinstance(rows, list) or len(rows) != 73728:
            errors.append(f"runs.{arm_id}.score_row_census")
            continue
        if run.get("raw_scores_sha256") != canonical_sha256(rows):
            errors.append(f"runs.{arm_id}.raw_scores_sha256")
        counts: dict[str, tuple[str, list[int]]] = {
            family_id: (fact_kind, [0, 0, 0])
            for family_id, fact_kind in family_fact.items()
        }
        observations: list[dict[str, Any]] = []
        for index, (row, query) in enumerate(zip(rows, expected_queries)):
            row_errors, observed_choice = _validate_score_row(
                row,
                query,
                f"runs.{arm_id}.score_rows.{index}",
                scorer_configuration,
            )
            errors.extend(row_errors)
            if observed_choice is None:
                continue
            observations.append(
                {
                    "query_id": query["query_id"],
                    "expected_choice": query["expected_choice"],
                    "observed_choice": observed_choice,
                }
            )
            if observed_choice == query["expected_choice"]:
                fact_kind, values = counts[query["family_id"]]
                evaluation_index = REQUIRED_EVALUATION_KINDS.index(
                    query["evaluation_kind"]
                )
                values[evaluation_index] += 1
                counts[query["family_id"]] = (fact_kind, values)
            if len(errors) > 100:
                return _report("Invalid", sorted(set(errors)))
        if run.get("observations_sha256") != canonical_sha256(observations):
            errors.append(f"runs.{arm_id}.observations_sha256")
        if previous_rows is not None and rows != previous_rows:
            errors.append("runs.cross_arm_row_parity")
        previous_rows = rows
        family_counts_by_arm[arm_id] = counts
    if errors:
        return _report("Invalid", sorted(set(errors)))
    critical = protocol["power_profile"]["minimum_student_t_critical_value"]
    interval_reports = {
        arm_id: _family_accuracy_intervals(counts, critical)
        for arm_id, counts in family_counts_by_arm.items()
    }
    margin = protocol["power_profile"]["equivalence_margin"]
    passed = all(
        interval["lower_bound"] >= -margin
        and interval["upper_bound"] <= margin
        and abs(interval["mean_chance_normalized_lift"]) <= margin
        for dimensions in interval_reports.values()
        for interval in dimensions.values()
    )
    return _baseline_disposition(passed, bundle_missing, interval_reports)


def _baseline_disposition(
    passed: bool,
    bundle_missing: bool,
    interval_reports: dict[str, Any],
) -> dict[str, Any]:
    if bundle_missing:
        return _report(
            "NotRun",
            [],
            ["acquisition.canonical_bundle_not_supplied"],
            interval_reports,
        )
    if not passed:
        return _report(
            "CorpusNotNovel",
            [],
            [
                "acquisition.v28r2_permanently_retired_corpus_not_novel"
            ],
            interval_reports,
        )
    return _report(
        "NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun",
        [],
        ["acquisition.update_arm_authorization_required"],
        interval_reports,
    )


def _report(
    status: str,
    errors: list[str],
    open_gates: list[str] | None = None,
    intervals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "version": "astral.rgs_acquisition_v28r2.validation_report.v1",
        "state_slice": "astral-rgs-v28r2-acquisition-qualification-validator",
        "status": status,
        "errors": errors,
        "open_gates": open_gates or [],
        "baseline_equivalence_intervals": intervals or {},
        "gate_state": {
            "acquisition": (
                "NoveltyCandidateUnverified"
                if status == "NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun"
                else (
                    "StoppedBeforeUpdates"
                    if status == "CorpusNotNovel"
                    else "NotRunOrInvalid"
                )
            ),
            "retention_recovery": "NotAuthorizedAcquisitionAbsent",
            "selection": "NotAuthorizedRetentionRecoveryAbsent",
            "assessment": "SealedNotAuthorized",
        },
        "claim_boundary": {
            "local_acquisition_validator_v28r2": True,
            "model_backed_acquisition": False,
            "retention_recovery_qualified": False,
            "astral_selection_authorized": False,
            "continual_learning_solved": False,
            "continual_learning_breakthrough": False,
            "autonomous_self_improvement": False,
            "introspection": False,
            "self_modeling": False,
            "stage_0c": False,
            "stage_1": False,
            "independently_replicated": False,
            "benchmark_dominance": False,
            "production_readiness": False,
        },
    }
