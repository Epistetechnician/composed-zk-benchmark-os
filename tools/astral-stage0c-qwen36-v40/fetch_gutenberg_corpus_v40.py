#!/usr/bin/env python3
"""Acquire and seal the fresh V40 Project Gutenberg corpus.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

Acquisition is separate from model execution. The output root is external to
the repository and is published atomically only after every selected ebook has
passed metadata, encoding, and Project Gutenberg boundary checks.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import protocol_v40 as protocol


START_MARKER = b"*** START OF"
END_MARKER = b"*** END OF"
USER_AGENT = "Astral-V40-corpus-custody/1.0"


def _fetch(urls: list[str]) -> tuple[bytes, str]:
    last_error: Exception | None = None
    for url in urls:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
            return payload, url
        except Exception as exc:  # pragma: no cover - network failures vary
            last_error = exc
    raise protocol.ProtocolError(f"all Gutenberg URLs failed: {last_error}")


def _metadata(rdf_bytes: bytes) -> dict[str, str]:
    root = ET.fromstring(rdf_bytes)
    namespaces = {
        "dcterms": "http://purl.org/dc/terms/",
        "pgterms": "http://www.gutenberg.org/2009/pgterms/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    }
    title = root.findtext(".//dcterms:title", default="", namespaces=namespaces).strip()
    author = root.findtext(".//pgterms:agent/pgterms:name", default="", namespaces=namespaces).strip()
    language = root.findtext(".//dcterms:language/rdf:Description/rdf:value", default="", namespaces=namespaces).strip()
    rights = root.findtext(".//dcterms:rights", default="", namespaces=namespaces).strip()
    if not title or not author or not language or not rights:
        raise protocol.ProtocolError("Gutenberg RDF metadata is incomplete")
    if language.lower() not in {"en", "eng", "english"}:
        raise protocol.ProtocolError(f"selected document is not English: {language}")
    if "public domain" not in rights.lower():
        raise protocol.ProtocolError(f"selected document lacks public-domain rights marker: {rights}")
    if any(marker in title.lower() for marker in protocol.FORBIDDEN_TITLE_MARKERS):
        raise protocol.ProtocolError(f"selected document appears to be an anthology or collected work: {title}")
    return {"title": title, "author": author, "language": language, "rights": rights}


def _assert_text_boundaries(text_bytes: bytes) -> None:
    start = text_bytes.lower().find(START_MARKER.lower())
    end = text_bytes.lower().rfind(END_MARKER.lower())
    if start < 0 or end <= start:
        raise protocol.ProtocolError("text lacks usable Project Gutenberg boundaries")
    if not text_bytes.decode("utf-8"):
        raise protocol.ProtocolError("text is empty")


def acquire(output_root: Path, repository_root: Path) -> Path:
    output_root = output_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite existing corpus root: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    documents: list[dict[str, Any]] = []
    try:
        selection = list(protocol.SELECTION)
        protocol.write_json(
            staging / "selection-manifest.json",
            {
                "protocol": protocol.PROTOCOL_ID,
                "state_slice": protocol.STATE_SLICE,
                "selection": selection,
                "selection_sha256": protocol.canonical_digest(selection),
            },
        )
        for item in selection:
            ebook_id = int(item["gutenberg_id"])
            text_urls = [
                f"https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt",
                f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}-8.txt",
                f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}.txt",
            ]
            rdf_urls = [
                f"https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.rdf",
                f"https://www.gutenberg.org/ebooks/{ebook_id}.rdf",
            ]
            text_bytes, text_url = _fetch(text_urls)
            rdf_bytes, rdf_url = _fetch(rdf_urls)
            _assert_text_boundaries(text_bytes)
            metadata = _metadata(rdf_bytes)
            text_path = staging / "texts" / f"{ebook_id}.txt"
            rdf_path = staging / "metadata" / f"{ebook_id}.rdf"
            text_path.parent.mkdir(parents=True, exist_ok=True)
            rdf_path.parent.mkdir(parents=True, exist_ok=True)
            text_path.write_bytes(text_bytes)
            rdf_path.write_bytes(rdf_bytes)
            documents.append(
                {
                    "gutenberg_id": ebook_id,
                    "split": item["split"],
                    **metadata,
                    "text_url": text_url,
                    "rdf_url": rdf_url,
                    "text_path": f"texts/{ebook_id}.txt",
                    "metadata_path": f"metadata/{ebook_id}.rdf",
                    "text_bytes": len(text_bytes),
                    "text_sha256": protocol.sha256_bytes(text_bytes),
                    "metadata_bytes": len(rdf_bytes),
                    "metadata_sha256": protocol.sha256_bytes(rdf_bytes),
                }
            )
        if len(documents) != len(protocol.SELECTION):
            raise protocol.ProtocolError("selection/document count mismatch")
        authors_by_split: dict[str, set[str]] = {split: set() for split in protocol.SPLITS}
        for document in documents:
            author = document["author"]
            split = document["split"]
            for other_split, authors in authors_by_split.items():
                if other_split != split and author in authors:
                    raise protocol.ProtocolError(f"author crosses split: {author}")
            authors_by_split[split].add(author)
        manifest = {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "corpus_kind": "project-gutenberg-canonical-text-rdf-v40",
            "selection_sha256": protocol.selection_digest(),
            "documents": sorted(documents, key=lambda value: int(value["gutenberg_id"])),
            "network_used_for_acquisition_only": True,
            "network_used_during_model_execution": False,
            "raw_intermediates_retained": False,
        }
        protocol.write_json(staging / "corpus-manifest.json", manifest)
        if output_root.exists():
            raise protocol.ProtocolError(f"corpus root appeared during acquisition: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = acquire(args.output_root, args.repository_root)
    except (OSError, ET.ParseError, protocol.ProtocolError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    print(json.dumps({"corpus_root": str(root), "selection_sha256": protocol.selection_digest(), "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
