"""Independent validation of the Oak Lab V5 compiled protocol.

State slice: ``oaklab-experience-learning-constrained-update-policy-v5``.
This validator deliberately reimplements canonicalization, framing, PRNG
transcript checks, and section checks instead of importing the compiler.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


STATE_SLICE = "oaklab-experience-learning-constrained-update-policy-v5"
COMPILED_SCHEMA = "oaklab.experience-learning.constrained-update-policy-v5.compiled.v1"
SECTIONS = [
    "hash_prng_transcript",
    "controller_transition_table",
    "generator_roster",
    "operation_and_byte_algebra",
    "ablation_execution_multiplicity",
    "adaptation_metrics",
    "lock_counter_control_schemas",
]
EXPECTED_ARTIFACT_KEYS = {
    "schema_version", "protocol_id", "state_slice", "claim_ceiling", "compiler_version",
    "source_spec_sha256", "sections", "section_digests", "transcript_test_vector",
    "assessment_materialization_state", "compiled", "stop_rules", "boundaries", "estimand",
    "compiled_protocol_sha256",
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def lp32(value: bytes) -> bytes:
    return struct.pack(">I", len(value)) + value


def splitmix64(seed: bytes, count: int) -> list[int]:
    state = int.from_bytes(seed[:8], "big")
    output: list[int] = []
    for _ in range(count):
        state = (state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        value = state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        output.append((value ^ (value >> 31)) & 0xFFFFFFFFFFFFFFFF)
    return output


def independent_vector(source_digest: str) -> dict[str, Any]:
    raw_digest = bytes.fromhex(source_digest)
    cohort = b"fit"
    stream = b"sparse_predictable_v5"
    seed = 4000
    frame = lp32(b"oaklab.cup.v5.splitmix64.seed.v1") + raw_digest + lp32(cohort) + lp32(stream) + struct.pack(">Q", seed)
    root = hashlib.sha256(frame).digest()
    outputs = splitmix64(root, 13)
    action = lp32(b"oaklab.cup.v5.action.v1") + raw_digest + bytes.fromhex("7fefd5e1fbc346fbe8c20dfba40c7c362a0f6935d6d5f4707291ded5ea87cd56") + lp32(cohort) + lp32(stream) + struct.pack(">Q", seed) + struct.pack(">I", 0)
    return {
        "frame_hex": frame.hex(),
        "root_sha256_hex": root.hex(),
        "initial_state_uint64_be": int.from_bytes(root[:8], "big"),
        "first_12_raw_uint64_hex": [f"{value:016x}" for value in outputs[:12]],
        "first_uniform53": (outputs[0] >> 11) / float(1 << 53),
        "first_normal12_after_first_draw": sum((value >> 11) / float(1 << 53) for value in outputs[1:13]) - 6.0,
        "action_hash_sha256_hex": hashlib.sha256(action).hexdigest(),
    }


def validate(source_path: Path, artifact_path: Path, repo_root: Path) -> dict[str, Any]:
    source_bytes = source_path.read_bytes()
    require(source_bytes.startswith(b"{") and source_bytes.endswith(b"\n"), "source must be UTF-8 JSON with a final LF")
    source = json.loads(source_bytes.decode("utf-8"))
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    require(isinstance(source, dict), "source is not an object")
    require(isinstance(artifact, dict) and set(artifact) == EXPECTED_ARTIFACT_KEYS, "compiled artifact has missing or extra keys")
    source_digest = digest(source_bytes)
    require(artifact["source_spec_sha256"] == source_digest, "source digest mismatch")
    require(artifact["schema_version"] == COMPILED_SCHEMA and artifact["protocol_id"] == "oaklab.cup.v5", "compiled identity mismatch")
    require(artifact["state_slice"] == STATE_SLICE and artifact["assessment_materialization_state"] == "absent", "state or assessment boundary mismatch")
    require(artifact["sections"] == SECTIONS and set(artifact["compiled"]) == set(SECTIONS), "seven compiled sections are not exact")
    require(artifact["estimand"] == source["estimand"] and "complete-policy" in artifact["estimand"]["scope"], "complete-policy estimand changed")
    require(artifact["compiled"] == {name: source[name] for name in SECTIONS}, "compiled section bytes do not equal source sections")
    require(artifact["section_digests"] == {name: digest(canonical(source[name])) for name in SECTIONS}, "section digest table mismatch")
    no_self = {key: value for key, value in artifact.items() if key != "compiled_protocol_sha256"}
    require(artifact["compiled_protocol_sha256"] == digest(canonical(no_self)), "compiled digest mismatch")
    require(artifact["transcript_test_vector"] == independent_vector(source_digest), "PRNG/action test vector mismatch")

    hash_spec = source["hash_prng_transcript"]
    require(hash_spec["file_bytes"] == "UTF-8 without BOM, LF line endings, exactly one final LF; source digest is over these exact bytes", "source byte policy changed")
    require(hash_spec["frame"].startswith("LP32(payload)="), "frame codec is not LP32/fixed-width")
    require(hash_spec["action_hash"]["fields"] == ["protocol_digest_raw_32", "exploration_master_seed_raw_32", "cohort_id_utf8", "stream_id_utf8", "data_seed_uint64", "local_row_uint32"], "action hash field widths changed")
    controller = source["controller_transition_table"]
    require(sorted(row["index"] for row in controller["rows"]) == list(range(8)), "controller indices are not complete")
    require(len(controller["state_fields"]) == 20, "controller state roster changed")
    names = {field["name"] for field in controller["state_fields"]}
    require({"pending_valid", "previous_mu_at_action", "pending_mu_at_action", "pending_local_row"}.issubset(names), "pending state is incomplete")
    require("undeclared state is invalid" in controller["pending_rule"], "controller closed-world state rule missing")

    roster = source["generator_roster"]
    expected_streams = {"sparse_predictable_v5", "noisy_mnist_v5", "feature_relevance_v5", "piecewise_drift_v5", "delayed_reward_v5", "event_camera_v5", "long_horizon_v5", "pure_noise_v5"}
    require(set(roster["streams"]) == expected_streams and set(roster["draw_roster"]) == expected_streams, "generator roster mismatch")
    require(roster["stream_order"] == ["delayed_reward_v5", "feature_relevance_v5", "piecewise_drift_v5", "event_camera_v5", "sparse_predictable_v5", "noisy_mnist_v5", "long_horizon_v5", "pure_noise_v5"], "stream order changed")
    require(roster["cohort_seeds"] == {"fit": {"start": 4000, "count": 16}, "tune": {"start": 5000, "count": 16}, "assessment": {"start": 6000, "count": 48}}, "cohort roster changed")
    for stream_id, draws in roster["draw_roster"].items():
        require([item["ordinal"] for item in draws] == list(range(len(draws))), f"{stream_id} draw ordinals changed")
        require(all(item["repeat"] > 0 for item in draws), f"{stream_id} has conditional/empty draw")

    algebra = source["operation_and_byte_algebra"]
    require(set(algebra["formula_ast"]) >= {"model_forward_dense", "model_gradient", "model_update", "parameter_writes", "controller_dot", "event_count"}, "typed operation AST incomplete")
    require(algebra["numeric_type_widths"] == {"boolean": 1, "uint8": 1, "uint32": 4, "uint64": 8, "float64": 8, "sha256_digest": 32}, "numeric widths changed")
    require(all(name in algebra["byte_layouts"] for name in ("model_state", "fit_controller_state", "pending_row", "counter_row", "assessment_compiled_controller", "lock_receipt")), "byte layouts incomplete")

    ablations = source["ablation_execution_multiplicity"]
    require(len(ablations["arm_order"]) == 10 and set(ablations["arms"]) == set(ablations["arm_order"]), "ablation table incomplete")
    require([row["phase"] for row in ablations["execution_table"]] == ["fit", "tune", "assessment"], "ablation phases changed")
    require(len(ablations["holm_groups"]) == 3 and all("sort raw p then" in group["adjustment"] for group in ablations["holm_groups"]), "multiplicity table incomplete")

    adaptation = source["adaptation_metrics"]
    require("[k,k+8)" in adaptation["recovery_scan"] and "[k+8,k+16)" in adaptation["recovery_scan"], "adaptation windows are not adjacent and bounded")
    require("next_shift" in adaptation["censoring"] and "never scan across a shift" in adaptation["aggregation"], "adaptation censoring changed")

    schemas = source["lock_counter_control_schemas"]
    required_schema_names = {"protocol_compile_receipt", "fit_lock", "tune_lock", "counter_row", "control_result", "assessment_absence", "validator_receipt"}
    require(required_schema_names.issubset(schemas), "lock/counter/control schema set incomplete")
    for schema_name in required_schema_names:
        schema = schemas[schema_name]
        require(schema["schema_id"].startswith("oaklab.cup.v5."), f"{schema_name} is not V5")
        fields = schema["fields"]
        require(len(fields) == len({entry[0] for entry in fields}) and all(len(entry) == 3 and entry[2] is True for entry in fields), f"{schema_name} is not closed-world")
    absence = schemas["assessment_absence"]
    require(absence["fields"][1] == ["materialization_state", "enum(absent)", True], "assessment absence state changed")

    forbidden = {"run_v5.py", "execute_v5.py", "v5_learner.py", "v5_assessment.py"}
    present_forbidden = sorted(str(path.relative_to(repo_root)) for path in repo_root.rglob("*") if path.is_file() and path.name in forbidden)
    require(not present_forbidden, f"V5 runtime files exist before review: {present_forbidden}")
    return {
        "status": "valid",
        "decision": "pending_independent_review",
        "state_slice": STATE_SLICE,
        "source_spec_sha256": source_digest,
        "compiled_protocol_sha256": artifact["compiled_protocol_sha256"],
        "sections": SECTIONS,
        "assessment_materialization_state": "absent",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(validate(args.source, args.artifact, args.repo_root), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
