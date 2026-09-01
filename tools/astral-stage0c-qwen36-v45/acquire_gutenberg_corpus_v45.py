#!/usr/bin/env python3
"""Acquire the fresh V45 Gutenberg corpus.

State slice: astral-stage0c-qwen36-response-anchored-causal-target-v45.
Network is allowed only here. The model is never loaded and no discarded
candidate payload is retained.
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

import protocol_v45 as protocol


START_MARKER = b"*** START OF"
END_MARKER = b"*** END OF"
USER_AGENT = "Astral-V45-corpus-custody/1.0"


def _fetch(urls: list[str]) -> tuple[bytes, str]:
    last_error: Exception | None = None
    for url in urls:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=25) as response:
                return response.read(), url
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
    lowered_title = title.lower()
    if any(marker in lowered_title for marker in protocol.FORBIDDEN_TITLE_MARKERS):
        raise protocol.ProtocolError(f"selected document appears collected or multi-work: {title}")
    return {"title": title, "author": author, "language": language, "rights": rights}


def _canonical_text(payload: bytes) -> bytes:
    text = payload.decode("utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    lower = canonical.lower()
    start = lower.find(START_MARKER.lower())
    end = lower.rfind(END_MARKER.lower())
    if start < 0 or end <= start:
        raise protocol.ProtocolError("text lacks usable Project Gutenberg boundaries")
    return canonical


def _candidate(ebook_id: int) -> dict[str, Any]:
    text_bytes, text_url = _fetch([
        f"https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt",
        f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}-8.txt",
        f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}.txt",
    ])
    rdf_bytes, rdf_url = _fetch([
        f"https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.rdf",
        f"https://www.gutenberg.org/ebooks/{ebook_id}.rdf",
    ])
    canonical_text = _canonical_text(text_bytes)
    metadata = _metadata(rdf_bytes)
    return {
        "gutenberg_id": ebook_id,
        **metadata,
        "text_url": text_url,
        "rdf_url": rdf_url,
        "text_payload": canonical_text,
        "metadata_payload": rdf_bytes,
        "text_sha256": protocol.sha256_bytes(canonical_text),
        "metadata_sha256": protocol.sha256_bytes(rdf_bytes),
    }


def _select(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used_authors: set[str] = set()
    used_ids: set[int] = set()
    for split in protocol.SPLITS:
        split_count = 0
        for candidate in candidates:
            author_key = " ".join(str(candidate["author"]).lower().split())
            ebook_id = int(candidate["gutenberg_id"])
            if split_count == protocol.DOCUMENTS_PER_SPLIT:
                break
            if ebook_id in used_ids or author_key in used_authors:
                continue
            selected.append({**candidate, "split": split, "author_key": author_key})
            used_ids.add(ebook_id)
            used_authors.add(author_key)
            split_count += 1
        if split_count != protocol.DOCUMENTS_PER_SPLIT:
            raise protocol.ProtocolError(f"candidate pool cannot fill {split}: {split_count}")
    return selected


def acquire(output_root: Path, repository_root: Path) -> Path:
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite existing corpus root: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        candidates: list[dict[str, Any]] = []
        attempted: list[int] = []
        rejected: dict[str, str] = {}
        for raw_id in protocol.CANDIDATE_GUTENBERG_IDS:
            ebook_id = int(raw_id)
            if ebook_id in protocol.KNOWN_RESERVED_GUTENBERG_IDS:
                rejected[str(ebook_id)] = "freshness_exclusion"
                continue
            if ebook_id in attempted:
                rejected[str(ebook_id)] = "duplicate_candidate"
                continue
            attempted.append(ebook_id)
            try:
                candidates.append(_candidate(ebook_id))
            except (OSError, ET.ParseError, UnicodeDecodeError, protocol.ProtocolError) as exc:
                rejected[str(ebook_id)] = f"{type(exc).__name__}:{exc}"
        selected = _select(candidates)
        selection = [{"gutenberg_id": int(item["gutenberg_id"]), "split": str(item["split"])} for item in selected]
        protocol.write_json(staging / "selection-manifest.json", {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "selection_algorithm": protocol.SELECTION_ALGORITHM_ID,
            "candidate_pool_sha256": protocol.canonical_digest(list(protocol.CANDIDATE_GUTENBERG_IDS)),
            "selection": selection,
            "selection_sha256": protocol.selection_digest(selection),
            "rejected_candidate_count": len(rejected),
        })
        documents: list[dict[str, Any]] = []
        for item in selected:
            ebook_id = int(item["gutenberg_id"])
            split = str(item["split"])
            text_path = staging / "texts" / f"{ebook_id}.txt"
            metadata_path = staging / "metadata" / f"{ebook_id}.rdf"
            text_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            text_path.write_bytes(item["text_payload"])
            metadata_path.write_bytes(item["metadata_payload"])
            documents.append({
                "gutenberg_id": ebook_id,
                "split": split,
                "title": item["title"],
                "author": item["author"],
                "language": item["language"],
                "rights": item["rights"],
                "text_url": item["text_url"],
                "rdf_url": item["rdf_url"],
                "text_path": f"texts/{ebook_id}.txt",
                "metadata_path": f"metadata/{ebook_id}.rdf",
                "text_bytes": len(item["text_payload"]),
                "text_sha256": item["text_sha256"],
                "metadata_bytes": len(item["metadata_payload"]),
                "metadata_sha256": item["metadata_sha256"],
            })
        selection_manifest_sha256 = protocol.sha256_file(staging / "selection-manifest.json")
        protocol.write_json(staging / "corpus-manifest.json", {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "corpus_kind": "project-gutenberg-canonical-text-rdf-v45",
            "selection_algorithm": protocol.SELECTION_ALGORITHM_ID,
            "candidate_pool_sha256": protocol.canonical_digest(list(protocol.CANDIDATE_GUTENBERG_IDS)),
            "selection_sha256": protocol.selection_digest(selection),
            "selection_manifest_sha256": selection_manifest_sha256,
            "freshness_checked": True,
            "freshness_exclusion_ids": list(protocol.FRESHNESS_EXCLUSION_INVENTORY),
            "freshness_exclusion_sha256": protocol.freshness_exclusion_digest(protocol.FRESHNESS_EXCLUSION_INVENTORY),
            "documents": sorted(documents, key=lambda value: int(value["gutenberg_id"])),
            "network_used_for_acquisition_only": True,
            "network_used_during_model_execution": False,
            "raw_intermediates_retained": False,
            "corpus_validator_receipt_required": True,
        })
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
    except (OSError, ET.ParseError, UnicodeDecodeError, protocol.ProtocolError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    manifest = protocol.read_json(root / "corpus-manifest.json")
    print(json.dumps({"corpus_root": str(root), "selection_sha256": manifest["selection_sha256"], "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
