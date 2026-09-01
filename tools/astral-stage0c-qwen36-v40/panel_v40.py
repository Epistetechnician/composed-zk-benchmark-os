"""Build the fresh V40 document-derived concept panel.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

This module performs no model execution. It constructs paired ordinary and
counterfactual prompts from the externally sealed corpus and rejects
cross-split excerpt overlap while retaining the raw panel only externally.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import protocol_v40 as protocol


PANEL_ID = "astral-stage0c-qwen36-intervention-conditioned-target-v40-panel-v1"
PANEL_KIND = "document-derived-token-presence-paired-swap-v40"
DEFAULT_MODEL = Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit")
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


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash(*parts: object) -> str:
    return _digest(":".join(str(part) for part in parts).encode("utf-8"))


def _body(text: str) -> str:
    start = START_RE.search(text)
    end = END_RE.search(text, start.end() if start else 0)
    if start is None or end is None or end.start() <= start.end():
        raise protocol.ProtocolError("source text lacks a usable Gutenberg body")
    return text[start.end():end.start()]


def _candidates(text: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line_number, paragraph in enumerate(re.split(r"\n\s*\n", _body(text)), start=1):
        normalized = " ".join(paragraph.split())
        words = WORD_RE.findall(normalized)
        if not 20 <= len(words) <= 120 or len(set(word.lower() for word in words)) < 10:
            continue
        lower_words = [word.lower() for word in words]
        grams = {tuple(lower_words[index:index + 12]) for index in range(len(lower_words) - 11)}
        result.append({"line_number": line_number, "normalized": normalized, "words": words, "lower_words": lower_words, "grams": grams})
    return result


def _choose_candidates(ebook_id: int, candidates: list[dict[str, Any]], used_grams: set[tuple[str, ...]]) -> list[dict[str, Any]]:
    chosen: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=lambda item: _hash(PANEL_ID, "candidate", ebook_id, item["line_number"])):
        if candidate["grams"] & used_grams:
            continue
        if any(candidate["grams"] & other["grams"] for other in chosen):
            continue
        chosen.append(candidate)
        used_grams.update(candidate["grams"])
        if len(chosen) == protocol.FAMILIES_PER_DOCUMENT:
            return chosen
    raise protocol.ProtocolError(f"document {ebook_id} has fewer than {protocol.FAMILIES_PER_DOCUMENT} usable families")


def _choose_target(candidate: dict[str, Any], ebook_id: int, ordinal: int) -> str:
    eligible = sorted(
        {
            word
            for word in candidate["lower_words"]
            if word not in STOPWORDS
            and word.isalpha()
            and 5 <= len(word) <= 12
            and candidate["lower_words"].count(word) == 1
            and re.search(rf"\b{re.escape(word)}\b", candidate["normalized"], flags=re.IGNORECASE) is not None
        },
        key=lambda word: _hash(PANEL_ID, "target", ebook_id, ordinal, word),
    )
    if not eligible:
        raise protocol.ProtocolError(f"document {ebook_id} has no unique target word")
    return eligible[0]


def _choose_distractor(target: str, source_words: set[str], all_words: list[set[str]], ebook_id: int, ordinal: int) -> str:
    options: set[str] = set()
    for words in all_words:
        options.update(word for word in words if word != target and word not in source_words and word not in STOPWORDS and word.isalpha() and len(word) == len(target))
    if not options:
        raise protocol.ProtocolError(f"no equal-length distractor for document {ebook_id}")
    return min(options, key=lambda word: _hash(PANEL_ID, "distractor", ebook_id, ordinal, word))


def _prompt(excerpt: str, target: str, distractor: str, tokenizer: Any) -> str:
    prefix = (
        "Read the passage and choose the option that appears in it.\n"
        f"Passage:\n{excerpt}\n"
        f"A) {target}\n"
        f"B) {distractor}\n"
    )
    suffix = "Answer with A or B.\nAnswer:"
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


def build_registry(corpus_root: Path, tokenizer: Any) -> list[dict[str, Any]]:
    manifest = protocol.read_json(corpus_root / "corpus-manifest.json")
    documents = manifest.get("documents") if isinstance(manifest, dict) else None
    if not isinstance(documents, list) or len(documents) != len(protocol.SELECTION):
        raise protocol.ProtocolError("corpus document manifest is invalid")
    parsed: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    document_words: list[set[str]] = []
    for document in documents:
        text = (corpus_root / str(document["text_path"])).read_text(encoding="utf-8")
        candidates = _candidates(text)
        parsed.append((document, candidates))
        document_words.append({word.lower() for word in WORD_RE.findall(_body(text))})
    used_grams: set[tuple[str, ...]] = set()
    registry: list[dict[str, Any]] = []
    for document, candidates in sorted(parsed, key=lambda item: int(item[0]["gutenberg_id"])):
        ebook_id = int(document["gutenberg_id"])
        chosen = _choose_candidates(ebook_id, candidates, used_grams)
        for ordinal, candidate in enumerate(chosen):
            target = _choose_target(candidate, ebook_id, ordinal)
            distractor = _choose_distractor(target, set(candidate["lower_words"]), document_words, ebook_id, ordinal)
            excerpt = candidate["normalized"]
            counterfactual = re.sub(rf"\b{re.escape(target)}\b", distractor, excerpt, count=1, flags=re.IGNORECASE)
            if counterfactual == excerpt:
                raise protocol.ProtocolError("counterfactual replacement did not change excerpt")
            registry.append(
                {
                    "family_id": f"v40-{document['split']}-doc{ebook_id}-{ordinal:02d}",
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
                    "ordinary_prompt": _prompt(excerpt, target, distractor, tokenizer),
                    "counterfactual_prompt": _prompt(counterfactual, target, distractor, tokenizer),
                    "ordinary_token_length": protocol.FIXED_TOKEN_LENGTH,
                    "counterfactual_token_length": protocol.FIXED_TOKEN_LENGTH,
                    "ordinary_correct_label": "A",
                    "counterfactual_correct_label": "B",
                    "response_tokens": protocol.RESPONSE_TOKENS,
                    "response_position_rule": protocol.RESPONSE_POSITION_RULE,
                }
            )
    registry.sort(key=lambda item: item["family_id"])
    if len(registry) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError(f"expected {protocol.TOTAL_FAMILIES} families, got {len(registry)}")
    return registry


def build_panel(corpus_root: Path, tokenizer: Any, model_manifest_sha256: str, registry: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    corpus_manifest_path = corpus_root / "corpus-manifest.json"
    corpus_manifest = protocol.read_json(corpus_manifest_path)
    registry = registry if registry is not None else build_registry(corpus_root, tokenizer)
    by_split: dict[str, list[str]] = {split: [] for split in protocol.SPLITS}
    by_document: dict[str, list[str]] = {}
    documents_by_split: dict[str, list[int]] = {split: [] for split in protocol.SPLITS}
    authors_by_split: dict[str, list[str]] = {split: [] for split in protocol.SPLITS}
    for family in registry:
        split = family["split"]
        by_split[split].append(family["family_id"])
        by_document.setdefault(str(family["gutenberg_id"]), []).append(family["family_id"])
        if family["gutenberg_id"] not in documents_by_split[split]:
            documents_by_split[split].append(family["gutenberg_id"])
        if family["author"] not in authors_by_split[split]:
            authors_by_split[split].append(family["author"])
    return {
        "panel_id": PANEL_ID,
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "panel_kind": PANEL_KIND,
        "corpus_manifest_sha256": protocol.sha256_file(corpus_manifest_path),
        "model_manifest_sha256": model_manifest_sha256,
        "concept_registry_sha256": _canonical(registry),
        "families_per_document": protocol.FAMILIES_PER_DOCUMENT,
        "families_per_split": protocol.FAMILIES_PER_SPLIT,
        "total_families": protocol.TOTAL_FAMILIES,
        "assessment_effects_present": False,
        "assessment_ready": False,
        "by_split": {split: sorted(values) for split, values in by_split.items()},
        "by_document": {key: sorted(values) for key, values in sorted(by_document.items())},
        "documents_by_split": {split: sorted(values) for split, values in documents_by_split.items()},
        "authors_by_split": {split: sorted(values) for split, values in authors_by_split.items()},
    }


def publish(corpus_root: Path, output_root: Path, model_root: Path, repository_root: Path) -> Path:
    output_root = output_root.resolve()
    model_root = model_root.resolve()
    protocol.assert_external(output_root, repository_root)
    protocol.assert_external(model_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite panel root: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    import shutil

    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        from mlx_lm import load

        model_manifest = protocol.model_manifest(model_root)
        _, tokenizer = load(str(model_root), lazy=True)
        registry = build_registry(corpus_root.resolve(), tokenizer)
        panel_manifest = build_panel(corpus_root.resolve(), tokenizer, model_manifest["manifest_sha256"], registry)
        split_manifest = {
            "panel_id": PANEL_ID,
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "corpus_manifest_sha256": panel_manifest["corpus_manifest_sha256"],
            "model_manifest_sha256": panel_manifest["model_manifest_sha256"],
            "by_split": panel_manifest["by_split"],
            "by_document": panel_manifest["by_document"],
            "documents_by_split": panel_manifest["documents_by_split"],
            "authors_by_split": panel_manifest["authors_by_split"],
        }
        panel_manifest["concept_registry_sha256"] = _canonical(registry)
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
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
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
