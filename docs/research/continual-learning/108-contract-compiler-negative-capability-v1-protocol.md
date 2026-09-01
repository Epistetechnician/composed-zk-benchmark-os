# Contract compiler and negative-capability audit v1

Date: 2026-08-28.

State slice: `continual-learning-contract-compiler-negative-capability-v1`.

Status: `ProtocolDraft / NoModelNoCorpusNoTraining`.

## Purpose and boundary

This is the first sequential prerequisite for future continual-learning work.
It is a pure contract compiler and negative-capability audit. It does not run
an experiment and makes no scientific claim. It may parse in-memory bytes and
run hermetic tests only.

V3, V4, and V5 adaptive-verification slices are permanently closed and are not
inputs. The pre-existing plasticity replication files in the shared worktree
are unverified user-owned state and are not imported, executed, or promoted by
this slice.

V1 is forbidden from:

- reading or writing any filesystem path;
- opening sockets or importing network/process/model libraries;
- spawning subprocesses or invoking MLX, MLX-LM, CUDA, H100, or GiveMeANode;
- acquiring or reading corpus text, model weights, adapters, logits, or
  training artifacts;
- modifying any external artifact root;
- authorizing a later slice.

The only permitted result is `ContractAuditPass` or `ContractAuditFailure`.
The claim ceiling is `LocalDevelopmentContractCompilerNegativeCapabilityAudit`.

## Exact implementation contract

The implementation file is
`experiments/continual_learning/contract_compiler_negative_capability_v1.py`.
It may import only these standard-library modules:

```text
ast, hashlib, json, math, re, typing
```

The implementation must not import `os`, `pathlib`, `socket`, `subprocess`,
`urllib`, `http`, `ssl`, `torch`, `mlx`, `mlx_lm`, `transformers`, or any
third-party package. The validator checks its own source AST and rejects an
import, attribute call, builtin call, or dynamic import outside the explicit
allowlist. It accepts bytes only and returns in-memory dictionaries; it has no
filesystem or process API.

The parser uses `json.loads` with an `object_pairs_hook` that rejects duplicate
keys. It rejects non-UTF-8 bytes, trailing bytes, non-object top-level values,
NaN, Infinity, negative zero, unknown keys, missing keys, wrong scalar types,
and arrays or objects outside the schema. Canonical JSON is exactly:

```python
json.dumps(value, ensure_ascii=False, sort_keys=True,
           separators=(",", ":"), allow_nan=False).encode("utf-8")
```

The contract digest is SHA-256 of those canonical bytes. A supplied digest is
never trusted. Strings are Unicode strings without control characters; paths
must be absolute POSIX strings; hex digests must be lowercase 64-character
SHA-256 values; UUID is uppercase `D53A2378-1B1E-3152-A36F-D5C68B522A84`.

## Exact contract schema

The top-level keys, with no extras, are exactly:

```text
schema, state_slice, execution_mode, claim_ceiling, exclusions, actor,
custody, corpus, training, estimator, reliability, power, events, lock,
retention, classification
```

The fixed scalar values are:

```yaml
schema: continual-learning-contract-compiler-v1
state_slice: continual-learning-contract-compiler-negative-capability-v1
execution_mode: NO_MODEL_NO_CORPUS_NO_TRAINING
claim_ceiling: LocalDevelopmentContractCompilerNegativeCapabilityAudit
```

`exclusions` is exactly an object with one key, `prior_slices`. `prior_slices`
is a list of exactly three objects, each with keys `state_slice`,
`protocol_sha256`, and `status`, binding V3, V4, and V5. The three exclusion
identities are:

```yaml
v3_protocol_sha256: 2f3c9562d9247abd75267e3de34ecd36ce5dfec5b353520f8976291d487134e0
v4_protocol_sha256: 6991f8ce5f9d98a0f2728e894ae9fa5897551d5cd9096ba2273652e09cd0df35
v5_protocol_sha256: 9cb3c08f343fcc4f6b2fd7f097d54e83ce82910b933b15b1fd8a0e38fbee18bb
```

`actor` is an object with exactly `name`, `model_root`, `runtime`, `device`,
and `execution_allowed`. V1 requires the literal future actor values
`google/gemma-3-1b-pt`,
`/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`,
`mlx-0.31.2/mlx-lm-0.31.3/python-3.14.5`, `metal`, and `false`. V1 does not
read the root.

`custody` is exactly `root`, `volume_uuid`, `mode`, `root_precondition`, and
`write_policy`. It requires the future root
`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-plasticity-guard-replication-v2-20260828`,
the UUID above, mode `0700`, `ABSENT_BEFORE_ACQUISITION`, and
`WRITE_ONCE_EXCEPT_EVENTS`. V1 only validates these literal values.

`corpus` is exactly `identity`, `status`, `source_policy`, `normalization`,
`split_policy`, and `prior_manifest_set`. Its fixed status is `NOT_ACQUIRED`.
The future identity is `gutenberg-plasticity-guard-replication-v2-20260828`;
source policy is `FRESH_EXTERNAL_DOCUMENTS_ONLY`; normalization is
`STRICT_UTF8_CRLF_LF_NFKC_MARKER_STRIP_ONE_LF`; split policy is
`DOCUMENT_DISJOINT_FIT_TUNE_ASSESSMENT`; and the prior manifest set is exactly
the three excluded identities above. V1 never opens a source path.

