from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_CHECKPOINT = (
    "sha256:0a321941ffa31f920284c932f98bd4dba7c7cb95acd797c01ec2fa0fdd1321ab"
)
EXPECTED_TOKENIZER = (
    "sha256:43c4bf51c8db8d03b43a5c2b3d1c44adf886d12fe3eba979b9d41f6101d10f5b"
)
EXPECTED_RUNTIME = {
    "python": "3.14.5",
    "mlx": "0.31.2",
    "mlx-lm": "0.31.3",
    "numpy": "2.4.5",
}
RUNGS = ("literal_copy", "direct_lookup", "one_hop", "two_hop")


def _canonical(value: Any) -> str:
    return json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True)


def _stable(value: Any) -> str:
    wrapped = {"replay_parts": [value]}
    return "sha256:" + hashlib.sha256(_canonical(wrapped).encode()).hexdigest()


def _sha256(value: Any) -> bool:
    text = str(value)
    return text.startswith("sha256:") and len(text) == 71


def _git_oid(value: Any) -> bool:
    text = str(value)
    return len(text) == 40 and all(character in "0123456789abcdef" for character in text)


def validate(data: dict) -> dict:
    errors = []
    overlay = data.get("overlay", {})
    qualification = data.get("qualification", {})
    source = data.get("source", {})
    runtime = data.get("runtime", {})
    inventory = data.get("model_inventory", {})

    overlay_body = {
        key: value for key, value in overlay.items() if key != "overlay_sha256"
    }
    if overlay.get("overlay_sha256") != _stable(overlay_body):
        errors.append("overlay hash")
    qualification_body = {
        key: value
        for key, value in qualification.items()
        if key != "qualification_sha256"
    }
    if qualification.get("qualification_sha256") != _stable(qualification_body):
        errors.append("qualification hash")
    if qualification.get("version") != "mesh.astral_v40r2_fit_probe_qualification.v2":
        errors.append("qualification version")
    if qualification.get("overlay_sha256") != overlay.get("overlay_sha256"):
        errors.append("overlay binding")
    if qualification.get("tokenizer_sha256") != EXPECTED_TOKENIZER:
        errors.append("tokenizer binding")
    if data.get("forward_pass") is not False or qualification.get("forward_pass") is not False:
        errors.append("forward-pass boundary")
    if inventory.get("checkpoint_sha256") != EXPECTED_CHECKPOINT:
        errors.append("model checkpoint")
    if inventory.get("tokenizer_sha256") != EXPECTED_TOKENIZER:
        errors.append("model tokenizer")
    if any(runtime.get(key) != value for key, value in EXPECTED_RUNTIME.items()):
        errors.append("runtime")
    if not _git_oid(source.get("rgs_commit")):
        errors.append("source commit")
    if not all(
        _sha256(source.get(field))
        for field in (
            "runner_sha256",
            "overlay_source_sha256",
            "corpus_input_sha256",
        )
    ):
        errors.append("source hashes")

    families = overlay.get("families", [])
    family_ids = {family.get("family_id") for family in families}
    if family_ids != {f"v40r2-fit-{index:02d}" for index in range(4)}:
        errors.append("fit family boundary")
    cases = [
        case
        for family in families
        for task in family.get("tasks", [])
        for case in task.get("cases", [])
    ]
    if len(cases) != 128 or len({case.get("case_id") for case in cases}) != 128:
        errors.append("fit case coverage")
    protected = overlay.get("protected_cases", [])
    if len(protected) != 16 or Counter(case.get("rung") for case in protected) != Counter(
        {rung: 4 for rung in RUNGS}
    ):
        errors.append("protected coverage")
    v40_targets = {case.get("target") for case in cases}
    if any(set(case.get("candidates", [])).intersection(v40_targets) for case in protected):
        errors.append("protected overlap")

    prompt_rows = qualification.get("prompt_rows", [])
    if qualification.get("prompt_count") != 400 or len(prompt_rows) != 400:
        errors.append("prompt coverage")
    if len({row.get("prompt_id") for row in prompt_rows}) != len(prompt_rows):
        errors.append("prompt ids")
    if any(
        row.get("input_tokens") != len(row.get("token_ids", []))
        or row.get("input_tokens", 0) <= 0
        for row in prompt_rows
    ):
        errors.append("token rows")
    maximum = max((row.get("input_tokens", 0) for row in prompt_rows), default=0)
    if qualification.get("maximum_input_tokens") != maximum or maximum > 96:
        errors.append("token ceiling")
    if qualification.get("qualified") is not True:
        errors.append("qualification")

    lengths = {
        tuple(row["prompt_id"].rsplit(":", 1)): row["input_tokens"]
        for row in prompt_rows
    }
    protected_tokens = sum(
        lengths.get((case["case_id"], "protected_prompt"), 0) for case in protected
    )
    budget = 0
    for family in families:
        tasks = {task["task_id"]: task["cases"] for task in family["tasks"]}
        for stage, task_id in enumerate(("A", "B", "C", "D"), start=1):
            if stage == 1:
                continue
            current = sum(
                lengths.get((case["case_id"], "direct_prompt"), 0)
                for case in tasks[task_id]
            )
            prior = sum(
                lengths.get((case["case_id"], "direct_prompt"), 0)
                for prior_id in ("A", "B", "C", "D")[: stage - 1]
                for case in tasks[prior_id]
            )
            paraphrase = sum(
                lengths.get((case["case_id"], "paraphrase_prompt"), 0)
                for seen_id in ("A", "B", "C", "D")[:stage]
                for case in tasks[seen_id]
            )
            budget += 32 * 2 * (current + prior + paraphrase + protected_tokens)
    if qualification.get("evaluation_forward_tokens") != budget or budget <= 0:
        errors.append("evaluation budget")
    feature_budget = 4 * 3 * 2 * protected_tokens
    if (
        qualification.get("feature_probe_forward_tokens") != feature_budget
        or feature_budget <= 0
    ):
        errors.append("feature probe budget")
    return {
        "valid": not errors,
        "errors": errors,
        "fit_case_count": len(cases),
        "protected_case_count": len(protected),
        "prompt_count": len(prompt_rows),
        "maximum_input_tokens": maximum,
        "evaluation_forward_tokens": budget,
        "feature_probe_forward_tokens": feature_budget,
        "forward_pass": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.artifact_root.resolve()
    manifest = (root / "MANIFEST.sha256").read_text().strip().split()
    expected, relative = manifest
    actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    data = json.loads((root / relative).read_text())
    report = validate(data)
    if expected != actual:
        report["valid"] = False
        report["errors"].append("manifest")
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
