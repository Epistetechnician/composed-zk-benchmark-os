#!/usr/bin/env python3
"""Build the fresh V44 document-disjoint measurement panel.

State slice: astral-stage0c-qwen36-causal-target-measurement-invariance-v44.
The panel seals three predeclared wrappers and two input positions for each
family. No model forward pass or intervention effect is performed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import protocol_v44 as protocol


START_RE = re.compile(r"\*\*\* START OF[^\n]*", re.IGNORECASE)
END_RE = re.compile(r"\*\*\* END OF[^\n]*", re.IGNORECASE)
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]{3,}")
STOPWORDS = frozenset(
    "a an and are as at be been but by for from had has have he her his i if in into is it its of on or that the their them then there these they this to was we were what when where which who will with you your project gutenberg".split()
)


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: Any) -> str:
    return _digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def write_json(file_path: Path, value: Any) -> None:
    file_path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash(*parts: object) -> str:
    return _digest(": ".join(str(part) for part in parts).encode("utf-8"))


def _body(text: str) -> str:
    start = START_RE.search(text)
    end = END_RE.search(text, start.end() if start else 0)
    if start is None or end is None or end.start() <= start.end():
        raise protocol.ProtocolError("source text lacks a usable Gutenberg body")
    return text[start.end() : end.start()]


def _candidates(text: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line_number, paragraph in enumerate(re.split(r"\n\s*\n", _body(text)), start=1):
        normalized = " ".join(paragraph.split())
        words = WORD_RE.findall(normalized)
        if not 20 <= len(words) <= 120 or len(set(word.lower() for word in words)) < 10:
            continue
        lower_words = [word.lower() for word in words]
        grams = {tuple(lower_words[index : index + 12]) for index in range(len(lower_words) - 11)}
        result.append({"line_number": line_number, "normalized": normalized, "words": words, "lower_words": lower_words, "grams": grams})
    return result


def _choose_target(candidate: dict[str, Any], ebook_id: int, ordinal: int, forbidden_words: set[str]) -> str:
    eligible = sorted(
        {
            word
            for word in candidate["lower_words"]
            if word not in STOPWORDS
            and word not in forbidden_words
            and word.isalpha()
            and 5 <= len(word) <= 12
            and candidate["lower_words"].count(word) == 1
            and re.search(rf"\b{re.escape(word)}\b", candidate["normalized"], flags=re.IGNORECASE) is not None
        },
        key=lambda word: _hash(protocol.PANEL_ID, "target", ebook_id, ordinal, word),
    )
    if not eligible:
        raise protocol.ProtocolError(f"document {ebook_id} has no unique target word")
    return eligible[0]


def _choose_distractor(
    target: str,
    source_words: set[str],
    all_words: list[set[str]],
    ebook_id: int,
    ordinal: int,
    forbidden_words: set[str],
) -> str:
    options: set[str] = set()
    for words in all_words:
        options.update(
            word
            for word in words
            if word != target
            and word not in source_words
            and word not in forbidden_words
            and word not in STOPWORDS
            and word.isalpha()
            and len(word) == len(target)
        )
    if not options:
        raise protocol.ProtocolError(f"no equal-length distractor for document {ebook_id}")
    return min(options, key=lambda word: _hash(protocol.PANEL_ID, "distractor", ebook_id, ordinal, word))


def _prompt(wrapper: str, excerpt: str, target: str, distractor: str, tokenizer: Any) -> str:
    prefix = (
        f"{protocol.WRAPPER_PREFIXES[wrapper]}\n"
        f"Passage:\n{excerpt}\n"
        f"A) {target}\n"
        f"B) {distractor}\n"
    )
    suffix = "Respond with A or B only.\nAnswer:"
    padding = ""
    padding_tokens = (". ", ", ", "; ", "! ", "? ", ": ", "- ", ") ")
    while True:
        current_length = len(tokenizer.encode(prefix + padding + suffix))
        if current_length == protocol.FIXED_TOKEN_LENGTH:
            return prefix + padding + suffix
        if current_length > protocol.FIXED_TOKEN_LENGTH:
            raise protocol.ProtocolError("prompt exceeds fixed tokenizer length")
        for candidate in padding_tokens:
            candidate_length = len(tokenizer.encode(prefix + padding + candidate + suffix))
            if candidate_length == current_length + 1:
                padding += candidate
                break
        else:
            raise protocol.ProtocolError("cannot reach fixed tokenizer length with deterministic padding")


def _load_manifest(corpus_root: Path) -> dict[str, Any]:
    manifest = protocol.read_json(corpus_root / "corpus-manifest.json")
    selection = protocol.read_json(corpus_root / "selection-manifest.json")
    receipt_path = corpus_root / "validator-receipt.json"
    if not isinstance(manifest, dict) or not isinstance(selection, dict):
        raise protocol.ProtocolError("corpus manifests must be objects")
    if manifest.get("protocol") != protocol.PROTOCOL_ID or manifest.get("state_slice") != protocol.STATE_SLICE:
        raise protocol.ProtocolError("corpus manifest protocol or state slice mismatch")
    if selection.get("selection") != list(protocol.SELECTION) or selection.get("selection_sha256") != protocol.selection_digest():
        raise protocol.ProtocolError("selection manifest does not match V44 selection")
    if manifest.get("selection_sha256") != protocol.selection_digest() or manifest.get("selection_manifest_sha256") != protocol.sha256_file(corpus_root / "selection-manifest.json"):
        raise protocol.ProtocolError("corpus selection binding mismatch")
    if not receipt_path.is_file():
        raise protocol.ProtocolError("independent corpus validator receipt is required")
    receipt = protocol.read_json(receipt_path)
    if receipt.get("protocol") != protocol.PROTOCOL_ID or receipt.get("state_slice") != protocol.STATE_SLICE or receipt.get("valid") is not True or receipt.get("corpus_manifest_sha256") != protocol.sha256_file(corpus_root / "corpus-manifest.json"):
        raise protocol.ProtocolError("independent corpus validator receipt is invalid")
    return manifest


def build_registry(corpus_root: Path, tokenizer: Any) -> list[dict[str, Any]]:
    manifest = _load_manifest(corpus_root)
    documents = manifest.get("documents")
    if not isinstance(documents, list) or len(documents) != protocol.TOTAL_DOCUMENTS:
        raise protocol.ProtocolError("corpus document census is invalid")
    parsed: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    document_words: list[set[str]] = []
    seen_ids: set[int] = set()
    seen_authors: dict[str, str] = {}
    by_split: dict[str, list[dict[str, Any]]] = {split: [] for split in protocol.SPLITS}
    for document in documents:
        if not isinstance(document, dict):
            raise protocol.ProtocolError("corpus document metadata must be an object")
        ebook_id = int(document.get("gutenberg_id", -1))
        split = document.get("split")
        author = str(document.get("author", "")).strip()
        title = str(document.get("title", "")).strip().lower()
        if ebook_id <= 0 or ebook_id in seen_ids or ebook_id in protocol.KNOWN_RESERVED_GUTENBERG_IDS:
            raise protocol.ProtocolError(f"reserved or duplicate Gutenberg ID: {ebook_id}")
        if split not in protocol.SPLITS or not author or not title:
            raise protocol.ProtocolError("corpus document metadata is incomplete")
        if any(marker in title for marker in protocol.FORBIDDEN_TITLE_MARKERS):
            raise protocol.ProtocolError(f"contained or collected work is not eligible: {ebook_id}")
        if author in seen_authors and seen_authors[author] != split:
            raise protocol.ProtocolError(f"author crosses splits: {author}")
        seen_ids.add(ebook_id)
        seen_authors[author] = split
        by_split[split].append(document)
        text_path = corpus_root / str(document.get("text_path", ""))
        if not text_path.is_file() or text_path.is_symlink():
            raise protocol.ProtocolError(f"corpus text is not a regular file: {text_path}")
        text = text_path.read_text(encoding="utf-8")
        if protocol.sha256_file(text_path) != document.get("text_sha256"):
            raise protocol.ProtocolError(f"corpus text digest mismatch: {ebook_id}")
        parsed.append((document, _candidates(text)))
        document_words.append({word.lower() for word in WORD_RE.findall(_body(text))})
    if any(len(by_split[split]) != protocol.DOCUMENTS_PER_SPLIT for split in protocol.SPLITS):
        raise protocol.ProtocolError("corpus documents per split mismatch")

    used_grams: set[tuple[str, ...]] = set()
    used_concepts: set[str] = set()
    registry: list[dict[str, Any]] = []
    for document, candidates in sorted(parsed, key=lambda item: int(item[0]["gutenberg_id"])):
        ebook_id = int(document["gutenberg_id"])
        chosen: list[tuple[dict[str, Any], str, str]] = []
        for candidate in sorted(candidates, key=lambda item: _hash(protocol.PANEL_ID, "candidate", ebook_id, item["line_number"])):
            if candidate["grams"] & used_grams or any(candidate["grams"] & other[0]["grams"] for other in chosen):
                continue
            ordinal = len(chosen)
            try:
                target = _choose_target(candidate, ebook_id, ordinal, used_concepts)
                distractor = _choose_distractor(target, set(candidate["lower_words"]), document_words, ebook_id, ordinal, used_concepts | {target})
                if target == distractor or target in used_concepts or distractor in used_concepts:
                    continue
                chosen.append((candidate, target, distractor))
            except protocol.ProtocolError:
                continue
            if len(chosen) == protocol.FAMILIES_PER_DOCUMENT:
                break
        if len(chosen) != protocol.FAMILIES_PER_DOCUMENT:
            raise protocol.ProtocolError(f"document {ebook_id} has too few usable families")
        for ordinal, (candidate, target, distractor) in enumerate(chosen):
            excerpt = candidate["normalized"]
            counterfactual = re.sub(rf"\b{re.escape(target)}\b", distractor, excerpt, count=1, flags=re.IGNORECASE)
            if counterfactual == excerpt or re.search(rf"\b{re.escape(target)}\b", excerpt, flags=re.IGNORECASE) is None:
                raise protocol.ProtocolError(f"counterfactual replacement failed: {ebook_id}")
            prompts: dict[str, str] = {}
            for wrapper in protocol.WRAPPER_NAMES:
                prompts[f"{wrapper}_ordinary_prompt"] = _prompt(wrapper, excerpt, target, distractor, tokenizer)
                prompts[f"{wrapper}_counterfactual_prompt"] = _prompt(wrapper, counterfactual, target, distractor, tokenizer)
            registry.append({
                "family_id": f"v44-{document['split']}-doc{ebook_id}-{ordinal:02d}",
                "split": document["split"],
                "gutenberg_id": ebook_id,
                "author": document["author"],
                "source_path": document["text_path"],
                "source_sha256": document["text_sha256"],
                "source_line_number": candidate["line_number"],
                "source_excerpt_sha256": _digest(excerpt.encode("utf-8")),
                "source_word_count": len(candidate["words"]),
                "target_word": target,
                "distractor_word": distractor,
                **prompts,
                "ordinary_token_length": protocol.FIXED_TOKEN_LENGTH,
                "counterfactual_token_length": protocol.FIXED_TOKEN_LENGTH,
                "ordinary_correct_label": "A",
                "counterfactual_correct_label": "B",
                "response_tokens": protocol.RESPONSE_TOKENS,
                "response_position_rule": protocol.FIXED_POSITION_RULE,
            })
            used_grams.update(candidate["grams"])
            used_concepts.update({target, distractor})
    registry.sort(key=lambda item: item["family_id"])
    if len(registry) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError(f"expected {protocol.TOTAL_FAMILIES} families, got {len(registry)}")
    return registry


def build_panel(corpus_root: Path, model_manifest_sha256: str, registry: list[dict[str, Any]]) -> dict[str, Any]:
    panel_by_split: dict[str, list[str]] = {split: [] for split in protocol.SPLITS}
    by_document: dict[str, list[str]] = {}
    documents_by_split: dict[str, list[int]] = {split: [] for split in protocol.SPLITS}
    authors_by_split: dict[str, list[str]] = {split: [] for split in protocol.SPLITS}
    for family in registry:
        split = family["split"]
        panel_by_split[split].append(family["family_id"])
        by_document.setdefault(str(family["gutenberg_id"]), []).append(family["family_id"])
        if family["gutenberg_id"] not in documents_by_split[split]:
            documents_by_split[split].append(family["gutenberg_id"])
        if family["author"] not in authors_by_split[split]:
            authors_by_split[split].append(family["author"])
    return {
        "panel_id": protocol.PANEL_ID,
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "panel_kind": "document-derived-three-wrapper-two-position-measurement-invariance-v44",
        "corpus_manifest_sha256": protocol.sha256_file(corpus_root / "corpus-manifest.json"),
        "corpus_validator_receipt_sha256": protocol.sha256_file(corpus_root / "validator-receipt.json"),
        "model_manifest_sha256": model_manifest_sha256,
        "concept_registry_sha256": _canonical(registry),
        "wrapper_names": list(protocol.WRAPPER_NAMES),
        "control_names": list(protocol.CONTROL_NAMES),
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "position_names": list(protocol.POSITION_NAMES),
        "position_offsets": list(protocol.POSITION_OFFSETS),
        "position_rule": protocol.FIXED_POSITION_RULE,
        "families_per_document": protocol.FAMILIES_PER_DOCUMENT,
        "families_per_split": protocol.FAMILIES_PER_SPLIT,
        "total_families": protocol.TOTAL_FAMILIES,
        "assessment_effects_present": False,
        "assessment_ready": False,
        "by_split": {split: sorted(values) for split, values in panel_by_split.items()},
        "by_document": {key: sorted(values) for key, values in sorted(by_document.items())},
        "documents_by_split": {split: sorted(values) for split, values in documents_by_split.items()},
        "authors_by_split": {split: sorted(values) for split, values in authors_by_split.items()},
    }


def publish(corpus_root: Path, output_root: Path, model_root: Path, repository_root: Path) -> Path:
    corpus_root = corpus_root.resolve()
    output_root = output_root.resolve()
    model_root = model_root.resolve()
    protocol.assert_external(corpus_root, repository_root)
    protocol.assert_external(output_root, repository_root)
    protocol.assert_external(model_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite panel root: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        from mlx_lm import load

        model_manifest = protocol.model_manifest(model_root)
        _, tokenizer = load(str(model_root), lazy=True)
        registry = build_registry(corpus_root, tokenizer)
        panel_manifest = build_panel(corpus_root, model_manifest["manifest_sha256"], registry)
        split_manifest = {
            "panel_id": protocol.PANEL_ID,
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "corpus_manifest_sha256": panel_manifest["corpus_manifest_sha256"],
            "corpus_validator_receipt_sha256": panel_manifest["corpus_validator_receipt_sha256"],
            "model_manifest_sha256": panel_manifest["model_manifest_sha256"],
            "wrapper_names": panel_manifest["wrapper_names"],
            "control_names": panel_manifest["control_names"],
            "candidate_layers": panel_manifest["candidate_layers"],
            "position_names": panel_manifest["position_names"],
            "position_offsets": panel_manifest["position_offsets"],
            "position_rule": panel_manifest["position_rule"],
            "by_split": panel_manifest["by_split"],
            "by_document": panel_manifest["by_document"],
            "documents_by_split": panel_manifest["documents_by_split"],
            "authors_by_split": panel_manifest["authors_by_split"],
        }
        write_json(staging / "concept-registry.json", {"protocol": protocol.PROTOCOL_ID, "state_slice": protocol.STATE_SLICE, "families": registry})
        write_json(staging / "split-manifest.json", split_manifest)
        write_json(staging / "panel-manifest.json", panel_manifest)
        if output_root.exists():
            raise protocol.ProtocolError(f"panel root appeared during publication: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"))
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = publish(args.corpus_root, args.output_root, args.model, args.repository_root)
    except (OSError, ImportError, json.JSONDecodeError, protocol.ProtocolError, UnicodeDecodeError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    print(json.dumps({"panel_root": str(root), "families": protocol.TOTAL_FAMILIES, "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
