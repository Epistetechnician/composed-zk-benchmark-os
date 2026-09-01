# Contract compiler and negative-capability audit v2

Date: 2026-08-29.

State slice: `continual-learning-contract-compiler-negative-capability-v2`.

Status: `ProtocolDraft / ReviewRequired / NoModelNoCorpusNoTraining`.

Mutation scope: documentation only under the named state slice. This protocol
does not authorize implementation, model loading, corpus acquisition, external
storage, node creation, H100 allocation, GiveMeANode execution, training, or
assessment.

## Purpose and terminal boundary

V2 is a pure contract compiler specification for the continual-learning lane.
It is a prerequisite audit of parser correctness, capability denial, custody
binding, event ordering, lock semantics, retention evidence, and classification
precedence. It produces no scientific result and cannot authorize a later
slice.

The only permitted V2 classifications are:

`text
ProtocolRejectedBeforeAudit
ContractAuditFailure
ContractAuditPass
`

The claim ceiling is
`LocalDevelopmentContractCompilerNegativeCapabilityAuditV2`. A pass means
only that the frozen in-memory fixtures and source-capability policy passed.
It does not establish that any future actor, corpus, runtime, provider, or
scientific protocol is available or valid.

V2 permanently excludes V1 and the prior adaptive-verification slices as
inputs. The pre-existing plasticity-guard replication files remain
unverified user-owned state and are neither imported nor executed.

## Review and authorization order

The order is mechanically fixed:

1. Independent review of this protocol and its digest.
2. `ACCEPT` permits implementation of the pure compiler, its hermetic tests,
   and its aggregate-only validator. `REJECT` terminates V2 before code.
3. The implementation must pass local qualification and the independent
   aggregate validator.
4. V2 remains a local contract-audit result. It cannot authorize model,
   corpus, provider, H100, training, or assessment work.

No implementation or test file may be created before an `ACCEPT` receipt is
recorded. Any protocol edit after review invalidates the receipt and requires
a new digest and review.

## Exact planned implementation boundary

The planned files, permitted only after acceptance, are:

`text
experiments/continual_learning/contract_compiler_negative_capability_v2.py
experiments/continual_learning/tests/test_contract_compiler_negative_capability_v2.py
experiments/continual_learning/validate_contract_compiler_negative_capability_v2.py
`

The compiler exports only pure functions over explicit byte/string/scalar
arguments. The principal interface is:

`python
compile_contract(
    contract_bytes: bytes,
    supplied_contract_sha256: str,
    source_bytes: bytes,
) -> dict
`

It must return either a deterministic failure receipt or a deterministic
compiled-contract receipt. It must not read a path, inspect an environment
variable, access a clock, generate randomness, open a socket, spawn a process,
load a package, or write an artifact. `source_bytes` is the explicit source
input used for the capability scan; this removes V1's undefined self-source
access while preserving a mechanically testable no-execution boundary.

The validator may read the three planned source files in its own test harness
solely to supply their bytes to the pure compiler. That harness boundary is
separate from the compiler boundary and is itself covered by a fixture that
rejects source access inside the compiler. No model, corpus, external root,
provider, network, or paid compute is present in the V2 harness.

## Import, call, and capability policy

The compiler source may import exactly these standard-library modules, with no
aliases, relative imports, wildcard imports, or imported names:

`text
ast, hashlib, json, math, re, typing
`

The following imports and names are forbidden wherever they occur, including
strings used as dynamic import targets and attribute components:

`text
os pathlib socket subprocess urllib http ssl requests httpx
torch mlx mlx_lm transformers ctypes multiprocessing threading
asyncio importlib runpy shutil tempfile pickle marshal builtins sys
resource signal platform time secrets random uuid
`

Only these bare builtin calls are permitted:

`text
all any bool bytes dict enumerate filter float int isinstance len list
map max min object range set sorted str sum tuple type zip
`

The following bare builtin calls are forbidden even if shadowed:

