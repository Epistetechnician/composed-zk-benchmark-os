#!/usr/bin/env python3
"""Independently validate the external V41 sealed panel.

State slice: astral-stage0c-qwen36-directional-block-target-v41.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import panel_v41 as panel
import protocol_v41 as protocol


def _receipt(errors: list[str], manifest_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV41PanelSealed",
        "classification": "PanelSealedForPreassessment" if not errors else "PanelInvalid",
        "valid": not errors,
        "errors": errors,
        "panel_manifest_sha256": manifest_digest,
    }


def validate(panel_root: Path, corpus_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    model_root = model_root.resolve()
    try:
        protocol.assert_external(panel_root, repository_root)
        protocol.assert_external(corpus_root, repository_root)
        protocol.assert_external(model_root, repository_root)
        manifest_path = panel_root / "panel-manifest.json"
        registry_path = panel_root / "concept-registry.json"
        split_path = panel_root / "split-manifest.json"
        manifest = protocol.read_json(manifest_path)
        registry_document = protocol.read_json(registry_path)
        split_manifest = protocol.read_json(split_path)
        from mlx_lm import load

        model_manifest = protocol.model_manifest(model_root)
        _, tokenizer = load(str(model_root), lazy=True)
        expected_registry = panel.build_registry(corpus_root, tokenizer)
        if manifest.get("protocol") != protocol.PROTOCOL_ID or manifest.get("state_slice") != protocol.STATE_SLICE:
            errors.append("protocol_or_state_slice_mismatch")
        if manifest.get("panel_id") != protocol.PANEL_ID:
            errors.append("panel_id_mismatch")
        if manifest.get("corpus_manifest_sha256") != protocol.sha256_file(corpus_root / "corpus-manifest.json"):
            errors.append("corpus_binding_mismatch")
        if manifest.get("corpus_validator_receipt_sha256") != protocol.sha256_file(corpus_root / "validator-receipt.json"):
            errors.append("corpus_validator_receipt_binding_mismatch")
        if manifest.get("model_manifest_sha256") != model_manifest["manifest_sha256"]:
            errors.append("model_binding_mismatch")
        if manifest.get("feature_map_sha256") != protocol.feature_map_digest():
            errors.append("feature_map_binding_mismatch")
        if registry_document.get("families") != expected_registry:
            errors.append("registry_recomputation_mismatch")
        if manifest.get("concept_registry_sha256") != protocol.canonical_digest(expected_registry):
            errors.append("registry_digest_mismatch")
        for key in ("by_split", "by_document", "documents_by_split", "authors_by_split", "corpus_validator_receipt_sha256"):
            if split_manifest.get(key) != manifest.get(key):
                errors.append(f"split_binding_mismatch:{key}")
        if split_manifest.get("feature_map_sha256") != protocol.feature_map_digest():
            errors.append("split_feature_map_binding_mismatch")
        if manifest.get("assessment_effects_present") is not False or manifest.get("assessment_ready") is not False:
            errors.append("assessment_not_closed")
        if not isinstance(registry_document.get("families"), list) or len(registry_document["families"]) != protocol.TOTAL_FAMILIES:
            errors.append("family_count_mismatch")
        by_split: dict[str, list[dict[str, Any]]] = {split: [] for split in protocol.SPLITS}
        authors: dict[str, set[str]] = {split: set() for split in protocol.SPLITS}
        for family in expected_registry:
            by_split[family["split"]].append(family)
            authors[family["split"]].add(family["author"])
        if any(len(by_split[split]) != protocol.FAMILIES_PER_SPLIT for split in protocol.SPLITS):
            errors.append("families_per_split_mismatch")
        for left_index, left_split in enumerate(protocol.SPLITS):
            for right_split in protocol.SPLITS[left_index + 1 :]:
                if authors[left_split] & authors[right_split]:
                    errors.append("author_cross_split")
        if any(len(manifest.get("documents_by_split", {}).get(split, [])) != protocol.DOCUMENTS_PER_SPLIT for split in protocol.SPLITS):
            errors.append("documents_per_split_mismatch")
        expected_files = {"panel-manifest.json", "concept-registry.json", "split-manifest.json"}
        actual_files = {candidate.relative_to(panel_root).as_posix() for candidate in panel_root.rglob("*") if candidate.is_file()}
        allowed_files = expected_files | {"validator-receipt.json"}
        if not actual_files <= allowed_files:
            errors.append("output_census_unknown_files")
        if not expected_files <= actual_files:
            errors.append("output_census_missing_files")
    except (OSError, json.JSONDecodeError, protocol.ProtocolError, UnicodeDecodeError, KeyError, TypeError, AttributeError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    return _receipt(errors, protocol.sha256_file(panel_root / "panel-manifest.json") if (panel_root / "panel-manifest.json").is_file() else None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel_root", type=Path)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"))
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.panel_root, args.corpus_root, args.model, args.repository_root)
    if args.write_receipt:
        protocol.write_json(args.panel_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
