# Information-budget frontier V1 execution record

State slice: `continual-learning-information-budget-frontier-v1`.

## Disposition

The bounded local autoresearch run is `NoCandidate`. The counterfactual
protected-subspace projection (CPSP) controller passed the locked assessment
hard guards and improved AFFU over the fixed-adapter control, but it did not
improve AFFU over the untouched base. The preregistered candidate rule
therefore rejects the mechanism as a continual-learning candidate.

This is exact-synthetic controller evidence only. It does not reopen the
closed plasticity-recovery family or the Astral V48 lane.

## Frozen execution

- Review receipt:
  `docs/research/continual-learning/132-information-budget-frontier-v1-independent-review-receipt-2026-08-29.json`
- Review packet digest:
  `15c21afea65a68ff3c971f615b01cf9c23e590f23a1490722143f9550f12cd85`
- Custody root:
  `/Users/shaanp/Documents/research-artifacts/continual-learning-information-budget-frontier-v1-20260829`
- Prediction lock digest:
  `3e378144730569d3cf70e5b876761d5a21dccdac48c09d8a103fc600f6df3773`
- Assessment digest:
  `e53fb1e5cfcfb06d7c9ae2331f4fa8b64fd4634fab31496d94ef9fd01aac0808`
- Candidate iterations: five preregistered candidates; one locked assessment.
- Selected candidate: `grid5_lr024` (`learning_rate=0.24`, `grid5` alpha grid).
- Replicate seeds: `20260841`, `20260842`, `20260843`.
- Order seeds: `6811`, `6812`, `6813`, forward and reverse.

The direct-entry runner, focused tests, and fast lint gate were corrected and
verified before execution. The run loaded no model, updated no weights, made
no provider or GiveMeANode call, and did not run Astral or ZK/PQC work.

## Locked assessment

| Arm | AFFU | Hard guards |
| --- | ---: | --- |
| Untouched base | `0.000000000000` | PASS |
| Fixed adapter | `-0.008653666003` | PASS |
| Locked CPSP frontier | `-0.008219852167` | PASS |
| Random-projection control | `-0.008424398273` | PASS |

The locked CPSP arm beat fixed cadence by `0.000433813836` AFFU units and
lost to the untouched base by `0.008219852167` AFFU units. Its maximum
positive forgetting was `0.029357344279`, maximum calibration Brier score
was `0.000062468973`, and maximum forward/reverse order delta was
`0.033368774214`; each remained below its preregistered guard.

The independent aggregate-only validator returned `validated` for
`assessment.json`. The selected candidate was not promoted because the
primary endpoint requires improvement over both untouched and fixed controls.

## Verification and claim ceiling

- Focused tests: `16 passed`.
- `pnpm --ignore-workspace run lint:fast`: PASS.
- Independent validator: PASS.
- Model loaded: no.
- Provider called: no.
- Astral integration: `not_run`.
- ZK/PQC evidence: `not_run`.
- Claim ceiling: `LocalDevelopmentInformationBudgetFrontierSyntheticOnly`.

No model-bearing, GiveMeANode, Astral, or ZK/PQC escalation is authorized by
this result. Any further continual-learning work requires a materially new
theory and estimand, a new protocol and independent review, and separate
authorization.

Every mutation in this execution record names state slice
`continual-learning-information-budget-frontier-v1`.