`text
__import__ eval exec compile open input breakpoint help dir globals locals
vars getattr setattr delattr hasattr memoryview bytearray property super
`

Attribute calls are permitted only for this exact receiver/member set:

`text
ast.parse
hashlib.sha256
json.loads json.dumps
math.isfinite math.copysign
re.fullmatch re.match
typing.cast typing.get_type_hints
decode encode lower upper strip split join replace startswith endswith
items keys values get append extend hexdigest digest is_integer
`

The source scanner rejects every other attribute call, every attribute whose
member begins with `_`, every `ast.Import` alias, every `ImportFrom` with a
nonzero relative level, every wildcard import, and every call-shaped dynamic
import. It rejects `__builtins__`, `__loader__`, `__spec__`, `__file__`,
`__package__`, and `__cached__` as names or attributes. It rejects syntax that
creates or executes code: `exec`, `eval`, `compile`, `lambda` is permitted only
as an AST fixture input and is forbidden in the compiler source, and function
annotations cannot contain calls.

The scanner receives source bytes explicitly and applies this deterministic
sequence:

1. Require `type(source_bytes) is bytes` and strict UTF-8 decoding.
2. Parse with `ast.parse(..., filename="<v2-source>", mode="exec")`.
3. Walk every node, including annotations, defaults, decorators, strings,
   and f-string expressions.
4. Apply the import, name, call, attribute, syntax, and forbidden-token rules
   above.
5. Return sorted violation identifiers; never return source text, AST text,
   identifiers, literals, or paths.

The exact violation identifiers are:

`text
source_type, source_utf8, syntax, import_module, import_alias,
relative_import, wildcard_import, forbidden_name, forbidden_attribute,
forbidden_call, forbidden_attribute_call, dynamic_import, dynamic_code,
compiler_io_surface
`

The scanner is a negative-capability audit, not a proof against arbitrary
Python implementation bugs. Its claim ceiling must remain the V2 local audit
ceiling.

## Canonical bytes and parser contract

`contract_bytes` and every digest-bound payload are UTF-8 bytes. The parser
must reject a byte sequence unless all of the following hold:

- UTF-8 decoding is strict.
- The top-level value is an object.
- No duplicate key occurs at any nesting depth.
- No unknown key, missing required key, array, or object appears outside the
  schema below.
- JSON constants `NaN`, `Infinity`, and `-Infinity` are rejected.
- Numeric parser hooks reject every lexical negative-zero form, including
  `-0`, `-0.0`, `-0e0`, and equivalent exponent forms.
- The parsed value contains no non-finite float and no negative zero.
- Strings contain no Unicode control character `U+0000` through `U+001F` or
  `U+007F`.
- No whitespace, BOM, or trailing byte exists outside the canonical JSON.

Canonical JSON is exactly:

`python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
`

The parser must require `canonical_json(parsed_value) == contract_bytes`.
This rejects alternate whitespace and escaped-ASCII spellings while retaining
Unicode characters. Boolean fields require `type(value) is bool`; integer
fields require `type(value) is int`; booleans must never satisfy
integer fields. Floats are permitted only where the schema names a float and
must be finite, non-negative where stated, and exactly representable by the
canonical round trip.

The compiler computes `contract_sha256 = sha256(contract_bytes).hexdigest()`.
It compares that recomputed value to `supplied_contract_sha256`, which must be
a lowercase 64-character hexadecimal string. A mismatch is
`contract_digest_mismatch`; the supplied digest is never trusted for any
other binding.

Every nested digest field is likewise lowercase 64-character SHA-256. A
payload digest is computed over the exact canonical bytes of that payload. A
command, manifest, lock, receipt, or review digest is a declared binding, not
evidence that the referenced bytes exist; this V2 distinction is explicit.

## Scalar and path predicates

The compiler uses these exact predicates:

- `sha256`: regular expression `^[0-9a-f]{64}$`.
- `uuid`: uppercase canonical form
  `^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$`.
