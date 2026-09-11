#!/usr/bin/env bash
set -euo pipefail

# State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v9.
# Review-handoff utility only. It does not run a model, contact a provider,
# include custody contents, or create/sign a review receipt.

usage() {
    printf '%s\n' \
        'Usage: prepare_gemma3_fineweb_edu_replication_h100_v9_review_handoff.sh \' \
        '  --bundle /absolute/path/to/review-bundle.tar.gz \' \
        '  --output-dir /absolute/external/path/to/handoff-dir'
}

bundle=''
output_dir=''
while (($# > 0)); do
    case "$1" in
        --bundle)
            (($# >= 2)) || { usage >&2; exit 2; }
            bundle=$2
            shift 2
            ;;
        --output-dir)
            (($# >= 2)) || { usage >&2; exit 2; }
            output_dir=$2
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            exit 2
            ;;
    esac
done

[[ -n "$bundle" && -n "$output_dir" ]] || { usage >&2; exit 2; }
[[ "$bundle" = /* && "$output_dir" = /* ]] || {
    printf '%s\n' 'bundle and output-dir must be absolute paths' >&2
    exit 2
}
[[ -f "$bundle" && ! -L "$bundle" ]] || {
    printf '%s\n' 'bundle must be an existing regular non-symlink file' >&2
    exit 1
}
[[ ! -e "$output_dir" ]] || {
    printf '%s\n' 'refusing to overwrite an existing output directory' >&2
    exit 1
}

repo_root=$(cd "$(dirname "$0")/.." && pwd -P)
resolved_output=$(python3 -B - "$output_dir" "$repo_root" <<'PY'
from pathlib import Path
import sys

output = Path(sys.argv[1]).expanduser()
repo = Path(sys.argv[2]).resolve()
resolved = output.resolve()
if resolved == repo or repo in resolved.parents:
    raise SystemExit("output-dir must be outside the repository")
if resolved.parts[1:2] != ("Volumes",):
    raise SystemExit("output-dir must be below an external mounted volume")
print(resolved)
PY
)

mkdir -p "$resolved_output"
python3 -B - "$bundle" "$resolved_output" <<'PY'
import hashlib
import json
import shutil
import sys
import tarfile
from pathlib import Path

bundle = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
expected = [
    "docs/research/continual-learning/320-gemma3-fineweb-edu-replication-h100-v9-protocol.md",
    "docs/research/continual-learning/321-gemma3-fineweb-edu-replication-h100-v9-review-packet.md",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_preflight.py",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v9_preflight.py",
    "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/Dockerfile",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/requirements.lock",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/runtime-lock.json",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/run_h100_v9.sh",
    "AGENTS.md",
    "docs/research/continual-learning/322-gemma3-fineweb-edu-replication-h100-v9-implementation-manifest.json",
]

with tarfile.open(bundle, "r:gz") as archive:
    members = archive.getmembers()
    if any(member.issym() or member.islnk() or not member.isfile() for member in members):
        raise SystemExit("archive contains a non-regular member")
    actual = [member.name for member in members]
    if actual != expected:
        raise SystemExit(f"archive inventory mismatch: {actual!r}")
    file_sha256 = {
        name: hashlib.sha256(archive.extractfile(name).read()).hexdigest()
        for name in expected
    }
    manifest = json.loads(archive.extractfile(expected[-1]).read().decode("utf-8"))
    implementation_self_digest = manifest.get("manifest_sha256")

shutil.copy2(bundle, output / bundle.name)
bundle_sha256 = hashlib.sha256(bundle.read_bytes()).hexdigest()
(output / (bundle.name + ".sha256")).write_text(
    f"{bundle_sha256}  {bundle.name}\n", encoding="utf-8"
)
inventory = {
    "schema": "gemma3-fineweb-edu-replication-h100-v9-review-handoff",
    "state_slice": "continual-learning-gemma3-fineweb-edu-replication-h100-v9",
    "effects_run": False,
    "contains_model_weights": False,
    "contains_datasets": False,
    "contains_credentials": False,
    "contains_signing_keys": False,
    "bundle_sha256": bundle_sha256,
    "implementation_manifest_self_digest": implementation_self_digest,
    "regular_file_inventory": expected,
    "file_sha256": file_sha256,
}
(output / "bundle-inventory.json").write_text(
    json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
)
(output / "reviewer-instructions.md").write_text(
    """# V9 independent review handoff

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v9`.

Review only the attached archive and exact inventory. Do not request or receive
model weights, datasets, raw custody contents, credentials, provider secrets,
or any private signing key. Do not run model effects, training, provider jobs,
or spend.

Recompute the archive SHA-256, every member SHA-256, and the implementation
manifest self-digest from archive bytes. Inspect fresh-cohort and V8 exclusion
boundaries, exact Decimal budget arithmetic, runtime/model freeze,
offline/network boundary, recurrence controls, uncertainty, assessment-ledger
lifecycle, validator fail-closed behavior, publication ordering, and terminal
V1/V2 identities.

Return a signed Ed25519 receipt from an independently controlled reviewer key.
Bind the exact archive digest, all 14 file digests, implementation-manifest
self-digest, protocol and packet digests, all seven findings, reviewer
identity, UTC timestamp, and `effects_run: false`. A rejection or unsigned
report is not an execution gate.
""",
    encoding="utf-8",
)
print(json.dumps({
    "handoff_dir": str(output),
    "bundle": str(output / bundle.name),
    "bundle_sha256": bundle_sha256,
    "implementation_manifest_self_digest": implementation_self_digest,
    "regular_file_count": len(expected),
    "status": "PASS",
}, indent=2))
PY
