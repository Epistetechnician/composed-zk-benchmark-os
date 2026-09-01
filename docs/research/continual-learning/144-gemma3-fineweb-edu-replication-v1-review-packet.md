# Independent review packet: Gemma3 FineWeb-Edu fresh-cohort replication V1

State slice: `continual-learning-gemma3-fineweb-edu-replication-v1`

Review status: `PENDING`

This packet is for an independent reviewer. The authoring agent must not
self-accept it. The reviewer must inspect the listed immutable r1 receipts,
the frozen protocol, and the validator implementation before any fresh
assessment effect is executed.

## Materials for inspection

- Frozen protocol:
  `docs/research/continual-learning/143-gemma3-fineweb-edu-replication-v1-protocol.md`
- r1 source root:
  `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1`
- r1 corpus root:
  `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-corpus-v1`
- r1 result root:
  `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-recirculation-v1`
- Cached model:
  `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`
- Existing independent validator:
  `experiments/continual_learning/validate_gemma3_fineweb_edu_bounded_v1.py`
- Existing r1 execution record:
  `docs/research/continual-learning/138-gemma3-fineweb-edu-bounded-execution-2026-08-29.md`

## Required review findings

The reviewer must record `ACCEPT` or `REJECT` for each item:

1. r1 source and result receipts are preserved and their semantic digests
   match the recorded values.
2. The fresh row ranges start at 2,048 and are disjoint from r1.
3. Fit and assessment use separate crawl snapshots and document identities.
4. The 64-window target is supported by the recorded tokenizer eligibility
   audit and cannot silently fall back to r1 records.
5. Candidate pairs, alpha values, beta, norm adjustment, temperature, and
   tie-break rule are fully locked before assessment effects.
6. The baseline, parity, repeat, temperature, and frozen-model controls are
   executable and retained.
7. The paired bootstrap rule, seed, interval, and `NoCandidate` gate are
   fixed before effects and do not permit post hoc tuning.
8. Source, corpus, and result roots remain external to the repository.
9. Network, training, weight mutation, provider calls, GiveMeANode, and
   Evidence Ledger mutation remain prohibited.
10. The independent validator will reject any digest, split, model, or claim
    ceiling mismatch.

## Acceptance receipt template

```json
{
  "schema": "gemma3-fineweb-edu-replication-v1-independent-review",
  "state_slice": "continual-learning-gemma3-fineweb-edu-replication-v1",
  "review_status": "ACCEPT",
  "reviewer": "<independent reviewer identity>",
  "protocol_sha256": "1e42fc79c8486b1534fd2996f58c7a78de93e287249d14b347f013846d2756ff",
  "findings": {
    "r1_preserved": true,
    "fresh_ranges_disjoint": true,
    "configuration_locked": true,
    "controls_executable": true,
    "uncertainty_rule_locked": true,
    "external_custody": true,
    "prohibited_actions_enforced": true,
    "validator_behavior_accepted": true
  },
  "authorization": "assessment effects authorized only after this receipt is independently signed",
  "receipt_sha256": "<sha256 of this receipt body>"
}
```

Until an accepted receipt exists, source preparation may proceed, but fresh
assessment effects must remain closed.
