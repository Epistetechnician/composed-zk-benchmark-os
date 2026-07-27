#!/usr/bin/env python3
"""Fail-closed V24 artifact and configuration-lock validator."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve()
V24_PATH = HERE.with_name("v24.py")


def import_v24():
    spec = importlib.util.spec_from_file_location("astral_v24_validated", V24_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


V24 = import_v24()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_lock(root: Path) -> dict[str, object]:
    if any(
        (root / name).exists()
        for name in (
            "assessment-started.json",
            "assessment-features.npz",
            "assessment-results.json",
        )
    ):
        raise ValueError("assessment exists before lock validation")
    lock = json.loads((root / "configuration-lock.json").read_text())
    if not all(
        (
            lock["assessment_started_absent"],
            lock["assessment_features_absent"],
            lock["assessment_results_absent"],
        )
    ):
        raise ValueError("configuration lock ordering failure")
    for name, expected in lock["inputs"].items():
        if sha(root / name) != expected:
            raise ValueError(f"configuration lock digest mismatch: {name}")
    expected_sources = {
        "v24_sha256": sha(V24_PATH),
        "validator_sha256": sha(HERE),
        "v22_shared_core_sha256": sha(V24.V22_PATH),
        "v17_shared_core_sha256": sha(V24.V22.V17_PATH),
        "preregistration_sha256": sha(V24.PREREGISTRATION_PATH),
    }
    if lock["source_identity"] != expected_sources:
        raise ValueError("configuration lock source identity mismatch")
    return {
        "lock_valid": True,
        "configuration_lock_sha256": sha(root / "configuration-lock.json"),
    }


def load_raw(path: Path) -> dict[str, np.ndarray]:
    archive = np.load(path)
    return {name: archive[name] for name in archive.files}


def recompute_development(root: Path) -> None:
    raw = load_raw(root / "development-features.npz")
    fit_mask = raw["split"] == "fit"
    features, _ = V24.method_features(raw, fit_mask)
    models = V24.fit_models(features, raw["label"], fit_mask)
    retained = json.loads((root / "development-metrics.json").read_text())
    for split in ("development", "tune"):
        recomputed = V24.evaluate_split(raw, features, models, split)
        if recomputed != retained["metrics"][split]:
            raise ValueError(f"development metric mismatch: {split}")
        if V24.gate(recomputed) != retained["gates"][split]:
            raise ValueError(f"development gate mismatch: {split}")
    qualification = json.loads((root / "qualification.json").read_text())
    expected_qualified = all(
        retained["gates"][split]["passed"] for split in ("development", "tune")
    )
    integrity = json.loads((root / "integrity.json").read_text())
    expected_qualified = expected_qualified and all(
        (
            integrity["native_parity_max_abs_error"] == 0,
            integrity["repeat_logits_max_abs_error"] == 0,
            integrity["repeat_residual_max_abs_error"] == 0,
            integrity["zero_strength_max_abs_error"] == 0,
            integrity["activation_none_prompt_identity"],
            integrity["downstream_readout"],
            abs(integrity["direction_norm_min"] - 1.0) <= 1e-6,
            abs(integrity["direction_norm_max"] - 1.0) <= 1e-6,
        )
    )
    if qualification["qualified"] != expected_qualified:
        raise ValueError("qualification disposition mismatch")


def recompute_assessment(root: Path) -> None:
    raw = load_raw(root / "assessment-features.npz")
    transform, models = V24.load_lock(root / "readout-lock.npz")
    features, _ = V24.method_features(
        raw, np.ones(len(raw["label"]), dtype=bool), transform
    )
    probabilities = {
        method: V24.ridge_predict(models[method], features[method])
        for method in V24.METHODS
    }
    result_metrics = {
        method: V24.metrics(
            probabilities[method], raw["label"], raw["wrapper"]
        )
        for method in V24.METHODS
    }
    retained = json.loads((root / "assessment-results.json").read_text())
    if result_metrics != retained["metrics"]:
        raise ValueError("assessment metric mismatch")
    if V24.gate(result_metrics) != retained["gate"]:
        raise ValueError("assessment gate mismatch")
    for method in V24.METHODS:
        if not np.allclose(
            probabilities[method],
            np.asarray(retained["predictions"][method]),
            rtol=0,
            atol=1e-15,
        ):
            raise ValueError(f"assessment prediction mismatch: {method}")
    if V24.assessment_bootstrap(raw, probabilities) != retained["bootstrap"]:
        raise ValueError("assessment bootstrap mismatch")


def validate(root: Path) -> dict[str, object]:
    manifest = json.loads((root / "manifest.json").read_text())
    actual = {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if actual != set(manifest["files"]):
        raise ValueError("manifest census mismatch")
    for name, expected in manifest["files"].items():
        if sha(root / name) != expected:
            raise ValueError(f"manifest digest mismatch: {name}")
    corpus = json.loads((root / "corpus.json").read_text())
    if corpus != [V24.asdict(row) for row in V24.build_trials()]:
        raise ValueError("corpus regeneration mismatch")
    if json.loads((root / "fixed-configuration.json").read_text()) != V24.fixed_configuration():
        raise ValueError("fixed configuration mismatch")
    if json.loads((root / "environment-inventory.json").read_text()) != V24.environment_inventory():
        raise ValueError("runtime environment mismatch")
    if json.loads((root / "model-inventory.json").read_text()) != V24.V17.model_inventory(
        V24.V17.MODEL_PATH
    ):
        raise ValueError("model inventory mismatch")
    recompute_development(root)
    result = json.loads((root / "result.json").read_text())
    if result["independently_verified"] != "NotRun":
        raise ValueError("independent verification was fabricated")
    if result["classification"] == "NotRunAuthorDevelopmentPerturbationReadoutQualification":
        if (
            not result["assessment_unopened"]
            or (root / "assessment-features.npz").exists()
            or (root / "assessment-results.json").exists()
            or (root / "assessment-started.json").exists()
            or (root / "configuration-lock.json").exists()
            or (root / "readout-lock.npz").exists()
        ):
            raise ValueError("qualification stop opened assessment")
    else:
        if result["classification"] not in {
            "AuthorDevelopmentPerturbationReadoutObserved",
            "AuthorDevelopmentPerturbationReadoutNoCandidate",
        }:
            raise ValueError("invalid assessed classification")
        started = json.loads((root / "assessment-started.json").read_text())
        if (
            not started["one_shot"]
            or started["assessment_forward_budget"] != 48
            or started["configuration_lock_sha256"]
            != sha(root / "configuration-lock.json")
        ):
            raise ValueError("invalid assessment start record")
        recompute_assessment(root)
        lock = json.loads((root / "configuration-lock.json").read_text())
        if result["configuration_lock_sha256"] != sha(
            root / "configuration-lock.json"
        ):
            raise ValueError("result lock binding mismatch")
        if lock["source_identity"]["v24_sha256"] != sha(V24_PATH):
            raise ValueError("post-lock V24 source mutation")
        assessment = json.loads((root / "assessment-results.json").read_text())
        expected_observed = (
            assessment["gate"]["passed"]
            and assessment["bootstrap"]["lower_95"] > 0
        )
        expected_classification = (
            "AuthorDevelopmentPerturbationReadoutObserved"
            if expected_observed
            else "AuthorDevelopmentPerturbationReadoutNoCandidate"
        )
        if result["classification"] != expected_classification:
            raise ValueError("assessment classification mismatch")
    return {
        "valid": True,
        "classification": result["classification"],
        "manifest_sha256": sha(root / "manifest.json"),
        "independently_verified": result["independently_verified"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--lock-only", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            validate_lock(args.root.resolve())
            if args.lock_only
            else validate(args.root.resolve())
        )
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
