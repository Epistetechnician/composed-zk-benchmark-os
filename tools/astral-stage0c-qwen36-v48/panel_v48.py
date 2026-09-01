#!/usr/bin/env python3
"""Build the sealed V48 state-transition panel without model execution.

State slice: astral-stage0c-cross-view-causal-state-transport-v48.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path

import protocol_v48 as protocol


VIEW1_CODES = ("amber-kite", "birch-lantern", "cobalt-river", "dawn-meadow")
VIEW2_CODES = ("quartz-7", "morrow-3", "sable-9", "tulip-4")
VIEW1_SEED = 481101
VIEW2_SEED = 481202
GENERATOR_SEED = 481303


def _paragraphs(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    candidates = [re.sub(r"\s+", " ", part).strip() for part in re.split(r"\n\s*\n", text)]
    return [part for part in candidates if len(part) >= 900 and not part.startswith("***")]


def _context_window(text: str, document_index: int, family_index: int) -> str:
    paragraphs = _paragraphs(text)
    if not paragraphs:
        raise protocol.ProtocolError("Gutenberg document has no usable prose paragraphs")
    index = (document_index * protocol.FAMILIES_PER_DOCUMENT + family_index) % len(paragraphs)
    value = paragraphs[index]
    return value[:2200]


def _prompt(view: str, code: str, state: int, context: str) -> str:
    if view == "view_1":
        return (
            "You are solving a fixed state-choice task. Respond with only A, B, C, or D.\n"
            "The task state is encoded by the ledger phrase below.\n"
            f"Ledger phrase: {code}\n"
            "Passage:\n"
            f"{context}\n"
            "State payload boundary:\n"
            f"The hidden state index is {state}.\n"
            "Choose the state label:"
        )
    if view == "view_2":
        return (
            "Answer the state routing task with exactly one label: A, B, C, or D.\n"
            "Ignore stylistic details and use the route marker.\n"
            f"Route marker: {code}\n"
            "Source context:\n"
            f"{context}\n"
            "State payload boundary:\n"
            f"Route state code is {state}.\n"
            "Select the route label:"
        )
    raise protocol.ProtocolError(f"unknown view: {view}")


def build(corpus_root: Path, output_root: Path, repository_root: Path) -> Path:
    corpus_root = corpus_root.resolve()
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(corpus_root, repository_root)
    protocol.assert_external(output_root, repository_root)
    if output_root.exists() and any(output_root.iterdir()):
        raise protocol.ProtocolError(f"panel root must be empty: {output_root}")
    corpus_manifest = protocol.read_json(corpus_root / "corpus-manifest.json")
    if corpus_manifest.get("corpus_id") != protocol.CORPUS_ID:
        raise protocol.ProtocolError("unexpected corpus identity")
    documents = corpus_manifest.get("documents")
    if not isinstance(documents, list) or len(documents) != protocol.TOTAL_DOCUMENTS:
        raise protocol.ProtocolError("unexpected corpus document count")

    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        graph = {
            "state_count": protocol.STATE_COUNT,
            "states": [{"state_id": i, "label": protocol.RESPONSE_LABELS[i]} for i in range(protocol.STATE_COUNT)],
            "edges": [{"from": i, "to": (i + 1) % protocol.STATE_COUNT} for i in range(protocol.STATE_COUNT)],
            "generator_seed": GENERATOR_SEED,
            "view_seeds": {"view_1": VIEW1_SEED, "view_2": VIEW2_SEED},
        }
        families: list[dict[str, object]] = []
        for document_index, document in enumerate(documents):
            book_id = int(document["gutenberg_id"])
            relative_text_path = document.get("text_path", f"texts/{book_id}.txt")
            if not isinstance(relative_text_path, str) or Path(relative_text_path).is_absolute():
                raise protocol.ProtocolError("corpus text path must be relative")
            source_path = (corpus_root / relative_text_path).resolve()
            if corpus_root not in source_path.parents or not source_path.is_file():
                raise protocol.ProtocolError(f"corpus text path is outside custody root or missing: {relative_text_path}")
            text = source_path.read_text(encoding="utf-8", errors="replace")
            split = document.get("split")
            if split not in protocol.SPLITS:
                raise protocol.ProtocolError(f"document has invalid sealed split: {split!r}")
            for family_index in range(protocol.FAMILIES_PER_DOCUMENT):
                state = (document_index + family_index) % protocol.STATE_COUNT
                alternate = (state + 1) % protocol.STATE_COUNT
                context = _context_window(text, document_index, family_index)
                views: dict[str, object] = {}
                for view, codes in (("view_1", VIEW1_CODES), ("view_2", VIEW2_CODES)):
                    views[view] = {
                        "receiver_prompt": _prompt(view, codes[state], state, context),
                        "donor_prompt": _prompt(view, codes[alternate], alternate, context),
                        "receiver_state": state,
                        "donor_state": alternate,
                        "codebook_seed": VIEW1_SEED if view == "view_1" else VIEW2_SEED,
                        "anchor_marker": "State payload boundary:",
                    }
                families.append({
                    "family_id": f"v48-{split}-doc{document_index:02d}-family{family_index}",
                    "split": split,
                    "document_index": document_index,
                    "family_index": family_index,
                    "gutenberg_id": book_id,
                    "state": state,
                    "alternate_state": alternate,
                    "state_graph_edge": [state, alternate],
                    "views": views,
                })
        manifest = {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "panel_id": protocol.PANEL_ID,
            "corpus_id": protocol.CORPUS_ID,
            "corpus_manifest_sha256": protocol.sha256_file(corpus_root / "corpus-manifest.json"),
            "state_graph": graph,
            "document_count": protocol.TOTAL_DOCUMENTS,
            "family_count": len(families),
            "families_per_split": {split: sum(1 for family in families if family["split"] == split) for split in protocol.SPLITS},
            "view_ids": list(protocol.VIEWS),
            "selection_rule": "fixed corpus order, four cyclic state edges per document, no model-dependent selection",
        }
        protocol.write_json(staging / "state-graph.json", graph)
        protocol.write_json(staging / "families.json", families)
        manifest["families_sha256"] = protocol.sha256_file(staging / "families.json")
        manifest["manifest_sha256"] = protocol.canonical_digest(manifest)
        protocol.write_json(staging / "panel-manifest.json", manifest)
        if output_root.exists() and any(output_root.iterdir()):
            raise protocol.ProtocolError(f"panel root appeared during execution: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = build(args.corpus_root, args.output_root, args.repository_root)
        print(json.dumps({"panel_root": str(root), "manifest_sha256": protocol.sha256_file(root / "panel-manifest.json"), "valid": True}, indent=2))
    except (OSError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
