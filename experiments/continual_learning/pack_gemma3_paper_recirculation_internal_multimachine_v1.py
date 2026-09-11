#!/usr/bin/env python3
"""Pack a bounded, lineage-preserving internal recirculation corpus.

State slice: continual-learning-gemma3-paper-recirculation-internal-multimachine-v1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "continual-learning-gemma3-paper-recirculation-internal-multimachine-v1"
WINDOW_TOKENS = 1024
WINDOW_LIMIT = 16


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def read_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing source manifest: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("source corpus is not a 1024-token corpus")
    for split in ("fit_windows", "assessment_windows"):
        if not isinstance(value.get(split), list) or len(value[split]) < WINDOW_LIMIT:
            raise ValueError(f"source corpus lacks {split}")
    return value


def select_entries(source: dict[str, Any], split: str, start: int) -> list[dict[str, Any]]:
    entries = source[f"{split}_windows"][start : start + WINDOW_LIMIT]
    if len(entries) != WINDOW_LIMIT:
        raise ValueError(f"source {split} range is incomplete")
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for ordinal, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError("source entry is not an object")
        identity = (entry.get("dataset"), entry.get("document_id"))
        if not all(isinstance(item, str) and item for item in identity) or identity in seen:
            raise ValueError(f"duplicate or invalid {split} identity")
        if entry.get("token_count") != WINDOW_TOKENS or not isinstance(entry.get("path"), str):
            raise ValueError(f"invalid {split} token/path contract")
        seen.add(identity)
        selected.append({**entry, "window_ordinal": ordinal})
    return selected


def pack(source_root: Path, output_root: Path, fit_start: int, assessment_start: int) -> dict[str, Any]:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(source_root)
    if output_root.exists() or output_root == REPO_ROOT or REPO_ROOT in output_root.parents:
        raise ValueError("output must be a new external root")
    source_manifest_path = source_root / "manifest.json"
    source = read_manifest(source_manifest_path)
    fit = select_entries(source, "fit", fit_start)
    assessment = select_entries(source, "assessment", assessment_start)
    fit_ids = {(item["dataset"], item["document_id"]) for item in fit}
    assessment_ids = {(item["dataset"], item["document_id"]) for item in assessment}
    if fit_ids & assessment_ids:
        raise ValueError("fit and assessment identities overlap")
    output_root.mkdir(parents=True)
    for split, entries in (("fit", fit), ("assessment", assessment)):
        (output_root / split).mkdir()
        for ordinal, entry in enumerate(entries):
            source_path = (source_root / entry["path"]).resolve()
            if source_root not in source_path.parents or not source_path.is_file() or source_path.is_symlink():
                raise ValueError(f"unsafe source path: {entry['path']}")
            text = source_path.read_text(encoding="utf-8")
            if hashlib.sha256(text.encode("utf-8")).hexdigest() != entry.get("text_sha256"):
                raise ValueError(f"source text digest mismatch: {entry['path']}")
            target_rel = f"{split}/window-{ordinal:06d}.txt"
            target = output_root / target_rel
            target.write_text(text, encoding="utf-8")
            entry["path"] = target_rel
            entry["byte_len"] = len(text.encode("utf-8"))
            entry["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            entry["token_count"] = WINDOW_TOKENS
    body = {
        "schema": "gemma3-paper-recirculation-internal-multimachine-v1-corpus",
        "state_slice": STATE_SLICE,
        "window_token_count": WINDOW_TOKENS,
        "fit_window_count": WINDOW_LIMIT,
        "assessment_window_count": WINDOW_LIMIT,
        "fit": fit,
        "assessment": assessment,
        "source_schema": source.get("schema"),
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "source_fit_start": fit_start,
        "source_assessment_start": assessment_start,
        "source_window_count": WINDOW_LIMIT,
        "prior_source_reused": True,
        "network_access": False,
        "training": False,
        "evidence_ledger_mutation": False,
    }
    body["manifest_sha256"] = digest(body)
    (output_root / "manifest.json").write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fit-start", type=int, default=16)
    parser.add_argument("--assessment-start", type=int, default=16)
    args = parser.parse_args()
    print(json.dumps(pack(args.source_root, args.output, args.fit_start, args.assessment_start), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
