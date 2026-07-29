# V28 Gate 1 Infrastructure-Abort Execution Record

State slice:
`astral-rgs-v28-gate1-infrastructure-abort-remediation`.

Status: `InvalidInfrastructureAbortBeforeModelLoad / CampaignConsumed /
NoGate1Result`.

## Verdict

The V28 Gate 1 one-shot campaign did not produce a scientific acquisition
result. The first `context_only` worker exited at `import mlx.core as mx` with
`ModuleNotFoundError: No module named 'mlx'`. The coordinator invoked
`/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`, not the
previously inventoried MLX runtime at
`/Users/shaanp/.pyenv/versions/3.14.5/bin/python`.

The failure occurred before checkpoint or tokenizer loading. No optimizer step,
adapter state, persistent cell, model score, or model outcome exists. This is
an infrastructure abort, not a negative acquisition result.

## Immutable failure evidence

- consumed ledger:
  `sha256:35b8dc1c71ccfcc01180e83f6d0e21813857b5fa1ca0945a348159f0ddcaa2cc`;
- abort packet:
  `sha256:d0aed52f5308ce660646c8231b8c3d76f98bad34203b87bcf15d9d65c863c0fb`;
- process record:
  `sha256:37f100ec22ed49bb9355c174ba7203e6a7b6e528f51ea96b631ef264b82f0479`;
- independent Astral invalid-run report file:
  `sha256:7e324d216e59527c3e764bc885d19111f1ddf25769d514bf747d28eb1198b450`;
- artifact manifest:
  `sha256:7c343e7c2894745ea9506bd43173af4f2b97ebe371b3fcc89c691558e801d1c4`;
- sealed artifact:
  `/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28-gate1-abort-7c343e7c2894-r1`.

The manifest contains 12 files and a complete rehash produced zero errors. The
independent report sets `valid_failure_record=true` and
`scientific_result_valid=false`.

## Remediation

RGS remediation commit `b015dae11dff9a8c2cbb874c6e96652969137cf5`
requires an explicit `--worker-python`, resolves it against the exact frozen
runtime, and verifies Python `3.14.5`, MLX `0.31.2`, MLX-LM `0.31.3`, and NumPy
`2.4.5` before any future ledger claim. Astral remediation commit
`b8788aa66c1ee8cf969b4ccec6ad1130dedb2d23` independently validates the
retained abort.

The pinned runtime preflight now passes. That repair does not revive the
consumed campaign.

## Required next boundary

The frozen rule states that the first ledger claim is consuming even on
failure and forbids a replacement campaign. V28 Gate 1 therefore cannot be
resumed or rerun. A scientifically valid next attempt requires a new
preregistration, a newly generated disjoint corpus and seed, a new novelty
preflight, a new one-shot ledger, and the corrected pre-ledger runtime gate.
No threshold, arm, or statistical rule may be chosen using nonexistent Gate 1
outcomes.

The current claim ceiling is
`RetainedInfrastructureAbortNoModelOutcomeV28Gate1`. Acquisition, continual
learning, retention/recovery, selection, assessment, confirmation,
independent replication, and breakthrough claims remain unsupported.
