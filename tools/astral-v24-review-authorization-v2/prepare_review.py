#!/usr/bin/env python3
"""Verify admin authorization and issue fresh V24 reviewer requests."""

from __future__ import annotations

import argparse
import json
import secrets
import shutil
from pathlib import Path

from review_auth import (
    ROLES,
    SHA256,
    build_request,
    canonical_bytes,
    decision_template,
    sha256_bytes,
    validate_spec,
    verify_admin_registry_signature,
    write_canonical,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--admin-policy", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--admin-signature", required=True, type=Path)
    parser.add_argument("--expected-registry-sha256", required=True)
    parser.add_argument("--issued-at", required=True)
    parser.add_argument("--expires-at", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--nonce", action="append", default=[])
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("review request output already exists")
    spec = json.loads(args.spec.read_text())
    validate_spec(spec)
    policy = json.loads(args.admin_policy.read_text())
    if sha256_bytes(canonical_bytes(policy)) != spec["admin_policy_sha256"]:
        raise SystemExit("admin policy digest mismatch")
    registry, registry_sha256 = verify_admin_registry_signature(
        policy, args.registry, args.admin_signature
    )
    if (
        not SHA256.fullmatch(args.expected_registry_sha256)
        or registry_sha256 != args.expected_registry_sha256
    ):
        raise SystemExit("reviewer registry digest mismatch")
    reviewers = {row["role"]: row for row in registry["reviewers"]}
    supplied = {}
    for raw in args.nonce:
        role, separator, nonce = raw.partition("=")
        if not separator or role in supplied or not SHA256.fullmatch(nonce):
            raise SystemExit(f"invalid or duplicate nonce: {raw}")
        supplied[role] = nonce
    if set(supplied) - set(ROLES):
        raise SystemExit("nonce supplied for unknown role")
    requests = args.output / "requests"
    templates = args.output / "decision-templates"
    metadata = args.output / "metadata"
    for directory in (requests, templates, metadata):
        directory.mkdir(parents=True)
    request_hashes = {}
    for role in ROLES:
        request = build_request(
            spec,
            reviewers[role],
            registry_sha256,
            supplied.get(role, secrets.token_hex(32)),
            args.issued_at,
            args.expires_at,
        )
        request_path = requests / f"{role}.request.json"
        request_digest = write_canonical(request_path, request)
        write_canonical(
            templates / f"{role}.decision.template.json",
            decision_template(request, request_digest),
        )
        request_hashes[role] = request_digest
    (metadata / "gate-spec.json").write_bytes(canonical_bytes(spec))
    (metadata / "admin-policy.json").write_bytes(canonical_bytes(policy))
    (metadata / "reviewer-registry.json").write_bytes(canonical_bytes(registry))
    shutil.copy2(args.admin_signature, metadata / "reviewer-registry.json.sig")
    write_canonical(
        metadata / "request-record.json",
        {
            "admin_id": policy["admin_id"],
            "admin_signature_sha256": sha256_bytes(args.admin_signature.read_bytes()),
            "expires_at": args.expires_at,
            "issued_at": args.issued_at,
            "request_sha256": request_hashes,
            "reviewer_registry_sha256": registry_sha256,
            "schema_version": 2,
        },
    )
    rows = []
    for path in sorted(candidate for candidate in args.output.rglob("*") if candidate.is_file()):
        rows.append(
            f"{sha256_bytes(path.read_bytes())}  {path.relative_to(args.output).as_posix()}"
        )
    manifest = "\n".join(rows) + "\n"
    (args.output / "REQUEST-MANIFEST.sha256").write_text(manifest)
    print(
        json.dumps(
            {
                "admin_id": policy["admin_id"],
                "output": str(args.output),
                "request_manifest_sha256": sha256_bytes(manifest.encode()),
                "request_sha256": request_hashes,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
