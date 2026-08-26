# V47 Llama codebook-alignment counterfactual execution

Date: 2026-08-26

State slice: `continual-learning-llama-codebook-alignment-counterfactual-execution-v47`

Protocol: `v47-llama-codebook-alignment-counterfactual-execution-v1`

Claim ceiling: `LocalDevelopmentCodebookAlignmentCounterfactualDiagnosis`

## Execution

The frozen V46 counterfactual was executed offline against the cached
`Llama-3.2-1B-Instruct-4bit` checkpoint. The campaign used fresh task seeds
`20260865`, `20260866`, and `20260867`; target shifts `0` and `1`; fixed
optimizer seed `20260856`; canonical task order `0123`; 160 iterations; and a
32-row update budget. Each arm ran in a separate subprocess with a fresh
adapter. The underlying facts were paired by digest; only the task-0 target
codebook changed between each pair.

The canonical immutable artifact root is:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-llama-codebook-alignment-counterfactual-v47-20260826-r4`

The bound inference-only runtime preflight was the independently validated V44
Llama runtime receipt. Its model-manifest digest is
`ea36d761a8af224a35f644ff77e9871d80452288174012e6c82884327bfde680`; the
receipt file SHA-256 is
`2de1317f703ebb766fba7690cc1a94e99b7557944257afbf89178320144bef85`.

## Independent validation

The independent campaign validator returned `valid=true` and
`CodebookAlignmentSupported` under the preregistered diagnostic rule. All six
arms were structurally valid. The three paired results were:

| Task seed | Identity target | Matched-shift target | Delta |
| --- | ---: | ---: | ---: |
| `20260865` | `0.25` | `1.00` | `+0.75` |
| `20260866` | `0.25` | `1.00` | `+0.75` |
| `20260867` | `0.25` | `1.00` | `+0.75` |

All three pairs had matching underlying-fact digests. The identity-target arms
were structurally valid but not eligible under the V37 acquisition gates; the
matched-shift arms were structurally valid and eligible. The result is a
counterfactual diagnosis of the V45 task-0 constant-readout failure: under
this frozen setup, replacing the task-0 identity codebook with the matched
shifted codebook changed target acquisition from `0.25` to `1.00`.

The aggregate report digest is
`7bf0ff68c7c5a52e60be46ff9adab86d92afc18346bb054d115dc28e39072527` and its
file SHA-256 is
`79ddaa60ba96932d916207969248ade3f7b86459c6a85e73b10875df295530b3`.
The contract digest is
`703d32c0d850aabcd359f6a8f2815572d07afd91ac55d30f0f48b64034dcea2f` and its
file SHA-256 is
`01c8a715b94453aaf22d01b2af1996e6ae851805e4de83bbd038715f46524678`.

## Harness custody

Earlier V47 roots `r1` and `r2` stopped at validator-only harness failures
(missing fixed-optimizer audit binding and stale aggregate digest recomputation,
respectively). Root `r3` stopped at a missing campaign validation directory.
Those roots remain immutable rejected attempts and are not scientific results.
The r4 campaign was started only after the fixes were covered by focused tests
and `pnpm run lint:fast`.

## Boundary

This is a local mechanism diagnosis, not a generally viable continual-learning
candidate. It does not establish retention, order robustness, cross-model
replication, provider readiness, production readiness, accepted benchmark
evidence, or any claim above the named local diagnostic ceiling. No V44 artifact
was mutated or promoted. Retention, order-retention, provider, production, and
network execution remained disabled.

Implementation and validators:

- `experiments/continual_learning/llama_codebook_alignment_counterfactual_v47.py`
- `experiments/continual_learning/validate_llama_codebook_alignment_counterfactual_v47.py`
- `experiments/continual_learning/tests/test_llama_codebook_alignment_counterfactual_v47.py`
