"""Independent pre-load review for the V3 normalization and asset contract.

State slice: astral-trace-completeness-gemma3-end-to-end-v3.
This reviewer does not load the base model and cannot open assessment.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import protocol_v3 as protocol


SOURCE_FILES = ("protocol_v3.py", "asset_qc_v3.py", "review_v3.py")
RECEIPT_FILENAME = "preload-review-v3-r2.json"


def _write_private(path: Path, value: dict[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(protocol.canonical_bytes(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _source_manifest(repository_root: Path) -> dict[str, Any]:
    source_root = repository_root / "tools" / "astral-trace-completeness-v3"
    files = {name: protocol.sha256_file(source_root / name) for name in SOURCE_FILES}
    return {"files": files, "manifest_sha256": protocol.digest_json(files)}


def review(repository_root: Path, custody_root: Path) -> dict[str, Any]:
    if custody_root.resolve() != protocol.CUSTODY_ROOT.resolve():
        raise protocol.ProtocolError("V3 custody identity is fixed")
    contract = protocol.public_contract()
    if contract["contract_sha256"] != protocol.digest_json({key: value for key, value in contract.items() if key != "contract_sha256"}):
        raise protocol.ProtocolError("protocol contract digest mismatch")
    qc_path = custody_root / "aggregate" / "preload-asset-qc.json"
    qc = protocol.strict_json(qc_path)
    if qc.get("asset_qc_sha256") != protocol.digest_json({key: value for key, value in qc.items() if key != "asset_qc_sha256"}):
        raise protocol.ProtocolError("asset QC digest mismatch")
    if qc.get("valid") is not True or qc.get("model_execution") is not False or qc.get("assessment_opened") is not False:
        raise protocol.ProtocolError("asset QC is not a sealed pre-load result")
    if qc.get("asset_repository") != protocol.ASSET_REPOSITORY or qc.get("asset_revision") != protocol.ASSET_REVISION or qc.get("asset_variant") != protocol.ASSET_VARIANT:
        raise protocol.ProtocolError("asset identity mismatch")
    if qc.get("examples_are_metadata_only") is not True or qc.get("reconstruction_target_source") != "fresh_model_qualification_fit_rows":
        raise protocol.ProtocolError("asset example semantics are not explicit")
    if qc.get("custody", {}).get("valid") is not True:
        raise protocol.ProtocolError("custody receipt is not valid")
    protocol.reject_raw_fields(qc)
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "review_type": "independent_preload_normalization_and_asset_schema_review",
        "reviewer": "review_v3.independent_static_validator",
        "contract_sha256": contract["contract_sha256"],
        "asset_qc_sha256": qc["asset_qc_sha256"],
        "source": _source_manifest(repository_root),
        "normalization_estimand_accepted": True,
        "asset_quality_schema_accepted": True,
        "model_execution": False,
        "assessment_opened": False,
        "signed_assessment_acceptance": False,
        "status": "PRELOAD_ACCEPTED_STATIC_VALIDATOR",
        "claim_ceiling": protocol.QUALIFICATION_CEILING,
    }
    return {**value, "review_sha256": protocol.digest_json(value)}


def execute(repository_root: Path, custody_root: Path) -> dict[str, Any]:
    receipt = protocol.custody_receipt(custody_root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("custody root invalid")
    result = review(repository_root, custody_root)
    path = custody_root / "review" / RECEIPT_FILENAME
    _write_private(path, result)
    return {**result, "receipt_path": str(path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--custody-root", type=Path, default=protocol.CUSTODY_ROOT)
    args = parser.parse_args(argv)
    print(json.dumps(execute(args.repository_root.resolve(), args.custody_root.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
