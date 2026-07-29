# V29R2 Canonical Token-Boundary Preregistration

State slice: `astral-rgs-v29r2-canonical-token-boundary-preregistration`.

Status: `DocsFirstPreregistered / ImplementationNotAuthorized / NotRun`.

V29 is immutable and negative. The post-result tokenizer audit produced a
single falsifiable repair: V29 ended its prefill with standalone space token
`220` and then scored bare A-D tokens `32/33/34/35`, although canonical
`Answer: X` tokenization uses leading-space tokens `362/425/356/422`.

V29R2 holds the 64-case fixture, prompts, label balance, checkpoint, runtime,
batch 8, and four eligibility thresholds byte-for-byte fixed. It tests only
chat-template serialization plus `Answer:` without trailing space and the four
canonical leading-space label tokens. Prefix-plus-label tokenization must equal
direct `Answer: X` tokenization for every label.

One model process produces 64 observations. Astral independently verifies the
fixture hash, exact token identities and concatenation property, score argmax,
four rung accuracies, process/source/model identities, packet, and manifest.
The only valid statuses are `CanonicalBoundaryQualified` and
`CanonicalBoundaryStillBlocked`.

Maximum claim: `LocalCanonicalTokenBoundaryQualificationV29R2`. Training,
candidate data, acquisition, continual learning, self-improvement, SOTA, and
breakthrough remain untested.
