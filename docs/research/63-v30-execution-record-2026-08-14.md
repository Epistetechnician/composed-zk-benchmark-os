# V30 Execution Record: Narrative–Mechanism–Verification

State slice: `astral-narrative-mechanism-verification-v30`.

Status: `Executed / LocalDevelopmentPlantedMechanismVerification`.

## Authorization and scope

This execution was authorized by the user's explicit request to run the
paper-informed narrative-versus-mechanism validation end to end. The run is
limited to the frozen planted-circuit protocol in
[V30](62-narrative-mechanism-verification-v30.md).

The slice uses only deterministic Rust test data and repository-owned code. It
does not load a model, call a provider or API, access the network, reuse V25,
V28, or V29 artifacts, collect reasoning traces, or mutate the Evidence
Ledger.

## Execution

Command:

```text
cargo test -p zkbench-core --test astral_narrative_mechanism_verification_v30 --quiet
```

Result: three tests passed; zero failed.

The test constructs a four-feature actor with planted weights
`[3,-2,0,1]`, compares narrative-only, mechanism-only, combined, and shuffled
mechanism observers, and evaluates eight held-out intervention vectors against
the actor's directly computed effects.

## Observed result

| Metric | Narrative-only | Mechanism-only | Combined | Shuffled mechanism |
| --- | ---: | ---: | ---: | ---: |
| Held-out MSE | `0.5` | `0.0` | `0.0` | `12.0` |
| Active-feature recall | `2/3` | `3/3` | `3/3` | not promoted |

Narrative/mechanism active-feature Jaccard was `0.5`. The mechanism object
therefore recovered the planted active support and predicted the held-out
effects exactly in this deterministic local circuit; the plausible narrative
and shuffled mechanism did not.

## Validation and disposition

- Focused V30 tests passed.
- The V30 test passed `rustfmt --check`.
- The repository claim-boundary test and full `zkbench-core` suite passed.
- The result is local planted-circuit evidence for separating narrative from
  measured mechanism in a known causal system.
- Maximum defensible claim remains
  `LocalDevelopmentPlantedMechanismVerification`.

This result does not establish mechanistic faithfulness in a trained model,
held-out real-model intervention prediction, Astral Stage 0C, Stage 1, HSAI
security, provider cryptography, benchmark status, production readiness,
consciousness, or general introspection. V25 and the repository claim ceiling
remain unchanged.
