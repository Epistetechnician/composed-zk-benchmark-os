# Contract compiler and negative-capability audit v3

Date: 2026-08-29.

State slice: continual-learning-contract-compiler-negative-capability-v3.

Status: ProtocolDraft / ReviewRequired / NoModelNoCorpusNoTraining.

Mutation scope: documentation only under this state slice. This protocol does
not authorize implementation, model loading, corpus acquisition, external
storage, node creation, H100 allocation, GiveMeANode execution, training, or
assessment.

## Purpose and terminal boundary

V3 is a new contract-compiler specification after the independent V2 rejection.
It is a local, in-memory audit of a future continual-learning contract. Its
single mechanical objective is zero unclassified or nondeterministic outcomes
across a fixed 56-fixture bundle and three fresh-process repeats.

V3 has no scientific estimand. It cannot establish a plasticity effect, validate
the unverified replication, or authorize a later slice. The only classifications
are ProtocolRejectedBeforeAudit, ContractAuditFailure, and ContractAuditPass.
The claim ceiling is LocalDevelopmentContractCompilerNegativeCapabilityAuditV3.

V3 excludes all earlier adaptive-verification work, rejected V1/V2 contract
compiler slices, pre-existing plasticity replication files, Astral artifacts,
Neural Chameleon artifacts, corpus text, model weights, and GiveMeANode/H100
state. A V3 pass is a validator result only.

## Fixed authorization and review order

The order is immutable:

1. Independent review of this protocol and its review packet.
2. Only an independent ACCEPT permits creation of the three planned local
   source files and hermetic tests.
3. The compiler and independent validator run only against explicit byte inputs
   and in-memory fixtures.
4. Three fresh-process repeats and independent aggregate validation must pass.
5. V3 terminates as a local contract-audit result.

A REJECT terminates V3 before implementation. No implementation file may be
created before acceptance. Editing this protocol or its review packet after
review begins invalidates the recorded digest and requires a new V3 review.
ACCEPT never authorizes model, corpus, custody, provider, H100, training,
assessment, or downstream scientific work.

## Exact planned files and input interfaces

Only after acceptance, the planned files are:

~~~text
experiments/continual_learning/contract_compiler_negative_capability_v3.py
experiments/continual_learning/tests/test_contract_compiler_negative_capability_v3.py
experiments/continual_learning/validate_contract_compiler_negative_capability_v3.py
~~~

The compiler exports one public function with exactly ten required positional
arguments:

~~~python
compile_audit_bundle(
    protocol_bytes: bytes,
    contract_bytes: bytes,
    supplied_contract_sha256: str,
    source_bytes: bytes,
    review_receipt_bytes: bytes,
    authorization_receipt_bytes: bytes,
    event_log_bytes: bytes,
    lock_bytes: bytes,
    retention_bytes: bytes,
    fixture_matrix_bytes: bytes,
) -> dict
~~~

The compiler checks runtime types before any operation. protocol_bytes is
UTF-8 Markdown and is hashed but not parsed as JSON. The other byte arguments
are canonical UTF-8 JSON. supplied_contract_sha256 is a lowercase 64-character
hex string. The return value is an in-memory dictionary with the exact
aggregate schema specified below.

The compiler must not read a path, environment variable, clock, random source,
standard input, socket, subprocess, package metadata, model, corpus, external
artifact, or provider. It must not write bytes, emit raw input in exceptions,
or expose raw input in diagnostics. It cannot authorize a later slice.

The independent validator is a separate process and separate source file. It
receives the same ten explicit inputs through a harness and does not import the
compiler. The harness may read only the one named protocol file, the one named
source file, and the seven named JSON artifacts supplied by the V3 fixture
builder; the supplied contract digest is a scalar argument, not a file. It may
not read the repository recursively or inspect external paths.

## Exact source-capability policy

The compiler source may import exactly these modules, with no aliases, imported
names, wildcard imports, or relative imports:

~~~text
ast, hashlib, json, math, re, typing
~~~

The allowed module-qualified call shapes are exactly:

~~~text
ast.parse, ast.walk, hashlib.sha256, json.loads, json.dumps,
math.isfinite, math.copysign, re.fullmatch, typing.cast
~~~

The only allowed bare builtin call names are:

