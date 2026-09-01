"""Hermetic Project Gutenberg custody tests for Astral V39.

State slice: astral-stage0c-qwen36-layer-effect-v39.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import corpus_v39 as corpus
import fetch_gutenberg_corpus_v39 as fetcher
import validate_gutenberg_corpus_v39 as validator


def selection_payload() -> bytes:
    documents = []
    for index, split in enumerate(corpus.SPLITS):
        for offset in range(corpus.EXPECTED_DOCUMENTS_PER_SPLIT):
            documents.append(
                {
                    "gutenberg_id": 1000 + index * 4 + offset + 1,
                    "split": split,
                }
            )
    return (json.dumps(
        {
            "protocol": corpus.protocol.PROTOCOL_ID,
            "state_slice": corpus.protocol.STATE_SLICE,
            "documents": documents,
        },
        indent=2,
        sort_keys=True,
    ) + "\n").encode("utf-8")


def metadata_payload(gutenberg_id: int) -> bytes:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<rdf:RDF xmlns:pgterms="http://www.gutenberg.org/2009/pgterms/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <pgterms:ebook rdf:about="ebooks/{gutenberg_id}">
    <dcterms:license rdf:resource="license"/>
    <dcterms:rights>Public domain in the USA.</dcterms:rights>
    <dcterms:issued rdf:datatype="http://www.w3.org/2001/XMLSchema#date">1900-01-01</dcterms:issued>
    <dcterms:title>Fixture Book {gutenberg_id}</dcterms:title>
    <dcterms:creator>
      <pgterms:agent rdf:about="2009/agents/1">
        <pgterms:name>Fixture Author</pgterms:name>
      </pgterms:agent>
    </dcterms:creator>
    <dcterms:language>
      <rdf:Description>
        <rdf:value rdf:datatype="http://purl.org/dc/terms/RFC4646">en</rdf:value>
      </rdf:Description>
    </dcterms:language>
  </pgterms:ebook>
</rdf:RDF>
'''.encode("utf-8")


def text_payload(gutenberg_id: int) -> bytes:
    return (
        f"The Project Gutenberg eBook of Fixture Book {gutenberg_id}\n"
        f"Release date: January 1, 1900 [eBook #{gutenberg_id}]\n"
        f"*** START OF THE PROJECT GUTENBERG EBOOK FIXTURE BOOK {gutenberg_id} ***\n"
        f"Unique fixture prose for document {gutenberg_id}.\n"
        f"*** END OF THE PROJECT GUTENBERG EBOOK FIXTURE BOOK {gutenberg_id} ***\n"
    ).encode("utf-8")


class FakeResponse:
    def __init__(self, payload: bytes, final_url: str, status: int = 200) -> None:
        self.payload = payload
        self.final_url = final_url
        self.status = status
        self.offset = 0

    def geturl(self) -> str:
        return self.final_url

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self.payload)
        chunk = self.payload[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


def fake_opener(request, timeout):
    url = request.full_url
    path = url.split("/", 4)[-1]
    if path.endswith(".rdf"):
        gutenberg_id = int(path.split("/")[-1][2:-4])
        return FakeResponse(metadata_payload(gutenberg_id), url)
    gutenberg_id = int(path.split("/")[-1].split(".", 1)[0])
    return FakeResponse(text_payload(gutenberg_id), url)


class GutenbergCorpusV39Tests(unittest.TestCase):
    def test_acquire_and_independent_validate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path = root / "selection.json"
            selection_path.write_bytes(selection_payload())
            repository_root = root / "repository"
            repository_root.mkdir()
            corpus_root = root / "external" / "gutenberg-v39"
            published = fetcher.acquire(
                selection_path,
                corpus_root,
                repository_root,
                opener=fake_opener,
                delay_seconds=0,
                now_fn=lambda: datetime(2026, 8, 26, tzinfo=timezone.utc),
            )
            self.assertEqual(published, corpus_root.resolve())
            receipt = validator.validate(corpus_root, repository_root)
            self.assertTrue(receipt["valid"], receipt)
            self.assertEqual(receipt["classification"], "ExternalCorpusCustodyValid")
            self.assertEqual(len(list((corpus_root / "documents").iterdir())), 12)

    def test_acquisition_refuses_existing_destination_and_repository_child(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path = root / "selection.json"
            selection_path.write_bytes(selection_payload())
            repository_root = root / "repository"
            repository_root.mkdir()
            existing = root / "external"
            existing.mkdir()
            with self.assertRaises(corpus.CorpusError):
                fetcher.acquire(
                    selection_path,
                    existing,
                    repository_root,
                    opener=fake_opener,
                    delay_seconds=0,
                )
            inside = repository_root / "corpus"
            with self.assertRaises(corpus.CorpusError):
                fetcher.acquire(
                    selection_path,
                    inside,
                    repository_root,
                    opener=fake_opener,
                    delay_seconds=0,
                )

    def test_selection_rejects_duplicate_ids_and_wrong_split_census(self) -> None:
        value = json.loads(selection_payload())
        value["documents"][1]["gutenberg_id"] = value["documents"][0]["gutenberg_id"]
        with self.assertRaises(corpus.CorpusError):
            corpus.parse_selection(value)
        value = json.loads(selection_payload())
        value["documents"][4]["split"] = "fit"
        with self.assertRaises(corpus.CorpusError):
            corpus.parse_selection(value)

    def test_fetch_rejects_redirect_outside_gutenberg(self) -> None:
        def escaped_opener(request, timeout):
            return FakeResponse(b"payload", "https://example.invalid/file")

        with self.assertRaises(corpus.CorpusError):
            corpus.fetch_url(
                "https://www.gutenberg.org/ebooks/1.txt.utf-8",
                max_bytes=100,
                user_agent="fixture",
                opener=escaped_opener,
            )

    def test_validator_detects_document_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path = root / "selection.json"
            selection_path.write_bytes(selection_payload())
            repository_root = root / "repository"
            repository_root.mkdir()
            corpus_root = root / "external" / "gutenberg-v39"
            fetcher.acquire(
                selection_path,
                corpus_root,
                repository_root,
                opener=fake_opener,
                delay_seconds=0,
            )
            tampered = corpus_root / "documents" / "1001" / "text.txt"
            tampered.write_bytes(tampered.read_bytes() + b"tampered\n")
            receipt = validator.validate(corpus_root, repository_root)
            self.assertFalse(receipt["valid"])
            self.assertTrue(any("document manifest binding mismatch:1001" in error for error in receipt["errors"]))


if __name__ == "__main__":
    unittest.main()