- `rfc3339_seconds`: `YYYY-MM-DDTHH:MM:SSZ`, UTC only, with calendar and
  range validation; no fractional seconds or offsets.
- `posix_absolute`: one leading `/`; not `//`; no backslash, NUL, control
  character, empty component, `.` component, or `..` component; root `/` is
  allowed only for a declared root field. The predicate does not resolve the
  path and makes no filesystem claim.
- `identifier`: ASCII `[A-Za-z0-9._-]{1,128}` and not `.` or `..`.
- `nonempty_text`: Unicode string of at least one code point and no control
  character.

All list ordering is significant and is part of the canonical digest. All
sets in the contract are represented as sorted lists, never JSON objects with
unordered semantics.

## Complete contract schema

The top-level object has exactly these keys and no others:

`text
schema, state_slice, execution_mode, claim_ceiling, exclusions,
implementation, actor, custody, corpus, training, estimator, reliability,
power, events, lock, retention, classification
`

The fixed top-level values are:

`yaml
schema: continual-learning-contract-compiler-v2
state_slice: continual-learning-contract-compiler-negative-capability-v2
execution_mode: NO_MODEL_NO_CORPUS_NO_TRAINING
claim_ceiling: LocalDevelopmentContractCompilerNegativeCapabilityAuditV2
`

`exclusions` has exactly `prior_slices`, a list of exactly four objects with
keys `state_slice`, `protocol_sha256`, and `status`, in this order:

`yaml
- state_slice: continual-learning-contract-compiler-negative-capability-v1
  protocol_sha256: ed57e6c43a18c4d24b4e45e0c70893030afb7e32c61fbacb41e5bb950c7b1648
  status: CLOSED_PROTOCOL_REJECTED
- state_slice: continual-learning-adaptive-verification-reversible-adapter-v3
  protocol_sha256: 2f3c9562d9247abd75267e3de34ecd36ce5dfec5b353520f8976291d487134e0
  status: CLOSED_PROTOCOL_REJECTED
- state_slice: continual-learning-adaptive-verification-reversible-adapter-v4
  protocol_sha256: 6991f8ce5f9d98a0f2728e894ae9fa5897551d5cd9096ba2273652e09cd0df35
  status: CLOSED_PROTOCOL_REJECTED
- state_slice: continual-learning-adaptive-verification-reversible-adapter-v5
  protocol_sha256: 9cb3c08f343fcc4f6b2fd7f097d54e83ce82910b933b15b1fd8a0e38fbee18bb
  status: CLOSED_PROTOCOL_REJECTED
`

`implementation` has exactly `module`, `tests`, `validator`, `source_input`,
`function`, `allowed_imports`, `allowed_builtins`, `allowed_attributes`, and
`io_policy`. The values are the three planned relative paths, `bytes`,
`compile_contract`, the exact allowlists above, and
`PURE_IN_MEMORY_NO_FILESYSTEM_NO_NETWORK_NO_PROCESS`.

`actor` has exactly `role`, `name`, `model_manifest_sha256`,
`runtime_manifest_sha256`, `source_manifest_sha256`, `device`, and
`execution_allowed`. It requires role `FUTURE_EXECUTION_ACTOR`, nonempty
identifiers for name/device, three valid digests, and `false`. It does not
name or load a model.

`custody` has exactly `root`, `volume_uuid`, `mode`, `root_precondition`,
`write_policy`, `manifest_sha256`, and `execution_allowed`. It requires a
non-root absolute POSIX root, a canonical uppercase UUID, mode `0700`,
`ABSENT_BEFORE_ACQUISITION`, `WRITE_ONCE_EXCEPT_EVENTS`, a valid digest, and
`false`. V2 validates the contract binding only; it cannot assert path
existence, permissions, or volume identity.

