from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import v28r2  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the complete V28R2 corpus before any model access."
    )
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--retired-r1-fingerprint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    fingerprint = json.loads(args.retired_r1_fingerprint.read_text(encoding="utf-8"))
    errors: list[str] = []
    checked = v28r2.validate_fingerprint(fingerprint, errors)
    families: dict[str, dict] = {}
    query_order: list[str] = []
    if checked is not None:
        try:
            families, query_order = v28r2.validate_corpus(corpus, checked, errors)
        except (KeyError, TypeError, IndexError, ValueError) as error:
            errors.append(f"validator.malformed_input.{type(error).__name__}")
    report = {
        "version": "astral.v28r2_corpus_validation_report.v1",
        "state_slice": v28r2.PROTOCOL["state_slice"],
        "status": "ValidCorpusCandidate" if not errors else "Invalid",
        "errors": sorted(set(errors)),
        "family_count": len(families),
        "query_count": len(query_order),
        "corpus_manifest_sha256": corpus.get("manifest_sha256") if isinstance(corpus, dict) else None,
        "retired_r1_fingerprint_sha256": fingerprint.get("fingerprint_sha256") if isinstance(fingerprint, dict) else None,
    }
    report["report_sha256"] = v28r2.content_hash(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError:
        parser.error("output already exists")
    print(f"status={report['status']}")
    print(f"report_sha256={report['report_sha256']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
