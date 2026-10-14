# V41R28 Local Surrogate Acquisition-Gate Characterization Execution Record

State slice: `V41R28LocalSurrogateAcquisitionGateCharacterization`.

Status: `Executed / IndependentlyValidatedLocally / ExternalReviewNotRun`.

## Question and design

V41R27 is terminal at census 30 of 48 with exactly one acquisition-gate
failure, `v41r27-panel-8-seed-412019` (pass: false with protected accuracy
1.0 on the H100). This preregistered surrogate experiment
(`266-v41r28-local-surrogate-acquisition-gate-preregistration.md`, preregistration
git blob `30d246e2eb3d14faf22ac0feaaf904279913b03b`) asks whether that failure
structure reproduces on local substrates under the identical frozen V41R27
instruments, schedule, A-GEM projection algebra, gates, and thresholds.

Four cells mirroring the V41R27R19 pattern were run once per substrate:
`panel-6-seed-412019` (H100 pass), `panel-8-seed-412003` (H100 pass),
`panel-8-seed-412007` (H100 pass), `panel-8-seed-412019` (H100 fail).

Frozen bindings: V41R27 contract SHA-256
`sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e`;
acquisition instrument
`sha256:0459d3c39e37c1a3fb7a8ffdbee1dca214b75b316dab456ab3e8d82dd98d1f92`;
protected instrument
`sha256:83e873627f55df68f62a90d9847a73e5838eccc76fe48fb3c77109b6122b503e`.

## Runtime

- machine: macOS 15.7.5 arm64 (Apple Silicon, Metal);
- python 3.14.5, mlx 0.31.2, mlx-lm 0.31.3;
- runner `tools/astral-v41r28-local-surrogate/surrogate_v41r28.py` SHA-256
  `29a854a55c9a43537cb754180eccdb7bdfd3a066f1dd13a06ac1d68c7296a957`;
- independent validator `validate_surrogate.py` SHA-256
  `a770c5bb9ebf6c05ff452807fd3272b54fbcf1f40ab90a084ead7f6942ff2a10`;
- hermetic tests `test_surrogate_v41r28.py` SHA-256
  `bab7b80f0f2e2986911896da06227e77b886043a11a456d07b9d4ce98d95a21d`
  (14 tests, all passing).

## Infrastructure incident (disclosed, no scientific content affected)

The first qwen2.5-0.5b driver pass crashed in all four cells during protected
batch construction with `ValueError: Initialization encountered non-uniform
length` before any optimizer step ran: the runner's collate omitted the
pad-to-width and label masking that the frozen V41R27 `collate_training_rows`
applies. The collate was corrected to match the frozen contract (pad to max
width, mask prompt and padding labels with -100), a stub-tokenizer regression
test was added, the four crash-only directories (containing only
`failure-result.json` and `INCOMPLETE`, zero steps, zero receipts) were
removed, and the cells were rerun. No scientific measurement was produced or
discarded by the crashed pass.

## Substrate preflight results

| Substrate | panel-6 protected acc | panel-8 protected acc | acquisition novelty | Preflight |
| --- | --- | --- | --- | --- |
| qwen2.5-0.5b (4bit MLX) | 1.0 | 1.0 | 3/4 incorrect | passes |
| llama-3.2-1b (4bit MLX) | 0.1875 | 0.375 | 3/4 incorrect | blocked |

The llama-3.2-1b substrate cannot reliably compute the protected arithmetic at
baseline, so the frozen preflight (protected accuracy exactly 1.0) blocks all
four of its cells. That blockage is itself retained evidence about surrogate
validity.

## Executed results (qwen2.5-0.5b)

All four cells completed 256 optimizer steps on the first attempt, passed all
frozen gates, and were independently validated (projection geometry
recomputation, gate recomputation, digest and census checks, claim-boundary
checks; validator returned `valid=true, errors=[]` for every cell).

| Cell | H100 outcome | Surrogate outcome | protected acc | projection steps | case margins (nats) |
| --- | --- | --- | --- | --- | --- |
| panel-6-seed-412019 | pass | pass (4/4) | 1.0 | 32/256 | 14.0, 15.1, 13.3, 13.8 |
| panel-8-seed-412003 | pass | pass (4/4) | 1.0 | 23/256 | (see artifact) |
| panel-8-seed-412007 | pass | pass (4/4) | 1.0 | 29/256 | (see artifact) |
| panel-8-seed-412019 | **fail** | **pass (4/4)** | 1.0 | 29/256 | 14.8, 18.3, 20.4, 15.6 |

Artifact digests (directory
`artifacts/native-pcsm-governed-autoresearch/local-surrogate-2026-08-04/`):

