# Astral V43 execution record — 2026-08-27

State slice: `astral-stage0c-qwen36-causal-target-localization-v43`.

Authorization: `Authorize astral-stage0c-qwen36-causal-target-localization-v43
end to end.`

Disposition: `TargetLocalizationNoCandidate`, independently validated. Claim
ceiling: `LocalDevelopmentV43TargetLocalizationNoCandidate`.

## Execution sequence

1. Audited 18 fresh Gutenberg candidates for English language, public-domain
   rights, single-work titles, text availability, and usable paragraph yield.
2. Acquired and atomically sealed the external text/RDF corpus. Network was
   used only by the intake command.
3. Independently validated the corpus and wrote its receipt.
4. Ran V43 qualification first against the re-custodied cached Qwen3.6 model.
5. Independently validated qualification; all gates passed.
6. Built the fresh 72-family panel and independently recomputed/validated it.
7. Ran fit/tune localization across layers 12, 19, and 26, both wrappers, and
   all preregistered controls. Assessment remained closed.
8. Independently validated the aggregate-only localization result and custody
   chain.

## External roots and digests

| Artifact | External root | Primary SHA-256 |
| --- | --- | --- |
| Corpus | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v43-corpus-r1-2026-08-27` | corpus manifest `18bc507f085dd33e19e3deb608bdce6dd73e082a394cc71d36d1fc57b8812942` |
| Qualification | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v43-qualification-r1-2026-08-27` | result `ff29cc873ba9c189da5cc1b71399a22ecd323ebba1759942f057cc33287bc4b9` |
| Panel | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v43-panel-r1-2026-08-27` | panel manifest `c1d82f58b228ee450df64720ee45b7adb010f8d3fcf337fa4a52a89b860f0699` |
| Localization | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v43-localization-r1-2026-08-27` | result `42a601cab20c1489d3230bd770376b39733c7679cdd2a4df71bcc5ac74ed59d5` |

Selection digest: `d6acc917b90c59549c1db81487a059685786d7de496935c4ed949e450939b5be`.

Qualification runtime was Python `3.14.5`, MLX `0.31.2`, and MLX-LM
`0.31.3`. Native parity and no-op parity were both `0.0`; deterministic
repeat delta was `0.0`. Nonzero replacement reached selected logits with
maximum absolute deltas of `19.078125` at layer 12, `15.98046875` at layer
19, and `9.78125` at layer 26. Observed shape was 40 layers × 2048 hidden
width. All qualification and custody gates passed.

## Fit/tune result

All three candidate layers were non-degenerate and all exact-copy,
shuffled, constant, matched, and repeatability controls passed. Localization
failed on wrapper invariance:

| Layer | Tune wrapper correlation | Tune sign agreement | Tune bootstrap lower 95% | Failed gates |
| ---: | ---: | ---: | ---: | --- |
| 12 | 0.326844 | 0.333333 | 0.069454 | sign agreement, bootstrap lower bound |
| 19 | 0.332923 | 0.291667 | -0.007421 | sign agreement, bootstrap lower bound |
| 26 | -0.343906 | 0.333333 | -0.603424 | correlation, sign agreement, bootstrap lower bound |

No layer passed the complete tune gate set. `passing_layers` is empty,
`selected_layer` is `null`, `assessment_opened` is `false`, and no independent
review receipt was accepted. The observed result shows measurable direct
effects and a reachable seam, but not a wrapper-invariant localized causal
target on this fresh panel.

## Claim boundary and next gate

V43 is a validated local target-localization no-candidate result. It does not
establish introspection, causal self-modeling, Stage 0C, Stage 1, benchmark
evidence, accepted Evidence Ledger status, or production readiness. V82
remains separately stopped at missing Gemma/oracle/monitor artifacts. Any
future Astral experiment requires its own separately authorized state slice,
fresh artifact identity, qualification, review ordering, and independent
validation.
