#!/usr/bin/env python3
"""Build the sealed V46 answer-aligned panel without model execution.

State slice: astral-stage0c-qwen36-answer-aligned-causal-target-v46.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import protocol_v46 as protocol


V45_SOURCE = Path(__file__).resolve().parents[1] / "astral-stage0c-qwen36-v45"
sys.path.insert(0, str(V45_SOURCE))
import panel_v45 as panel_engine  # noqa: E402


def _v46_registry(corpus_root: Path, tokenizer: object) -> list[dict[str, object]]:
    registry = panel_engine._V46_ORIGINAL_BUILD_REGISTRY(corpus_root, tokenizer)
    for family in registry:
        family["family_id"] = str(family["family_id"]).replace("v45-", "v46-", 1)
    return registry


def publish(corpus_root: Path, output_root: Path, model_root: Path, repository_root: Path) -> Path:
    panel_engine.protocol = protocol
    if not hasattr(panel_engine, "_V46_ORIGINAL_BUILD_REGISTRY"):
        panel_engine._V46_ORIGINAL_BUILD_REGISTRY = panel_engine.build_registry
    panel_engine.build_registry = _v46_registry
    root = panel_engine.publish(corpus_root, output_root, model_root, repository_root)
    manifest_path = root / "panel-manifest.json"
    manifest = protocol.read_json(manifest_path)
    manifest["panel_kind"] = "document-derived-answer-aligned-content-anchor-v46"
    protocol.write_json(manifest_path, manifest)
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = publish(args.corpus_root, args.output_root, args.model, args.repository_root.resolve())
    except (OSError, ImportError, KeyError, TypeError, ValueError, protocol.ProtocolError) as exc:
        print({"valid": False, "error": f"{type(exc).__name__}:{exc}"})
        return 2
    print({"panel_root": str(root), "panel_manifest_sha256": protocol.sha256_file(root / "panel-manifest.json"), "valid": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
