#!/usr/bin/env python3
"""Authorization gate for the V2 external acquisition lane.

State slice: gemma3-paper-recirculation-schema-resolution-v2.

This entrypoint is intentionally fail-closed. It verifies a packet-bound
Ed25519 authorization and exact external roots before materializing an atomic
corpus from operator-supplied normalized source records. It never downloads
raw data; source acquisition remains a separately authorized input step.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

from verify_gemma3_paper_recirculation_schema_v2 import validate_corpus_root, validate_packet


AUTH_SCHEMA = "gemma3-paper-recirculation-acquisition-authorization-v2"
REQUIRED_EXCLUSIONS = {
    "no_model_execution",
    "no_weco_execution",
    "no_spending",
    "no_assessment",
    "no_evidence_ledger_mutation",
    "no_publication",
}
MODEL_PATH = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
SOURCE_FILES = {
    ("fit", "arxiv"): Path("fit/arxiv.jsonl"),
    ("fit", "c4"): Path("fit/c4.jsonl"),
    ("fit", "pg19"): Path("fit/pg19.jsonl"),
    ("assessment", "arxiv"): Path("assessment/arxiv.jsonl"),
    ("assessment", "big_patent"): Path("assessment/big_patent.jsonl"),
    ("assessment", "billsum"): Path("assessment/billsum.jsonl"),
    ("assessment", "booksum/book"): Path("assessment/booksum-book.jsonl"),
    ("assessment", "c4/webtextlike"): Path("assessment/c4-webtextlike.jsonl"),
    ("assessment", "gov_report"): Path("assessment/gov_report.jsonl"),
    ("assessment", "lambada"): Path("assessment/lambada.jsonl"),
    ("assessment", "newsroom"): Path("assessment/newsroom.jsonl"),
    ("assessment", "pg19"): Path("assessment/pg19.jsonl"),
    ("assessment", "pubmed"): Path("assessment/pubmed.jsonl"),
}
FIT_QUOTAS = {"arxiv": 6, "c4": 5, "pg19": 5}
ASSESSMENT_QUOTAS = {
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


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


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


def _verify_signature(packet: dict[str, Any]) -> None:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise ValueError("cryptography is required to verify acquisition authorization") from exc
    try:
        public_key = base64.b64decode(packet["reviewer_public_key_b64"], validate=True)
        signature = base64.b64decode(packet["signature_b64"], validate=True)
        expected_fingerprint = packet["reviewer_key_fingerprint_sha256"]
        import hashlib

        if hashlib.sha256(public_key).hexdigest() != expected_fingerprint:
            raise ValueError("reviewer key fingerprint mismatch")
        signed = {key: value for key, value in packet.items() if key != "signature_b64"}
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, _canonical(signed))
    except (KeyError, ValueError) as exc:
        raise ValueError("invalid packet-bound Ed25519 authorization") from exc


def verify_authorization(
    packet_path: Path,
    manifest_path: Path,
    protocol_path: Path,
    operator_id: str,
) -> dict[str, Any]:
    packet = _load(packet_path)
    local = validate_packet(manifest_path, protocol_path)
    manifest = _load(manifest_path)
    if packet.get("schema") != AUTH_SCHEMA:
        raise ValueError("authorization schema mismatch")
    if packet.get("status") != "ACCEPT":
        raise ValueError("authorization status is not ACCEPT")
    if packet.get("packet_digest") != local["packet_digest"]:
        raise ValueError("authorization is bound to different packet bytes")
    if packet.get("operator_id") != operator_id:
        raise ValueError("operator identity mismatch")
    if packet.get("reviewer_id") == operator_id:
        raise ValueError("reviewer and operator must be distinct")
    if not isinstance(packet.get("reviewer_registry_ref"), str) or not packet["reviewer_registry_ref"]:
        raise ValueError("reviewer registry reference missing")
    if not isinstance(packet.get("independence_attestation_sha256"), str) or len(packet["independence_attestation_sha256"]) != 64:
        raise ValueError("independence attestation digest missing")
    if packet.get("conflict_of_interest") is not False:
        raise ValueError("reviewer conflict-of-interest attestation failed")
    if packet.get("acquisition_command") != manifest["acquisition_command"]:
        raise ValueError("authorized command is not the frozen command")
    custody = manifest["external_custody"]
    if packet.get("external_custody") != custody:
        raise ValueError("authorized custody roots do not match the frozen roots")
    if set(packet.get("exclusions", [])) != REQUIRED_EXCLUSIONS:
        raise ValueError("authorization exclusions are incomplete or broadened")
    _verify_signature(packet)
    return {
        "status": "authorization_verified_acquisition_not_started",
        "packet_digest": local["packet_digest"],
        "reviewer_id": packet["reviewer_id"],
        "operator_id": operator_id,
        "external_custody": custody,
    }


def _validate_custody_paths(paths: dict[str, Path], repo_root: Path) -> None:
    resolved: dict[str, Path] = {}
    for name, path in paths.items():
        raw_path = path.expanduser()
        current = raw_path
        while current != current.parent:
            if current.is_symlink():
                raise ValueError(f"{name} contains a symlinked path component: {current}")
            current = current.parent
        _resolved = raw_path.resolve()
        if not _resolved.is_absolute() or not str(_resolved).startswith("/Volumes/PrimaryED/"):
            raise ValueError(f"{name} must be an absolute Primary ED path")
        if _resolved == repo_root or repo_root in _resolved.parents:
            raise ValueError(f"{name} cannot be inside the repository")
        if name == "corpus_root":
            if _resolved.exists() or _resolved.is_symlink():
                raise ValueError(f"corpus_root must not already exist: {_resolved}")
            if not _resolved.parent.is_dir():
                raise ValueError(f"corpus_root parent directory is missing: {_resolved.parent}")
        else:
            if not _resolved.is_dir() or _resolved.is_symlink():
                raise ValueError(f"{name} must be an existing regular directory: {_resolved}")
            import stat

            if stat.S_IMODE(_resolved.stat().st_mode) != 0o700:
                raise ValueError(f"{name} must be owner-only 0700: {_resolved}")
        resolved[name] = _resolved
    if len(set(resolved.values())) != len(resolved):
        raise ValueError("custody roots must be distinct")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _model_manifest_digest(model_path: Path) -> str:
    files = []
    for path in sorted(
        candidate
        for candidate in model_path.rglob("*")
        if candidate.is_file()
        and not candidate.is_symlink()
        and ".cache" not in candidate.relative_to(model_path).parts
    ):
        files.append({
            "path": path.relative_to(model_path).as_posix(),
            "byte_len": path.stat().st_size,
            "sha256": _sha256_bytes(path.read_bytes()),
        })
    if not files:
        raise ValueError(f"frozen model directory has no stable files: {model_path}")
    body = {"model_name": model_path.name, "files": files}
    return _sha256_bytes(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _source_records(path: Path) -> Iterable[tuple[str, str]]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"source record file is missing or symlinked: {path}")
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"blank source record at {path}:{line_number}")
            try:
                def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
                    result: dict[str, Any] = {}
                    for key, item in pairs:
                        if key in result:
                            raise ValueError(f"duplicate JSON key in {path}:{line_number}: {key}")
                        result[key] = item
                    return result

                value = json.loads(line, object_pairs_hook=reject_duplicates)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid source record at {path}:{line_number}") from exc
            if not isinstance(value, dict) or not isinstance(value.get("document_id"), str) or not value["document_id"]:
                raise ValueError(f"source record identity invalid at {path}:{line_number}")
            if not isinstance(value.get("text"), str) or not value["text"]:
                raise ValueError(f"source record text invalid at {path}:{line_number}")
            yield value["document_id"], value["text"]


def _load_tokenizer(model_path: Path, expected_manifest_sha256: str) -> Any:
    if not model_path.is_dir() or model_path.is_symlink():
        raise ValueError(f"frozen tokenizer/model directory is missing: {model_path}")
    if _model_manifest_digest(model_path) != expected_manifest_sha256:
        raise ValueError("frozen model manifest digest mismatch")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from mlx_lm.utils import load_tokenizer

    return load_tokenizer(model_path)


def _materialize(
    source_root: Path,
    corpus_root: Path,
    model_path: Path,
    expected_model_manifest_sha256: str,
) -> dict[str, Any]:
    source_manifest = source_root / "acquisition-manifest.json"
    if not source_manifest.is_file() or source_manifest.is_symlink():
        raise ValueError("source root must contain a regular acquisition-manifest.json")
    source_value = _load(source_manifest)
    if source_value.get("schema") != "gemma3-paper-recirculation-source-record-v2":
        raise ValueError("source root schema is not the frozen V2 source schema")
    if source_value.get("state_slice") != "gemma3-paper-recirculation-schema-resolution-v2":
        raise ValueError("source root state slice mismatch")
    if source_value.get("protocol_id") != "gemma3-paper-recirculation-schema-resolution-v2":
        raise ValueError("source root protocol mismatch")
    expected_file_map = {key: value.as_posix() for (split, key), value in SOURCE_FILES.items()}
    if source_value.get("file_map") != expected_file_map:
        raise ValueError("source root file map mismatch")
    expected_files = sorted({"acquisition-manifest.json", *expected_file_map.values()})
    if source_value.get("file_census") != expected_files:
        raise ValueError("source root file census mismatch")
    if any(path.is_symlink() for path in source_root.rglob("*")):
        raise ValueError("source root contains a symlink")
    actual_files = sorted(
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*")
        if path.is_file()
    )
    if actual_files != expected_files:
        raise ValueError("source root contains undeclared files")
    file_digests = source_value.get("file_digests")
    if not isinstance(file_digests, dict) or set(file_digests) != set(expected_file_map.values()):
        raise ValueError("source root file digests are incomplete")
    for relative in expected_file_map.values():
        path = source_root / relative
        if not path.is_file() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) & 0o077 or _sha256_bytes(path.read_bytes()) != file_digests[relative]:
            raise ValueError(f"source root file digest mismatch: {relative}")
    source_body = {key: value for key, value in source_value.items() if key != "manifest_sha256"}
    if source_value.get("manifest_sha256") != _sha256_bytes(json.dumps(source_body, sort_keys=True, separators=(",", ":")).encode("utf-8")):
        raise ValueError("source root manifest digest mismatch")
    tokenizer = _load_tokenizer(model_path, expected_model_manifest_sha256)
    fit_entries: list[dict[str, Any]] = []
    assessment_entries: list[dict[str, Any]] = []
    used_rows: set[str] = set()
    used_source_digests: set[str] = set()
    with tempfile.TemporaryDirectory(dir=corpus_root.parent, prefix=f".{corpus_root.name}.staging-") as staging_name:
        staging = Path(staging_name)
        staging.chmod(0o700)

        def pack(split: str, dataset: str, quota: int) -> list[dict[str, Any]]:
            source_path = source_root / SOURCE_FILES[(split, dataset)]
            entries: list[dict[str, Any]] = []
            for document_id, text in _source_records(source_path):
                if document_id in used_rows:
                    raise ValueError(f"source row reused across panels: {document_id}")
                source_digest = _sha256_bytes(text.encode("utf-8"))
                if source_digest in used_source_digests:
                    raise ValueError(f"source digest reused across panels: {document_id}")
                used_rows.add(document_id)
                used_source_digests.add(source_digest)
                token_ids = list(tokenizer.encode(text, add_special_tokens=False))
                if len(token_ids) < 1024:
                    continue
                chunk = token_ids[:1024]
                window_text = tokenizer.decode(chunk)
                if list(tokenizer.encode(window_text, add_special_tokens=False)) != chunk:
                    raise ValueError(f"tokenizer round-trip changed {split}/{dataset}/{document_id}")
                output_dataset = dataset
                relative = Path(split) / dataset.replace("/", "-") / f"window-{len(entries):06d}.txt"
                destination = staging / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                encoded = window_text.encode("utf-8")
                destination.write_bytes(encoded)
                destination.chmod(0o600)
                entries.append({
                    "dataset": output_dataset,
                    "source_row_id": document_id,
                    "document_id": document_id,
                    "path": relative.as_posix(),
                    "window_ordinal": 0,
                    "byte_len": len(encoded),
                    "source_sha256": source_digest,
                    "text_sha256": _sha256_bytes(encoded),
                    "token_count": 1024,
                })
                if len(entries) == quota:
                    return entries
            raise ValueError(f"{split}/{dataset} ended before its exact quota {quota}")

        for dataset, quota in FIT_QUOTAS.items():
            fit_entries.extend(pack("fit", dataset, quota))
        for dataset, quota in ASSESSMENT_QUOTAS.items():
            assessment_entries.extend(pack("assessment", dataset, quota))

        declared_paths = sorted({entry["path"] for entry in fit_entries + assessment_entries})
        body = {
            "schema": "gemma3-paper-recirculation-corpus-v2",
            "state_slice": "gemma3-paper-recirculation-schema-resolution-v2",
            "window_token_count": 1024,
            "fit": fit_entries,
            "assessment": assessment_entries,
            "fit_window_count": len(fit_entries),
            "assessment_window_count": len(assessment_entries),
            "file_census": sorted({"manifest.json", *declared_paths}),
        }
        manifest = {
            **body,
            "manifest_sha256": _sha256_bytes(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        }
        manifest_path = staging / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest_path.chmod(0o600)
        os.replace(staging, corpus_root)
    validate_corpus_root(corpus_root)
    return {
        "status": "corpus_materialized",
        "corpus_root": str(corpus_root),
        "fit_window_count": len(fit_entries),
        "assessment_window_count": len(assessment_entries),
        "manifest_sha256": manifest["manifest_sha256"],
    }


def main() -> int:
    repo_root = Path(__file__).parents[2]
    default_manifest = repo_root / "docs/research/continual-learning/304-gemma3-paper-recirculation-schema-resolution-v2-manifest.json"
    default_protocol = repo_root / "docs/research/continual-learning/303-gemma3-paper-recirculation-schema-resolution-v2-protocol.md"
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-packet", type=Path, required=True)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_PATH)
    parser.add_argument("--manifest", type=Path, default=default_manifest)
    parser.add_argument("--protocol", type=Path, default=default_protocol)
    args = parser.parse_args()
    try:
        result = verify_authorization(args.authorization_packet, args.manifest, args.protocol, args.operator_id)
        manifest = _load(args.manifest)
        expected = manifest["external_custody"]
        raw_supplied = {
            "raw_root": args.raw_root.expanduser(),
            "source_root": args.source_root.expanduser(),
            "corpus_root": args.corpus_root.expanduser(),
        }
        _validate_custody_paths(raw_supplied, repo_root.resolve())
        supplied = {key: str(path.resolve()) for key, path in raw_supplied.items()}
        if any(supplied[key] != expected[key] for key in supplied):
            raise ValueError("CLI custody roots do not match the frozen packet")
        materialized = _materialize(
            args.source_root.resolve(),
            args.corpus_root.resolve(),
            args.model.expanduser().resolve(),
            manifest["tokenizer_contract"]["model_manifest_sha256"],
        )
        result["materialization"] = materialized
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
