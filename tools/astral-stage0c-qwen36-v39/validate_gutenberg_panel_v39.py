#!/usr/bin/env python3
"""Independently validate the sealed V39 concept panel.

State slice: astral-stage0c-qwen36-layer-effect-v39.

This validator performs no network access and no model execution. It checks
the external source custody bundle, panel files, family construction, split
membership, prior-protocol freshness exclusions, control declarations, and
assessment closure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_v39 as corpus
import panel_v39 as panel
import validator_v39


EXPECTED_ROOT_FILES = {
    "concept-registry.json",
    "split-manifest.json",
    "panel-manifest.json",
    "panel-manifest.sha256",
}
PRIOR_DIGESTS = {
    "cf22b02d5b4b3ff4fc09c8a24405c09895e8329d871bf2cf9437f6a5c9472e87",
    "006d01a02d4ed9b25b154fcfa5b1f7b3b51d5b221c61d7db6b278034d097aaf9",
    "3cc596fcebaf5a816b0a1c1922e9e7e27e3e79a8fffe7d602a215d26d0b70ee5",
}


def _sha(path: Path) -> str:
    return corpus.sha256_bytes(path.read_bytes())


def validate(
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    repository_root = repository_root.resolve()
    errors: list[str] = []
    try:
        corpus.assert_external(panel_root, repository_root)
    except corpus.CorpusError as exc:
        errors.append(str(exc))
    source_errors = corpus.manifest_errors(corpus_root, repository_root)
    errors.extend(f"source:{error}" for error in source_errors)
    if not panel_root.is_dir() or panel_root.is_symlink():
        errors.append("panel root is not a regular directory")
        return _receipt(errors, None)
    entries = list(panel_root.iterdir())
    if any(path.is_symlink() for path in entries):
        errors.append("symlink in panel root")
    actual_files = {path.name for path in entries if path.is_file()}
    if actual_files - EXPECTED_ROOT_FILES - {"validator-receipt.json"}:
        errors.append("unexpected panel files")
    if EXPECTED_ROOT_FILES - actual_files:
        errors.append("missing panel files")
    try:
        manifest = corpus.read_strict_json(panel_root / "panel-manifest.json")
        registry_document = corpus.read_strict_json(panel_root / "concept-registry.json")
        split = corpus.read_strict_json(panel_root / "split-manifest.json")
        sidecar = (panel_root / "panel-manifest.sha256").read_text(encoding="utf-8")
    except (OSError, corpus.CorpusError) as exc:
        errors.append(f"panel files unreadable:{type(exc).__name__}:{exc}")
        return _receipt(errors, None)
    manifest_digest = _sha(panel_root / "panel-manifest.json")
    if sidecar != f"{manifest_digest}  panel-manifest.json\n":
        errors.append("panel manifest sidecar mismatch")
    if not isinstance(manifest, dict):
        errors.append("panel manifest is not an object")
        return _receipt(errors, manifest_digest)
    required_manifest = {
        "panel_id", "protocol", "state_slice", "panel_kind", "corpus_root",
        "corpus_manifest_sha256", "selection_manifest_sha256", "qualification_root",
        "qualification_result_sha256", "qualification_validator_receipt_sha256",
        "model_root", "model_manifest_sha256", "concept_registry_sha256",
        "split_manifest_sha256", "family_count", "families_per_document",
        "families_per_split", "assessment_effects_present", "assessment_ready",
        "raw_documents_retained_externally", "raw_intermediates_retained",
        "freshness_exclusions", "target", "controls",
    }
    if set(manifest) != required_manifest:
        errors.append("panel manifest fields invalid")
    for key, expected in (
        ("panel_id", panel.PANEL_ID),
        ("protocol", corpus.protocol.PROTOCOL_ID),
        ("state_slice", panel.STATE_SLICE),
        ("panel_kind", panel.PANEL_KIND),
        ("corpus_root", str(corpus_root)),
        ("qualification_root", str(qualification_root)),
        ("family_count", panel.EXPECTED_FAMILY_COUNT),
        ("families_per_document", panel.EXPECTED_FAMILIES_PER_DOCUMENT),
        ("families_per_split", panel.EXPECTED_FAMILIES_PER_SPLIT),
        ("assessment_effects_present", False),
        ("assessment_ready", False),
        ("raw_documents_retained_externally", True),
        ("raw_intermediates_retained", False),
    ):
        if manifest.get(key) != expected:
            errors.append(f"panel {key} mismatch")
    try:
        source_manifest = corpus.read_strict_json(corpus_root / "corpus-manifest.json")
        if manifest.get("corpus_manifest_sha256") != _sha(corpus_root / "corpus-manifest.json"):
            errors.append("panel corpus digest mismatch")
        if manifest.get("selection_manifest_sha256") != source_manifest.get("selection_manifest_sha256"):
            errors.append("panel selection digest mismatch")
    except (OSError, corpus.CorpusError) as exc:
        errors.append(f"source manifest unreadable:{type(exc).__name__}:{exc}")
    if manifest.get("concept_registry_sha256") != _sha(panel_root / "concept-registry.json"):
        errors.append("concept registry digest mismatch")
    if manifest.get("split_manifest_sha256") != _sha(panel_root / "split-manifest.json"):
        errors.append("split manifest digest mismatch")
    registry = registry_document.get("families") if isinstance(registry_document, dict) else None
    errors.extend(panel.registry_errors(registry, split, manifest.get("corpus_manifest_sha256")))
    freshness = manifest.get("freshness_exclusions")
    if not isinstance(freshness, dict):
        errors.append("freshness exclusions invalid")
    else:
        if freshness.get("excluded_protocols") != ["V25", "V28", "V29"]:
            errors.append("freshness protocol exclusions mismatch")
        if freshness.get("registry_digest_excluded_from_prior_records") is not True:
            errors.append("registry freshness exclusion failed")
        prior = freshness.get("prior_artifact_records")
        if not isinstance(prior, list) or {item.get("digest") for item in prior if isinstance(item, dict)} != PRIOR_DIGESTS:
            errors.append("prior artifact digest exclusions mismatch")
    target = manifest.get("target")
    if not isinstance(target, dict) or target.get("target_layer") != 19:
        errors.append("target declaration invalid")
    controls = manifest.get("controls")
    if not isinstance(controls, dict) or controls.get("matched_used_for_tuning") is not False:
        errors.append("control declaration invalid")
    qualification_result_path = qualification_root / "qualification-result.json"
    if not qualification_result_path.is_file():
        errors.append("qualification result missing")
    else:
        try:
            qualification_result = validator_v39._strict_json(qualification_result_path)
            qualification_receipt = validator_v39.validate(
                qualification_result,
                qualification_result_path,
                model_root,
                repository_root,
            )
            if not qualification_receipt["valid"]:
                errors.append("qualification receipt invalid")
            if manifest.get("model_root") != str(model_root):
                errors.append("panel model root mismatch")
            if manifest.get("model_manifest_sha256") != qualification_result.get("model_manifest_sha256"):
                errors.append("panel model manifest mismatch")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"qualification validation failed:{type(exc).__name__}:{exc}")
    return _receipt(errors, manifest_digest)


def _receipt(errors: list[str], manifest_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": corpus.protocol.PROTOCOL_ID,
        "state_slice": panel.STATE_SLICE,
        "classification": "PanelSealedForPreassessment" if not errors else "PanelInvalid",
        "claim_ceiling": "LocalDevelopmentV39PanelSealed",
        "valid": not errors,
        "panel_manifest_sha256": manifest_digest,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel_root", type=Path)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = validate(
            args.panel_root,
            args.corpus_root,
            args.qualification_root,
            args.model,
            args.repository_root,
        )
    except (OSError, corpus.CorpusError, ValueError, json.JSONDecodeError) as exc:
        receipt = _receipt([f"validator_error:{type(exc).__name__}:{exc}"], None)
    if args.write_receipt:
        receipt_path = args.panel_root.resolve() / "validator-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
