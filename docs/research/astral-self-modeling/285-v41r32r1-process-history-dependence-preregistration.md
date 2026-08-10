# V41R32R1 Process-History Dependence Probe Preregistration

State slice: `V41R32R1ProcessHistoryDependenceProbe`.

The original V41R27R19 failing bundle is no longer present in GMAN snapshot
custody, so its receipts cannot be compared retroactively. V41R30R1, R2, and
V41R31R4 independently passed the same frozen cell, and V41R31R4 showed exact
deterministic-mode parity. This identity tests one prospective explanation:
whether an explicitly declared same-process prelude changes the frozen worker
outcome.

## Locked protocol

- two arms, one worker per arm: `v41r27-panel-8-seed-412019`;
- same frozen source commit `c3b287d4227db94a43af7888d0211fb337c330fa`;
- same source archive `sha256:8b1802d97b14d83b6d6d4596589664885efd973cec1e02ac03250acf0e250645`;
- canonical frozen Git archive SHA-256
  `sha256:19c1f485125c0cb7d113fd763f972c28df0d02e02e26c6f0777de6ab08a06db5`;
- frozen entrypoint SHA-256
  `sha256:cccc6a69caace07871274a929785c75de98a3fe6975acd67d4866ee4c7ae8859`;
- frozen method SHA-256
  `sha256:f9fa45c268fccdecde2f3dfb2c6720ed0a47e2004f1f4b50d9c4c89767ba98dd`;
- frozen requirements SHA-256
  `sha256:0a114a8f7abaee60c0aff87e27354e2eae5090772b20b1bbd30093ad6d1c3541`;
- model `openai/gpt-oss-20b`, revision
  `d0e2aa76789354d715f8b22553b9feb6c462fcf0`, tokenizer class
  `PreTrainedTokenizerFast`; runtime Python `3.10.12`, torch `2.10.0`, CUDA
  `12.8`, transformers `4.57.6`, peft `0.18.1`, GPU `NVIDIA H100 80GB HBM3`;
- exact run spec: acquisition cases `v41r27-acquisition-032` through
  `035`, protected cases `v41r27-protected-128` through `143`, contract
  SHA-256 `sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e`;
- same H100 class, model, tokenizer, optimizer, seed, 256 steps, gates, and thresholds;
- control: fresh process invokes the frozen worker directly;
- intervention: one external wrapper imports the frozen model/tokenizer, runs a
  fixed no-update scoring prelude on the worker's exact declared panel in its
  manifest order, using the worker's own tokenizer, model evaluation mode,
  dtype, device, batching, and scoring path, without optimizer construction or
  parameter mutation; it then deletes the prelude objects, calls
  `torch.cuda.empty_cache()`, and invokes the frozen worker in that same process;
- the frozen worker source is unchanged; the wrapper is the only intervention;
- before each arm, verify the worker source tree and archive against both locked
  hashes; hash the wrapper, command, environment, import path, and runtime
  identity; the wrapper may not write or monkey-patch worker files;
- the intervention wrapper saves and restores Python, CPU, CUDA, and library RNG
  states immediately before model/tokenizer construction, immediately before
  the prelude, and immediately after the prelude; it restores Python,
  NumPy, PyTorch CPU, every CUDA device, explicit generators, and DataLoader
  worker seeds before invoking the worker, so the declared contrast is resource
  and process history rather than an unregistered RNG advance;
- both arms bind the same container digest, Python/PyTorch/CUDA/driver versions,
  GPU identity fields, working directory, launch bytes, and environment; source
  verification recomputes SHA-256 for the canonical archive, the complete
  worker tree, the entrypoint, and every imported worker module and fails closed
  on any mismatch;
- the prelude is exactly one evaluation-mode, no-grad forward pass over the
  four selected acquisition rows and sixteen selected protected rows, in the
  frozen manifest order, with the frozen worker's tokenizer, batch construction,
  dtype, device, and scoring callable; it synchronizes before deletion and
  records object deletion and allocator state hashes;
- if the exact container/image digest or NVIDIA driver version cannot be
  captured before launch, classify the identity as infrastructure-incomplete
  and do not start either scientific arm;
- no retries, substitutions, tuning, threshold changes, assessment, or census update;
- export and verify both result directories, then stop the node immediately.
- execute the control first, then the intervention, on the same physical node
  and disk with separate fresh Python processes; do not reset or recreate the
  node between arms, and record the node identity and arm timestamps;
- the wrapper must be committed and content-addressed before node creation,
  with wrapper path `tools/v41r32r1_history_prelude_wrapper.py`, SHA-256
  `sha256:e5d2a6455fcab601838f9b47c127eacfe207ee779341c362329b69a5850236b`,
  entrypoint `main`, command bytes `python3 tools/v41r32r1_history_prelude_wrapper.py
  --output <arm-output>`, and expected imports rooted at `/home/dev/rgs/scripts`;
  a missing or mismatched wrapper is a fail-closed infrastructure result;
- bind the independent artifact validator identity, validator source hash,
  and durable artifact destination before launch. The validator is
  `tools/astral-v41r27-agem-retention/validate_worker.py`, SHA-256
  `sha256:f1b9f45cfc7d58812b0f72fba890d3ccb274224b578a74e9f87d584af645dfd4`,
  invoked against each exported directory with the frozen RGS root. Missing
  custody or validator verification is non-scientific and stops the identity.

## Outcomes and interpretation

Record acquisition pass/fail, protected accuracy, all receipt rows, runtime and
source bindings, adapter-state hash, and artifact hashes. A difference in a
preregistered terminal gate supports process-history dependence for this
specific prelude. Equal outcomes weaken that explanation but do not identify
the lost V41R27R19 cause. An import, prelude, OOM, or wrapper-integrity error
before complete worker termination is `InfrastructureOrInterventionIncomplete`
and is not a scientific arm result; only a complete frozen-worker terminal
result enters the paired comparison.

Even a gate difference is evidence only for a process-history-associated
difference under this wrapper. It does not isolate RNG-independent history,
CUDA/library state, allocator state, or a mechanism.

Maximum budget: one 1x H100 session at the locked platform rate and minimum
window. Claim ceiling: `RemoteH100V41R32R1ProcessHistoryDependenceProbe`.

V41R27 remains terminal at census `30/48`, qualification `NotAssessed`.
Governance remains `tune_opened:false`, `assessment_opened:false`,
`production_actions:false`, `provider_direct_authority:false`.
