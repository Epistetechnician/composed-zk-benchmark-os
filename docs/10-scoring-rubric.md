# Scoring Rubric

## Purpose

The Score Report separates performance, correctness, soundness-failure detection, recursion stress, formal evidence, reproducibility, portability, and risk. A single aggregate score is optional and dangerous.

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

## Score Axes

| Axis | Inputs | Output | Notes |
|---|---|---|---|
| performance score | prover time, verifier latency, proof size, memory use, constraint count | normalized speed/resource score | Missing metrics lower confidence, not necessarily score. |
| correctness score | expected_accept cases and backend accepted outcomes | acceptance alignment score | Backend acceptance is not proof. |
| soundness-failure detection score | expected_reject and expected_unsound_if_accepted cases | negative-test coverage score | Performance without negative tests is incomplete. |
| recursion stress score | recursion depth, envelope checks, proof size | recursion-specific score | Recursion proof is not semantic proof. |
| formal evidence score | formal statement, proof status, scope | scoped evidence score | Machine-checked proof must be scoped. |
| reproducibility score | replay manifest, artifact hashes, deterministic seed | reproducibility confidence | Local replay is not official benchmark evidence. |
| adapter portability score | capability flags and successful normalization | backend coverage score | Capability gaps are explicit. |
| risk penalty | overclaiming, unsupported features, inconclusive outcomes | penalty | Prevents weak evidence from looking strong. |

## Normalization Rules

- Normalize performance metrics per Benchmark Family and backend class.
- Do not compare unsupported metrics as zero.
- Missing data reduces confidence and may trigger capability_gap.
- Negative-test support is scored separately from performance.
- Formal evidence is capped by scope.

## Missing Data Handling

| Missing Data | Handling |
|---|---|
| Metric unsupported by backend | Record capability_gap. |
| Replay artifact hash missing | Lower reproducibility score. |
| Expected verdict missing | Reject Score Report as invalid. |
| Backend outcome inconclusive | Mark inconclusive and lower confidence. |
| Trace export unsupported | Record capability gap, do not infer semantics. |

## Capability Gap Handling

Capability gaps are not failures by themselves. They affect adapter portability, soundness coverage, and confidence. A backend that is fast but cannot run negative tests must not receive a high overall soundness score.

## Confidence Level

Confidence levels:

- low: design-only or incomplete evidence,
- medium: local replay with artifacts,
- high: reproducible benchmark artifact and deterministic replay,
- scoped-proof: machine-checked property for a specific layer,
- independent: independently reproduced evidence.

## Phase F Local Score Reports

Phase F may write a conservative `ScoreReport` into a local benchmark pack. That report is a local summary container only. It records evidence count, maximum claim boundary, missing metrics, and low confidence. It does not compute meaningful performance, recursion, formal, portability, or reproducibility scores.

`validate_score_report` rejects populated score axes at local claim boundaries, rejects non-finite or out-of-range score values outside `[0.0, 1.0]`, and rejects positive official/formal/performance claim language in score-report metadata. Negative boundary disclaimers remain valid. Local benchmark pack writing and reading apply this validator to embedded score reports.

Phase F score reports must leave these fields missing unless future evidence exists:

- prover time
- verifier latency
- proof size
- memory use
- constraint count
- recursion tolerance
- formal evidence score

Acceptable local summary data includes generated instance count, mutation variant count, replay manifest count, replay result count, evidence record count, local accepted trace count, local rejected trace count, local capability gap count, and unsound acceptance candidate count under local/mock classification.

Local replay evidence cannot produce an official performance score. A local unsound acceptance candidate is not a proven exploit.

## Phase G zk-Harness Dry-Run Metric Mappings

Phase G defines zk-Harness metric mapping schema only. zk-Harness dry-run plans do not provide performance scores.

Dry-run plans may name future metric kinds:

- prover time,
- verifier latency,
- proof size,
- memory use,
- constraint count,
- setup time,
- witness generation time.

All metric values must remain absent in Phase G. No prover, verifier, proof-size, memory, or constraint fields may be filled from dry-run plans. The performance score remains missing until validated external replay artifacts and result import validation exist.

## Phase H External Result Import Schemas

Phase H defines result import schemas, not benchmark scores. External result candidates are untrusted local review objects until a later phase validates artifact digests, provenance fields, source references, and claim boundaries.

