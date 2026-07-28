# V28 Acquisition-Novelty Producer Boundary

State slice: `astral-rgs-v28-acquisition-novelty-producer`.

Status: `ImplementationAuthorized / CorpusNotGenerated /
ModelBackedBaselineNotRun / UpdateArmsNotAuthorized / AssessmentSealed`.

## Decision

The next executable V28 slice is only the Gate 1 novelty falsification. A clean
committed Recoverable Ghost States producer may hash the cached starting state,
generate one corpus without consulting model outputs, and run `pre_update` and
separately restarted `no_update`. It may not train or dispatch any update arm.

The Astral V28 validator remains the authoritative packet consumer. A valid
baseline-only packet can reach only
`NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun`. The referenced bytes
remain unverified until a later artifact-rehash slice is separately authorized.

## Frozen autoresearch contract

- Goal: determine whether one checkpoint-bound V28 qualification corpus is
  genuinely non-ceiling for the cached Qwen checkpoint.
- Writable scope: additive V28 producer source, script, focused tests, scoped
  authorization, validation registry, and producer notes in a clean RGS branch;
  this boundary note and append-only Astral navigation/status records.
- Read-only scope: V27 source and evidence, the cached model directory, Astral
  protocol V2 and validator, and all earlier Astral corpora and outcomes.
- Primary metric: both baseline arms pass the validator's two-sided
  chance-equivalence gate in every fact kind, query kind, seed/order cell, and
  overall.
- Direction: absolute chance-normalized lift and interval width must remain
  inside the frozen `0.05` boundary.
- Verification: RGS focused tests and gates, then Astral protocol V2 validation
  over the emitted baseline-only packet.
- Guard: V27 focused regressions and Astral V28 validator tests remain green.
- Budget: exactly one generated qualification corpus and one complete
  18-process-pair baseline matrix. No seed replacement after outcomes.
- Git policy: commit producer source before execution; execute only from a clean
  source tree; retain failed artifacts instead of rewriting them.
- Artifact policy: repository-external, content-addressed, no symlinks, raw
  inputs and four-choice scores retained, assessment content absent.

## Checkpoint-first sequence

1. Inventory checkpoint weights/config, tokenizer files, interpreter/platform
   and package versions, clean RGS commit/tree, generator bytes, and the exact
   Astral protocol bytes.
2. Durably write `checkpoint-receipt.json`.
3. Create a 256-bit seed and checkpoint-bound seed commitment.
4. Generate exactly 24 families for each of `nonce_fact`, `entity_relation`,
   `changed_rule`, and `opaque_mapping` from domain-separated hashes.
5. Seal raw UTF-8/NFC source, support, semantic AST, template catalog, option,
   query, and hash manifests before loading a tokenizer or model.
6. Lock scorer, prompt shell, four label completions, tie rule, required seeds,
   task orders, process semantics, and zero budgets.
7. For each of nine cells, run a distinct no-op state-preparation process and a
   fresh base-model evaluator for `pre_update`; repeat with new processes for
   `no_update`.
8. Join expected choices only after inference, retain all four raw scores, emit
   the baseline-only packet, and invoke Astral validation.
9. Stop regardless of outcome. A passing novelty packet authorizes a later
   docs-first update-arm slice; a failure retires this corpus and does not
   authorize regeneration.

## Corpus safeguards

Every family uses four symmetric rows so all candidate values appear equally in
source material. The target row, document order, aliases, wrappers, answer
permutations, and surface templates use separate derivation domains. Four
queries in each evaluation class rotate the same semantic answer through A-D
exactly once. Training and evaluation template families are disjoint; prompt
instances remain byte-unique. Exact, normalized, clause, typed-scaffold, and
cross-split overlap checks run before sealing.

Paraphrase queries depend on the source document. Multi-hop queries require
`alias -> anchor -> value`. Withheld compositions require
`wrapper -> alias -> anchor -> value`. Neither prompt contains the missing
premises. Changed rules use the same candidate set under old and new deranged
permutations so recency wording or token exposure cannot reveal the answer.

## Hard stops and claim ceiling

Any dirty source tree, mutable checkpoint inventory, protocol drift, seed
ordering violation, corpus overlap, answer-position imbalance, tokenizer label
failure, same-process reuse, observation mismatch, missing raw score, manifest
failure, non-chance baseline, or Astral validation error retains the failed
artifact and stops before updates.

This slice can establish only
`LocalModelBackedAcquisitionNoveltyPreflightV28`: a local author-run check that
the frozen corpus is not already solved by one cached model. It is not
acquisition, consolidation, retention, recovery, continual learning,
independent replication, benchmark evidence, a breakthrough, or authorization
to run Astral selection.
