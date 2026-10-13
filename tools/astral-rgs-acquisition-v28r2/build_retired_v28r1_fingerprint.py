from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any


R1_PACKET_SHA256 = (
    "sha256:2fd74b389907d3167518a0d91d9d63f18fda7c1231a51764657e791286ee2ad0"
)
R1_REPORT_SHA256 = (
    "sha256:3e24804dc84744a300bb11bc246fdfd40256459f97a68da0df7993d676b9ea3d"
)
R1_MANIFEST_SHA256 = (
    "sha256:5b01a32e1ba9d7d9ce84c8b301f29e0145962ac8c0eac0ec59b07cd5cfca846e"
)
R1_PACKET_FILE_SHA256 = (
    "sha256:f3b5217e725322d2cf964267b63af4fb956a0232507ac646f07fbaf12a31c121"
)
R1_REPORT_FILE_SHA256 = (
    "sha256:0ec4215734583566f593c6214eec2317523e0bc7471e6d9f837ca3e0337b53e9"
)
R1_MANIFEST_FILE_SHA256 = (
    "sha256:7ca7e09302aff508368d53335aa47c90564fa6393e262ecadc8db51e401ce5f7"
)
REQUIRED_ROOT_PATHS = frozenset(
    {
        "acquisition-packet.json",
        "astral-validation-report.json",
        "artifact-manifest.json",
        "checkpoint-receipt.json",
        "seed-material.json",
        "seed-commitment.json",
        "raw-corpus.json",
        "protocol-corpus.json",
        "future-assessment-commitment.json",
        "configuration-lock.json",
        "one-shot-execution-claim.json",
        "run-summary.json",
    }
)
SET_NAMES = (
    "seed_commitments",
    "campaign_ids",
    "ledger_ids",
    "namespace_ids",
    "family_ids",
    "item_ids",
    "query_ids",
    "concept_schema_ids",
    "anchor_ids",
    "value_ids",
    "alias_ids",
    "wrapper_ids",
    "source_hashes",
    "support_hashes",
    "question_hashes",
    "prompt_hashes",
    "option_hashes",
    "dependency_hashes",
    "mapping_hashes",
    "training_template_ids",
    "evaluation_template_ids",
    "concept_ast_hashes",
    "template_ast_hashes",
    "normalized_skeleton_hashes",
    "normalized_line_hashes",
    "structural_ngram_hashes",
    "future_assessment_family_ids",
    "future_assessment_commitments",
)


class DuplicateKeyError(ValueError):
    pass


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def load_json_strict(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_no_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"nonfinite JSON constant: {value}")
        ),
    )


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    return {
        candidate: child
        for candidate, child in value.items()
        if candidate != key
    }


def fingerprint(set_name: str, canonical_value: str) -> str:
    return sha256_bytes(
        (
            "v28r1-fingerprint-v1\0" + set_name + "\0" + canonical_value
        ).encode("utf-8")
    )


def _add(sets: dict[str, set[str]], name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"invalid {name} value")
    sets[name].add(fingerprint(name, value))


def _verify_self_hash(
    value: dict[str, Any],
    key: str,
    expected: str | None = None,
) -> None:
    observed = value.get(key)
    if observed != canonical_sha256(_without(value, key)):
        raise ValueError(f"invalid self hash: {key}")
    if expected is not None and observed != expected:
        raise ValueError(f"unexpected self hash: {key}")


def _verified_text_payload(value: dict[str, Any]) -> tuple[str, str]:
    text = value["text"]
    digest = sha256_bytes(text.encode("utf-8"))
    if value["sha256"] != digest:
        raise ValueError("text digest mismatch")
    return text, digest


def _verified_source_text_hash(
    value: dict[str, Any],
) -> tuple[str, str]:
    if set(value) != {"license_id", "sha256", "text"}:
        raise ValueError("invalid source text record")
    return _verified_text_payload(value)


def _verified_option_text_hash(
    value: dict[str, Any],
) -> tuple[str, str]:
    if set(value) != {"sha256", "text"}:
        raise ValueError("invalid option text record")
    return _verified_text_payload(value)


