from __future__ import annotations

import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_ID_RE = re.compile(r"^[0-9a-f]{40}$")


def protocol() -> dict[str, Any]:
    return json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def stable_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def seal_packet(packet: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(packet)
    sealed.pop("packet_sha256", None)
    sealed["packet_sha256"] = stable_hash(sealed)
    return sealed


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def _git_id(value: Any) -> bool:
    return isinstance(value, str) and bool(GIT_ID_RE.fullmatch(value))


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _hash_matches(value: Any, supplied: Any) -> bool:
    try:
        return supplied == stable_hash(value)
    except (TypeError, ValueError):
        return False


def _exact_keys(
    value: dict[str, Any], expected: set[str], prefix: str, errors: list[str]
) -> None:
    if set(value) != expected:
        errors.append(f"{prefix}.field_census")


def _accuracy(correct: int, total: int) -> float:
    return round(correct / total, 10) if total else 0.0


def _chance_lift(accuracy: float, choice_count: int) -> float:
    chance = 1.0 / choice_count
    return round((accuracy - chance) / (1.0 - chance), 10)


def _validate_provenance(packet: dict[str, Any], errors: list[str]) -> str | None:
    provenance = _dict(packet.get("provenance"))
    _exact_keys(
        provenance,
        {
            "starting_checkpoint_sha256",
            "protocol_sha256",
            "tokenizer_sha256",
            "runtime_sha256",
            "source_commit",
            "source_tree",
            "generator_sha256",
            "generator_config_sha256",
            "seed_commitment_sha256",
            "corpus_manifest_sha256",
            "split_commitment_sha256",
            "configuration_lock_sha256",
            "future_assessment_family_commitment_sha256",
            "generator_checkpoint_sha256",
            "v27_data_reused",
            "model_output_guided_generation",
            "checkpoint_hashed_order",
            "seed_committed_order",
            "corpus_generated_order",
            "configuration_locked_order",
            "baseline_outcomes_order",
            "update_outcomes_order",
        },
        "provenance",
        errors,
    )
    digest_fields = (
        "starting_checkpoint_sha256",
        "protocol_sha256",
        "tokenizer_sha256",
        "runtime_sha256",
        "generator_sha256",
        "generator_config_sha256",
        "seed_commitment_sha256",
        "corpus_manifest_sha256",
        "split_commitment_sha256",
        "configuration_lock_sha256",
        "future_assessment_family_commitment_sha256",
    )
    for field in digest_fields:
        if not _sha256(provenance.get(field)):
            errors.append(f"provenance.{field}")
    if provenance.get("protocol_sha256") != stable_hash(protocol()):
        errors.append("provenance.protocol_sha256_binding")
    for field in ("source_commit", "source_tree"):
        if not _git_id(provenance.get(field)):
            errors.append(f"provenance.{field}")
    if provenance.get("generator_checkpoint_sha256") != provenance.get(
        "starting_checkpoint_sha256"
    ):
        errors.append("provenance.generator_checkpoint_binding")
    if provenance.get("v27_data_reused") is not False:
        errors.append("provenance.v27_data_reused")
    if provenance.get("model_output_guided_generation") is not False:
        errors.append("provenance.model_output_guided_generation")
    orders = [
        provenance.get("checkpoint_hashed_order"),
        provenance.get("seed_committed_order"),
        provenance.get("corpus_generated_order"),
        provenance.get("configuration_locked_order"),
        provenance.get("baseline_outcomes_order"),
    ]
    if any(not isinstance(value, int) or isinstance(value, bool) for value in orders):
        errors.append("provenance.order_types")
    elif orders != sorted(orders) or len(set(orders)) != len(orders):
        errors.append("provenance.ordering")
    update_order = provenance.get("update_outcomes_order")
    if update_order is not None and (
        not isinstance(update_order, int)
        or isinstance(update_order, bool)
        or not isinstance(orders[-1], int)
        or update_order <= orders[-1]
    ):
        errors.append("provenance.update_outcomes_order")
    return provenance.get("starting_checkpoint_sha256")


def _validate_corpus(
    packet: dict[str, Any], contract: dict[str, Any], errors: list[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, str]]:
    corpus = _dict(packet.get("corpus"))
    _exact_keys(
        corpus,
        {"choice_count", "split", "manifest_sha256", "items"},
        "corpus",
        errors,
    )
    items = _list(corpus.get("items"))
    if corpus.get("choice_count") != contract["choice_count"]:
        errors.append("corpus.choice_count")
    if corpus.get("split") != "qualification":
        errors.append("corpus.split")
    if not _hash_matches(items, corpus.get("manifest_sha256")):
        errors.append("corpus.manifest_sha256")
    if corpus.get("manifest_sha256") != _dict(packet.get("provenance")).get(
        "corpus_manifest_sha256"
    ):
        errors.append("corpus.provenance_manifest_binding")

    required_fact_kinds = set(contract["required_fact_kinds"])
    required_eval_kinds = set(contract["required_evaluation_kinds"])
    fact_counts: Counter[str] = Counter()
    families: set[str] = set()
    item_ids: set[str] = set()
    source_hashes: set[str] = set()
    prompt_hashes: set[str] = set()
    training_template_ids: set[str] = set()
    evaluation_template_ids: set[str] = set()
    answer_option_hashes: set[str] = set()
    query_index: dict[str, dict[str, Any]] = {}
    query_fact_kind: dict[str, str] = {}
    query_family_id: dict[str, str] = {}
    answer_counts: dict[tuple[str, str], Counter[int]] = defaultdict(Counter)

    for index, raw_item in enumerate(items):
        item = _dict(raw_item)
        prefix = f"corpus.items[{index}]"
        _exact_keys(
            item,
            {
                "item_id",
                "family_id",
                "fact_kind",
                "source_form_sha256",
                "support_source_sha256s",
                "training_template_family_id",
                "answer_option_sha256s",
                "answer_position",
                "expected_answer_sha256",
                "answer_mapping_sha256",
                "queries",
            },
            prefix,
            errors,
        )
        item_id = item.get("item_id")
        family_id = item.get("family_id")
        fact_kind = item.get("fact_kind")
        source_hash = item.get("source_form_sha256")
        support_hashes = _list(item.get("support_source_sha256s"))
        training_template_id = item.get("training_template_family_id")
        answer_options = _list(item.get("answer_option_sha256s"))
        answer_position = item.get("answer_position")
        expected_answer_sha256 = item.get("expected_answer_sha256")
        if not _nonempty(item_id) or item_id in item_ids:
            errors.append(f"{prefix}.item_id")
        else:
            item_ids.add(item_id)
        if not _nonempty(family_id) or family_id in families:
            errors.append(f"{prefix}.family_id")
        else:
            families.add(family_id)
        if not isinstance(fact_kind, str) or fact_kind not in required_fact_kinds:
            errors.append(f"{prefix}.fact_kind")
        else:
            fact_counts[fact_kind] += 1
        if not _sha256(source_hash) or source_hash in source_hashes:
            errors.append(f"{prefix}.source_form_sha256")
        else:
            source_hashes.add(source_hash)
        if (
            len(support_hashes) != 1
            or not _sha256(support_hashes[0])
            or support_hashes[0] == source_hash
            or support_hashes[0] in source_hashes
        ):
            errors.append(f"{prefix}.support_source_sha256s")
        else:
            source_hashes.add(support_hashes[0])
        if (
            not _nonempty(training_template_id)
            or training_template_id in training_template_ids
        ):
            errors.append(f"{prefix}.training_template_family_id")
        else:
            training_template_ids.add(training_template_id)
        if (
            len(answer_options) != contract["choice_count"]
            or any(not _sha256(value) for value in answer_options)
            or len(set(answer_options)) != contract["choice_count"]
            or any(value in answer_option_hashes for value in answer_options)
        ):
            errors.append(f"{prefix}.answer_option_sha256s")
        else:
            answer_option_hashes.update(answer_options)
        if (
            not isinstance(answer_position, int)
            or isinstance(answer_position, bool)
            or not 0 <= answer_position < contract["choice_count"]
        ):
            errors.append(f"{prefix}.answer_position")
        elif (
            len(answer_options) != contract["choice_count"]
            or expected_answer_sha256 != answer_options[answer_position]
        ):
            errors.append(f"{prefix}.expected_answer_sha256")
        answer_mapping = {
            "item_id": item_id,
            "family_id": family_id,
            "answer_option_sha256s": answer_options,
            "answer_position": answer_position,
            "expected_answer_sha256": expected_answer_sha256,
        }
        if not _hash_matches(answer_mapping, item.get("answer_mapping_sha256")):
            errors.append(f"{prefix}.answer_mapping_sha256")
        queries = _list(item.get("queries"))
        query_kind_counts = Counter(
            str(_dict(query).get("evaluation_kind")) for query in queries
        )
        if (
            len(queries)
            != len(required_eval_kinds) * contract["queries_per_evaluation_kind"]
            or set(query_kind_counts) != required_eval_kinds
            or any(
                query_kind_counts[eval_kind] != contract["queries_per_evaluation_kind"]
                for eval_kind in required_eval_kinds
            )
        ):
            errors.append(f"{prefix}.query_census")
        for query_index_in_item, raw_query in enumerate(queries):
            query = _dict(raw_query)
            query_prefix = f"{prefix}.queries[{query_index_in_item}]"
            _exact_keys(
                query,
                {
                    "query_id",
                    "evaluation_kind",
                    "prompt_sha256",
                    "expected_choice",
                    "expected_answer_sha256",
                    "answer_mapping_sha256",
                    "template_family_id",
                    "dependency_source_sha256s",
                    "derivation_manifest_sha256",
                    "withheld_from_training",
                },
                query_prefix,
                errors,
            )
            query_id = query.get("query_id")
            eval_kind = query.get("evaluation_kind")
            prompt_hash = query.get("prompt_sha256")
            expected_choice = query.get("expected_choice")
            query_expected_answer = query.get("expected_answer_sha256")
            template_family_id = query.get("template_family_id")
            dependencies = _list(query.get("dependency_source_sha256s"))
            if not _nonempty(query_id) or query_id in query_index:
                errors.append(f"{query_prefix}.query_id")
            if not _sha256(prompt_hash) or prompt_hash in prompt_hashes:
                errors.append(f"{query_prefix}.prompt_sha256")
            elif prompt_hash == source_hash:
                errors.append(f"{query_prefix}.training_form_overlap")
            else:
                prompt_hashes.add(prompt_hash)
            if (
                not isinstance(expected_choice, int)
                or isinstance(expected_choice, bool)
                or not 0 <= expected_choice < contract["choice_count"]
            ):
                errors.append(f"{query_prefix}.expected_choice")
            if expected_choice != answer_position:
                errors.append(f"{query_prefix}.answer_position_binding")
            if query_expected_answer != expected_answer_sha256:
                errors.append(f"{query_prefix}.expected_answer_sha256")
            if query.get("answer_mapping_sha256") != item.get("answer_mapping_sha256"):
                errors.append(f"{query_prefix}.answer_mapping_sha256")
            if (
                not _nonempty(template_family_id)
                or template_family_id in evaluation_template_ids
            ):
                errors.append(f"{query_prefix}.template_family_id")
            else:
                evaluation_template_ids.add(template_family_id)
            valid_local_sources = _sha256(source_hash) and all(
                _sha256(value) for value in support_hashes
            )
            expected_dependencies = (
                (
                    {source_hash}
                    if eval_kind == "paraphrase"
                    else {source_hash, *support_hashes}
                )
                if valid_local_sources
                else set()
            )
            if (
                any(not _sha256(value) for value in dependencies)
                or len(dependencies) != len(set(dependencies))
                or set(dependencies) != expected_dependencies
            ):
                errors.append(f"{query_prefix}.dependency_source_sha256s")
            derivation = {
                "item_id": item_id,
                "family_id": family_id,
                "query_id": query_id,
                "evaluation_kind": eval_kind,
                "prompt_sha256": prompt_hash,
                "template_family_id": template_family_id,
                "dependency_source_sha256s": dependencies,
                "expected_choice": expected_choice,
                "expected_answer_sha256": query_expected_answer,
                "answer_mapping_sha256": query.get("answer_mapping_sha256"),
                "withheld_from_training": query.get("withheld_from_training"),
            }
            if not _hash_matches(derivation, query.get("derivation_manifest_sha256")):
                errors.append(f"{query_prefix}.derivation_manifest_sha256")
            if query.get("withheld_from_training") is not True:
                errors.append(f"{query_prefix}.withheld_from_training")
            if (
                _nonempty(query_id)
                and query_id not in query_index
                and isinstance(eval_kind, str)
                and eval_kind in required_eval_kinds
                and isinstance(fact_kind, str)
                and fact_kind in required_fact_kinds
                and isinstance(expected_choice, int)
                and not isinstance(expected_choice, bool)
                and 0 <= expected_choice < contract["choice_count"]
            ):
                query_index[query_id] = query
                query_fact_kind[query_id] = fact_kind
                query_family_id[query_id] = family_id
                answer_counts[(fact_kind, eval_kind)][expected_choice] += 1

    if source_hashes & prompt_hashes:
        errors.append("corpus.global_training_form_overlap")
    if answer_option_hashes & (source_hashes | prompt_hashes):
        errors.append("corpus.answer_option_leakage")
    if training_template_ids & evaluation_template_ids:
        errors.append("corpus.training_evaluation_template_overlap")

    minimum = contract["thresholds"]["minimum_families_per_fact_kind"]
    if set(fact_counts) != required_fact_kinds:
        errors.append("corpus.fact_kind_census")
    for fact_kind in contract["required_fact_kinds"]:
        if fact_counts[fact_kind] < minimum:
            errors.append(f"corpus.fact_kind_minimum.{fact_kind}")
    for fact_kind in contract["required_fact_kinds"]:
        for eval_kind in contract["required_evaluation_kinds"]:
            counts = answer_counts[(fact_kind, eval_kind)]
            expected = (
                fact_counts[fact_kind]
                * contract["queries_per_evaluation_kind"]
                // contract["choice_count"]
            )
            if (
                fact_counts[fact_kind] % contract["choice_count"] != 0
                or set(counts) != set(range(contract["choice_count"]))
                or any(count != expected for count in counts.values())
            ):
                errors.append(f"corpus.answer_balance.{fact_kind}.{eval_kind}")
    return query_index, query_fact_kind, query_family_id


def _validate_run(
    raw_run: Any,
    contract: dict[str, Any],
    starting_checkpoint_sha256: str | None,
    query_index: dict[str, dict[str, Any]],
    query_fact_kind: dict[str, str],
    query_family_id: dict[str, str],
    process_ids: set[str],
    errors: list[str],
) -> tuple[str | None, tuple[int, str] | None, dict[str, Any]]:
    run = _dict(raw_run)
    arm_id = run.get("arm_id")
    prefix = f"runs.{arm_id}" if _nonempty(arm_id) else "runs.unknown"
    _exact_keys(
        run,
        {
            "arm_id",
            "seed",
            "task_order_id",
            "execution_status",
            "persistence_class",
            "implementation_sha256",
            "arm_configuration_sha256",
            "artifact_manifest_sha256",
            "starting_state_sha256",
            "post_update_state_sha256",
            "restart_loaded_state_sha256",
            "update_process_id",
            "evaluation_process_id",
            "source_context_present",
            "retrieval_enabled",
            "source_context_item_count",
            "retrieval_payload_count",
            "source_context_manifest_sha256",
            "retrieval_payload_manifest_sha256",
            "evaluation_input_manifest_sha256",
            "update_budget",
            "observations",
            "observations_sha256",
        },
        prefix,
        errors,
    )
    allowed_arms = {
        *contract["required_baseline_arm_ids"],
        *contract["required_comparison_arm_ids"],
        *contract["optional_experimental_arm_ids"],
    }
    if not isinstance(arm_id, str) or arm_id not in allowed_arms:
        errors.append(f"{prefix}.arm_id")
        return None, None, {}
    seed = run.get("seed")
    task_order_id = run.get("task_order_id")
    if seed not in contract["required_seeds"]:
        errors.append(f"{prefix}.seed")
    if task_order_id not in contract["required_task_order_ids"]:
        errors.append(f"{prefix}.task_order_id")
    cell = (
        (seed, task_order_id)
        if seed in contract["required_seeds"]
        and task_order_id in contract["required_task_order_ids"]
        else None
    )
    if run.get("execution_status") != "producer_declared_native_unverified":
        errors.append(f"{prefix}.execution_status")
    expected_class = contract["persistence_classes"][arm_id]
    if run.get("persistence_class") != expected_class:
        errors.append(f"{prefix}.persistence_class")
    for field in (
        "implementation_sha256",
        "arm_configuration_sha256",
        "artifact_manifest_sha256",
    ):
        if not _sha256(run.get(field)):
            errors.append(f"{prefix}.{field}")
    if run.get("starting_state_sha256") != starting_checkpoint_sha256:
        errors.append(f"{prefix}.starting_state_sha256")
    post_state = run.get("post_update_state_sha256")
    restart_state = run.get("restart_loaded_state_sha256")
    if not _sha256(post_state) or not _sha256(restart_state):
        errors.append(f"{prefix}.state_hashes")
    if expected_class == "persistent_state":
        if post_state == starting_checkpoint_sha256:
            errors.append(f"{prefix}.unchanged_persistent_state")
        if restart_state != post_state:
            errors.append(f"{prefix}.restart_state_binding")
    elif (
        post_state != starting_checkpoint_sha256
        or restart_state != starting_checkpoint_sha256
    ):
        errors.append(f"{prefix}.nonpersistent_state_mutation")

    update_process = run.get("update_process_id")
    evaluation_process = run.get("evaluation_process_id")
    if (
        not _nonempty(update_process)
        or not _nonempty(evaluation_process)
        or update_process == evaluation_process
    ):
        errors.append(f"{prefix}.process_restart")
    for process_id in (update_process, evaluation_process):
        if _nonempty(process_id):
            if process_id in process_ids:
                errors.append(f"{prefix}.duplicate_process_id")
            process_ids.add(process_id)

    expected_source_context = arm_id == "context_only"
    expected_retrieval = arm_id == "retrieval"
    if run.get("source_context_present") is not expected_source_context:
        errors.append(f"{prefix}.source_context_present")
    if run.get("retrieval_enabled") is not expected_retrieval:
        errors.append(f"{prefix}.retrieval_enabled")
    source_context_count = run.get("source_context_item_count")
    retrieval_payload_count = run.get("retrieval_payload_count")
    if (
        not isinstance(source_context_count, int)
        or isinstance(source_context_count, bool)
        or source_context_count < 0
    ):
        errors.append(f"{prefix}.source_context_item_count")
    if (
        not isinstance(retrieval_payload_count, int)
        or isinstance(retrieval_payload_count, bool)
        or retrieval_payload_count < 0
    ):
        errors.append(f"{prefix}.retrieval_payload_count")
    committed_source_hashes = sorted(
        {
            source_hash
            for query in query_index.values()
            for source_hash in _list(query.get("dependency_source_sha256s"))
            if _sha256(source_hash)
        }
    )
    retrieval_payloads = [
        {
            "query_id": query_id,
            "dependency_source_sha256s": query_index[query_id].get(
                "dependency_source_sha256s"
            ),
        }
        for query_id in sorted(query_index)
    ]
    expected_source_count = (
        len(committed_source_hashes) if arm_id == "context_only" else 0
    )
    expected_retrieval_count = len(retrieval_payloads) if arm_id == "retrieval" else 0
    if source_context_count != expected_source_count:
        errors.append(f"{prefix}.source_context_census")
    if retrieval_payload_count != expected_retrieval_count:
        errors.append(f"{prefix}.retrieval_payload_census")
    expected_source_manifest = (
        stable_hash(committed_source_hashes) if arm_id == "context_only" else None
    )
    expected_retrieval_manifest = (
        stable_hash(retrieval_payloads) if arm_id == "retrieval" else None
    )
    if run.get("source_context_manifest_sha256") != expected_source_manifest:
        errors.append(f"{prefix}.source_context_manifest_sha256")
    if run.get("retrieval_payload_manifest_sha256") != expected_retrieval_manifest:
        errors.append(f"{prefix}.retrieval_payload_manifest_sha256")
    expected_input_manifest = {
        "arm_id": arm_id,
        "query_ids": sorted(query_index),
        "source_context_item_count": source_context_count,
        "retrieval_payload_count": retrieval_payload_count,
        "source_context_manifest_sha256": run.get("source_context_manifest_sha256"),
        "retrieval_payload_manifest_sha256": run.get(
            "retrieval_payload_manifest_sha256"
        ),
    }
    if not _hash_matches(
        expected_input_manifest, run.get("evaluation_input_manifest_sha256")
    ):
        errors.append(f"{prefix}.evaluation_input_manifest_sha256")

    budget = _dict(run.get("update_budget"))
    _exact_keys(
        budget,
        {"update_tokens", "gradient_steps", "adapter_rank"},
        f"{prefix}.update_budget",
        errors,
    )
    for field in ("update_tokens", "gradient_steps", "adapter_rank"):
        value = budget.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{prefix}.update_budget.{field}")
    if expected_class == "persistent_state" and any(
        not isinstance(budget.get(field), int)
        or isinstance(budget.get(field), bool)
        or budget.get(field) <= 0
        for field in ("update_tokens", "gradient_steps", "adapter_rank")
    ):
        errors.append(f"{prefix}.persistent_budget_positive")
    if expected_class != "persistent_state" and any(
        budget.get(field) != 0
        for field in ("update_tokens", "gradient_steps", "adapter_rank")
    ):
        errors.append(f"{prefix}.nonpersistent_budget")

    observations = _list(run.get("observations"))
    if not _hash_matches(observations, run.get("observations_sha256")):
        errors.append(f"{prefix}.observations_sha256")
    observed_query_ids: set[str] = set()
    correct_total = 0
    correct_by_kind: Counter[str] = Counter()
    total_by_kind: Counter[str] = Counter()
    correct_by_eval: Counter[str] = Counter()
    total_by_eval: Counter[str] = Counter()
    correct_by_family: Counter[str] = Counter()
    total_by_family: Counter[str] = Counter()
    correct_by_family_eval: Counter[tuple[str, str]] = Counter()
    total_by_family_eval: Counter[tuple[str, str]] = Counter()
    for index, raw_observation in enumerate(observations):
        observation = _dict(raw_observation)
        observation_prefix = f"{prefix}.observations[{index}]"
        _exact_keys(
            observation,
            {"query_id", "expected_choice", "observed_choice"},
            observation_prefix,
            errors,
        )
        query_id = observation.get("query_id")
        if (
            not isinstance(query_id, str)
            or query_id not in query_index
            or query_id in observed_query_ids
        ):
            errors.append(f"{observation_prefix}.query_id")
            continue
        observed_query_ids.add(query_id)
        query = query_index[query_id]
        expected_choice = observation.get("expected_choice")
        observed_choice = observation.get("observed_choice")
        if expected_choice != query["expected_choice"]:
            errors.append(f"{observation_prefix}.expected_choice")
        if (
            not isinstance(observed_choice, int)
            or isinstance(observed_choice, bool)
            or not 0 <= observed_choice < contract["choice_count"]
        ):
            errors.append(f"{observation_prefix}.observed_choice")
            continue
        fact_kind = query_fact_kind[query_id]
        family_id = query_family_id[query_id]
        eval_kind = query["evaluation_kind"]
        is_correct = observed_choice == query["expected_choice"]
        correct_total += int(is_correct)
        correct_by_kind[fact_kind] += int(is_correct)
        total_by_kind[fact_kind] += 1
        correct_by_eval[eval_kind] += int(is_correct)
        total_by_eval[eval_kind] += 1
        correct_by_family[family_id] += int(is_correct)
        total_by_family[family_id] += 1
        correct_by_family_eval[(family_id, eval_kind)] += int(is_correct)
        total_by_family_eval[(family_id, eval_kind)] += 1
    if observed_query_ids != set(query_index):
        errors.append(f"{prefix}.observation_census")
    metrics = {
        "overall_accuracy": _accuracy(correct_total, len(query_index)),
        "accuracy_by_fact_kind": {
            kind: _accuracy(correct_by_kind[kind], total_by_kind[kind])
            for kind in contract["required_fact_kinds"]
        },
        "accuracy_by_evaluation_kind": {
            kind: _accuracy(correct_by_eval[kind], total_by_eval[kind])
            for kind in contract["required_evaluation_kinds"]
        },
        "accuracy_by_family": {
            family_id: _accuracy(
                correct_by_family[family_id], total_by_family[family_id]
            )
            for family_id in sorted(set(query_family_id.values()))
        },
        "accuracy_by_family_and_evaluation_kind": {
            family_id: {
                eval_kind: _accuracy(
                    correct_by_family_eval[(family_id, eval_kind)],
                    total_by_family_eval[(family_id, eval_kind)],
                )
                for eval_kind in contract["required_evaluation_kinds"]
            }
            for family_id in sorted(set(query_family_id.values()))
        },
    }
    return arm_id, cell, metrics


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 10) if values else 0.0


