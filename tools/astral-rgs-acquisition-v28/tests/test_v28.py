from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v28", HERE / "v28.py")
assert SPEC and SPEC.loader
V28 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V28)


def test_missing_packet_is_explicit_not_run() -> None:
    report = V28.validate_packet(None)

    assert report["status"] == "NotRun"
    assert report["open_gates"] == ["acquisition.packet_not_supplied"]
    assert report["gate_state"]["selection"] == "NotAuthorizedAcquisitionAbsent"


def test_non_object_packet_is_invalid_not_exception() -> None:
    report = V28.validate_packet([])  # type: ignore[arg-type]

    assert report["status"] == "Invalid"
    assert report["errors"] == ["packet.object"]


def test_operator_cli_writes_the_recomputed_report(tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.json"
    output_path = tmp_path / "report.json"
    packet_path.write_text(
        json.dumps(_packet(full=False), sort_keys=True) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(HERE / "validate_packet.py"),
            "--packet",
            str(packet_path),
            "--output",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert (
        "status=NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun"
        in completed.stdout
    )
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == (
        "NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun"
    )


def test_operator_cli_fails_closed_for_json_null_packet(tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.json"
    output_path = tmp_path / "report.json"
    packet_path.write_text("null\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(HERE / "validate_packet.py"),
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


def test_low_baselines_and_two_persistent_arms_qualify_gate_1() -> None:
    report = V28.validate_packet(_packet(full=True))

    assert report["status"] == "AcquisitionPacketCandidateUnverified"
    assert report["errors"] == []
    assert report["packet_threshold_passing_persistent_arm_ids"] == [
        "naive_sequential_lora",
        "replay",
        "scol_style_consolidation",
    ]
    assert (
        report["gate_state"]["retention_recovery"]
        == "NotAuthorizedArtifactVerificationAbsent"
    )
    assert report["gate_state"]["selection"] == "NotAuthorizedRetentionRecoveryAbsent"
    assert set(report["nonpersistent_comparison_metrics"]) == {
        "context_only",
        "retrieval",
    }
    assert (
        report["acquisition_metrics"]["replay"][
            "paired_per_cell_family_cluster_interval"
        ]["interval_method"]
        == "per_seed_order_family_cluster_student_t_interval"
    )
    assert all(
        report["baseline_chance_normalized_lifts"][arm_id]["equivalence_passed"]
        for arm_id in ("pre_update", "no_update")
    )
    assert all(
        value is False
        for key, value in report["claim_boundary"].items()
        if key != "local_acquisition_validator"
    )


def test_validation_and_per_cell_cluster_intervals_are_deterministic() -> None:
    packet = _packet(full=True)

    first = V28.validate_packet(packet)
    second = V28.validate_packet(packet)

    assert first == second
    assert all(
        metrics["paired_per_cell_family_cluster_interval"]["two_sided"] is False
        for metrics in first["acquisition_metrics"].values()
    )


def test_no_update_at_one_stops_before_update_comparison() -> None:
    packet = _packet(full=False, baseline_accuracy=1.0)
    report = V28.validate_packet(packet)

    assert report["status"] == "CorpusNotNovel"
    assert report["errors"] == []
    assert report["gate_state"]["acquisition"] == "StoppedBeforeUpdates"
    assert report["acquisition_metrics"] == {}


def test_update_outcomes_after_failed_novelty_gate_are_invalid() -> None:
    packet = _packet(full=True, baseline_accuracy=1.0)
    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "gate_order.update_arms_present_after_novelty_failure" in report["errors"]


def test_novel_baseline_only_packet_keeps_comparison_not_run() -> None:
    report = V28.validate_packet(_packet(full=False))

    assert report["status"] == "NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun"
    assert report["gate_state"]["retention_recovery"] == "NotRunAcquisitionUnqualified"


def test_checkpoint_must_precede_seed_and_corpus_generation() -> None:
    packet = _packet(full=False)
    packet["provenance"]["seed_committed_order"] = 0
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "provenance.ordering" in report["errors"]


def test_packet_binds_protocol_slice_not_validator_slice() -> None:
    packet = _packet(full=False)
    packet["state_slice"] = V28.protocol()["state_slice"]
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "packet.state_slice" in report["errors"]


def test_persistent_arm_rejects_source_context_leakage() -> None:
    packet = _packet(full=True)
    _run(packet, "naive_sequential_lora")["source_context_present"] = True
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "runs.naive_sequential_lora.source_context_present" in report["errors"]


def test_training_form_prompt_overlap_is_invalid() -> None:
    packet = _packet(full=False)
    item = packet["corpus"]["items"][0]
    item["queries"][0]["prompt_sha256"] = item["source_form_sha256"]
    packet["corpus"]["manifest_sha256"] = V28.stable_hash(packet["corpus"]["items"])
    packet["provenance"]["corpus_manifest_sha256"] = packet["corpus"]["manifest_sha256"]
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert any(error.endswith("training_form_overlap") for error in report["errors"])


def test_cross_item_training_form_overlap_is_invalid() -> None:
    packet = _packet(full=False)
    items = packet["corpus"]["items"]
    items[0]["queries"][0]["prompt_sha256"] = items[1]["source_form_sha256"]
    packet["corpus"]["manifest_sha256"] = V28.stable_hash(items)
    packet["provenance"]["corpus_manifest_sha256"] = packet["corpus"]["manifest_sha256"]
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "corpus.global_training_form_overlap" in report["errors"]


def test_query_semantics_require_committed_dependencies() -> None:
    packet = _packet(full=False)
    query = packet["corpus"]["items"][0]["queries"][4]
    query["dependency_source_sha256s"] = query["dependency_source_sha256s"][:1]
    query["derivation_manifest_sha256"] = V28.stable_hash(
        {
            "item_id": packet["corpus"]["items"][0]["item_id"],
            "family_id": packet["corpus"]["items"][0]["family_id"],
            "query_id": query["query_id"],
            "evaluation_kind": query["evaluation_kind"],
            "prompt_sha256": query["prompt_sha256"],
            "template_family_id": query["template_family_id"],
            "dependency_source_sha256s": query["dependency_source_sha256s"],
            "expected_choice": query["expected_choice"],
            "withheld_from_training": query["withheld_from_training"],
        }
    )
    packet["corpus"]["manifest_sha256"] = V28.stable_hash(packet["corpus"]["items"])
    packet["provenance"]["corpus_manifest_sha256"] = packet["corpus"]["manifest_sha256"]
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert any(
        error.endswith("dependency_source_sha256s") for error in report["errors"]
    )


def test_derivation_manifest_binds_prompt_and_family_identity() -> None:
    packet = _packet(full=False)
    query = packet["corpus"]["items"][0]["queries"][0]
    query["prompt_sha256"] = V28.stable_hash("unrelated-prompt")
    packet["corpus"]["manifest_sha256"] = V28.stable_hash(packet["corpus"]["items"])
    packet["provenance"]["corpus_manifest_sha256"] = packet["corpus"]["manifest_sha256"]
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert any(
        error.endswith("derivation_manifest_sha256") for error in report["errors"]
    )


def test_same_process_is_not_a_restart() -> None:
    packet = _packet(full=False)
    run = _run(packet, "no_update")
    run["evaluation_process_id"] = run["update_process_id"]
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "runs.no_update.process_restart" in report["errors"]


def test_assessment_or_selector_material_is_rejected() -> None:
    packet = _packet(full=False)
    packet["selection"] = {"predictions": []}
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "packet.selection_must_be_absent" in report["errors"]


def test_rehashed_claim_overstatement_is_rejected() -> None:
    packet = _packet(full=False)
    packet["claim_boundary"]["model_backed_acquisition"] = True
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "claim_boundary.model_backed_acquisition" in report["errors"]


def test_partial_comparison_census_is_invalid() -> None:
    packet = _packet(full=True)
    packet["runs"] = [
        run for run in packet["runs"] if run["arm_id"] != "scol_style_consolidation"
    ]
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "runs.partial_comparison_census" in report["errors"]


def test_seed_order_cell_census_is_exact() -> None:
    packet = _packet(full=False)
    packet["runs"].remove(_runs(packet, "no_update")[0])
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "runs.cell_census.no_update" in report["errors"]


def test_pre_update_and_restart_predictions_must_match_row_for_row() -> None:
    packet = _packet(full=False)
    run = _runs(packet, "pre_update")[0]
    first = run["observations"][0]
    later = run["observations"][100]
    first["observed_choice"] = (first["expected_choice"] + 1) % 4
    later["observed_choice"] = later["expected_choice"]
    run["observations_sha256"] = V28.stable_hash(run["observations"])
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "runs.baseline_restart_prediction_parity" in report["errors"]


def test_persistent_arms_bind_distinct_implementations() -> None:
    packet = _packet(full=True)
    naive_implementation = _runs(packet, "naive_sequential_lora")[0][
        "implementation_sha256"
    ]
    for run in _runs(packet, "replay"):
        run["implementation_sha256"] = naive_implementation
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "runs.distinct_persistent_implementations" in report["errors"]


def test_complete_comparison_without_two_candidates_is_negative() -> None:
    packet = _packet(full=True)
    for arm_id in ("naive_sequential_lora", "replay", "scol_style_consolidation"):
        for run in _runs(packet, arm_id):
            for observation in run["observations"]:
                observation["observed_choice"] = (
                    observation["expected_choice"] + 1
                ) % 4
            run["observations_sha256"] = V28.stable_hash(run["observations"])
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "AcquisitionPacketNoCandidateUnverified"
    assert report["packet_threshold_passing_persistent_arm_ids"] == []
    assert report["gate_state"]["selection"] == "NotAuthorizedRetentionRecoveryAbsent"


def test_zero_accuracy_baseline_is_not_near_chance() -> None:
    report = V28.validate_packet(_packet(full=False, baseline_accuracy=0.0))

    assert report["status"] == "CorpusNotNovel"
    assert report["baseline_chance_normalized_lifts"]["no_update"]["overall"] < 0


def test_each_evaluation_kind_must_be_near_chance() -> None:
    packet = _packet(full=False)
    correct_limits = {0: 12, 1: 3, 2: 3}
    for arm_id in ("pre_update", "no_update"):
        for run in _runs(packet, arm_id):
            for observation in run["observations"]:
                _, _, item_position, eval_index, _ = observation["query_id"].split("-")
                expected = observation["expected_choice"]
                observation["observed_choice"] = (
                    expected
                    if int(item_position) < correct_limits[int(eval_index)]
                    else (expected + 1) % 4
                )
            run["observations_sha256"] = V28.stable_hash(run["observations"])
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "CorpusNotNovel"


def test_point_near_chance_without_equivalence_precision_is_not_novel() -> None:
    packet = _packet(full=False)
    for arm_id in ("pre_update", "no_update"):
        for run in _runs(packet, arm_id):
            for observation in run["observations"]:
                item_position = int(observation["query_id"].split("-")[2])
                observation["observed_choice"] = (
                    observation["expected_choice"]
                    if item_position < 6
                    else (observation["expected_choice"] + 1) % 4
                )
            run["observations_sha256"] = V28.stable_hash(run["observations"])
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "CorpusNotNovel"
    assert report["errors"] == []
    assert all(
        report["baseline_chance_normalized_lifts"][arm_id]["overall"] == 0.0
        for arm_id in ("pre_update", "no_update")
    )
    assert all(
        report["baseline_chance_normalized_lifts"][arm_id]["equivalence_passed"]
        is False
        for arm_id in ("pre_update", "no_update")
    )


def test_fixed_choice_bias_is_neutralized_within_every_family() -> None:
    packet = _packet(full=False)
    for arm_id in ("pre_update", "no_update"):
        for run in _runs(packet, arm_id):
            for observation in run["observations"]:
                observation["observed_choice"] = 0
            run["observations_sha256"] = V28.stable_hash(run["observations"])
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun"
    assert all(
        report["baseline_chance_normalized_lifts"][arm_id]["equivalence_passed"]
        for arm_id in ("pre_update", "no_update")
    )


def test_family_census_above_minimum_need_not_be_divisible_by_choice_count() -> None:
    report = V28.validate_packet(_packet(full=False, families_per_kind=25))

    assert report["status"] == "NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun"
    assert report["errors"] == []


def test_each_query_class_rotates_the_semantic_answer_through_all_positions() -> None:
    packet = _packet(full=False)
    item = packet["corpus"]["items"][0]
    query = item["queries"][1]
    expected_answer = query["expected_answer_sha256"]
    reordered = list(query["answer_option_sha256s"])
    expected_index = reordered.index(expected_answer)
    reordered[0], reordered[expected_index] = reordered[expected_index], reordered[0]
    query["expected_choice"] = 0
    query["answer_option_sha256s"] = reordered
    query["answer_mapping_sha256"] = V28.stable_hash(
        {
            "item_id": item["item_id"],
            "family_id": item["family_id"],
            "query_id": query["query_id"],
            "answer_option_sha256s": reordered,
            "expected_choice": 0,
            "expected_answer_sha256": expected_answer,
        }
    )
    query["derivation_manifest_sha256"] = V28.stable_hash(
        {
            "item_id": item["item_id"],
            "family_id": item["family_id"],
            "query_id": query["query_id"],
            "evaluation_kind": query["evaluation_kind"],
            "prompt_sha256": query["prompt_sha256"],
            "template_family_id": query["template_family_id"],
            "dependency_source_sha256s": query["dependency_source_sha256s"],
            "expected_choice": query["expected_choice"],
            "expected_answer_sha256": query["expected_answer_sha256"],
            "answer_mapping_sha256": query["answer_mapping_sha256"],
            "withheld_from_training": query["withheld_from_training"],
        }
    )
    packet["corpus"]["manifest_sha256"] = V28.stable_hash(packet["corpus"]["items"])
    packet["provenance"]["corpus_manifest_sha256"] = packet["corpus"]["manifest_sha256"]
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "corpus.items[0].answer_position_rotation.paraphrase" in report["errors"]


def test_persistent_arm_must_pass_every_fact_kind() -> None:
    packet = _packet(full=True)
    for run in _runs(packet, "naive_sequential_lora"):
        for observation in run["observations"]:
            if observation["query_id"].startswith("query-3-"):
                observation["observed_choice"] = (
                    observation["expected_choice"] + 1
                ) % 4
        run["observations_sha256"] = V28.stable_hash(run["observations"])
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "AcquisitionPacketCandidateUnverified"
    assert (
        report["acquisition_metrics"]["naive_sequential_lora"][
            "passes_packet_gate_1_thresholds"
        ]
        is False
    )


def test_nonfinite_packet_value_fails_closed() -> None:
    packet = _packet(full=False)
    packet["runs"][0]["observations"][0]["observed_choice"] = float("nan")

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "packet.packet_sha256" in report["errors"]
    assert "runs.pre_update.observations_sha256" in report["errors"]


def test_wrong_json_types_fail_closed() -> None:
    packet = _packet(full=False)
    packet["corpus"]["items"][0]["fact_kind"] = []
    packet["corpus"]["manifest_sha256"] = V28.stable_hash(packet["corpus"]["items"])
    packet["provenance"]["corpus_manifest_sha256"] = packet["corpus"]["manifest_sha256"]
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "corpus.items[0].fact_kind" in report["errors"]


def test_observation_tamper_without_resealing_is_rejected() -> None:
    packet = _packet(full=False)
    _run(packet, "no_update")["observations"][0]["observed_choice"] = 3

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "packet.packet_sha256" in report["errors"]
    assert "runs.no_update.observations_sha256" in report["errors"]


def test_context_only_requires_the_exact_committed_source_census() -> None:
    packet = _packet(full=True)
    run = _runs(packet, "context_only")[0]
    run["source_context_item_count"] -= 1
    run["evaluation_input_manifest_sha256"] = V28.stable_hash(
        {
            "arm_id": run["arm_id"],
            "query_ids": sorted(
                observation["query_id"] for observation in run["observations"]
            ),
            "source_context_item_count": run["source_context_item_count"],
            "retrieval_payload_count": run["retrieval_payload_count"],
            "source_context_manifest_sha256": run["source_context_manifest_sha256"],
            "retrieval_payload_manifest_sha256": run[
                "retrieval_payload_manifest_sha256"
            ],
        }
    )
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "runs.context_only.source_context_census" in report["errors"]


def test_query_answer_commitment_cannot_be_rebound_by_rehashing() -> None:
    packet = _packet(full=False)
    item = packet["corpus"]["items"][0]
    query = item["queries"][0]
    query["expected_answer_sha256"] = query["answer_option_sha256s"][
        (query["expected_choice"] + 1) % V28.protocol()["choice_count"]
    ]
    query["derivation_manifest_sha256"] = V28.stable_hash(
        {
            "item_id": item["item_id"],
            "family_id": item["family_id"],
            "query_id": query["query_id"],
            "evaluation_kind": query["evaluation_kind"],
            "prompt_sha256": query["prompt_sha256"],
            "template_family_id": query["template_family_id"],
            "dependency_source_sha256s": query["dependency_source_sha256s"],
            "expected_choice": query["expected_choice"],
            "expected_answer_sha256": query["expected_answer_sha256"],
            "answer_mapping_sha256": query["answer_mapping_sha256"],
            "withheld_from_training": query["withheld_from_training"],
        }
    )
    packet["corpus"]["manifest_sha256"] = V28.stable_hash(packet["corpus"]["items"])
    packet["provenance"]["corpus_manifest_sha256"] = packet["corpus"]["manifest_sha256"]
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)

    assert report["status"] == "Invalid"
    assert "corpus.items[0].queries[0].expected_answer_sha256" in report["errors"]


def test_per_cell_interval_exposes_a_seed_level_persistent_failure() -> None:
    packet = _packet(full=True)
    failed_seed = V28.protocol()["required_seeds"][0]
    for run in _runs(packet, "replay"):
        if run["seed"] != failed_seed:
            continue
        for observation in run["observations"]:
            item_position = int(observation["query_id"].split("-")[2])
            observation["observed_choice"] = (
                observation["expected_choice"]
                if item_position < 5
                else (observation["expected_choice"] + 1) % 4
            )
        run["observations_sha256"] = V28.stable_hash(run["observations"])
    packet = V28.seal_packet(packet)

    report = V28.validate_packet(packet)
    replay = report["acquisition_metrics"]["replay"]

    assert report["status"] == "AcquisitionPacketCandidateUnverified"
    assert replay["cell_hard_floors_passed"] is False
    assert (
        replay["paired_per_cell_family_cluster_interval"][
            "bonferroni_adjusted_lower_bound"
        ]
        <= 0.0
    )
    assert replay["passes_packet_gate_1_thresholds"] is False


def test_per_cell_interval_captures_balanced_crossed_interactions() -> None:
    contract = V28.protocol()
    values = {
        ((seed, order_id), f"family-{family_index:02d}"): (
            2.0 / 3.0 if (seed_index + order_index + family_index) % 3 == 0 else 1.0
        )
        for seed_index, seed in enumerate(contract["required_seeds"])
        for order_index, order_id in enumerate(contract["required_task_order_ids"])
        for family_index in range(
            contract["statistics"]["minimum_family_clusters_per_interval"]
        )
    }

    interval = V28._per_cell_family_cluster_interval(
        values,
        contract,
        comparison_count=324,
    )

    assert interval["bonferroni_adjusted_lower_bound"] < interval["mean"]
    assert all(
        cell["standard_error"] > 0.0 for cell in interval["cell_intervals"].values()
    )


def _packet(
    *,
    full: bool,
    baseline_accuracy: float = 0.25,
    families_per_kind: int | None = None,
) -> dict:
    contract = V28.protocol()
    checkpoint = V28.stable_hash("checkpoint")
    items = _items(contract, per_kind=families_per_kind)
    manifest = V28.stable_hash(items)
    provenance = {
        "starting_checkpoint_sha256": checkpoint,
        "protocol_sha256": V28.stable_hash(contract),
        "tokenizer_sha256": V28.stable_hash("tokenizer"),
        "runtime_sha256": V28.stable_hash("runtime"),
        "source_commit": "1" * 40,
        "source_tree": "2" * 40,
        "generator_sha256": V28.stable_hash("generator"),
        "generator_config_sha256": V28.stable_hash("generator-config"),
        "seed_commitment_sha256": V28.stable_hash("seed-commitment"),
        "corpus_manifest_sha256": manifest,
        "split_commitment_sha256": V28.stable_hash("splits"),
        "configuration_lock_sha256": V28.stable_hash("configuration-lock"),
        "future_assessment_family_commitment_sha256": V28.stable_hash(
            "future-assessment-families"
        ),
        "generator_checkpoint_sha256": checkpoint,
        "v27_data_reused": False,
        "model_output_guided_generation": False,
        "checkpoint_hashed_order": 1,
        "seed_committed_order": 2,
        "corpus_generated_order": 3,
        "configuration_locked_order": 4,
        "baseline_outcomes_order": 5,
        "update_outcomes_order": 6 if full else None,
    }
    packet = {
        "version": contract["packet_version"],
        "state_slice": contract["packet_state_slice"],
        "provenance": provenance,
        "corpus": {
            "choice_count": contract["choice_count"],
            "split": "qualification",
            "manifest_sha256": manifest,
            "items": items,
        },
        "runs": [
            *_make_runs("pre_update", items, checkpoint, baseline_accuracy, 0),
            *_make_runs("no_update", items, checkpoint, baseline_accuracy, 1),
        ],
        "retention_recovery": None,
        "selection": None,
        "assessment": None,
        "claim_boundary": {claim: False for claim in contract["required_false_claims"]},
    }
    if full:
        packet["runs"].extend(
            [
                *_make_runs("context_only", items, checkpoint, 0.95, 2),
                *_make_runs("retrieval", items, checkpoint, 0.95, 3),
                *_make_runs("naive_sequential_lora", items, checkpoint, 0.95, 4),
                *_make_runs("replay", items, checkpoint, 0.95, 5),
                *_make_runs("scol_style_consolidation", items, checkpoint, 1.0, 6),
            ]
        )
    return V28.seal_packet(packet)


def _items(contract: dict, *, per_kind: int | None = None) -> list[dict]:
    items = []
    per_kind = (
        contract["thresholds"]["minimum_families_per_fact_kind"]
        if per_kind is None
        else per_kind
    )
    for kind_index, fact_kind in enumerate(contract["required_fact_kinds"]):
        for item_index in range(per_kind):
            item_id = f"item-{kind_index}-{item_index:02d}"
            queries = []
            source_hash = V28.stable_hash(f"source:{item_id}")
            support_hash = V28.stable_hash(f"support:{item_id}")
            answer_options = [
                V28.stable_hash(f"answer:{item_id}:{position}")
                for position in range(contract["choice_count"])
            ]
            expected_answer_sha256 = answer_options[0]
            for eval_index, eval_kind in enumerate(
                contract["required_evaluation_kinds"]
            ):
                for variant_index in range(contract["queries_per_evaluation_kind"]):
                    query_id = (
                        f"query-{kind_index}-{item_index:02d}-{eval_index}-"
                        f"{variant_index}"
                    )
                    template_id = f"eval-template-{eval_index}-{variant_index}"
                    query_answer_options: list[str | None] = [
                        None for _ in range(contract["choice_count"])
                    ]
                    query_answer_options[variant_index] = expected_answer_sha256
                    distractors = iter(answer_options[1:])
                    for position in range(contract["choice_count"]):
                        if query_answer_options[position] is None:
                            query_answer_options[position] = next(distractors)
                    ordered_answer_options = [
                        str(value) for value in query_answer_options
                    ]
                    dependencies = (
                        [source_hash]
                        if eval_kind == "paraphrase"
                        else [source_hash, support_hash]
                    )
                    answer_mapping_sha256 = V28.stable_hash(
                        {
                            "item_id": item_id,
                            "family_id": f"family-{kind_index}-{item_index:02d}",
                            "query_id": query_id,
                            "answer_option_sha256s": ordered_answer_options,
                            "expected_choice": variant_index,
                            "expected_answer_sha256": expected_answer_sha256,
                        }
                    )
                    query = {
                        "query_id": query_id,
                        "evaluation_kind": eval_kind,
                        "prompt_sha256": V28.stable_hash(
                            f"prompt:{kind_index}:{item_index}:{eval_index}:"
                            f"{variant_index}"
                        ),
                        "expected_choice": variant_index,
                        "answer_option_sha256s": ordered_answer_options,
                        "expected_answer_sha256": expected_answer_sha256,
                        "answer_mapping_sha256": answer_mapping_sha256,
                        "template_family_id": template_id,
                        "dependency_source_sha256s": dependencies,
                        "withheld_from_training": True,
                    }
                    query["derivation_manifest_sha256"] = V28.stable_hash(
                        {
                            "item_id": item_id,
                            "family_id": f"family-{kind_index}-{item_index:02d}",
                            "query_id": query_id,
                            "evaluation_kind": eval_kind,
                            "prompt_sha256": query["prompt_sha256"],
                            "template_family_id": template_id,
                            "dependency_source_sha256s": dependencies,
                            "expected_choice": query["expected_choice"],
                            "expected_answer_sha256": query["expected_answer_sha256"],
                            "answer_mapping_sha256": query["answer_mapping_sha256"],
                            "withheld_from_training": True,
                        }
                    )
                    queries.append(query)
            items.append(
                {
                    "item_id": item_id,
                    "family_id": f"family-{kind_index}-{item_index:02d}",
                    "fact_kind": fact_kind,
                    "source_form_sha256": source_hash,
                    "support_source_sha256s": [support_hash],
                    "training_template_family_id": f"train-template-{kind_index}",
                    "answer_option_sha256s": answer_options,
                    "expected_answer_sha256": expected_answer_sha256,
                    "queries": queries,
                }
            )
    return items


def _make_runs(
    arm_id: str,
    items: list[dict],
    checkpoint: str,
    target_accuracy: float,
    process_index: int,
) -> list[dict]:
    contract = V28.protocol()
    return [
        _make_run(
            arm_id,
            items,
            checkpoint,
            target_accuracy,
            process_index,
            seed,
            task_order_id,
        )
        for seed in contract["required_seeds"]
        for task_order_id in contract["required_task_order_ids"]
    ]


def _make_run(
    arm_id: str,
    items: list[dict],
    checkpoint: str,
    target_accuracy: float,
    process_index: int,
    seed: int,
    task_order_id: str,
) -> dict:
    contract = V28.protocol()
    persistent = arm_id in contract["persistent_arm_ids"]
    post_state = (
        V28.stable_hash(f"state:{arm_id}:{seed}:{task_order_id}")
        if persistent
        else checkpoint
    )
    observations = []
    queries = [query for item in items for query in item["queries"]]
    correct_variants = round(contract["queries_per_evaluation_kind"] * target_accuracy)
    for query in queries:
        expected = query["expected_choice"]
        variant_index = int(query["query_id"].split("-")[4])
        observed = expected if variant_index < correct_variants else (expected + 1) % 4
        observations.append(
            {
                "query_id": query["query_id"],
                "expected_choice": expected,
                "observed_choice": observed,
            }
        )
    run = {
        "arm_id": arm_id,
        "seed": seed,
        "task_order_id": task_order_id,
        "execution_status": "producer_declared_native_unverified",
        "persistence_class": contract["persistence_classes"][arm_id],
        "implementation_sha256": V28.stable_hash(f"implementation:{arm_id}"),
        "arm_configuration_sha256": V28.stable_hash(f"configuration:{arm_id}"),
        "artifact_manifest_sha256": V28.stable_hash(
            f"artifact:{arm_id}:{seed}:{task_order_id}"
        ),
        "starting_state_sha256": checkpoint,
        "post_update_state_sha256": post_state,
        "restart_loaded_state_sha256": post_state,
        "update_process_id": f"process-update-{process_index}-{seed}-{task_order_id}",
        "evaluation_process_id": f"process-eval-{process_index}-{seed}-{task_order_id}",
        "source_context_present": arm_id == "context_only",
        "retrieval_enabled": arm_id == "retrieval",
        "source_context_item_count": 2 * len(items) if arm_id == "context_only" else 0,
        "retrieval_payload_count": len(queries) if arm_id == "retrieval" else 0,
        "update_budget": (
            {"update_tokens": 1000, "gradient_steps": 20, "adapter_rank": 8}
            if persistent
            else {"update_tokens": 0, "gradient_steps": 0, "adapter_rank": 0}
        ),
        "observations": observations,
    }
    committed_source_hashes = sorted(
        {
            source_hash
            for query in queries
            for source_hash in query["dependency_source_sha256s"]
        }
    )
    retrieval_payloads = [
        {
            "query_id": query["query_id"],
            "dependency_source_sha256s": query["dependency_source_sha256s"],
        }
        for query in sorted(queries, key=lambda value: value["query_id"])
    ]
    run["source_context_manifest_sha256"] = (
        V28.stable_hash(committed_source_hashes) if arm_id == "context_only" else None
    )
    run["retrieval_payload_manifest_sha256"] = (
        V28.stable_hash(retrieval_payloads) if arm_id == "retrieval" else None
    )
    run["evaluation_input_manifest_sha256"] = V28.stable_hash(
        {
            "arm_id": arm_id,
            "query_ids": sorted(query["query_id"] for query in queries),
            "source_context_item_count": run["source_context_item_count"],
            "retrieval_payload_count": run["retrieval_payload_count"],
            "source_context_manifest_sha256": run["source_context_manifest_sha256"],
            "retrieval_payload_manifest_sha256": run[
                "retrieval_payload_manifest_sha256"
            ],
        }
    )
    run["observations_sha256"] = V28.stable_hash(observations)
    return run


def _run(packet: dict, arm_id: str) -> dict:
    return next(run for run in packet["runs"] if run["arm_id"] == arm_id)


def _runs(packet: dict, arm_id: str) -> list[dict]:
    return [run for run in packet["runs"] if run["arm_id"] == arm_id]