`corpus` has exactly `identity`, `status`, `source_policy`, `normalization`,
`split_policy`, and `prior_manifest_set`. It requires identity
`NOT_APPLICABLE_UNTIL_SEPARATE_AUTHORIZATION`, status `NOT_ACQUIRED`, source
policy `NO_SOURCE_READ`, normalization `NOT_APPLICABLE`, split policy
`NOT_APPLICABLE`, and an empty prior manifest list. This prevents the
contract-audit lane from consuming corpus text or silently inheriting prior
data.

`training` has exactly `base_weights_updated`, `adapter_merge`, `fine_tune_type`,
`iterations`, `rows`, `batch_size`, `num_layers`, `learning_rate`,
`mask_prompt`, `command_digest`, and `network_access`. It requires
`false,false,NONE,0,0,0,0,0.0,false,<valid digest>,false`. No model or adapter
operation is represented as permitted.

`estimator` has exactly `primary`, `secondary`, `threshold`, `bootstrap`,
`positive_case_count`, `assessment_guard`, and `missingness`. It requires
`contract_audit_only`, `not_applicable`, `0.0`, `NONE`, `0_OF_0`,
`NO_ASSESSMENT`, and `REJECT_NO_IMPUTATION`. These fields explicitly prevent
V2 from becoming a scientific or performance experiment.

`reliability` has exactly `process_repeats`, `deterministic`,
`receipt_digest_tolerance`, and `independence`. It requires `3`, `true`,
`0`, and `THREE_FRESH_OS_PROCESSES_SAME_COMMAND_ENVIRONMENT`. Repeatability
means byte-identical aggregate receipts across fresh processes.

`power` has exactly `simulations`, `null_mu`, `alternative_mu`,
`alternative_min`, `null_max`, and `hash_grammar`. It requires `0`, `0.0`,
`0.0`, `0.0`, `0.0`, and `NOT_APPLICABLE_CONTRACT_AUDIT_ONLY`. V2 performs no
power analysis and makes no effect claim.

`events` has exactly `sequence_origin`, `line_keys`, `order`,
`payload_schemas`, and `assessment_transition`. It requires sequence origin
`0`, line keys
`sequence,event,timestamp,state_slice,contract_sha256,payload,payload_sha256`,
and this exact event order:

`text
protocol_review_accepted, implementation_authorized, audit_started,
contract_digest_verified, contract_schema_validated,
source_capability_scan_completed, fixtures_completed,
aggregate_receipt_sealed, audit_completed
`

V2 may emit only events through `audit_completed`; the first two are review
and implementation receipts, not compiler-generated authorization. Every
event object has exactly the line keys above. `sequence` is contiguous from
zero; `state_slice` and `contract_sha256` must equal the current values;
`payload_sha256` is recomputed from canonical payload bytes; timestamps are
strictly increasing UTC RFC3339 seconds. Each event payload schema is fixed:

`yaml
protocol_review_accepted: review_sha256, reviewer_role, verdict
implementation_authorized: authorization_sha256, execution_authorized
audit_started: validator_identity, validator_sha256
contract_digest_verified: recomputed_contract_sha256, supplied_contract_sha256
contract_schema_validated: schema_version, top_level_key_count
source_capability_scan_completed: source_sha256, violation_ids, passed
fixtures_completed: fixture_count, failed_fixture_ids, passed
aggregate_receipt_sealed: receipt_sha256, retained_field_names
audit_completed: classification, claim_ceiling, terminal
`

Every payload key has a declared scalar/list type in the implementation
schema. `execution_authorized` is always `false` in V2. The validator rejects
missing, extra, out-of-order, duplicate, or phase-inconsistent events. An
assessment transition is impossible because no `assessment_started` event is
in the V2 order.

