#!/usr/bin/env python3
"""Build the sealed V45 canonical-task panel without loading the model.

State slice: astral-stage0c-qwen36-response-anchored-causal-target-v45.
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

import protocol_v45 as protocol


START_RE = re.compile(r"\*\*\* START OF[^\n]*", re.IGNORECASE)
END_RE = re.compile(r"\*\*\* END OF[^\n]*", re.IGNORECASE)
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]{3,}")
STOPWORDS = frozenset(
    "a an and are as at be been but by for from had has have he her his i if in into is it its of on or that the their them then there these they this to was we were what when where which who will with you your project gutenberg".split()
)
PADDING_TOKENS = (". ", ", ", "; ", "! ", "? ", ": ", "- ", ") ")


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: Any) -> str:
    return _digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


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
        if not 20 <= len(words) <= 75 or len(set(word.lower() for word in words)) < 15:
            continue
        lower_words = [word.lower() for word in words]
        grams = {tuple(lower_words[index : index + 16]) for index in range(len(lower_words) - 15)}
        result.append({"line_number": line_number, "normalized": normalized, "words": words, "lower_words": lower_words, "grams": grams})
    return result


def _choose_target(candidate: dict[str, Any], ebook_id: int, ordinal: int, forbidden: set[str]) -> str:
    eligible = sorted({
        word for word in candidate["lower_words"]
        if word not in STOPWORDS and word not in forbidden and word.isalpha()
        and 5 <= len(word) <= 12 and candidate["lower_words"].count(word) == 1
    }, key=lambda word: _canonical([protocol.PANEL_ID, "target", ebook_id, ordinal, word]))
    if not eligible:
        raise protocol.ProtocolError(f"document {ebook_id} has no unique target")
    return eligible[0]


def _token_length(tokenizer: Any, value: str) -> int:
    return len(list(tokenizer.encode(value)))


def _token_lengths(tokenizer: Any, values: list[str]) -> list[int]:
    backend = getattr(getattr(tokenizer, "_tokenizer", None), "backend_tokenizer", None)
    if backend is not None and hasattr(backend, "encode_batch"):
        return [len(encoded.ids) for encoded in backend.encode_batch(values)]
    return [_token_length(tokenizer, value) for value in values]


def _choose_distractor(target: str, excerpt: str, source_words: set[str], all_words: list[set[str]], ebook_id: int, ordinal: int, forbidden: set[str], tokenizer: Any, token_lengths: dict[str, int]) -> str:
    target_length = token_lengths.setdefault(target, _token_length(tokenizer, " " + target))
    options: set[str] = set()
    for words in all_words:
        options.update(
            word for word in words
            if word != target and word not in source_words and word not in forbidden
            and word not in STOPWORDS and word.isalpha() and 5 <= len(word) <= 12
            and token_lengths.setdefault(word, _token_length(tokenizer, " " + word)) == target_length
        )
    if not options:
        raise protocol.ProtocolError(f"no equal-token-length distractor for document {ebook_id}")
    ordered_options = sorted(options, key=lambda word: _canonical([protocol.PANEL_ID, "distractor", ebook_id, ordinal, word]))[:protocol.MAX_DISTRACTOR_OPTIONS]
    suffix = "\nContext boundary:\n"
    option_texts: list[str] = []
    option_metadata: list[tuple[str, str]] = []
    for distractor in ordered_options:
        counterfactual = re.sub(rf"\b{re.escape(target)}\b", distractor, excerpt, count=1, flags=re.IGNORECASE)
        ordinary_prefix = f"{protocol.CANONICAL_WRAPPER}\nPassage:\n{excerpt}"
        counterfactual_prefix = f"{protocol.CANONICAL_WRAPPER}\nPassage:\n{counterfactual}"
        options_text = f"Options:\nA) {target}\nB) {distractor}\nAnswer:"
        option_texts.extend((ordinary_prefix, counterfactual_prefix, ordinary_prefix + suffix + options_text, counterfactual_prefix + suffix + options_text))
        option_metadata.append((distractor, counterfactual))
    lengths = _token_lengths(tokenizer, option_texts)
    for index, (distractor, counterfactual) in enumerate(option_metadata):
        ordinary_prefix_length, counterfactual_prefix_length, ordinary_base_length, counterfactual_base_length = lengths[index * 4 : index * 4 + 4]
        if ordinary_prefix_length != counterfactual_prefix_length:
            continue
        if ordinary_base_length > protocol.FIXED_TOKEN_LENGTH or counterfactual_base_length > protocol.FIXED_TOKEN_LENGTH:
            continue
        try:
            ordinary_prompt, ordinary_anchor = _prompt(excerpt, target, distractor, tokenizer)
            counterfactual_prompt, counterfactual_anchor = _prompt(counterfactual, target, distractor, tokenizer)
        except protocol.ProtocolError:
            continue
        if ordinary_anchor == counterfactual_anchor and len(list(tokenizer.encode(ordinary_prompt))) == protocol.FIXED_TOKEN_LENGTH and len(list(tokenizer.encode(counterfactual_prompt))) == protocol.FIXED_TOKEN_LENGTH:
            return distractor
    raise protocol.ProtocolError(f"no boundary-stable distractor for document {ebook_id}")


def _prompt(excerpt: str, target: str, distractor: str, tokenizer: Any) -> tuple[str, int]:
    prefix = f"{protocol.CANONICAL_WRAPPER}\nPassage:\n{excerpt}"
    boundary_index = _token_length(tokenizer, prefix)
    anchor_index = boundary_index - protocol.CONTENT_ANCHOR_OFFSET
    if anchor_index < 0:
        raise protocol.ProtocolError("content anchor is before prompt start")
    suffix = "\nContext boundary:\n"
    options = f"Options:\nA) {target}\nB) {distractor}\nAnswer:"
    padding = ""
    while True:
        prompt = prefix + suffix + padding + options
        length = _token_length(tokenizer, prompt)
        if length == protocol.FIXED_TOKEN_LENGTH:
            return prompt, anchor_index
        if length > protocol.FIXED_TOKEN_LENGTH:
            raise protocol.ProtocolError("canonical prompt exceeds fixed token length")
        current = _token_length(tokenizer, prefix + suffix + padding + options)
        for candidate in PADDING_TOKENS:
            trial = prefix + suffix + padding + candidate + options
            trial_length = _token_length(tokenizer, trial)
            if trial_length == current + 1:
                padding += candidate
                break
        else:
            raise protocol.ProtocolError("cannot deterministically pad canonical prompt")


def _load_corpus(corpus_root: Path) -> dict[str, Any]:
    manifest = protocol.read_json(corpus_root / "corpus-manifest.json")
    selection = protocol.read_json(corpus_root / "selection-manifest.json")
    receipt = protocol.read_json(corpus_root / "validator-receipt.json") if (corpus_root / "validator-receipt.json").is_file() else None
    if not isinstance(manifest, dict) or not isinstance(selection, dict) or not isinstance(receipt, dict):
        raise protocol.ProtocolError("validated corpus manifests are required")
    if manifest.get("protocol") != protocol.PROTOCOL_ID or manifest.get("state_slice") != protocol.STATE_SLICE:
        raise protocol.ProtocolError("corpus protocol binding mismatch")
    if receipt.get("valid") is not True or receipt.get("corpus_manifest_sha256") != protocol.sha256_file(corpus_root / "corpus-manifest.json"):
        raise protocol.ProtocolError("independent corpus receipt is invalid")
    if selection.get("selection_sha256") != manifest.get("selection_sha256"):
        raise protocol.ProtocolError("selection digest mismatch")
    return manifest


def build_registry(corpus_root: Path, tokenizer: Any) -> list[dict[str, Any]]:
    manifest = _load_corpus(corpus_root)
    documents = manifest.get("documents")
    if not isinstance(documents, list) or len(documents) != protocol.TOTAL_DOCUMENTS:
        raise protocol.ProtocolError("corpus document census is invalid")
    parsed: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    document_words: list[set[str]] = []
    token_lengths: dict[str, int] = {}
    used_ids: set[int] = set()
    used_authors: set[str] = set()
    by_split: dict[str, list[dict[str, Any]]] = {split: [] for split in protocol.SPLITS}
    for document in documents:
        if not isinstance(document, dict):
            raise protocol.ProtocolError("document metadata must be an object")
        ebook_id = int(document.get("gutenberg_id", -1))
        split = str(document.get("split", ""))
        author = " ".join(str(document.get("author", "")).split())
        title = str(document.get("title", "")).strip().lower()
        if ebook_id <= 0 or ebook_id in used_ids or ebook_id not in protocol.CANDIDATE_GUTENBERG_IDS:
            raise protocol.ProtocolError(f"invalid or duplicate corpus ID: {ebook_id}")
        if ebook_id in protocol.KNOWN_RESERVED_GUTENBERG_IDS or split not in protocol.SPLITS or not author or not title:
            raise protocol.ProtocolError(f"corpus metadata violates V45 custody: {ebook_id}")
        if any(marker in title for marker in protocol.FORBIDDEN_TITLE_MARKERS):
            raise protocol.ProtocolError(f"multi-work title is not eligible: {ebook_id}")
        if author.lower() in used_authors:
            raise protocol.ProtocolError(f"author is not unique across V45 documents: {author}")
        used_ids.add(ebook_id)
        used_authors.add(author.lower())
        by_split[split].append(document)
        text_path = corpus_root / str(document.get("text_path", ""))
        if not text_path.is_file() or text_path.is_symlink() or protocol.sha256_file(text_path) != document.get("text_sha256"):
            raise protocol.ProtocolError(f"source text custody failure: {ebook_id}")
        text = text_path.read_text(encoding="utf-8")
        parsed.append((document, _candidates(text)))
        document_words.append({word.lower() for word in WORD_RE.findall(_body(text))})
    vocabulary = sorted({
        word for words in document_words for word in words
        if word not in STOPWORDS and word.isalpha() and 5 <= len(word) <= 12
    })
    for start in range(0, len(vocabulary), 2048):
        chunk = vocabulary[start : start + 2048]
        token_lengths.update(dict(zip(chunk, _token_lengths(tokenizer, [" " + word for word in chunk]))))
    if any(len(by_split[split]) != protocol.DOCUMENTS_PER_SPLIT for split in protocol.SPLITS):
        raise protocol.ProtocolError("documents per split mismatch")

    used_grams: set[tuple[str, ...]] = set()
    used_concepts: set[str] = set()
    registry: list[dict[str, Any]] = []
    for document, candidates in sorted(parsed, key=lambda item: int(item[0]["gutenberg_id"])):
        ebook_id = int(document["gutenberg_id"])
        chosen: list[tuple[dict[str, Any], str, str]] = []
        ordered_candidates = sorted(candidates, key=lambda item: _canonical([protocol.PANEL_ID, "candidate", ebook_id, item["line_number"]]))[:protocol.MAX_PANEL_CANDIDATE_PARAGRAPHS]
        for candidate in ordered_candidates:
            if candidate["grams"] & used_grams or any(candidate["grams"] & other[0]["grams"] for other in chosen):
                continue
            ordinal = len(chosen)
            try:
                target = _choose_target(candidate, ebook_id, ordinal, used_concepts)
                distractor = _choose_distractor(target, candidate["normalized"], set(candidate["lower_words"]), document_words, ebook_id, ordinal, used_concepts | {target}, tokenizer, token_lengths)
                if target == distractor or target in used_concepts or distractor in used_concepts:
                    continue
            except protocol.ProtocolError:
                continue
            chosen.append((candidate, target, distractor))
            if len(chosen) == protocol.FAMILIES_PER_DOCUMENT:
                break
        if len(chosen) != protocol.FAMILIES_PER_DOCUMENT:
            raise protocol.ProtocolError(f"document {ebook_id} has too few usable families")
        for ordinal, (candidate, target, distractor) in enumerate(chosen):
            excerpt = candidate["normalized"]
            counterfactual = re.sub(rf"\b{re.escape(target)}\b", distractor, excerpt, count=1, flags=re.IGNORECASE)
            ordinary_prompt, ordinary_anchor = _prompt(excerpt, target, distractor, tokenizer)
            counterfactual_prompt, counterfactual_anchor = _prompt(counterfactual, target, distractor, tokenizer)
            if ordinary_anchor != counterfactual_anchor or _token_length(tokenizer, ordinary_prompt) != protocol.FIXED_TOKEN_LENGTH or _token_length(tokenizer, counterfactual_prompt) != protocol.FIXED_TOKEN_LENGTH:
                raise protocol.ProtocolError(f"anchor or prompt length mismatch: {ebook_id}")
            registry.append({
                "family_id": f"v45-{document['split']}-doc{ebook_id}-{ordinal:02d}",
                "split": document["split"],
                "gutenberg_id": ebook_id,
                "author": document["author"],
                "title": document["title"],
                "source_path": document["text_path"],
                "source_sha256": document["text_sha256"],
                "source_line_number": candidate["line_number"],
                "source_excerpt_sha256": _digest(excerpt.encode("utf-8")),
                "source_word_count": len(candidate["words"]),
                "target_word": target,
                "distractor_word": distractor,
                "canonical_wrapper": protocol.CANONICAL_WRAPPER,
                "ordinary_prompt": ordinary_prompt,
                "counterfactual_prompt": counterfactual_prompt,
                "ordinary_content_anchor_index": ordinary_anchor,
                "counterfactual_content_anchor_index": counterfactual_anchor,
                "ordinary_token_length": protocol.FIXED_TOKEN_LENGTH,
                "counterfactual_token_length": protocol.FIXED_TOKEN_LENGTH,
                "ordinary_correct_label": "A",
                "counterfactual_correct_label": "B",
                "response_tokens": protocol.RESPONSE_TOKENS,
                "position_rule": protocol.POSITION_RULE,
            })
            used_grams.update(candidate["grams"])
            used_concepts.update({target, distractor})
    registry.sort(key=lambda item: item["family_id"])
    if len(registry) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError(f"expected {protocol.TOTAL_FAMILIES} families, got {len(registry)}")
    return registry


def publish(corpus_root: Path, output_root: Path, model_root: Path, repository_root: Path) -> Path:
    corpus_root = corpus_root.resolve()
    output_root = output_root.resolve()
    model_root = model_root.resolve()
    protocol.assert_external(corpus_root, repository_root)
    protocol.assert_external(output_root, repository_root)
    protocol.assert_external(model_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite panel root: {output_root}")
    from mlx_lm import load

    _, tokenizer = load(str(model_root), lazy=True)
    manifest = _load_corpus(corpus_root)
    model_manifest = protocol.model_manifest(model_root)
    registry = build_registry(corpus_root, tokenizer)
    by_split = {split: sorted(family["family_id"] for family in registry if family["split"] == split) for split in protocol.SPLITS}
    by_document: dict[str, list[str]] = {}
    documents_by_split: dict[str, list[int]] = {split: [] for split in protocol.SPLITS}
    authors_by_split: dict[str, list[str]] = {split: [] for split in protocol.SPLITS}
    for family in registry:
        by_document.setdefault(str(family["gutenberg_id"]), []).append(family["family_id"])
        if family["gutenberg_id"] not in documents_by_split[family["split"]]:
            documents_by_split[family["split"]].append(family["gutenberg_id"])
        if family["author"] not in authors_by_split[family["split"]]:
            authors_by_split[family["split"]].append(family["author"])
    panel = {
        "panel_id": protocol.PANEL_ID,
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "panel_kind": "document-derived-canonical-task-content-anchor-v45",
        "corpus_manifest_sha256": protocol.sha256_file(corpus_root / "corpus-manifest.json"),
        "corpus_validator_receipt_sha256": protocol.sha256_file(corpus_root / "validator-receipt.json"),
        "model_manifest_sha256": model_manifest["manifest_sha256"],
        "concept_registry_sha256": _canonical(registry),
        "canonical_wrapper": protocol.CANONICAL_WRAPPER,
        "control_names": list(protocol.CONTROL_NAMES),
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "position_name": protocol.POSITION_NAME,
        "content_anchor_offset": protocol.CONTENT_ANCHOR_OFFSET,
        "position_rule": protocol.POSITION_RULE,
        "feature_map_id": protocol.FEATURE_MAP_ID,
        "ridge_alphas": list(protocol.RIDGE_ALPHAS),
        "families_per_document": protocol.FAMILIES_PER_DOCUMENT,
        "families_per_split": protocol.FAMILIES_PER_SPLIT,
        "total_families": protocol.TOTAL_FAMILIES,
        "assessment_effects_present": False,
        "assessment_ready": False,
        "by_split": by_split,
        "by_document": {key: sorted(value) for key, value in sorted(by_document.items())},
        "documents_by_split": {split: sorted(value) for split, value in documents_by_split.items()},
        "authors_by_split": {split: sorted(value) for split, value in authors_by_split.items()},
    }
    split_manifest = {key: panel[key] for key in ("panel_id", "protocol", "state_slice", "corpus_validator_receipt_sha256", "by_split", "by_document", "documents_by_split", "authors_by_split")}
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        protocol.write_json(staging / "concept-registry.json", {"protocol": protocol.PROTOCOL_ID, "state_slice": protocol.STATE_SLICE, "families": registry})
        protocol.write_json(staging / "panel-manifest.json", panel)
        protocol.write_json(staging / "split-manifest.json", split_manifest)
        if output_root.exists():
            raise protocol.ProtocolError(f"panel root appeared during execution: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = publish(args.corpus_root, args.output_root, args.model, args.repository_root)
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    print(json.dumps({"panel_root": str(root), "panel_manifest_sha256": protocol.sha256_file(root / "panel-manifest.json"), "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
