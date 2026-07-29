from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
import statistics
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
PROTOCOL_BYTES = (HERE / "protocol.json").read_bytes()
PROTOCOL = json.loads(PROTOCOL_BYTES)
LABELS = tuple(PROTOCOL["choice_labels"])
FACT_KINDS = tuple(PROTOCOL["required_fact_kinds"])
EVALUATION_KINDS = tuple(PROTOCOL["required_evaluation_kinds"])
PERMUTATIONS = tuple(itertools.permutations(range(4)))
ATOM = re.compile(r"\b(?:[a-z]{2,8}-)?[a-z]{4,}-[0-9a-f]{5,}\b")
HEX = re.compile(r"\b[0-9a-f]{16,}\b")
SPACE = re.compile(r"\s+")

FACT_TERMS = {
    "nonce_fact": ("capsule", "pulse code"),
    "entity_relation": ("junction", "linked node"),
    "changed_rule": ("ordinance", "current outcome"),
    "opaque_mapping": ("cipher mark", "mapped token"),
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode())


def content_hash(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def without_hash(value: dict[str, Any], key: str) -> dict[str, Any]:
    return {name: item for name, item in value.items() if name != key}


def tag_id(tag: str, *values: Any, length: int = 24) -> str:
    digest = hashlib.sha256(canonical_bytes([tag, *values])).hexdigest()[:length]
    return f"{tag}-{digest}"


def normalize_skeleton(value: str) -> str:
    value = ATOM.sub("<atom>", value.lower())
    value = HEX.sub("<hex>", value)
    value = re.sub(r"\d+", "<n>", value)
    return SPACE.sub(" ", value).strip()


def structural_ngrams(value: str, width: int = 7) -> set[str]:
    tokens = re.findall(r"[a-z]+|<[^>]+>|[.?]", normalize_skeleton(value))
    return {
        sha256_text(" ".join(tokens[index : index + width]))
        for index in range(max(0, len(tokens) - width + 1))
    }


def content_strings(family: dict[str, Any]) -> Iterable[str]:
    for key in ("family_id", "namespace_id", "source_document", "source_sha256", "support_document", "support_sha256"):
        value = family.get(key)
        if isinstance(value, str):
            yield value
    for record in family.get("records", []):
        if isinstance(record, dict):
            for key in ("subject", "alias", "bridge", "value"):
                value = record.get(key)
                if isinstance(value, str):
                    yield value
    for query in family.get("queries", []):
        if not isinstance(query, dict):
            continue
        for key in ("query_id", "question", "prompt", "prompt_sha256", "template_id"):
            value = query.get(key)
            if isinstance(value, str):
                yield value
        for option in query.get("options", []):
            if isinstance(option, str):
                yield option


def normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_skeleton(value)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_value(item) for key, item in value.items()}
    return value


def question_for(
    fact_kind: str, evaluation_kind: str, variant: int, record: dict[str, str]
) -> str:
    subject_noun, answer_noun = FACT_TERMS[fact_kind]
    subject = record["subject"]
    alias = record["alias"]
    bridge = record["bridge"]
    templates = {
        "paraphrase": (
            "Without the sealed dossier, select the {answer} assigned to {subject}.",
            "Which {answer} would complete the private entry for {subject}?",
            "Mark the candidate {answer} belonging to {subject} in the hidden register.",
            "For concealed {noun} {subject}, identify its unavailable {answer}.",
        ),
        "multi_hop": (
            "Private alias {alias} resolves to a hidden {noun}; choose its {answer}.",
            "Follow unavailable alias {alias}, then mark the associated {answer}.",
            "Which {answer} sits beyond the concealed alias link {alias}?",
            "Resolve private alias {alias} to its {noun} and select the {answer}.",
        ),
        "withheld_composition": (
            "Traverse hidden bridge {bridge} and its alias; choose the terminal {answer}.",
            "What {answer} terminates the unavailable bridge chain beginning at {bridge}?",
            "Decode private bridge {bridge}, resolve its alias, and mark the {answer}.",
            "Select the {answer} reached through concealed bridge {bridge}.",
        ),
    }
    return templates[evaluation_kind][variant].format(
        noun=subject_noun,
        answer=answer_noun,
        subject=subject,
        alias=alias,
        bridge=bridge,
    )


def render_prompt(question: str, options: list[str]) -> str:
    lines = [
        "Blind registry probe. The supporting dossier is intentionally absent.",
        question,
        *(f"[{label}] {option}" for label, option in zip(LABELS, options)),
        "Return one bracket-free uppercase label:",
    ]
    return "\n".join(lines) + "\n"


