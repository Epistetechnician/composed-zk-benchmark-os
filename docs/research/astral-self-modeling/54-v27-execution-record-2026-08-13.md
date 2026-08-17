# V27 Execution Record — 2026-08-13

State slice: `astral-public-abi-final-embedding-feasibility-v27-execution`.

Disposition: `PublicAbiFinalEmbeddingInterventionFeasible`.

## Exact custody

- actor: `/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_K_M.gguf`;
- actor SHA-256:
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`;
- runtime: `/opt/homebrew/Cellar/llama.cpp/10050/lib/libllama.0.0.10050.dylib`;
- runtime SHA-256:
  `25aa1419a298e05a6bbd340c5bccafffb836e15e1ac42460b31fcd4a089df2ff`;
- public header SHA-256:
  `2331631b6a3567311abc0402c55aa9a867ee99759f2550bdfa261ec3693a21f6`;
- runner source SHA-256:
  `ca13520e75ee2fd35e5f2b09da041173a6652277c14b15217d08714a62d313ec`;
- validator SHA-256:
  `cd1c85e24e0443f610837714e04d17ef6c856ef5c021fd1d89a66be5aa249938`;
- preflight SHA-256:
  `377c39b5e3282d9ef26042a0be3a4e6264baeeb3cd306e7cd229457045e881a4`;
- aggregate result root: `/tmp/astral-v27-public-abi-20260813`;
- aggregate result SHA-256 captured at execution:
  `9f40ec22caf7755971815c8da49082fe129fe7a45631c6c2de4b1461e30e25d7`.

The aggregate JSON was written to the external transient result root during
execution. That `/tmp` root is not present in the current environment, so the
file is not currently re-openable from this checkout. The captured hash,
aggregate metrics, and validator output remain in this record. No raw
embeddings, logits, model output, control vector, or runtime log entered the
repository.

## Frozen execution result

| Field | Result |
| --- | ---: |
| Classification | `PublicAbiFinalEmbeddingInterventionFeasible` |
| Embedding dimension | `4096` |
| Layer count | `32` |
| Prompt token count | `10` |
| Clean/zero maximum absolute error | `0` |
| Clean repeat maximum absolute error | `0` |
| Intervention repeat maximum absolute error | `0` |
| Clean embedding norm | `133.217056` |
| Intervention embedding norm | `133.134598` |
| Direct `A-B` logit-margin effect | `0.0415115356` |
| Finite-value gate | passed |
| Parity gate | passed |
| Repeatability gate | passed |
| Direct-effect gate | passed |
| Network access | `false` |

Independent validation:

```text
python3 tools/astral-public-abi-final-embedding-feasibility-v27/validator_v27.py /tmp/astral-v27-public-abi-20260813/result.json
{"errors": [], "valid": true}
```

## Interpretation

This is a positive local runtime/instrument feasibility result. It establishes
that the declared public llama.cpp ABI and one local Qwen3.5 GGUF actor can
produce deterministic final embeddings and a directly measurable output-logit
effect under the frozen control-vector harness.

It does not establish per-layer residual telemetry, causal-channel separation,
opaque-artifact information, faithful computation, mechanistic explanation,
provider cryptography, introspection, self-modeling, consciousness,
generalization, Stage 0C, Stage 1, benchmark evidence, production readiness,
or accepted Evidence Ledger status.

V26 remains unexecuted. V25 remains unchanged at
`LocalDevelopmentPrivilegedTelemetryInformationPresence`. The V27 result does
not authorize observer training or raise any Astral scientific claim ceiling.
