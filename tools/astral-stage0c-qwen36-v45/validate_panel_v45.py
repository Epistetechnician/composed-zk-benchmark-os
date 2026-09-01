#!/usr/bin/env python3
"""Independently validate the sealed V45 panel.

State slice: astral-stage0c-qwen36-response-anchored-causal-target-v45.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import panel_v45 as panel
import protocol_v45 as protocol


def _receipt(errors: list[str], digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV45PanelSealed",
        "classification": "PanelSealedForCanonicalTask" if not errors else "PanelInvalid",
        "valid": not errors,
        "errors": errors,
        "panel_manifest_sha256": digest,
        "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
        "independent_validation": True,
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
        if not isinstance(manifest, dict) or not isinstance(registry_document, dict) or not isinstance(split_manifest, dict):
            raise protocol.ProtocolError("panel documents must be objects")
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
            errors.append("corpus_receipt_binding_mismatch")
        if manifest.get("model_manifest_sha256") != model_manifest["manifest_sha256"]:
            errors.append("model_binding_mismatch")
        if manifest.get("canonical_wrapper") != protocol.CANONICAL_WRAPPER or manifest.get("control_names") != list(protocol.CONTROL_NAMES):
            errors.append("task_or_control_binding_mismatch")
        if manifest.get("candidate_layers") != list(protocol.CANDIDATE_LAYERS) or manifest.get("position_name") != protocol.POSITION_NAME or manifest.get("content_anchor_offset") != protocol.CONTENT_ANCHOR_OFFSET or manifest.get("position_rule") != protocol.POSITION_RULE:
            errors.append("target_binding_mismatch")
        if manifest.get("feature_map_id") != protocol.FEATURE_MAP_ID or manifest.get("ridge_alphas") != list(protocol.RIDGE_ALPHAS):
            errors.append("feature_binding_mismatch")
        if registry_document.get("protocol") != protocol.PROTOCOL_ID or registry_document.get("state_slice") != protocol.STATE_SLICE or registry_document.get("families") != expected_registry:
            errors.append("registry_recomputation_mismatch")
        if manifest.get("concept_registry_sha256") != protocol.canonical_digest(expected_registry):
            errors.append("registry_digest_mismatch")
        for key in ("by_split", "by_document", "documents_by_split", "authors_by_split"):
            if split_manifest.get(key) != manifest.get(key):
                errors.append(f"split_binding_mismatch:{key}")
        if manifest.get("assessment_effects_present") is not False or manifest.get("assessment_ready") is not False:
            errors.append("assessment_not_closed")
        families = expected_registry
        if len(families) != protocol.TOTAL_FAMILIES:
            errors.append("family_count_mismatch")
        concepts: set[str] = set()
        for family in families:
            for key in ("target_word", "distractor_word"):
                value = family.get(key)
                if not isinstance(value, str) or value in concepts:
                    errors.append(f"concept_reused_or_invalid:{family.get('family_id')}:{key}")
                concepts.add(value)
            if family.get("position_rule") != protocol.POSITION_RULE:
                errors.append(f"position_rule_mismatch:{family.get('family_id')}")
            if family.get("ordinary_content_anchor_index") != family.get("counterfactual_content_anchor_index"):
                errors.append(f"anchor_mismatch:{family.get('family_id')}")
            for key in ("ordinary_prompt", "counterfactual_prompt"):
                if len(tokenizer.encode(family[key])) != protocol.FIXED_TOKEN_LENGTH:
                    errors.append(f"prompt_length_mismatch:{family.get('family_id')}:{key}")
        expected_files = {"panel-manifest.json", "concept-registry.json", "split-manifest.json"}
        actual_files = {candidate.relative_to(panel_root).as_posix() for candidate in panel_root.rglob("*") if candidate.is_file()}
        if actual_files not in (expected_files, expected_files | {"validator-receipt.json"}):
            errors.append("output_census_invalid")
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    digest = protocol.sha256_file(panel_root / "panel-manifest.json") if (panel_root / "panel-manifest.json").is_file() else None
    return _receipt(errors, digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel_root", type=Path)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.panel_root, args.corpus_root, args.model, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.panel_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
