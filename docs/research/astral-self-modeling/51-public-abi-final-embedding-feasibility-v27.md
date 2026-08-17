# Public-ABI Final-Embedding Intervention Feasibility V27

State slice: `astral-public-abi-final-embedding-feasibility-v27`.

Status: `Executed / PublicAbiFinalEmbeddingInterventionFeasible`.

V27 is a new protocol identity created after V26 stopped because the public
llama.cpp surface did not expose per-layer residual capture. It tests a narrower
question: can the local GGUF runtime support a reproducible controlled
intervention and final-embedding measurement through its public ABI?

V27 is not V26 executed by another name. It does not claim that final
embeddings are per-layer telemetry, and it cannot establish provider-artifact
behavior, faithful reasoning recovery, mechanistic explanation, or introspection.

## Capability question

Can one exact local runtime and one exact local GGUF actor satisfy all of these
requirements without network access or provider integration?

1. Load the declared GGUF through the declared llama.cpp shared library.
2. Tokenize a fixed prompt through the public vocabulary API.
3. Run a clean forward and capture final embeddings and selected logits.
4. Apply a declared control-vector intervention through
   `llama_set_adapter_cvec`.
5. Re-run with a zero vector and establish clean/zero parity.
6. Re-run with the nonzero vector and establish a non-silent direct logit
   effect.
7. Repeat the same condition and establish deterministic embedding/logit
   parity within a frozen tolerance.

The protocol stops before any observer training or causal-channel comparison if
the ABI, model load, tokenizer, parity, or behavioral-effect gate fails.

## Public ABI contract

The runner may bind only these public symbols:

```text
llama_backend_init
llama_backend_free
llama_model_default_params
llama_model_load_from_file
llama_model_free
llama_init_from_model
llama_free
llama_model_get_vocab
llama_model_n_embd
llama_model_n_layer
llama_batch_init
llama_batch_free
llama_tokenize
llama_decode
llama_get_embeddings_ith
llama_get_logits_ith
llama_set_adapter_cvec
```

No private symbols, C++ symbols, command-line scraping, provider endpoint,
network transport, or undocumented tensor access is admissible. The exact
header and shared-library digests must be recorded before model load.

The public surface returns final embeddings only. V27 must label them
`final_embedding_observation`; it must never label them `residual_telemetry`,
`mechanistic_state`, or `per_layer_capture`.

## Frozen local inputs

- actor: `/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_K_M.gguf`;
- runtime: `/opt/homebrew/Cellar/llama.cpp/10050/lib/libllama.0.0.10050.dylib`;
- public header: `/opt/homebrew/Cellar/llama.cpp/10050/include/llama.h`;
- runtime library SHA-256:
  `25aa1419a298e05a6bbd340c5bccafffb836e15e1ac42460b31fcd4a089df2ff`;
- runtime header SHA-256:
  `2331631b6a3567311abc0402c55aa9a867ee99759f2550bdfa261ec3693a21f6`;
- actor size: `5,627,044,256` bytes;
- actor identity: GGUF Qwen3.5 9B Q4_K_M, pending metadata capture by the
  model-loading preflight;
- protocol seeds: control `26082701`, repeat `26082702`, bootstrap `26082703`.

These are frozen local inputs for feasibility. Their presence does not imply
that model execution is authorized.

## Intervention and gates

The first execution candidate uses one normalized control vector over a single
declared layer range. The exact vector bytes, dimension, layer range, prompt,
token pair, and tolerances must be sealed before model load. The vector is an
intervention instrument, not a semantic concept direction.

Required gates, in order:

1. ABI symbol and header consistency;
2. actor file identity and no-follow path checks;
3. model load and vocabulary identity;
4. clean forward success with finite final embedding/logits;
5. zero-vector output parity against clean output;
6. repeated clean and zero-vector parity;
7. nonzero-vector direct logit-effect threshold;
8. repeated nonzero-vector direction agreement;
9. read-only export of aggregate receipts and digests.

Any failure is a named stop. There is no adaptive vector, prompt, layer,
threshold, or tolerance search after the first exposed result.

## Claim ceiling

If all V27 gates pass, the maximum claim is:

> The declared local llama.cpp public ABI and one declared local GGUF actor
> supported a reproducible final-embedding observation and a controlled-vector
> intervention with a directly measured output effect under the frozen
> feasibility harness.

This remains below `LocalDevelopmentCausalChannelSeparation`. It does not
authorize V26, Stage 0C, Stage 1, observer training, artifact decoding,
provider cryptographic claims, faithful computation claims, consciousness,
general introspection, benchmark evidence, production readiness, or accepted
Evidence Ledger status.

## Retention and authority

Only aggregate receipts, digests, dimensions, finite-value checks, parity
metrics, effect metrics, and stop codes may be retained. No prompts, raw
embeddings, logits, control vectors, model outputs, credentials, PII, or
provider artifacts may enter the repository. The control vector may be stored
only in a separately approved external bundle if needed for reproduction.

V27 output has no authority to mutate state. It remains local development
diagnostic evidence.
