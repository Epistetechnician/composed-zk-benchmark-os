from __future__ import annotations

import argparse
import json
from pathlib import Path

from v28r3 import sha256_text, stable_hash, validate_corpus, validate_fingerprint


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and independently rederive a V28R3 corpus")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--seed-material", type=Path, required=True)
    parser.add_argument("--predecessor-fingerprint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    seed_doc = json.loads(args.seed_material.read_text(encoding="utf-8"))
    fingerprint = json.loads(args.predecessor_fingerprint.read_text(encoding="utf-8"))
    errors: list[str] = []
    validate_fingerprint(fingerprint, errors)
    try:
        seed = bytes.fromhex(seed_doc["seed_hex"])
    except (KeyError, TypeError, ValueError):
        seed = b""
        errors.append("seed.material")
    if seed_doc.get("seed_commitment") != sha256_text(seed_doc.get("seed_hex", "")):
        errors.append("seed.commitment")
    families, queries = validate_corpus(
        corpus, seed=seed, fingerprint=fingerprint, errors=errors
    )
    core = {
        "version": "astral.v28r3_corpus_validation_report.v1",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "family_count": len(families),
        "query_count": len(queries),
        "corpus_manifest_sha256": corpus.get("manifest_sha256"),
    }
    result = {**core, "report_sha256": stable_hash(core)}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
