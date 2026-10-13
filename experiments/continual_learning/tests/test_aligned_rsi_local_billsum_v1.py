"""Hermetic contract checks for aligned-rsi-local-billsum-adaptation-internal-v1."""

from __future__ import annotations

import random

import pytest

from experiments.continual_learning import aligned_rsi_local_billsum_v1 as experiment


def test_protocol_is_local_only_and_has_pinned_runtime() -> None:
    manifest = experiment._verify_protocol()

    assert manifest["state_slice"] == "aligned-rsi-local-billsum-adaptation-internal-v1"
    assert manifest["independent_acceptance_requested"] is False
    assert manifest["execution"]["paid_provider_calls"] is False
    assert manifest["execution"]["network_during_run"] is False
    assert manifest["runtime"] == experiment._runtime_manifest()


def test_document_digest_and_rouge_are_deterministic() -> None:
    first = experiment.document_id("A bill", "A summary")
    assert first == experiment.document_id("A bill", "A summary")
    assert first != experiment.document_id("A bill", "A different summary")
    assert experiment.rouge_l_f1("A bill, with purpose.", "a bill, with purpose.") == 1.0
    assert experiment.rouge_l_f1("", "reference") == 0.0


def test_bootstrap_interval_is_seeded_and_ordered() -> None:
    values = [-0.1, 0.05, 0.1, 0.2]
    interval = experiment.bootstrap_interval(values)

    assert interval == experiment.bootstrap_interval(values)
    assert interval[0] <= sum(values) / len(values) <= interval[1]


def test_metric_properties_over_deterministic_fuzz_corpus() -> None:
    generator = random.Random(10261006)
    vocabulary = ["bill", "shall", "provide", "funds", "42", ",", ".", "agency"]
    for _ in range(300):
        tokens = [generator.choice(vocabulary) for _ in range(generator.randrange(1, 30))]
        text = " ".join(tokens)
        score = experiment.rouge_l_f1(text, text)
        assert score == 1.0
        perturbed = " ".join(generator.choice(vocabulary) for _ in range(generator.randrange(1, 30)))
        assert 0.0 <= experiment.rouge_l_f1(text, perturbed) <= 1.0


def test_local_report_reconstructs_complete_no_candidate_without_independent_claim() -> None:
    assessment_ids = [experiment.document_id(f"bill {index}", f"summary {index}") for index in range(128)]
    references = {identifier: "reference bill summary" for identifier in assessment_ids}
    generations = {identifier: "reference bill summary" for identifier in assessment_ids}
    nlls = {identifier: 1.0 for identifier in assessment_ids}
    private = {
        "assessment_ids": assessment_ids,
        "fit_pool_ids": [f"fit-{index}" for index in range(512)],
        "arms": {
            "untouched_base": {"generation": generations, "nll": nlls},
            "loss_selected": [
                {
                    "seed": seed,
                    "generation": generations,
                    "nll": nlls,
                    "selection_ids": [f"selected-{index}" for index in range(128)],
                }
                for seed in experiment.SEEDS
            ],
            "random_control": [
                {
                    "seed": seed,
                    "generation": generations,
                    "nll": nlls,
                    "selection_ids": [f"random-{seed}-{index}" for index in range(128)],
                }
                for seed in experiment.SEEDS
            ],
        },
        "mechanistic": [
            {
                "doc_id": identifier,
                "arm": arm,
                "seed": seed,
                "base_nll": 2.0,
                "adapted_nll": 1.0,
                "identity_patch_abs_error": 0.0,
                "base_activation_patch_nll": 1.5,
                "activation_patch_delta_nll": 0.5,
            }
            for arm in ("loss_selected", "random_control")
            for seed in experiment.SEEDS
            for identifier in assessment_ids[: experiment.MECHANISTIC_ROWS]
        ],
    }

    report = experiment._report_from_private(private, references)

    assert report["candidate_disposition"] == "NoCandidate"
    assert report["assurance_level"] == "PENDING_LOCAL_VERIFICATION"
    assert report["local_acceptance"] == "PENDING_LOCAL_VERIFICATION"
    assert report["independent_acceptance"] is False
    assert report["primary"]["mean_effect"] == 0.0
    assert report["secondary"]["complete_finite_outputs"] is True
    assert report["secondary"]["mean_fraction_base_activation_recovered"] == 0.5

    incomplete = {
        **private,
        "arms": {
            **private["arms"],
            "untouched_base": {
                **private["arms"]["untouched_base"],
                "generation": {
                    key: value for key, value in generations.items() if key != assessment_ids[0]
                },
            },
        },
    }
    with pytest.raises(experiment.ExperimentError, match="base assessment roster"):
        experiment._report_from_private(incomplete, references)


def test_duplicate_json_keys_are_rejected(tmp_path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"version": 1, "version": 2}', encoding="utf-8")

    with pytest.raises(experiment.ExperimentError, match="duplicate JSON key"):
        experiment.load_json(path)


def test_input_tree_symlinks_are_rejected(tmp_path) -> None:
    target = tmp_path / "payload.txt"
    target.write_text("fixture", encoding="utf-8")
    link = tmp_path / "linked.txt"
    link.symlink_to(target)

    with pytest.raises(experiment.ExperimentError, match="symlink"):
        experiment.tree_manifest(tmp_path)


def test_manifest_is_duplicate_key_free() -> None:
    decoded = experiment.load_json(experiment.MANIFEST_PATH)
    assert decoded["protocol_id"] == experiment.PROTOCOL_ID
