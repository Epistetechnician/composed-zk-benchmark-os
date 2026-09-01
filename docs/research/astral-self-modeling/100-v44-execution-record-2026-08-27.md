# Astral V44 execution record — 2026-08-27

State slice: `astral-stage0c-qwen36-causal-target-measurement-invariance-v44`.

Authorization: fresh V44 measurement-invariance protocol with new data
identity, predeclared wrappers/layers/positions, unchanged controls,
qualification, review ordering, and independent validation.

Disposition: `MeasurementInvarianceNoCandidate`, independently validated.
Claim ceiling: `LocalDevelopmentV44MeasurementInvarianceNoCandidate`.

## Execution sequence

1. Sealed the V44 protocol contract and replaced two candidate IDs discovered
   by the hermetic freshness test because they were already in the V43
   exclusion inventory: `18875` became `452`, and `43063` became `451`.
2. Acquired and atomically sealed the fresh external Gutenberg text/RDF root.
   Network was used only by the intake command.
3. Independently validated the corpus and wrote its receipt.
4. Ran V44 qualification first against the re-custodied cached Qwen3.6
   checkpoint; all gates passed.
5. Independently validated qualification.
6. Built and independently recomputed the 72-family panel with three wrappers,
   three candidate layers, and final/penultimate positions.
7. Ran fit/tune measurement with the fixed activation-only, text-only,
   exact-copy, shuffled, constant, and matched controls. Assessment stayed
   closed.
8. Detected and diagnosed a batch-size-sensitive exact-copy defect in the first
   measurement implementation. The initial `r1` result was superseded before
   interpretation because clean baselines used a different batch size from
   intervention chunks. A single seam diagnostic showed exact-copy was a true
   no-op at matched batch size; the runner was corrected so clean capture and
   intervention chunks share the fixed batch size.
9. Reran the unchanged V44 measurement under immutable `r2` output identity.
10. Independently validated the corrected aggregate-only result, including
    custody, lock digest, raw-field rejection, gate arithmetic, and ordered
    passing-target recomputation.

## External roots and digests

| Artifact | External root | Primary SHA-256 |
| --- | --- | --- |
| Corpus | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v44-corpus-r1-2026-08-27` | corpus manifest `3e9d6d49d51cc869b0e8b07aa76b2f1dab1d60bf852a9ee9fce6f0201df91bac` |
| Qualification | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v44-qualification-r1-2026-08-27` | result `d95dd69942e525388c8b48b31583253014e871abaa93af7dc48a014ad54ee656` |
| Panel | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v44-panel-r1-2026-08-27` | panel manifest `2e7e82c9f4d8b803360c0d714b3f3f2ddfb882f84bcc045f05744f0e8dace032` |
| Corrected measurement | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v44-invariance-r2-2026-08-27` | result `a181695c410ff4cc3cc06e60169b34821f72091f7750abccb48e1c855d3d30ee` |
| Corrected measurement lock | same measurement root | lock `b578977fd09876a8231f115d70bc891c6febf2928d517d1fab04e5211bcc698b` |
| Independent measurement receipt | same measurement root | receipt `37d54ecb60595f1e9960931b72b2636ef143a6e46df1f08a75f38d1fc3891f19` |

Selection digest: `c15bddd10b67485cfa8a79f333d1dada7c478571023493e492c47bfcb09d7ce1`.

Qualification used Python `3.14.5`, MLX `0.31.2`, and MLX-LM `0.31.3`.
Native parity, deterministic repeat, and no-op replacement were all `0.0`.
Nonzero replacement reached selected logits at every cell:

| Cell | Maximum absolute logit delta |
| --- | ---: |
| 12:final | 19.078125 |
| 12:penultimate | 17.000000 |
| 19:final | 15.980469 |
| 19:penultimate | 15.812500 |
| 26:final | 9.781250 |
| 26:penultimate | 14.125000 |

Observed shape was 40 layers × 2048 hidden width. All qualification and
custody gates passed.

## Corrected fit/tune measurement

