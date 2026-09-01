#!/usr/bin/env python3
"""Acquire the fresh V46 Gutenberg corpus.

State slice: astral-stage0c-qwen36-answer-aligned-causal-target-v46.
Network is permitted only for this intake command.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import protocol_v46 as protocol


V45_SOURCE = Path(__file__).resolve().parents[1] / "astral-stage0c-qwen36-v45"
sys.path.insert(0, str(V45_SOURCE))
import acquire_gutenberg_corpus_v45 as intake  # noqa: E402


STATE_SLICE = "astral-stage0c-qwen36-answer-aligned-causal-target-v46"


def acquire(output_root: Path, repository_root: Path) -> Path:
    intake.protocol = protocol
    intake.USER_AGENT = "Astral-V46-corpus-custody/1.0"
    root = intake.acquire(output_root, repository_root)
    manifest_path = root / "corpus-manifest.json"
    manifest = protocol.read_json(manifest_path)
    manifest["corpus_kind"] = "project-gutenberg-canonical-text-rdf-v46"
    protocol.write_json(manifest_path, manifest)
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = acquire(args.output_root, args.repository_root.resolve())
    except (OSError, ValueError, protocol.ProtocolError) as exc:
        print({"valid": False, "error": f"{type(exc).__name__}:{exc}"})
        return 2
    manifest = protocol.read_json(root / "corpus-manifest.json")
    print({"corpus_root": str(root), "selection_sha256": manifest["selection_sha256"], "valid": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
