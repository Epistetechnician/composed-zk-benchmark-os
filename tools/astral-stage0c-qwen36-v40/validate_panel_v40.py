#!/usr/bin/env python3
"""Independently validate the external V40 sealed panel.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

Validation recomputes the panel from current corpus bytes, checks all split and
author boundaries, and rejects assessment material or unknown output files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import panel_v40 as panel
import protocol_v40 as protocol


def _receipt(errors: list[str], manifest_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV40PanelSealed",
        "classification": "PanelSealedForPreassessment" if not errors else "PanelInvalid",
        "valid": not errors,
        "errors": errors,
        "panel_manifest_sha256": manifest_digest,
    }


def validate(panel_root: Path, corpus_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    panel_root = panel_root.resolve()
    model_root = model_root.resolve()
    try:
        protocol.assert_external(panel_root, repository_root)
        protocol.assert_external(corpus_root.resolve(), repository_root)
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
        expected_registry = panel.build_registry(corpus_root.resolve(), tokenizer)
        if manifest.get("protocol") != protocol.PROTOCOL_ID or manifest.get("state_slice") != protocol.STATE_SLICE:
            errors.append("protocol_or_state_slice_mismatch")
        if manifest.get("panel_id") != panel.PANEL_ID:
            errors.append("panel_id_mismatch")
        if manifest.get("corpus_manifest_sha256") != protocol.sha256_file(corpus_root / "corpus-manifest.json"):
            errors.append("corpus_binding_mismatch")
        if manifest.get("model_manifest_sha256") != model_manifest["manifest_sha256"]:
            errors.append("model_binding_mismatch")
        if registry_document.get("families") != expected_registry:
            errors.append("registry_recomputation_mismatch")
        if manifest.get("concept_registry_sha256") != protocol.canonical_digest(expected_registry):
            errors.append("registry_digest_mismatch")
        if split_manifest.get("by_split") != manifest.get("by_split") or split_manifest.get("by_document") != manifest.get("by_document") or split_manifest.get("model_manifest_sha256") != manifest.get("model_manifest_sha256"):
            errors.append("split_binding_mismatch")
        if manifest.get("assessment_effects_present") is not False or manifest.get("assessment_ready") is not False:
            errors.append("assessment_not_closed")
        if not isinstance(registry_document.get("families"), list) or len(registry_document["families"]) != protocol.TOTAL_FAMILIES:
            errors.append("family_count_mismatch")
        by_split: dict[str, list[dict[str, Any]]] = {split: [] for split in protocol.SPLITS}
        authors: dict[str, set[str]] = {split: set() for split in protocol.SPLITS}
        for family in expected_registry:
            split = family["split"]
            by_split[split].append(family)
            authors[split].add(family["author"])
        if any(len(by_split[split]) != protocol.FAMILIES_PER_SPLIT for split in protocol.SPLITS):
            errors.append("families_per_split_mismatch")
        for left_index, left_split in enumerate(protocol.SPLITS):
            for right_split in protocol.SPLITS[left_index + 1:]:
                if authors[left_split] & authors[right_split]:
                    errors.append("author_cross_split")
        if any(len(manifest.get("documents_by_split", {}).get(split, [])) != protocol.DOCUMENTS_PER_SPLIT for split in protocol.SPLITS):
            errors.append("documents_per_split_mismatch")
        expected_files = {"panel-manifest.json", "concept-registry.json", "split-manifest.json"}
        actual_files = {path.relative_to(panel_root).as_posix() for path in panel_root.rglob("*") if path.is_file()}
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
    parser.add_argument("--model", type=Path, default=panel.DEFAULT_MODEL)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.panel_root, args.corpus_root, args.model, args.repository_root)
    if args.write_receipt:
        protocol.write_json(args.panel_root / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
