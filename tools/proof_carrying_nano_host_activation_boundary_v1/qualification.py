"""One offline CPU qualification for the cached small-transformer adapter.

State slice: proof-carrying-nano-host-activation-boundary-v1.

The source snapshot is copied into a new owner-only external custody root.
The qualification loads only that copy with local-files-only settings, writes
raw activation bytes outside the repository, and stops before intervention or
causal assessment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from tools.proof_carrying_nano_jevlike_independent_validation_v1.activation import (
    validate_activation_bundle,
)

from .adapter import (
    BUNDLE_STATUS,
    CLAIM_CEILING,
    MODEL_ID,
    MODEL_SNAPSHOT,
    PROTOCOL_ID,
    SITE,
    STATE_SLICE,
    CachedSmallTransformerAdapter,
    canonical_bytes,
    canonical_digest,
    runtime_identity,
)
from .proof import ActivationLeanProofEngine
from .store import ActivationStore


CUSTODY_SCHEMA = "cached-small-transformer-checkpoint-custody-v1"
QUALIFICATION_SCHEMA = "cached-small-transformer-activation-cpu-qualification-v1"
QUALIFICATION_STATUS = "QualifiedReadOnlyHostActivationBoundary"
CHECKPOINT_KEYS = {
    "checkpoint_digest",
    "checkpoint_root",
    "device",
    "files",
    "manifest_digest",
    "model_id",
    "network_access",
    "schema",
    "state_slice",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _raw_activation_digest(raw: bytes, *, dtype: str, shape: list[int]) -> str:
    metadata = {"dtype": dtype, "shape": shape}
    return f"sha256:{hashlib.sha256(canonical_bytes(metadata) + b'\0' + raw).hexdigest()}"


def _external_directory(path: Path, repo_root: Path, label: str) -> Path:
    path = Path(path).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    repository = Path(repo_root).expanduser().resolve()
    resolved = path.resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the repository")
    current = path
    while True:
        if current.is_symlink():
            raise ValueError(f"{label} has a symlinked path component")
        if current.exists() and current.stat().st_mode & 0o002:
            raise ValueError(f"{label} has a world-writable path component")
        if current.parent == current:
            break
        current = current.parent
    return resolved


def _external_file(path: Path, repo_root: Path, label: str) -> Path:
    path = Path(path).expanduser()
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be an immutable absolute file")
    resolved = path.resolve()
    repository = Path(repo_root).expanduser().resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the repository")
    current = path
    while True:
        if current.is_symlink():
            raise ValueError(f"{label} has a symlinked path component")
        if current.exists() and current.stat().st_mode & 0o002:
            raise ValueError(f"{label} has a world-writable path component")
        if current.parent == current:
            break
        current = current.parent
    if path.stat().st_mode & 0o222:
        raise ValueError(f"{label} is mutable")
    return resolved


def _files(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            if path.is_symlink():
                raise ValueError("checkpoint contains a symlinked directory")
            continue
        if not path.is_file():
            raise ValueError("checkpoint contains a non-file entry")
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    if not entries:
        raise ValueError("checkpoint contains no files")
    return entries


def prepare_checkpoint_custody(
    source_checkpoint: Path,
    custody_root: Path,
    *,
    repo_root: Path,
    model_id: str = MODEL_ID,
) -> Path:
    """Copy a cached model snapshot into a fresh immutable external root."""

    source = Path(source_checkpoint).expanduser()
    if not source.is_absolute() or not source.is_dir() or source.is_symlink():
        raise ValueError("source checkpoint must be an absolute real directory")
    repository = Path(repo_root).expanduser().resolve()
    if source.resolve() == repository or repository in source.resolve().parents:
        raise ValueError("source checkpoint must be outside the repository")
    root = _external_directory(custody_root, repo_root, "checkpoint custody root")
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    checkpoint = root / "checkpoint"
    checkpoint.mkdir(mode=0o700)
    for source_path in sorted(source.rglob("*")):
        relative = source_path.relative_to(source)
        destination = checkpoint / relative
        if source_path.is_dir():
            if source_path.is_symlink():
                raise ValueError("source checkpoint contains a symlinked directory")
            destination.mkdir(mode=0o700)
        elif source_path.is_file():
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copyfile(source_path, destination)
            destination.chmod(0o400)
        else:
            raise ValueError("source checkpoint contains an unsupported entry")
    entries = _files(checkpoint)
    body = {
        "checkpoint_digest": canonical_digest({"files": entries, "model_id": model_id}),
        "checkpoint_root": str(checkpoint),
        "device": "cpu",
        "files": entries,
        "model_id": model_id,
        "network_access": False,
        "schema": CUSTODY_SCHEMA,
        "state_slice": STATE_SLICE,
    }
    manifest = {**body, "manifest_digest": canonical_digest(body)}
    manifest_path = root / "checkpoint-custody.json"
    manifest_path.write_bytes(canonical_bytes(manifest))
    manifest_path.chmod(0o400)
    return manifest_path


def validate_checkpoint_custody(path: Path, *, repo_root: Path) -> dict[str, Any]:
    """Validate immutable checkpoint files and return the normalized manifest."""

    manifest_path = _external_file(path, repo_root, "checkpoint custody manifest")
    raw = manifest_path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("checkpoint custody manifest is invalid JSON") from exc
    if not isinstance(value, dict) or set(value) != CHECKPOINT_KEYS:
        raise ValueError("checkpoint custody manifest schema is not closed")
    if raw != canonical_bytes(value):
        raise ValueError("checkpoint custody manifest is not canonical")
    if value["schema"] != CUSTODY_SCHEMA or value["state_slice"] != STATE_SLICE:
        raise ValueError("checkpoint custody identity is invalid")
    if value["device"] != "cpu" or value["network_access"] is not False:
        raise ValueError("checkpoint custody execution boundary is invalid")
    root = _external_directory(Path(value["checkpoint_root"]), repo_root, "custody checkpoint root")
    if not root.is_dir() or root.is_symlink():
        raise ValueError("custody checkpoint root is invalid")
    if root.stat().st_mode & 0o777 != 0o700 or manifest_path.parent.stat().st_mode & 0o777 != 0o700:
        raise ValueError("checkpoint custody is not owner-only")
    entries = _files(root)
    for path in root.rglob("*"):
        if path.is_dir() and path.stat().st_mode & 0o777 != 0o700:
            raise ValueError("checkpoint custody directory is not owner-only")
        if path.is_file() and path.stat().st_mode & 0o777 != 0o400:
            raise ValueError("checkpoint custody file is not immutable owner-only")
    if value["files"] != entries:
        raise ValueError("custody checkpoint file manifest mismatch")
    if value["checkpoint_digest"] != canonical_digest({"files": entries, "model_id": value["model_id"]}):
        raise ValueError("custody checkpoint digest mismatch")
    body = {key: item for key, item in value.items() if key != "manifest_digest"}
    if value["manifest_digest"] != canonical_digest(body):
        raise ValueError("checkpoint custody manifest digest mismatch")
    return {**value, "checkpoint_root": str(root)}


def _write_immutable(path: Path, value: Any) -> None:
    path.write_bytes(canonical_bytes(value))
    path.chmod(0o400)


def run_qualification(
    *,
    custody_manifest: Path,
    output_root: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Run and persist one offline CPU activation qualification."""

    custody = validate_checkpoint_custody(custody_manifest, repo_root=repo_root)
    output = _external_directory(output_root, repo_root, "qualification output root")
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    raw_root = output / "raw-output"
    raw_root.mkdir(mode=0o700)

    adapter = CachedSmallTransformerAdapter.from_cached_checkpoint(
        checkpoint_root=Path(custody["checkpoint_root"]),
        host_checkpoint_digest=custody["checkpoint_digest"],
        model_identity=f"{custody['model_id']}@{MODEL_SNAPSHOT}",
    )
    layer = 2
    input_ids, attention_mask = adapter.tokenize("Activation boundary qualification.")
    token_position = len(input_ids) - 1
    timestamp = "2026-09-17T12:00:00Z"
    first = adapter.capture_tokens(
        input_ids=input_ids,
        attention_mask=attention_mask,
        layer=layer,
        site=SITE,
        token_position=token_position,
        replay_seed=41,
        timestamp=timestamp,
    )
    repeat = adapter.replay(first.action)

    raw_path = raw_root / "activation.bin"
    raw_path.write_bytes(first.raw_activation)
    raw_path.chmod(0o400)
    raw_metadata_path = raw_root / "activation-metadata.json"
    _write_immutable(raw_metadata_path, first.raw_metadata)

    proof = ActivationLeanProofEngine().attempt(first.action)
    store_path = output / "store.sqlite3"
    with ActivationStore(store_path) as store:
        store.commit_action(first.action)
        store.commit_proof(proof)
        bundle = store.export_bundle(action_digest=first.action["action_digest"])
        integrity = store.validate_integrity()
    bundle_path = output / "bundle.json"
    _write_immutable(bundle_path, bundle)
    independent = validate_activation_bundle(bundle)
    host_parameter_digest = first.action["outputs"]
    checks = {
        "exact_replay": repeat.action == first.action and repeat.raw_activation == first.raw_activation,
        "hook_reachability": first.action["outputs"]["hook_reached"] is True,
        "activation_capture": bool(first.raw_activation)
        and _sha256_file(raw_path).startswith("sha256:")
        and _raw_activation_digest(
            first.raw_activation,
            dtype=first.raw_metadata["activation_dtype"],
            shape=first.raw_metadata["activation_shape"],
        )
        == first.action["outputs"]["activation_digest"],
        "parameter_digest_unchanged": host_parameter_digest["parameter_digest_before"] == host_parameter_digest["parameter_digest_after"],
        "no_host_mutation": host_parameter_digest["parameter_digest_before"] == host_parameter_digest["parameter_digest_after"],
        "checked_activation_proof": proof.status == "checked",
        "independent_bundle_validation": independent.valid,
    }
    if not all(checks.values()):
        raise RuntimeError(f"activation qualification failed: {checks}")
    runtime = runtime_identity()
    body = {
        "bundle_digest": bundle["bundle_digest"],
        "checkpoint_custody_manifest_digest": custody["manifest_digest"],
        "checkpoint_digest": custody["checkpoint_digest"],
        "checks": checks,
        "claim_ceiling": CLAIM_CEILING,
        "device": "cpu",
        "host_runtime_digest": first.action["host_runtime_digest"],
        "integrity": integrity,
        "layer": layer,
        "model_identity": adapter.model_identity,
        "network_access": False,
        "parameter_digest_after": first.action["outputs"]["parameter_digest_after"],
        "parameter_digest_before": first.action["outputs"]["parameter_digest_before"],
        "protocol_identity": PROTOCOL_ID,
        "proof_status": proof.status,
        "qualification_schema": QUALIFICATION_SCHEMA,
        "raw_activation_file_digest": _sha256_file(raw_path),
        "raw_output_root": str(raw_root),
        "state_slice": STATE_SLICE,
        "status": QUALIFICATION_STATUS,
        "token_position": token_position,
        "site": SITE,
        "causal_intervention_records": "SEALED_UNTIL_INDEPENDENT_REVIEW",
        "dashboard": "NOT_IMPLEMENTED",
        "swarm_coordination": "NOT_IMPLEMENTED",
        "runtime_identity": runtime,
        "action_digest": first.action["action_digest"],
    }
    report = {**body, "report_digest": canonical_digest(body)}
    _write_immutable(output / "qualification-report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--prepare-source-checkpoint", type=Path)
    parser.add_argument("--custody-root", type=Path)
    parser.add_argument("--custody-manifest", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    if args.prepare_source_checkpoint is not None:
        if args.custody_root is None:
            parser.error("--custody-root is required with --prepare-source-checkpoint")
        print(prepare_checkpoint_custody(args.prepare_source_checkpoint, args.custody_root, repo_root=args.repo_root))
        return 0
    if args.custody_manifest is None or args.output_root is None:
        parser.error("--custody-manifest and --output-root are required for qualification")
    report = run_qualification(
        custody_manifest=args.custody_manifest,
        output_root=args.output_root,
        repo_root=args.repo_root,
    )
    print(json.dumps({"status": report["status"], "report_digest": report["report_digest"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
