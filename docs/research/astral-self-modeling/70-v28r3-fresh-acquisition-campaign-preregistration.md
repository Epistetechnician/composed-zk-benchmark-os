# V28R3 Fresh Acquisition Campaign Preregistration

State slice:
`astral-rgs-v28r3-fresh-acquisition-campaign-preregistration`.

Status: `DocsFirstPreregistered / ImplementationAuthorized /
RuntimeNotAccessed / CorpusNotGenerated / CampaignNotRun`.

## Decision

V28R3 is a new campaign, not a resume or replacement of the consumed V28 Gate
1 ledger. It requires a new generator, namespace, 256-bit seed, corpus,
baseline observations, artifact root, and ledger. It retains the V28R3 result
regardless of sign and cannot substitute any V28R1 or V28R2 row or model
outcome.

For efficiency, novelty and acquisition are one sequential campaign. The
baseline novelty gate must pass before any context control, update process, or
adapter exists. A novelty failure stops the campaign. A novelty pass unlocks
the already-frozen Gate 1 comparison matrix without another corpus or ledger.

## Immutable predecessors

- V28R1 is retired as `CorpusNotNovel`.
- V28R2 novelty packet:
  `sha256:5e830ee437e8d67faa9dedc667db35114fa5ccf84809a9b2874c60a1ed622ddc`.
- V28R2 corpus manifest:
  `sha256:0264b3c922e567f53f539e09582cea1becb60156b1a92dbbe7906f3541b460a2`.
- consumed Gate 1 abort manifest:
  `sha256:7c343e7c2894745ea9506bd43173af4f2b97ebe371b3fcc89c691558e801d1c4`.
- cached checkpoint inventory:
  `sha256:0a321941ffa31f920284c932f98bd4dba7c7cb95acd797c01ec2fa0fdd1321ab`.
- required worker executable:
  `/Users/shaanp/.pyenv/versions/3.14.5/bin/python`.
- required runtime versions: Python `3.14.5`, MLX `0.31.2`, MLX-LM `0.31.3`,
  NumPy `2.4.5`.

## Pre-ledger gates

Before a ledger or seed exists, the coordinator must verify:

1. both repositories are clean and committed;
2. the worker executable resolves to the frozen path and imports the exact
   runtime versions;
3. the model and tokenizer inventory equals the frozen checkpoint identity;
4. at least `30 GiB` is available on the artifact volume;
5. the V28R1 retired fingerprint, complete V28R2 corpus, V28R2 packet, and
   consumed-abort manifest rehash exactly;
6. generator, worker, coordinator, protocol, and validator bytes are frozen;
7. no V28R3 ledger, seed, namespace, corpus, or artifact directory exists.

Failure before ledger creation is a non-consuming preflight rejection and
creates no campaign identity. After the exclusive ledger is written, every
failure is consuming.

## Fresh corpus and nonreuse

After the ledger is durable, generate one 256-bit seed from OS entropy, write
its commitment before its plaintext, and generate exactly:

- 1,536 families per fact kind;
- 6,144 families total;
- 12 queries per family;
- 73,728 queries per run;
- four answer positions exactly balanced inside every family;
- three query classes: paraphrase, multi-hop, withheld composition.

The namespace prefix is `r3`. Fact semantics remain nonce fact, entity
relation, changed rule, and opaque mapping, but every identifier, lexical
surface, question template, source/support template, semantic AST, normalized
skeleton, and structural seven-gram must be disjoint from both V28R1 and
V28R2. The generator may consume only sealed fingerprints, never predecessor
model outcomes for content selection. Corpus generation finishes before model
loading and cannot be repeated.

## Phase A: novelty gate

Run exactly one `pre_update` and one separately prepared/restarted `no_update`
full-corpus baseline. Both have zero update tokens and use fresh model
processes. Join labels only after inference. Require exact row parity and the
unchanged family-cluster equivalence gates:

- absolute chance-normalized lift at most `0.05` overall;
- the same interval containment per fact kind and query class;
- critical value at least `5.0`;
- identical checkpoint, tokenizer, prompts, token IDs, and scorer.

Any novelty failure returns `CorpusNotNovel` and seals the campaign before
updates.

## Phase B: acquisition gate

Only after novelty passes, run:

- nonpersistent `context_only` and deterministic lexical `retrieval` controls;
- `naive_sequential_lora`;
- `replay_lora` with 25% deterministic reservoir replay after task one;
- `scol_style_sparse_lora` with source-only gradient ranking and the top third
  of six LoRA layers plastic;
- `nested_multiscale_lora` with fast/medium/slow clocks of 1/2/4 steps;
- `modular_ghost_state`;
- `compressed_adapter_recollection` with deterministic int8 rehydration;
- `representation_time_distillation` with source-only prior-task anchors.

Persistent seeds remain `280301`, `280303`, and `280307`; task orders remain
`order-abcd`, `order-acdb`, and `order-bdac`. Every cell uses rank 8 over six
layers, 768 optimizer steps, 8 examples per step, 128 tokens per example,
786,432 presented tokens, learning rate `0.0001`, and at most 67,108,864 state
bytes. Update processes receive source/support rows only.

The balanced 96-family superblock futility rule, overall floor `0.70`,
fact-kind/query-class floor `0.60`, gain floor `0.20`, critical value `5.0`,
10,000 family-paired stratified bootstrap draws, and Bonferroni correction
across seven persistent arms remain unchanged.

## Transactional execution

Every completed process output is written exclusively, fsynced, hashed, and
recorded in an append-only campaign journal before the next process starts. A
restart may reuse a completed artifact only after full byte verification; it
may never rerun that process. An incomplete or crashed update/evaluation cell
disqualifies its arm and triggers the frozen skip rule. A control or provenance
failure makes the campaign invalid. No outcome-dependent repair is allowed.

## Disposition and claim ceiling

- novelty failure: `CorpusNotNovel`;
- novelty pass and zero qualified persistent arms: `AcquisitionNoCandidate`;
- exactly one: `AcquisitionSingleCandidate`, with Gate 2 sealed;
- at least two: `AcquisitionQualifiedCandidates`, still local and subject to
  Gate 2;
- any provenance, leakage, runtime, artifact, or control defect: `Invalid`.

Gate 2, Gate 3, assessment, confirmation, independent replication, benchmarks,
and public breakthrough claims remain sealed. The maximum claim before model
execution is `LocalProspectiveFreshAcquisitionCampaignV28R3`.
