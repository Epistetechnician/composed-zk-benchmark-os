# V27 Execution Authorization Record

State slice: `astral-public-abi-final-embedding-feasibility-v27-execution`.

Date: 2026-08-13.

## Gate status

The no-model V27 public-ABI preflight passed. The exact local header and shared
library resolved all required public symbols, and the actor path is a regular
local file with digest:

`cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`

This record authorizes one bounded local feasibility execution under the exact
configuration below. It does not authorize V26, Stage 0C, Stage 1, provider/API
access, network access, raw artifact retention, or Evidence Ledger mutation.

## Frozen execution

- runner source: `tools/astral-public-abi-final-embedding-feasibility-v27/runner_v27.c`;
- compile command:
  `clang -O2 -std=c11 -Wall -Wextra -Werror -I/opt/homebrew/Cellar/llama.cpp/10050/include -I/opt/homebrew/Cellar/ggml/0.17.0/include runner_v27.c -L/opt/homebrew/Cellar/llama.cpp/10050/lib -L/opt/homebrew/Cellar/ggml/0.17.0/lib -lllama -lggml -lggml-base -Wl,-rpath,/opt/homebrew/Cellar/llama.cpp/10050/lib -Wl,-rpath,/opt/homebrew/Cellar/ggml/0.17.0/lib -lm -o runner_v27`;
- model: `/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_K_M.gguf`;
- runtime library SHA-256:
  `25aa1419a298e05a6bbd340c5bccafffb836e15e1ac42460b31fcd4a089df2ff`;
- header SHA-256:
  `2331631b6a3567311abc0402c55aa9a867ee99759f2550bdfa261ec3693a21f6`;
- prompt: `Choose one token: A or B. Answer:`;
- control vector: dimension `llama_model_n_embd`, coordinate `0` equals `1.0`,
  all other coordinates `0.0`, layer range `1..1`;
- conditions: clean, zero-vector, clean-repeat, nonzero-vector,
  nonzero-vector-repeat;
- tolerances: `1e-4` maximum absolute parity error;
- direct-effect gate: `1e-4` absolute change in the `A-B` final-logit margin;
- output: aggregate JSON only, external root
  `/tmp/astral-v27-public-abi-20260813`;
- validator: `tools/astral-public-abi-final-embedding-feasibility-v27/validator_v27.py`.

The runner emits no raw embeddings, logits, prompt text, control vector, or
generated model output. The execution is one-shot; no tuning or retry follows
an exposed result.

The initial launch stopped before inference because the runner mishandled the
public tokenizer's negative required-size return and did not use an orderly
abort path. No result JSON, raw output, or assessment data was produced. The
runner was corrected in-place within this execution slice; the corrected
compile and validation gates must pass before the one-shot run is retried.

The corrected retry then stopped at `llama_decode: n_tokens == 0`. Upstream's
public batch contract confirms that `llama_batch_init` allocates capacity while
leaving the active `n_tokens` field at zero; the runner now assigns the active
token count before decoding. No scientific output was produced by either stop.

The next graph reservation then stopped on `n_outputs_max <= cparams.n_outputs_max`.
Embedding mode can materialize one output per prompt token, so the runner now
binds `n_outputs_max` to the frozen prompt token count. No scientific output was
produced by that stop.

The final corrected run must emit the explicit
`LocalDevelopmentPublicAbiFinalEmbeddingFeasibility` claim ceiling and pass
`validator_v27.py`; that is the only result eligible for the V27 execution
record.

## Result ceiling

Any positive result supports only the V27 local public-ABI final-embedding
feasibility claim. A stop is infrastructure/instrument evidence, not a
scientific null. Neither outcome establishes causal-channel separation, faithful
computation, mechanistic explanation, provider cryptography, introspection,
consciousness, Stage 0C, Stage 1, benchmark evidence, or production readiness.
