#!/usr/bin/env python3
"""Independently validate the external V40 Gutenberg custody bundle.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

The validator recomputes every retained digest, selection binding, metadata
field, author split rule, output census, and source boundary. It never runs a
model and never opens an assessment.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import fetch_gutenberg_corpus_v40 as acquisition
import protocol_v40 as protocol


def validate(corpus_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    corpus_root = corpus_root.resolve()
    try:
        protocol.assert_external(corpus_root, repository_root)
        manifest = protocol.read_json(corpus_root / "corpus-manifest.json")
        selection_manifest = protocol.read_json(corpus_root / "selection-manifest.json")
        if manifest.get("protocol") != protocol.PROTOCOL_ID:
            errors.append("protocol_mismatch")
        if manifest.get("state_slice") != protocol.STATE_SLICE:
            errors.append("state_slice_mismatch")
        if selection_manifest.get("selection") != list(protocol.SELECTION):
            errors.append("selection_mismatch")
        if selection_manifest.get("selection_sha256") != protocol.selection_digest():
            errors.append("selection_digest_mismatch")
        if manifest.get("selection_sha256") != protocol.selection_digest():
            errors.append("manifest_selection_digest_mismatch")
        documents = manifest.get("documents")
        if not isinstance(documents, list) or len(documents) != len(protocol.SELECTION):
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
            if not isinstance(ebook_id, int) or ebook_id in seen_ids:
                errors.append("duplicate_or_invalid_gutenberg_id")
                continue
            seen_ids.add(ebook_id)
            if ebook_id in protocol.V39_GUTENBERG_IDS:
                errors.append(f"prior_v39_id:{ebook_id}")
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
                for other_split, authors in authors_by_split.items():
                    if other_split != split and author in authors:
                        errors.append(f"author_crosses_split:{author}")
                authors_by_split[split].add(author)
            text_path = corpus_root / str(document.get("text_path"))
            metadata_path = corpus_root / str(document.get("metadata_path"))
            for path, byte_key, digest_key in (
                (text_path, "text_bytes", "text_sha256"),
                (metadata_path, "metadata_bytes", "metadata_sha256"),
            ):
                if not path.is_file():
                    errors.append(f"missing_file:{ebook_id}:{path.name}")
                    continue
                payload = path.read_bytes()
                if len(payload) != document.get(byte_key):
                    errors.append(f"byte_length_mismatch:{ebook_id}:{path.name}")
                if protocol.sha256_bytes(payload) != document.get(digest_key):
                    errors.append(f"digest_mismatch:{ebook_id}:{path.name}")
            if metadata_path.is_file():
                try:
                    metadata = acquisition._metadata(metadata_path.read_bytes())
                    for key in ("title", "author", "language", "rights"):
                        if document.get(key) != metadata[key]:
                            errors.append(f"metadata_mismatch:{ebook_id}:{key}")
                except (OSError, protocol.ProtocolError, ValueError) as exc:
                    errors.append(f"metadata_invalid:{ebook_id}:{type(exc).__name__}")
            if text_path.is_file():
                text = text_path.read_bytes()
                start = text.lower().find(b"*** start of")
                end = text.lower().rfind(b"*** end of")
                if start < 0 or end <= start:
                    errors.append(f"boundary_mismatch:{ebook_id}")
                try:
                    text.decode("utf-8")
                except UnicodeDecodeError:
                    errors.append(f"utf8_mismatch:{ebook_id}")
        if split_counts != {split: protocol.DOCUMENTS_PER_SPLIT for split in protocol.SPLITS}:
            errors.append("documents_per_split_mismatch")
        expected_files = {
            "corpus-manifest.json",
            "selection-manifest.json",
            *{f"texts/{ebook_id}.txt" for ebook_id in expected_by_id},
            *{f"metadata/{ebook_id}.rdf" for ebook_id in expected_by_id},
        }
        actual_files = {path.relative_to(corpus_root).as_posix() for path in corpus_root.rglob("*") if path.is_file()}
        if actual_files != expected_files:
            errors.append("output_census_mismatch")
    except (OSError, json.JSONDecodeError, TypeError, AttributeError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV40ExternalCorpusCustodyOnly",
        "classification": "ExternalCorpusCustodyValid" if not errors else "ExternalCorpusCustodyInvalid",
        "valid": not errors,
        "errors": errors,
        "corpus_manifest_sha256": (
            protocol.sha256_file(corpus_root / "corpus-manifest.json")
            if (corpus_root / "corpus-manifest.json").is_file()
            else None
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_root", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    receipt = validate(args.corpus_root, args.repository_root)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
