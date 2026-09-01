#!/usr/bin/env python3
"""Independently validate V48 panel custody and structure.

State slice: astral-stage0c-cross-view-causal-state-transport-v48.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import protocol_v48 as protocol


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate(panel_root: Path, corpus_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    repository_root = repository_root.resolve()
    try:
        protocol.assert_external(panel_root, repository_root)
        protocol.assert_external(corpus_root, repository_root)
        manifest = protocol.read_json(panel_root / "panel-manifest.json")
        families = protocol.read_json(panel_root / "families.json")
        graph = protocol.read_json(panel_root / "state-graph.json")
        corpus_manifest = protocol.read_json(corpus_root / "corpus-manifest.json")
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        return {"valid": False, "errors": [f"load:{type(exc).__name__}:{exc}"], "state_slice": protocol.STATE_SLICE}

    if manifest.get("protocol") != protocol.PROTOCOL_ID:
        _fail(errors, "protocol_identity")
    if manifest.get("state_slice") != protocol.STATE_SLICE:
        _fail(errors, "state_slice_identity")
    if manifest.get("corpus_id") != protocol.CORPUS_ID or corpus_manifest.get("corpus_id") != protocol.CORPUS_ID:
        _fail(errors, "corpus_identity")
    if manifest.get("corpus_manifest_sha256") != protocol.sha256_file(corpus_root / "corpus-manifest.json"):
        _fail(errors, "corpus_manifest_digest")
    if manifest.get("families_sha256") != protocol.sha256_file(panel_root / "families.json"):
        _fail(errors, "families_digest")
    if manifest.get("document_count") != protocol.TOTAL_DOCUMENTS or manifest.get("family_count") != protocol.TOTAL_FAMILIES:
        _fail(errors, "panel_counts")
    if graph.get("state_count") != protocol.STATE_COUNT or len(graph.get("states", [])) != protocol.STATE_COUNT:
        _fail(errors, "state_graph")
    if tuple(manifest.get("view_ids", [])) != protocol.VIEWS:
        _fail(errors, "views")
    if not isinstance(families, list) or len(families) != protocol.TOTAL_FAMILIES:
        _fail(errors, "family_list")

    ids: set[str] = set()
    docs: set[int] = set()
    by_split: dict[str, int] = {split: 0 for split in protocol.SPLITS}
    for family in families if isinstance(families, list) else []:
        if not isinstance(family, dict):
            _fail(errors, "family_type")
            continue
        family_id = family.get("family_id")
        if not isinstance(family_id, str) or family_id in ids:
            _fail(errors, "duplicate_family_id")
        ids.add(str(family_id))
        split = family.get("split")
        if split not in protocol.SPLITS:
            _fail(errors, "split_identity")
        else:
            by_split[split] += 1
        book_id = family.get("gutenberg_id")
        if not isinstance(book_id, int) or book_id not in protocol.CORPUS_DOCUMENTS:
            _fail(errors, "document_identity")
        else:
            docs.add(book_id)
        state = family.get("state")
        alternate = family.get("alternate_state")
        if not isinstance(state, int) or not isinstance(alternate, int) or not (0 <= state < protocol.STATE_COUNT and alternate == (state + 1) % protocol.STATE_COUNT):
            _fail(errors, "state_edge")
        views = family.get("views")
        if not isinstance(views, dict) or set(views) != set(protocol.VIEWS):
            _fail(errors, "view_cells")
            continue
        for view in protocol.VIEWS:
            cell = views[view]
            if not isinstance(cell, dict):
                _fail(errors, "view_cell_type")
                continue
            if not isinstance(cell.get("receiver_prompt"), str) or not isinstance(cell.get("donor_prompt"), str):
                _fail(errors, "prompt_presence")
            if cell.get("receiver_state") != state or cell.get("donor_state") != alternate:
                _fail(errors, "view_state_binding")
            if cell.get("anchor_marker") != "State payload boundary:":
                _fail(errors, "anchor_marker")
    if by_split != {split: protocol.DOCUMENTS_PER_SPLIT * protocol.FAMILIES_PER_DOCUMENT for split in protocol.SPLITS}:
        _fail(errors, "split_counts")
    if len(docs) != protocol.TOTAL_DOCUMENTS:
        _fail(errors, "document_count")
    receipt = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "panel_id": protocol.PANEL_ID,
        "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
        "corpus_manifest_sha256": protocol.sha256_file(corpus_root / "corpus-manifest.json"),
        "valid": not errors,
        "errors": errors,
        "classification": "PanelSealedForCrossViewCausalStateTransport" if not errors else "PanelInvalid",
        "claim_ceiling": "LocalDevelopmentV48PanelSealed" if not errors else "LocalDevelopmentV48PanelValidationFailed",
    }
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel_root", type=Path)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.panel_root, args.corpus_root, args.repository_root)
    if args.write_receipt:
        protocol.write_json(args.panel_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
