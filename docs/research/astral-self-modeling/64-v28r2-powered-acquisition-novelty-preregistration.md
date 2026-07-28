# V28R2 Powered Acquisition-Novelty Preregistration

State slice:
`astral-rgs-v28r2-powered-acquisition-novelty-preregistration`.

Status: `DocsFirstPreregistered / R1CorpusNotNovelRetired /
R2PowerProfileLocked / R2ImplementationNotAuthorized /
R2CorpusNotGenerated / R2ModelBackedExecutionNotRun /
UpdateArmsNotAuthorized / Gate2SealedNotAuthorized /
Gate3SealedNotAuthorized / AssessmentSealedNotAuthorized`.

## Decision

The first V28 acquisition-novelty corpus, `V28R1`, is a valid negative
falsification result. Its `pre_update` and separately restarted `no_update`
observations were deterministic and identical, and both point estimates were
close to four-choice chance. The corpus still failed the frozen two-sided,
multiplicity-adjusted family-cluster equivalence gate because some stratified
intervals were too wide. The authoritative disposition is `CorpusNotNovel`.

V28R1 is permanently retired. It may not be regenerated, expanded, pooled with
a replacement corpus, used to select replacement items, or treated as
acquisition evidence. No update arm ran.

This note preregisters a distinct `V28R2` corpus campaign with a
pilot-informed precision floor. It does not authorize implementation, seed
creation, corpus generation, tokenizer or model access, baseline execution,
update arms, retention/recovery, Astral selection, or assessment.

## V28R1 retained negative

The one-shot V28R1 run completed 18 unchanged-checkpoint baseline cells over 96
knowledge families and 1,152 evaluation queries. Both arms reached overall
accuracy `0.2517361111` against chance `0.25`. The stopped bundle retains:

- acquisition packet
  `sha256:2fd74b389907d3167518a0d91d9d63f18fda7c1231a51764657e791286ee2ad0`;
- Astral validation report
  `sha256:3e24804dc84744a300bb11bc246fdfd40256459f97a68da0df7993d676b9ea3d`;
- artifact manifest
  `sha256:5b01a32e1ba9d7d9ce84c8b301f29e0145962ac8c0eac0ec59b07cd5cfca846e`.

The validation report contains no structural error and opens only
`acquisition.new_corpus_required`. Gate 2 and Gate 3 remain sealed.

## Frozen V28R2 census

V28R2 contains exactly 1,536 complete knowledge families for each of:

1. `nonce_fact`;
2. `entity_relation`;
3. `changed_rule`;
4. `opaque_mapping`.

The total is 6,144 qualification families. Every family contains exactly four
paraphrase, four multi-hop, and four withheld-composition queries, for 12
queries per family and 73,728 evaluation queries. Each family/query-class cell
rotates the semantic answer through A-D exactly once.

The census is a floor and a ceiling. It may not be reduced after a favorable
preflight, increased after an unfavorable baseline outcome, or stopped early.
All four fact kinds and all three query classes are independently reported.

### Conservative precision and power calculation

V28R1 is used only to motivate rejecting the 24-family census and to report
sensitivity. It is not an inferential row in V28R2. The primary V28R2 design
does not assume that V28R1's unusually low observed variance will recur.

Under an independent 12-query four-choice chance model, the standard deviation
of family-level chance-normalized lift is `1/6`. V28R2 conservatively freezes a
design effect of `2.0`, giving planning standard deviation
`sqrt(2) / 6 = 0.2357022604`. The planning point permits true absolute
chance-normalized lift `0.01`. The calculation keeps the frozen minimum
critical value `5.0` and adds `1.64485363` standard errors for a central 90%
normal-approximation design bound, equivalent to at least 95% one-sided pass
probability at the positive planning boundary under the frozen planning model:

```text
n_min =
  ((5.0 + 1.64485363) * 0.2357022604
    / (0.05 - 0.01))^2
  = 1533.1278
```

V28R2 freezes 1,536 families per fact kind: the smallest 24-family multiple
above the computed minimum. The multiple preserves a complete cycle over the
24 permutations of four surface-template identities against four correct-label
positions. At `n = 1,536`, the projected standard error is `0.0060140653`, and
the corresponding design bound is:

```text
0.01 + (5.0 + 1.64485363) * 0.0060140653
  = 0.049962584
```

This is an assumption-based conservative design, not a guarantee. A
distribution-free worst-case construction would require a materially larger
census. The V28R1 plug-in minimum is only 72 families per fact kind, and an
upper-variance pilot calculation would still give only about 87% pass
probability at 192; neither is the frozen design. The equivalence margin,
critical value, familywise error rate, reporting strata, and fail-closed
disposition do not change.

## Statistical gate remains unchanged

Chance is `0.25`, with:

```text
chance_normalized_lift = (accuracy - 0.25) / 0.75
```