~~~text
all, any, bool, bytes, dict, enumerate, filter, float, int, isinstance, len,
list, map, max, min, object, range, set, sorted, str, sum, tuple, type, zip
~~~

There are no general object-method calls. The sole allowed chained call shape
is a hexdigest call on the immediate result of hashlib.sha256. The receiver
must be that exact module call. The compiler must use module-qualified calls
for AST, JSON, hashing, math, regex, and typing operations.

The scanner rejects every forbidden token, including in string constants:

~~~text
os pathlib socket subprocess urllib http ssl requests httpx torch mlx mlx_lm
transformers ctypes multiprocessing threading asyncio importlib runpy shutil
tempfile pickle marshal builtins sys resource signal platform time secrets
random uuid __import__ eval exec compile open input breakpoint help dir globals
locals vars getattr setattr delattr hasattr memoryview bytearray property super
__builtins__ __loader__ __spec__ __file__ __package__ __cached__
~~~

It also rejects every attribute whose member begins with underscore, all
non-allowlisted calls, import aliases, wildcard imports, nonzero relative
imports, f-string expressions containing calls, calls in annotations/defaults/
decorators, lambda/exec/eval/compile syntax, and any assignment or parameter
that shadows an allowed module or builtin. It walks the complete AST with
ast.walk, including nested expressions.

The scanner applies receiver binding structurally, not by spelling alone. An
allowed module call must be exactly a Call whose func is Attribute(value=Name
of one allowed module, attr=one allowed member), with no other receiver node.
The only allowed chained call is exactly a Call whose func is
Attribute(attr=hexdigest) and whose value is a Call whose func is
Attribute(value=Name(hashlib), attr=sha256). Any other Attribute node is a
forbidden_attribute, and any other Call node is forbidden_call or
forbidden_attribute_call according to whether its func is an Attribute. The
scanner walks every AST node before returning, checks every assignment target,
function parameter, comprehension target, and exception alias for shadowing,
and scans every string and identifier token for forbidden names. The scanner
itself may report only the fixed violation IDs below.

Exact source violation IDs, returned lexicographically sorted, are:

~~~text
source_type, source_utf8, source_syntax, import_module, import_alias,
relative_import, wildcard_import, forbidden_name, forbidden_attribute,
forbidden_call, forbidden_attribute_call, dynamic_import, dynamic_code,
shadowed_allowlist_name, compiler_io_surface
~~~

The scanner returns no source text, AST dump, name, literal, or path. This is a
negative-capability audit, not a proof against arbitrary Python implementation
bugs; the claim ceiling remains the V3 local audit ceiling.

## Canonical JSON parser contract

The parser is shared by the compiler and independent validator as an exact
algorithm:

1. Require type(value) is bytes before decoding.
2. Decode strict UTF-8 and reject a BOM.
3. Call json.loads with an object-pairs hook that rejects duplicate keys at
   every depth, a parse_int hook that rejects tokens beginning with -0, a
   parse_float hook that rejects finite zero from tokens beginning with -0,
   and a parse_constant hook that always rejects.
4. Require the top-level value to be an object.
5. Recursively reject non-finite floats, negative zero, control code points
   U+0000 through U+001F and U+007F, unknown keys, missing keys, wrong types,
   and invalid list cardinalities.
6. Serialize exactly with ensure_ascii false, sort_keys true, separators
   comma/colon, and allow_nan false, then UTF-8 encode.
7. Require canonical bytes to equal input bytes.
8. Apply the fixed error precedence and return only its first failure ID.

The exact error precedence is:

~~~text
bytes_type, utf8, bom, duplicate_key, constant, top_level_type,
negative_zero, non_finite, control_character, canonical_bytes,
unknown_key, missing_key, type_mismatch, cardinality, enum_value,
no_execution_value, no_assessment_value, no_power_value, corpus_reuse,
regex_value, cross_field, authorization_state, supplied_digest_format,
contract_digest_mismatch, artifact_digest_mismatch, source_capability,
sequence_gap, sequence_duplicate, state_binding, digest_binding,
payload_digest, event_order, timestamp_order, forbidden_transition,
payload_schema, event_state, lock_state, lock_schema, retention_state,
classification_state, fixture_state
~~~

