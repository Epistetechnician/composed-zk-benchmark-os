# Phase 134 PCSM-Governed Agent Admission Boundary Spec

## Status

Docs-first boundary. This phase records how the recoverable-ghost-states PCSM
work can inform this repository and Hyper Sacred AI without importing its
artifacts, claiming its metrics as local evidence, or authorizing code.

## State Slice

This slice is limited to Markdown updates under:

- `docs/134-pcsm-governed-agent-admission-boundary-spec.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `docs/research/assumption-ledger.md`
- `README.md`
- `AGENTS.md`

It does not touch Rust source, tests, fixtures, Cargo metadata, generated
artifacts, accepted Evidence Ledgers, output roots, package runtime files,
operator-live paths, or external adapters.

## Source Handoff

The source input is the local cross-repo handoff named
`pcsm-cl12-cross-repo-handoff` from:

```text
/Users/shaanp/.codex/attachments/ecdb4436-66a3-4ef6-890f-b57b0a1e1152/pasted-text.txt
```

That handoff describes the recoverable-ghost-states PCSM lane as:

```text
provider/model output
-> strict PCSMO1
-> PcsmTransitionCandidate
-> pcsm_evaluate_transition
-> pcsm_runtime_apply
-> PCSMJ1 journal append
```

The portable pattern is:

```text
untrusted claim proposal
-> strict typed candidate
-> deterministic admission or rejection kernel
-> accepted state mutation or rejected audit record
-> append-only journal
-> hash-bound source artifacts
-> verifier-backed public claim boundary
```

The handoff is not imported as benchmark evidence. Exact recoverable-ghost
metrics must be reverified in that repository before being cited as current.

## Boundary Fit For This Repository

Composed ZK Benchmark OS already has local candidates, proposals, reviews,
append previews, accepted-ledger append mechanics, accepted-ledger
materialization, official-submission package materialization, external replay
preflight, claim envelopes, agent cases, evidence lanes, and HSAI attestation
plumbing.

The remaining architectural value of PCSM is the missing admission-governance
rule between untrusted agent or provider output and any state mutation. In this
repo, the PCSM pattern should be treated as a boundary template for future
implementation, not as a transplanted runtime.

The future template is:

```text
AgentCase or benchmark result proposal
-> strict admission candidate
-> deterministic admission policy
-> accepted ClaimEnvelope or rejected audit entry
-> explicit append-only admission journal
-> source artifact digest binding
-> non-claim labels
-> separately authorized accepted-ledger append, if eligible
```

## HSAI Layer Mapping

For Hyper Sacred AI, a future PCSM-governed admission layer would sit between
raw agent output and the first mutable system authority.

- L0 Semantic Substrate: model/provider output may propose an `AgentCase`; it
  must not directly become a case accepted by downstream state.
- L1 Evidence Lanes: lane outputs may propose `ClaimEnvelope` records; the
  admission kernel decides whether the record can be accepted, quarantined, or
  rejected.
- L2 Identity And Trust Graph: identity, reputation, and anchor-set changes
  should require admitted evidence, not raw semantic claims.
- L3 Economy: credit minting should require admitted work evidence and preserve
  rejection records for audit.
- L4 Harness: agent spend, replication, goal mutation, and remediation authority
  should be gated by admitted transitions.
- L5 Interop: federated acceptance should exchange bounded claim envelopes,
  admission journals, and explicit nonclaims, not narrative summaries.

The core HSAI rule is unchanged: a governed admission path can say whether a
transition was accepted under a policy. It does not prove semantic correctness,
agent benevolence, production readiness, global uniqueness, benchmark
dominance, or model competence.

## Future Implementation Shape

A future code phase may implement only after a separate explicit authorization.
That phase should define local, hermetic types rather than importing the
recoverable-ghost runtime directly.

Required future surfaces:

- `AgentAdmissionCandidate`: strict typed input derived from an `AgentCase`,
  evidence-record candidate, provider response, or benchmark-result proposal.
- `AgentAdmissionDecision`: accepted, rejected, or quarantined outcome with a
  stable reason code.
- `AgentAdmissionPolicy`: deterministic policy inputs, including maximum claim
  boundary and required nonclaim labels.
- `AgentAdmissionJournalEntry`: append-only entry with sequence number,
  previous-entry digest, candidate digest, decision digest, and source artifact
  digests.
- `AgentAdmissionJournal`: local digest-chain validation, replay validation,
  and no-repair behavior.
- Conversion helpers that can build a `ClaimEnvelope` or accepted-ledger append
  request only from an accepted decision.

Required future rejection behavior:

- raw model text without strict decoding;
- provider output that asks for direct authority;
- claim-boundary elevation;
- missing source artifact digests;
- stale journal tip;
- stale or replayed candidate;
- missing nonclaim labels;
- accepted-ledger mutation without separate append authorization;
- score-axis population from local-only admission evidence;
- Level2+ or formal-evidence claims without external replay or formal proof
  prerequisites.

## Relationship To Existing Phase W

Phase W accepted-ledger append mechanics remain the mutation boundary for
accepted Evidence Ledger entries. PCSM-governed admission is earlier than that:
it decides whether a candidate may become an eligible reviewed input. It must
not bypass review, append preview validation, transaction validation, local
ledger materialization rules, official-submission package rules, or external
replay preflight rules.

A future admission journal entry is not accepted Evidence Ledger evidence by
itself. It is admission metadata unless a separately authorized accepted-ledger
append transaction validates and appends a reviewed record.

## Required Future Tests

Any future implementation must include hermetic tests for:

- accepted transition mutates only the governed local target;
- rejected transition appends audit metadata without mutating governed state;
- candidate digest, decision digest, and previous-entry digest validation;
- stale journal tip rejection;
- replayed candidate rejection;
- claim-boundary elevation rejection;
- missing nonclaim label rejection;
- provider direct-authority rejection;
- accepted-ledger append bypass rejection;
- local-only Level2+ and score-axis population rejection;
- source scans proving no network, credential, operator-live, external replay,
  official-submission, process-spawn, or generated-artifact path is reachable
  from normal tests.

## Explicit Non-Goals

This docs-first slice does not permit:

- Rust source or test changes.
- Cargo metadata changes.
- `Cargo.lock` changes.
- PCSM runtime import or vendoring.
- Recoverable-ghost artifact import.
- Accepted Evidence Ledger mutation.
- Official benchmark submission.
- External replay execution.
- Live backend execution.
- Network access.
- Credentials or secrets.
- Generated benchmark artifacts.
- Operator-live Phala calls.
- DCAP, PCCS, JWKS, JWT, or TLS implementation changes.
- Command-line tools.
- UI dashboards.
- JavaScript, TypeScript, or package runtime additions.
- Score-axis population.
- ZK backend performance claims.
- Level2+ evidence creation.
- Formal evidence creation.
- Production-readiness claims.
- Semantic-correctness claims.
- Global software-agent uniqueness claims.

## Claim Boundary

This phase is architecture boundary work only. It is not PCSM evidence in this
repository. It is not recoverable-ghost-states evidence admission in this
repository. It is not accepted evidence. It is not benchmark evidence. It is
not proof. It is not external replay evidence. It is not Level2+ evidence. It
is not production readiness. It is not semantic correctness.

The only claim is that the PCSM handoff identifies a useful future admission
governance boundary: untrusted agent or provider output should propose typed
candidates, and only deterministic admitted transitions should be allowed to
drive governed state.
