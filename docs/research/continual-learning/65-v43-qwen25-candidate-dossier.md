# V43 Qwen2.5 local candidate dossier

Date: 2026-08-25

State slice: `continual-learning-qwen25-candidate-dossier-v43`

Claim ceiling: `LocalDevelopmentCandidateSelectionDossier`

## Decision contract

V43 selects a local continual-learning candidate by aggregating only immutable,
previously executed evidence. The mechanical metric is true only when the V40
fresh-acquisition campaign, V40 canonical-order retention campaign, and V41
noncanonical-order retention replication each pass their independent validator
and contain exactly `3 + 3 + 9 = 15` eligible cases.

The slice performs no training, inference, network access, provider call, or
production operation. It reruns each source validator in a fresh offline
subprocess, binds source report and contract file hashes, and writes a separate
immutable dossier outside the repository. The independent V43 validator reruns
those source validators again and verifies the dossier from disk.

## Result

The immutable dossier is stored at:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-candidate-dossier-v43-20260825-r1`

The independent V43 validator returned `valid=true`,
`candidate_selected=true`, and `local_case_count=15`. Every frozen selection
gate passed:

- V40 fresh acquisition: `3/3` independently validated cases eligible.
- V40 canonical-order retention: `3/3` independently validated cases eligible.
- V41 noncanonical-order retention: `9/9` independently validated cases eligible.
- Total source evidence: exactly `15` cases.

The selected classification is
`Qwen25LocalCandidateSelectedProviderProductionAndSecondModelPending`. The
signed contract digest is
`ed608938c1cf55b5909d7774dda95b378ba3c888d96c82b858080228ea268dff`; its
file SHA-256 is
`6da1fa4651f0e9659ce4b5cbdad6e343223a7d437cd37b2de21ce676d30d63f9`.
The signed dossier digest is
`331f7fca2ce43549fc569158b137361c1df89c7d42fb83405a2d08a022a5ab93`; its
file SHA-256 is
`10eb4933f8b64efcb4a867bf3d8b35991fcb7f9bbc50fd8e3e014f9ffeeb43d4`.

The V42 Nemotron boundary also revalidated from disk with `valid=true` and
`eligible=false`: no-update, adapter-train, and adapter-held-out accuracy were
all `0.25`, and every acquisition gate remained false.

## Boundary

Candidate selection is not provider validation, production validation, or an
independent second-model replication. V42 Nemotron evidence is retained as a
validator-approved negative acquisition result, not converted into a positive
replication. Live provider work remains closed until the separately specified
endpoint, invocation, credential allowlist, target environment, rollback, and
operator acknowledgement are present.
