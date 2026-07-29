# V28R5 Last-Token Projection Preflight Preregistration

State slice:
`astral-rgs-v28r5-last-token-projection-preflight-preregistration`.

Status: `DocsFirstPreregistered / ImplementationNotAuthorized / NotRun`.

V28R4 established exact batch-8 streaming parity but failed batch 64. The
frozen scorer currently constructs logits for every sequence position although
the metric reads only the last position. V28R5 prospectively tests projecting
only the last hidden token into vocabulary space.

The fixed public V28R4 fixture is reused and remains non-candidate. The sealed
V28R4 monolithic batch-8 result file
`sha256:9cdade169d775a027361029fd8fe203eb23a4bc536b5b27c8a0daf81caa71227`
is copied as the immutable reference; it may not be rerun. Optimized batch 8
and batch 64 must both preserve every semantic field and prediction with score
drift at most `1e-5`, complete under the 8 GiB child-RSS gate, prove that output
logits have shape `[batch, vocabulary]`, retain frozen identities, and pass
independent validation.

This is infrastructure optimization only. No candidate, update, acquisition,
continual-learning, assessment, confirmation, or breakthrough evidence can be
created by this preflight.