`lock` has exactly `filename`, `write_policy`, `assessment_started`,
`required_fields`, `canonical_digest`, `review_binding`, `input_bindings`,
and `sealed`. It requires `not-applicable-v2.lock.json`, `WRITE_ONCE`,
`false`, the exact list
`protocol_sha256,contract_sha256,source_sha256,fixture_matrix_sha256,validator_identity,review_sha256,classification,claim_ceiling,execution_authorized`,
`V2_CANONICAL_JSON_SHA256`,
`REVIEW_SHA256_MUST_EQUAL_RECOMPUTED_REVIEW_SHA256`, an exact object binding
the protocol/contract/source/fixture digests, and `false`. A V2 lock is a
local receipt-bound configuration object, not an assessment prediction lock.

`retention` has exactly `deadline`, `source_validator_phase`,
`aggregate_validator_phase`, `retained_fields`, `deleted_fields`,
`deletion_evidence`, and `execution_data_present`. It requires deadline
`2026-09-05T00:00:00Z`, `BEFORE_CLEANUP`, `AFTER_CLEANUP`, retained fields
`classification,claim_ceiling,contract_sha256,source_sha256,fixture_ids,gate_booleans,receipt_digests`, deleted fields
`contract_bytes,source_bytes,fixture_inputs,raw_text,token_ids,logits,activations,adapter_tensors,training_data,training_logs,per_window_outputs`,
an exact deletion-evidence object containing `actor`, `timestamp`,
`deleted_digest`, and `event_sequence`, and `false` for
`execution_data_present`. V2 retains only aggregate and receipt metadata;
the validator output must never contain raw contract/source/fixture bytes.

`classification` has exactly `protocol_rejected`, `audit_failure`,
`audit_pass`, `precedence`, and `receipt_binding`. It requires values
`ProtocolRejectedBeforeAudit`, `ContractAuditFailure`, and
`ContractAuditPass`; precedence
`PROTOCOL_REJECTED_THEN_AUDIT_FAILURE_THEN_AUDIT_PASS`; and a binding that
requires the final classification and receipt digest to be recomputed from
the aggregate receipt. Predicates are:

`text
ProtocolRejectedBeforeAudit: no ACCEPT review receipt exists.
ContractAuditFailure: ACCEPT exists but any required gate or fixture fails.
ContractAuditPass: ACCEPT exists, all fixtures and gates pass, and the
                    independent aggregate validator recomputes the receipt.
`

No other classification is valid.

## Digest and custody bindings

The protocol digest is computed over the exact bytes of this protocol file.
The review packet stores that digest and the reviewed path. The implementation
authorization, if ever created, must bind the reviewed protocol digest and
must set `execution_authorized: false` for V2.

The compiler aggregate receipt must contain only:

`text
state_slice, protocol_sha256, contract_sha256, source_sha256,
fixture_matrix_sha256, validator_sha256, fixture_count, failed_fixture_ids,
gate_booleans, classification, claim_ceiling, execution_authorized
`

`failed_fixture_ids` is an ordered list of fixture identifiers, never raw
inputs. Every digest in the receipt is recomputed in the same process and
independently recomputed by the validator in a fresh process. No digest is
accepted merely because it was supplied by a contract or event payload.

Custody fields are schema bindings only. The V2 result must state explicitly
that it does not validate an external root, model, corpus, runtime, node,
volume, permissions, or provider account.

## Immutable fixture matrix

The fixture matrix is an in-memory ordered list of exactly 56 fixtures. Each
fixture has exactly `id`, `category`, `input_kind`, `expected`, and
`failure_id`. Fixture IDs are immutable and sorted lexicographically in the
matrix digest. Inputs are constructed in memory by the tests; no fixture file
is read.

