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
- no retries, substitutions, tuning, threshold changes, assessment, or census update;
- export and verify both result directories, then stop the node immediately.

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
