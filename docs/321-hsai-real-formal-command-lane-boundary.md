# Phase 321 HSAI Real Formal Command Lane Boundary

State slice: `Phase 321 HSAI real formal command lane boundary`.

## Scope

Phase 321 defines the docs-first boundary for the first real formal command
lane after the Phase 319/320 local fixture execution readback lane.

This phase does not add Rust code, package runtime files, solver scripts,
checker scripts, proof assistant setup files, command execution, proof
artifacts, checker transcripts, solver certificates, accepted evidence, Level2+
evidence, score axes, or proof-authority claims.

## Backend Choice

The first real command lane is:

```text
local_smt_tiny_gateway_invariant
```

The first backend mode is:

```text
smt-lib2-offline-command
```

This is the smallest responsible crossing because the existing Phase 303-320
sequence already built a local SMT-style lane, hermetic command policy,
quarantine readback, and negative coverage around that lane.

Lean and COBALT remain deferred:

- Lean/Rust-to-Lean requires a separate extraction/source-correspondence
  boundary before any theorem can be trusted.
- COBALT requires a separate source/toolchain reproduction boundary before any
  containment result can be treated as local evidence.
- Neither Lean nor COBALT may be invoked by the first command-lane
  implementation.

## First Property

The first property is:

```text
attestation_challenge_binding_deterministic_input_sensitive
```

The command lane may check only a tiny, hand-authored SMT-LIB2 obligation over
the Phase 317 non-secret fixture values:

- identical normalized inputs produce the same binding label;
- changed proposal digest changes the binding label;
- changed nonce changes the binding label;
- all imported `report_data_binding` assumptions remain explicit;
- no provider attestation claim is made;
- no gateway-wide semantic-correctness claim is made.

The command lane must not claim to prove the Rust implementation, the
attestation provider, the admission gateway, HSAI as a whole, or any external
system semantics.

## Future Input Contract

A future implementation may consume only these local, non-secret inputs:

- Phase 317 adapter request.
- Phase 317 fixture input.
- Phase 317 command descriptor metadata.
- Phase 317 source adapter output manifest.
- Phase 319 execution output manifest.
- Phase 319 execution transcript.
- Phase 320 readback-hardening assumptions.
- One static SMT-LIB2 obligation file or in-memory obligation string.
- One static expected-output grammar.
- Caller-supplied run id and created-at timestamp.
- Explicit operator acknowledgement.

The future implementation must reject:

- missing Phase 317 source manifest readback;
- missing Phase 319 execution manifest readback;
- missing operator acknowledgement;
- secrets or credentials;
- raw provider payloads;
- raw quotes;
- network endpoints;
- absolute source paths in semantic fields;
- shell fragments;
- inherited environment;
- stdin;
- mutable accepted Evidence Ledger paths;
- benchmark output paths;
- score-axis output paths;
- proof-promotion paths.

## Future Command Contract

A future implementation may define exactly one command descriptor for this
lane:

```text
backend_id = local_smt_tiny_gateway_invariant
backend_mode = smt-lib2-offline-command
command_kind = direct_process_no_shell
input_kind = static_non_secret_smt2_obligation
output_kind = bounded_solver_stdout_stderr
```

The future command descriptor must require:

- fixed executable policy;
- fixed argv template;
- no caller-supplied executable path;
- no caller-supplied argv;
- no shell;
- no stdin;
- no inherited environment;
- empty or explicit allowlist environment only;
- no network;
- timeout in milliseconds;
- maximum stdout bytes;
- maximum stderr bytes;
- ignored output root only;
- declared input digest binding;
- declared obligation digest binding;
- declared expected-output grammar digest binding.

## Artifact Grammar

A future command-lane output bundle must declare exactly one local namespace:

```text
gateway-formal-real-command-lane/
```

The future declared files must be:

```text
gateway-formal-real-command-lane/manifest.json
gateway-formal-real-command-lane/source-execution-manifest.json
gateway-formal-real-command-lane/command-request.json
gateway-formal-real-command-lane/command-descriptor.json
gateway-formal-real-command-lane/obligation.smt2
gateway-formal-real-command-lane/obligation-binding.json
gateway-formal-real-command-lane/execution-transcript.json
gateway-formal-real-command-lane/stdout-summary.json
gateway-formal-real-command-lane/stderr-summary.json
gateway-formal-real-command-lane/solver-verdict.json
gateway-formal-real-command-lane/checker-transcript.json
gateway-formal-real-command-lane/redaction-report.json
gateway-formal-real-command-lane/nonpromotion-report.json
gateway-formal-real-command-lane/nonclaims.md
gateway-formal-real-command-lane/validation-report.json
```

Every declared file must have a `.sha256` sidecar. Any undeclared file or
directory must be rejected.

## Checker Transcript Grammar

