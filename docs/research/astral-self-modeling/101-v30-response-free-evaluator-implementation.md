# V30 Response-Free Evaluator Implementation

State slice: `astral-rgs-v30-response-free-evaluator-implementation`.

Status: `Implemented / HermeticValidationComplete / ModelExecutionUnauthorized`.

The V30 implementation provides a two-process coordinator for the frozen Qwen
0.5B and Llama 1B checkpoints and a separate Astral validator. The model worker
retains positive and null likelihoods for all 32 public content tokens, exact
greedy-token outputs, token identities, process budgets, and every derived
decision. The Astral validator reconstructs the fixture and all 576 decisions
without model execution.

The coordinator fails closed on dirty source bindings, checkpoint or tokenizer
drift, an existing consuming ledger, a prior V30 artifact, process failure,
manifest mismatch, source-lock mismatch, budget drift, or independent
validation failure. Exactly 64 prompt forwards are allowed per checkpoint and
128 total. No training, adapter, candidate corpus, acquisition, or assessment
path exists in this slice.

Maximum claim: `LocalUnexecutedResponseFreeEvaluatorInstrumentV30`.
