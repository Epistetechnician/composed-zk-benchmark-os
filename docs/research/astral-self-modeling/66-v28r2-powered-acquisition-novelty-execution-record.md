# V28R2 Powered Acquisition-Novelty Execution Record

State slice:
`astral-rgs-v28r2-powered-acquisition-novelty-implementation`.

Status: `SourceFrozen / OneShotCampaignConsumed /
ValidCorpusCandidate / NoveltyPacketCandidate / UpdateArmsNotAuthorized /
AcquisitionNotTested`.

## Authoritative result

The one authorized V28R2 baseline campaign completed on 2026-07-29 from RGS
commit `c7dfe08dec8f389b9f0bcf84baf0973c4d79cf78` and Astral commit
`4b5baefe05a48d418c0a32b1b41e7b463944e645`. The independent corpus-only
validator accepted exactly 1,536 families per fact kind, 6,144 families total,
12 queries per family, and 73,728 queries with zero errors before model access.

The frozen Qwen2.5-0.5B-Instruct-4bit checkpoint then completed exactly two
scientific baseline runs in four distinct processes: separate no-op
preparations and fresh evaluators for `pre_update` and `no_update`. Each arm
scored 73,728 prompts. Both produced 18,437 correct choices, accuracy
`0.2500678168402778`, and byte-identical observations bound by
`sha256:7739c7afd1d2ca52f8e8c1acd7c01594201fbec1c7fba9500da036da5ce099d2`.

The overall family-cluster chance-normalized lift was
`0.000090422453703702`. With the frozen critical value `5.0`, its interval was
`[-0.002462512125257007, 0.002643357032664411]`. All 16 preregistered
two-sided equivalence decisions—two arms times overall, four fact kinds, and
three evaluation kinds—lay strictly within `[-0.05, 0.05]`.

The authoritative Astral status is `NoveltyPacketCandidate`. The maximum claim
is `LocalModelBackedAcquisitionNoveltyPreflightV28R2`.

## Immutable bindings

- RGS source commit:
  `c7dfe08dec8f389b9f0bcf84baf0973c4d79cf78`;
- Astral source commit:
  `4b5baefe05a48d418c0a32b1b41e7b463944e645`;
- retired-R1 fingerprint:
  `sha256:24f5cf8c7341dfdf50f1094d171e29debdccec8f9d5c2d97dbf0d33664793b96`;
- packet:
  `sha256:5e830ee437e8d67faa9dedc667db35114fa5ccf84809a9b2874c60a1ed622ddc`;
- validation report:
  `sha256:a5a090fa7707b179bd373e3a2b76511085c47daf67f910ff55f874ed0ae5547f`;
- artifact manifest:
  `sha256:e4bba029e565445f4fe930c7aeea1e7b9f572f111df22085100018ff6ed8efde`;
- execution final:
  `sha256:559750d8ed35dd68b416b4f5aeb82ede141e0a5964fffc0500b968291f7fedbc`.

Artifact root:
`/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28r2-powered-acquisition-c7dfe08-r1`.

The authoritative validator was rerun from the frozen packet into a separate
output and reproduced the report byte for byte. A post-run audit independently
rehashed all 15 manifest entries, matched the listed and actual file censuses,
and found no symlink, size, or hash discrepancy.

## Gate disposition

V28R2 demonstrates only that the new sealed evaluation corpus is sufficiently
novel relative to the unchanged checkpoint under the frozen equivalence rule.
It does not demonstrate that any update method can acquire, retain, recover,
or consolidate these facts.

The following remain absent and unauthorized:

- context-only, retrieval, sequential-LoRA, replay, SCoL-style, nested, or any
  other update/comparison arm;
- retention and protected-capability evaluation;
- corruption, termination, restart, rollback, or replay evidence;
- prospective Astral selection;
- assessment access;
- independent reproduction or replication.

The next state slice must be a separate docs-first Gate 1 update-arm
authorization. It must bind the existing V28R2 corpus and unchanged-checkpoint
reference without changing the corpus, seed, scorer, thresholds, or baseline
outcomes.
