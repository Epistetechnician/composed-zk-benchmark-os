"""One bounded CPU qualification of the pinned Jevlike adapter boundary.

State slice: proof-carrying-nano-jevlike-independent-validation-v1.

The qualification uses a synthetic toy host only. It records aggregate and
exact captured probability evidence outside the repository and never attaches
to a real host model or performs an intervention.
"""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.proof_carrying_nano_interp_v1.protocol import canonical_digest
from tools.proof_carrying_nano_interp_v1.ranking import (
    HypothesisOption,
    HypothesisOptionSet,
    context_digest,
)
from tools.proof_carrying_nano_interp_v1.runtime import ToyHostSlice
from tools.proof_carrying_nano_interp_jevlike_adapter_v1.adapter import (
    PINNED_JEVLIKE_REVISION,
    JevlikeAdapterConfig,
    JevlikeHypothesisRankingNano,
    JevlikeOptionScorer,
    PinnedJevlikeRunner,
)
from tools.proof_carrying_nano_interp_jevlike_adapter_v1.proof import (
    JevlikeLeanProofEngine,
)
from tools.proof_carrying_nano_interp_jevlike_adapter_v1.store import (
    JevlikeHypothesisStore,
)
from tools.proof_carrying_nano_jevlike_independent_validation_v1.validator import (
    IndependentValidationReport,
    validate_bundle,
)


STATE_SLICE = "proof-carrying-nano-jevlike-independent-validation-v1"
CUSTODY_SCHEMA = "jevlike-adapter-checkpoint-custody-v1"
QUALIFICATION_SCHEMA = "jevlike-adapter-cpu-qualification-v1"
IDENTITY = "jevlike-tiny-pinned-v1"
CHECKPOINT_CUSTODY_KEYS = {
    "checkpoint_path",
    "checkpoint_sha256",
    "device",
    "manifest_sha256",
    "network_access",
    "schema",
    "state_slice",
    "upstream_revision",
}


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(value)).hexdigest()}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _external_file(path: Path, repo_root: Path, label: str) -> Path:
    path = Path(path).expanduser()
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be an immutable absolute file")
    resolved = path.resolve()
    repository = repo_root.expanduser().resolve()
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


def _external_directory(path: Path, repo_root: Path, label: str) -> Path:
    path = Path(path).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    repository = repo_root.expanduser().resolve()
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


def prepare_checkpoint_custody(
    source_checkpoint: Path,
    custody_root: Path,
    *,
    repo_root: Path,
    upstream_revision: str = PINNED_JEVLIKE_REVISION,
) -> Path:
    """Copy an external checkpoint into a new owner-only immutable custody root."""

    source = Path(source_checkpoint).expanduser()
    if not source.is_file() or source.is_symlink():
        raise ValueError("source checkpoint must be a regular file")
    source_resolved = source.resolve()
    repository = Path(repo_root).expanduser().resolve()
    if source_resolved == repository or repository in source_resolved.parents:
        raise ValueError("source checkpoint must be outside the repository")
    if upstream_revision != PINNED_JEVLIKE_REVISION:
        raise ValueError("custody revision is not the pinned Jevlike revision")
    root = _external_directory(custody_root, repo_root, "checkpoint custody root")
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    destination = root / "jevlike-checkpoint.pt"
    shutil.copyfile(source, destination)
    destination.chmod(0o400)
    body = {
        "checkpoint_path": str(destination),
        "checkpoint_sha256": _sha256_file(destination),
        "device": "cpu",
        "network_access": False,
        "schema": CUSTODY_SCHEMA,
        "state_slice": STATE_SLICE,
        "upstream_revision": upstream_revision,
    }
    manifest = {**body, "manifest_sha256": _digest(body)}
    manifest_path = root / "checkpoint-custody.json"
    manifest_path.write_bytes(_canonical(manifest))
    manifest_path.chmod(0o400)
    return manifest_path


