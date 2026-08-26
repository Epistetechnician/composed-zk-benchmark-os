"""Hermetic V1 custody and claim-boundary tests.

State slice: astral-neural-chameleon-replication-v1-preflight.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOCOL = load_module("neural_chameleon_protocol_v1", "protocol_v1.py")
VALIDATOR = load_module("neural_chameleon_validator_v1", "validator_v1.py")


def _entry(root: Path, role: str, filename: str, kind: str, content: bytes) -> dict:
    path = root / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {
        "path": filename,
        "byte_len": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _manifest(root: Path) -> dict:
    entries = []
    for role, kind in PROTOCOL.ROLE_KINDS.items():
        filename = f"{role}.bin"
        files = [_entry(root, role, filename, kind, role.encode("utf-8"))]
        entries.append(
            {
                "role": role,
                "files": files,
                "role_sha256": PROTOCOL._role_digest(files),
                "artifact_kind": kind,
            }
        )
    source_commit = "a" * 40
    model_provenance = {
        role: {
            "model_family": "test-family",
            "model_revision": f"{role}-revision",
            "architecture": "causal-decoder",
            "dimensions": {
                "hidden_size": 64,
                "num_layers": 16,
                "num_attention_heads": 8,
                "num_kv_heads": 8,
            },
            "tokenizer_files": [f"{role}.bin"],
            "tokenization_expectations": ["last-token-stable"],
            "source_repository": "https://example.invalid/source",
            "source_commit": source_commit,
        }
        for role in (
            "chameleon_checkpoint",
            "precursor_checkpoint",
            "activation_oracle_checkpoint",
        )
    }
    panel_counts = {"fit": 4, "tune": 2, "assessment": 3}
    corpus_provenance = {
        role: {
            "lineage": f"external-{role}-source",
            "panel_counts": panel_counts.copy(),
            "template_ids": [f"{role}-template-1"],
            "split_sha256": "b" * 64,
            "concept_registry_sha256": "c" * 64,
            "source_study_reuse": "ExplicitSourceInputsOnly",
        }
        for role in ("oracle_corpus_bundle", "mechanistic_corpus_bundle")
    }
    oracle_arm = {
        "actor_role": "chameleon_checkpoint",
        "oracle_role": "activation_oracle_checkpoint",
        "corpus_role": "oracle_corpus_bundle",
        "runtime_role": "runtime_manifest",
        "primary_endpoint": "activation_oracle_robustness_at_fixed_fpr",
        "formula": "TPR_at_fixed_FPR = triggered_true_positive / triggered_positive at clean_FPR <= fixed_FPR",
        "activation_layer": 12,
        "activation_position": "last_token",
        "trigger_template": "trigger-template-v1",
        "score_rule": "locked_binary_activation_oracle_score",
        "metrics": PROTOCOL.ORACLE_METRICS,
        "controls": PROTOCOL.ORACLE_CONTROLS,
        "fit_rows": 4,
        "tune_rows": 2,
        "assessment_rows": 3,
        "fixed_fpr": 0.05,
        "prediction_lock_required": True,
    }
    mechanistic_arm = {
        "chameleon_role": "chameleon_checkpoint",
        "precursor_role": "precursor_checkpoint",
        "monitor_role": "linear_monitor_bundle",
        "corpus_role": "mechanistic_corpus_bundle",
        "runtime_role": "runtime_manifest",
        "primary_endpoint": "direct_held_out_intervention_effect",
        "formula": "effect = metric(intervened) - metric(matched_baseline)",
        "monitor_layer": 12,
        "monitor_definition": "linear-last-token-residual-monitor",
        "transplant_sites": ["residual:12", "mlp:12"],
        "head_set": ["L12H0", "L12H1"],
        "qkv_factorial": PROTOCOL.QKV_FACTORIAL,
        "hybridization_slices": PROTOCOL.HYBRIDIZATION_SLICES,
        "score_rule": "locked_monitor_score",
        "metrics": PROTOCOL.MECHANISTIC_METRICS,
        "controls": PROTOCOL.MECHANISTIC_CONTROLS,
        "fit_rows": 4,
        "tune_rows": 2,
        "assessment_rows": 3,
        "bootstrap_unit": "prompt_family",
        "prediction_lock_required": True,
    }
    return {
        "protocol": PROTOCOL.PROTOCOL_ID,
        "state_slice": PROTOCOL.STATE_SLICE,
        "claim_ceiling": PROTOCOL.CLAIM_CEILING,
        "schema_version": PROTOCOL.MANIFEST_SCHEMA_VERSION,
        "artifact_entries": entries,
        "runtime_capabilities": list(PROTOCOL.REQUIRED_CAPABILITIES),
        "retention": {
            "artifact_root_external": True,
            "artifact_root_immutable": True,
            "raw_payloads_external_only": True,
            "raw_payloads_in_result": False,
            "network_access": False,
            "model_training": False,
            "assessment_opened": False,
        },
        "arms": {"activation_oracle": oracle_arm, "mechanistic": mechanistic_arm},
        "execution_contract": {
            "order": PROTOCOL.EXECUTION_ORDER,
            "prediction_lock_required": True,
            "arm_independence": {
                "shared_roles": ["runtime_manifest"],
                "forbid_cross_arm_selection": True,
                "forbid_cross_arm_evidence": True,
            },
            "activation_oracle": {
                "formula": oracle_arm["formula"],
                "metrics": oracle_arm["metrics"],
                "controls": oracle_arm["controls"],
                "fit_rows": oracle_arm["fit_rows"],
                "tune_rows": oracle_arm["tune_rows"],
                "assessment_rows": oracle_arm["assessment_rows"],
                "assessment_requires_prediction_lock": True,
                "fixed_fpr": oracle_arm["fixed_fpr"],
            },
            "mechanistic": {
                "formula": mechanistic_arm["formula"],
                "metrics": mechanistic_arm["metrics"],
                "controls": mechanistic_arm["controls"],
                "fit_rows": mechanistic_arm["fit_rows"],
                "tune_rows": mechanistic_arm["tune_rows"],
                "assessment_rows": mechanistic_arm["assessment_rows"],
                "assessment_requires_prediction_lock": True,
                "bootstrap_unit": mechanistic_arm["bootstrap_unit"],
                "qkv_combinations": PROTOCOL.QKV_FACTORIAL,
                "transplant_directions": ["ordinary_to_triggered", "triggered_to_ordinary"],
                "hybridization_slices": PROTOCOL.HYBRIDIZATION_SLICES,
            },
        },
        "provenance": {
            "models": model_provenance,
            "monitor": {
                "source_repository": "https://example.invalid/monitor",
                "source_commit": source_commit,
                "trained_on_role": "mechanistic_corpus_bundle",
                "layer": 12,
                "pooling": "last_token",
                "threshold": 0.5,
                "calibration": "fit-only-threshold",
                "score_definition": "linear-logit-score",
            },
            "corpora": corpus_provenance,
            "runtime": {
                "python": "3.14",
                "libraries": {"mlx": "test", "numpy": "test"},
                "source_commit": source_commit,
            },
        },
        "freshness": {
            "disallow_protocols": PROTOCOL.DISALLOWED_PROTOCOLS,
            "disallow_concepts": True,
            "concept_registry_sha256": "c" * 64,
            "disallow_predictions": True,
            "disallow_assessment_rows": True,
            "disallow_artifacts": True,
            "source_study_reuse": "ExplicitSourceInputsOnly",
            "astral_derived_selection": False,
        },
    }


class ProtocolV1Tests(unittest.TestCase):
    def test_missing_root_stops_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = PROTOCOL.inspect(Path(directory).resolve() / "missing")
        self.assertEqual(result["classification"], PROTOCOL.MISSING_ROOT)
        self.assertFalse(result["model_execution"])
        self.assertFalse(result["assessment_opened"])

    def test_missing_manifest_stops_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            result = PROTOCOL.inspect(root)
            validator_errors = VALIDATOR.validate(result, root)
        self.assertEqual(result["classification"], PROTOCOL.MISSING_REQUIRED)
        self.assertEqual(result["reasons"], ["artifact_manifest_missing"])
        self.assertEqual(validator_errors, [])

    def test_valid_complete_manifest_is_ready_for_instrument_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "artifact-manifest.json").write_text(json.dumps(_manifest(root)), encoding="utf-8")
            result = PROTOCOL.inspect(root)
            validator_errors = VALIDATOR.validate(result, root)
        self.assertEqual(result["classification"], PROTOCOL.READY)
        self.assertEqual(result["verified_artifact_count"], len(PROTOCOL.REQUIRED_ROLES))
        self.assertTrue(VALIDATOR._is_digest(result["artifact_manifest_sha256"]))
        self.assertEqual(validator_errors, [])

    def test_sharded_role_file_set_is_supported_and_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            role = "chameleon_checkpoint"
            extra = _entry(root, role, "chameleon_checkpoint.index.json", "checkpoint", b"index")
            manifest["artifact_entries"][0]["files"].append(extra)
            manifest["artifact_entries"][0]["role_sha256"] = PROTOCOL._role_digest(
                manifest["artifact_entries"][0]["files"]
            )
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
        self.assertEqual(result["classification"], PROTOCOL.READY)
        self.assertEqual(result["verified_artifact_count"], len(PROTOCOL.REQUIRED_ROLES))

    def test_duplicate_json_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "artifact-manifest.json").write_text(
                '{"protocol":"x", "protocol":"y"}', encoding="utf-8"
            )
            result = PROTOCOL.inspect(root)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertEqual(result["reasons"], ["artifact_manifest_invalid:ValueError"])

    def test_digest_or_length_tampering_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            manifest["artifact_entries"][0]["files"][0]["sha256"] = "0" * 64
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertIn("artifact_0_file_0_digest_mismatch", result["reasons"])

    def test_path_escape_and_manifest_census_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            manifest["artifact_entries"][0]["files"][0]["path"] = "../outside.bin"
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertIn("artifact_0_file_0_unsafe_path", result["reasons"])

    def test_control_character_path_fails_closed_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            manifest["artifact_entries"][0]["files"][0]["path"] = "bad\x00path"
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertIn("artifact_0_file_0_unsafe_path", result["reasons"])

    def test_noncanonical_manifest_paths_fail_closed(self) -> None:
        for unsafe_path in ("C:artifact.bin", "nested//artifact.bin"):
            with self.subTest(unsafe_path=unsafe_path), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                manifest = _manifest(root)
                manifest["artifact_entries"][0]["files"][0]["path"] = unsafe_path
                (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                result = PROTOCOL.inspect(root)
            self.assertEqual(result["classification"], PROTOCOL.INVALID)
            self.assertIn("artifact_0_file_0_unsafe_path", result["reasons"])

    def test_unlisted_file_fails_manifest_census(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            (root / "unlisted.bin").write_bytes(b"not declared")
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertIn("artifact_manifest_census_mismatch", result["reasons"])

    def test_nested_manifest_is_census_material(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            nested = root / "nested"
            nested.mkdir()
            (nested / "artifact-manifest.json").write_text("{}", encoding="utf-8")
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertIn("artifact_manifest_census_mismatch", result["reasons"])

    def test_unlisted_symlink_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            target = root / "target.bin"
            target.write_bytes(b"not declared")
            os.symlink(target, root / "unlisted.bin")
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertIn("symlinked_path:unlisted.bin", result["reasons"])

    def test_symlinked_root_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory).resolve()
            target = parent / "target"
            target.mkdir()
            link = parent / "link"
            os.symlink(target, link, target_is_directory=True)
            result = PROTOCOL.inspect(link)
        self.assertEqual(result["classification"], PROTOCOL.MISSING_ROOT)
        self.assertIn("artifact_root_missing_or_not_directory", result["reasons"])

    def test_artifact_root_inside_repository_fails_closed(self) -> None:
        result = PROTOCOL.inspect(HERE)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertEqual(result["reasons"], ["artifact_root_inside_repository"])

    def test_symlinked_ancestor_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory).resolve()
            target = parent / "target"
            target.mkdir()
            real_root = target / "artifacts"
            real_root.mkdir()
            (real_root / "artifact-manifest.json").write_text("{}", encoding="utf-8")
            link = parent / "link"
            os.symlink(target, link, target_is_directory=True)
            result = PROTOCOL.inspect(link / "artifacts")
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertTrue(any(reason.startswith("artifact_root_ancestor_symlink:") for reason in result["reasons"]))

    def test_retention_escalation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            manifest["retention"]["raw_payloads_in_result"] = True
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertIn("retention_raw_payloads_in_result_mismatch", result["reasons"])

    def test_runtime_capability_escalation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            manifest["runtime_capabilities"] = ["network_access"]
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertIn("runtime_capabilities_mismatch", result["reasons"])

    def test_independent_validator_rejects_boolean_schema_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            manifest["schema_version"] = True
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
            errors = VALIDATOR.validate(result, root)
        self.assertEqual(result["classification"], PROTOCOL.INVALID)
        self.assertIn("artifact_manifest_identity_mismatch", errors)

    def test_independent_validator_rejects_forged_ready_nested_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            manifest["arms"]["activation_oracle"]["primary_endpoint"] = "forged-endpoint"
            manifest["freshness"]["disallow_concepts"] = False
            manifest["provenance"]["runtime"]["libraries"]["mlx"] = False
            manifest["execution_contract"]["order"] = []
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
            result["classification"] = VALIDATOR.READY
            result["reasons"] = []
            errors = VALIDATOR.validate(result, root)
        self.assertIn("artifact_manifest_activation_oracle_primary_endpoint_mismatch", errors)
        self.assertIn("artifact_manifest_freshness_disallow_concepts_mismatch", errors)
        self.assertIn("artifact_manifest_provenance_runtime_libraries_invalid", errors)
        self.assertIn("artifact_manifest_execution_contract_order_mismatch", errors)

    def test_independent_validator_rejects_forged_ready_duplicate_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            manifest["artifact_entries"].append(json.loads(json.dumps(manifest["artifact_entries"][0])))
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
            result["classification"] = VALIDATOR.READY
            result["reasons"] = []
            result["verified_artifact_count"] = len(VALIDATOR.REQUIRED_ROLES)
            errors = VALIDATOR.validate(result, root)
        self.assertIn("artifact_manifest_entries_count_mismatch", errors)
        self.assertIn("artifact_7_revalidation_duplicate_role", errors)
        self.assertIn("artifact_7_file_0_revalidation_duplicate_path", errors)
        self.assertIn("artifact_manifest_revalidation_roles_mismatch", errors)

    def test_independent_validator_rejects_non_string_role_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = _manifest(root)
            manifest["artifact_entries"][0]["role"] = []
            (root / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = PROTOCOL.inspect(root)
            errors = VALIDATOR.validate(result, root)
        self.assertIn("artifact_0_revalidation_role_invalid", errors)

    def test_deep_unknown_result_payload_fails_closed_without_recursion_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "missing"
            result = PROTOCOL.inspect(root)
            nested: object = "leaf"
            for _ in range(1_100):
                nested = [nested]
            result["unexpected"] = nested
            errors = VALIDATOR.validate(result, root)
        self.assertIn("result_unknown_field:unexpected", errors)

    def test_independent_validator_rejects_boundary_escalation(self) -> None:
        result = {
            "protocol": VALIDATOR.PROTOCOL_ID,
            "state_slice": VALIDATOR.STATE_SLICE,
            "claim_ceiling": "Stage0C",
            "required_roles": VALIDATOR.REQUIRED_ROLES,
            "artifact_roles": [],
            "verified_artifact_count": 0,
            "model_execution": True,
            "model_training": False,
            "network_access": False,
            "assessment_opened": False,
            "raw_payloads_retained": False,
            "classification": VALIDATOR.MISSING_REQUIRED,
            "reasons": ["artifact_manifest_missing"],
        }
        errors = VALIDATOR.validate(result)
        self.assertIn("claim_ceiling_mismatch", errors)
        self.assertIn("model_execution_mismatch", errors)

    def test_independent_validator_rejects_forbidden_payload_field(self) -> None:
        result = {
            "protocol": VALIDATOR.PROTOCOL_ID,
            "state_slice": VALIDATOR.STATE_SLICE,
            "claim_ceiling": VALIDATOR.CLAIM_CEILING,
            "required_roles": VALIDATOR.REQUIRED_ROLES,
            "artifact_roles": [],
            "verified_artifact_count": 0,
            "model_execution": False,
            "model_training": False,
            "network_access": False,
            "assessment_opened": False,
            "raw_payloads_retained": False,
            "classification": VALIDATOR.MISSING_REQUIRED,
            "reasons": ["artifact_manifest_missing"],
            "raw_activations": [1, 2, 3],
        }
        self.assertIn("forbidden_payload_field", VALIDATOR.validate(result))

    def test_independent_validator_rejects_unknown_result_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "artifact-manifest.json").write_text(json.dumps(_manifest(root)), encoding="utf-8")
            result = PROTOCOL.inspect(root)
            result["unbounded_claim"] = True
            errors = VALIDATOR.validate(result, root)
        self.assertIn("result_unknown_field:unbounded_claim", errors)

    def test_independent_validator_rejects_forged_ready_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "artifact-manifest.json").write_text(json.dumps(_manifest(root)), encoding="utf-8")
            result = PROTOCOL.inspect(root)
            (root / "artifact-manifest.json").unlink()
            errors = VALIDATOR.validate(result, root)
        self.assertIn("artifact_manifest_presence_mismatch", errors)
        self.assertIn("artifact_manifest_revalidation_missing", errors)

    def test_independent_validator_binds_missing_root_to_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "missing"
            result = PROTOCOL.inspect(root)
            result["artifact_manifest_present"] = True
            result["artifact_manifest_sha256"] = "0" * 64
            result["artifact_roles"] = ["chameleon_checkpoint"]
            result["verified_artifact_count"] = 1
            errors = VALIDATOR.validate(result, root)
        self.assertIn("missing_root_manifest_presence_mismatch", errors)
        self.assertIn("missing_root_manifest_digest_mismatch", errors)
        self.assertIn("missing_root_artifact_roles_mismatch", errors)
        self.assertIn("missing_root_verified_artifact_count_mismatch", errors)

    def test_independent_validator_binds_missing_manifest_to_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            result = PROTOCOL.inspect(root)
            result["artifact_roles"] = ["chameleon_checkpoint"]
            result["verified_artifact_count"] = 1
            errors = VALIDATOR.validate(result, root)
        self.assertIn("missing_manifest_artifact_roles_mismatch", errors)
        self.assertIn("missing_manifest_verified_artifact_count_mismatch", errors)

    def test_independent_validator_rejects_post_result_artifact_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "artifact-manifest.json").write_text(json.dumps(_manifest(root)), encoding="utf-8")
            result = PROTOCOL.inspect(root)
            target = root / "chameleon_checkpoint.bin"
            target.write_bytes(b"mutated")
            errors = VALIDATOR.validate(result, root)
        self.assertIn("artifact_0_file_0_revalidation_digest_mismatch", errors)

    def test_independent_validator_requires_real_boolean_boundary_flags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "artifact-manifest.json").write_text(json.dumps(_manifest(root)), encoding="utf-8")
            result = PROTOCOL.inspect(root)
            result["model_execution"] = 0
            errors = VALIDATOR.validate(result, root)
        self.assertIn("model_execution_mismatch", errors)

    def test_validator_cli_reopens_trusted_artifact_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "artifact-manifest.json").write_text(json.dumps(_manifest(root)), encoding="utf-8")
            result = PROTOCOL.inspect(root)
            with tempfile.TemporaryDirectory() as result_directory:
                result_path = Path(result_directory).resolve() / "preflight-result.json"
                result_path.write_text(json.dumps(result), encoding="utf-8")
                self.assertEqual(
                    VALIDATOR.main([str(result_path), "--artifact-root", str(root)]),
                    0,
                )


if __name__ == "__main__":
    unittest.main()
