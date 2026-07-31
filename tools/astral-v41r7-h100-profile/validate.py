from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

EXPECTED_VERSION = "mesh.astral_v41r7_h100_runtime_profile.v1"
EXPECTED_SLICE = "V41R7ExpertLoRAMemoryCorrection"
EXPECTED_MODEL = "openai/gpt-oss-20b"
EXPECTED_REVISION = "d0e2aa76789354d715f8b22553b9feb6c462fcf0"
EXPECTED_CEILING = "RemoteH100RuntimeProfileOnlyV41R7"
EXPECTED_RUNTIME = {
    "torch": "2.10.0",
    "transformers": "4.57.6",
    "peft": "0.18.1",
    "cuda": "12.8",
}


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, allow_nan=False, separators=(",", ":"), sort_keys=True
    ).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate_microbatches(update: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = update.get("microbatches")
    if not isinstance(rows, list) or len(rows) != 4:
        return ["microbatch count"]
    if [(row.get("start"), row.get("end")) for row in rows] != [
        (0, 1), (1, 2), (2, 3), (3, 4)
    ]:
        errors.append("microbatch coverage")
    weights = [row.get("weight") for row in rows]
    if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in weights):
        errors.append("microbatch weights")
    elif abs(sum(weights) - 1.0) > 1.0e-12:
        errors.append("microbatch weight sum")
    targets = [row.get("target_tokens") for row in rows]
    if any(not isinstance(value, int) or value <= 0 for value in targets):
        errors.append("microbatch target tokens")
    for index, row in enumerate(rows):
        memory = row.get("memory")
        if not isinstance(memory, dict):
            errors.append(f"microbatch memory:{index}")
            continue
        if any(not isinstance(memory.get(key), int) or memory[key] < 0 for key in (
            "allocated_bytes", "reserved_bytes", "peak_allocated_bytes", "peak_reserved_bytes"
        )):
            errors.append(f"microbatch memory:{index}")
    return errors


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    result_path = artifact / "profile-result.json"
    manifest_path = artifact / "MANIFEST.sha256"
    if not result_path.is_file() or not manifest_path.is_file():
        return {"valid": False, "errors": ["profile artifact files missing"]}
    result = json.loads(result_path.read_text())
    expected_manifest = (
        file_hash(result_path).removeprefix("sha256:")
        + "  profile-result.json\n"
    )
    if manifest_path.read_text() != expected_manifest:
        errors.append("manifest")
    for key, value in {
        "version": EXPECTED_VERSION,
        "state_slice": EXPECTED_SLICE,
        "classification": "RuntimeProfileOperational",
        "tune_opened": False,
        "assessment_opened": False,
        "scientific_result": False,
        "claim_ceiling": EXPECTED_CEILING,
    }.items():
        if result.get(key) != value:
            errors.append(key)
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != canonical_hash(body):
        errors.append("result_sha256")

    model = result.get("model", {})
    if model.get("id") != EXPECTED_MODEL or model.get("revision") != EXPECTED_REVISION:
        errors.append("model binding")
    runtime = result.get("runtime", {})
    if "H100" not in str(runtime.get("gpu", "")).upper():
        errors.append("gpu")
    for key, value in EXPECTED_RUNTIME.items():
        if runtime.get(key) != value:
            errors.append(f"runtime:{key}")

    correction = result.get("correction", {})
    if correction != {
        "microbatch_size": 1,
        "effective_batch_size": 4,
        "loss_weighting": "nonignored_causal_target_tokens",
        "optimizer_steps": 1,
        "dropout_required_zero": True,
        "cuda_cache_cleared_before_update": True,
    }:
        errors.append("correction binding")

    update = result.get("update_evidence", {})
    if (
        update.get("gradient_steps") != 1
        or update.get("microbatch_forwards") != 4
        or update.get("training_examples") != 4
        or update.get("rollback_exact") is not True
        or update.get("pre_state_sha256") != update.get("rollback_state_sha256")
        or update.get("pre_state_sha256") == update.get("post_state_sha256")
    ):
        errors.append("update and rollback evidence")
    for key in ("loss", "gradient_norm"):
        value = update.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"update:{key}")
    errors.extend(validate_microbatches(update))

    forward = result.get("forward_evidence", {})
    if forward.get("real_tokenizer") is not True or forward.get("real_logits") is not True:
        errors.append("real forward flags")
    if forward.get("pre_direct") != forward.get("post_rollback_direct"):
        errors.append("post-rollback logit parity")
    for group in ("pre_direct", "pre_protected", "post_rollback_direct"):
        rows = forward.get(group)
        if not isinstance(rows, list) or len(rows) != 4:
            errors.append(f"forward:{group}")
            continue
        for row in rows:
            scores = row.get("candidate_log_probabilities", {})
            values = list(scores.values()) if isinstance(scores, dict) else []
            if (
                len(values) != 4
                or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values)
                or abs(sum(math.exp(value) for value in values) - 1.0) > 1.0e-5
            ):
                errors.append(f"scores:{group}:{row.get('case_id')}")

    source = result.get("source", {})
    commit = source.get("rgs_commit", "")
    if not isinstance(commit, str) or len(commit) != 40:
        errors.append("source commit")
    else:
        for key, relative in (
            ("runner_sha256", "scripts/run_v41r7_h100_profile.py"),
            ("baseline_runner_sha256", "scripts/run_v41_h100_profile.py"),
            ("microbatch_source_sha256", "mesh_brain/meshmodel/v41r7_microbatch.py"),
            ("contract_source_sha256", "mesh_brain/meshmodel/v41_h100_acquisition.py"),
            ("requirements_sha256", "requirements-v41-h100-profile.txt"),
        ):
            try:
                content = subprocess.run(
                    ["git", "show", f"{commit}:{relative}"],
                    cwd=rgs_root,
                    check=True,
                    capture_output=True,
                ).stdout
                if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest():
                    errors.append(key)
            except subprocess.CalledProcessError:
                errors.append(f"{key} unavailable")
    return {
        "version": "astral.v41r7_h100_profile_validation.v1",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "artifact": str(artifact),
        "result_sha256": result.get("result_sha256"),
        "claim_ceiling": EXPECTED_CEILING if not errors else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(text)
    print(text, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
