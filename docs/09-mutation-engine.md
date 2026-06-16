# Mutation Engine

## Goals

The mutation engine converts a valid Benchmark Instance into valid, near-valid, malicious, or invalid Mutation Variants. Every variant must carry an Expected Verdict before any backend sees it.

## Canonical Pipeline

```text
Surface DSL
  -> parsed AST
  -> canonical semantic IR
  -> generated benchmark family
  -> concrete benchmark instance
  -> mutation variant
  -> backend artifact
  -> replay result
  -> evidence record
  -> scored report
```

## Variant Classes

- Valid variant: semantics preserved; expected_accept.
- Near-valid variant: close to valid but violates a boundary; often expected_reject or expected_inconclusive.
- Malicious variant: designed to expose unsound acceptance; expected_unsound_if_accepted.
- Invalid variant: malformed by semantic definition; expected_reject or expected_backend_error.

## Expected Verdicts

- expected_accept
- expected_reject
- expected_backend_error
- expected_inconclusive
- expected_capability_gap
- expected_unsound_if_accepted

## Oracle Interaction

The Oracle evaluates traces, transition relation, invariant satisfaction, witness policy, public/private boundary, and expected result. Backend results are compared against Oracle verdicts. Backend disagreement is evidence to triage, not automatic proof of a backend bug.

## Capability Gaps

If a backend cannot express negative tests, trace export, formal semantics, recursion, or public/private boundary checks, the adapter reports expected_capability_gap. That is not a failure, but it affects adapter portability and soundness-coverage scoring.

## False Positive Handling

A false positive candidate occurs when the Oracle expected rejection but the backend accepted, and the artifact is well-formed. It becomes an unsound-acceptance candidate until independently minimized and replayed.

## False Negative Handling

A false rejection candidate occurs when the Oracle expected acceptance but the backend rejected. It may indicate adapter encoding error, unsupported feature, malformed artifact, or backend behavior. It is not automatically semantic correctness.

## Replay Triage

Triage order:

1. Confirm mutation provenance.
2. Confirm Oracle Expected Verdict.
3. Confirm backend capability flags.
4. Confirm replay manifest and artifact hashes.
5. Classify Backend Outcome.
6. Assign Evidence Record and Claim Boundary.

## Mutation Classes

| Class | Description | Example | Expected Semantic Verdict | Expected Backend Behavior | Evidence Value | Scoring Impact | Misclassification Risk |
|---|---|---|---|---|---|---|---|
| missing constraints | Remove a required invariant or transition constraint. | Omit `acc == prior_acc + i`. | expected_unsound_if_accepted | Reject or fail negative test. | High soundness stress. | Boosts failure coverage if caught. | Backend may lack negative-test path. |
| corrupted guards | Change guard predicate. | `i < n` becomes `i <= n`. | expected_reject | Reject invalid trace. | Guard soundness. | Affects correctness and soundness. | Boundary cases need precise oracle. |
| bad counters | Skip or double increment. | `i = i + 2`. | expected_reject | Reject trace. | Loop consistency. | Failure coverage. | Counter overflow policy ambiguity. |
| stale state reads | Read old state after update. | Spend checks previous balance. | expected_unsound_if_accepted | Reject if encoded correctly. | High adversarial value. | Strong soundness signal. | Requires careful trace semantics. |
| invalid unroll bounds | Exceed declared loop bound. | Run 65 steps with bound 64. | expected_reject | Reject or backend error. | Loop bound evidence. | Failure coverage. | Backend may encode fixed unroll only. |
| nondeterministic transition injection | Add choice not in semantic relation. | Branch to unauthorized state. | expected_reject | Reject or capability gap. | Choice semantics. | Capability and soundness. | Some backends lack nondeterminism model. |
| recursion-envelope mismatch | Break depth/digest binding. | Valid proof at wrong depth. | expected_unsound_if_accepted | Reject recursion envelope. | Recursion stress. | Recursion stress score. | Recursion proof can hide semantic mismatch. |
| public/private boundary mismatch | Expose or alias private witness as public input. | `secret_nonce` aliases `public_nonce`. | expected_reject | Reject if supported. | Boundary discipline. | Risk penalty if missed. | Adapter may not expose boundary checks. |
| witness aliasing | Same witness slot satisfies distinct fields incorrectly. | Private A and B share memory. | expected_reject | Reject if supported. | Witness soundness. | Failure coverage. | Hard to express in some backends. |
| invariant weakening | Remove or weaken invariant. | `balance >= 0` omitted. | expected_unsound_if_accepted | Reject if invariant required. | Invariant evidence. | Formal evidence stress. | Weak invariant may be irrelevant. |
| invariant strengthening | Add impossible or too-strong invariant. | `i == n` at every step. | expected_backend_error or expected_reject | Reject or fail compilation. | Rejection handling. | Correctness and triage. | Could be malformed spec instead. |
| observation omission | Hide a metric or trace field required for verdict. | No final digest observed. | expected_inconclusive | Report inconclusive. | Observation model. | Penalizes reproducibility. | Backend may infer omitted data. |
| semantic no-op drift | Preserve surface shape while changing semantic effect. | Update temporary not state. | expected_reject | Reject if semantic check exists. | Semantic sensitivity. | Soundness coverage. | Needs equivalence-class definition. |
| trace ordering corruption | Swap dependent transitions. | Spend before deposit. | expected_reject | Reject invalid trace. | Trace relation evidence. | Failure coverage. | Independent transitions may commute. |

## Mutation Provenance

Every Mutation Variant records:

- source machine,
- benchmark instance,
- mutation class,
- target field/transition/loop/invariant,
- expected verdict,
- oracle rationale,
- seed,
- parent artifact hash,
- claim boundary max.

## Local v0 Implementation Status

Implemented locally in Phase D/E:

- missing constraints: selects an eligible rejected-trace transition and replaces a non-trivial guard with `true`.
- corrupted guards: selects an eligible accepted-trace transition and deterministically flips an executable guard form such as `eq`/`neq` or `lt`/`lte`.
- bad counters: selects an eligible accepted-trace counter action and deterministically changes the integer update amount.

All other mutation classes remain future implementation work:

- stale state reads,
- invalid unroll bounds,
- nondeterministic transition injection,
- recursion-envelope mismatch,
- public/private boundary mismatch,
- witness aliasing,
- invariant weakening,
- invariant strengthening,
- observation omission,
- semantic no-op drift,
- trace ordering corruption.

The v0 engine records mutation provenance, expected verdict, safety class, affected transition ids, affected guard/action ids when available, affected field ids when available, claim boundary, and notes. It revalidates the mutated Surface DSL and lowers through Semantic IR. It does not generate backend artifacts.

An accepted mutated trace is an unsound acceptance candidate when paired with an expected rejection. It is not proof of exploit or proof of backend unsoundness.

## Phase K Local Soak Telemetry

Phase K records mutation application coverage and local outcome changes as internal benchmark OS telemetry only. It can count mutation variants generated, mutation no-target events, local replay outcomes, and failure corpus entries for regression detection.

Mutation coverage counts are not soundness proofs. Unsound acceptance candidates remain candidates, not proven exploits. Local soak telemetry is not official benchmark evidence. Internal timing telemetry is not ZK backend performance.
