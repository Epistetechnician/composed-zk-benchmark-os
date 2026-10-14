# V40 Tokenizer Qualification Authorization

Status: `AuthorizedOnce / NotRun`.

Authorize an offline tokenizer-only report binding the committed V40 corpus,
cached Qwen tokenizer inventory, canonical answer-boundary token ids, candidate
distinctness, and 96-token prompt-window compatibility. Any failure retires the
corpus. No forward pass, telemetry, gradient, fitting, assessment, download,
network access, or in-place corpus repair is authorized.
