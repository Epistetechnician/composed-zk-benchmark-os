# V30 Response-Free Evaluator Qualification Preregistration

State slice: `astral-rgs-v30-response-free-evaluator-preregistration`.

Status: `DocsFirstPreregistered / ImplementationNotAuthorized / NotRun`.

V30 replaces the falsified A-D channel with answer-content scoring. A public,
deterministic 32-case fixture covers literal, direct, one-hop, and two-hop
positive controls. Each case has four ordinary-word candidates that are exactly
one leading-space token under both frozen tokenizers.

Qwen 0.5B and Llama 1B each receive 32 positive and 32 matched null prompts in
one process. Restricted content likelihood, positive-minus-null contrastive
likelihood, and full-vocabulary greedy exact-content prediction reuse those same
logits. Wrong-dossier and reversed-candidate controls require no additional
model forwards.

Positive floors are `0.95/0.90/0.80/0.70`; null and shuffled accuracy must not
exceed `0.375`; permutation invariance must be exact. Select the simplest fully
passing evaluator per checkpoint. Only the lowest-resource qualified checkpoint
may enter a separately preregistered tiny-acquisition sanity check.

Maximum claim: `LocalResponseFreeEvaluatorQualificationV30`. No training,
acquisition, continual learning, self-improvement, SOTA, or breakthrough is
tested here.