The exact-copy control was zero for every corrected cell. Repeatability was
zero for every corrected cell. No tune cell passed the complete measurement-
invariance gate set. The following are the minimum pairwise wrapper metrics;
control columns are aggregate means across wrappers.

| Split | Cell | Wrapper corr. min | Sign agreement min | Bootstrap lower 95% min | Effect std. min | Shuffled mean | Constant mean | Matched mean | Failed invariance gates |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| fit | 12:final | -0.076788 | 0.416667 | -0.521174 | 0.080519 | -0.156250 | 0.012587 | -0.152778 | correlation, sign, bootstrap |
| fit | 12:penultimate | 0.000481 | 0.458333 | -0.417929 | 0.081648 | -0.073351 | 0.001736 | -0.072049 | correlation, sign, bootstrap |
| fit | 19:final | -0.236138 | 0.250000 | -0.526064 | 0.079406 | -0.182292 | -0.006944 | -0.181424 | correlation, sign, bootstrap |
| fit | 19:penultimate | -0.184807 | 0.333333 | -0.428945 | 0.071555 | 0.013889 | 0.046875 | 0.014757 | correlation, sign, bootstrap |
| fit | 26:final | -0.158019 | 0.291667 | -0.629757 | 0.089872 | -0.178385 | -0.034722 | -0.178385 | correlation, sign, bootstrap |
| fit | 26:penultimate | -0.101628 | 0.291667 | -0.418972 | 0.061502 | 0.055990 | 0.003038 | 0.061198 | correlation, sign, bootstrap |
| tune | 12:final | -0.071562 | 0.333333 | -0.523346 | 0.083496 | -0.038628 | 0.026042 | -0.047309 | correlation, sign, bootstrap |
| tune | 12:penultimate | -0.383439 | 0.250000 | -0.727832 | 0.061846 | 0.025608 | 0.022569 | 0.017361 | correlation, sign, bootstrap |
| tune | 19:final | 0.101978 | 0.416667 | -0.352899 | 0.077853 | -0.056424 | 0.003038 | -0.039931 | correlation, sign, bootstrap |
| tune | 19:penultimate | -0.495636 | 0.166667 | -0.751734 | 0.067796 | 0.035590 | 0.027344 | 0.016059 | correlation, sign, bootstrap |
| tune | 26:final | -0.138431 | 0.333333 | -0.520197 | 0.106285 | 0.003906 | 0.006076 | 0.007812 | correlation, sign, bootstrap |
| tune | 26:penultimate | -0.197532 | 0.291667 | -0.480143 | 0.053734 | 0.015625 | 0.014323 | 0.020833 | correlation, sign, bootstrap |

All six tune cells failed wrapper correlation, sign agreement, and bootstrap
lower-bound gates. Therefore `passing_targets` is empty, `selected_target` is
`null`, `review_required_before_assessment` is `false`, and assessment effects
were not generated.

## Claim boundary and next gate

V44 is a validated local measurement-invariance no-candidate result. It shows
that the qualified Qwen3.6 seam can be measured under the fresh protocol and
that this panel did not produce a wrapper-invariant target at the predeclared
cells. It does not establish introspection, causal self-modeling, Stage 0C,
Stage 1, benchmark evidence, accepted Evidence Ledger status, or production
readiness. No independent review receipt was consumed because no tune target
passed and assessment remained closed.

Stage 0C remains blocked pending a complete validated causal-target result;
Stage 1 remains blocked until Stage 0C passes. V82 remains a separate stopped
Neural Chameleon branch with missing Gemma/oracle/monitor artifacts. Any future
Astral experiment requires another separately authorized state slice, fresh
artifact identity, qualification-first execution, review ordering, and
independent validation.

## Repository verification boundary

The V44-focused regression passed: `3 passed` in
`tools/astral-stage0c-qwen36-v44/tests`, and `git diff --check` passed.
`pnpm run lint:fast` passed. The full root `pnpm run lint` was attempted and
stopped at an unrelated pre-existing continual-learning test because the
external `/Volumes/PrimaryED` volume is not mounted; no unrelated lane was
modified. This environmental failure does not invalidate the V44-specific
validation receipts, but the repository-wide lint status is not green in this
environment.