Scalar grammar is exact:

~~~text
D: string matching ^[0-9a-f]{64}$
U: string matching ^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$
I(a,b): type int and a <= value <= b
F(a,b): type float, finite, and a <= value <= b
B: type bool
S: nonempty Unicode string without a control character
ID: ASCII [A-Za-z0-9._-]{1,128}, excluding . and ..
REL: repository-relative POSIX string, no leading slash, backslash, empty,
     dot, dot-dot, or control component
ABS: one-leading-slash POSIX string, not //, with no backslash, empty, dot,
     dot-dot, or control component
timestamp: YYYY-MM-DDTHH:MM:SSZ with calendar/range validation
id_list: sorted list with cardinality 0 through 56 of ID values; each field
         declares its exact cardinality separately
~~~

A boolean never satisfies I or F. Lists are ordered and their cardinality is
part of the digest.

## Complete recursive contract schema

The contract JSON top-level object has exactly these keys:

~~~text
schema, state_slice, execution_mode, claim_ceiling, exclusions, implementation,
actor, custody, corpus, training, estimator, reliability, power, events, lock,
retention, classification
~~~

Fixed values are:

~~~yaml
schema: continual-learning-contract-compiler-v3
state_slice: continual-learning-contract-compiler-negative-capability-v3
execution_mode: NO_MODEL_NO_CORPUS_NO_TRAINING
claim_ceiling: LocalDevelopmentContractCompilerNegativeCapabilityAuditV3
~~~

Schema notation: O means an object with exactly listed keys; L[n,T] means a
list of exactly n values of T; E means an exact enum. Every unlisted key is
forbidden.

~~~text
exclusions = O{prior_slices:L[5,EXCLUSION]}
EXCLUSION = O{state_slice:ID, protocol_sha256:D,
               status:E[CLOSED_PROTOCOL_REJECTED]}
implementation = O{
 module:REL, tests:REL, validator:REL, source_input:E[bytes],
 function:E[compile_audit_bundle], allowed_imports:L[6,ID],
 allowed_builtins:L[24,ID], allowed_attribute_calls:L[9,S],
 io_policy:E[PURE_IN_MEMORY_NO_FILESYSTEM_NO_NETWORK_NO_PROCESS],
 harness_input_schema:L[10,ID],
 runner_command:E[FIXED_ISOLATED_PYTHON3_INVOCATION]
}
actor = O{
 role:E[FUTURE_EXECUTION_ACTOR], name:ID,
 model_manifest_sha256:D, runtime_manifest_sha256:D,
 source_manifest_sha256:D, device:ID, execution_allowed:E[false]
}
custody = O{
 root:ABS, volume_uuid:U, mode:E[0700],
 root_precondition:E[ABSENT_BEFORE_ACQUISITION],
 write_policy:E[WRITE_ONCE_EXCEPT_EVENTS], manifest_sha256:D,
 execution_allowed:E[false]
}
corpus = O{
 identity:E[NOT_APPLICABLE_UNTIL_SEPARATE_AUTHORIZATION],
 status:E[NOT_ACQUIRED], source_policy:E[NO_SOURCE_READ],
 normalization:E[NOT_APPLICABLE], split_policy:E[NOT_APPLICABLE],
 prior_manifest_set:L[0,ID]
}
training = O{
 base_weights_updated:E[false], adapter_merge:E[false], fine_tune_type:E[NONE],
 iterations:I(0,0), rows:I(0,0), batch_size:I(0,0), num_layers:I(0,0),
 learning_rate:F(0.0,0.0), mask_prompt:E[false],
 command_digest:D, network_access:E[false]
}
estimator = O{
 primary:E[contract_audit_only], secondary:E[not_applicable],
 threshold:F(0.0,0.0), bootstrap:E[NONE], positive_case_count:E[0_OF_0],
 assessment_guard:E[NO_ASSESSMENT], missingness:E[REJECT_NO_IMPUTATION]
}
reliability = O{
 process_repeats:I(3,3), deterministic:E[true],
 aggregate_digest_tolerance:I(0,0),
 independence:E[THREE_FRESH_OS_PROCESSES_SAME_COMMAND_ENVIRONMENT],
 process_command:E[FIXED_ISOLATED_PYTHON3_INVOCATION],
 environment:E[EMPTY_ENV_C_UTF8_UTC_HASHSEED_0]
}
power = O{
 simulations:I(0,0), null_mu:F(0.0,0.0), alternative_mu:F(0.0,0.0),
 alternative_min:F(0.0,0.0), null_max:F(0.0,0.0),
 hash_grammar:E[NOT_APPLICABLE_CONTRACT_AUDIT_ONLY]
}
~~~