Phase H artifacts cannot fill:

- prover time,
- verifier latency,
- proof size,
- memory use,
- constraint count,
- recursion score,
- formal evidence score.

Imported metric candidates are not trusted until validated in a later phase. Quarantined candidates must not affect official scoring. Manual handoff bundles, artifact capture contracts, provenance contracts, result import schemas, and quarantine manifests are `Level0DesignNote` artifacts. They do not provide performance scores.

## Phase I Synthetic Result Import

Phase I validates synthetic result candidates and can normalize them into pending-review drafts. It does not calculate benchmark scores.

Synthetic result candidates are not benchmark results. Evidence append proposals are not accepted evidence. Proposal ledgers are review ledgers only and must not mutate the accepted Evidence Ledger.

Phase I artifacts cannot fill:

- prover time
- verifier latency
- proof size
- memory use
- constraint count
- recursion score
- formal evidence score

Metric candidates with values must have source artifact refs and pass local validation, but they remain candidate-only metadata. Valid synthetic imports may create normalized result drafts and evidence append proposals only. Score reports must continue to represent missing performance, formal, recursion, reproducibility, and portability data unless future accepted evidence exists.

## Phase J Reviewed Proposal Acceptance

Phase J defines review decisions, evidence acceptance policies, evidence-record candidates, append previews, Level2 eligibility reports, and review ledgers. It does not calculate benchmark scores.

Evidence-record candidates are not accepted evidence. Append previews are not accepted evidence and do not mutate `EvidenceLedger`. Level2 eligibility reports are not Level2 evidence. Review ledgers are review artifacts only.

Phase J artifacts cannot fill:

- prover time
- verifier latency
- proof size
- memory use
- constraint count
- recursion score
- formal evidence score
- reproducibility score
- adapter portability score

Reviewed local-only candidates may carry `Level1LocalReplay` claim boundaries as candidate metadata only. Candidate metrics remain excluded from Score Reports. Eligibility for future Level2 review is not a Level2 score input.

## Phase K Local Soak Telemetry

Phase K internal telemetry does not fill performance score fields. Internal generation, mutation, local oracle, local replay, pack write/read, proposal-preview, and total runner durations are local engineering metrics only.

Phase K artifacts cannot fill:

- prover time
- verifier latency
- proof size
- memory use
- constraint count
- recursion score
- formal evidence score
- reproducibility score
- adapter portability score

Soak reports may inform system readiness but not benchmark scoring. Failure corpus counts do not imply backend soundness or unsoundness. Local soak telemetry is not official benchmark evidence. Internal timing telemetry is not ZK backend performance. Failure corpus entries are reproduction aids, not accepted evidence.

## Evidence And Claim Boundary Levels

- Level 0: design note only.
- Level 1: local replay evidence.
- Level 2: reproducible benchmark artifact.
- Level 3: cross-backend replay evidence.
- Level 4: formal property statement.
- Level 5: machine-checked proof for a scoped property.
- Level 6: independently reproduced evidence.

## Risk Penalty Examples

- Claiming benchmark pass as proof.
- Claiming local replay as official benchmark evidence.
- Hiding failed negative tests behind aggregate speed.
- Treating timeout as soundness failure.
- Treating recursion aggregation as semantic proof.
- Using unverified source versions.

## Aggregate Score Warning

An aggregate score may be useful for dashboards later, but it must always expose axis values and confidence. A single aggregate score must not hide weak soundness evidence.

## Mandatory Anti-Overclaiming Statements

- A benchmark pass is not proof.
- A local replay is not official benchmark evidence.
- A formal proof about one layer is not a formal proof about the full system.
- A recursion proof is not semantic proof.
- A backend rejection is not automatically semantic correctness.
- A timeout is not automatically a soundness failure.
- A successful proof is not automatically evidence that the source spec was meaningful.
- Performance without negative tests is incomplete.
- Soundness-failure detection is not the same as formal soundness.

## Optional Composite Score

If used later:

```text
composite = weighted_performance
          + weighted_correctness
          + weighted_soundness_detection
          + weighted_reproducibility
          + weighted_formal_evidence
          - risk_penalty
```

The composite must include a warning banner and cannot exceed the Claim Boundary justified by Evidence Records.