def _aggregate_metrics(
    cells: dict[tuple[int, str], dict[str, Any]], contract: dict[str, Any]
) -> dict[str, Any]:
    metrics = list(cells.values())
    return {
        "overall_accuracy": _mean([row["overall_accuracy"] for row in metrics]),
        "accuracy_by_fact_kind": {
            fact_kind: _mean(
                [row["accuracy_by_fact_kind"][fact_kind] for row in metrics]
            )
            for fact_kind in contract["required_fact_kinds"]
        },
        "accuracy_by_evaluation_kind": {
            eval_kind: _mean(
                [row["accuracy_by_evaluation_kind"][eval_kind] for row in metrics]
            )
            for eval_kind in contract["required_evaluation_kinds"]
        },
        "accuracy_by_family": {
            family_id: _mean([row["accuracy_by_family"][family_id] for row in metrics])
            for family_id in sorted(metrics[0]["accuracy_by_family"] if metrics else {})
        },
    }


def _per_cell_family_cluster_interval(
    values: dict[tuple[tuple[int, str], str], float],
    contract: dict[str, Any],
    comparison_count: int,
    *,
    two_sided: bool = False,
) -> dict[str, Any]:
    policy = contract["statistics"]
    if not values or comparison_count <= 0:
        raise ValueError("family cluster intervals require populated values")
    calibrated_comparison_limit = policy[
        "critical_value_maximum_two_sided_comparisons"
        if two_sided
        else "critical_value_maximum_one_sided_comparisons"
    ]
    if comparison_count > calibrated_comparison_limit:
        raise ValueError("comparison count exceeds critical-value calibration")
    cell_ids = sorted({cell_id for cell_id, _ in values})
    adjusted_alpha = policy["familywise_alpha"] / comparison_count
    critical_value = policy["minimum_student_t_critical_value"]
    cell_intervals: dict[str, dict[str, Any]] = {}
    for seed, task_order_id in cell_ids:
        family_values = [
            value
            for (cell_id, _), value in values.items()
            if cell_id == (seed, task_order_id)
        ]
        if len(family_values) < policy["minimum_family_clusters_per_interval"]:
            raise ValueError("insufficient family clusters for interval")
        mean = _mean(family_values)
        standard_error = statistics.stdev(family_values) / len(family_values) ** 0.5
        margin = critical_value * standard_error
        cell_intervals[f"{seed}:{task_order_id}"] = {
            "mean": round(mean, 10),
            "lower_bound": round(mean - margin, 10),
            "upper_bound": round(mean + margin, 10),
            "family_cluster_count": len(family_values),
            "standard_error": round(standard_error, 10),
        }
    return {
        "mean": round(_mean(list(values.values())), 10),
        "bonferroni_adjusted_lower_bound": min(
            interval["lower_bound"] for interval in cell_intervals.values()
        ),
        "bonferroni_adjusted_upper_bound": max(
            interval["upper_bound"] for interval in cell_intervals.values()
        ),
        "adjusted_alpha": round(adjusted_alpha, 10),
        "minimum_student_t_critical_value": critical_value,
        "cell_intervals": cell_intervals,
        "interval_method": policy["interval_method"],
        "two_sided": two_sided,
        "multiplicity_policy": policy["multiplicity_policy"],
    }