def _load_custody_manifest(path: Path, *, repo_root: Path) -> dict[str, Any]:
    manifest_path = _external_file(path, repo_root, "checkpoint custody manifest")
    raw = manifest_path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("checkpoint custody manifest is invalid JSON") from error
    if not isinstance(value, dict) or set(value) != CHECKPOINT_CUSTODY_KEYS:
        raise ValueError("checkpoint custody manifest schema is not closed")
    if raw != _canonical(value):
        raise ValueError("checkpoint custody manifest is not canonical")
    if value["schema"] != CUSTODY_SCHEMA or value["state_slice"] != STATE_SLICE:
        raise ValueError("checkpoint custody identity mismatch")
    if value["upstream_revision"] != PINNED_JEVLIKE_REVISION or value["device"] != "cpu" or value["network_access"] is not False:
        raise ValueError("checkpoint custody execution boundary is invalid")
    body = {key: item for key, item in value.items() if key != "manifest_sha256"}
    if value["manifest_sha256"] != _digest(body):
        raise ValueError("checkpoint custody manifest digest mismatch")
    checkpoint = _external_file(Path(value["checkpoint_path"]), repo_root, "custody checkpoint")
    if value["checkpoint_sha256"] != _sha256_file(checkpoint):
        raise ValueError("custody checkpoint digest mismatch")
    return {**value, "checkpoint_path": str(checkpoint)}


def _exact_capture(action: Mapping[str, Any]) -> bool:
    inputs = action["inputs"]
    outputs = action["outputs"]
    raw = inputs["external_scores"]
    quantized = inputs["quantized_scores"]
    scale = inputs["quantization"]["scale"]
    rounding = {
        "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
        "ROUND_HALF_UP": ROUND_HALF_UP,
    }[inputs["quantization"]["rounding"]]
    try:
        expected = [
            int((Decimal(value) * scale).to_integral_value(rounding=rounding))
            for value in raw
        ]
    except (InvalidOperation, TypeError, ValueError):
        return False
    denominator = sum(expected)
    return (
        expected == quantized
        and denominator > 0
        and outputs["probabilities"]
        == [{"denominator": denominator, "numerator": value} for value in expected]
    )


def evaluate_checks(
    original: Mapping[str, Any],
    repeat: Mapping[str, Any],
    permuted: Mapping[str, Any],
    *,
    host_before: tuple[Any, ...],
    host_after: tuple[Any, ...],
    independent_valid: bool,
) -> dict[str, bool]:
    """Evaluate the five qualification invariants from captured action data."""

    original_scores = original["inputs"]["external_scores"]
    permuted_scores = permuted["inputs"]["external_scores"]
    return {
        "permutation_sensitivity": original_scores != permuted_scores,
        "repeatability": original == repeat,
        "exact_probability_capture": _exact_capture(original) and _exact_capture(permuted),
        "host_unchanged": host_before == host_after,
        "independent_bundle_validation": independent_valid,
    }


def _options(values: Sequence[str], identity: str, context: str) -> HypothesisOptionSet:
    kinds = ("feature", "circuit", "intervention")
    return HypothesisOptionSet.create(
        context_digest=context_digest(context),
        scorer_identity=identity,
        options=tuple(
            HypothesisOption(candidate_id=value, kind=kind)
            for value, kind in zip(values, kinds, strict=True)
        ),
    )