For both `pre_update` and `no_update`, every required overall, fact-kind, and
query-class family-cluster interval must lie wholly inside `[-0.05, 0.05]`.
The validator continues to use the frozen minimum Student-t critical value
`5.0` and familywise alpha `0.05`. The exact baseline comparison census is 16
two-sided hypotheses: two arms times eight dimensions consisting of overall,
four fact kinds, and three query classes. The Bonferroni-adjusted per-hypothesis
alpha is therefore `0.003125`; the critical value used by the validator may
not be lower than `5.0`. A point estimate inside the margin is insufficient. A
systematic below-chance result fails symmetrically.

Any interval crossing either boundary returns `CorpusNotNovel`, permanently
retires V28R2, and stops before updates. The result may not be repaired by
changing the seed, adding families, removing difficult strata, rejecting
items, editing aliases, relabeling answers, or rerunning a second corpus under
the same campaign.

## Baseline process census

The unchanged-checkpoint novelty check uses exactly two scientific baseline
runs:

1. `pre_update`: a fresh model load before any update-data processing;
2. `no_update`: a distinct no-op preparation process followed by a separately
   restarted fresh evaluator after all corpus source material is removed from
   the evaluation workspace.

Each run scores all 73,728 queries, for 147,456 total baseline query
evaluations. Process identities, runtime inventories, raw four-choice scores,
tie rules, prompt hashes, and row-to-manifest bindings are retained. Exact
row-level `pre_update`/`no_update` parity is mandatory.

The V28R1 3-seed by 3-order repetition demonstrated deterministic
unchanged-checkpoint parity but did not create independent seed or order
clusters. V28R2 therefore does not repeat the same frozen model eighteen times
or present process duplication as statistical replication. Family clusters
are the novelty gate's statistical units.

This baseline simplification does not alter the future update-arm design. If
V28R2 qualifies and a later slice authorizes updates, every persistent arm must
still run the frozen three update seeds by three task orders under matched
budgets. The single restarted `no_update` result is the deterministic matched
reference for every update cell.

## Complete nonreuse boundary

V28R2 must use new, prospectively committed identities for:

- campaign, protocol, packet, corpus, power profile, and one-shot execution
  ledger;
- generator and validator versions, source digests, namespace, and
  domain-separation labels;
- configuration and protocol packet;
- seed and checkpoint-bound seed commitment;
- source documents, facts, entities, relations, rules, symbols, values,
  aliases, wrappers, templates, option permutations, and prompt instances;
- qualification, development, tuning, and future-assessment family IDs;
- future-assessment identity commitment.

V28R1 generator bytes, seed, namespace, concepts, candidate values, semantic
ASTs, aliases, templates, prompts, family identities, future-assessment
identities, and model outcomes are forbidden inputs. V18-V27 data and exposed
outcomes remain forbidden.

The V28R1 packet may be read only by the independently bounded retired-corpus
fingerprint builder and validator. The V28R2 generator receives neither R1
rows nor R1 model outcomes. V28R1 and V28R2 may never be pooled for a
qualification or acquisition claim.

A manifest-level disjointness validator must compare V28R2 with the sealed
V28R1 inventory across seed commitments; family, item, query, namespace,
concept-schema, anchor, value, alias, and wrapper IDs; source, support,
question, prompt, option, and dependency hashes; and training/evaluation
template IDs and canonical AST hashes. Normalized template skeletons, source
lines, question lines, and structural n-grams must also be disjoint. Renaming a
V28R1 template or substituting fresh nonce strings into the same typed skeleton
must fail before model access.

## Prospective generation boundary

Before the V28R2 seed exists, a future implementation must:

1. re-inventory and hash the exact starting checkpoint, tokenizer, runtime,
   clean source commit/tree, generator, validator, and protocol bytes;
2. seal the 1,536-per-kind census, power profile, concept and template
   catalogs, canonical
   template ASTs, derivation grammar, split commitments, scorer, prompt shell,
   labels, tie rule, process semantics, and future-assessment identity
   commitment;
3. seal a ledger schema that binds the hashes of every item in steps 1 and 2,
   the retired-V28R1 fingerprint inventory, output root, checkpoint receipt,
   tokenizer, generator, validator, protocol, source commit, and source tree;
4. create and exclusively claim the new fixed repository-external campaign
   ledger, then durably sync the ledger and its parent directory;
5. create the seed only after the receipt and exclusive ledger claim are
   durable;
6. generate and validate the complete corpus without loading the model;
7. reject the campaign before model access on any overlap, leakage, semantic,
   balance, provenance, or manifest failure.

Within each 24-family block, the four evaluation templates and four answer
positions use all 24 permutations. Thus template identity and correct-label
position are orthogonal within every fact-kind/query-class block without
inflating the statistical cluster count. Repeated queries and repeated
processes never count as additional family clusters.

The generator may not query a model, use token probabilities, reject or revise
items based on model behavior, conduct a model-backed pilot run, adaptively
stop, or replace the seed. Any failure or negative result consumes the
one-shot campaign and retires V28R2 without replacement.

