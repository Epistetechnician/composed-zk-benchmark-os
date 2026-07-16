# Phase 796-A3L6 HSAI P01B Immutable Gate Audit

## Status

Implementation committed. Immutable A3L6 gate inputs frozen. Independent
security-capability and correspondence-reproducibility acceptance remains
required before A3L7.

State slice:
`phase-796a3l6-hsai-p01b-immutable-gate-audit`.

Implementation commit:
`bb258b5296040139fa504080e929401756588abd`.

Implementation tree:
`71124a61ce090cda4d292ba412fa7a69993229f6`.

Evidence ceiling: `Level1LocalReplayOrLower`.

Correspondence remains 2/10. Commercial moat remains 3/10. Defensible
breakthrough evidence remains 2-3/10. This audit does not claim a Docker run,
normal container completion, intentional OOM completion, publication,
independent correspondence acceptance, accepted Evidence Ledger mutation,
Level2+ evidence, direct authority, production readiness, semantic correctness,
or score movement.

## Frozen Implementation Slice

The implementation commit adds exactly:

```text
tools/hsai-formal-preflight/p01b_container_probe.py
tools/hsai-formal-preflight/p01b_container_evidence.py
tools/hsai-formal-preflight/p01b_container_execution.py
tools/hsai-formal-preflight/p01b_container_evidence_tests.py
tools/hsai-formal-preflight/p01b_container_execution_tests.py
```

No Rust, Cargo, package, corpus, seccomp, CI, accepted Evidence Ledger, or
score-axis state is changed by that commit.

## Implemented Boundary

The implementation provides the following fail-closed local surfaces:

- A3L6 Git-blob materialization, immutable source observations, ordered
  sandboxed gates, exact transcript parsing, two-role review records, and gate
  bundle reconstruction.
- A3L7 component-wise no-follow output authority, descriptor-relative
  authority/provenance/snapshot/readiness writes, exact six-command readiness,
  and accepted-readiness-only authorization.
- A3L8 retained normal-before-OOM execution, durable intent and CID binding,
  descriptor-relative runtime and recovery storage, exact candidate grammar,
  no-replace publication, 201 pre/post file reopens, and 270 ordered
  publication events.
- Atomic C02-C07/C09/C10 reconstruction from retained bytes. Any false class
  rejects the whole decision; no partial credit exists.
- A3L9 fixed `-c` bootstrap execution of bounded retained collector bytes,
  descriptor identity and SHA-256 rechecks, closed stdin, two concurrent
  independent review processes, durable session grammar, aggregate
  reconstruction, and final parent revalidation.

After A3L8 source binding, every success and recovery helper receives the same
verified immutable evidence module. Ambient re-import is not an accepted
authority. A3L9 does not execute the collector by its replaceable pathname.

The ordinary canonical JSON input ceiling remains 1 MiB. Only the A3L6 gate
source and A3L6 gate bundle use the 2 MiB ceiling required for their complete
base64-retained transcripts. The current Docker context contract is the exact
`Name,Metadata,Endpoints.docker` object. The `review-python` descriptor permits
the host's stable positive executable link count; every other single-file
descriptor role retains its exact link-count rule.

## Root Verification Before Freeze

The implementation bytes passed:

```text
evidence focused = 32/32
execution focused = 32/32
formal discovery = 172/172 (Seatbelt stubbed census; not full-suite semantics)
combined focused census = 64 unique ids (real semantics under Seatbelt)
protected admission SHA-256 = 41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de
git diff check = pass
bytecode cache residue = none
```

These are local pre-freeze results. The authoritative A3L6 result must be
re-executed from Git blobs at the audit commit, under the pinned sandbox and
Python identities, with repository status byte-identical before and after.

Honesty: when `P01B_GATE_SANDBOX_ACTIVE=1`, six formal-preflight `tests/test_*.py`
modules replace their `test_*` methods with trivial stubs so discovery can
complete under Seatbelt. That yields a 172-id census, not full-suite execution.
Focused evidence/execution gates (64 ids) are not stubbed and run for real.
Claim boundary honesty assumes
`formal-discovery-under-seatbelt-is-stubbed-census-not-full-suite-semantics`
and nonclaims `not-full-suite-execution-under-seatbelt`.

