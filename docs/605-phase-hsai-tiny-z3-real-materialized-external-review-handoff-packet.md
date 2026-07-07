# Phase 605 HSAI Tiny Z3 Real Materialized External Review Handoff Packet

State slice: `Phase 605 HSAI tiny Z3 real materialized external review handoff packet`.

Phase 605 defines the bounded handoff packet for taking the Phase 604 local
real-Z3 materialized accepted append result to an external operator and a human
reviewer without promoting the evidence class.

```text
Phase 604 real local Z3 materialized accepted-ledger artifact path
  + external operator reproduction instructions
  + human reviewer checklist
  -> local handoff packet contract only
```

This phase is documentation and navigation only. It does not add Rust code,
change Cargo metadata, add dependencies, add binaries, add scripts, write
operator artifacts, retain generated ledgers, import external results, mutate
the accepted Evidence Ledger, create Level2 artifacts, populate score axes,
run Lean, run COBALT, run Rust-to-Lean extraction, create proof artifacts,
create checker transcripts, create solver certificates, submit benchmarks,
or claim semantic correctness, production readiness, SOTA status, breakthrough
status, full security, global uniqueness, external audit status, or authority
to execute an action.

## Source Binding

The packet is bound to the Phase 604 focused path:

```sh
cargo test -p hsai-agent-admission \
  phase604_real_z3_unsat_result_materializes_accepted_ledger_artifact_without_claim_escalation \
  -- --nocapture
```

The expected local result remains:

```text
test tests::phase604_real_z3_unsat_result_materializes_accepted_ledger_artifact_without_claim_escalation ... ok
```

The operator must run from the repository root with Z3 available on `PATH`.
If `phase529_z3_executable()` skips because Z3 is absent, the packet is not an
external reproduction packet. It is only a failed or incomplete operator
attempt.

## Required Operator Capture

An external operator packet must report, at minimum:

- repository remote URL or source bundle identifier;
- repository commit hash;
- branch name;
- dirty status before running the command;
- operating system and architecture;
- Rust toolchain version;
- Z3 executable path;
- `z3 --version` output;
- exact command line used;
- UTC start and finish timestamps;
- process exit status;
- focused test result line;
- transcript SHA-256 digest;
- stderr SHA-256 digest, or the digest of an explicit empty stderr record;
- nonsecret operator identifier;
- acknowledgement that no secrets, credentials, or private machine identifiers
  are included;
- acknowledgement that the output remains `LocalReplay` /
  `Level1LocalReplay` unless a later import-review phase accepts otherwise.

Phase 604's focused test uses temporary output paths. This Phase 605 handoff
does not require the external operator to retain the generated local ledger
JSON artifact. Any future retained external artifact must be authorized by a
separate output-root/import-candidate phase and must bind the transcript,
command, Z3 version, source commit, and materialized ledger digest together.

## Reviewer Checklist

A human reviewer may mark the operator packet complete only if all of these are
true:

- the operator command exactly matches the Phase 604 focused command;
- the repository commit is identified;
- the pre-run dirty status is present;
- Z3 path and version are present;
- the focused Phase 604 test passed;
- the transcript digest is present and reproducible from the supplied
  transcript;
- no Level2, score-axis, Lean, COBALT, Rust-to-Lean, proof, checker
  transcript, solver-certificate, benchmark, external-audit, production,
  SOTA, semantic-correctness, full-security, or action-authority claim appears;
- any retained artifact is quarantined and explicitly not accepted evidence;
- the reviewer records a decision id, reviewer id, timestamp, and decision
  digest before any future import-candidate phase may use the packet.

The reviewer must reject the packet if any required field is missing, the
command differs, the run skipped for missing Z3, the test fails, the transcript
is edited without a matching digest update, or the packet claims stronger
evidence than `LocalReplay` / `Level1LocalReplay`.

## Nonclaims

Phase 605 does not establish independent external reproduction by itself. It
only defines the packet shape needed for an external operator and reviewer to
avoid ambiguity.

The following remain false after this phase:

- accepted formal evidence;
- accepted independent external reproduction;
- Level2+ evidence;
- populated score axes;
- Lean proof;
- COBALT containment evidence;
- Rust-to-Lean proof;
- SMT proof authority;
- proof artifact authority;
- checker transcript authority;
- solver certificate authority;
- benchmark evidence;
- external audit evidence;
- semantic correctness;
- production readiness;
- SOTA status;
- breakthrough status;
- full security;
- global software-agent uniqueness;
- authority to execute an action.

## Next Boundary

The next responsible boundary is a separate external-operator capture/import
phase that ingests one completed Phase 605 packet as quarantined evidence.
That future phase must still fail closed unless the operator transcript,
source commit, Z3 version, command, reviewer decision, and all inherited
Phase 604 nonpromotion constraints are present and digest-bound.
