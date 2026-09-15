#!/usr/bin/env python3
"""Fail-closed validator for the paper-recirculation V2 pre-acquisition packet.

State slice: gemma3-paper-recirculation-schema-resolution-v2.
This validator is read-only. It never downloads, materializes, changes custody,
loads model weights, or authorizes execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from pathlib import Path
from typing import Any


STATE_SLICE = "gemma3-paper-recirculation-schema-resolution-v2"
PROTOCOL_ID = "gemma3-paper-recirculation-schema-resolution-v2"
CORPUS_SCHEMA = "gemma3-paper-recirculation-corpus-v2"
MANIFEST_SCHEMA = "gemma3-paper-recirculation-acquisition-manifest-v2"
EXPECTED_FIT = {"arxiv", "c4", "pg19"}
EXPECTED_SOURCE_KEYS = {
    "arxiv",
    "c4",
    "pg19",
    "big_patent",
    "billsum",
    "booksum/book",
    "gov_report",
    "lambada",
    "newsroom",
    "pubmed",
}
EXPECTED_ASSESSMENT = {
    "arxiv",
    "big_patent",
    "billsum",
    "booksum/book",
    "c4/webtextlike",
    "gov_report",
    "lambada",
    "newsroom",
    "pg19",
    "pubmed",
}
EXPECTED_FIT_QUOTAS = {"arxiv": 6, "c4": 5, "pg19": 5}
EXPECTED_ASSESSMENT_QUOTAS = {
    "arxiv": 2,
    "big_patent": 2,
    "billsum": 2,
    "booksum/book": 2,
    "c4/webtextlike": 2,
    "gov_report": 2,
    "lambada": 1,
    "newsroom": 1,
    "pg19": 1,
    "pubmed": 1,
}
NEWSROOM_ACCEPTANCE_SHA256 = (
    "d415a6659ee0395ac3848041d52fda8875da817dbf4c17b6db03af6c94ca3bf0"
)
EXPECTED_SOURCE_FIELDS = {
    "arxiv": "article_text[] joined with LF",
    "c4": "text",
    "pg19": "text file contents",
    "big_patent": "description",
    "billsum": "text",
    "booksum/book": "text",
    "gov_report": "document",
    "lambada": "text",
    "newsroom": "text",
    "pubmed": "article_text[] joined with LF",
}
EXPECTED_SELECTION_KEYS = {
    "algorithm_id",
    "loader_versions",
    "row_enumeration",
    "malformed_row",
    "duplicate_row_id",
    "duplicate_source_digest",
    "eligibility",
    "window_rule",
    "quota_rule",
    "assessment_adaptation",
    "row_id_finalization",
}
EXPECTED_WINDOW_FIELDS = {
    "dataset",
    "source_row_id",
    "document_id",
    "path",
    "window_ordinal",
    "byte_len",
    "source_sha256",
    "text_sha256",
    "token_count",
}
EXPECTED_SOURCE_FILES = {
    "fit/arxiv": "fit/arxiv.jsonl",
    "fit/c4": "fit/c4.jsonl",
    "fit/pg19": "fit/pg19.jsonl",
    "assessment/arxiv": "assessment/arxiv.jsonl",
    "assessment/big_patent": "assessment/big_patent.jsonl",
    "assessment/billsum": "assessment/billsum.jsonl",
    "assessment/booksum/book": "assessment/booksum-book.jsonl",
    "assessment/c4/webtextlike": "assessment/c4-webtextlike.jsonl",
    "assessment/gov_report": "assessment/gov_report.jsonl",
    "assessment/lambada": "assessment/lambada.jsonl",
    "assessment/newsroom": "assessment/newsroom.jsonl",
    "assessment/pg19": "assessment/pg19.jsonl",
    "assessment/pubmed": "assessment/pubmed.jsonl",
}


def _load(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _packet_files(protocol_path: Path, manifest_path: Path) -> list[Path]:
    repo_root = Path(__file__).resolve().parents[2]
    return [
        protocol_path,
        manifest_path,
        Path(__file__).resolve(),
        repo_root / "experiments/continual_learning/acquire_gemma3_paper_recirculation_schema_v2.py",
        repo_root / "experiments/continual_learning/tests/test_verify_gemma3_paper_recirculation_schema_v2.py",
    ]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_packet(manifest_path: Path, protocol_path: Path) -> dict[str, Any]:
    manifest = _load(manifest_path)
    protocol = protocol_path.read_text(encoding="utf-8")

    _require(f"State slice: `{STATE_SLICE}`" in protocol, "protocol state slice mismatch")
    _require(f"Protocol: `{PROTOCOL_ID}`" in protocol, "protocol identity missing")
    _require(f"Corpus schema: `{CORPUS_SCHEMA}`" in protocol, "corpus schema missing")
    _require(manifest["schema"] == MANIFEST_SCHEMA, "manifest schema mismatch")
    _require(manifest["state_slice"] == STATE_SLICE, "manifest state slice mismatch")
    _require(manifest["protocol_id"] == PROTOCOL_ID, "manifest protocol mismatch")
    _require(manifest["corpus_schema"] == CORPUS_SCHEMA, "manifest corpus schema mismatch")
    _require(manifest["acquisition_authorized"] is False, "pre-acquisition packet cannot authorize acquisition")
    tokenizer_contract = manifest.get("tokenizer_contract")
    _require(isinstance(tokenizer_contract, dict), "tokenizer contract missing")
    _require(tokenizer_contract.get("model_path") == "/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16", "tokenizer model path mismatch")
    _require(isinstance(tokenizer_contract.get("model_manifest_sha256"), str) and len(tokenizer_contract["model_manifest_sha256"]) == 64, "tokenizer model digest missing")
    _require(tokenizer_contract.get("policy") == "cached Gemma 3 1B BF16 tokenizer; no special tokens; offline only", "tokenizer policy mismatch")

    contract = manifest["corpus_contract"]
    _require(contract["fit_window_count"] == 16, "fit count mismatch")
    _require(contract["assessment_window_count"] == 16, "assessment count mismatch")
    _require(contract["window_token_count"] == 1024, "token count mismatch")
    _require(contract["custody_mode"] == "0700", "custody mode mismatch")
    _require(contract["fit_window_quotas"] == EXPECTED_FIT_QUOTAS, "fit quotas mismatch")
    _require(
        contract["assessment_window_quotas"] == EXPECTED_ASSESSMENT_QUOTAS,
        "assessment quotas mismatch",
    )
    _require(contract["selected_row_ids"] == [], "row IDs must remain deferred")
    _require(contract["selected_window_digests"] == [], "window digests must remain deferred")

    custody = manifest.get("external_custody")
    _require(isinstance(custody, dict), "external custody contract missing")
    for key in ("raw_root", "source_root", "corpus_root"):
        _require(isinstance(custody.get(key), str) and custody[key].startswith("/Volumes/PrimaryED/"), f"{key} must be an external Primary ED root")
    _require(custody.get("mode") == "0700", "external custody mode mismatch")
    _require(custody.get("input_roots_must_exist") is True, "input-root custody policy missing")
    _require(custody.get("refuse_existing_output_root") is True, "output-root refusal missing")
    _require(custody.get("raw_retention_hours_after_validation") == 72, "raw retention policy mismatch")
    _require(isinstance(manifest.get("acquisition_command"), str), "acquisition command missing")
    _require("acquire_gemma3_paper_recirculation_schema_v2.py" in manifest["acquisition_command"], "acquisition command identity mismatch")
    _require(
        (Path(__file__).with_name("acquire_gemma3_paper_recirculation_schema_v2.py")).is_file(),
        "acquisition entrypoint missing",
    )

    selection = manifest.get("selection_policy")
    _require(isinstance(selection, dict), "selection policy missing")
    _require(set(selection) == EXPECTED_SELECTION_KEYS, "selection policy fields are not exact")
    _require(selection["algorithm_id"] == "ordered-first-eligible-exact-window-v2", "selection algorithm mismatch")
    _require(selection["malformed_row"] == "fail_closed", "malformed-row policy weakened")
    _require(selection["duplicate_row_id"] == "fail_closed", "duplicate-row policy weakened")
    _require(selection["duplicate_source_digest"] == "fail_closed within and across panels", "duplicate-digest policy weakened")
    _require(selection["assessment_adaptation"] == "forbidden", "assessment adaptation policy weakened")
    _require(isinstance(selection["loader_versions"], dict) and len(selection["loader_versions"]) == 5, "loader versions incomplete")
    source_root_contract = manifest.get("source_root_contract")
    _require(isinstance(source_root_contract, dict), "source-root contract missing")
    _require(source_root_contract.get("manifest_file") == "acquisition-manifest.json", "source manifest filename mismatch")
    _require(source_root_contract.get("record_schema") == "{document_id:string,text:string}", "source record schema mismatch")
    _require(source_root_contract.get("required_manifest_fields") == ["schema", "state_slice", "protocol_id", "file_map", "file_census", "file_digests", "manifest_sha256"], "source manifest field contract mismatch")
    _require(source_root_contract.get("file_map") == EXPECTED_SOURCE_FILES, "source file map mismatch")
    _require(source_root_contract.get("blank_or_malformed_record") == "fail_closed", "source malformed-record policy weakened")
    _require(source_root_contract.get("source_root_mode") == "0700", "source root mode mismatch")

    sources = manifest.get("sources")
    _require(isinstance(sources, list) and len(sources) == 10, "source count mismatch")
    keys = [item.get("dataset_key") for item in sources]
    _require(len(set(keys)) == 10, "source keys must be unique")
    _require(set(keys) == EXPECTED_SOURCE_KEYS, "source roster mismatch")
    source_by_key = {item["dataset_key"]: item for item in sources}

    for key, source_field in EXPECTED_SOURCE_FIELDS.items():
        _require(source_by_key[key].get("source_field") == source_field, f"{key} source field mismatch")

    for key in EXPECTED_FIT:
        _require(source_by_key[key]["fit_split"] == "train", f"{key} fit split mismatch")
    assessment_source_key = {"c4/webtextlike": "c4"}
    for panel_key in EXPECTED_ASSESSMENT:
        source_key = assessment_source_key.get(panel_key, panel_key)
        _require(
            source_by_key[source_key]["assessment_split"] in {"test", "validation"},
            f"{panel_key} assessment split invalid",
        )
    _require(source_by_key["c4"]["assessment_split"] == "validation", "C4 assessment must use validation")
    _require(source_by_key["newsroom"]["rights_status"] == "accepted-restricted-terms", "Newsroom acceptance scope mismatch")
    _require(source_by_key["newsroom"]["acceptance_evidence_sha256"] == NEWSROOM_ACCEPTANCE_SHA256, "Newsroom evidence digest mismatch")
    _require(source_by_key["arxiv"]["rights_status"] == "rights-review-required", "arXiv rights gate weakened")
    _require(source_by_key["pubmed"]["rights_status"] == "rights-review-required", "PubMed rights gate weakened")
    _require(source_by_key["booksum/book"]["rights_status"] == "rights-review-required-and-derived-source", "BookSum rights gate weakened")
    _require(source_by_key["booksum/book"]["config"] == "books", "BookSum must use the books config")
    _require(source_by_key["gov_report"]["config"] == "plain_text", "GovReport config mismatch")
    _require(source_by_key["gov_report"]["source_field"] == "document", "GovReport must use plain-text document field")
    _require(source_by_key["lambada"]["license_record"] == "Modified MIT as recorded by the pinned source", "LAMBADA license record mismatch")
    c4_inputs = source_by_key["c4"].get("input_artifacts")
    _require(isinstance(c4_inputs, list) and {item.get("role") for item in c4_inputs} == {"openwebtext_manual_archive", "commoncrawl_wet_path_manifests"}, "C4 input identity is incomplete")
    for item in sources:
        for field in ("source", "revision", "config", "source_field", "enumeration", "normalization", "rights_status", "license_record", "selected_row_ids"):
            _require(field in item, f"{item.get('dataset_key')} missing source contract field {field}")
        _require(item["selected_row_ids"] == [], f"{item['dataset_key']} row IDs must remain deferred")

    packet_files = _packet_files(protocol_path, manifest_path)
    _require(all(path.is_file() and not path.is_symlink() for path in packet_files), "packet file set is incomplete")
    packet_digest = hashlib.sha256(
        b"".join(path.read_bytes() for path in packet_files)
    ).hexdigest()
    return {
        "status": "valid_preacquisition_packet",
        "state_slice": STATE_SLICE,
        "protocol_id": PROTOCOL_ID,
        "corpus_schema": CORPUS_SCHEMA,
        "acquisition_authorized": False,
        "source_count": len(sources),
        "packet_digest": packet_digest,
        "packet_files": [str(path) for path in packet_files],
        "manifest_sha256": _sha256(manifest_path),
        "protocol_sha256": _sha256(protocol_path),
    }


def validate_corpus_root(root: Path) -> dict[str, Any]:
    """Validate the complete safe structure of an already materialized root."""

    _require(root.is_dir() and not root.is_symlink(), "corpus root must be a real directory")
    _require(stat.S_IMODE(root.stat().st_mode) == 0o700, "corpus root must be owner-only 0700")
    manifest_path = root / "manifest.json"
    _require(manifest_path.is_file() and not manifest_path.is_symlink(), "corpus manifest missing or symlinked")
    corpus_manifest = _load(manifest_path)
    _require(corpus_manifest.get("schema") == CORPUS_SCHEMA, "materialized corpus schema mismatch")
    _require(corpus_manifest.get("state_slice") == STATE_SLICE, "materialized corpus state slice mismatch")
    _require(corpus_manifest.get("window_token_count") == 1024, "materialized token count mismatch")
    _require(corpus_manifest.get("fit_window_count") == 16, "materialized fit count mismatch")
    _require(corpus_manifest.get("assessment_window_count") == 16, "materialized assessment count mismatch")
    body = {key: value for key, value in corpus_manifest.items() if key != "manifest_sha256"}
    expected_manifest_digest = hashlib.sha256(_canonical_json(body)).hexdigest()
    _require(corpus_manifest.get("manifest_sha256") == expected_manifest_digest, "materialized manifest digest mismatch")

    fit = corpus_manifest.get("fit")
    assessment = corpus_manifest.get("assessment")
    _require(isinstance(fit, list) and isinstance(assessment, list), "materialized windows must be arrays")
    _require(len(fit) == 16 and len(assessment) == 16, "materialized window count mismatch")
    declared_paths: list[str] = []
    seen_source_rows: set[str] = set()
    seen_documents: set[tuple[str, str]] = set()
    split_counts: dict[str, dict[str, int]] = {"fit": {}, "assessment": {}}
    for split, windows in (("fit", fit), ("assessment", assessment)):
        for item in windows:
            _require(isinstance(item, dict) and set(item) == EXPECTED_WINDOW_FIELDS, f"{split} window fields are not exact")
            dataset = item["dataset"]
            panel = "c4/webtextlike" if dataset == "c4" and split == "assessment" else dataset
            allowed = EXPECTED_FIT if split == "fit" else EXPECTED_ASSESSMENT
            _require(panel in allowed, f"{split} dataset is outside the frozen panel: {dataset}")
            _require(isinstance(item["path"], str) and item["path"] == Path(item["path"]).as_posix(), f"{split} path is not canonical")
            relative = Path(item["path"])
            _require(not relative.is_absolute() and ".." not in relative.parts, f"{split} path escapes root")
            file_path = root / relative
            _require(file_path.is_file() and not file_path.is_symlink(), f"{split} window file missing or symlinked")
            _require(stat.S_IMODE(file_path.stat().st_mode) & 0o077 == 0, f"{split} window file is not owner-only")
            raw = file_path.read_bytes()
            _require(len(raw) == item["byte_len"], f"{split} byte length mismatch")
            _require(hashlib.sha256(raw).hexdigest() == item["text_sha256"], f"{split} text digest mismatch")
            _require(item["token_count"] == 1024, f"{split} token count mismatch")
            _require(isinstance(item["source_sha256"], str) and len(item["source_sha256"]) == 64, f"{split} source digest invalid")
            _require(isinstance(item["source_row_id"], str) and item["source_row_id"], f"{split} source row identity missing")
            _require(item["source_row_id"] not in seen_source_rows, "source row reused across panels")
            seen_source_rows.add(item["source_row_id"])
            document_key = (dataset, item["document_id"])
            _require(document_key not in seen_documents, "document reused across windows")
            seen_documents.add(document_key)
            declared_paths.append(item["path"])
            split_counts[split][panel] = split_counts[split].get(panel, 0) + 1

    _require(split_counts["fit"] == {"arxiv": 6, "c4": 5, "pg19": 5}, "fit quotas mismatch")
    expected_assessment_counts = {
        "arxiv": 2,
        "big_patent": 2,
        "billsum": 2,
        "booksum/book": 2,
        "c4/webtextlike": 2,
        "gov_report": 2,
        "lambada": 1,
        "newsroom": 1,
        "pg19": 1,
        "pubmed": 1,
    }
    _require(split_counts["assessment"] == expected_assessment_counts, "assessment quotas mismatch")
    census = corpus_manifest.get("file_census")
    _require(isinstance(census, list) and all(isinstance(item, str) for item in census), "file census missing")
    expected_census = sorted({"manifest.json", *declared_paths})
    _require(census == expected_census, "file census does not match declared windows")
    actual_files = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )
    _require(not any(path.is_symlink() for path in root.rglob("*")), "corpus contains a symlink")
    _require(len(declared_paths) == len(set(declared_paths)), "duplicate declared window path")
    _require(actual_files == expected_census, "corpus contains undeclared files")
    return {"status": "corpus_root_identity_ok", "root": str(root), "file_count": len(actual_files)}


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path(__file__).parents[2] / "docs/research/continual-learning/304-gemma3-paper-recirculation-schema-resolution-v2-manifest.json")
    parser.add_argument("--protocol", type=Path, default=Path(__file__).parents[2] / "docs/research/continual-learning/303-gemma3-paper-recirculation-schema-resolution-v2-protocol.md")
    parser.add_argument("--corpus-root", type=Path)
    args = parser.parse_args()
    try:
        result = validate_packet(args.manifest, args.protocol)
        if args.corpus_root is not None:
            result["corpus"] = validate_corpus_root(args.corpus_root)
        print(json.dumps(result, sort_keys=True))
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, sort_keys=True))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