The required ordered exclusion values are:

~~~yaml
- state_slice: continual-learning-contract-compiler-negative-capability-v1
  protocol_sha256: ed57e6c43a18c4d24b4e45e0c70893030afb7e32c61fbacb41e5bb950c7b1648
  status: CLOSED_PROTOCOL_REJECTED
- state_slice: continual-learning-contract-compiler-negative-capability-v2
  protocol_sha256: aa8ba5ef32ec9292e3a3a82381d44c5b67594e56858cf38a26c7705c06f9ed2a
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
~~~

The exact values for implementation are:
module experiments/continual_learning/contract_compiler_negative_capability_v3.py;
tests experiments/continual_learning/tests/test_contract_compiler_negative_capability_v3.py;
validator experiments/continual_learning/validate_contract_compiler_negative_capability_v3.py;
source_input bytes; function compile_audit_bundle; allowed imports and
builtins are the lists above; allowed attribute calls are the nine module calls
above; io_policy PURE_IN_MEMORY_NO_FILESYSTEM_NO_NETWORK_NO_PROCESS;
harness_input_schema is the exact ten argument names of compile_audit_bundle;
runner_command is FIXED_ISOLATED_PYTHON3_INVOCATION.

The exact actor requirements are role FUTURE_EXECUTION_ACTOR, name/device ID,
three D values, and execution_allowed false. The exact custody requirements
are a non-root ABS root, U, mode 0700, ABSENT_BEFORE_ACQUISITION,
WRITE_ONCE_EXCEPT_EVENTS, D manifest, and false. These are contract bindings
only; V3 cannot assert path, permission, volume, model, runtime, or provider
existence.

## Events, lock, retention, and classification

events is exactly:

~~~text
O{
 sequence_origin:I(0,0),
 line_keys:L[7,E[sequence|event|timestamp|state_slice|contract_sha256|payload|payload_sha256]],
 order:L[9,E[protocol_review_accepted|implementation_authorized|audit_started|
   contract_digest_verified|contract_schema_validated|source_capability_scan_completed|
   fixtures_completed|aggregate_receipt_sealed|audit_completed]],
 payload_schemas:PAYLOAD_SCHEMAS,
 assessment_transition:E[FORBIDDEN_NO_ASSESSMENT_EVENT],
 event_log_sha256:D,
 event_log_input:E[CANONICAL_JSON_OBJECT_EVENTS_LIST]
}
~~~

PAYLOAD_SCHEMAS is an object with exactly the nine event names. Each value is
an ordered list of exact field specifications
O{name:ID,type:E[bool|int|sha256|string|timestamp|enum|id|id_list],
enum_values:L[0..9,S]}. The enum_values list is empty for non-enum types and
is the exact allowed-value list for enum types. The exact payload field
specifications, including their types and enum values, are:

~~~text
protocol_review_accepted: review_sha256:sha256, reviewer_role:id,
  verdict:enum[ACCEPT]
implementation_authorized: authorization_sha256:sha256,
  execution_authorized:bool[false]
audit_started: validator_identity:id, validator_sha256:sha256
contract_digest_verified: recomputed_contract_sha256:sha256,
  supplied_contract_sha256:sha256
contract_schema_validated: schema_version:enum[continual-learning-contract-compiler-v3],
  top_level_key_count:int[17]
source_capability_scan_completed: source_sha256:sha256,
  violation_ids:id_list, passed:bool
fixtures_completed: fixture_count:int[56], failed_fixture_ids:id_list, passed:bool
aggregate_receipt_sealed: receipt_sha256:sha256,
  retained_field_names:id_list
audit_completed: classification:enum[ProtocolRejectedBeforeAudit|ContractAuditFailure|
  ContractAuditPass], claim_ceiling:enum[LocalDevelopmentContractCompilerNegativeCapabilityAuditV3],
  terminal:bool[true]