def _typed_normalize(
    text: str,
    identifiers: dict[str, set[str]],
) -> str:
    normalized = unicodedata.normalize("NFC", text)
    replacements = [
        (identifier, f"<{kind}>")
        for kind, values in identifiers.items()
        for identifier in values
    ]
    for identifier, placeholder in sorted(
        replacements, key=lambda pair: (-len(pair[0]), pair[0])
    ):
        normalized = re.sub(
            rf"(?<![A-Za-z0-9_-]){re.escape(identifier)}(?![A-Za-z0-9_-])",
            placeholder,
            normalized,
        )
    return re.sub(r"[ \t\r\n\f\v]+", " ", normalized.lower()).strip(
        " \t\r\n\f\v"
    )


def _add_structural_surfaces(
    sets: dict[str, set[str]],
    text: str,
    identifiers: dict[str, set[str]],
) -> None:
    normalized_surface = _typed_normalize(text, identifiers)
    _add(
        sets,
        "normalized_skeleton_hashes",
        sha256_bytes(normalized_surface.encode("utf-8")),
    )
    for line in text.splitlines():
        normalized_line = _typed_normalize(line, identifiers)
        if not normalized_line:
            continue
        line_hash = sha256_bytes(normalized_line.encode("utf-8"))
        _add(sets, "normalized_line_hashes", line_hash)
        tokens = normalized_line.split()
        for index in range(max(0, len(tokens) - 7)):
            ngram = " ".join(tokens[index : index + 8])
            _add(
                sets,
                "structural_ngram_hashes",
                sha256_bytes(ngram.encode("utf-8")),
            )


def _reduced_concept_projection(
    family: dict[str, Any],
) -> dict[str, Any]:
    ast = family["semantic_ast"]
    records = ast["records"]
    target = records[ast["target_row"]]
    chain_edge_count = len(ast["resolution_chain"]) - 1
    return {
        "fact_kind": family["fact_kind"],
        "candidate_value_count": len(records),
        "target_alias_count": len(target["aliases"]),
        "target_wrapper_count": len(target["wrappers"]),
        "evaluation_path_lengths": {
            "paraphrase": 1,
            "multi_hop": max(1, chain_edge_count - 1),
            "withheld_composition": chain_edge_count,
        },
    }


def _reduced_training_template_projection(
    family: dict[str, Any],
    identifiers: dict[str, set[str]],
    source_text: str,
    support_text: str,
) -> dict[str, Any]:
    return {
        "fact_kind": family["fact_kind"],
        "source_skeleton": _typed_normalize(source_text, identifiers),
        "support_skeleton": _typed_normalize(support_text, identifiers),
    }


def _reduced_evaluation_template_projection(
    raw_query: dict[str, Any],
    identifiers: dict[str, set[str]],
) -> dict[str, Any]:
    return {
        "evaluation_kind": raw_query["evaluation_kind"],
        "variant": raw_query["variant"],
        "question_skeleton": _typed_normalize(
            raw_query["question"], identifiers
        ),
        "prompt_skeleton": _typed_normalize(
            raw_query["prompt"], identifiers
        ),
    }


