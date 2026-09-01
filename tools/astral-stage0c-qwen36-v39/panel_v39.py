"""Pure-data V39 document-derived panel construction and validation.

State slice: astral-stage0c-qwen36-layer-effect-v39.

This module creates a fresh, deterministic lexical-presence panel from the
external Gutenberg corpus. It performs no model execution. The construction
is intentionally explicit: the scientific target is later measured by
swapping the paired ordinary/counterfactual layer-19 final activations, while
the unrelated same-document replacement is retained as a matched negative
control.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import corpus_v39 as corpus


PANEL_ID = "astral-stage0c-qwen36-layer-effect-v39-panel-v1"
STATE_SLICE = corpus.protocol.STATE_SLICE
PANEL_KIND = "document-derived-token-presence-paired-swap-v1"
EXPECTED_FAMILY_COUNT = 48
EXPECTED_FAMILIES_PER_DOCUMENT = 4
EXPECTED_FAMILIES_PER_SPLIT = 16
RESPONSE_LABELS = ("A", "B")
RESPONSE_TOKENS = {"A": " A", "B": " B"}
RESPONSE_POSITION_RULE = "last_input_position_before_response"
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]{3,}")
STOPWORDS = frozenset(
    "a an and are as at be been but by for from had has have he her his i if in "
    "into is it its of on or that the their them then there these they this to "
    "was we were what when where which who will with you your project gutenberg".split()
)
START_RE = re.compile(r"\*\*\* START OF[^\n]*", re.IGNORECASE)
END_RE = re.compile(r"\*\*\* END OF[^\n]*", re.IGNORECASE)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_digest(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _candidate_lines(text_bytes: bytes) -> tuple[str, list[dict[str, Any]]]:
    text = text_bytes.decode("utf-8")
    start = START_RE.search(text)
    end = END_RE.search(text, start.end() if start else 0)
    if start is None or end is None or end.start() <= start.end():
        raise corpus.CorpusError("source text has no usable Project Gutenberg body")
    body_start = start.end()
    body = text[body_start:end.start()]
    candidates: list[dict[str, Any]] = []
    paragraph: list[dict[str, Any]] = []
    cursor = body_start
    byte_cursor = len(text[:body_start].encode("utf-8"))

    def flush_paragraph() -> None:
        if not paragraph:
            return
        for start in range(len(paragraph)):
            for width in (2, 3, 4):
                selected = paragraph[start:start + width]
                if len(selected) != width:
                    continue
                raw = "".join(item["line"] for item in selected).rstrip("\r\n")
                normalized = re.sub(r"\s+", " ", raw).strip()
                words = WORD_RE.findall(normalized)
                lower = [word.lower() for word in words]
                if not 15 <= len(words) <= 48:
                    continue
                if "http://" in normalized.lower() or "https://" in normalized.lower():
                    continue
                if normalized.startswith(("[Illustration", "[Image", "***")):
                    continue
                if len(set(lower)) < 8:
                    continue
                source_start = selected[0]["byte_start"]
                source_end = selected[-1]["byte_end"]
                candidates.append(
                    {
                        "line_number": selected[0]["line_number"],
                        "raw": raw,
                        "normalized": normalized,
                        "words": words,
                        "lower_words": lower,
                        "byte_start": source_start,
                        "byte_end": source_end,
                    }
                )

    for line_number, line in enumerate(body.splitlines(keepends=True), start=1):
        raw_line = line.rstrip("\r\n")
        if not raw_line.strip():
            flush_paragraph()
            paragraph.clear()
            cursor += len(line)
            byte_cursor += len(line.encode("utf-8"))
            continue
        raw_line_bytes = raw_line.encode("utf-8")
        paragraph.append(
            {
                "line_number": line_number,
                "line": line,
                "byte_start": byte_cursor,
                "byte_end": byte_cursor + len(raw_line_bytes),
            }
        )
        cursor += len(line)
        byte_cursor += len(line.encode("utf-8"))
    flush_paragraph()
    return text, candidates


def _ngrams(words: list[str], size: int = 12) -> set[tuple[str, ...]]:
    return {
        tuple(words[index:index + size])
        for index in range(max(0, len(words) - size + 1))
    }


def _choose_candidates(
    gutenberg_id: int,
    candidates: list[dict[str, Any]],
    used_ngrams: set[tuple[str, ...]],
) -> list[dict[str, Any]]:
    ordered = sorted(
        candidates,
        key=lambda item: sha256_bytes(
            f"{PANEL_ID}:candidate:{gutenberg_id}:{item['line_number']}".encode()
        ),
    )
    chosen: list[dict[str, Any]] = []
    for candidate in ordered:
        candidate_ngrams = _ngrams(candidate["lower_words"])
        if candidate_ngrams & used_ngrams:
            continue
        if any(candidate_ngrams & _ngrams(item["lower_words"]) for item in chosen):
            continue
        chosen.append(candidate)
        used_ngrams.update(candidate_ngrams)
        if len(chosen) == EXPECTED_FAMILIES_PER_DOCUMENT:
            return chosen
    raise corpus.CorpusError(
        f"document {gutenberg_id} has fewer than "
        f"{EXPECTED_FAMILIES_PER_DOCUMENT} non-overlapping source lines"
    )


def _choose_target(candidate: dict[str, Any], gutenberg_id: int, ordinal: int) -> str:
    words = candidate["lower_words"]
    eligible = sorted(
        {
            word
            for word in words
            if word not in STOPWORDS
            and 5 <= len(word) <= 12
            and word.isalpha()
            and words.count(word) == 1
        },
        key=lambda word: sha256_bytes(
            f"{PANEL_ID}:target:{gutenberg_id}:{ordinal}:{word}".encode()
        ),
    )
    if not eligible:
        eligible = sorted(
            {word for word in words if word not in STOPWORDS and word.isalpha()},
            key=lambda word: sha256_bytes(
                f"{PANEL_ID}:fallback-target:{gutenberg_id}:{ordinal}:{word}".encode()
            ),
        )
    if not eligible:
        raise corpus.CorpusError(f"document {gutenberg_id} has no eligible target word")
    return eligible[0]


def _choose_distractor(
    target: str,
    source_words: set[str],
    other_document_words: list[tuple[int, set[str]]],
    gutenberg_id: int,
    ordinal: int,
) -> str:
    same_length: list[tuple[int, str]] = []
    near_length: list[tuple[int, str]] = []
    for other_id, words in other_document_words:
        if other_id == gutenberg_id:
            continue
        for word in words:
            if word == target or word in source_words or word in STOPWORDS or not word.isalpha():
                continue
            distance = abs(len(word) - len(target))
            if distance == 0:
                same_length.append((other_id, word))
            elif distance <= 1:
                near_length.append((other_id, word))
    options = same_length or near_length
    if not options:
        raise corpus.CorpusError(f"no distractor available for document {gutenberg_id}")
    options = sorted(
        set(options),
        key=lambda item: sha256_bytes(
            f"{PANEL_ID}:distractor:{gutenberg_id}:{ordinal}:{item[0]}:{item[1]}".encode()
        ),
    )
    return options[0][1]


def _replace_once(excerpt: str, target: str, distractor: str) -> str:
    replaced, count = re.subn(
        rf"\b{re.escape(target)}\b",
        distractor,
        excerpt,
        count=1,
        flags=re.IGNORECASE,
    )
    if count != 1:
        raise corpus.CorpusError(f"target word replacement count was {count}")
    return replaced


def _prompt(excerpt: str, target: str, distractor: str) -> str:
    return (
        "Read the passage and choose the option that appears in it.\n"
        f"Passage:\n{excerpt}\n"
        f"A) {target}\n"
        f"B) {distractor}\n"
        "Answer with A or B.\n"
        "Answer:"
    )


def build_registry(corpus_root: Path) -> list[dict[str, Any]]:
    manifest = corpus.read_strict_json(corpus_root / "corpus-manifest.json")
    if not isinstance(manifest, dict):
        raise corpus.CorpusError("corpus manifest is not an object")
    documents = manifest.get("documents")
    if not isinstance(documents, list) or len(documents) != corpus.EXPECTED_DOCUMENT_COUNT:
        raise corpus.CorpusError("corpus manifest has an invalid document list")
    parsed: dict[int, tuple[dict[str, Any], str, list[dict[str, Any]]]] = {}
    document_words: list[tuple[int, set[str]]] = []
    for document in documents:
        if not isinstance(document, dict):
            raise corpus.CorpusError("corpus document entry is not an object")
        gutenberg_id = document.get("gutenberg_id")
        text_path = corpus_root / str(document.get("text_path"))
        text_bytes = text_path.read_bytes()
        text, candidates = _candidate_lines(text_bytes)
        if sha256_bytes(text_bytes) != document.get("text_sha256"):
            raise corpus.CorpusError(f"source digest changed: {gutenberg_id}")
        body_words = {word.lower() for word in WORD_RE.findall(text)}
        document_words.append((gutenberg_id, body_words))
        parsed[gutenberg_id] = (document, text, candidates)

    used_ngrams: set[tuple[str, ...]] = set()
    registry: list[dict[str, Any]] = []
    for document in documents:
        gutenberg_id = document["gutenberg_id"]
        split = document["split"]
        source_document, _, candidates = parsed[gutenberg_id]
        selected = _choose_candidates(gutenberg_id, candidates, used_ngrams)
        source_words = parsed[gutenberg_id][1]
        for ordinal, candidate in enumerate(selected):
            target = _choose_target(candidate, gutenberg_id, ordinal)
            distractor = _choose_distractor(
                target,
                {word.lower() for word in candidate["words"]},
                document_words,
                gutenberg_id,
                ordinal,
            )
            excerpt = candidate["normalized"]
            counterfactual_excerpt = _replace_once(excerpt, target, distractor)
            ordinary_prompt = _prompt(excerpt, target, distractor)
            counterfactual_prompt = _prompt(counterfactual_excerpt, target, distractor)
            registry.append(
                {
                    "family_id": f"v39-{split}-doc{gutenberg_id}-{ordinal:02d}",
                    "split": split,
                    "gutenberg_id": gutenberg_id,
                    "source_path": source_document["text_path"],
                    "source_sha256": source_document["text_sha256"],
                    "source_line_number": candidate["line_number"],
                    "source_byte_start": candidate["byte_start"],
                    "source_byte_end": candidate["byte_end"],
                    "source_excerpt_sha256": sha256_bytes(excerpt.encode("utf-8")),
                    "source_word_count": len(candidate["words"]),
                    "target_word": target,
                    "distractor_word": distractor,
                    "ordinary_prompt": ordinary_prompt,
                    "counterfactual_prompt": counterfactual_prompt,
                    "ordinary_correct_label": "A",
                    "counterfactual_correct_label": "B",
                    "incorrect_label": "B",
                    "response_position_rule": RESPONSE_POSITION_RULE,
                    "response_tokens": RESPONSE_TOKENS,
                    "source_text_sha256": source_document["text_sha256"],
                }
            )
    registry.sort(key=lambda item: item["family_id"])
    if len(registry) != EXPECTED_FAMILY_COUNT:
        raise corpus.CorpusError(f"expected {EXPECTED_FAMILY_COUNT} families, got {len(registry)}")
    return registry


def split_manifest(registry: list[dict[str, Any]], corpus_manifest_sha256: str) -> dict[str, Any]:
    by_split = {split: [] for split in corpus.SPLITS}
    by_document: dict[str, list[str]] = {}
    for family in registry:
        by_split[family["split"]].append(family["family_id"])
        by_document.setdefault(str(family["gutenberg_id"]), []).append(family["family_id"])
    return {
        "panel_id": PANEL_ID,
        "protocol": corpus.protocol.PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "corpus_manifest_sha256": corpus_manifest_sha256,
        "families_per_split": EXPECTED_FAMILIES_PER_SPLIT,
        "families_per_document": EXPECTED_FAMILIES_PER_DOCUMENT,
        "by_split": {key: sorted(value) for key, value in by_split.items()},
        "by_document": {key: sorted(value) for key, value in sorted(by_document.items())},
    }


def registry_errors(registry: object, split: object, corpus_manifest_sha256: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(registry, list) or len(registry) != EXPECTED_FAMILY_COUNT:
        return ["family_count_invalid"]
    if not isinstance(split, dict):
        return ["split_manifest_invalid"]
    ids: set[str] = set()
    split_counts = {key: 0 for key in corpus.SPLITS}
    doc_counts: dict[int, int] = {}
    ngrams: set[tuple[str, ...]] = set()
    for family in registry:
        if not isinstance(family, dict):
            errors.append("family_not_object")
            continue
        required = {
            "family_id", "split", "gutenberg_id", "source_path", "source_sha256",
            "source_line_number", "source_byte_start", "source_byte_end",
            "source_excerpt_sha256", "source_word_count", "target_word", "distractor_word",
            "ordinary_prompt", "counterfactual_prompt", "ordinary_correct_label",
            "counterfactual_correct_label", "incorrect_label", "response_position_rule",
            "response_tokens", "source_text_sha256",
        }
        if set(family) != required:
            errors.append(f"family_fields_invalid:{family.get('family_id')}")
            continue
        family_id = family["family_id"]
        if not isinstance(family_id, str) or family_id in ids:
            errors.append("family_id_invalid_or_duplicate")
        ids.add(family_id)
        split_name = family["split"]
        if split_name not in corpus.SPLITS:
            errors.append(f"family_split_invalid:{family_id}")
        else:
            split_counts[split_name] += 1
        gutenberg_id = family["gutenberg_id"]
        if not isinstance(gutenberg_id, int) or isinstance(gutenberg_id, bool):
            errors.append(f"family_document_invalid:{family_id}")
        else:
            doc_counts[gutenberg_id] = doc_counts.get(gutenberg_id, 0) + 1
        if family["ordinary_correct_label"] != "A" or family["counterfactual_correct_label"] != "B":
            errors.append(f"family_label_order_invalid:{family_id}")
        if family["incorrect_label"] != "B":
            errors.append(f"family_incorrect_label_invalid:{family_id}")
        if family["response_position_rule"] != RESPONSE_POSITION_RULE:
            errors.append(f"family_response_position_invalid:{family_id}")
        if family["response_tokens"] != RESPONSE_TOKENS:
            errors.append(f"family_response_tokens_invalid:{family_id}")
        if not isinstance(family["ordinary_prompt"], str) or not isinstance(family["counterfactual_prompt"], str):
            errors.append(f"family_prompt_invalid:{family_id}")
        if family["target_word"] == family["distractor_word"]:
            errors.append(f"family_option_collision:{family_id}")
        if family["target_word"] not in family["ordinary_prompt"]:
            errors.append(f"family_target_absent_ordinary:{family_id}")
        if family["distractor_word"] not in family["counterfactual_prompt"]:
            errors.append(f"family_distractor_absent_counterfactual:{family_id}")
        if not all(isinstance(family[key], int) and not isinstance(family[key], bool) for key in (
            "source_line_number", "source_byte_start", "source_byte_end", "source_word_count"
        )):
            errors.append(f"family_source_coordinates_invalid:{family_id}")
        if not all(
            isinstance(family[key], str)
            and len(family[key]) == 64
            and all(char in "0123456789abcdef" for char in family[key])
            for key in ("source_sha256", "source_excerpt_sha256", "source_text_sha256")
        ):
            errors.append(f"family_digest_invalid:{family_id}")
        prompt_words = len(WORD_RE.findall(family["ordinary_prompt"]))
        if prompt_words < 15:
            errors.append(f"family_prompt_too_short:{family_id}")
        passage = family["ordinary_prompt"].split("Passage:\n", 1)[-1].split("\nA) ", 1)[0]
        family_ngrams = _ngrams([word.lower() for word in WORD_RE.findall(passage)])
        if family_ngrams & ngrams:
            errors.append(f"family_source_overlap:{family_id}")
        ngrams.update(family_ngrams)
    if split_counts != {key: EXPECTED_FAMILIES_PER_SPLIT for key in corpus.SPLITS}:
        errors.append("split_family_counts_invalid")
    if any(count != EXPECTED_FAMILIES_PER_DOCUMENT for count in doc_counts.values()) or len(doc_counts) != corpus.EXPECTED_DOCUMENT_COUNT:
        errors.append("document_family_counts_invalid")
    if split.get("corpus_manifest_sha256") != corpus_manifest_sha256:
        errors.append("split_corpus_digest_mismatch")
    expected_by_split = {
        key: sorted(family["family_id"] for family in registry if family.get("split") == key)
        for key in corpus.SPLITS
    }
    if split.get("by_split") != expected_by_split:
        errors.append("split_manifest_membership_invalid")
    return errors
