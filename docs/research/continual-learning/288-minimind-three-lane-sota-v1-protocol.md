# MiniMind three-lane continual-learning comparison V1

State slice: `continual-learning-minimind-three-lane-sota-v1`.

This protocol defines a bounded comparison harness for a small MiniMind model
across task-incremental, domain-incremental, and experience-incremental lanes.
The requested frontier methods and the local research are inputs to the audit
and method roster, not evidence that this pilot reproduces those methods. The
audit is recorded in [287](287-minimind-state-of-the-art-comparison-audit-v1.md).

## Scientific boundary

The published-benchmark lane is not executed by V1. The fixture corpus is
synthetic and contains no AG News, Amazon Reviews, Yelp, DBpedia, Yahoo
Answers, DAPset, TWEET, CL-Bench, ContinualSkillBench, or real local-domain
records. Consequently V1 cannot claim benchmark accuracy, domain-CPT BPB,
experience-learning superiority, a frontier-method reproduction, or global
SOTA. Its model ceiling is
`LocalDevelopmentMiniMindThreeLanePilotQualification`.

The model path uses a freshly checked-out, digest-bound MiniMind source tree
and a deterministic randomly initialized dense `minimind-3-dense` instance.
The upstream checkout contains no base checkpoint in this slice. The model
run therefore validates the integration, update paths, checkpoint restoration,
repeatability, and aggregate accounting only. It is not a pretrained-model
result.

## Lane definitions

The task lane has the declared task roster `ag_news`, `amazon_reviews`,
`yelp`, `dbpedia`, and `yahoo_answers`. Its fixed primary metric is final
macro held-out accuracy in a future full campaign. The V1 fixture exercises
the same task identities through bounded target vectors.

The domain lane has the declared domain-incremental roster DAPset/TWEET plus
a fresh real local-domain corpus in the future published campaign. V1 uses
the fixture identities `materials`, `clinical`, and `finance`; its primary
metric is only a synthetic held-out target loss. No domain-CPT claim is made.

The experience lane models ordered software, forecasting, and database
interaction trajectories. Experience is represented separately from transient
request context and KV cache. The declared arms are `stateless`, `naive_icl`,
`retrieval_memory`, `skill_library`, `parametric_experience_update`, and
`hybrid_experience_update`. The future primary metric is normalized held-out
gain over the stateless arm, with context and exact-answer retrieval removed
from the held-out evaluation. V1 exercises the state/accounting schema with
synthetic transitions and a bounded MiniMind context/state wrapper; it makes
no experience-learning claim.

Each lane has disjoint fit, tune, and assessment identities. Three replicate
seeds and both seeded forward/reverse order directions are used by the
synthetic campaign. Assessment is emitted only after every arm has a tune
lock. Every arm receives assessment; tune does not select a single arm and
discard the others.

In the model pilot, `naive_icl` prefixes the held-out query with the ordered
fit transcript, `retrieval_memory` exposes one deterministic retrieved fit
record, `skill_library` exposes structured procedural entries, and
`hybrid_experience_update` combines the latter two with a parametric update.
`stateless` and `parametric_experience_update` are evaluated without external
context after their declared update boundary.

## Methods

The required comparison panel is represented in the synthetic contract:

`untouched_base`, `joint_oracle`, `sequential_full`, `shared_lora`, `replay`,
`ewc_lwf`, `independent_adapters`, `task_routed_bank`, `o_lora`, `n_lora`,
`oplora`, and `osft`.

The model pilot executes only `untouched_base`, `sequential_full`,
`shared_lora`, and `replay` in the parameter lanes, plus all six explicit
experience arms. `ewc_lwf`, independent adapters, the routed bank, O-LoRA,
N-LoRA, OPLoRA, and OSFT are recorded as exclusions because no faithful
MiniMind implementation is frozen in V1. OLieRA, ASO-LoRA, DAS,
HPrompt-CPT, and stability-gap sampling are also excluded from the pilot.
An excluded method is not a baseline result and cannot be described as
beaten.

`joint_oracle` is a synthetic control only. A future full study must implement
each published method from its source and bind its code, hyperparameters,
data, and accounting separately before admitting it to a SOTA comparison.

## Accounting and guards

Every aggregate row binds lane, arm, split, replicate seed, order seed,
direction, exact item order, stage count, primary metrics, forgetting,
forward transfer, compute units, persistent state bytes, and hard guards.
The model path additionally records tokenized train/evaluation/context tokens,
trainable parameter count, optimizer steps, adapter bytes, memory reads/writes,
checkpoint restoration, and repeated inference error. A future full campaign
must additionally add routing decisions and reset/deletion receipts. No
resource quantity may be represented by an unmeasured zero.

The synthetic fixture requires complete stage coverage, zero attrition, equal
budget, held-out experience evaluation, and explicit state accounting. The
model pilot additionally requires finite outputs, checkpoint restoration at
`1e-12` maximum absolute error, and repeated evaluation at `1e-12` metric
error. Results are aggregate-only; raw prompts, trajectories, activations,
and checkpoints are not written to the result root.

## Execution gates

1. The exact source, protocol, review packet, manifest, runner, validator,
   tests, and current `AGENTS.md` bytes are frozen.
2. The fresh fixture source and corpus manifests pass custody, freshness,
   disjointness, and prior-artifact exclusion checks.
3. The synthetic campaign and independent validator pass with the exact
   roster and phase order.
4. An external trust bundle, reviewer registry, and operator binding are
   verified. A reviewer identity distinct from the operator reviews the exact
   packet and returns a packet-bound Ed25519 `ACCEPT`.
5. Only after that receipt passes both the runner and independent validator
   custody checks may the offline model pilot start.
6. The model contract must pass independent validation. Any failed gate closes
   V1; no adaptive retuning, method shopping, or assessment reinterpretation
   is allowed.

The runner refuses a missing, stale, malformed, self-attested, or
cryptographically invalid receipt. The operator cannot create an acceptable
review receipt. Network access is prohibited during model import, training,
and evaluation; the only network activity in this slice is frozen source
acquisition before the source manifest is written.

## Claim ceiling

The synthetic disposition is at most
`LocalDevelopmentMiniMindThreeLaneSyntheticQualification`.

The model disposition, if all gates pass, is at most
`LocalDevelopmentMiniMindThreeLanePilotQualification`.

Neither disposition is a benchmark result, a published-method reproduction,
a general continual-learning claim, a SOTA claim, an energy claim, a
production-readiness claim, or evidence about introspection or self-modeling.
