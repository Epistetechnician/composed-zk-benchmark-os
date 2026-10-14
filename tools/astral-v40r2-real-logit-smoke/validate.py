from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

EXPECTED_VERSION = "mesh.astral_v40r2_real_logit_smoke.v1"
EXPECTED_SLICE = "V40R2RealTokenizerLogitSmoke"
EXPECTED_CEILING = "LocalForwardOnlyRealTokenizerLogitSmokeV40R2"
EXPECTED_CHECKPOINT = (
    "sha256:0a321941ffa31f920284c932f98bd4dba7c7cb95acd797c01ec2fa0fdd1321ab"
)
EXPECTED_TOKENIZER = (
    "sha256:43c4bf51c8db8d03b43a5c2b3d1c44adf886d12fe3eba979b9d41f6101d10f5b"
)
EXPECTED_PROBE = (
    "sha256:97e7ebe81c9faef3e92fe0b04e62143ddaa1151ce55b484f6b6206707d4831b9"
)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, allow_nan=False, separators=(",", ":"), sort_keys=True
    ).encode()


def _stable_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate(artifact: Path, probe_artifact: Path, rgs_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    result_path = artifact / "real-logit-smoke.json"
    manifest_path = artifact / "MANIFEST.sha256"
    if not result_path.is_file() or not manifest_path.is_file():
        return {"valid": False, "errors": ["artifact files missing"]}
    result = json.loads(result_path.read_text())
    expected_manifest = (
        _file_hash(result_path).removeprefix("sha256:")
        + "  real-logit-smoke.json\n"
    )
    if manifest_path.read_text() != expected_manifest:
        errors.append("manifest")
    expected_scalars = {
        "version": EXPECTED_VERSION,
        "state_slice": EXPECTED_SLICE,
        "claim_ceiling": EXPECTED_CEILING,
        "classification": "RealTokenizerLogitPathOperational",
        "real_tokenizer": True,
        "real_logits": True,
        "forward_pass": True,
        "forward_count": 12,
        "model_load_count": 1,
        "training": False,
        "optimizer": False,
        "adapter": False,
        "tune_access": False,
        "assessment_access": False,
    }
    for key, expected in expected_scalars.items():
        if result.get(key) != expected:
            errors.append(key)
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != _stable_hash(body):
        errors.append("result_sha256")
    inventory = result.get("model_inventory", {})
    if inventory.get("checkpoint_sha256") != EXPECTED_CHECKPOINT:
        errors.append("checkpoint_sha256")
    if inventory.get("tokenizer_sha256") != EXPECTED_TOKENIZER:
        errors.append("tokenizer_sha256")
    source = result.get("source", {})
    if source.get("probe_artifact_sha256") != EXPECTED_PROBE:
        errors.append("probe binding")
    if _file_hash(probe_artifact) != EXPECTED_PROBE:
        errors.append("probe file")
    commit = source.get("rgs_commit", "")
    if not isinstance(commit, str) or len(commit) != 40:
        errors.append("source commit")
    else:
        for key, relative in (
            ("runner_sha256", "scripts/run_v40r2_real_logit_smoke.py"),
            (
                "core_sha256",
                "mesh_brain/meshmodel/v40r2_real_logit_smoke.py",
            ),
        ):
            try:
                content = subprocess.run(
                    ["git", "show", f"{commit}:{relative}"],
                    cwd=rgs_root,
                    check=True,
                    capture_output=True,
                ).stdout
                actual = "sha256:" + hashlib.sha256(content).hexdigest()
                if source.get(key) != actual:
                    errors.append(key)
            except subprocess.CalledProcessError:
                errors.append(f"{key} unavailable")
    receipts = result.get("receipts")
    if not isinstance(receipts, list) or len(receipts) != 12:
        errors.append("receipt count")
        receipts = []
    ids = [row.get("case_id") for row in receipts]
    expected_fit = [f"v40r2-fit-00-a-{index:02d}" for index in range(8)]
    if ids[:8] != expected_fit or len(set(ids)) != len(ids):
        errors.append("case selection")
    protected = receipts[8:]
    if len({row.get("rung") for row in protected}) != 4:
        errors.append("protected rung coverage")
    for row in receipts:
        scores = row.get("candidate_scores", {})
        values = list(scores.values()) if isinstance(scores, dict) else []
        if len(values) != 4 or any(
            not isinstance(value, (int, float)) or not math.isfinite(value)
            for value in values
        ):
            errors.append(f"score values:{row.get('case_id')}")
            continue
        if abs(sum(math.exp(value) for value in values) - 1.0) > 1e-5:
            errors.append(f"score normalization:{row.get('case_id')}")
        receipt_body = {
            key: row[key]
            for key in (
                "case_id",
                "target",
                "candidates",
                "candidate_scores",
                "selected",
                "correct",
            )
        }
        expected_receipt = _stable_hash({"replay_parts": [receipt_body]})
        if row.get("receipt_sha256") != expected_receipt:
            errors.append(f"receipt hash:{row.get('case_id')}")
        token_ids = row.get("candidate_token_ids", {})
        if (
            set(token_ids) != set(row.get("candidates", []))
            or len(set(token_ids.values())) != 4
            or not 1 <= row.get("prompt_token_count", 0) <= 96
        ):
            errors.append(f"token evidence:{row.get('case_id')}")
    runtime = result.get("runtime", {})
    for key in ("python", "executable", "mlx", "mlx-lm", "numpy"):
        if not runtime.get(key):
            errors.append(f"runtime:{key}")
    return {
        "version": "astral.v40r2_real_logit_smoke_validation.v1",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "artifact": str(artifact),
        "result_sha256": result.get("result_sha256"),
        "claim_ceiling": EXPECTED_CEILING if not errors else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--probe-artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    report = validate(
        args.artifact.resolve(),
        args.probe_artifact.resolve(),
        args.rgs_root.resolve(),
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(text)
    print(text, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
