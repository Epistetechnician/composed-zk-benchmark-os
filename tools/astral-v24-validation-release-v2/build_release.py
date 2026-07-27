#!/usr/bin/env python3
"""Build the content-addressed Astral V24 validation release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from release import (
    observed_runtime,
    sha256,
    verify_json_manifest_directory,
    verify_model_inventory,
    write_json,
    write_manifest,
)


HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
SPEC_PATH = HERE.with_name("release-spec.json")
MANIFEST_NAME = "RELEASE-MANIFEST.sha256"


def git(*arguments: str, text: bool = True):
    output = subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=text,
    ).stdout
    return output.strip() if text else output


def source_in_scope(relative: str) -> bool:
    return relative in {"AGENTS.md", "Cargo.toml", "Cargo.lock", "README.md"} or any(
        relative.startswith(prefix)
        for prefix in (
            "crates/astral-stage0-protocol/",
            "docs/research/astral-self-modeling/",
            "tools/astral-",
        )
    )


def source_inventory(commit: str) -> dict[str, str]:
    paths = git("ls-tree", "-r", "--name-only", commit).splitlines()
    inventory = {}
    for relative in sorted(path for path in paths if source_in_scope(path)):
        content = git("show", f"{commit}:{relative}", text=False)
        inventory[relative] = hashlib.sha256(content).hexdigest()
    return inventory


def require_external_output(path: Path) -> None:
    try:
        path.relative_to(REPOSITORY)
    except ValueError:
        return
    raise ValueError("release output parent must be outside the repository")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output-parent", required=True, type=Path)
    args = parser.parse_args()
    if git("status", "--porcelain"):
        raise SystemExit("release builder worktree must be clean")
    spec = json.loads(SPEC_PATH.read_text())
    if git("rev-parse", spec["source_commit"]) != spec["source_commit"]:
        raise SystemExit("frozen source commit is absent")
    if git("rev-parse", f"{spec['source_commit']}^{{tree}}") != spec["source_tree"]:
        raise SystemExit("frozen source tree mismatch")

    artifact = args.artifact.resolve()
    verify_json_manifest_directory(
        artifact,
        "manifest.json",
        "astral-v24",
        spec["artifact_identity"],
    )
    result = json.loads((artifact / "result.json").read_text())
    if (
        result.get("classification") != spec["expected_classification"]
        or result.get("claim_ceiling") != spec["claim_ceiling"]
        or result.get("independently_verified") != "NotRun"
    ):
        raise SystemExit("V24 artifact result binding mismatch")
    model_inventory = json.loads((artifact / "model-inventory.json").read_text())
    model = args.model.resolve()
    verify_model_inventory(model, model_inventory)

    output_parent = args.output_parent.resolve()
    require_external_output(output_parent)
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".astral-v24-release-v2-", dir=output_parent))
    try:
        (staging / "artifact").mkdir()
        (staging / "metadata").mkdir()
        shutil.copytree(artifact, staging / "artifact" / artifact.name)
        shutil.copytree(model, staging / "model/qwen", symlinks=False)
        shutil.copy2(SPEC_PATH, staging / "metadata/release-spec.json")
        shutil.copy2(
            REPOSITORY
            / "docs/research/astral-self-modeling/50-v24-independent-validation-release-v2-spec.md",
            staging / "README.md",
        )
        write_json(staging / "metadata/source-inventory.json", source_inventory(spec["source_commit"]))
        write_json(staging / "metadata/runtime-contract.json", observed_runtime())
        write_json(
            staging / "metadata/build-record.json",
            {
                "artifact_identity": spec["artifact_identity"],
                "builder_commit": git("rev-parse", "HEAD"),
                "builder_sha256": sha256(HERE),
                "builder_tree": git("rev-parse", "HEAD^{tree}"),
                "claim_ceiling": spec["claim_ceiling"],
                "model_file_count": len(model_inventory["files"]),
                "source_commit": spec["source_commit"],
                "source_tree": spec["source_tree"],
                "validator_sha256": sha256(HERE.with_name("validate_release.py")),
            },
        )
        identity = write_manifest(staging, MANIFEST_NAME)
        destination = output_parent / f"{spec['release_id']}-{identity}"
        if destination.exists():
            raise RuntimeError("content-addressed release already exists")
        os.replace(staging, destination)
        print(
            json.dumps(
                {"release": str(destination), "release_identity": identity},
                sort_keys=True,
            )
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
