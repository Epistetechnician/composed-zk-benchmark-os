#!/usr/bin/env python3
"""Build the content-addressed V24 admin and reviewer authorization kit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from review_auth import canonical_bytes, sha256_file, validate_admin_policy


HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
KIT_ID = "astral-v24-review-authorization-kit-v2"
MANIFEST_NAME = "KIT-MANIFEST.sha256"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def manifest_identity(root: Path, manifest_name: str, prefix: str) -> str:
    manifest = root / manifest_name
    if root.is_symlink() or not root.is_dir() or manifest.is_symlink() or not manifest.is_file():
        raise ValueError(f"{prefix} root or manifest is invalid")
    rows = {}
    for line in manifest.read_text().splitlines():
        expected, separator, relative = line.partition("  ")
        path = Path(relative)
        if (
            not separator
            or not SHA256.fullmatch(expected)
            or path.is_absolute()
            or ".." in path.parts
            or relative in rows
        ):
            raise ValueError(f"{prefix} manifest row is invalid")
        rows[relative] = expected
    if list(rows) != sorted(rows):
        raise ValueError(f"{prefix} manifest rows are not sorted")
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"{prefix} symlink is forbidden")
        if path.is_file() and path != manifest:
            actual.add(path.relative_to(root).as_posix())
    if actual != set(rows):
        raise ValueError(f"{prefix} manifest census mismatch")
    for relative, expected in rows.items():
        if sha256_file(root / relative) != expected:
            raise ValueError(f"{prefix} manifest digest mismatch: {relative}")
    identity = sha256_file(manifest)
    if root.name != f"{prefix}-{identity}":
        raise ValueError(f"{prefix} content-addressed name mismatch")
    return identity


def require_external(path: Path) -> None:
    try:
        path.relative_to(REPOSITORY)
    except ValueError:
        return
    raise ValueError("review-kit output must be outside the repository")


def render_readme(gate_spec: dict) -> str:
    return f"""# Astral V24 reviewer authorization kit V2

State slice: `astral-v24-independent-validation-release-v2`.

Admin: `shaanp` (`AdminCoordinator`, assignment authority only).

Release: `{gate_spec["release_identity"]}`.

Capsule: `{gate_spec["capsule_identity"]}`.

Claim ceiling: `{gate_spec["claim_ceiling"]}`.

Independent verification: `NotRun`. Confirmation: `NotAuthorized`. Stage 0C:
`Blocked`.

## Boundary

The admin may register two distinct reviewers and issue role-bound requests.
The admin may not sign reviewer decisions, waive findings, declare reviewer
independence, or promote any research state. An `agent_advisory` reviewer never
counts as independent review. Two declared `external_human` reviewers can only
produce a signed quorum candidate for external identity, conflict, and
scientific acceptance checks.

Keep every private key outside this kit, the capsule, the repository, and all
review evidence.

## 1. Register reviewers

Copy `templates/reviewer-registry.template.json` to a writable external
directory. Fill exactly one `artifact_reproducibility` reviewer and one
`scientific_validity` reviewer. They must have distinct signer identities and
distinct Ed25519 public keys. Set `reviewer_kind` to `agent_advisory` or
`external_human`; only the latter uses
`counts_toward_independent_verification: true`.

Confirm each submitted public-key fingerprint independently:

```sh
ssh-keygen -lf <reviewer-public-key-file> -E sha256
```

Canonicalize the completed registry. The command prints the registry SHA-256
needed in the next step:

```sh
python tools/canonicalize_json.py \\
  --input <completed-registry-draft.json> \\
  --output <reviewer-registry.json>
```

## 2. Admin authorization

The admin signs the canonical registry with one public key pinned by
`metadata/admin-policy.json`. This creates
`<reviewer-registry.json>.sig` without exporting the private key:

```sh
ssh-keygen -Y sign \\
  -f <admin-private-key> \\
  -n astral-v24-review-admin-v2 \\
  <reviewer-registry.json>
```

Issue fresh, expiring, role-bound requests into a new directory:

```sh
python tools/prepare_review.py \\
  --spec metadata/gate-spec.json \\
  --admin-policy metadata/admin-policy.json \\
  --registry <reviewer-registry.json> \\
  --admin-signature <reviewer-registry.json.sig> \\
  --expected-registry-sha256 <canonical-registry-sha256> \\
  --issued-at <UTC-ISO-8601> \\
  --expires-at <UTC-ISO-8601> \\
  --output <new-review-request-directory>
```

## 3. Reviewer execution

Each reviewer independently runs the separate content-addressed capsule in a
fresh absolute workspace:

```sh
python <capsule>/tools/run_capsule.py \\
  --workspace <new-absolute-reviewer-workspace>
```

Each reviewer fills only their role's generated decision template, inventories
the required evidence beneath one external evidence root, canonicalizes the
decision as `<role>.decision.json`, and signs it with their own registered key:

```sh
python tools/canonicalize_json.py \\
  --input <completed-role-decision-draft.json> \\
  --output <decisions>/<role>.decision.json

ssh-keygen -Y sign \\
  -f <reviewer-private-key> \\
  -n astral-v24-independent-review-v2 \\
  <decisions>/<role>.decision.json
```