~~~

Each event record is exactly O{sequence:I(0,8), event:enum, timestamp:timestamp,
state_slice:ID, contract_sha256:D, payload:object, payload_sha256:D}. Sequence
is contiguous, event names equal order, timestamps are strictly increasing
UTC seconds, and payload hashes are recomputed from canonical payload bytes.
The event-log hash is recomputed from canonical JSON. Every predecessor is
required before its successor. Any assessment event is forbidden.

lock is exactly:

~~~text
O{
 filename:E[not-applicable-v3.lock.json],
 write_policy:E[WRITE_ONCE], assessment_started:E[false],
 required_fields:L[9,ID],
 canonical_digest:E[V3_CANONICAL_JSON_SHA256],
 review_binding:E[REVIEW_SHA256_MUST_EQUAL_RECOMPUTED_REVIEW_SHA256],
 input_bindings:O{
   protocol_sha256:D, contract_sha256:D, source_sha256:D,
   review_sha256:D, authorization_sha256:D, event_log_sha256:D,
   retention_sha256:D, fixture_matrix_sha256:D
 },
 sealed:E[false]
}
~~~

The exact lock field list is:
protocol_sha256,contract_sha256,source_sha256,fixture_matrix_sha256,
validator_identity,review_sha256,classification,claim_ceiling,
execution_authorized. Every input binding is recomputed from the corresponding
explicit byte input. This lock cannot represent an assessment prediction lock.

retention is exactly:

~~~text
O{
 deadline:E[2026-09-05T00:00:00Z],
 source_validator_phase:E[BEFORE_CLEANUP],
 aggregate_validator_phase:E[AFTER_CLEANUP],
 retained_fields:L[7,ID], deleted_fields:L[11,ID],
 deletion_evidence:O{
   actor:ID, timestamp:timestamp, deleted_digest:D, event_sequence:I(0,8)
 },
 execution_data_present:E[false]
}
~~~

The exact retained list is:
classification,claim_ceiling,contract_sha256,source_sha256,fixture_ids,
gate_booleans,receipt_digests.
The exact deleted list is:
contract_bytes,source_bytes,fixture_inputs,raw_text,token_ids,logits,
activations,adapter_tensors,training_data,training_logs,per_window_outputs.
The validator proves output-key closure and absence of every deleted field in
aggregate receipts, nested payloads, exception text, and diagnostics. V3 makes
no external deletion claim.

classification is exactly:

~~~text
O{
 protocol_rejected:E[ProtocolRejectedBeforeAudit],
 audit_failure:E[ContractAuditFailure],
 audit_pass:E[ContractAuditPass],
 precedence:E[PROTOCOL_REJECTED_THEN_AUDIT_FAILURE_THEN_AUDIT_PASS],
 receipt_binding:O{
   algorithm:E[RECOMPUTE_FINAL_CLASSIFICATION_AND_RECEIPT_SHA256],
   fields:L[4,ID]
 }
}
~~~

The exact receipt-binding fields are:
classification,claim_ceiling,execution_authorized,gate_booleans.
No ACCEPT review yields ProtocolRejectedBeforeAudit. ACCEPT plus any failed
gate yields ContractAuditFailure. ACCEPT plus all gates and independent receipt
recomputation yields ContractAuditPass. execution_authorized is always false.

## Review, authorization, and artifact schemas

The review receipt is canonical JSON with exactly:

~~~text
O{
 state_slice:ID, reviewed_protocol_sha256:D, reviewed_packet_sha256:D,
 reviewer_role:ID, verdict:E[ACCEPT|REJECT],
 findings:L[13,O{
   id:ID, severity:E[critical|major|minor],
   requirement:I(1,13), disposition:E[pass|fail|limitation], evidence:S
 }],
 execution_authorized:E[false], review_timestamp:timestamp
}
~~~

The authorization receipt is canonical JSON with exactly:

~~~text
O{
 state_slice:ID, protocol_sha256:D, review_sha256:D,
 implementation_authorized:E[true], execution_authorized:E[false],
 authorized_files:L[3,REL], authorization_timestamp:timestamp
}
~~~

The seven JSON artifact byte inputs have exact top-level envelopes. There are
no wrapper keys beyond these definitions:

