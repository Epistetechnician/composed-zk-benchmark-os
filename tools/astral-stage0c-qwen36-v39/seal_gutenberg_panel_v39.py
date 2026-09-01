#!/usr/bin/env python3
"""Seal the fresh V39 concept registry and split manifest.

State slice: astral-stage0c-qwen36-layer-effect-v39.

This command consumes only the externally validated Gutenberg custody bundle
and the passed V39 qualification receipt. It creates a new external panel
bundle with 48 deterministic document-derived families. It performs no model
execution, does not measure intervention effects, and leaves assessment closed.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_v39 as corpus
import panel_v39 as panel
import validator_v39


PRIOR_ARTIFACT_RECORDS = (
    {
        "protocol": "V25",
        "digest_kind": "final_manifest",
        "digest": "cf22b02d5b4b3ff4fc09c8a24405c09895e8329d871bf2cf9437f6a5c9472e87",
    },
    {
        "protocol": "V28",
        "digest_kind": "aggregate_result",
        "digest": "006d01a02d4ed9b25b154fcfa5b1f7b3b51d5b221c61d7db6b278034d097aaf9",
    },
    {
        "protocol": "V29",
        "digest_kind": "aggregate_result",
        "digest": "3cc596fcebaf5a816b0a1c1922e9e7e27e3e79a8fffe7d602a215d26d0b70ee5",
    },
)


def _sha(path: Path) -> str:
    return corpus.sha256_bytes(path.read_bytes())


def seal(
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    output_root: Path,
    repository_root: Path,
) -> Path:
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    corpus.assert_external(output_root, repository_root)
    if output_root.exists():
        raise corpus.CorpusError(f"refusing to overwrite existing panel root: {output_root}")
    source_errors = corpus.manifest_errors(corpus_root, repository_root)
    if source_errors:
        raise corpus.CorpusError(
            "source corpus failed independent validation: " + "; ".join(source_errors)
        )
    qualification_result_path = qualification_root / "qualification-result.json"
    qualification_receipt_path = qualification_root / "validator-receipt.json"
    if not qualification_result_path.is_file() or not qualification_receipt_path.is_file():
        raise corpus.CorpusError("passed V39 qualification result and receipt are required")
    qualification_result = validator_v39._strict_json(qualification_result_path)
    qualification_receipt = validator_v39.validate(
        qualification_result,
        qualification_result_path,
        model_root,
        repository_root,
    )
    if not qualification_receipt["valid"]:
        raise corpus.CorpusError(
            "qualification is not independently valid: "
            + "; ".join(qualification_receipt["errors"])
        )
    registry = panel.build_registry(corpus_root)
    corpus_manifest_path = corpus_root / "corpus-manifest.json"
    corpus_manifest = corpus.read_strict_json(corpus_manifest_path)
    corpus_manifest_digest = _sha(corpus_manifest_path)
    split = panel.split_manifest(registry, corpus_manifest_digest)
    panel_manifest = {
        "panel_id": panel.PANEL_ID,
        "protocol": corpus.protocol.PROTOCOL_ID,
        "state_slice": panel.STATE_SLICE,
        "panel_kind": panel.PANEL_KIND,
        "corpus_root": str(corpus_root),
        "corpus_manifest_sha256": corpus_manifest_digest,
        "selection_manifest_sha256": corpus_manifest["selection_manifest_sha256"],
        "qualification_root": str(qualification_root),
        "qualification_result_sha256": _sha(qualification_result_path),
        "qualification_validator_receipt_sha256": _sha(qualification_receipt_path),
        "model_root": str(model_root),
        "model_manifest_sha256": qualification_result["model_manifest_sha256"],
        "concept_registry_sha256": None,
        "split_manifest_sha256": None,
        "family_count": panel.EXPECTED_FAMILY_COUNT,
        "families_per_document": panel.EXPECTED_FAMILIES_PER_DOCUMENT,
        "families_per_split": panel.EXPECTED_FAMILIES_PER_SPLIT,
        "assessment_effects_present": False,
        "assessment_ready": False,
        "raw_documents_retained_externally": True,
        "raw_intermediates_retained": False,
        "freshness_exclusions": {
            "excluded_protocols": ["V25", "V28", "V29"],
            "prior_artifact_records": list(PRIOR_ARTIFACT_RECORDS),
            "source_selection_is_new_project_gutenberg_bundle": True,
            "registry_digest_excluded_from_prior_records": None,
        },
        "target": {
            "target_layer": 19,
            "formula": "mean_pair_margin(do(layer_19_final:=paired_opposite_final))-mean_pair_margin(clean)",
            "margin": "logit(correct_response_token)-logit(incorrect_response_token)",
            "response_labels": list(panel.RESPONSE_LABELS),
            "response_tokens": panel.RESPONSE_TOKENS,
            "response_position_rule": panel.RESPONSE_POSITION_RULE,
            "paired_replacement": "opposite_prompt_same_family_final_activation_norm_matched",
        },
        "controls": {
            "activation_only": "fixed_64_scalar_layer_19_final_projection",
            "text_only": "fixed_64_scalar_prompt_token_panel",
            "shuffled": "protocol_hash_derived_row_permutation",
            "constant": "fit_target_mean",
            "matched": "unrelated_same_document_family_norm_sequence_position_matched_replacement",
            "matched_used_for_tuning": False,
        },
    }
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent))
    )
    try:
        panel.write_json(staging / "concept-registry.json", {"families": registry})
        panel.write_json(staging / "split-manifest.json", split)
        registry_digest = _sha(staging / "concept-registry.json")
        split_digest = _sha(staging / "split-manifest.json")
        panel_manifest["concept_registry_sha256"] = registry_digest
        panel_manifest["split_manifest_sha256"] = split_digest
        panel_manifest["freshness_exclusions"]["registry_digest_excluded_from_prior_records"] = (
            registry_digest not in {item["digest"] for item in PRIOR_ARTIFACT_RECORDS}
        )
        panel.write_json(staging / "panel-manifest.json", panel_manifest)
        manifest_digest = _sha(staging / "panel-manifest.json")
        (staging / "panel-manifest.sha256").write_text(
            f"{manifest_digest}  panel-manifest.json\n", encoding="utf-8"
        )
        if output_root.exists():
            raise corpus.CorpusError(f"panel root appeared during sealing: {output_root}")
        staging.rename(output_root)
        return output_root
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args(argv)
    try:
        root = seal(
            args.corpus_root,
            args.qualification_root,
            args.model,
            args.output_root,
            args.repository_root,
        )
    except (OSError, corpus.CorpusError, ValueError) as exc:
        parser.error(str(exc))
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