The decision must retain the issued request and artifact bindings. A `Pass`
with `material_findings_unresolved: true` is rejected.

## 4. Fail-closed gate

After both signed decisions and every declared evidence file are present, run:

```sh
python tools/verify_review_gate.py \\
  --spec metadata/gate-spec.json \\
  --admin-policy metadata/admin-policy.json \\
  --registry <reviewer-registry.json> \\
  --admin-signature <reviewer-registry.json.sig> \\
  --requests <review-request-directory>/requests \\
  --decisions <decisions> \\
  --evidence-root <evidence-root> \\
  --verified-at <UTC-ISO-8601> \\
  --report <new-review-gate-report.json>
```

Possible successful outputs are
`AuthorizedAgentReviewAdvisoryCandidate` or
`SignedExternalReviewQuorumCandidate`. Neither output sets
`IndependentlyVerified`; external acceptance and independent implementation
replication remain separate gates.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capsule", required=True, type=Path)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--author-report", required=True, type=Path)
    parser.add_argument("--output-parent", required=True, type=Path)
    args = parser.parse_args()
    if git("status", "--porcelain"):
        raise SystemExit("review-kit builder worktree must be clean")
    capsule = args.capsule.resolve()
    release = args.release.resolve()
    capsule_identity = manifest_identity(
        capsule, "CAPSULE-MANIFEST.sha256", "astral-v24-independent-review-capsule-v2"
    )
    release_identity = manifest_identity(
        release, "RELEASE-MANIFEST.sha256", "astral-v24-validation-release-v2"
    )
    capsule_spec = json.loads((capsule / "metadata/capsule-spec.json").read_text())
    release_spec = json.loads((release / "metadata/release-spec.json").read_text())
    report = args.author_report.resolve()
    report_sha256 = sha256_file(report)
    if (
        capsule_spec["release_identity"] != release_identity
        or capsule_spec["author_report_sha256"] != report_sha256
        or capsule_spec["source_commit"] != release_spec["source_commit"]
    ):
        raise SystemExit("release, capsule, and report binding mismatch")
    policy = json.loads(HERE.with_name("admin-policy.json").read_text())
    validate_admin_policy(policy)
    policy_sha256 = hashlib.sha256(canonical_bytes(policy)).hexdigest()
    gate_spec = {
        "admin_policy_sha256": policy_sha256,
        "artifact_identity": release_spec["artifact_identity"],
        "author_report_sha256": report_sha256,
        "capsule_identity": capsule_identity,
        "claim_ceiling": release_spec["claim_ceiling"],
        "external_states": release_spec["external_states"],
        "release_identity": release_identity,
        "required_roles": ["artifact_reproducibility", "scientific_validity"],
        "required_scientific_sections": [
            "assessment_sealing",
            "claim_ceiling",
            "control_strength",
            "corpus_overlap_and_leakage",
            "preregistration_chronology",
            "statistics_and_uncertainty",
            "stopping_and_selection_rules",
        ],
        "review_namespace": "astral-v24-independent-review-v2",
        "schema_version": 2,
        "source_commit": release_spec["source_commit"],
        "source_tree": release_spec["source_tree"],
    }
    output_parent = args.output_parent.resolve()
    require_external(output_parent)
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".astral-v24-review-kit-v2-", dir=output_parent))
    try:
        for name in ("metadata", "templates", "tools"):
            (staging / name).mkdir()
        for name in (
            "canonicalize_json.py",
            "prepare_review.py",
            "review_auth.py",
            "verify_kit.py",
            "verify_review_gate.py",
        ):
            shutil.copy2(HERE.with_name(name), staging / "tools" / name)
        shutil.copy2(
            HERE.with_name("reviewer-registry.template.json"),
            staging / "templates/reviewer-registry.template.json",
        )
        (staging / "metadata/admin-policy.json").write_bytes(canonical_bytes(policy))
        (staging / "metadata/gate-spec.json").write_bytes(canonical_bytes(gate_spec))
        (staging / "README.md").write_text(render_readme(gate_spec))
        (staging / "ADMIN-SIGNING.txt").write_text(
            "ssh-keygen -Y sign -f <admin-private-key> "
            "-n astral-v24-review-admin-v2 reviewer-registry.json\n"
        )
        rows = []
        for path in sorted(candidate for candidate in staging.rglob("*") if candidate.is_file()):
            rows.append(f"{sha256_file(path)}  {path.relative_to(staging).as_posix()}")
        manifest = "\n".join(rows) + "\n"
        (staging / MANIFEST_NAME).write_text(manifest)
        identity = hashlib.sha256(manifest.encode()).hexdigest()
        destination = output_parent / f"{KIT_ID}-{identity}"
        if destination.exists():
            raise RuntimeError("content-addressed review kit already exists")
        os.replace(staging, destination)
        print(
            json.dumps(
                {
                    "admin_id": policy["admin_id"],
                    "kit": str(destination),
                    "kit_identity": identity,
                },
                sort_keys=True,
            )
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
