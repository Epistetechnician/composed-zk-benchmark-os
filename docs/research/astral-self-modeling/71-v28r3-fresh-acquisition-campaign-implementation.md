# V28R3 Fresh Acquisition Campaign Implementation

State slice:
`astral-rgs-v28r3-fresh-acquisition-campaign-implementation`.

Status: `Implemented / IndependentlyRecomputedInTests / RuntimeNotAuthorized`.

The checked-in Astral instrument freezes the campaign constants and provides
two fail-closed entrypoints. The corpus entrypoint independently rederives all
identifiers, documents, questions, answer permutations, prompts, and hashes
from the revealed seed before checking complete disjointness from the combined
V28R1/V28R2 fingerprint. The campaign entrypoint recomputes novelty at the
family-cluster unit, exact baseline parity, persistent-cell status, futility,
metrics, family-paired bootstrap results, state inventories, and the complete
artifact census.

The validator imports no RGS producer module. Its only reused scientific code
is the already committed Astral Gate 1 recomputation module, rebound to the
V28R3 state identity and fresh no-update baseline. Producer and consumer tests
cover deterministic generation, answer-position balance, all five non-reuse
surfaces, seed/corpus tampering, chance equivalence, retained negative results,
fresh-baseline gain, query/answer isolation, and MLX-free imports.

This is implementation evidence only. No ledger, OS seed, V28R3 corpus, model
load, update, adapter, outcome, or scientific claim was created. Execution
requires a new explicit state-slice authorization and the maximum present
claim remains `LocalProspectiveFreshAcquisitionCampaignV28R3`.