## Future implementation boundary

A later, separately authorized implementation must be additive. It must not
mutate the retired V28R1 producer, protocol, validator, packet, corpus, ledger,
or artifacts. Candidate composed-repository paths are:

```text
tools/astral-rgs-acquisition-v28r2/protocol.json
tools/astral-rgs-acquisition-v28r2/v28r2.py
tools/astral-rgs-acquisition-v28r2/validate_packet.py
tools/astral-rgs-acquisition-v28r2/tests/test_v28r2.py
```

Candidate RGS paths are:

```text
docs/v28r2-powered-acquisition-novelty-producer.md
mesh_brain/meshmodel/v28r2_acquisition.py
mesh_brain/meshmodel/v28r2_acquisition_mlx.py
scripts/run_v28r2_acquisition_novelty.py
tests/test_v28r2_acquisition.py
```

These paths describe a future review surface. They are not implementation
authority.

### Required V28R2 validator contract

The future additive validator must fail closed unless it independently
recomputes and verifies:

- exactly 1,536 families per fact kind, 12 queries per family, 73,728 canonical
  queries per run, and exactly two baseline runs;
- family/query-class answer balance and every 24-family
  template-to-answer-position permutation cycle;
- the power profile, concept catalog, template catalog, retired-R1 fingerprint
  inventory, checkpoint receipt, and one-shot ledger were sealed before the
  seed;
- exactly one seed draw, one candidate corpus, no discarded candidate, no
  optional extra family, no adaptive expansion, and no post-seed power change;
- complete R1/R2 identifier, content, template-AST, normalized-skeleton, and
  structural-n-gram disjointness;
- an allowlisted generator input inventory with no model, tokenizer scores,
  V28R1 observations, or V28R1 item rows;
- distinct preparation and evaluation process identities for each arm and a
  fresh checkpoint reload for `no_update`;
- one canonical score row per sealed query, with no unknown, missing,
  duplicate, reordered, or rebound row;
- exact prompt-byte and tokenized-input hashes, four finite label scores,
  scorer configuration, tie rule, and independently recomputed argmax;
- exact cross-arm checkpoint, implementation, prompt, score, argmax, and
  observation parity;
- family clusters, not prompts or restart processes, are the only statistical
  units;
- every overall, fact-kind, and evaluation-kind equivalence interval lies
  inside `[-0.05, 0.05]`;
- hard absence of update, retention/recovery, selection, and assessment
  material.

The validator is a clean-room protocol consumer. It may not import, call, or
reuse V28R1 or V28R2 generator code or generator objects. From protocol-owned
logic and packet bytes, it must independently reconstruct corpus semantics,
canonical concept and template ASTs, the complete 24-permutation census,
canonical prompts, hashes, and every R1/R2 disjointness decision. Its only R1
input is a pinned, content-addressed fingerprint manifest; it may not load an
R1 generator module, corpus object, or observation row.

At minimum, hermetic adversarial coverage must include sealed-power-plan
ordering; exact corpus and query censuses; repeated-process nonindependence;
distinct restart processes; generator input denial; deterministic generation;
R1 namespace/content/template-skeleton rejection; training/evaluation
skeleton disjointness; blockwise template/position balance; atomic one-shot
ledger races; permanent retirement after failure; R1 ledger/seed rejection;
counterfeit, unknown, missing, duplicate, swapped, and rebound score rows;
prompt/token/argmax binding; point-near-chance but interval-failing behavior;
stratum failure despite an overall pass; and rejection of later-gate material.
It must also reject renamed and rehashed R1 templates and a malformed corpus
that is internally consistent with the generator but violates the independent
protocol reconstruction.

## Sealed downstream gates

A V28R2 novelty pass would establish only
`LocalModelBackedAcquisitionNoveltyPreflightV28R2` after a separately
authorized implementation, clean committed execution, artifact rehash, and
validator pass. It would not establish acquisition and would not itself
authorize an update arm.

Gate 1 update-arm execution requires a later docs-first authorization. That
includes context-only, retrieval, sequential LoRA, replay, SCoL-style, and
nested/multiscale arms. Gate 2 retention and real process-level
corruption/restart/rollback/replay remains sealed until at least two native
persistent arms pass Gate 1. Gate 3 prospective Astral selection remains sealed
until Gate 2 passes and multiple arms exhibit a statistically supported
acquisition-retention tradeoff. Assessment remains unopened.

The breakthrough gate in the parent V28 protocol is unchanged. This
preregistration is not acquisition, consolidation, continual-learning
evidence, replication, benchmark evidence, a breakthrough, self-improvement,
introspection, self-modeling, Stage 0C or Stage 1 evidence, or production
evidence. Its maximum claim is
`LocalProspectivePoweredAcquisitionNoveltyProtocolV28R2`.
