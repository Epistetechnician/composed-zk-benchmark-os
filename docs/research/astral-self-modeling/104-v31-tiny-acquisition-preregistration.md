# V31 Tiny Acquisition Sanity Check Preregistration

State slice: `astral-rgs-v31-tiny-acquisition-preregistration`.

Status: `DocsFirstPreregistered / ImplementationNotAuthorized / NotRun`.

V31 uses only the lowest-resource V30-qualified checkpoint, Qwen 0.5B, and the
locked content-likelihood evaluator. It freezes 16 new entity-to-value
associations, separate source/direct/paraphrase templates, a rank-4 LoRA,
eight trainable layers, 64 gradient steps, batch 4, and at most 16,384 update
tokens.

Qualification requires pre-update direct accuracy at most 0.375, post-reload
direct accuracy at least 0.875, improvement at least 0.50, paraphrase accuracy
at least 0.75, protected V30 accuracy drop at most 0.02, exact no-update
replay, and post-save/reload score agreement within `1e-5`.

Maximum claim: `LocalTinyAcquisitionSanityV31`. No continual-learning,
self-improvement, SOTA, breakthrough, assessment, or confirmation claim is
authorized.