def _paired_per_cell_family_cluster_interval(
    candidate_cells: dict[tuple[int, str], dict[str, Any]],
    no_update_cells: dict[tuple[int, str], dict[str, Any]],
    contract: dict[str, Any],
    comparison_count: int,
) -> dict[str, Any]:
    differences = {
        (cell_id, family_id): (
            candidate_cells[cell_id]["accuracy_by_family"][family_id]
            - no_update_cells[cell_id]["accuracy_by_family"][family_id]
        )
        for cell_id in sorted(candidate_cells)
        for family_id in sorted(candidate_cells[cell_id]["accuracy_by_family"])
    }
    summary = _per_cell_family_cluster_interval(differences, contract, comparison_count)
    summary["mean_paired_gain"] = summary.pop("mean")
    return summary


def validate_packet(packet: dict[str, Any] | None) -> dict[str, Any]:
    contract = protocol()
    if packet is None:
        report = {
            "version": "astral.rgs_acquisition_v28.validation.v1",
            "state_slice": contract["state_slice"],
            "status": "NotRun",
            "errors": [],
            "open_gates": ["acquisition.packet_not_supplied"],
            "gate_state": {
                "acquisition": "NotRun",
                "retention_recovery": "NotRunAcquisitionAbsent",
                "selection": "NotAuthorizedAcquisitionAbsent",
            },
            "claim_boundary": _claim_boundary(contract),
        }
        report["report_sha256"] = stable_hash(report)
        return report

    if not isinstance(packet, dict):
        report = {
            "version": "astral.rgs_acquisition_v28.validation.v1",
            "state_slice": contract["state_slice"],
            "protocol_state_slice": contract["packet_state_slice"],
            "status": "Invalid",
            "errors": ["packet.object"],
            "open_gates": [],
            "gate_state": {
                "acquisition": "Invalid",
                "retention_recovery": "NotRunAcquisitionUnqualified",
                "selection": "NotAuthorizedRetentionRecoveryAbsent",
                "assessment": "SealedNotAuthorized",
            },
            "claim_boundary": _claim_boundary(contract),
        }
        report["report_sha256"] = stable_hash(report)
        return report

    errors: list[str] = []
    _exact_keys(
        packet,
        {
            "version",
            "state_slice",
            "provenance",
            "corpus",
            "runs",
            "retention_recovery",
            "selection",
            "assessment",
            "claim_boundary",
            "packet_sha256",
        },
        "packet",
        errors,
    )
    if packet.get("version") != contract["packet_version"]:
        errors.append("packet.version")
    if packet.get("state_slice") != contract["packet_state_slice"]:
        errors.append("packet.state_slice")
    supplied_digest = packet.get("packet_sha256")
    unsealed = dict(packet)
    unsealed.pop("packet_sha256", None)
    if not _hash_matches(unsealed, supplied_digest):
        errors.append("packet.packet_sha256")
    for prohibited in ("retention_recovery", "selection", "assessment"):
        if packet.get(prohibited) is not None:
            errors.append(f"packet.{prohibited}_must_be_absent")
    claims = _dict(packet.get("claim_boundary"))
    if set(claims) != set(contract["required_false_claims"]):
        errors.append("claim_boundary.field_census")
    for claim in contract["required_false_claims"]:
        if claims.get(claim) is not False:
            errors.append(f"claim_boundary.{claim}")

    checkpoint = _validate_provenance(packet, errors)
    query_index, query_fact_kind, query_family_id = _validate_corpus(
        packet, contract, errors
    )
    family_fact_kind = {
        family_id: query_fact_kind[query_id]
        for query_id, family_id in query_family_id.items()
    }
    raw_runs = _list(packet.get("runs"))
    process_ids: set[str] = set()
    run_metrics: dict[str, dict[tuple[int, str], dict[str, Any]]] = defaultdict(dict)
    run_budgets: dict[str, dict[tuple[int, str], dict[str, Any]]] = defaultdict(dict)
    observation_hashes: dict[str, dict[tuple[int, str], str]] = defaultdict(dict)
    implementation_ids: dict[str, set[str]] = defaultdict(set)
    configuration_ids: dict[str, set[str]] = defaultdict(set)
    artifact_manifests: set[str] = set()
    persistent_state_signatures: set[tuple[str, str, str]] = set()
    for raw_run in raw_runs:
        run = _dict(raw_run)
        arm_id, cell, metrics = _validate_run(
            run,
            contract,
            checkpoint,
            query_index,
            query_fact_kind,
            query_family_id,
            process_ids,
            errors,
        )
        if arm_id is None or cell is None:
            continue
        if cell in run_metrics[arm_id]:
            errors.append(f"runs.duplicate_cell.{arm_id}")
            continue
        run_metrics[arm_id][cell] = metrics
        run_budgets[arm_id][cell] = _dict(run.get("update_budget"))
        observation_hashes[arm_id][cell] = run.get("observations_sha256")
        for field, target in (
            ("implementation_sha256", implementation_ids),
            ("arm_configuration_sha256", configuration_ids),
        ):
            value = run.get(field)
            if _sha256(value):
                target[arm_id].add(value)
        artifact_manifest = run.get("artifact_manifest_sha256")
        if _sha256(artifact_manifest):
            if artifact_manifest in artifact_manifests:
                errors.append("runs.duplicate_artifact_manifest")
            artifact_manifests.add(artifact_manifest)
        if arm_id in contract["persistent_arm_ids"]:
            signature = (
                run.get("post_update_state_sha256"),
                run.get("restart_loaded_state_sha256"),
                run.get("observations_sha256"),
            )
            if all(_sha256(value) for value in signature):
                if signature in persistent_state_signatures:
                    errors.append("runs.duplicate_persistent_state_output_signature")
                persistent_state_signatures.add(signature)

    baseline_ids = set(contract["required_baseline_arm_ids"])
    comparison_ids = set(contract["required_comparison_arm_ids"])
    optional_ids = set(contract["optional_experimental_arm_ids"])
    observed_ids = set(run_metrics)
    expected_cells = {
        (seed, order_id)
        for seed in contract["required_seeds"]
        for order_id in contract["required_task_order_ids"]
    }
    cell_matrix_complete = True
    for arm_id, cells in run_metrics.items():
        if set(cells) != expected_cells:
            errors.append(f"runs.cell_census.{arm_id}")
            cell_matrix_complete = False
        if len(implementation_ids[arm_id]) != 1:
            errors.append(f"runs.implementation_identity.{arm_id}")
        if len(configuration_ids[arm_id]) != 1:
            errors.append(f"runs.configuration_identity.{arm_id}")
    if not baseline_ids.issubset(observed_ids):
        errors.append("runs.baseline_census")
    extra_ids = observed_ids - baseline_ids
    full_comparison = comparison_ids.issubset(observed_ids)
    if extra_ids and not full_comparison:
        errors.append("runs.partial_comparison_census")
    if observed_ids - baseline_ids - comparison_ids - optional_ids:
        errors.append("runs.unexpected_arm")
    persistent_observed = [
        arm_id for arm_id in contract["persistent_arm_ids"] if arm_id in run_budgets
    ]
    persistent_budgets = [
        budget
        for arm_id in persistent_observed
        for budget in run_budgets[arm_id].values()
    ]
    if persistent_budgets and any(
        budget != persistent_budgets[0] for budget in persistent_budgets[1:]
    ):
        errors.append("runs.persistent_budget_parity")
    persistent_implementations = [
        next(iter(implementation_ids[arm_id]))
        for arm_id in persistent_observed
        if len(implementation_ids[arm_id]) == 1
    ]
    if len(persistent_implementations) != len(set(persistent_implementations)):
        errors.append("runs.distinct_persistent_implementations")

    aggregate_metrics = {
        arm_id: _aggregate_metrics(cells, contract)
        for arm_id, cells in run_metrics.items()
        if cells
    }
    if baseline_ids.issubset(observation_hashes):
        for cell in expected_cells:
            if observation_hashes["pre_update"].get(cell) != observation_hashes[
                "no_update"
            ].get(cell):
                errors.append("runs.baseline_restart_prediction_parity")
                break

    novelty_passed = False
    baseline_lifts: dict[str, dict[str, Any]] = {}
    if baseline_ids.issubset(aggregate_metrics) and not errors:
        maximum_lift = contract["thresholds"][
            "maximum_absolute_baseline_chance_normalized_lift"
        ]
        novelty_comparison_count = (
            len(contract["required_baseline_arm_ids"])
            * (
                1
                + len(contract["required_evaluation_kinds"])
                + len(contract["required_fact_kinds"])
            )
            * len(expected_cells)
        )
        novelty_passed = True
        for arm_id in contract["required_baseline_arm_ids"]:
            metrics = aggregate_metrics[arm_id]
            lifts = {
                "overall": _chance_lift(
                    metrics["overall_accuracy"], contract["choice_count"]
                ),
                "by_fact_kind": {
                    fact_kind: _chance_lift(accuracy, contract["choice_count"])
                    for fact_kind, accuracy in metrics["accuracy_by_fact_kind"].items()
                },
                "by_evaluation_kind": {
                    eval_kind: _chance_lift(accuracy, contract["choice_count"])
                    for eval_kind, accuracy in metrics[
                        "accuracy_by_evaluation_kind"
                    ].items()
                },
            }
            cell_lifts = [
                _chance_lift(cell_metrics["overall_accuracy"], contract["choice_count"])
                for cell_metrics in run_metrics[arm_id].values()
            ]
            cell_fact_lifts = [
                _chance_lift(accuracy, contract["choice_count"])
                for cell_metrics in run_metrics[arm_id].values()
                for accuracy in cell_metrics["accuracy_by_fact_kind"].values()
            ]
            evaluation_kind_lifts = [
                lift for lift in lifts["by_evaluation_kind"].values()
            ]
            cell_evaluation_kind_lifts = [
                _chance_lift(accuracy, contract["choice_count"])
                for cell_metrics in run_metrics[arm_id].values()
                for accuracy in cell_metrics["accuracy_by_evaluation_kind"].values()
            ]
            lifts["maximum_absolute_cell_overall"] = max(map(abs, cell_lifts))
            lifts["maximum_absolute_cell_fact_kind"] = max(map(abs, cell_fact_lifts))
            lifts["maximum_absolute_cell_evaluation_kind"] = max(
                map(abs, cell_evaluation_kind_lifts)
            )
            equivalence_intervals = {
                "overall": _per_cell_family_cluster_interval(
                    {
                        (cell_id, family_id): _chance_lift(
                            cell_metrics["accuracy_by_family"][family_id],
                            contract["choice_count"],
                        )
                        for cell_id, cell_metrics in run_metrics[arm_id].items()
                        for family_id in cell_metrics["accuracy_by_family"]
                    },
                    contract,
                    novelty_comparison_count,
                    two_sided=True,
                ),
                "by_evaluation_kind": {
                    eval_kind: _per_cell_family_cluster_interval(
                        {
                            (cell_id, family_id): _chance_lift(
                                cell_metrics["accuracy_by_family_and_evaluation_kind"][
                                    family_id
                                ][eval_kind],
                                contract["choice_count"],
                            )
                            for cell_id, cell_metrics in run_metrics[arm_id].items()
                            for family_id in cell_metrics["accuracy_by_family"]
                        },
                        contract,
                        novelty_comparison_count,
                        two_sided=True,
                    )
                    for eval_kind in contract["required_evaluation_kinds"]
                },
                "by_fact_kind": {
                    fact_kind: _per_cell_family_cluster_interval(
                        {
                            (cell_id, family_id): _chance_lift(
                                cell_metrics["accuracy_by_family"][family_id],
                                contract["choice_count"],
                            )
                            for cell_id, cell_metrics in run_metrics[arm_id].items()
                            for family_id in cell_metrics["accuracy_by_family"]
                            if family_fact_kind.get(family_id) == fact_kind
                        },
                        contract,
                        novelty_comparison_count,
                        two_sided=True,
                    )
                    for fact_kind in contract["required_fact_kinds"]
                },
            }
            lifts["equivalence_intervals"] = equivalence_intervals
            all_equivalence_intervals = [
                equivalence_intervals["overall"],
                *equivalence_intervals["by_evaluation_kind"].values(),
                *equivalence_intervals["by_fact_kind"].values(),
            ]
            lifts["equivalence_passed"] = all(
                interval["bonferroni_adjusted_lower_bound"] >= -maximum_lift
                and interval["bonferroni_adjusted_upper_bound"] <= maximum_lift
                for interval in all_equivalence_intervals
            )
            baseline_lifts[arm_id] = lifts
            if (
                abs(lifts["overall"]) > maximum_lift
                or any(
                    abs(lift) > maximum_lift for lift in lifts["by_fact_kind"].values()
                )
                or any(abs(lift) > maximum_lift for lift in cell_lifts)
                or any(abs(lift) > maximum_lift for lift in cell_fact_lifts)
                or any(abs(lift) > maximum_lift for lift in evaluation_kind_lifts)
                or any(abs(lift) > maximum_lift for lift in cell_evaluation_kind_lifts)
                or not lifts["equivalence_passed"]
            ):
                novelty_passed = False
    if not novelty_passed and extra_ids:
        errors.append("gate_order.update_arms_present_after_novelty_failure")
    update_order = _dict(packet.get("provenance")).get("update_outcomes_order")
    if full_comparison and update_order is None:
        errors.append("provenance.update_outcomes_order_missing")
    if not full_comparison and update_order is not None:
        errors.append("provenance.update_outcomes_order_without_comparison")

    threshold_passing_arms: list[str] = []
    acquisition_metrics: dict[str, dict[str, Any]] = {}
    if (
        novelty_passed
        and full_comparison
        and cell_matrix_complete
        and not errors
        and "no_update" in aggregate_metrics
    ):
        no_update_accuracy = aggregate_metrics["no_update"]["overall_accuracy"]
        retrieval_accuracy = aggregate_metrics["retrieval"]["overall_accuracy"]
        thresholds = contract["thresholds"]
        statistical_comparison_count = (
            len(persistent_observed)
            * (
                2
                + len(contract["required_evaluation_kinds"])
                + len(contract["required_fact_kinds"])
            )
            * len(expected_cells)
        )
        for arm_id in contract["persistent_arm_ids"]:
            if arm_id not in aggregate_metrics:
                continue
            metrics = dict(aggregate_metrics[arm_id])
            gain = round(metrics["overall_accuracy"] - no_update_accuracy, 10)
            paired_interval = _paired_per_cell_family_cluster_interval(
                run_metrics[arm_id],
                run_metrics["no_update"],
                contract,
                statistical_comparison_count,
            )
            absolute_intervals = {
                "overall": _per_cell_family_cluster_interval(
                    {
                        (cell_id, family_id): cell_metrics["accuracy_by_family"][
                            family_id
                        ]
                        for cell_id, cell_metrics in run_metrics[arm_id].items()
                        for family_id in cell_metrics["accuracy_by_family"]
                    },
                    contract,
                    statistical_comparison_count,
                ),
                "by_evaluation_kind": {
                    eval_kind: _per_cell_family_cluster_interval(
                        {
                            (cell_id, family_id): cell_metrics[
                                "accuracy_by_family_and_evaluation_kind"
                            ][family_id][eval_kind]
                            for cell_id, cell_metrics in run_metrics[arm_id].items()
                            for family_id in cell_metrics["accuracy_by_family"]
                        },
                        contract,
                        statistical_comparison_count,
                    )
                    for eval_kind in contract["required_evaluation_kinds"]
                },
                "by_fact_kind": {
                    fact_kind: _per_cell_family_cluster_interval(
                        {
                            (cell_id, family_id): cell_metrics["accuracy_by_family"][
                                family_id
                            ]
                            for cell_id, cell_metrics in run_metrics[arm_id].items()
                            for family_id in cell_metrics["accuracy_by_family"]
                            if family_fact_kind.get(family_id) == fact_kind
                        },
                        contract,
                        statistical_comparison_count,
                    )
                    for fact_kind in contract["required_fact_kinds"]
                },
            }
            cell_hard_floors_passed = all(
                cell_metrics["overall_accuracy"]
                >= thresholds["minimum_persistent_overall_accuracy"]
                and min(cell_metrics["accuracy_by_evaluation_kind"].values())
                >= thresholds["minimum_persistent_accuracy_per_evaluation_kind"]
                and min(cell_metrics["accuracy_by_fact_kind"].values())
                >= thresholds["minimum_persistent_accuracy_per_fact_kind"]
                and (
                    cell_metrics["overall_accuracy"]
                    - run_metrics["no_update"][cell_id]["overall_accuracy"]
                )
                >= thresholds["minimum_gain_over_no_update"]
                for cell_id, cell_metrics in run_metrics[arm_id].items()
            )
            qualifies = (
                metrics["overall_accuracy"]
                >= thresholds["minimum_persistent_overall_accuracy"]
                and min(metrics["accuracy_by_evaluation_kind"].values())
                >= thresholds["minimum_persistent_accuracy_per_evaluation_kind"]
                and min(metrics["accuracy_by_fact_kind"].values())
                >= thresholds["minimum_persistent_accuracy_per_fact_kind"]
                and gain >= thresholds["minimum_gain_over_no_update"]
                and cell_hard_floors_passed
                and absolute_intervals["overall"]["bonferroni_adjusted_lower_bound"]
                >= thresholds["minimum_persistent_overall_accuracy"]
                and min(
                    summary["bonferroni_adjusted_lower_bound"]
                    for summary in absolute_intervals["by_evaluation_kind"].values()
                )
                >= thresholds["minimum_persistent_accuracy_per_evaluation_kind"]
                and min(
                    summary["bonferroni_adjusted_lower_bound"]
                    for summary in absolute_intervals["by_fact_kind"].values()
                )
                >= thresholds["minimum_persistent_accuracy_per_fact_kind"]
                and paired_interval["bonferroni_adjusted_lower_bound"]
                > contract["statistics"]["minimum_paired_gain_lower_bound"]
            )
            metrics["gain_over_no_update"] = gain
            metrics["delta_from_retrieval"] = round(
                metrics["overall_accuracy"] - retrieval_accuracy, 10
            )
            metrics["paired_per_cell_family_cluster_interval"] = paired_interval
            metrics["absolute_acquisition_clustered_intervals"] = absolute_intervals
            metrics["cell_hard_floors_passed"] = cell_hard_floors_passed
            metrics["passes_packet_gate_1_thresholds"] = qualifies
            acquisition_metrics[arm_id] = metrics
            if qualifies:
                threshold_passing_arms.append(arm_id)

    if errors:
        status = "Invalid"
        acquisition_state = "Invalid"
        open_gates: list[str] = []
    elif not novelty_passed:
        status = "CorpusNotNovel"
        acquisition_state = "StoppedBeforeUpdates"
        open_gates = ["acquisition.new_corpus_required"]
    elif not full_comparison:
        status = "NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun"
        acquisition_state = "NoveltyPacketCandidateArtifactVerificationNotRun"
        open_gates = [
            "acquisition.artifact_bytes_not_verified",
            "acquisition.complete_comparison_not_supplied",
        ]
    elif (
        len(threshold_passing_arms)
        < contract["thresholds"]["minimum_packet_threshold_passing_persistent_arms"]
    ):
        status = "AcquisitionPacketNoCandidateUnverified"
        acquisition_state = "InsufficientPacketThresholdPassingPersistentArms"
        open_gates = [
            "acquisition.requires_two_packet_threshold_passing_persistent_arms"
        ]
    else:
        status = "AcquisitionPacketCandidateUnverified"
        acquisition_state = "PacketCandidateArtifactVerificationNotRun"
        open_gates = [
            "acquisition.artifact_bytes_not_verified",
            "retention_recovery.not_authorized",
            "selection.not_authorized",
        ]

    report = {
        "version": "astral.rgs_acquisition_v28.validation.v1",
        "state_slice": contract["state_slice"],
        "protocol_state_slice": contract["packet_state_slice"],
        "status": status,
        "errors": errors,
        "open_gates": open_gates,
        "baseline_metrics": {
            arm_id: aggregate_metrics[arm_id]
            for arm_id in contract["required_baseline_arm_ids"]
            if arm_id in aggregate_metrics
        },
        "baseline_chance_normalized_lifts": baseline_lifts,
        "nonpersistent_comparison_metrics": {
            arm_id: aggregate_metrics[arm_id]
            for arm_id in ("context_only", "retrieval")
            if arm_id in aggregate_metrics
        },
        "acquisition_metrics": acquisition_metrics,
        "statistical_policy": contract["statistics"],
        "packet_threshold_passing_persistent_arm_ids": threshold_passing_arms,
        "gate_state": {
            "acquisition": acquisition_state,
            "retention_recovery": (
                "NotAuthorizedArtifactVerificationAbsent"
                if status == "AcquisitionPacketCandidateUnverified"
                else "NotRunAcquisitionUnqualified"
            ),
            "selection": "NotAuthorizedRetentionRecoveryAbsent",
            "assessment": "SealedNotAuthorized",
        },
        "claim_boundary": _claim_boundary(contract),
    }
    report["report_sha256"] = stable_hash(report)
    return report


def _claim_boundary(contract: dict[str, Any]) -> dict[str, bool]:
    return {
        "local_acquisition_validator": True,
        **{claim: False for claim in contract["required_false_claims"]},
    }
