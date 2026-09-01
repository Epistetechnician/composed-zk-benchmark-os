#!/usr/bin/env python3
"""Independently validate the external V41 Gutenberg custody bundle.

State slice: astral-stage0c-qwen36-directional-block-target-v41.

This validator checks the fixed selection, freshness exclusion inventory,
metadata, UTF-8 canonical text, author/split census, byte digests, and output
census. It never loads a model or opens an assessment.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import protocol_v41 as protocol


START_MARKER = b"*** START OF"
END_MARKER = b"*** END OF"


def _has_boundaries(text_bytes: bytes) -> bool:
    lower_text = text_bytes.lower()
    start = lower_text.find(START_MARKER.lower())
    end = lower_text.rfind(END_MARKER.lower())
    return start >= 0 and end > start


def _metadata(rdf_bytes: bytes) -> dict[str, str]:
    root = ET.fromstring(rdf_bytes)
    namespaces = {
        "dcterms": "http://purl.org/dc/terms/",
        "pgterms": "http://www.gutenberg.org/2009/pgterms/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    }
    result = {
        "title": root.findtext(".//dcterms:title", default="", namespaces=namespaces).strip(),
        "author": root.findtext(".//pgterms:agent/pgterms:name", default="", namespaces=namespaces).strip(),
        "language": root.findtext(".//dcterms:language/rdf:Description/rdf:value", default="", namespaces=namespaces).strip(),
        "rights": root.findtext(".//dcterms:rights", default="", namespaces=namespaces).strip(),
    }
    if not all(result.values()):
        raise protocol.ProtocolError("Gutenberg RDF metadata is incomplete")
    if result["language"].lower() not in {"en", "eng", "english"}:
        raise protocol.ProtocolError(f"selected document is not English: {result['language']}")
    if "public domain" not in result["rights"].lower():
        raise protocol.ProtocolError("selected document lacks public-domain rights marker")
    if any(marker in result["title"].lower() for marker in protocol.FORBIDDEN_TITLE_MARKERS):
        raise protocol.ProtocolError("selected document is an anthology or collected work")
    return result


def _safe_file(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative:
        raise protocol.ProtocolError("corpus path is missing")
    candidate = (root / relative).resolve()
    if candidate == root or root not in candidate.parents:
        raise protocol.ProtocolError(f"corpus path escapes root: {relative}")
    if not candidate.is_file() or candidate.is_symlink():
        raise protocol.ProtocolError(f"corpus path is not a regular file: {relative}")
    return candidate


def _receipt(errors: list[str], manifest_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV41ExternalCorpusCustodyOnly",
        "classification": "ExternalCorpusCustodyValid" if not errors else "ExternalCorpusCustodyInvalid",
        "valid": not errors,
        "errors": errors,
        "corpus_manifest_sha256": manifest_digest,
    }


def validate(corpus_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    corpus_root = corpus_root.resolve()
    try:
        protocol.assert_external(corpus_root, repository_root)
        manifest_path = corpus_root / "corpus-manifest.json"
        selection_path = corpus_root / "selection-manifest.json"
        manifest = protocol.read_json(manifest_path)
        selection_manifest = protocol.read_json(selection_path)
        if manifest.get("protocol") != protocol.PROTOCOL_ID or selection_manifest.get("protocol") != protocol.PROTOCOL_ID:
            errors.append("protocol_mismatch")
        if manifest.get("state_slice") != protocol.STATE_SLICE or selection_manifest.get("state_slice") != protocol.STATE_SLICE:
            errors.append("state_slice_mismatch")
        if selection_manifest.get("selection") != list(protocol.SELECTION) or selection_manifest.get("selection_sha256") != protocol.selection_digest():
            errors.append("selection_mismatch")
        if manifest.get("selection_sha256") != protocol.selection_digest() or manifest.get("selection_manifest_sha256") != protocol.sha256_file(selection_path):
            errors.append("selection_binding_mismatch")
        if manifest.get("corpus_kind") != "project-gutenberg-canonical-text-rdf-v41":
            errors.append("corpus_kind_mismatch")
        if manifest.get("freshness_checked") is not True:
            errors.append("freshness_not_checked")
        exclusion_ids = manifest.get("freshness_exclusion_ids")
        if not isinstance(exclusion_ids, list) or sorted(set(exclusion_ids)) != exclusion_ids or not set(protocol.FRESHNESS_EXCLUSION_INVENTORY).issubset(exclusion_ids):
            errors.append("freshness_inventory_invalid")
        elif manifest.get("freshness_exclusion_sha256") != protocol.freshness_exclusion_digest(exclusion_ids):
            errors.append("freshness_digest_mismatch")
        if manifest.get("network_used_for_acquisition_only") is not True or manifest.get("network_used_during_model_execution") is not False or manifest.get("raw_intermediates_retained") is not False:
            errors.append("execution_boundary_invalid")
        if manifest.get("corpus_validator_receipt_required") is not True:
            errors.append("corpus_validator_receipt_requirement_missing")
        documents = manifest.get("documents")
        if not isinstance(documents, list) or len(documents) != protocol.TOTAL_DOCUMENTS:
            errors.append("document_count_mismatch")
            documents = []
        expected_by_id = {int(item["gutenberg_id"]): item for item in protocol.SELECTION}
        seen_ids: set[int] = set()
        authors_by_split: dict[str, set[str]] = {split: set() for split in protocol.SPLITS}
        split_counts: dict[str, int] = {split: 0 for split in protocol.SPLITS}
        for document in documents:
            if not isinstance(document, dict):
                errors.append("document_not_object")
                continue
            ebook_id = document.get("gutenberg_id")
            split = document.get("split")
            if not isinstance(ebook_id, int) or isinstance(ebook_id, bool) or ebook_id in seen_ids:
                errors.append("duplicate_or_invalid_gutenberg_id")
                continue
            seen_ids.add(ebook_id)
            if ebook_id in protocol.KNOWN_RESERVED_GUTENBERG_IDS:
                errors.append(f"reserved_id:{ebook_id}")
            if expected_by_id.get(ebook_id, {}).get("split") != split:
                errors.append(f"split_mismatch:{ebook_id}")
            if split not in protocol.SPLITS:
                errors.append(f"invalid_split:{ebook_id}")
                continue
            split_counts[split] += 1
            author = document.get("author")
            if not isinstance(author, str) or not author:
                errors.append(f"author_missing:{ebook_id}")
            else:
                if any(author in authors for other_split, authors in authors_by_split.items() if other_split != split):
                    errors.append(f"author_crosses_split:{author}")
                authors_by_split[split].add(author)
            text_path = _safe_file(corpus_root, document.get("text_path"))
            metadata_path = _safe_file(corpus_root, document.get("metadata_path"))
            text_bytes = text_path.read_bytes()
            metadata_bytes = metadata_path.read_bytes()
            if len(text_bytes) != document.get("text_bytes") or protocol.sha256_bytes(text_bytes) != document.get("text_sha256"):
                errors.append(f"text_digest_mismatch:{ebook_id}")
            if len(metadata_bytes) != document.get("metadata_bytes") or protocol.sha256_bytes(metadata_bytes) != document.get("metadata_sha256"):
                errors.append(f"metadata_digest_mismatch:{ebook_id}")
            if not _has_boundaries(text_bytes):
                errors.append(f"text_boundary_mismatch:{ebook_id}")
            if b"\r" in text_bytes:
                errors.append(f"text_not_canonical_newline:{ebook_id}")
            try:
                text_bytes.decode("utf-8")
            except UnicodeDecodeError:
                errors.append(f"text_not_utf8:{ebook_id}")
            try:
                metadata = _metadata(metadata_bytes)
                for key in ("title", "author", "language", "rights"):
                    if document.get(key) != metadata[key]:
                        errors.append(f"metadata_mismatch:{ebook_id}:{key}")
            except (ET.ParseError, protocol.ProtocolError, ValueError):
                errors.append(f"metadata_invalid:{ebook_id}")
            for key in ("text_url", "rdf_url"):
                if not isinstance(document.get(key), str) or not document[key].startswith("https://www.gutenberg.org/"):
                    errors.append(f"source_url_invalid:{ebook_id}:{key}")
        if seen_ids != set(expected_by_id):
            errors.append("selection_id_census_mismatch")
        if split_counts != {split: protocol.DOCUMENTS_PER_SPLIT for split in protocol.SPLITS}:
            errors.append("documents_per_split_mismatch")
        expected_files = {
            "corpus-manifest.json",
            "selection-manifest.json",
            *{f"texts/{ebook_id}.txt" for ebook_id in expected_by_id},
            *{f"metadata/{ebook_id}.rdf" for ebook_id in expected_by_id},
        }
        actual_files = {path.relative_to(corpus_root).as_posix() for path in corpus_root.rglob("*") if path.is_file()}
        allowed_files = expected_files | {"validator-receipt.json"}
        if not actual_files <= allowed_files or not expected_files <= actual_files:
            errors.append("output_census_mismatch")
    except (OSError, json.JSONDecodeError, TypeError, AttributeError, protocol.ProtocolError, ValueError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    return _receipt(
        errors,
        protocol.sha256_file(corpus_root / "corpus-manifest.json") if (corpus_root / "corpus-manifest.json").is_file() else None,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_root", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.corpus_root, args.repository_root)
    if args.write_receipt and receipt["valid"]:
        protocol.write_json(args.corpus_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
