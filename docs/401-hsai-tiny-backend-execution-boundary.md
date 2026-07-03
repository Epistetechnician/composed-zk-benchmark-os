# Phase 401 HSAI Tiny Backend-Execution Boundary

State slice: `Phase 401 HSAI tiny backend-execution boundary`.

Phase 401 opens a docs-first boundary for the first post-400 backend-execution
step. The only future property in scope is deterministic digest-binding
replay for one local HSAI gateway metadata record. The future backend run may
check that a fixed input digest, explicit nonclaim digest, and current accepted
append blocker digest recompute to the expected local record digest under a
declared deterministic rule.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, mutate the accepted Evidence Ledger, change accepted
append policy, create accepted formal evidence, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, run Lean, run SMT, run COBALT, run Rust-to-Lean
extraction, submit benchmarks, claim semantic correctness, claim production
readiness, claim SOTA, claim breakthrough status, claim full security, or grant
authority to execute an action.

## Future Tiny Property

The future backend-execution slice may target only:

`gateway-local-digest-binding-determinism-v1`

The property is intentionally narrow:

Given a fixed local metadata record, a fixed input digest, a fixed explicit
nonclaim digest, and a fixed accepted-append blocker digest, the checker must
confirm that the declared digest-binding tuple is stable under deterministic
serialization and rejects drifted digests.

The property is not semantic correctness for HSAI. It is not proof that the
metadata is meaningful. It is not proof that the gateway is secure. It is not
accepted evidence.

## Future Backend Lanes

A future implementation may prepare at most these local lanes:

- `smt-z3-local`: a local SMT/Z3 check for equality and drift rejection over
  the digest tuple;
- `lean-local-skeleton`: a local Lean proof/checker skeleton for the same
  tuple if Lean is installed and explicitly detected;
- `cobalt-local-skeleton`: a COBALT-inspired local containment lane only if a
  concrete local checker exists; otherwise it must record `unavailable`.

No future implementation may fetch tools from the network, clone external
repos, vendor source, require credentials, or treat a missing tool as proof.

## Required Future Inputs

A future backend-execution implementation must bind:

- one selected local metadata record digest;
- one selected local metadata input digest;
- one explicit nonclaim digest;
- one current accepted append blocker digest;
- one declared backend lane id;
- one declared backend executable identity or explicit unavailable status;
- one hermetic command descriptor;
- one deterministic expected-verdict descriptor;
- one output quarantine descriptor.

## Required Future Outputs

A future run may emit only quarantined local execution evidence:

- backend-run request metadata;
- backend availability status;
- command descriptor digest;
- stdout/stderr summary digests;
- checker verdict metadata;
- nonpromotion report;
- explicit nonclaims.

The run must not append to the accepted Evidence Ledger, create Level2+
evidence, populate score axes, or change public claims.

## Required Future Validation

A future validator must reject the run if:

- the state slice is not the future implementation state;
- the selected property id is not `gateway-local-digest-binding-determinism-v1`;
- any required digest is missing, zero, extra, or drifted;
- backend availability is claimed without executable identity;
- a missing backend is treated as success;
- stdout/stderr summaries contain secrets or promotion text;
- the result attempts accepted append;
- the result mutates the accepted Evidence Ledger;
- the result creates accepted formal evidence;
- the result creates Level2+ evidence;
- the result populates score axes;
- the result claims semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority.

## Phase 402 Exit Criteria

Phase 402 may implement a hermetic local backend-execution preparation and
availability probe for this one property only if it:

- names the selected backend lane;
- records missing tools as unavailable, not success;
- writes only local quarantined metadata if artifact writes are explicitly
  authorized in Phase 402;
- keeps accepted evidence blocked;
- keeps Level2+ evidence blocked;
- keeps score axes blocked;
- keeps all public strong claims blocked.
