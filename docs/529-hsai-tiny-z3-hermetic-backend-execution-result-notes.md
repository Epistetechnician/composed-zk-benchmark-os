# Phase 529 HSAI Tiny Z3 Hermetic Backend Execution Result Notes

State slice: `Phase 529 HSAI tiny Z3 hermetic backend execution result`.

Phase 529 implements the local Lane A execution-result path authorized by
Phase 528. It adds a hermetic process runner for one scoped SMT/Z3 command over
one exact Phase 527 backend-execution candidate.

It also updates the HSAI claim-boundary source scan with a single Phase 529
exception for this named runner. The exception is restricted to
`run_gateway_formal_tiny_z3_hermetic_backend_execution_result` in
`crates/hsai-agent-admission/src/lib.rs` and requires the Phase 529 claim
boundary needle to remain present in source.

The valid successful classification is:

```text
LaneASmtZ3RunObservedLocalOnly
```

The result binds:

- the Phase 527 backend-execution candidate digest;
- the Phase 527 backend-execution candidate input digest;
- Phase 527 lane `LaneAScopedSmtZ3Replay`;
- Phase 527 classification `LaneAExecutionCandidateDeclaredNoRun`;
- Phase 527 obligation, toolchain, command, expected-output grammar, timeout,
  and scratch-output-root policy digests;
- the actual SMT-LIB2 text digest submitted to Z3;
- the actual executable digest;
- the fixed argv digest for `-in -smt2`;
- the working-directory policy digest;
- the empty environment digest;
- the timeout policy digest;
- the exit-code label;
- redacted stdout and stderr summary digests;
- the parsed solver verdict label.

The runner uses a caller-supplied Z3 executable path, checks its SHA-256 digest
against the request, clears the environment, pipes SMT-LIB2 through stdin, uses
bounded stdout/stderr capture, and enforces a bounded timeout. The captured
stream summaries retain digests and byte counts only, not raw solver logs.

Validation fails closed when:

- the Phase 527 candidate is not exact;
- Lane A is not the only open lane;
- any Phase 527 descriptor digest is zero;
- the request ids are invalid;
- the request executable digest is zero or does not match the executable bytes;
- the argv, working-directory, environment, or obligation binding drifts;
- the timeout or stream caps are outside the bounded policy;
- the explicit nonclaim set drifts;
- accepted evidence, Level2+ evidence, score-axis population, Lean, COBALT,
  Rust-to-Lean, benchmark evidence, external audit, strong public claims, or
  action authority are claimed.

Implemented tests cover a local Z3 run when Z3 is available, rejection of
candidate promotion drift, rejection of executable-digest drift, and the
single-function source-scan exception for the Phase 529 process path.

This phase creates a local backend execution observation only. It does not
write backend artifacts, write accepted-evidence artifacts, accept
external-result evidence, create accepted formal evidence, create Level2+
evidence, populate score axes, create proof artifacts, create checker
transcripts, create solver certificates, run Lean, run COBALT, run
Rust-to-Lean extraction, create benchmark evidence, create external-audit
evidence, prove semantic correctness, establish production readiness, establish
SOTA, establish breakthrough status, establish full security, or grant
authority to execute an action.
