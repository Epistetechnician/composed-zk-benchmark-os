#!/usr/bin/env python3
"""Build and execute Astral V25 with fail-closed Docker isolation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE_IMAGE_DIGEST = "python@sha256:76d4b7b6305788c6b4c6a19d6a22a3921bf802e9af4d5e1e5bd771208dba74bf"


def run(command: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=HERE,
        capture_output=capture,
        text=True,
        env={**os.environ, "DOCKER_BUILDKIT": "1"},
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    return completed


def build_tag() -> str:
    digest = hashlib.sha256()
    for name in ("Dockerfile", "experiment-contract.json", "v25.py"):
        digest.update((HERE / name).read_bytes())
    return f"astral-v25:{digest.hexdigest()[:16]}"


def execute(output_parent: Path) -> dict[str, str]:
    output_parent = output_parent.resolve()
    if output_parent.is_symlink():
        raise ValueError("artifact parent may not be a symlink")
    output_parent.mkdir(parents=True, exist_ok=True)
    building = output_parent / "astral-v25-building"
    if building.exists():
        raise ValueError("stale V25 building directory exists")
    tag = build_tag()
    run(
        [
            "docker",
            "build",
            "--network=none",
            "--pull=false",
            "--provenance=false",
            "--tag",
            tag,
            ".",
        ]
    )
    image_id = run(["docker", "image", "inspect", tag, "--format", "{{.Id}}" ]).stdout.strip()
    if not image_id.startswith("sha256:"):
        raise ValueError("Docker image identity missing")
    command = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=128",
        "--memory=512m",
        "--cpus=2",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--env",
        f"ASTRAL_V25_BASE_IMAGE_DIGEST={BASE_IMAGE_DIGEST}",
        "--env",
        f"ASTRAL_V25_IMAGE_ID={image_id}",
        "--mount",
        f"type=bind,src={output_parent},dst=/artifacts",
        tag,
        "run",
        "--root",
        "/artifacts/astral-v25-building",
    ]
    completed = run(command)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Docker execution produced no result")
    result = json.loads(lines[-1])
    if result.get("status") != "completed":
        raise ValueError("Docker execution did not complete")
    artifact = output_parent / Path(result["artifact"]).name
    if not artifact.is_dir():
        raise ValueError("Docker artifact missing after execution")
    validator = run([sys.executable, str(HERE / "validator_v25.py"), str(artifact)])
    validation = json.loads(validator.stdout.splitlines()[-1])
    if validation.get("status") != "V25ValidationPassed":
        raise ValueError("host validation did not pass")
    return {
        "artifact": str(artifact),
        "container_image_id": image_id,
        "image_tag": tag,
        "manifest_sha256": result["manifest_sha256"],
        "status": result["classification"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-parent", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = execute(args.output_parent)
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
