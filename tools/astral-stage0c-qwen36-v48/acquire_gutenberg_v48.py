#!/usr/bin/env python3
"""Acquire and seal the fresh V48 Gutenberg context corpus.

State slice: astral-stage0c-cross-view-causal-state-transport-v48.
Network is permitted only for this intake script. It never loads a model.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import urllib.request
from pathlib import Path
from typing import Any

import protocol_v48 as protocol


START_MARKER = b"*** START OF"
END_MARKER = b"*** END OF"
USER_AGENT = "astral-v48-corpus-custody/1.1"
MIRROR_ROOT = "rsync://rsync.ibiblio.org/gutenberg-epub/{book_id}/pg{book_id}.{suffix}"


def _fetch(urls: list[str]) -> tuple[bytes, str]:
    last_error: Exception | None = None
    for url in urls:
        match = re.search(r"/pg(\d+)\.(txt|rdf)$", url)
        if match:
            book_id, suffix = int(match.group(1)), match.group(2)
            source = MIRROR_ROOT.format(book_id=book_id, suffix=suffix)
            with tempfile.TemporaryDirectory(prefix="astral-v48-fetch-") as temporary:
                destination = Path(temporary) / f"pg{book_id}.{suffix}"
                command = ["rsync", "--timeout=60", "--contimeout=60", source, str(destination)]
                completed = subprocess.run(command, check=False, capture_output=True, text=True)
                if completed.returncode == 0 and destination.is_file():
                    payload = destination.read_bytes()
                    if payload:
                        return payload, source
                detail = (completed.stderr or completed.stdout).strip()
                last_error = protocol.ProtocolError(f"mirror fetch failed: {source}: {detail}")
                continue
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
            if payload:
                return payload, url
        except Exception as exc:  # pragma: no cover - network failures vary
            last_error = exc
    raise protocol.ProtocolError(f"all Gutenberg URLs failed: {last_error}")


def _fetch_text(book_id: int) -> tuple[bytes, str]:
    payload, url = _fetch([
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-8.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
    ])
    canonical = payload.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    lowered = canonical.lower()
    start = lowered.find(START_MARKER.lower())
    end = lowered.rfind(END_MARKER.lower())
    if start < 0 or end <= start:
        raise protocol.ProtocolError(f"Gutenberg text lacks usable boundaries: {book_id}")
    return canonical, url


def _metadata(rdf_bytes: bytes) -> dict[str, str]:
    root = ET.fromstring(rdf_bytes)
    namespaces = {
        "dcterms": "http://purl.org/dc/terms/",
        "pgterms": "http://www.gutenberg.org/2009/pgterms/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    }
    title = root.findtext(".//dcterms:title", default="", namespaces=namespaces).strip().replace("\r", " ").replace("\n", " ")
    author = root.findtext(".//pgterms:agent/pgterms:name", default="", namespaces=namespaces).strip()
    language_values = root.findall(".//dcterms:language//rdf:value", namespaces=namespaces)
    language = next((value.text or "" for value in language_values if (value.text or "").strip()), "").strip()
    rights = root.findtext(".//dcterms:rights", default="", namespaces=namespaces).strip()
    if not title or not author or not language or not rights:
        raise protocol.ProtocolError("Gutenberg RDF metadata is incomplete")
    if language.lower() not in {"en", "eng", "english"}:
        raise protocol.ProtocolError(f"selected document is not English: {language}")
    if "public domain" not in rights.lower():
        raise protocol.ProtocolError(f"selected document lacks public-domain rights marker: {rights}")
    if any(marker in title.lower() for marker in protocol.FORBIDDEN_TITLE_MARKERS):
        raise protocol.ProtocolError(f"selected document appears collected or non-contextual: {title}")
    return {"title": title, "author": author, "language": language, "rights": rights}


def _candidate(book_id: int) -> dict[str, Any]:
    rdf_bytes, rdf_url = _fetch([
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.rdf",
        f"https://www.gutenberg.org/ebooks/{book_id}.rdf",
    ])
    return {
        "gutenberg_id": book_id,
        **_metadata(rdf_bytes),
        "rdf_url": rdf_url,
        "metadata_payload": rdf_bytes,
    }


def _select(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {int(candidate["gutenberg_id"]): candidate for candidate in candidates}
    if set(by_id) != set(protocol.CORPUS_DOCUMENTS):
        missing = sorted(set(protocol.CORPUS_DOCUMENTS) - set(by_id))
        raise protocol.ProtocolError(f"fixed corpus candidates missing: {missing}")
    return [
        {**by_id[book_id], "split": protocol.SPLITS[index // protocol.DOCUMENTS_PER_SPLIT]}
        for index, book_id in enumerate(protocol.CORPUS_DOCUMENTS)
    ]


def acquire(output_root: Path, repository_root: Path) -> Path:
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite existing corpus root: {output_root}")
    if len(set(protocol.CANDIDATE_GUTENBERG_IDS)) != len(protocol.CANDIDATE_GUTENBERG_IDS):
        raise protocol.ProtocolError("fixed candidate catalog contains duplicate ids")
    if set(protocol.CANDIDATE_GUTENBERG_IDS) & set(protocol.FRESHNESS_EXCLUSION_INVENTORY):
        raise protocol.ProtocolError("candidate catalog overlaps the freshness exclusion inventory")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    candidates: list[dict[str, Any]] = []
    rejected: dict[str, str] = {}
    for raw_id in protocol.CANDIDATE_GUTENBERG_IDS:
        book_id = int(raw_id)
        try:
            candidates.append(_candidate(book_id))
        except (OSError, ET.ParseError, UnicodeDecodeError, protocol.ProtocolError) as exc:
            rejected[str(book_id)] = f"{type(exc).__name__}:{exc}"
    selected = _select(candidates)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        texts = staging / "texts"
        metadata_dir = staging / "metadata"
        texts.mkdir(parents=True)
        metadata_dir.mkdir(parents=True)
        documents: list[dict[str, Any]] = []
        for item in selected:
            book_id = int(item["gutenberg_id"])
            text_payload, text_url = _fetch_text(book_id)
            metadata_payload = item["metadata_payload"]
            text_path = texts / f"{book_id}.txt"
            metadata_path = metadata_dir / f"{book_id}.rdf"
            text_path.write_bytes(text_payload)
            metadata_path.write_bytes(metadata_payload)
            documents.append({
                "gutenberg_id": book_id,
                "split": item["split"],
                "title": item["title"],
                "author": item["author"],
                "language": item["language"],
                "rights": item["rights"],
                "text_url": text_url,
                "rdf_url": item["rdf_url"],
                "text_path": f"texts/{book_id}.txt",
                "metadata_path": f"metadata/{book_id}.rdf",
                "text_bytes": len(text_payload),
                "text_sha256": protocol.sha256_bytes(text_payload),
                "metadata_bytes": len(metadata_payload),
                "metadata_sha256": protocol.sha256_bytes(metadata_payload),
            })
        selection = [{"gutenberg_id": int(item["gutenberg_id"]), "split": str(item["split"])} for item in selected]
        protocol.write_json(staging / "selection-manifest.json", {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "corpus_id": protocol.CORPUS_ID,
            "selection_algorithm": protocol.SELECTION_ALGORITHM_ID,
            "candidate_catalog_sha256": protocol.canonical_digest(list(protocol.CANDIDATE_GUTENBERG_IDS)),
            "selection": selection,
            "selection_sha256": protocol.selection_digest(selection),
            "freshness_exclusion_sha256": protocol.freshness_exclusion_digest(protocol.FRESHNESS_EXCLUSION_INVENTORY),
            "rejected_candidates": rejected,
        })
        selection_manifest_path = staging / "selection-manifest.json"
        manifest = {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "corpus_id": protocol.CORPUS_ID,
            "corpus_kind": "project-gutenberg-canonical-text-rdf-v48",
            "selection_algorithm": protocol.SELECTION_ALGORITHM_ID,
            "candidate_catalog_sha256": protocol.canonical_digest(list(protocol.CANDIDATE_GUTENBERG_IDS)),
            "selection_manifest_sha256": protocol.sha256_file(selection_manifest_path),
            "selection_sha256": protocol.selection_digest(selection),
            "freshness_exclusion_ids": list(protocol.FRESHNESS_EXCLUSION_INVENTORY),
            "freshness_exclusion_sha256": protocol.freshness_exclusion_digest(protocol.FRESHNESS_EXCLUSION_INVENTORY),
            "source": "Project Gutenberg public-domain text and RDF endpoints",
            "documents": sorted(documents, key=lambda value: int(value["gutenberg_id"])),
            "document_count": len(documents),
            "network_used_for_acquisition_only": True,
            "network_used_during_model_execution": False,
            "raw_intermediates_retained": False,
            "corpus_validator_receipt_required": True,
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
        print(json.dumps({"corpus_root": str(root), "manifest_sha256": protocol.sha256_file(root / "corpus-manifest.json"), "valid": True}, indent=2))
    except (OSError, ET.ParseError, UnicodeDecodeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