def _validate_root_and_manifest(
    root: Path,
    manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError("bundle root must be an absolute real directory")
    if any(parent.is_symlink() for parent in root.parents):
        raise ValueError("bundle root has a symlink ancestor")
    if sha256_file(root / "artifact-manifest.json") != R1_MANIFEST_FILE_SHA256:
        raise ValueError("artifact manifest raw digest mismatch")
    if set(manifest) != {
        "version",
        "state_slice",
        "files",
        "manifest_sha256",
    }:
        raise ValueError("artifact manifest shape")
    files = manifest["files"]
    if manifest["manifest_sha256"] != canonical_sha256(files):
        raise ValueError("artifact manifest self hash")
    if manifest["manifest_sha256"] != R1_MANIFEST_SHA256:
        raise ValueError("artifact manifest semantic identity")
    if not isinstance(files, list):
        raise ValueError("artifact manifest files")
    paths = [entry.get("path") for entry in files if isinstance(entry, dict)]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ValueError("artifact manifest path order")
    declared: dict[str, dict[str, Any]] = {}
    for entry in files:
        if set(entry) != {"path", "sha256", "size_bytes"}:
            raise ValueError("artifact manifest entry")
        path_text = entry["path"]
        if (
            not isinstance(path_text, str)
            or path_text.startswith("/")
            or "\\" in path_text
            or any(
                component in ("", ".", "..")
                for component in path_text.split("/")
            )
        ):
            raise ValueError("artifact manifest path")
        path = root / path_text
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or unsafe artifact: {path_text}")
        if (
            isinstance(entry["size_bytes"], bool)
            or not isinstance(entry["size_bytes"], int)
            or entry["size_bytes"] < 0
            or path.stat().st_size != entry["size_bytes"]
            or sha256_file(path) != entry["sha256"]
        ):
            raise ValueError(f"artifact integrity mismatch: {path_text}")
        declared[path_text] = entry
    observed: set[str] = set()
    for current_root, directories, filenames in os.walk(
        root, followlinks=False
    ):
        current = Path(current_root)
        for directory in directories:
            if (current / directory).is_symlink():
                raise ValueError("symlink in artifact bundle")
        for filename in filenames:
            path = current / filename
            relative = path.relative_to(root).as_posix()
            if relative != "artifact-manifest.json":
                observed.add(relative)
    if observed != set(declared):
        raise ValueError("artifact manifest file census")
    if not REQUIRED_ROOT_PATHS - {"artifact-manifest.json"} <= set(declared):
        raise ValueError("required root artifact missing")
    return declared


def _load_member(
    root: Path,
    declared: dict[str, dict[str, Any]],
    path_text: str,
) -> dict[str, Any]:
    if path_text not in declared:
        raise ValueError(f"undeclared member: {path_text}")
    loaded = load_json_strict(root / path_text)
    if not isinstance(loaded, dict):
        raise ValueError(f"member is not an object: {path_text}")
    return loaded


def _extract_manifest(
    packet: dict[str, Any],
    report: dict[str, Any],
    checkpoint: dict[str, Any],
    seed_material: dict[str, Any],
    seed_commitment: dict[str, Any],
    raw_corpus: dict[str, Any],
    protocol_corpus: dict[str, Any],
    future: dict[str, Any],
    configuration: dict[str, Any],
    one_shot: dict[str, Any],
) -> dict[str, Any]:
    if report.get("status") != "CorpusNotNovel":
        raise ValueError("retired report disposition is not CorpusNotNovel")
    if report.get("errors") != [] or report.get("open_gates") != [
        "acquisition.new_corpus_required"
    ]:
        raise ValueError("retired report is not the closed novelty stop")
    _verify_self_hash(packet, "packet_sha256", R1_PACKET_SHA256)
    _verify_self_hash(report, "report_sha256", R1_REPORT_SHA256)
    _verify_self_hash(checkpoint, "receipt_sha256")
    _verify_self_hash(seed_commitment, "seed_commitment_sha256")
    _verify_self_hash(raw_corpus, "raw_corpus_sha256")
    if protocol_corpus.get("manifest_sha256") != canonical_sha256(
        protocol_corpus.get("items")
    ):
        raise ValueError("protocol corpus manifest")
    _verify_self_hash(
        future, "future_assessment_family_commitment_sha256"
    )
    _verify_self_hash(configuration, "configuration_lock_sha256")
    seed_hex = seed_material.get("seed_hex")
    if (
        not isinstance(seed_hex, str)
        or len(seed_hex) != 64
        or sha256_bytes(bytes.fromhex(seed_hex))
        != seed_commitment.get("seed_sha256")
    ):
        raise ValueError("seed material binding")
    receipt = checkpoint["receipt_sha256"]
    for value in (
        seed_material,
        seed_commitment,
        raw_corpus,
        future,
        configuration,
        one_shot,
    ):
        if value.get("receipt_sha256") != receipt:
            raise ValueError("checkpoint receipt chain")
    provenance = packet.get("provenance", {})
    for key, expected in {
        "seed_commitment_sha256": seed_commitment[
            "seed_commitment_sha256"
        ],
        "corpus_manifest_sha256": protocol_corpus["manifest_sha256"],
        "future_assessment_family_commitment_sha256": future[
            "future_assessment_family_commitment_sha256"
        ],
        "configuration_lock_sha256": configuration[
            "configuration_lock_sha256"
        ],
    }.items():
        if provenance.get(key) != expected:
            raise ValueError(f"packet provenance binding: {key}")
    if raw_corpus.get("seed_commitment_sha256") != seed_commitment.get(
        "seed_commitment_sha256"
    ):
        raise ValueError("raw corpus seed binding")
    raw_families = raw_corpus.get("families")
    protocol_items = protocol_corpus.get("items")
    packet_items = packet.get("corpus", {}).get("items")
    if (
        not isinstance(raw_families, list)
        or len(raw_families) != 96
        or protocol_items != packet_items
        or len(protocol_items) != 96
    ):
        raise ValueError("corpus census or packet binding")
    protocol_by_family = {
        item["family_id"]: item for item in protocol_items
    }
    if len(protocol_by_family) != 96:
        raise ValueError("duplicate protocol family")
    sets = {name: set() for name in SET_NAMES}
    _add(
        sets,
        "seed_commitments",
        seed_commitment["seed_commitment_sha256"],
    )
    _add(sets, "seed_commitments", seed_commitment["seed_sha256"])
    _add(sets, "campaign_ids", one_shot["output_directory"])
    _add(sets, "campaign_ids", one_shot["source_commit"])
    _add(sets, "ledger_ids", one_shot["output_directory"])
    _add(sets, "ledger_ids", one_shot["receipt_sha256"])
    _add(
        sets,
        "future_assessment_commitments",
        future["future_assessment_family_commitment_sha256"],
    )
    seen_items: set[str] = set()
    seen_queries: set[str] = set()
    for family in raw_families:
        protocol_item = protocol_by_family.get(family.get("family_id"))
        if protocol_item is None:
            raise ValueError("raw family missing protocol binding")
        if protocol_item.get("item_id") != family.get("item_id"):
            raise ValueError("item binding")
        family_id = family["family_id"]
        item_id = family["item_id"]
        if item_id in seen_items:
            raise ValueError("duplicate item")
        seen_items.add(item_id)
        for name, value in (
            ("namespace_ids", family["namespace"]),
            ("family_ids", family_id),
            ("item_ids", item_id),
            (
                "concept_schema_ids",
                f"{family['semantic_ast']['version']}:{family['fact_kind']}",
            ),
            ("training_template_ids", family["training_template_family_id"]),
        ):
            _add(sets, name, value)
        semantic_ast = family["semantic_ast"]
        semantic_rows = [
            {
                "aliases": record["aliases"],
                "anchor": record["anchor"],
                "row_index": record["row_index"],
                "value": record["current_value"],
                "wrappers": record["wrappers"],
            }
            for record in semantic_ast.get("records", [])
        ]
        if (
            semantic_ast.get("namespace") != family["namespace"]
            or semantic_ast.get("fact_kind") != family["fact_kind"]
            or semantic_rows != family["rows"]
        ):
            raise ValueError("semantic AST binding")
        _add(
            sets,
            "concept_ast_hashes",
            canonical_sha256(semantic_ast),
        )
        _add(
            sets,
            "concept_ast_hashes",
            canonical_sha256(_reduced_concept_projection(family)),
        )
        identifiers: dict[str, set[str]] = {
            "namespace": {family["namespace"]},
            "anchor": set(),
            "value": set(),
            "alias": set(),
            "wrapper": set(),
        }
        for row in family["rows"]:
            _add(sets, "anchor_ids", row["anchor"])
            _add(sets, "value_ids", row["value"])
            identifiers["anchor"].add(row["anchor"])
            identifiers["value"].add(row["value"])
            for alias in row["aliases"]:
                _add(sets, "alias_ids", alias)
                identifiers["alias"].add(alias)
            for wrapper in row["wrappers"]:
                _add(sets, "wrapper_ids", wrapper)
                identifiers["wrapper"].add(wrapper)
        source_text, source_hash = _verified_source_text_hash(
            family["source_form"]
        )
        support_text, support_hash = _verified_source_text_hash(
            family["support_source"]
        )
        if protocol_item.get("source_form_sha256") != source_hash:
            raise ValueError("source protocol binding")
        if protocol_item.get("support_source_sha256s") != [support_hash]:
            raise ValueError("support protocol binding")
        _add(sets, "source_hashes", source_hash)
        _add(sets, "support_hashes", support_hash)
        _add_structural_surfaces(sets, source_text, identifiers)
        _add_structural_surfaces(sets, support_text, identifiers)
        option_hashes: list[str] = []
        for option in family["answer_options"]:
            option_text, option_hash = _verified_option_text_hash(option)
            option_hashes.append(option_hash)
            _add(sets, "option_hashes", option_hash)
            if option_text not in identifiers["value"]:
                raise ValueError("option semantic binding")
        if protocol_item.get("answer_option_sha256s") != option_hashes:
            raise ValueError("option protocol binding")
        raw_queries = family["queries"]
        protocol_queries = protocol_item.get("queries")
        if not isinstance(raw_queries, list) or len(raw_queries) != 12:
            raise ValueError("query census")
        if not isinstance(protocol_queries, list) or len(protocol_queries) != 12:
            raise ValueError("protocol query census")
        for raw_query, protocol_query in zip(raw_queries, protocol_queries):
            query_id = raw_query["query_id"]
            if query_id in seen_queries:
                raise ValueError("duplicate query")
            seen_queries.add(query_id)
            if protocol_query.get("query_id") != query_id:
                raise ValueError("query order binding")
            question_hash = sha256_bytes(
                raw_query["question"].encode("utf-8")
            )
            prompt_hash = sha256_bytes(raw_query["prompt"].encode("utf-8"))
            raw_option_hashes = [
                _verified_option_text_hash(option)[1]
                for option in raw_query["answer_options"]
            ]
            for key, expected in {
                "prompt_sha256": prompt_hash,
                "answer_option_sha256s": raw_option_hashes,
                "dependency_source_sha256s": raw_query[
                    "dependency_source_sha256s"
                ],
                "template_family_id": raw_query["template_family_id"],
            }.items():
                if protocol_query.get(key) != expected:
                    raise ValueError(f"protocol query binding: {key}")
            if raw_query["prompt_sha256"] != prompt_hash:
                raise ValueError("raw prompt binding")
            _add(sets, "query_ids", query_id)
            _add(sets, "question_hashes", question_hash)
            _add(sets, "prompt_hashes", prompt_hash)
            _add(
                sets,
                "evaluation_template_ids",
                raw_query["template_family_id"],
            )
            _add(
                sets,
                "template_ast_hashes",
                canonical_sha256(
                    _reduced_evaluation_template_projection(
                        raw_query, identifiers
                    )
                ),
            )
            for digest in raw_option_hashes:
                _add(sets, "option_hashes", digest)
            for digest in raw_query["dependency_source_sha256s"]:
                _add(sets, "dependency_hashes", digest)
            _add(
                sets,
                "mapping_hashes",
                protocol_query["answer_mapping_sha256"],
            )
            _add(
                sets,
                "mapping_hashes",
                protocol_query["derivation_manifest_sha256"],
            )
            _add_structural_surfaces(
                sets, raw_query["question"], identifiers
            )
            _add_structural_surfaces(sets, raw_query["prompt"], identifiers)
        _add(
            sets,
            "template_ast_hashes",
            canonical_sha256(
                _reduced_training_template_projection(
                    family,
                    identifiers,
                    source_text,
                    support_text,
                )
            ),
        )
    if len(seen_queries) != 1152:
        raise ValueError("query identity census")
    future_ids = future.get("family_ids")
    if (
        not isinstance(future_ids, list)
        or len(future_ids) != 96
        or len(set(future_ids)) != 96
    ):
        raise ValueError("future assessment family census")
    for family_id in future_ids:
        _add(sets, "future_assessment_family_ids", family_id)
    output: dict[str, Any] = {
        "version": "astral.rgs_v28r1_retired_fingerprint.v1",
        "state_slice": "astral-rgs-v28r2-retired-r1-fingerprint",
        "source_bundle": {
            "packet_sha256": R1_PACKET_SHA256,
            "validation_report_sha256": R1_REPORT_SHA256,
            "artifact_manifest_sha256": R1_MANIFEST_SHA256,
            "packet_file_sha256": R1_PACKET_FILE_SHA256,
            "validation_report_file_sha256": R1_REPORT_FILE_SHA256,
            "artifact_manifest_file_sha256": R1_MANIFEST_FILE_SHA256,
            "generator_sha256": provenance["generator_sha256"],
            "seed_commitment_sha256": provenance[
                "seed_commitment_sha256"
            ],
            "corpus_manifest_sha256": provenance[
                "corpus_manifest_sha256"
            ],
            "future_assessment_commitment_sha256": provenance[
                "future_assessment_family_commitment_sha256"
            ],
            "disposition": "CorpusNotNovel",
        },
        "normalization_profile": {
            "unicode": "NFC",
            "case": "lowercase",
            "generated_values": "typed_placeholders_from_semantic_ast",
            "whitespace": "collapse_ascii_whitespace",
            "structural_ngram_size": 8,
        },
        "fingerprint_sets": {},
        "model_outcomes_included": False,
        "paths_sorted": True,
    }
    for name in SET_NAMES:
        items = sorted(sets[name])
        output["fingerprint_sets"][name] = {
            "count": len(items),
            "items": items,
            "set_sha256": canonical_sha256(items),
        }
    output["manifest_sha256"] = canonical_sha256(output)
    return output


def build_from_bundle(
    packet_path: Path,
    report_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    expected_names = (
        "acquisition-packet.json",
        "astral-validation-report.json",
        "artifact-manifest.json",
    )
    paths = (packet_path, report_path, manifest_path)
    if any(
        not path.is_absolute() or not path.is_file() or path.is_symlink()
        for path in paths
    ):
        raise ValueError("inputs must be absolute regular non-symlink files")
    if tuple(path.name for path in paths) != expected_names:
        raise ValueError("input basenames")
    roots = {path.parent for path in paths}
    if len(roots) != 1:
        raise ValueError("inputs must share one bundle root")
    root = paths[0].parent
    manifest = load_json_strict(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("artifact manifest object")
    declared = _validate_root_and_manifest(root, manifest)
    if sha256_file(packet_path) != R1_PACKET_FILE_SHA256:
        raise ValueError("packet raw digest")
    if sha256_file(report_path) != R1_REPORT_FILE_SHA256:
        raise ValueError("report raw digest")
    loaded = {
        path_text: _load_member(root, declared, path_text)
        for path_text in REQUIRED_ROOT_PATHS
        if path_text != "artifact-manifest.json"
    }
    return _extract_manifest(
        loaded["acquisition-packet.json"],
        loaded["astral-validation-report.json"],
        loaded["checkpoint-receipt.json"],
        loaded["seed-material.json"],
        loaded["seed-commitment.json"],
        loaded["raw-corpus.json"],
        loaded["protocol-corpus.json"],
        loaded["future-assessment-commitment.json"],
        loaded["configuration-lock.json"],
        loaded["one-shot-execution-claim.json"],
    )


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise OSError("zero-progress fingerprint write")
        offset += written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a hash-only retired V28R1 fingerprint manifest."
    )
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--validation-report", type=Path, required=True)
    parser.add_argument("--artifact-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        output = args.output
        if not output.is_absolute() or output.exists() or output.is_symlink():
            raise ValueError("output must be a new absolute path")
        if output.parent.is_symlink() or not output.parent.is_dir():
            raise ValueError("output parent must be an existing real directory")
        result = build_from_bundle(
            args.packet,
            args.validation_report,
            args.artifact_manifest,
        )
        descriptor = os.open(
            output,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            _write_all(descriptor, canonical_bytes(result) + b"\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        directory_descriptor = os.open(output.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, f"error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
