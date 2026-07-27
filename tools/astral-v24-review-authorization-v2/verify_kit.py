#!/usr/bin/env python3
"""Verify the complete V24 review-authorization kit before use."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath

from review_auth import (
    load_canonical,
    sha256_file,
    validate_admin_policy,
    validate_spec,
)


SHA256 = re.compile(r"^[0-9a-f]{64}$")
KIT_ID = "astral-v24-review-authorization-kit-v2"
MANIFEST_NAME = "KIT-MANIFEST.sha256"


def verify_kit(root: Path) -> dict[str, object]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("kit root must be a real directory")
    manifest = root / MANIFEST_NAME
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError("kit manifest must be a real file")
    rows = {}
    for line in manifest.read_text().splitlines():
        expected, separator, relative = line.partition("  ")
        path = PurePosixPath(relative)
        if (
            not separator
            or not SHA256.fullmatch(expected)
            or relative != path.as_posix()
            or path.is_absolute()
            or ".." in path.parts
            or relative in rows
        ):
            raise ValueError("invalid kit manifest row")
        rows[relative] = expected
    if list(rows) != sorted(rows):
        raise ValueError("kit manifest rows are not sorted")
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("kit symlink is forbidden")
        if path.is_file() and path != manifest:
            actual.add(path.relative_to(root).as_posix())
    if actual != set(rows):
        raise ValueError("kit manifest census mismatch")
    for relative, expected in rows.items():
        if sha256_file(root / relative) != expected:
            raise ValueError(f"kit manifest digest mismatch: {relative}")
    identity = sha256_file(manifest)
    if root.name != f"{KIT_ID}-{identity}":
        raise ValueError("kit content-addressed name mismatch")
    policy, policy_sha256 = load_canonical(root / "metadata/admin-policy.json")
    spec, _ = load_canonical(root / "metadata/gate-spec.json")
    validate_admin_policy(policy)
    validate_spec(spec)
    if policy_sha256 != spec["admin_policy_sha256"]:
        raise ValueError("kit admin policy binding mismatch")
    return {
        "admin_id": policy["admin_id"],
        "file_count": len(rows),
        "kit_identity": identity,
        "status": "V24ReviewAuthorizationKitValid",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify_kit(args.kit.resolve())
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"reason": str(exc), "valid": False}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
