# Aligned RSI BillSum chat-template adaptation V6 execution closure

State slice: `aligned-rsi-billsum-chat-template-adaptation-v6`.

Governance slice: `global-experiment-assurance-lifecycle-v1`.

Disposition: `ExecutionFailedUnexpectedPEFTAdapterFileSet`. V6 is terminal.

## Result

The one frozen local MPS execution completed the 512-document fit-loss pass
and all three 64-document untouched-base assessment repeats. The selected
arm for training seed `59` completed all eight optimizer steps and wrote its
adapter. PEFT wrote `README.md` alongside `adapter_config.json` and
`adapter_model.safetensors`; the frozen adapter file validator allowed only
the latter two and stopped the run. This exact artifact-set mismatch is the
terminal V6 failure. No retry, edit, or acceptance under V6 is permitted.

The selected adapter was not loaded for evaluation. The random arm, the other
training seeds, updated-arm assessments, the layer-level residual patch,
private aggregate run receipt, evaluation report, release manifest, and local
acceptance were not produced. The experiment has no `Candidate` or
`NoCandidate` disposition. The memory-bounded training path completed its
first full set of eight optimizer steps without an MPS OOM; peak memory
counters were not captured because execution stopped before report creation.

## Frozen identity and retained evidence

- Repository revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`; the
  worktree was already dirty.
- Run ID: `run-20261007T023107039280Z`.
- Started: `2026-10-07T02:31:07.039280Z`.
- Failed: `2026-10-07T02:45:17.760838Z`.
- Failure: `ExperimentError: unexpected PEFT adapter files: ['README.md',
  'adapter_config.json', 'adapter_model.safetensors']`.
- Prepared-input SHA-256:
  `b139e2f2ee49bffcb8554fa29c56ba09c2510acb9346b7564e35f4d923a3dcc9`.
- Fit roster: 512 documents, SHA-256
  `4288836f34fef9362ea66889b7e307bc285045b60ead44653542d750a5e00d66`.
- Assessment roster: 64 documents, SHA-256
  `eeff4c21fbe6dd7d6b116d365f322e6087b394f9067933da9875899a3e1d19c8`.
- Reconstructed V5 fit exclusion: 512 source IDs, SHA-256
  `9dab518511424ce830a4598bc45dd96f61be4de51839a3252866c750b84ca6eb`.
- Reconstructed V5 assessment exclusion: 64 source IDs, SHA-256
  `abc9cfbebdbc4cb24c4d271e3aeb70070d419bba3e29537e9f3ca4cdd51b13c1`.
- V1 exclusions were reconstructed from the pinned raw inputs. Eight
  repeated-source groups (16 train rows) were excluded; no test duplicates
  were found. The selected fit and assessment rosters were disjoint from V1
  and V5 and had no cross-split source overlap. Prompt/target token ranges
  were 494-1,279 / 23-505 for fit and 834-1,275 / 19-498 for assessment.
- Pinned model file-manifest SHA-256:
  `e77990a87387a8bd81db5a96b8ec8b2853d08b1c4b7fa65c8a34d768eab6459b`.
- Pinned dataset file-manifest SHA-256:
  `03ff3ea855c3e5840722315fb7a986da0001b2a3a932b5e6cd98b34eb967eda1`.
- Post-run readback confirmed the pinned model and dataset manifests were
  unchanged.
- V6 runner SHA-256:
  `5d409b385731237bc7988d1bc4372e3468398cc7d21be6e1069e5cbb10f718c6`.
- V6 protocol SHA-256:
  `986741cd8d2eb3057e3eef1aebcce95dca746e7760d43b76878a743d86b80666`.
- V6 protocol-manifest SHA-256:
  `ec2afafee6bc21f0598a4676c42e3ed018b0cde7ae5d091abb47eab631c09651`.
- V6 focused-test SHA-256:
  `ad93d6693352dff7ace5e7615aff2321708516af138125bae3574156e4530595`.
- V6 requirements-lock SHA-256:
  `6ba2dd58a8671884adee10d0cf41017f8ad4931ffa2bc7812a14a9061750d266`.
- Current `AGENTS.md` SHA-256 at execution start:
  `e5c85fbfeea00617cf677049989f8c2d50cb4a28d47a0c6de08e0c984e301c3d`.
- Focused V6 tests passed `11/11`; `uv pip check` confirmed all 131
  installed packages compatible. These are `INTERNAL_PASS` only for those
  local checks and the small-model loss/gradient parity contract.
- MPS was available and idle before the run; recommended maximum at preflight
  was 30,150,672,384 bytes. This is not an execution peak measurement.

The V6 owner-only root is mode `0700`; its files are mode `0600`. It retains
the prepared receipt, terminal run status, and the partial seed-59 adapter
directory with the three files listed in the failure. No generation, raw
source row, fit-loss table, `private_run.json`, or aggregate release was
persisted. `release/aligned_rsi_billsum_chat_template_v6/` is absent. V5
source, contract, tests, and lock digests still match their preserved V5
closure.

## Assurance and claim boundary

- Experiment assurance: not achieved. The run is incomplete and supports no
  scientific candidate disposition.
- `INTERNAL_PASS`: limited to 11 focused V6 tests, dependency compatibility,
  and the test's Qwen3/PEFT objective-and-gradient parity scope.
- Reviewer status: local acceptance was not issued; independent acceptance
  was not requested or performed.
- Reproducibility status: one local execution failed;
  `REPRODUCED_LOCAL` was not achieved.
- Data and artifact custody: the pinned Qwen3 model and federal BillSum bytes
  remain in the existing owner-only V1 cache. The V6 receipt, failed status,
  and partial adapter remain under the V6 `0700` owner root. No report,
  acceptance, or repository release exists.
- Claim ceiling: `LocalDevelopmentBillSumChatTemplateCurriculumQualificationV6`
  was not earned. No curriculum benefit, alignment, recursive
  self-improvement, benchmark, mechanistic, or production claim is supported.
- Next blocked authority gate: a new, separately authorized state slice and
  frozen packet are required before another model execution. V6 is terminal;
  do not edit, retry, verify, or accept it.
