#!/usr/bin/env python3
"""Acquire an external Project Gutenberg corpus bundle for Astral V39.

State slice: astral-stage0c-qwen36-layer-effect-v39.

The operator supplies an explicit selection manifest containing exactly twelve
Project Gutenberg ebook IDs and four document assignments to each fit, tune,
and assessment split. This command downloads only the canonical UTF-8 text
and per-ebook RDF metadata, validates both, writes a digest-bound external
bundle, and never creates scientific concepts or opens an assessment.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_v39 as corpus


DEFAULT_USER_AGENT = (
    "astral-stage0c-qwen36-v39-corpus-fetch/1.0 "
    "(research custody; Project Gutenberg client)"
)


def acquire(
    selection_path: Path,
    output_root: Path,
    repository_root: Path,
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout_seconds: float = corpus.DEFAULT_TIMEOUT_SECONDS,
    delay_seconds: float = corpus.DEFAULT_DELAY_SECONDS,
    opener: Callable[..., Any] = corpus.urlopen,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> Path:
    """Download and atomically publish one new external corpus bundle."""

    selection_payload = selection_path.read_bytes()
    selection = corpus.parse_selection(corpus.strict_json_bytes(selection_payload))
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    corpus.assert_external(output_root, repository_root)
    if output_root.exists():
        raise corpus.CorpusError(
            f"refusing to overwrite existing corpus root: {output_root}"
        )
    if not user_agent.strip():
        raise corpus.CorpusError("user agent must not be empty")
    if timeout_seconds <= 0 or delay_seconds < 0:
        raise corpus.CorpusError("timeout must be positive and delay must be nonnegative")

    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent))
    )
    retrieved_at = now_fn().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    documents: list[dict[str, Any]] = []
    try:
        documents_root = staging / "documents"
        documents_root.mkdir()
        for index, selected in enumerate(selection):
            if index and delay_seconds:
                sleep_fn(delay_seconds)
            gutenberg_id = selected["gutenberg_id"]
            urls = corpus.document_urls(gutenberg_id)
            metadata_bytes, _ = corpus.fetch_url(
                urls["metadata_url"],
                max_bytes=corpus.MAX_METADATA_BYTES,
                timeout_seconds=timeout_seconds,
                user_agent=user_agent,
                opener=opener,
            )
            text_bytes, _ = corpus.fetch_url(
                urls["text_url"],
                max_bytes=corpus.MAX_TEXT_BYTES,
                timeout_seconds=timeout_seconds,
                user_agent=user_agent,
                opener=opener,
            )
            metadata = corpus.parse_metadata(metadata_bytes, gutenberg_id)
            corpus.validate_text(text_bytes, gutenberg_id)
            if metadata["language"] != corpus.DEFAULT_LANGUAGE:
                raise corpus.CorpusError(
                    f"ebook {gutenberg_id} language is {metadata['language']!r}, expected "
                    f"{corpus.DEFAULT_LANGUAGE!r}"
                )
            document_root = documents_root / str(gutenberg_id)
            document_root.mkdir()
            text_path = document_root / "text.txt"
            metadata_path = document_root / "metadata.rdf"
            text_path.write_bytes(text_bytes)
            metadata_path.write_bytes(metadata_bytes)
            documents.append(
                {
                    "gutenberg_id": gutenberg_id,
                    "split": selected["split"],
                    "title": metadata["title"],
                    "authors": metadata["authors"],
                    "language": metadata["language"],
                    "rights": metadata["rights"],
                    "license_url": corpus.GUTENBERG_LICENSE_URL,
                    **urls,
                    "text_path": f"documents/{gutenberg_id}/text.txt",
                    "metadata_path": f"documents/{gutenberg_id}/metadata.rdf",
                    "text_byte_len": len(text_bytes),
                    "text_sha256": corpus.sha256_bytes(text_bytes),
                    "metadata_byte_len": len(metadata_bytes),
                    "metadata_sha256": corpus.sha256_bytes(metadata_bytes),
                }
            )
        split_counts = {
            split: sum(item["split"] == split for item in documents)
            for split in corpus.SPLITS
        }
        manifest = {
            "protocol": corpus.protocol.PROTOCOL_ID,
            "state_slice": corpus.protocol.STATE_SLICE,
            "corpus_kind": corpus.CORPUS_KIND,
            "claim_ceiling": corpus.CORPUS_CLAIM_CEILING,
            "selection_manifest_sha256": corpus.sha256_bytes(selection_payload),
            "document_count": len(documents),
            "documents_per_split": corpus.EXPECTED_DOCUMENTS_PER_SPLIT,
            "split_counts": split_counts,
            "documents": documents,
            "concept_registry_sha256": None,
            "assessment_ready": False,
            "raw_documents_retained_externally": True,
            "retrieved_at_utc": retrieved_at,
        }
        corpus.write_json(staging / "corpus-manifest.json", manifest)
        manifest_digest = corpus.sha256_file(staging / "corpus-manifest.json")
        (staging / "corpus-manifest.sha256").write_text(
            f"{manifest_digest}  corpus-manifest.json\n", encoding="utf-8"
        )
        (staging / "selection-manifest.json").write_bytes(selection_payload)
        if output_root.exists():
            raise corpus.CorpusError(
                f"output root appeared during acquisition: {output_root}"
            )
        staging.rename(output_root)
        return output_root
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--timeout-seconds", type=float, default=corpus.DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--delay-seconds", type=float, default=corpus.DEFAULT_DELAY_SECONDS)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    args = parser.parse_args(argv)
    try:
        root = acquire(
            args.selection_manifest.resolve(),
            args.output_root,
            args.repository_root,
            user_agent=args.user_agent,
            timeout_seconds=args.timeout_seconds,
            delay_seconds=args.delay_seconds,
        )
    except (OSError, corpus.CorpusError) as exc:
        parser.error(str(exc))
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
