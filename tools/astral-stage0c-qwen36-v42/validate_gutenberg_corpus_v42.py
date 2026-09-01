#!/usr/bin/env python3
"""Independently validate the external V42 Gutenberg custody root.

State slice: astral-stage0c-qwen36-causal-target-reliability-v42.
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import protocol_v42 as protocol


START_RE = re.compile(rb"\*\*\* START OF", re.IGNORECASE)
END_RE = re.compile(rb"\*\*\* END OF", re.IGNORECASE)


def _metadata(rdf_bytes: bytes) -> dict[str, str]:
    root = ET.fromstring(rdf_bytes)
    namespaces = {
        "dcterms": "http://purl.org/dc/terms/",
        "pgterms": "http://www.gutenberg.org/2009/pgterms/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    }
    return {
        "title": root.findtext(".//dcterms:title", default="", namespaces=namespaces).strip(),
        "author": root.findtext(".//pgterms:agent/pgterms:name", default="", namespaces=namespaces).strip(),
        "language": root.findtext(
            ".//dcterms:language/rdf:Description/rdf:value", default="", namespaces=namespaces
        ).strip(),
        "rights": root.findtext(".//dcterms:rights", default="", namespaces=namespaces).strip(),
    }


def _receipt(errors: list[str], manifest_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV42CorpusCustody",
        "classification": "CorpusSealed" if not errors else "CorpusInvalid",
        "valid": not errors,
        "errors": errors,
        "corpus_manifest_sha256": manifest_digest,
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
            raise protocol.ProtocolError("custody manifests must be objects")
        if manifest.get("protocol") != protocol.PROTOCOL_ID or manifest.get("state_slice") != protocol.STATE_SLICE:
            errors.append("manifest_protocol_or_state_slice_mismatch")
        if selection.get("protocol") != protocol.PROTOCOL_ID or selection.get("state_slice") != protocol.STATE_SLICE:
            errors.append("selection_protocol_or_state_slice_mismatch")
        if selection.get("selection") != list(protocol.SELECTION):
            errors.append("selection_mismatch")
        if selection.get("selection_sha256") != protocol.selection_digest():
            errors.append("selection_digest_mismatch")
        if manifest.get("selection_sha256") != protocol.selection_digest():
            errors.append("manifest_selection_digest_mismatch")
        if manifest.get("selection_manifest_sha256") != protocol.sha256_file(selection_path):
            errors.append("selection_manifest_binding_mismatch")
        exclusion_ids = manifest.get("freshness_exclusion_ids")
        if (
            manifest.get("freshness_checked") is not True
            or not isinstance(exclusion_ids, list)
            or any(isinstance(value, bool) or not isinstance(value, int) for value in exclusion_ids)
            or sorted(set(exclusion_ids)) != exclusion_ids
            or not set(protocol.FRESHNESS_EXCLUSION_INVENTORY).issubset(exclusion_ids)
            or manifest.get("freshness_exclusion_sha256")
            != protocol.freshness_exclusion_digest(exclusion_ids)
        ):
            errors.append("freshness_exclusion_binding_invalid")
        if manifest.get("network_used_for_acquisition_only") is not True:
            errors.append("acquisition_network_boundary_missing")
        if manifest.get("network_used_during_model_execution") is not False:
            errors.append("model_execution_network_boundary_missing")
        documents = manifest.get("documents")
        if not isinstance(documents, list) or len(documents) != protocol.TOTAL_DOCUMENTS:
            errors.append("document_count_mismatch")
            documents = []
        expected_by_id = {int(item["gutenberg_id"]): item for item in protocol.SELECTION}
        seen_ids: set[int] = set()
        authors_by_split: dict[str, set[str]] = {split: set() for split in protocol.SPLITS}
        for document in documents:
            if not isinstance(document, dict):
                errors.append("document_entry_not_object")
                continue
            try:
                ebook_id = int(document["gutenberg_id"])
                split = str(document["split"])
                text_path = corpus_root / str(document["text_path"])
                metadata_path = corpus_root / str(document["metadata_path"])
                if ebook_id in seen_ids or ebook_id in protocol.KNOWN_RESERVED_GUTENBERG_IDS:
                    errors.append(f"duplicate_or_reserved_id:{ebook_id}")
                seen_ids.add(ebook_id)
                if expected_by_id.get(ebook_id, {}).get("split") != split:
                    errors.append(f"selection_split_mismatch:{ebook_id}")
                if split not in protocol.SPLITS:
                    errors.append(f"unknown_split:{ebook_id}")
                if not text_path.is_file() or text_path.is_symlink() or not metadata_path.is_file() or metadata_path.is_symlink():
                    errors.append(f"missing_or_symlinked_source:{ebook_id}")
                    continue
                text_bytes = text_path.read_bytes()
                rdf_bytes = metadata_path.read_bytes()
                if document.get("text_sha256") != protocol.sha256_bytes(text_bytes):
                    errors.append(f"text_digest_mismatch:{ebook_id}")
                if document.get("metadata_sha256") != protocol.sha256_bytes(rdf_bytes):
                    errors.append(f"metadata_digest_mismatch:{ebook_id}")
                if len(text_bytes) != document.get("text_bytes") or len(rdf_bytes) != document.get("metadata_bytes"):
                    errors.append(f"source_size_mismatch:{ebook_id}")
                if not START_RE.search(text_bytes) or not END_RE.search(text_bytes):
                    errors.append(f"gutenberg_boundary_missing:{ebook_id}")
                metadata = _metadata(rdf_bytes)
                for key in ("title", "author", "language", "rights"):
                    if document.get(key) != metadata[key] or not metadata[key]:
                        errors.append(f"metadata_mismatch:{ebook_id}:{key}")
                if metadata["language"].lower() not in {"en", "eng", "english"}:
                    errors.append(f"non_english:{ebook_id}")
                if "public domain" not in metadata["rights"].lower():
                    errors.append(f"rights_marker_missing:{ebook_id}")
                if any(marker in metadata["title"].lower() for marker in protocol.FORBIDDEN_TITLE_MARKERS):
                    errors.append(f"multi_work_title:{ebook_id}")
                author = metadata["author"]
                if any(author in authors for other_split, authors in authors_by_split.items() if other_split != split):
                    errors.append(f"author_cross_split:{author}")
                authors_by_split.setdefault(split, set()).add(author)
            except (KeyError, OSError, ET.ParseError, TypeError, ValueError) as exc:
                errors.append(f"document_error:{type(exc).__name__}:{exc}")
        if seen_ids != set(expected_by_id):
            errors.append("document_id_census_mismatch")
        for split in protocol.SPLITS:
            if sum(1 for document in documents if isinstance(document, dict) and document.get("split") == split) != protocol.DOCUMENTS_PER_SPLIT:
                errors.append(f"documents_per_split_mismatch:{split}")
        expected_files = {
            "corpus-manifest.json",
            "selection-manifest.json",
            *(f"texts/{book_id}.txt" for book_id in expected_by_id),
            *(f"metadata/{book_id}.rdf" for book_id in expected_by_id),
        }
        actual_files = {
            candidate.relative_to(corpus_root).as_posix()
            for candidate in corpus_root.rglob("*")
            if candidate.is_file()
        }
        if not actual_files <= expected_files | {"validator-receipt.json"}:
            errors.append("output_census_unknown_files")
        if not expected_files <= actual_files:
            errors.append("output_census_missing_files")
    except (OSError, json.JSONDecodeError, protocol.ProtocolError, TypeError, ValueError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    manifest_digest = (
        protocol.sha256_file(corpus_root / "corpus-manifest.json")
        if (corpus_root / "corpus-manifest.json").is_file()
        else None
    )
    return _receipt(errors, manifest_digest)


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
