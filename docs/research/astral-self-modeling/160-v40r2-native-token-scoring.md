# V40R2 Native Tokenization and Scoring

State slice: `V40R2NativeMLXTokenizationScoring`.

Status: `TokenScoringImplemented / OptimizerRuntimeIncomplete`.

The native boundary now enforces the exact chat-template and `Answer:` token
position, the 96-token ceiling, unique canonical one-token candidates, stable
candidate-set log probabilities, deterministic tie-breaking, and hashed score
receipts.

Hermetic tests use a fake tokenizer and synthetic logits. No model or tokenizer
artifact was loaded, and no forward pass occurred. LoRA/AdamW update execution,
telemetry-gradient caching, and runtime integration remain incomplete.
