#!/usr/bin/env python3
"""Independently validate V45 corpus custody.

State slice: astral-stage0c-qwen36-response-anchored-causal-target-v45.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import protocol_v45 as protocol


def _receipt(errors: list[str], digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV45FreshCorpusValidated",
        "classification": "FreshCorpusValidated" if not errors else "CorpusInvalid",
        "valid": not errors,
        "errors": errors,
        "corpus_manifest_sha256": digest,
        "independent_validation": True,
    }


def validate(corpus_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    corpus_root = corpus_root.resolve()
    try:
        protocol.assert_external(corpus_root, repository_root)
        manifest_path = corpus_root / "corpus-manifest.json"
        selection_path = corpus_root / "selection-manifest.json"
        manifest = protocol.read_json(manifest_path)
        selection = protocol.read_json(selection_path)
        if not isinstance(manifest, dict) or not isinstance(selection, dict):
            raise protocol.ProtocolError("corpus manifests must be objects")
        if manifest.get("protocol") != protocol.PROTOCOL_ID or manifest.get("state_slice") != protocol.STATE_SLICE:
            errors.append("protocol_or_state_slice_mismatch")
        if selection.get("protocol") != protocol.PROTOCOL_ID or selection.get("state_slice") != protocol.STATE_SLICE:
            errors.append("selection_protocol_or_state_slice_mismatch")
        if selection.get("selection_algorithm") != protocol.SELECTION_ALGORITHM_ID or manifest.get("selection_algorithm") != protocol.SELECTION_ALGORITHM_ID:
            errors.append("selection_algorithm_mismatch")
        selected = selection.get("selection")
        documents = manifest.get("documents")
        if not isinstance(selected, list) or not isinstance(documents, list):
            raise protocol.ProtocolError("selection and documents must be arrays")
        if len(selected) != protocol.TOTAL_DOCUMENTS or len(documents) != protocol.TOTAL_DOCUMENTS:
            errors.append("document_count_mismatch")
        if selection.get("selection_sha256") != protocol.selection_digest(selected):
            errors.append("selection_digest_mismatch")
        if manifest.get("selection_sha256") != selection.get("selection_sha256"):
            errors.append("manifest_selection_binding_mismatch")
        if manifest.get("selection_manifest_sha256") != protocol.sha256_file(selection_path):
            errors.append("selection_manifest_digest_mismatch")
        if manifest.get("freshness_exclusion_ids") != list(protocol.FRESHNESS_EXCLUSION_INVENTORY) or manifest.get("freshness_exclusion_sha256") != protocol.freshness_exclusion_digest(protocol.FRESHNESS_EXCLUSION_INVENTORY):
            errors.append("freshness_inventory_mismatch")
        selected_by_id = {int(item["gutenberg_id"]): str(item["split"]) for item in selected if isinstance(item, dict) and "gutenberg_id" in item and "split" in item}
        seen_ids: set[int] = set()
        authors_by_split: dict[str, set[str]] = {split: set() for split in protocol.SPLITS}
        expected_files = {"corpus-manifest.json", "selection-manifest.json"}
        for document in documents:
            if not isinstance(document, dict):
                errors.append("document_not_object")
                continue
            ebook_id = int(document.get("gutenberg_id", -1))
            split = str(document.get("split", ""))
            author = " ".join(str(document.get("author", "")).lower().split())
            title = str(document.get("title", "")).lower()
            if ebook_id in seen_ids or ebook_id in protocol.KNOWN_RESERVED_GUTENBERG_IDS or ebook_id not in protocol.CANDIDATE_GUTENBERG_IDS:
                errors.append(f"invalid_or_duplicate_id:{ebook_id}")
            if selected_by_id.get(ebook_id) != split or split not in protocol.SPLITS or not author or not title:
                errors.append(f"selection_binding_or_metadata_invalid:{ebook_id}")
            if any(marker in title for marker in protocol.FORBIDDEN_TITLE_MARKERS):
                errors.append(f"multi_work_marker:{ebook_id}")
            if split in authors_by_split and author in authors_by_split[split]:
                errors.append(f"duplicate_author:{ebook_id}")
            if split in authors_by_split:
                authors_by_split[split].add(author)
            seen_ids.add(ebook_id)
            text_path = corpus_root / str(document.get("text_path", ""))
            metadata_path = corpus_root / str(document.get("metadata_path", ""))
            expected_files.update({str(document.get("text_path", "")), str(document.get("metadata_path", ""))})
            if not text_path.is_file() or text_path.is_symlink() or not metadata_path.is_file() or metadata_path.is_symlink():
                errors.append(f"source_file_invalid:{ebook_id}")
                continue
            if protocol.sha256_file(text_path) != document.get("text_sha256") or protocol.sha256_file(metadata_path) != document.get("metadata_sha256"):
                errors.append(f"source_digest_mismatch:{ebook_id}")
            if text_path.stat().st_size != int(document.get("text_bytes", -1)) or metadata_path.stat().st_size != int(document.get("metadata_bytes", -1)):
                errors.append(f"byte_count_mismatch:{ebook_id}")
        for left_index, left_split in enumerate(protocol.SPLITS):
            for right_split in protocol.SPLITS[left_index + 1 :]:
                if authors_by_split[left_split] & authors_by_split[right_split]:
                    errors.append("author_cross_split")
        if any(sum(1 for item in documents if isinstance(item, dict) and item.get("split") == split) != protocol.DOCUMENTS_PER_SPLIT for split in protocol.SPLITS):
            errors.append("documents_per_split_mismatch")
        actual_files = {candidate.relative_to(corpus_root).as_posix() for candidate in corpus_root.rglob("*") if candidate.is_file()}
        if actual_files not in (expected_files, expected_files | {"validator-receipt.json"}):
            errors.append("output_census_invalid")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    digest = protocol.sha256_file(corpus_root / "corpus-manifest.json") if (corpus_root / "corpus-manifest.json").is_file() else None
    return _receipt(errors, digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_root", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.corpus_root, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.corpus_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
