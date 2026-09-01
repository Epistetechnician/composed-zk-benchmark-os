# Astral V45 execution record — 2026-08-28

State slice: `astral-stage0c-qwen36-response-anchored-causal-target-v45`.

Authorization: fresh V45 response-anchored canonical-task causal-target
measurement audit with fresh corpus identity, fixed content-anchor semantics,
unchanged controls, qualification-first execution, prediction locking,
independent review before assessment, aggregate-only retention, and
independent validation.

Disposition: `CanonicalTaskNoCandidate`, independently validated.
Claim ceiling: `LocalDevelopmentV45CanonicalTaskNoCandidate`.

## Execution sequence

1. Acquired and independently validated a fresh external 24-document,
   author-disjoint Project Gutenberg corpus. Network was used only by the
   acquisition command; model execution was offline.
2. Built and independently validated the 96-family canonical-task panel. The
   final panel uses the predeclared 20–75-word passage eligibility rule, fixed
   320-token prompts, equal-token target/distractor pairs, and equal ordinary/
   counterfactual content-anchor indices.
3. Ran final-code V45 qualification first. Native parity, deterministic
   repeatability, no-op and zero replacement, nonzero layer reach, shape,
   response-token, runtime, source-custody, offline, and retention gates all
   passed. Independent qualification validation returned zero errors.
4. Ran fit/tune measurement over layers 12, 19, and 26 with the fixed signed
   32-block feature map, ridge alphas `0.1`, `1`, `10`, and `100`, and the
   unchanged activation-only, text-only, exact-copy, shuffled, constant, and
   matched controls. Tune predictions were generated before tune effects.
5. No layer/alpha pair passed the complete fixed tune gate set. Assessment
   effects were not generated, no review receipt was required, and no
   assessment configuration was opened.
6. Independently validated the aggregate-only result, custody bindings,
   source digests, lock digest, raw-field rejection, assessment-closed state,
   and no-candidate classification. The first completed measurement root was
   superseded before interpretation because its qualification source digest
   predated the final runner correction; the accepted result is V45 `r2` only.

## External roots and digests

| Artifact | External root | Primary SHA-256 |
| --- | --- | --- |
| Corpus | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v45-corpus-r1-2026-08-27` | corpus manifest `776cbb32688d0943106e5fc3edcb3294fbabf1f826ebc6f649598c9de271baab` |
| Corpus selection | same corpus root | selection digest `060b27ac32f3b487804be6516cb0c7e9de817b9edcb4e08d6f2457222646dd6c` |
| Corpus validator | same corpus root | receipt `4615f58bb929294ba9ca728e0cef7a25e790704ae660602290d5ec54d47f3b95` |
| Panel | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v45-panel-r1-2026-08-27` | panel manifest `53aa4d290112c380ac96e5f2456bff9ccf693724121ec7beef17e08ecff8643a` |
| Panel validator | same panel root | receipt `1a3ca20684a5be55d96da10461ac77ee1604e51f5e577635f9b00abffa88791a` |
| Qualification | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v45-qualification-r2-2026-08-28` | result `1c5dfa1cd535efc8252c8e26a762ee9bb6747dac88f223f77a176f9cd05cff17` |
| Qualification validator | same qualification root | receipt `385332833b1d2bdbc808dac70c8daaeaaaa49f99f56163a964a00ac2a6f6c983` |
| Accepted fit/tune result | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v45-canonical-task-r2-2026-08-28` | result `56d42ac2f140d6bb200644875964e7fbdf36846ccb76651d8c0fbd64b999045a` |
| Configuration lock | same result root | lock `9d7897dfeffa9ed44322919930ba98f9ad2d415eab2414dffa5921f426161d90` |
| Independent result validator | same result root | receipt `6378ed1ac5c7762e230cbceda97ae98114888f2fee6a65e25e49d717787682fd` |

The model manifest digest was
`a95dc0f89c98c82331865ef0f51fc52ee832e41d6a97bd9b76351d37cec1e9e4` for the
cached `Qwen3.6-35B-A3B-MLX-4bit` checkpoint. Qualification used Python
`3.14.5`, MLX `0.31.2`, and MLX-LM `0.31.3`. The final protocol source digest
was `bede1f8abca0f6b4e10d536163e7ecbd5bac55a4a6d8496720e572db82ec7c12`.
The Qwen source digests were
`f0daa30bba5cb521c8bdfa7093101a544c6a37bbba09bca582288219cb04ae3a` and
`ef9e8e1f6a5c097b29587c8330e8eb9c9cbdc52fbb4597fbc2362606c1996619`.

Qualification observed 40 layers and hidden width 2048. Native parity,
deterministic repeat, and no-op replacement had maximum absolute logit delta
`0.0`. Zero replacement reached selected logits at layers 12, 19, and 26 with
maximum absolute deltas `8.671875`, `9.234375`, and `9.40625`; nonzero
replacement reached them with maximum absolute deltas `16.890625`, `14.216796875`,
and `8.96875`.

## Fit/tune result

All three tune cells were non-degenerate and all unchanged reliability controls
passed. Exact-copy effects were zero, and repeatability passed. The predictor
gates failed for every alpha at every layer:

| Cell | Effect std. | Correlation range | Sign agreement | Bootstrap lower-95% range | Failed predictor gates |
| --- | ---: | ---: | ---: | ---: | --- |
| 12:content_anchor | `0.098744` | `-0.131755` to `-0.131650` | `0.40625` | `-0.527687` to `-0.517128` | correlation, sign, bootstrap |
| 19:content_anchor | `0.094540` | `0.219157` to `0.219480` | `0.34375` | `-0.017181` to `-0.006365` | correlation, sign, bootstrap |
| 26:content_anchor | `0.065713` | `-0.170281` to `-0.170214` | `0.43750` | `-0.501672` to `-0.479420` | correlation, sign, bootstrap |

The strongest correlation was layer 19, alpha `0.1`, at `0.219480`, below the
locked `0.25` requirement. `passing_targets` is empty and `selected_target` is
`null`.

## Claim boundary and next gate

V45 is a validated local canonical-task no-candidate result. It shows that the
final qualified seam and fixed controls executed on the fresh panel, while the
predeclared activation geometry did not meet the held-out tune prediction
requirements. It does not establish introspection, causal self-modeling,
Stage 0C, Stage 1, benchmark evidence, accepted Evidence Ledger status, or
production readiness.

Because no tune target passed, independent review and assessment remained
closed. No V45 adaptive retuning of layers, anchors, wrappers, features,
thresholds, controls, or corpus was performed after effects. V28–V29 remain
closed, V25 remains information-presence only, V30–V37 remain governance
controls, V61 remains docs-only, and V82 remains isolated and blocked for the
missing Gemma/oracle/monitor artifact bundle. Stage 0C and Stage 1 remain
blocked. Any further Astral experiment requires a separately authorized fresh
state slice and cannot consume V45 scientific effects or predictions.

## Repository verification boundary

The V45-focused hermetic suite passed: `3 passed`. `pnpm run lint:fast` passed,
including Python-source verification and `git diff --check`. The expanded
`pnpm run test:focused` reached 321 passed tests and 41 passing subtests, with
one unrelated pre-existing continual-learning failure because
`/Volumes/PrimaryED` is not mounted; the affected files are untracked existing
worktree files and were not modified. The declared root `pnpm run lint` was
also attempted and stopped at that same focused-test failure before contract,
workspace, feature, or clippy gates. The repository-wide test gate is therefore
not green in this environment, while the V45-specific gates and independent
artifact validators are green.