`text
P01 canonical_positive contract pass
P02 unicode_canonical contract pass
P03 nested_duplicate_key contract duplicate_key
P04 top_level_array contract top_level_type
P05 top_level_scalar contract top_level_type
P06 empty_object contract missing_key
P07 unknown_top_level_key contract unknown_key
P08 unknown_nested_key contract unknown_key
P09 missing_required_nested_key contract missing_key
P10 bool_for_integer contract type_mismatch
P11 integer_for_bool contract type_mismatch
P12 float_for_integer contract type_mismatch
P13 string_for_digest contract type_mismatch
P14 nan_constant contract non_finite
P15 infinity_constant contract non_finite
P16 negative_zero_int contract negative_zero
P17 negative_zero_float contract negative_zero
P18 non_utf8 contract utf8
P19 bom_prefix contract canonical_bytes
P20 trailing_nonspace contract canonical_bytes
P21 trailing_space contract canonical_bytes
P22 escaped_ascii_noncanonical contract canonical_bytes
P23 control_character contract control_character
P24 invalid_sha256 contract digest_format
P25 uppercase_sha256 contract digest_format
P26 invalid_uuid contract uuid_format
P27 relative_path contract path_format
P28 double_slash_path contract path_format
P29 dot_path_component contract path_format
P30 backslash_path contract path_format
P31 wrong_exclusion_order contract exclusion_binding
P32 wrong_exclusion_digest contract exclusion_binding
P33 wrong_exclusion_status contract exclusion_binding
P34 nonempty_prior_manifest contract corpus_reuse
P35 training_enabled contract no_execution_value
P36 network_enabled contract no_execution_value
P37 nonzero_iterations contract no_execution_value
P38 assessment_estimator contract no_assessment_value
P39 event_gap events sequence_gap
P40 event_duplicate_sequence events sequence_duplicate
P41 event_wrong_state_slice events state_binding
P42 event_wrong_contract_digest events digest_binding
P43 event_bad_payload_digest events payload_digest
P44 event_timestamp_regression events timestamp_order
P45 event_extra_payload_key events payload_schema
P46 event_assessment_transition events forbidden_transition
P47 lock_started lock_transition
P48 lock_bad_review_binding lock_binding
P49 retention_raw_field retention_policy
P50 retention_missing_deletion_evidence retention_evidence
P51 classification_bad_precedence classification_precedence
P52 classification_bad_receipt_binding classification_binding
P53 source_forbidden_import source_import
P54 source_forbidden_builtin source_builtin
P55 source_dynamic_import source_dynamic_import
P56 source_dynamic_code source_dynamic_code
`

`P01` and `P02` must pass. Every other fixture must fail with exactly the
listed primary failure identifier. The tests also run each failure fixture
through every fresh process repeat; an exception, nondeterministic failure,
unexpected pass, or unexpected failure is a V2 audit failure.

## Gates and independent validation

The post-acceptance qualification gates are fixed:

1. Protocol, implementation, fixture, and validator digests are present and
   recomputed.
2. The compiler imports only the allowlist and has no forbidden capability
   surface.
3. Native in-memory output is deterministic across three fresh OS processes.
4. Canonical parsing and all 56 expected fixture outcomes pass.
5. Digest, event, lock, retention, and classification bindings recompute.
6. Aggregate output contains no raw input or execution data.
7. The independent validator reproduces the same aggregate receipt.

Any failed gate is terminal `ContractAuditFailure`; no adaptive fixture,
schema, allowlist, or threshold repair is allowed inside V2. There is no
provider step and no H100 step in this slice.

The independent validator must be a separate process and a separate source
file from the compiler. It may duplicate validation logic, but it may not
import the compiler's private validator or accept the compiler's booleans
without recomputation. It must verify the receipt against the protocol,
fixture matrix, source digest, and contract digest, then emit aggregate-only
fields.

## Claim ceiling and next gate

Even a passing V2 result is only
`ContractAuditPass / LocalDevelopmentContractCompilerNegativeCapabilityAuditV2`.
It does not validate the unverified plasticity replication, establish a
plasticity effect, authorize a commit-budget mechanism audit, justify a
cross-actor replication, or authorize GiveMeANode/H100 use. Those actions
require their own fresh sealed protocols and independent reviews.

The next decision is solely the independent V2 protocol verdict. An
`ACCEPT` permits protocol implementation and hermetic local validation. A
`REJECT` terminates the V2 slice and all downstream slices remain blocked.
