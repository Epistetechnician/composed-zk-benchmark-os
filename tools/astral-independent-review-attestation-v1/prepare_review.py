#!/usr/bin/env python3
"""Issue fresh role-bound Astral review requests from a pinned reviewer registry."""

from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path

from review_gate import (
    SHA256,
    build_request,
    canonical_bytes,
    decision_template,
    load_canonical,
    sha256_bytes,
    validate_registry,
    validate_spec,
    write_canonical,
)


HERE = Path(__file__).resolve()
SPEC_PATH = HERE.with_name("gate-spec.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--expected-registry-sha256", required=True)
    parser.add_argument("--issued-at", required=True)
    parser.add_argument("--expires-at", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--nonce",
        action="append",
        default=[],
        help="Optional deterministic role=64-lowercase-hex nonce",
    )
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("review request output already exists")
    spec = json.loads(SPEC_PATH.read_text())
    validate_spec(spec)
    registry, registry_sha256 = load_canonical(args.registry)
    if (
        not SHA256.fullmatch(args.expected_registry_sha256)
        or registry_sha256 != args.expected_registry_sha256
    ):
        raise SystemExit("reviewer registry digest mismatch")
    reviewers = validate_registry(registry, spec)
    supplied = {}
    for raw in args.nonce:
        role, separator, nonce = raw.partition("=")
        if not separator or role in supplied or not SHA256.fullmatch(nonce):
            raise SystemExit(f"invalid or duplicate nonce: {raw}")
        supplied[role] = nonce
    if set(supplied) - set(spec["required_roles"]):
        raise SystemExit("nonce supplied for unknown role")

    requests = args.output / "requests"
    templates = args.output / "decision-templates"
    metadata = args.output / "metadata"
    for directory in (requests, templates, metadata):
        directory.mkdir(parents=True)
    request_hashes = {}
    for role in spec["required_roles"]:
        request = build_request(
            spec,
            reviewers[role],
            supplied.get(role, secrets.token_hex(32)),
            args.issued_at,
            args.expires_at,
        )
        request_path = requests / f"{role}.request.json"
        request_sha256 = write_canonical(request_path, request)
        write_canonical(
            templates / f"{role}.decision.template.json",
            decision_template(request, request_sha256),
        )
        request_hashes[role] = request_sha256
    (metadata / "gate-spec.json").write_bytes(canonical_bytes(spec))
    (metadata / "reviewer-registry.json").write_bytes(canonical_bytes(registry))
    write_canonical(
        metadata / "request-record.json",
        {
            "expires_at": args.expires_at,
            "issued_at": args.issued_at,
            "request_sha256": request_hashes,
            "reviewer_registry_sha256": registry_sha256,
            "schema_version": 1,
        },
    )
    rows = []
    for path in sorted(candidate for candidate in args.output.rglob("*") if candidate.is_file()):
        relative = path.relative_to(args.output).as_posix()
        rows.append(f"{sha256_bytes(path.read_bytes())}  {relative}")
    manifest = "\n".join(rows) + "\n"
    (args.output / "REQUEST-MANIFEST.sha256").write_text(manifest)
    print(
        json.dumps(
            {
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
