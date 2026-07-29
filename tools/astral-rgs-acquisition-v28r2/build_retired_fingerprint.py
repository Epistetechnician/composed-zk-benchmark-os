from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


sys.dont_write_bytecode = True
VERSION = "astral.v28r2.retired_r1_fingerprint.v1"
ATOM = re.compile(r"\b(?:[a-z]{2,8}-)?[a-z]{4,}-[0-9a-f]{5,}\b")
HEX = re.compile(r"\b[0-9a-f]{16,}\b")
SPACE = re.compile(r"\s+")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode())


def content_strings(family: dict[str, Any]) -> Iterable[str]:
    for key in ("family_id", "item_id", "namespace", "training_template_family_id"):
        value = family.get(key)
        if isinstance(value, str):
            yield value
    for row in family.get("rows", []):
        if isinstance(row, dict):
            for key in ("anchor", "value"):
                value = row.get(key)
                if isinstance(value, str):
                    yield value
            for key in ("aliases", "wrappers"):
                for value in row.get(key, []):
                    if isinstance(value, str):
                        yield value
    for key in ("source_form", "support_source"):
        entry = family.get(key)
        if isinstance(entry, dict):
            for name in ("text", "sha256"):
                value = entry.get(name)
                if isinstance(value, str):
                    yield value
    for query in family.get("queries", []):
        if not isinstance(query, dict):
            continue
        for key in ("query_id", "question", "prompt", "prompt_sha256", "template_family_id"):
            value = query.get(key)
            if isinstance(value, str):
                yield value
        for option in query.get("answer_options", []):
            if isinstance(option, dict):
                for key in ("text", "sha256"):
                    value = option.get(key)
                    if isinstance(value, str):
                        yield value


def normalize_skeleton(value: str) -> str:
    value = ATOM.sub("<atom>", value.lower())
    value = HEX.sub("<hex>", value)
    value = re.sub(r"\d+", "<n>", value)
    return SPACE.sub(" ", value).strip()


def structural_ngrams(value: str, width: int = 7) -> set[str]:
    tokens = re.findall(r"[a-z]+|<[^>]+>|[.?]", normalize_skeleton(value))
    if len(tokens) < width:
        return set()
    return {
        sha256_text(" ".join(tokens[index : index + width]))
        for index in range(len(tokens) - width + 1)
    }


def normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_skeleton(value)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_value(item) for key, item in value.items()}
    return value


def fingerprint(raw_corpus: dict[str, Any], source_sha256: str) -> dict[str, Any]:
    families = raw_corpus.get("families")
    if not isinstance(families, list) or not families:
        raise ValueError("raw corpus has no families")
    exact: set[str] = set()
    skeletons: set[str] = set()
    ngrams: set[str] = set()
    asts: set[str] = set()
    normalized_asts: set[str] = set()
    for family in families:
        if not isinstance(family, dict):
            raise ValueError("family is not an object")
        for value in content_strings(family):
            exact.add(sha256_text(value))
        text_surfaces: list[str] = []
        for key in ("source_form", "support_source"):
            entry = family.get(key)
            if isinstance(entry, dict) and isinstance(entry.get("text"), str):
                text_surfaces.append(entry["text"])
        for query in family.get("queries", []):
            if isinstance(query, dict):
                text_surfaces.extend(
                    value
                    for value in (query.get("question"), query.get("prompt"))
                    if isinstance(value, str)
                )
        for text in text_surfaces:
            skeletons.add(sha256_text(normalize_skeleton(text)))
            ngrams.update(structural_ngrams(text))
        if isinstance(family.get("semantic_ast"), dict):
            asts.add(sha256_bytes(canonical_bytes(family["semantic_ast"])))
            normalized_asts.add(
                sha256_bytes(canonical_bytes(normalize_value(family["semantic_ast"])))
            )
    body = {
        "version": VERSION,
        "state_slice": "astral-rgs-v28r2-powered-acquisition-novelty-implementation",
        "retired_campaign": "V28R1",
        "source_raw_corpus_sha256": source_sha256,
        "source_raw_corpus_receipt_sha256": raw_corpus.get("receipt_sha256"),
        "source_seed_commitment_sha256": raw_corpus.get("seed_commitment_sha256"),
        "family_count": len(families),
        "exact_string_sha256s": sorted(exact),
        "normalized_surface_skeleton_sha256s": sorted(skeletons),
        "structural_seven_gram_sha256s": sorted(ngrams),
        "semantic_ast_sha256s": sorted(asts),
        "normalized_semantic_ast_sha256s": sorted(normalized_asts),
    }
    body["fingerprint_sha256"] = sha256_bytes(canonical_bytes(body))
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a sealed non-row V28R1 fingerprint for V28R2 intake."
    )
    parser.add_argument("--raw-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    raw_bytes = args.raw_corpus.read_bytes()
    value = json.loads(raw_bytes)
    result = fingerprint(value, sha256_bytes(raw_bytes))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError:
        parser.error("output already exists")
    print(f"fingerprint_sha256={result['fingerprint_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