`training` is exactly `base_weights_updated`, `adapter_merge`,
`fine_tune_type`, `iterations`, `rows`, `batch_size`, `num_layers`,
`learning_rate`, `mask_prompt`, `command_digest`, and `network_access`. It
requires `false`, `false`, `lora`, `3`, `4`, `1`, `4`, `0.0001`, `false`, a
lowercase SHA-256 string, and `false`, respectively.

`estimator` is exactly `primary`, `secondary`, `threshold`, `bootstrap`,
`positive_case_count`, `assessment_guard`, and `missingness`. The primary is
`guarded_absolute_improvement_vs_untouched_base`; the secondary is
`guarded_improvement_minus_fixed_improvement`; threshold is `0.010`; bootstrap
is `10000_CASE_LEVEL_PERCENTILE_249_9749`; positive count is `3_OF_4`; the
assessment guard is `BASE_NLL_DENOMINATOR_STRICTLY_POSITIVE_MAX_0.05`; and
missingness is `REJECT_NO_IMPUTATION`.

`reliability` is exactly `process_repeats`, `native_nll_tolerance`,
`adapter_aggregate_tolerance`, and `independence`. It requires `3`, `1e-8`,
`1e-6`, and `THREE_FRESH_OS_PROCESSES_SAME_COMMAND_ENVIRONMENT`.

`power` is exactly `simulations`, `null_mu`, `alternative_mu`,
`alternative_min`, `null_max`, and `hash_grammar`. It requires `10000`, `0.0`,
`0.030`, `0.80`, `0.05`, and
`SHA256_POWER_V5_TAGGED_DOC_CASE_CELL_BOOTSTRAP_10000`. V1 validates the
contract values but does not run the simulation.

`events` is exactly `sequence_origin`, `line_keys`, `order`, and
`assessment_transition`. It requires origin `0`, line keys
`sequence,event,timestamp,state_slice,contract_sha256,payload,payload_sha256`,
and this exact event order:

```text
theory_review_accepted, implementation_authorized, acquisition_complete,
corpus_sealed, power_calibration_passed, qualification_passed,
scores_sealed, fit_tune_lock_sealed, assessment_review_passed,
assessment_started, assessment_complete, aggregate_validation_passed,
raw_retention_complete
```

`assessment_transition` is `ONLY_EVENT_9_AFTER_LOCK_AND_REVIEW`. Each payload
must be an object; its digest is recomputed over canonical JSON; timestamps are
UTC RFC3339 seconds ending in `Z` and strictly nondecreasing. V1 validates
event shapes in memory only.

`lock` is exactly `filename`, `write_policy`, `assessment_started`,
`required_fields`, `canonical_digest`, and `review_binding`. It requires
`fit-tune-lock.json`, `WRITE_ONCE`, `false`, the exact field list
`protocol_sha256,contract_sha256,model_manifest_sha256,source_manifest_sha256,corpus_manifest_sha256,case_ids,selection_digest,control_definitions,adapter_contract,command_digests,fit_aggregates,tune_aggregates,threshold_config,bootstrap_config,power_config,retention_config,validator_identity,theory_review_sha256,implementation_authorization_sha256,assessment_review_sha256,predicted_assessment_delta,predicted_positive_documents,assessment_started`,
`V5_CANONICAL_JSON_SHA256`, and
`REVIEWED_LOCK_SHA256_MUST_EQUAL_RECOMPUTED_LOCK_SHA256`.

`retention` is exactly `deadline`, `source_validator_phase`,
`aggregate_validator_phase`, `retained_fields`, and `deleted_fields`. It
requires deadline `2026-09-04T00:00:00Z`, source validation before cleanup,
aggregate validation after cleanup, the exact retained list
`aggregate_nlls,document_effects,selection_ids,control_summaries,digests,gate_booleans,receipts`,
and the exact deleted list
`raw_text,token_ids,logits,activations,adapter_tensors,training_data,training_logs,per_window_outputs`.

`classification` is exactly `protocol_rejected`, `audit_failure`, and
`audit_pass`, with values `ProtocolRejectedBeforeAudit`,
`ContractAuditFailure`, and `ContractAuditPass`. V1 evaluates in that order;
there is no scientific-result classification.

## Audit result and review gate

The validator must run 40 in-memory fixtures covering positive parsing,
duplicate keys, unknown keys, every wrong type, non-finite values, digest
recomputation, exclusion identities, no-execution values, path/UUID rules,
event payload/hash/order rules, lock fields, retention fields, classification
precedence, and forbidden capability ASTs. The output is one in-memory
aggregate receipt containing only state slice, validator digest, contract
digest, fixture count, booleans, failure names, and claim ceiling.

An independent reviewer must review this protocol before implementation. An
`ACCEPT` permits only the pure validator and hermetic tests. It does not permit
model loading, data acquisition, training, assessment, providers, H100, or
GiveMeANode. `REJECT` closes V1 before implementation.