~~~text
review_receipt_bytes = the exact review object above
authorization_receipt_bytes = the exact authorization object above
event_log_bytes = O{events:L[9,EVENT_RECORD]}
lock_bytes = the exact lock object above
retention_bytes = the exact retention object above
fixture_matrix_bytes = the exact fixture matrix object below
contract_bytes = the exact contract object above
~~~

EVENT_RECORD is the exact event record defined above, including its payload
object and payload_sha256. The compiler receives all ten inputs positionally,
parses each JSON byte input with the shared canonical parser, recomputes each
artifact hash from the supplied bytes, and compares it to the contract's
binding. The artifact hash is a schema binding, not proof of external custody.

## Exact fixture bundle

fixture_matrix_bytes is canonical JSON with exactly:

JSON_PATH is an ASCII string matching
^\\$(\\.[A-Za-z_][A-Za-z0-9_]*|\\[[0-9]+\\])*$. It may be the root path $.
Each fixture applies exactly one mutation to one explicit byte artifact at one
JSON_PATH.

~~~text
O{
 schema:E[contract-compiler-fixture-matrix-v3],
 base_bundle_sha256:D,
 fixture_count:I(56,56),
 fixtures:L[56,O{
   id:E[P01|P02|P03|P04|P05|P06|P07|P08|P09|P10|P11|P12|P13|P14|P15|P16|P17|P18|P19|P20|P21|P22|P23|P24|P25|P26|P27|P28|P29|P30|P31|P32|P33|P34|P35|P36|P37|P38|P39|P40|P41|P42|P43|P44|P45|P46|P47|P48|P49|P50|P51|P52|P53|P54|P55|P56],
   artifact:E[contract|source|review|authorization|events|lock|retention],
   operation:E[replace|insert|delete|reorder|type_change|byte_change|source_snippet],
   path:JSON_PATH,
   replacement:S,
   expected_failure:E[pass|cross_field|unknown_key|missing_key|type_mismatch|no_execution_value|enum_value|corpus_reuse|regex_value|cardinality|no_assessment_value|no_power_value|sequence_gap|sequence_duplicate|state_binding|digest_binding|payload_digest|event_order|timestamp_order|forbidden_transition|payload_schema|lock_state|lock_schema|retention_state|classification_state|source_capability|shadowed_allowlist_name|dynamic_code|canonical_bytes|duplicate_key],
   expected_classification:E[ProtocolRejectedBeforeAudit|ContractAuditFailure|ContractAuditPass],
   expected_gate_profile:E[all_true|one_false|protocol_false],
   expected_failed_fixture_ids:E[empty|self],
   expected_message:E[PRIMARY_FAILURE_ONLY]
 }]
}
~~~

The fixture list has IDs P01 through P56 in numeric order. The positive bundle
is the canonical JSON serialization of the complete contract schema with all
fixed values in this protocol, the exact source snippet in the source policy,
an ACCEPT review with exactly thirteen pass findings, a false execution
authorization, nine correctly chained events, an unsealed lock, the fixed
retention object, and the fixture matrix. The builder serializes each object,
computes all cross-artifact hashes, sets base_bundle_sha256, and then applies
exactly one listed mutation. No fixture file is read and no fixture-specific
tuning is allowed.

The aggregate output expected by each row is exact: P01 is a pass with all
gate booleans true and no failed fixture ID; P21 is
ProtocolRejectedBeforeAudit with protocol_digest false and its own fixture ID;
all other rows are ContractAuditFailure with one false gate and their own
fixture ID. expected_message is always the literal PRIMARY_FAILURE_ONLY.

The exact mutation table is:

~~~text
id artifact operation path replacement expected_failure expected_classification expected_gate_profile expected_failed_fixture_ids
P01 contract replace $.schema continual-learning-contract-compiler-v3 pass ContractAuditPass all_true empty
P02 contract replace $.state_slice other-state-slice cross_field ContractAuditFailure one_false self
P03 contract insert $.extra true unknown_key ContractAuditFailure one_false self
P04 contract delete $.actor NO_REPLACEMENT missing_key ContractAuditFailure one_false self
P05 contract type_change $.training.iterations true type_mismatch ContractAuditFailure one_false self
P06 contract replace $.training.base_weights_updated true no_execution_value ContractAuditFailure one_false self
P07 contract replace $.corpus.status ACQUIRED enum_value ContractAuditFailure one_false self
P08 contract insert $.corpus.prior_manifest_set[0] reused-manifest corpus_reuse ContractAuditFailure one_false self
P09 contract replace $.custody.root relative/path regex_value ContractAuditFailure one_false self
P10 contract replace $.actor.model_manifest_sha256 BAD regex_value ContractAuditFailure one_false self
P11 contract replace $.training.learning_rate 0 type_mismatch ContractAuditFailure one_false self
P12 contract replace $.reliability.process_repeats 2 cardinality ContractAuditFailure one_false self
P13 contract replace $.estimator.threshold 0.1 no_assessment_value ContractAuditFailure one_false self
P14 contract replace $.power.simulations 1 no_power_value ContractAuditFailure one_false self
P15 contract reorder $.exclusions.prior_slices REVERSE cross_field ContractAuditFailure one_false self
P16 contract replace $.exclusions.prior_slices[1].protocol_sha256 BAD cross_field ContractAuditFailure one_false self
P17 contract replace $.implementation.allowed_imports extra cross_field ContractAuditFailure one_false self
P18 contract delete $.implementation.harness_input_schema NO_REPLACEMENT missing_key ContractAuditFailure one_false self
P19 contract replace $.lock.assessment_started true lock_state ContractAuditFailure one_false self
P20 contract replace $.retention.execution_data_present true retention_state ContractAuditFailure one_false self
P21 review replace $.verdict REJECT pass ProtocolRejectedBeforeAudit protocol_false self
P22 review delete $.findings[11] NO_REPLACEMENT cardinality ContractAuditFailure one_false self
P23 review replace $.execution_authorized true no_execution_value ContractAuditFailure one_false self
P24 authorization replace $.execution_authorized true no_execution_value ContractAuditFailure one_false self
P25 authorization replace $.implementation_authorized false authorization_state ContractAuditFailure one_false self
P26 authorization delete $.review_sha256 NO_REPLACEMENT missing_key ContractAuditFailure one_false self
P27 events replace $.events[0].sequence 1 sequence_gap ContractAuditFailure one_false self
P28 events replace $.events[1].sequence 0 sequence_duplicate ContractAuditFailure one_false self
P29 events replace $.events[4].state_slice other-state-slice state_binding ContractAuditFailure one_false self
P30 events replace $.events[5].contract_sha256 BAD digest_binding ContractAuditFailure one_false self
P31 events replace $.events[6].payload_sha256 BAD payload_digest ContractAuditFailure one_false self
P32 events reorder $.events REVERSE event_order ContractAuditFailure one_false self
P33 events replace $.events[8].timestamp 1970-01-01T00:00:00Z timestamp_order ContractAuditFailure one_false self
P34 events replace $.events[0].event assessment_started forbidden_transition ContractAuditFailure one_false self
P35 events insert $.events[0].payload.extra other payload_schema ContractAuditFailure one_false self
P36 lock replace $.lock.input_bindings.source_sha256 BAD digest_binding ContractAuditFailure one_false self
P37 lock replace $.lock.sealed true lock_state ContractAuditFailure one_false self
P38 lock replace $.lock.required_fields extra lock_schema ContractAuditFailure one_false self
P39 retention insert $.retention.deleted_fields[0] raw_text retention_state ContractAuditFailure one_false self
P40 retention delete $.retention.deletion_evidence NO_REPLACEMENT missing_key ContractAuditFailure one_false self
P41 retention replace $.retention.execution_data_present true retention_state ContractAuditFailure one_false self
P42 contract replace $.classification.precedence other classification_state ContractAuditFailure one_false self
P43 contract replace $.classification.receipt_binding.fields other classification_state ContractAuditFailure one_false self
P44 source source_snippet $.source_snippet import os source_capability ContractAuditFailure one_false self
P45 source source_snippet $.source_snippet from os import path source_capability ContractAuditFailure one_false self
P46 source source_snippet $.source_snippet import os as os source_capability ContractAuditFailure one_false self
P47 source source_snippet $.source_snippet from . import helper source_capability ContractAuditFailure one_false self
P48 source source_snippet $.source_snippet import * source_capability ContractAuditFailure one_false self
P49 source source_snippet $.source_snippet open(\"x\") source_capability ContractAuditFailure one_false self
P50 source source_snippet $.source_snippet __import__(\"os\") source_capability ContractAuditFailure one_false self
P51 source source_snippet $.source_snippet eval(\"1\") source_capability ContractAuditFailure one_false self
P52 source source_snippet $.source_snippet object.decode() source_capability ContractAuditFailure one_false self
P53 source source_snippet $.source_snippet fake shadowed_allowlist_name ContractAuditFailure one_false self
P54 source source_snippet $.source_snippet lambda: 1 dynamic_code ContractAuditFailure one_false self
P55 contract byte_change $ trailing_space canonical_bytes ContractAuditFailure one_false self
P56 contract byte_change $ duplicate_nested_key duplicate_key ContractAuditFailure one_false self
~~~

P01 has expected_failure pass. P21 deliberately tests terminal
ProtocolRejectedBeforeAudit with expected_failure pass. P02 through P20 and
P22 through P56 have the listed first failure under fixed precedence. The
fixture validator rejects any duplicate, missing, out-of-order, unknown, or
unexpected fixture field, path, operation, replacement, expected ID,
classification, gate profile, failed-fixture profile, or expected message. It
also rejects any exception or raw-input leak.

## Aggregate receipt, runner, and gates

The compiler aggregate receipt has exactly:

~~~text
state_slice, protocol_sha256, contract_sha256, source_sha256,
fixture_matrix_sha256, validator_sha256, fixture_count, failed_fixture_ids,
gate_booleans, classification, claim_ceiling, execution_authorized
~~~

gate_booleans is an object with exactly:
protocol_digest, contract_digest, schema, source_capability, artifacts, events,
lock, retention, fixtures, repeatability, aggregate_only. Every value is bool.
A pass has all true; failure has at least one false; protocol rejection has
protocol_digest false because no accepted review is present. The receipt
contains no raw bytes, source text, fixture inputs, event payloads, exception
messages, or undeclared paths. Its canonical hash is recomputed.

The exact isolated validator command is:

~~~text
env -i PATH=/usr/bin:/bin LC_ALL=C.UTF-8 TZ=UTC PYTHONHASHSEED=0 /usr/bin/python3 -I -S experiments/continual_learning/validate_contract_compiler_negative_capability_v3.py --protocol <protocol.md> --contract <contract.json> --contract-sha256 <supplied-digest> --source <source.py> --review <review.json> --authorization <authorization.json> --events <events.json> --lock <lock.json> --retention <retention.json> --fixtures <fixtures.json>
~~~

This is one exact shell command and one exact argv vector. The angle-bracket
values are placeholders resolved only to the ten declared inputs. Additional
arguments are rejected. The validator emits one canonical
aggregate JSON receipt on stdout and no diagnostics on stderr. It imports no
compiler module and recomputes every gate.

Three fresh invocations use identical bytes, exact command, empty environment,
UTF-8 locale, UTC timezone, and PYTHONHASHSEED=0. Receipt bytes must match
exactly. Any exception, raw-input leak, mismatch, unexpected fixture result,
failed digest, or unauthorized operation is terminal ContractAuditFailure.

Post-acceptance gates, in order:

1. Recompute protocol, packet, contract, source, artifact, fixture, event,
   lock, retention, receipt, and validator digests.
2. Pass compiler and validator source-capability scans.
3. Pass all 56 fixture outcomes with fixed error precedence.
4. Pass event, lock, retention, and classification state machines.
5. Pass aggregate-key closure and raw-input exclusion.
6. Pass three fresh-process byte-identical repeats.
7. Pass independent validator recomputation.

No adaptive repair of schema, fixtures, precedence, source policy, or digest
rules is allowed after a failed gate. V3 failure is terminal
ContractAuditFailure. V3 pass remains only
LocalDevelopmentContractCompilerNegativeCapabilityAuditV3 and does not validate
external custody or GiveMeANode readiness.

V3 cannot authorize plasticity-guard replication, commit-budget matching,
cross-actor replication, restart/rollback audit, Astral, Stage 0C, Stage 1, or
V82.