| File | SHA-256 |
| --- | --- |
| qwen2.5-0.5b/v41r27-panel-6-seed-412019/worker-result.json | `3a030b56796e5e1b2d5e289f1a854587c6eea0135aa3125c227873aa46b61ae6` |
| qwen2.5-0.5b/v41r27-panel-6-seed-412019/worker-adapter-state.safetensors | `2e534b33e5cd172f944a800ee7e87c66690156e4a7a11a31df281fce8794f7b7` |
| qwen2.5-0.5b/v41r27-panel-8-seed-412003/worker-result.json | `ad0585b94ab29cfd2daea02d04a78358991662234815cf21d8470af413e7fdf4` |
| qwen2.5-0.5b/v41r27-panel-8-seed-412003/worker-adapter-state.safetensors | `b363f8fe75bc825d605988ad25ef442037b802d9757b868f661a12ce20dd0774` |
| qwen2.5-0.5b/v41r27-panel-8-seed-412007/worker-result.json | `7322d11eef883d3f0e9296ebaadd2b507ef4c4dd16e902067b111873229fd17a` |
| qwen2.5-0.5b/v41r27-panel-8-seed-412007/worker-adapter-state.safetensors | `7005d1ebdc41be45596a4f58c05cc68f550c0bb79ad387b6a87973a4cf27ce4f` |
| qwen2.5-0.5b/v41r27-panel-8-seed-412019/worker-result.json | `b3c9d52e894d76828e68773de6f49ff672691f83dd008fc7add9d5d7c7e8197d` |
| qwen2.5-0.5b/v41r27-panel-8-seed-412019/worker-adapter-state.safetensors | `c4b324fe8281d122b640c5a4519b52d98928d519c4dad8c55cb41bfb6bf97fcb` |
| llama-3.2-1b/v41r27-panel-6-seed-412019/preflight-blocked.json | `b806b9273e40a29ffeba7471339ceb1c7d8c04fd2ceb28e94304a625c43d4922` |
| llama-3.2-1b/v41r27-panel-8-seed-412003/preflight-blocked.json | `fe988e77c001384143c83561bb92e01bcafb6304d85412a3aa7455b56521ef9b` |
| llama-3.2-1b/v41r27-panel-8-seed-412007/preflight-blocked.json | `3de07bb5f84589101b17b1fa87879a29aab19607141482bac05e1f31b2470b36` |
| llama-3.2-1b/v41r27-panel-8-seed-412019/preflight-blocked.json | `8a24033eb59110f893539a3e14f24d50ff0b386c5c8f66e6b1c06332365173c4` |

## Interpretation (preregistered ladder)

The preregistered ladder rung fired for the executable substrate: all four
cells passed on qwen2.5-0.5b, so the surrogate shows no acquisition-failure
signal and the H100 failure of `panel-8-seed-412019` does **not reproduce**
locally at this scale. The llama-3.2-1b substrate was preflight-blocked and is
uninformative for the failure question. The joint (both-substrate)
reproduction condition was therefore not met by the failure pattern: the
failure did not appear on either local substrate.

Reading: the panel-8 x seed-412019 acquisition-gate failure is not expressed
by the 0.5B 4-bit MLX surrogate under identical instruments, schedule, and
gates. This is consistent with the failure involving the 20B MXFP4 H100
substrate specifically (scale, quantization, kernel numerics, or their
interaction with that seed trajectory). It does not distinguish those
hypotheses.

Positive control value: on the surrogate, protected retention under A-GEM
projection held at 1.0 in every executed cell with active projection on
23-32% of steps, mirroring the retention result of the H100 campaign at small
scale.

## Retained negative and its weight

This is a valid local surrogate characterization. It does not explain the H100
failure, requalify V41R27, complete the 48-worker census, or substitute for
the unreachable failing bundle. The V41R27 census remains 30 of 48,
qualification `NotAssessed`, claim ceiling
`RemoteH100AGEMPartialQualificationInfrastructureInterruptedV41R27R2`.

## Claim ceiling and nonclaims

Claim ceiling: `LocalSurrogateAcquisitionGateCharacterizationV41R28`.

This record does not support claims of H100 substrate equivalence, H100
failure explanation, V41R27 campaign qualification or requalification, census
change, continual learning, recovery, autonomous self-improvement,
introspection, SOTA, confirmation, independent replication, or Stage 0C
advancement. A surrogate result is evidence about the surrogate.

## Governance

`tune_opened: false`, `assessment_opened: false`, `adaptive_stopping: false`,
`production_actions: false`, `provider_direct_authority: false`. One attempt
per cell-substrate; no retries of executed cells; the single collate correction
was an infrastructure alignment to the frozen V41R27 contract, not a change to
any scientific variable.
