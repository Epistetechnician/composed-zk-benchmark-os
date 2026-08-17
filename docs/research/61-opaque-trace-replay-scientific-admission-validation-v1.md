# OpaqueTraceReplay Scientific Admission Validation V1

State slice: `research-synthesis-trace-replay-v1-scientific-admission-validation`.

Status: `Executed / LocalSyntheticAdmissionControlValidated`.

## Question

Does the paper-derived HSAI control boundary provide measurable local utility
against the ten synthetic `OpaqueTraceReplay` mutations? The validation tests
whether independently implemented typed admission preserves the valid case,
rejects or quarantines mutations, prevents unauthorized transition attempts,
and agrees with the frozen semantic oracle.

This is a validation of a local control hypothesis. It is not a reproduction of
the paper's provider attack and does not establish provider cryptography,
provider vulnerability, HSAI security, or faithful trace recovery.

## Frozen design

- corpus: all ten frozen `OpaqueTraceReplay` variants;
- positive control: `valid_same_session`;
- negative cases: the nine replay, ordering, injection, secret, stale, and
  malformed variants;
- unsafe arm: raw-output passthrough that accepts every candidate and attempts
  every state transition;
- typed arm: independently implemented context, predecessor, model, freshness,
  nonce, payload-risk, schema, digest, retention, and claim-boundary checks;
- oracle: existing variant-owned expected verdict and quarantine status;
- authority rule: neither arm may represent accepted Evidence Ledger state; the
  unsafe arm intentionally models the forbidden authority bypass only as a
  local control baseline;
- retention: metadata-only synthetic candidates; no payload, trace text,
  secret, credential, PII, provider signature, or model execution.

## Metrics and gates

The typed arm passes if it has:

- `1/1` valid-case acceptance;
- `0/9` false accepts;
- `6/6` quarantine matches;
- `10/10` semantic-oracle matches;
- `0` authority leaks;
- exactly `1` transition attempt, for the valid pending-review case.

The unsafe arm is a required negative control. It must expose the expected
failure surface: `9` false accepts, `10` authority leaks, and `10` transition
attempts. These are simulation metrics, not production measurements.

## Result

The Rust integration test executed the complete ten-case matrix and passed all
three tests:

| Metric | Typed arm | Raw-output passthrough control |
|---|---:|---:|
| Cases | 10 | 10 |
| Valid accepts | 1 | 1 |
| False accepts | 0/9 | 9/9 |
| Quarantine matches | 6/6 | 0/6 |
| Semantic matches | 10/10 | 1/10 |
| Authority leaks | 0 | 10 |
| Transition attempts | 1 | 10 |

## Claim ceiling and limitations

Maximum claim: `LocalSyntheticAdmissionControlValidated`.

This establishes only that the local typed policy distinguishes the frozen
synthetic mutations under its declared oracle. It does not establish complete
security, production readiness, provider mitigation, cryptographic correctness,
generalization beyond the ten cases, or authority to mutate governed state.
It does not alter V25, V26, V28, V29, Stage 0C, Stage 1, or the Evidence Ledger.