The first checker transcript is not a proof artifact and not accepted evidence.
It is a bounded local transcript that records only:

- schema version;
- run id;
- backend id;
- backend mode;
- property id;
- command descriptor digest;
- obligation digest;
- expected-output grammar digest;
- process exit code label;
- timeout flag;
- solver status label;
- solver verdict label;
- stdout summary digest;
- stderr summary digest;
- redaction report digest;
- nonpromotion report digest;
- imported assumptions;
- explicit nonclaims;
- claim boundary.

The first checker transcript must not retain:

- raw solver trace;
- raw prover log;
- raw checker log;
- proof artifact;
- solver certificate as evidence;
- accepted evidence file;
- Level2+ evidence file;
- benchmark output;
- score-axis output;
- provider response;
- credential;
- secret.

## Solver Verdict Labels

The first implementation may use only these labels:

```text
not_run
process_exited
process_failed
process_timed_out
solver_unsat_without_certificate
solver_sat_witness_without_certificate
solver_unknown
output_unparseable
```

`solver_unsat_without_certificate` may not be promoted to semantic correctness
or accepted formal evidence. It is local command output only until a future
certificate/checker boundary exists and runs.

## Readback Rules

The future readback implementation must fail closed on:

- missing declared files;
- missing sidecars;
- stale sidecars;
- undeclared files;
- undeclared directories;
- symlink output root;
- symlink bundle directory;
- symlink declared file;
- symlink sidecar;
- malformed declared JSON;
- obligation digest drift;
- command descriptor drift;
- source execution manifest drift;
- transcript digest drift;
- stdout summary drift;
- stderr summary drift;
- solver verdict drift;
- checker transcript drift;
- redaction report drift;
- nonpromotion report drift;
- nonclaim drift;
- raw-log retention;
- solver-certificate promotion;
- proof-artifact promotion;
- checker-transcript promotion;
- accepted Evidence Ledger mutation;
- Level2+ evidence flags;
- score-axis flags;
- benchmark evidence flags;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- action-authority claims.

## Evidence Meaning

This phase can support only this claim:

```text
HSAI has a documented boundary for a future real SMT-LIB2 command lane for one tiny gateway invariant.
```

A future successful command run may support only this bounded claim:

```text
One local SMT-style command ran under a hermetic policy for one tiny encoded gateway invariant, and its bounded output was quarantined and read back without claim escalation.
```

It would not mean:

- HSAI is SOTA;
- HSAI is fully secure;
- HSAI proves semantic correctness;
- HSAI is production ready;
- HSAI has accepted formal evidence;
- HSAI has Level2+ formal evidence;
- HSAI has backend score axes;
- Lean proof exists;
- COBALT containment proof exists;
- Rust-to-Lean extraction succeeded;
- proof artifacts are accepted evidence;
- checker transcripts are accepted evidence;
- solver certificates are accepted evidence;
- source correspondence is proven;
- accepted Evidence Ledger state changed;
- authority to execute an action exists.

## Required Future Tests

A future implementation must include focused tests for:

- valid command descriptor construction;
- missing operator acknowledgement rejection;
- source Phase 317 manifest drift rejection;
- source Phase 319 manifest drift rejection;
- shell-fragment rejection;
- inherited-environment rejection;
- stdin rejection;
- network-enabled rejection;
- caller executable rejection;
- caller argv rejection;
- protected output-root rejection;
- explicit overwrite behavior;
- timeout classification;
- solver nonzero exit classification;
- stdout summary bounding;
- stderr summary bounding;
- malformed solver output classification;
- stale sidecar rejection;
- malformed declared JSON rejection;
- symlink root rejection;
- symlink bundle-directory rejection;
- symlink declared-file rejection;
- symlink sidecar rejection;
- obligation digest drift rejection;
- transcript semantic drift rejection;
- solver verdict drift rejection;
- checker transcript drift rejection;
- redaction drift rejection;
- nonpromotion drift rejection;
- undeclared proof-artifact rejection;
- undeclared checker-log rejection;
- undeclared accepted-evidence file rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation code;
- Cargo metadata changes;
- package runtime files;
- command execution;
- process spawning;
- backend runner implementation;
- solver scripts;
- checker scripts;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean execution;
- SMT/Z3 execution;
- COBALT execution;
- Aeneas/Hax/rust-lean execution;
- Coq/TLA+/CBMC/model-checker execution;
- generated proof artifacts;
- generated checker transcripts;
- generated solver certificates;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- official benchmark submission;
- live provider calls;
- credential handling;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- authority to execute an action.

## Validation

Required validation for this docs-first boundary:

```text
cargo fmt --all -- --check
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

Phase 322 may implement only an inert Rust data model and declared output
contract for this real SMT command lane. It may not run a real solver command
until the data model, output grammar, readback drift tests, and source-scan
exception are complete and reviewed.
