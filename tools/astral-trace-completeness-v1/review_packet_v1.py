"""Build a digest-bound, fail-closed reopening packet for V1.

State slice: astral-trace-completeness-native-instrument-v1.

The packet builder records unavailable facts explicitly and never emits a
signed ACCEPT.  A separate reviewer must bind a signer identity and receipt
after inspecting the frozen packet and any external custody manifest.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import platform
from pathlib import Path
from typing import Any

import custody_v1 as custody
import fixture_corpus_v1 as fixture_corpus
import protocol


SOURCE_FILES = (
    "protocol.py",
    "native_adapter.py",
    "mlx_adapter_v1.py",
    "custody_v1.py",
    "fixture_corpus_v1.py",
    "validate_trace_bundle_v1.py",
    "review_packet_v1.py",
    "review_receipt_v1.py",
)
FROZEN_IDENTITY_PATH = Path(__file__).resolve().parent / "frozen_identity_v1.json"


def _runtime_observation() -> dict[str, Any]:
    observed: dict[str, Any] = {"python": platform.python_version()}
    errors: list[str] = []
    for package, key in (("mlx", "mlx"), ("mlx-lm", "mlx_lm")):
        try:
            observed[key] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError as exc:
            errors.append(f"{key}:{type(exc).__name__}")
    for module_name, key in (
        ("mlx.core", "mlx_core_source_sha256"),
        ("mlx_lm.generate", "mlx_lm_generate_source_sha256"),
        ("mlx_lm.models.qwen3_5", "qwen3_5_source_sha256"),
        ("mlx_lm.models.qwen3_5_moe", "qwen3_5_moe_source_sha256"),
    ):
        try:
            module = importlib.import_module(module_name)
            source = getattr(module, "__file__", None)
            if not isinstance(source, str):
                raise OSError("module source path missing")
            observed[key] = protocol.sha256_file(Path(source).resolve())
        except (ImportError, OSError, ValueError) as exc:
            errors.append(f"{key}:{type(exc).__name__}")
    if errors:
        observed["errors"] = errors
    return observed


def _model_observation(model_root: Path, repository_root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"root": str(model_root.resolve()), "id": protocol.MODEL_ID}
    try:
        protocol.assert_external(model_root, repository_root)
        if model_root.name != protocol.MODEL_ID or not model_root.is_dir():
            raise protocol.ProtocolError("model root identity or directory check failed")
        files: list[dict[str, Any]] = []
        for path in sorted(model_root.rglob("*")):
            if path.is_symlink():
                raise protocol.ProtocolError(f"model symlink: {path}")
            if path.is_file():
                files.append({"path": path.relative_to(model_root).as_posix(), "bytes": path.stat().st_size, "sha256": protocol.sha256_file(path)})
        if not files:
            raise protocol.ProtocolError("model root is empty")
        manifest = {"model_root_basename": model_root.name, "files": files}
        result["manifest_sha256"] = protocol.canonical_digest(manifest)
        result["file_count"] = len(files)
    except (OSError, protocol.ProtocolError) as exc:
        result["error"] = f"{type(exc).__name__}:{exc}"
    return result


def _frozen_identity_check(
    frozen: dict[str, Any],
    *,
    source_digests: dict[str, str],
    model: dict[str, Any],
    runtime: dict[str, Any],
    fixture_manifest_sha256: str,
) -> list[str]:
    errors: list[str] = []
    if frozen.get("protocol") != protocol.PROTOCOL_ID or frozen.get("state_slice") != protocol.STATE_SLICE:
        errors.append("frozen_identity_protocol")
    if frozen.get("source_digests") != source_digests:
        errors.append("frozen_source_digests")
    if model.get("manifest_sha256") != frozen.get("model", {}).get("manifest_sha256"):
        errors.append("frozen_model_manifest")
    frozen_runtime = frozen.get("runtime", {})
    for key in ("python", "mlx", "mlx_lm", "mlx_core_source_sha256", "mlx_lm_generate_source_sha256", "qwen3_5_source_sha256", "qwen3_5_moe_source_sha256"):
        if runtime.get(key) != frozen_runtime.get(key):
            errors.append(f"frozen_runtime_{key}")
    if fixture_manifest_sha256 != frozen.get("fixture_manifest_sha256"):
        errors.append("frozen_fixture_manifest")
    return errors


def build_packet(repository_root: Path, *, model_root: Path = Path(protocol.MODEL_ROOT), custody_root: Path = Path(protocol.CUSTODY_ROOT)) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    source_paths = [Path(__file__).resolve().parent / name for name in SOURCE_FILES]
    source_digests = protocol.digest_source_manifest(source_paths, repository_root)
    operator_digest = protocol.canonical_digest({"id": protocol.OPERATOR_ID, "semantics": protocol.OPERATOR_SEMANTICS})
    model = _model_observation(model_root.resolve(), repository_root)
    runtime = _runtime_observation()
    fixture_manifest_sha256 = fixture_corpus.corpus_digest()
    try:
        frozen = protocol.strict_json(FROZEN_IDENTITY_PATH)
        frozen_errors = _frozen_identity_check(
            frozen,
            source_digests=source_digests,
            model=model,
            runtime=runtime,
            fixture_manifest_sha256=fixture_manifest_sha256,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        frozen = {}
        frozen_errors = [f"frozen_identity_load:{type(exc).__name__}:{exc}"]
    custody_receipt = custody.validate_custody_root(custody_root.resolve(), repository_root, require_existing=False)
    missing: list[str] = []
    if "manifest_sha256" not in model:
        missing.append("model_manifest_sha256")
    if runtime.get("errors") or any(runtime.get(key) != value for key, value in protocol.RUNTIME_CONTRACT.items()):
        missing.append("locked_runtime_and_runtime_source_digests")
    if not custody_receipt["valid"] or not custody_root.exists():
        missing.append("external_0700_custody_root_and_manifest")
    missing.extend(f"frozen_identity:{error}" for error in frozen_errors)
    missing.extend(("model_specific_module_registry_sha256", "independent_reviewer_identity", "signing_key_identity", "signed_ACCEPT_receipt"))
    prediction_lock_spec = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "corpus_id": protocol.FRESH_CORPUS_ID,
        "corpus_manifest_sha256": fixture_manifest_sha256,
        "model_manifest_sha256": model.get("manifest_sha256"),
        "runtime": runtime,
        "source_digests": source_digests,
        "operator_id": protocol.OPERATOR_ID,
        "operator_digest": operator_digest,
        "module_registry_sha256": None,
        "controls": list(protocol.CONTROLS),
        "falsifiers": list(protocol.FALSIFIERS),
        "qualification_gates": protocol.protocol_manifest()["qualification_gates"],
        "scientific_gates_sealed": protocol.protocol_manifest()["scientific_gates_sealed"],
    }
    prediction_lock_digest = protocol.canonical_digest(prediction_lock_spec)
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "parent_terminal_state": "astral-cumulative-evidence-synthesis-stop-v48",
        "authorization": {
            "user_authorized_contract_and_hermetic_fixture_scope_on": protocol.AUTHORIZATION_DATE,
            "model_execution_authorized": False,
            "assessment_authorized": False,
            "sae_or_transcoder_training_authorized": False,
        },
        "claim_ceiling": protocol.CLAIM_CEILING,
        "status": "BLOCKED_PENDING_SIGNED_ACCEPT" if missing else "READY_FOR_INDEPENDENT_REVIEW",
        "model": {**model, "architecture": protocol.MODEL_ARCHITECTURE},
        "runtime": {"locked": protocol.RUNTIME_CONTRACT, "observed": runtime},
        "frozen_identity": {
            "path": str(FROZEN_IDENTITY_PATH),
            "sha256": protocol.sha256_file(FROZEN_IDENTITY_PATH) if FROZEN_IDENTITY_PATH.is_file() else None,
            "errors": frozen_errors,
        },
        "source_digests": source_digests,
        "operator": {
            "operator_identity": "Shaan Patel",
            "operator_id": protocol.OPERATOR_ID,
            "operator_semantics": protocol.OPERATOR_SEMANTICS,
            "operator_digest": operator_digest,
            "operator_source_sha256": source_digests["native_adapter.py"],
            "assignment": "deterministic counterbalanced assignment by fixture_id, seed 20260830, fixed before effects",
            "timing": "intervention before downstream consumer; output after final consumer",
            "consistency": "declared donor state is the applied recipient replacement at the exact boundary key",
            "positivity": "each boundary has donor and no-op/control realizations",
            "interference": "isolated run_id and cache state; no cross-run mutable state",
        },
        "runner": {"id": protocol.RUNNER_ID, "source_sha256": source_digests["native_adapter.py"]},
        "validator": {"id": protocol.VALIDATOR_ID, "source_sha256": source_digests["validate_trace_bundle_v1.py"]},
        "module_registry": {"digest": None, "status": "not_bound_until_model_specific_native_registry_is_frozen"},
        "custody": {
            "root": str(custody_root.resolve()),
            "raw_root": protocol.RAW_CUSTODY_ROOT,
            "aggregate_root": protocol.AGGREGATE_CUSTODY_ROOT,
            "permissions": "0700 owner-only",
            "raw_retention_hours": protocol.RAW_RETENTION_HOURS,
            "retention_policy": protocol.RAW_RETENTION_POLICY,
            "validation": custody_receipt,
        },
        "fresh_corpus": {
            "id": protocol.FRESH_CORPUS_ID,
            "description": protocol.FRESH_CORPUS_DESCRIPTION,
            "generator": "fixture_corpus_v1.fixture_manifest",
            "generator_sha256": source_digests["fixture_corpus_v1.py"],
            "manifest_sha256": fixture_manifest_sha256,
            "fixture_count": fixture_corpus.FIXTURE_COUNT,
            "raw_corpus_sha256": None,
            "retention": protocol.FRESH_CORPUS_RETENTION,
        },
        "estimand": {
            "primary": "ATE of final-output logit-margin change under exact activation/path interchange versus locked no-op/control, clustered by fresh fixture family",
            "assignment": "fixed counterbalanced deterministic donor assignment independent of held-out outcome conditional on locked fixture and split",
            "timing": "treatment at declared boundary before downstream consumer; outcome at final output event in same run",
            "consistency": "observed outcome under assigned operator equals the corresponding potential outcome for that operator and boundary",
            "positivity": "each declared boundary has at least one donor, no-op, shuffled, constant, and matched-norm realization",
            "interference": "none across isolated run_ids; within-run cache/state transitions are part of the observed treatment path",
        },
        "thresholds": protocol.protocol_manifest()["qualification_gates"] | protocol.protocol_manifest()["scientific_gates_sealed"],
        "uncertainty_missingness_multiplicity_power": {
            "uncertainty": "two-sided 95 percent cluster bootstrap over document or fixture family, 10000 resamples, seed 20260830",
            "missingness": "no imputation; any missing required event invalidates instrument qualification; scientific attrition maximum 5 percent and reported",
            "multiplicity": "Holm correction across declared feature and graph-edge effects at alpha 0.05",
            "power": "target 0.90 at standardized effect 0.35 under ICC sensitivity 0.10 and 0.30",
            "repeats": protocol.REPEATS_REQUIRED,
            "attrition": protocol.MAX_ASSESSMENT_ATTRITION,
        },
        "controls": list(protocol.CONTROLS),
        "falsifiers": list(protocol.FALSIFIERS),
        "prediction_lock": {
            "required": True,
            "kind": "pre-effect-analysis-specification",
            "digest": prediction_lock_digest,
            "must_precede_assessment_effects": True,
            "assessment_effects_measured": False,
            "spec_sha256": prediction_lock_digest,
        },
        "independent_review": {
            "reviewer_identity": None,
            "signing_key_identity": None,
            "receipt_path": None,
            "receipt_status": "PENDING_SIGNED_ACCEPT",
        },
        "missing_required_fields": sorted(set(missing)),
        "execution_authorized": False,
        "assessment_opened": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--model-root", type=Path, default=Path(protocol.MODEL_ROOT))
    parser.add_argument("--custody-root", type=Path, default=Path(protocol.CUSTODY_ROOT))
    args = parser.parse_args(argv)
    packet = build_packet(args.repository_root, model_root=args.model_root, custody_root=args.custody_root)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0 if packet["status"] == "READY_FOR_INDEPENDENT_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