def run_qualification(
    *,
    custody_manifest: Path,
    upstream_root: Path,
    output_root: Path,
    repo_root: Path,
    runner: Any | None = None,
    proof_engine: JevlikeLeanProofEngine | None = None,
) -> dict[str, Any]:
    """Run one CPU-only adapter qualification and persist only external output."""

    custody = _load_custody_manifest(custody_manifest, repo_root=repo_root)
    output = _external_directory(output_root, repo_root, "qualification output root")
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    upstream = Path(upstream_root).expanduser()
    if not upstream.is_dir() or upstream.is_symlink():
        raise ValueError("upstream Jevlike checkout is not a real directory")

    import torch

    config = JevlikeAdapterConfig(
        upstream_revision=PINNED_JEVLIKE_REVISION,
        checkout_path=upstream,
        scorer_checkpoint_digest=custody["checkpoint_sha256"],
        scorer_checkpoint_path=Path(custody["checkpoint_path"]),
        encoder_identity="jevlike-tiny-byte-v1",
        runtime_identity=f"python-{platform.python_version()}|torch-{torch.__version__}",
        device="cpu",
        seed=17,
        context_tokens=512,
        option_tokens=32,
    )
    scorer = JevlikeOptionScorer(
        identity=IDENTITY,
        config=config,
        runner=runner or PinnedJevlikeRunner(),
    )
    nano = JevlikeHypothesisRankingNano(identity=IDENTITY, scorer=scorer)
    host = ToyHostSlice(checkpoint_id="jevlike-qualification-toy-host-v1")
    attachment = nano.attach(host, layer=3, site="residual")
    trace = host.capture(
        prompt="qualification prompt",
        activation=(3, 1),
        seed=17,
        layer=3,
        site="residual",
    )
    values = ("feature:alpha", "circuit:beta", "intervention:gamma")
    reversed_values = tuple(reversed(values))
    context = "qualification context: alpha beta gamma"
    original_options = _options(values, IDENTITY, context)
    permuted_options = _options(reversed_values, IDENTITY, context)
    before = host.snapshot()
    original = attachment.run(
        trace,
        original_options,
        context=context,
        timestamp="2026-09-16T12:00:00Z",
    )
    repeat = attachment.run(
        trace,
        original_options,
        context=context,
        timestamp="2026-09-16T12:00:00Z",
    )
    permuted = attachment.run(
        trace,
        permuted_options,
        context=context,
        timestamp="2026-09-16T12:00:00Z",
    )
    after = host.snapshot()
    engine = proof_engine or JevlikeLeanProofEngine()
    proof = engine.attempt(original)
    store_path = output / "store.sqlite3"
    with JevlikeHypothesisStore(store_path, proof_engine=engine) as store:
        store.commit_action(original)
        store.commit_proof(proof)
        bundle = store.export_bundle(action_digest=original.action_digest)
    independent: IndependentValidationReport | None = None
    independent_error: str | None = None
    try:
        independent = validate_bundle(bundle)
    except ValueError as error:
        independent_error = str(error)
    checks = evaluate_checks(
        original.to_dict(),
        repeat.to_dict(),
        permuted.to_dict(),
        host_before=before,
        host_after=after,
        independent_valid=independent is not None and independent.valid,
    )
    bundle_path = output / "bundle.json"
    bundle_path.write_bytes(_canonical(bundle))
    bundle_path.chmod(0o400)
    report = {
        "schema": QUALIFICATION_SCHEMA,
        "state_slice": STATE_SLICE,
        "status": "QualifiedAdapterBoundary" if all(checks.values()) else "QualificationFailed",
        "claim_ceiling": "LocalExternalJevlikeQuantizedHypothesisRankingOnly",
        "upstream_revision": PINNED_JEVLIKE_REVISION,
        "checkpoint_custody_manifest_sha256": custody["manifest_sha256"],
        "checkpoint_sha256": custody["checkpoint_sha256"],
        "config_digest": config.config_digest,
        "runtime_identity": config.runtime_identity,
        "checks": checks,
        "bundle_digest": bundle["bundle_digest"],
        "independent_validation": {
            "valid": independent is not None and independent.valid,
            "checked_proofs": independent.checked_proofs if independent else 0,
            "error": independent_error,
        },
        "captured": {
            "original_external_scores": original.inputs["external_scores"],
            "original_quantized_scores": original.inputs["quantized_scores"],
            "original_probabilities": original.outputs["probabilities"],
            "permuted_external_scores": permuted.inputs["external_scores"],
            "permuted_quantized_scores": permuted.inputs["quantized_scores"],
            "permuted_probabilities": permuted.outputs["probabilities"],
        },
        "execution_policy": {
            "device": "cpu",
            "network_access": False,
            "host_model_execution": False,
            "real_host_activation_integration": False,
            "causal_intervention": False,
            "dashboard": False,
            "swarm_coordination": False,
            "hypothesis_only": True,
        },
    }
    report["report_sha256"] = _digest(report)
    report_path = output / "qualification-report.json"
    report_path.write_bytes(_canonical(report))
    report_path.chmod(0o400)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--prepare-source-checkpoint", type=Path)
    parser.add_argument("--custody-root", type=Path)
    parser.add_argument("--custody-manifest", type=Path)
    parser.add_argument("--upstream-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    if args.prepare_source_checkpoint is not None:
        if args.custody_root is None:
            parser.error("--custody-root is required with --prepare-source-checkpoint")
        manifest = prepare_checkpoint_custody(
            args.prepare_source_checkpoint,
            args.custody_root,
            repo_root=args.repo_root,
        )
        print(json.dumps({"custody_manifest": str(manifest)}, sort_keys=True))
        return 0
    if args.custody_manifest is None or args.upstream_root is None or args.output_root is None:
        parser.error("--custody-manifest, --upstream-root, and --output-root are required")
    report = run_qualification(
        custody_manifest=args.custody_manifest,
        upstream_root=args.upstream_root,
        output_root=args.output_root,
        repo_root=args.repo_root,
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "QualifiedAdapterBoundary" else 1


if __name__ == "__main__":
    raise SystemExit(main())