def semantic_ast(family: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "mesh.astral_v28r2_semantic_graph.v1",
        "fact_kind": family["fact_kind"],
        "namespace_id": family["namespace_id"],
        "target_index": family["target_index"],
        "vertices": family["records"],
        "edges": ["bridge_to_alias", "alias_to_subject", "subject_to_value"],
    }


def expected_options(family: dict[str, Any], evaluation_index: int, variant: int) -> list[str]:
    target_index = family["target_index"]
    target_value = family["records"][target_index]["value"]
    choice = PERMUTATIONS[(family["family_in_block"] + 7 * evaluation_index) % 24][variant]
    distractors = [
        row["value"]
        for index, row in enumerate(family["records"])
        if index != target_index
    ]
    rotate = (variant + evaluation_index) % 3
    distractors = distractors[rotate:] + distractors[:rotate]
    result: list[str] = []
    cursor = 0
    for index in range(4):
        if index == choice:
            result.append(target_value)
        else:
            result.append(distractors[cursor])
            cursor += 1
    return result


def _error(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def validate_fingerprint(value: Any, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        _error(errors, "retired_fingerprint.object")
        return None
    if value.get("version") != "astral.v28r2.retired_r1_fingerprint.v1":
        _error(errors, "retired_fingerprint.version")
    if value.get("retired_campaign") != "V28R1":
        _error(errors, "retired_fingerprint.campaign")
    expected = content_hash(without_hash(value, "fingerprint_sha256"))
    if value.get("fingerprint_sha256") != expected:
        _error(errors, "retired_fingerprint.hash")
    for key in (
        "exact_string_sha256s",
        "normalized_surface_skeleton_sha256s",
        "structural_seven_gram_sha256s",
        "semantic_ast_sha256s",
        "normalized_semantic_ast_sha256s",
    ):
        items = value.get(key)
        if not isinstance(items, list) or items != sorted(set(items)):
            _error(errors, f"retired_fingerprint.{key}")
    return value


def validate_corpus(
    corpus: Any,
    fingerprint: dict[str, Any],
    errors: list[str],
    families_per_kind: int | None = None,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if not isinstance(corpus, dict):
        _error(errors, "corpus.object")
        return {}, []
    if corpus.get("version") != "mesh.astral_v28r2_corpus.v1":
        _error(errors, "corpus.version")
    expected_manifest = content_hash(without_hash(corpus, "manifest_sha256"))
    if corpus.get("manifest_sha256") != expected_manifest:
        _error(errors, "corpus.manifest_sha256")
    families = corpus.get("families")
    if not isinstance(families, list):
        _error(errors, "corpus.families")
        return {}, []
    per_kind = families_per_kind or int(PROTOCOL["families_per_fact_kind"])
    if len(families) != per_kind * len(FACT_KINDS):
        _error(errors, "corpus.family_count")
    family_map: dict[str, dict[str, Any]] = {}
    query_order: list[str] = []
    r1_exact = set(fingerprint["exact_string_sha256s"])
    r1_skeletons = set(fingerprint["normalized_surface_skeleton_sha256s"])
    r1_ngrams = set(fingerprint["structural_seven_gram_sha256s"])
    r1_asts = set(fingerprint["semantic_ast_sha256s"])
    r1_normalized_asts = set(fingerprint["normalized_semantic_ast_sha256s"])
    surface_skeletons: set[str] = set()
    surface_ngrams: set[str] = set()
    for ordinal, family in enumerate(families):
        prefix = f"corpus.family[{ordinal}]"
        if not isinstance(family, dict):
            _error(errors, f"{prefix}.object")
            continue
        family_id = family.get("family_id")
        if not isinstance(family_id, str) or family_id in family_map:
            _error(errors, f"{prefix}.family_id")
            continue
        family_map[family_id] = family
        fact_kind = family.get("fact_kind")
        if fact_kind not in FACT_KINDS:
            _error(errors, f"{prefix}.fact_kind")
            continue
        expected_kind_ordinal = ordinal % per_kind
        expected_kind = FACT_KINDS[ordinal // per_kind] if ordinal < per_kind * 4 else None
        if fact_kind != expected_kind:
            _error(errors, f"{prefix}.ordering")
        if family.get("block_index") != expected_kind_ordinal // 24:
            _error(errors, f"{prefix}.block_index")
        if family.get("family_in_block") != expected_kind_ordinal % 24:
            _error(errors, f"{prefix}.family_in_block")
        records = family.get("records")
        if not isinstance(records, list) or len(records) != 4:
            _error(errors, f"{prefix}.records")
            continue
        if family.get("target_index") not in range(4):
            _error(errors, f"{prefix}.target_index")
            continue
        required_record_keys = {"subject", "alias", "bridge", "value"}
        if any(not isinstance(row, dict) or set(row) != required_record_keys for row in records):
            _error(errors, f"{prefix}.record_schema")
            continue
        ast = semantic_ast(family)
        if family.get("semantic_ast_sha256") != content_hash(ast):
            _error(errors, f"{prefix}.semantic_ast_sha256")
        if content_hash(ast) in r1_asts:
            _error(errors, "corpus.r1_semantic_ast_overlap")
        if content_hash(normalize_value(ast)) in r1_normalized_asts:
            _error(errors, "corpus.r1_normalized_semantic_ast_overlap")
        source = family.get("source_document")
        support = family.get("support_document")
        for name, text in (("source", source), ("support", support)):
            if not isinstance(text, str) or family.get(f"{name}_sha256") != sha256_text(text):
                _error(errors, f"{prefix}.{name}_binding")
            elif text:
                skeleton_hash = sha256_text(normalize_skeleton(text))
                surface_skeletons.add(skeleton_hash)
                surface_ngrams.update(structural_ngrams(text))
        queries = family.get("queries")
        if not isinstance(queries, list) or len(queries) != 12:
            _error(errors, f"{prefix}.queries")
            continue
        seen_query_ids: set[str] = set()
        for query_ordinal, query in enumerate(queries):
            qprefix = f"{prefix}.query[{query_ordinal}]"
            if not isinstance(query, dict):
                _error(errors, f"{qprefix}.object")
                continue
            evaluation_index = query_ordinal // 4
            variant = query_ordinal % 4
            evaluation_kind = EVALUATION_KINDS[evaluation_index]
            if query.get("evaluation_kind") != evaluation_kind or query.get("variant") != variant:
                _error(errors, f"{qprefix}.ordering")
            if query.get("template_id") != f"r2-{fact_kind}-{evaluation_kind}-surface-{variant}":
                _error(errors, f"{qprefix}.template_id")
            record = records[family["target_index"]]
            expected_question = question_for(fact_kind, evaluation_kind, variant, record)
            expected_values = expected_options(family, evaluation_index, variant)
            expected_choice = PERMUTATIONS[
                (family["family_in_block"] + 7 * evaluation_index) % 24
            ][variant]
            expected_prompt = render_prompt(expected_question, expected_values)
            query_id = tag_id("r2query", family_id, evaluation_kind, variant)
            if query.get("query_id") != query_id or query_id in seen_query_ids:
                _error(errors, f"{qprefix}.query_id")
            seen_query_ids.add(query_id)
            if query.get("question") != expected_question:
                _error(errors, f"{qprefix}.question")
            if query.get("options") != expected_values:
                _error(errors, f"{qprefix}.options")
            if query.get("expected_choice") != expected_choice:
                _error(errors, f"{qprefix}.expected_choice")
            if query.get("expected_label") != LABELS[expected_choice]:
                _error(errors, f"{qprefix}.expected_label")
            if query.get("prompt") != expected_prompt:
                _error(errors, f"{qprefix}.prompt")
            if query.get("prompt_sha256") != sha256_text(expected_prompt):
                _error(errors, f"{qprefix}.prompt_sha256")
            query_order.append(query_id)
            for text in (expected_question, expected_prompt):
                surface_skeletons.add(sha256_text(normalize_skeleton(text)))
                surface_ngrams.update(structural_ngrams(text))
        if any(sha256_text(value) in r1_exact for value in content_strings(family)):
            _error(errors, "corpus.r1_exact_string_overlap")
    if len(query_order) != per_kind * 4 * 12 or len(set(query_order)) != len(query_order):
        _error(errors, "corpus.query_census")
    if surface_skeletons & r1_skeletons:
        _error(errors, "corpus.r1_normalized_skeleton_overlap")
    if surface_ngrams & r1_ngrams:
        _error(errors, "corpus.r1_structural_ngram_overlap")
    for fact_kind in FACT_KINDS:
        kind_families = [family for family in families if family.get("fact_kind") == fact_kind]
        for start in range(0, len(kind_families), 24):
            block = kind_families[start : start + 24]
            if len(block) != 24:
                _error(errors, f"corpus.permutation_block.{fact_kind}.{start // 24}.size")
                continue
            for evaluation_index, evaluation_kind in enumerate(EVALUATION_KINDS):
                observed = {
                    tuple(
                        family["queries"][evaluation_index * 4 + variant]["expected_choice"]
                        for variant in range(4)
                    )
                    for family in block
                }
                if observed != set(PERMUTATIONS):
                    _error(
                        errors,
                        f"corpus.permutation_block.{fact_kind}.{evaluation_kind}.{start // 24}",
                    )
    return family_map, query_order


def validate_run(
    run: Any,
    arm_id: str,
    query_map: dict[str, dict[str, Any]],
    query_order: list[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    if not isinstance(run, dict):
        _error(errors, f"run.{arm_id}.object")
        return {}
    if run.get("arm_id") != arm_id:
        _error(errors, f"run.{arm_id}.arm_id")
    if run.get("seed_id") != 280201 or run.get("task_order_id") != "full-corpus":
        _error(errors, f"run.{arm_id}.cell")
    if run.get("persistence_class") != "unchanged_checkpoint":
        _error(errors, f"run.{arm_id}.persistence_class")
    observations = run.get("observations")
    if not isinstance(observations, list):
        _error(errors, f"run.{arm_id}.observations")
        return {}
    if run.get("observations_sha256") != content_hash(observations):
        _error(errors, f"run.{arm_id}.observations_sha256")
    if len(observations) != len(query_order):
        _error(errors, f"run.{arm_id}.count")
    result: dict[str, dict[str, Any]] = {}
    for index, observation in enumerate(observations):
        prefix = f"run.{arm_id}.observation[{index}]"
        if not isinstance(observation, dict):
            _error(errors, f"{prefix}.object")
            continue
        query_id = observation.get("query_id")
        if query_id not in query_map or query_id in result:
            _error(errors, f"{prefix}.query_id")
            continue
        result[query_id] = observation
        if index >= len(query_order) or query_id != query_order[index]:
            _error(errors, f"{prefix}.order")
        query = query_map[query_id]
        if observation.get("prompt_sha256") != query["prompt_sha256"]:
            _error(errors, f"{prefix}.prompt_sha256")
        token_ids = observation.get("token_ids")
        if not isinstance(token_ids, list) or not token_ids or any(
            not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in token_ids
        ):
            _error(errors, f"{prefix}.token_ids")
        elif observation.get("tokenized_input_sha256") != content_hash(token_ids):
            _error(errors, f"{prefix}.tokenized_input_sha256")
        scores = observation.get("label_scores")
        if not isinstance(scores, list) or len(scores) != 4 or any(
            not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(item)
            for item in (scores if isinstance(scores, list) else [])
        ):
            _error(errors, f"{prefix}.label_scores")
            continue
        predicted_choice = max(range(4), key=lambda choice: scores[choice])
        if observation.get("predicted_label") != LABELS[predicted_choice]:
            _error(errors, f"{prefix}.predicted_label")
        correct = predicted_choice == query["expected_choice"]
        if observation.get("correct") is not correct:
            _error(errors, f"{prefix}.correct")
    return result


def interval(values: list[float]) -> dict[str, Any]:
    count = len(values)
    mean = statistics.fmean(values) if values else 0.0
    standard_error = statistics.stdev(values) / math.sqrt(count) if count > 1 else math.inf
    critical = float(PROTOCOL["minimum_student_t_critical_value"])
    lower = mean - critical * standard_error
    upper = mean + critical * standard_error
    margin = float(PROTOCOL["equivalence_margin"])
    return {
        "family_cluster_count": count,
        "mean_chance_normalized_lift": mean,
        "standard_error": standard_error,
        "critical_value": critical,
        "lower": lower,
        "upper": upper,
        "equivalence_passed": lower > -margin and upper < margin,
    }


def arm_metrics(
    observations: dict[str, dict[str, Any]], families: list[dict[str, Any]]
) -> dict[str, Any]:
    family_rows: list[dict[str, Any]] = []
    for family in families:
        by_kind: dict[str, list[float]] = {kind: [] for kind in EVALUATION_KINDS}
        all_correct: list[float] = []
        for query in family["queries"]:
            value = 1.0 if observations[query["query_id"]]["correct"] else 0.0
            all_correct.append(value)
            by_kind[query["evaluation_kind"]].append(value)
        normalize = lambda accuracy: (accuracy - 0.25) / 0.75
        family_rows.append(
            {
                "fact_kind": family["fact_kind"],
                "overall": normalize(statistics.fmean(all_correct)),
                **{
                    kind: normalize(statistics.fmean(values))
                    for kind, values in by_kind.items()
                },
            }
        )
    result: dict[str, Any] = {"overall": interval([row["overall"] for row in family_rows])}
    result["fact_kinds"] = {
        kind: interval([row["overall"] for row in family_rows if row["fact_kind"] == kind])
        for kind in FACT_KINDS
    }
    result["evaluation_kinds"] = {
        kind: interval([row[kind] for row in family_rows]) for kind in EVALUATION_KINDS
    }
    result["equivalence_passed"] = all(
        entry["equivalence_passed"]
        for entry in (
            [result["overall"]]
            + list(result["fact_kinds"].values())
            + list(result["evaluation_kinds"].values())
        )
    )
    return result


def validate_packet(packet: Any, retired_fingerprint: Any) -> dict[str, Any]:
    try:
        return _validate_packet(packet, retired_fingerprint)
    except (KeyError, TypeError, IndexError, ValueError, statistics.StatisticsError) as error:
        packet_value = packet if isinstance(packet, dict) else None
        return _report(
            "Invalid",
            [f"validator.malformed_input.{type(error).__name__}"],
            {},
            packet_value,
        )


def _validate_packet(packet: Any, retired_fingerprint: Any) -> dict[str, Any]:
    errors: list[str] = []
    if packet is None:
        return _report("NotRun", ["packet.not_supplied"], {}, None)
    if not isinstance(packet, dict):
        return _report("Invalid", ["packet.object"], {}, None)
    fingerprint = validate_fingerprint(retired_fingerprint, errors)
    if fingerprint is None:
        return _report("Invalid", errors, {}, packet)
    if packet.get("version") != PROTOCOL["packet_version"]:
        _error(errors, "packet.version")
    if packet.get("state_slice") != PROTOCOL["packet_state_slice"]:
        _error(errors, "packet.state_slice")
    if packet.get("packet_sha256") != content_hash(without_hash(packet, "packet_sha256")):
        _error(errors, "packet.packet_sha256")
    provenance = packet.get("provenance")
    if not isinstance(provenance, dict):
        _error(errors, "provenance.object")
        provenance = {}
    if provenance.get("protocol_sha256") != sha256_bytes(PROTOCOL_BYTES):
        _error(errors, "provenance.protocol_sha256")
    if provenance.get("retired_r1_fingerprint_sha256") != fingerprint.get("fingerprint_sha256"):
        _error(errors, "provenance.retired_r1_fingerprint_sha256")
    expected_power = {
        "families_per_fact_kind": 1536,
        "total_families": 6144,
        "queries_per_family": 12,
        "queries_per_run": 73728,
        "total_baseline_evaluations": 147456,
        "equivalence_margin": 0.05,
        "minimum_student_t_critical_value": 5.0,
        "two_sided_hypothesis_count": 16,
    }
    if provenance.get("power_profile") != expected_power:
        _error(errors, "provenance.power_profile")
    orders = provenance.get("sealing_order")
    required_order_keys = (
        "source_committed",
        "receipts_sealed",
        "ledger_claimed",
        "seed_created",
        "corpus_generated",
        "model_loaded",
        "baselines_completed",
    )
    if not isinstance(orders, dict) or set(orders) != set(required_order_keys) or not all(
        isinstance(orders.get(key), int) and not isinstance(orders.get(key), bool)
        for key in required_order_keys
    ) or [orders[key] for key in required_order_keys] != sorted(
        orders[key] for key in required_order_keys
    ) or len(set(orders.values())) != len(required_order_keys):
        _error(errors, "provenance.sealing_order")
    allowed_inputs = {
        "protocol",
        "source_receipt",
        "runtime_receipt",
        "checkpoint_receipt",
        "retired_r1_fingerprint",
        "seed_material",
    }
    inventory = provenance.get("generator_input_inventory")
    if not isinstance(inventory, list) or set(inventory) != allowed_inputs or len(inventory) != len(allowed_inputs):
        _error(errors, "provenance.generator_input_inventory")
    for flag in ("single_seed_draw", "single_candidate_corpus", "no_discarded_candidate", "no_adaptive_expansion"):
        if provenance.get(flag) is not True:
            _error(errors, f"provenance.{flag}")
    family_map, query_order = validate_corpus(packet.get("corpus"), fingerprint, errors)
    query_map = {
        query["query_id"]: query
        for family in family_map.values()
        for query in family.get("queries", [])
        if isinstance(query, dict) and isinstance(query.get("query_id"), str)
    }
    runs = packet.get("runs")
    if not isinstance(runs, list) or len(runs) != 2:
        _error(errors, "runs.exactly_two")
        runs = []
    run_by_arm = {
        run.get("arm_id"): run for run in runs if isinstance(run, dict) and isinstance(run.get("arm_id"), str)
    }
    if set(run_by_arm) != set(PROTOCOL["required_baseline_arm_ids"]):
        _error(errors, "runs.arm_ids")
    validated_runs = {
        arm_id: validate_run(run_by_arm.get(arm_id), arm_id, query_map, query_order, errors)
        for arm_id in PROTOCOL["required_baseline_arm_ids"]
    }
    if len(run_by_arm) == 2:
        pre = run_by_arm["pre_update"]
        no_update = run_by_arm["no_update"]
        for key in ("preparation_process_id", "evaluation_process_id"):
            if not isinstance(pre.get(key), str) or not isinstance(no_update.get(key), str):
                _error(errors, f"runs.{key}")
        process_ids = {
            pre.get("preparation_process_id"),
            pre.get("evaluation_process_id"),
            no_update.get("preparation_process_id"),
            no_update.get("evaluation_process_id"),
        }
        if len(process_ids) != 4 or None in process_ids:
            _error(errors, "runs.distinct_processes")
        if no_update.get("fresh_checkpoint_reload") is not True or pre.get("fresh_checkpoint_reload") is not True:
            _error(errors, "runs.fresh_checkpoint_reload")
        for key in ("checkpoint_sha256", "implementation_sha256", "scorer_sha256", "tokenizer_sha256"):
            if pre.get(key) != no_update.get(key) or not isinstance(pre.get(key), str):
                _error(errors, f"runs.parity.{key}")
        if validated_runs.get("pre_update") != validated_runs.get("no_update"):
            _error(errors, "runs.exact_observation_parity")
    for key in PROTOCOL["forbidden_material_keys"]:
        if packet.get(key) is not None:
            _error(errors, f"later_gate_material.{key}")
    claims = packet.get("claim_boundary")
    if not isinstance(claims, dict):
        _error(errors, "claim_boundary.object")
    else:
        if claims.get("local_model_backed_acquisition_novelty_preflight_v28r2") is not False:
            _error(errors, "claim_boundary.local_preflight_must_be_false_in_packet")
        for key in PROTOCOL["required_false_claims"]:
            if claims.get(key) is not False:
                _error(errors, f"claim_boundary.{key}")
    metrics: dict[str, Any] = {}
    if not errors:
        families = packet["corpus"]["families"]
        metrics = {
            arm_id: arm_metrics(observations, families)
            for arm_id, observations in validated_runs.items()
        }
    if errors:
        status = "Invalid"
    elif all(entry["equivalence_passed"] for entry in metrics.values()):
        status = "NoveltyPacketCandidate"
    else:
        status = "CorpusNotNovel"
    return _report(status, errors, metrics, packet)


def _report(
    status: str,
    errors: list[str],
    metrics: dict[str, Any],
    packet: dict[str, Any] | None,
) -> dict[str, Any]:
    report = {
        "version": "astral.v28r2_validation_report.v1",
        "state_slice": PROTOCOL["state_slice"],
        "status": status,
        "errors": sorted(errors),
        "packet_sha256": packet.get("packet_sha256") if isinstance(packet, dict) else None,
        "protocol_sha256": sha256_bytes(PROTOCOL_BYTES),
        "baseline_equivalence_metrics": metrics,
        "statistical_unit": "family_cluster",
        "open_gates": (
            ["acquisition.update_arms_require_separate_authorization"]
            if status == "NoveltyPacketCandidate"
            else ["acquisition.new_corpus_not_authorized"]
            if status == "CorpusNotNovel"
            else ["acquisition.valid_v28r2_packet_required"]
        ),
        "claim_ceiling": (
            PROTOCOL["claim_ceiling"] if status == "NoveltyPacketCandidate" else "NoScientificClaim"
        ),
    }
    report["report_sha256"] = content_hash(report)
    return report