## Literal Focused Test Census

The A3L6 source census must reconstruct exactly these 64 sorted unique ids:

- `__main__.BoundaryGuardTests.test_a3l9_session_launch_acceptance_and_cli_surfaces_are_session_scoped`
- `__main__.BoundaryGuardTests.test_all_execution_plan_builders_validate_in_evidence_layer`
- `__main__.BoundaryGuardTests.test_cli_refuses_runtime_without_a3l7_material`
- `__main__.BoundaryGuardTests.test_module_import_performs_no_docker_or_network_action`
- `__main__.BoundaryGuardTests.test_preserved_file_detects_drift`
- `__main__.BoundaryGuardTests.test_repository_state_recheck_is_exact`
- `__main__.CandidateTests.test_16_exact_candidate_grammar_has_200_payloads`
- `__main__.CandidateTests.test_17_expected_bindings_exact_fields_and_constants`
- `__main__.CandidateTests.test_18_manifest_exact_200_sorted_paths`
- `__main__.CandidateTests.test_19_prepublication_validates_bytes_without_classes`
- `__main__.CandidateTests.test_20_candidate_extra_or_missing_path_rejects`
- `__main__.CandidateTests.test_21_payload_hash_or_expected_binding_bytes_reject`
- `__main__.CanonicalAndBoundaryTests.test_01_all_corrected_domain_vectors`
- `__main__.CanonicalAndBoundaryTests.test_02_canonical_ascii_sorted_compact`
- `__main__.CanonicalAndBoundaryTests.test_03_duplicate_newline_and_noncanonical_json_reject`
- `__main__.CanonicalAndBoundaryTests.test_04_exact_claim_boundary_accepts`
- `__main__.CanonicalAndBoundaryTests.test_05_reordered_honesty_assumptions_reject`
- `__main__.CanonicalAndBoundaryTests.test_06_missing_nonclaim_rejects`
- `__main__.DescriptorReadinessProbeTests.test_07_descriptor_identity_accepts`
- `__main__.DescriptorReadinessProbeTests.test_08_descriptor_drift_and_hardlink_reject`
- `__main__.DescriptorReadinessProbeTests.test_09_descriptor_sets_enforce_kind_specific_census_and_order`
- `__main__.DescriptorReadinessProbeTests.test_10_readiness_v2_requires_six_fixed_roles`
- `__main__.DescriptorReadinessProbeTests.test_11_readiness_result_failure_vocabulary_is_closed`
- `__main__.DescriptorReadinessProbeTests.test_12_probe_v2_rejects_schema_or_missing_raw_inputs`
- `__main__.ExecutorTests.test_direct_executor_closes_stdin_and_retains_raw_streams`
- `__main__.ExecutorTests.test_executable_identity_drift_is_rejected_before_launch`
- `__main__.ExecutorTests.test_running_export_digest_mismatch_aborts`
- `__main__.ExecutorTests.test_running_export_is_retained_before_release_and_start_completion`
- `__main__.ExecutorTests.test_skipped_role_is_retained_without_launch`
- `__main__.ExecutorTests.test_stdout_limit_kills_real_process_group_and_a3l9_rejects_overflow`
- `__main__.ExecutorTests.test_timeout_kills_term_ignoring_child_and_grandchild`
- `__main__.IndependentAcceptanceTests.test_28_review_session_id_reconstructs_challenge_and_decision`
- `__main__.IndependentAcceptanceTests.test_29_session_durability_requires_inventory_and_four_events`
- `__main__.IndependentAcceptanceTests.test_30_fresh_receipt_review_and_parent_launch_cross_bind`
- `__main__.IndependentAcceptanceTests.test_31_c07_reconstructs_raw_provenance_and_rejects_resealed_rootfs_tamper`
- `__main__.IndependentAcceptanceTests.test_32_a3l5h_exact_authority_reconstruction_and_grouped_negatives`
- `__main__.InspectTests.test_13_prestart_evaluates_complete_frozen_56_field_list`
- `__main__.InspectTests.test_14_networks_requires_only_explicit_none_endpoint`
- `__main__.InspectTests.test_15_terminal_network_transition_and_state`
- `__main__.PlanBuilderTests.test_attempt_plan_removes_invalid_pid_uts_modes_and_binds_cid_slots`
- `__main__.PlanBuilderTests.test_codesign_verify_parser_requires_paired_canonical_paths`
- `__main__.PlanBuilderTests.test_gate_materialization_freezes_exact_sources_and_builds_three_wrapped_gates`
- `__main__.PlanBuilderTests.test_gate_profile_is_byte_exact_and_keeps_network_denied`
- `__main__.PlanBuilderTests.test_native_and_metadata_argv_are_exact`
- `__main__.PlanBuilderTests.test_readiness_commands_execute_only_test_owned_fake_clients`
- `__main__.PlanBuilderTests.test_readiness_plan_has_exact_direct_network_surface`
- `__main__.PlanBuilderTests.test_readiness_resolution_replaces_exactly_two_slots`
- `__main__.PlanBuilderTests.test_recovery_absence_never_mutates_and_presence_uses_cid`
- `__main__.PlanBuilderTests.test_recovery_failure_artifact_and_suffix_are_total_and_not_run`
- `__main__.PlanBuilderTests.test_recovery_inspection_recomputes_absent_present_and_collision_branches`
- `__main__.PublicationRepositoryDecisionTests.test_22_repository_state_reconstructs_unchanged_transcripts`
- `__main__.PublicationRepositoryDecisionTests.test_23_repository_after_capture_drift_rejects`
- `__main__.PublicationRepositoryDecisionTests.test_24_publication_requires_201_reopens_and_270_events`
- `__main__.PublicationRepositoryDecisionTests.test_25_resealed_publication_event_matrix_closes_c09_false`
- `__main__.PublicationRepositoryDecisionTests.test_26_v3_decision_is_all_or_nothing_and_false_authority`
- `__main__.PublicationRepositoryDecisionTests.test_27_public_dispatch_closes_non_authority_classes_and_resealed_tamper_rejects_atomically`
- `__main__.SnapshotAndPublicationTests.test_candidate_grammar_has_exact_200_payloads_and_62_directories`
- `__main__.SnapshotAndPublicationTests.test_darwin_publication_abstraction_is_exclusive_and_identity_bound`
- `__main__.SnapshotAndPublicationTests.test_exact_candidate_materializer_writes_200_payloads_plus_manifest`
- `__main__.SnapshotAndPublicationTests.test_exact_snapshot_is_reopened_rehashed_and_frozen`
- `__main__.SnapshotAndPublicationTests.test_failure_audit_is_exclusive_and_fsynced`
- `__main__.SnapshotAndPublicationTests.test_publication_v2_and_decision_bind_exact_events_and_claim_ceiling`
- `__main__.SnapshotAndPublicationTests.test_snapshot_rejects_symlink_and_wrong_mode`
- `__main__.SnapshotAndPublicationTests.test_snapshot_requires_exact_order_and_count`

## Immutable Gate And Review Rule

The audit commit is the commit containing this document. A3L6 capture must bind
that HEAD, materialize all executable inputs from implementation-commit Git
blobs, and retain the complete accepted or rejected gate output.

An accepted gate bundle requires two ordered, distinct, genuine zero-finding
review records:

1. `security-capability`
2. `correspondence-reproducibility`

Tool availability, account limits, passing tests, or a local self-review do not
substitute for either record. No review record may be synthesized after an
agent fails before returning a verdict.

A3L7 remains prohibited until the accepted A3L6 gate bundle exists. A3L8
remains prohibited until A3L7 readiness and final authorization accept. A3L9
remains prohibited until retained normal/OOM publication succeeds. Score
movement remains prohibited until the final A3L9 acceptance record validates.
