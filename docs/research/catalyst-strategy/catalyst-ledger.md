# Catalyst Ledger

State slice: `catalyst-strategy-catalyst-ledger-v1`.

Append-only record of market catalysts backtested by the catalyst loop
(`README.md`). Each run appends a dated iteration. Catalyst statuses are Level 0
design notes, not evidence. "Fired" means the trigger evidence was observed, not
that any module claim is established. Promotion and packaging actions enter the
modules only through the claim-packet forge and its reproduction checker, and
never raise evidence maturity.

Verdict vocabulary (mirrors the oracle model):

- **Dormant.** No trigger evidence observed.
- **Warming.** Partial or adjacent signals observed; trigger evidence not yet met.
- **Fired.** The named trigger evidence was observed and recorded with a source.
- **Inconclusive.** Signals are ambiguous or a capability gap prevents classification.

Each catalyst carries a confidence (low / medium / high) and the source that
produced the status.

---

## Catalyst Registry

| ID | Catalyst | Class | Trigger evidence (what proves it fired) | Primary modules | Status | Conf. |
|---|---|---|---|---|---|---|
| C1 | AI chat-log / prompt data surfaces in legal discovery, exposing privacy risk | privacy-discovery | A high-profile case where AI conversation logs are produced in discovery and reported | M1 Attestation, M3 Audit trail | Warming | Medium |
| C2 | On-device / open-weight model becomes a mainstream platform positioning | on-device | A major platform ships or markets on-device open-source AI as a privacy feature | M1 Attestation, M4 Formal | Warming | Medium |
| C3 | Agent-autonomy incident: an agent takes an unauthorized or harmful action | agent-incident | A reported incident where an autonomous agent acted outside its mandate | M2 Bounded authority, M1 | Dormant | Medium |
| C4 | Regulation assigns liability / audit requirements to AI agents | regulation | A regulatory framework requiring auditable, bounded agent behavior | M3 Audit trail, M2 | Dormant | Medium |
| C5 | Competitor releases a trust / risk layer for agents | competitor | A named competitor ships or funds an agent-trust product | M6 Packaging, M2, M3 | Warming | High |
| C6 | Agent-native payment / settlement rails standardize (x402, stablecoins) | payments | A payment rail adopts an agent-transaction standard | M5 Economy/settlement | Dormant | Medium |

Module IDs reference `module-sensitivity-matrix.md`.

---

## Iteration 0001 — 2026-08-04

Initial registration of the catalyst set the maintainer is actively tracking.
Sources for this iteration are the maintainer's stated thesis and two tracked
competitor organizations; no external trigger evidence has been verified yet, so
no catalyst is marked Fired.

### C1 — Chat-log discovery (Warming, medium)

Thesis: it is a matter of time until a high-profile case surfaces AI chat logs in
discovery and the privacy risk becomes legible to buyers. This is the central
privacy catalyst and the one the repository's attestation and audit-trail modules
are best positioned to answer. Not fired: no specific case is yet recorded as
trigger evidence. Action: keep M1 and M3 packet-ready.

### C2 — On-device / open-weight positioning (Warming, medium)

Signal: a platform leadership change is read as a privacy / on-device
positioning move. Adjacent evidence, not yet the trigger (a shipped on-device
open-source AI product marketed on privacy). Action: keep M1 attestation and the
local formal lane (M4) packet-ready, since both answer "verifiable without cloud
custody."

### C3 — Agent-autonomy incident (Dormant, medium)

No specific incident recorded. This is the catalyst that M2 (bounded authority,
quarantine, admission gating) answers directly. Action: monitor; pre-stage an M2
packet outline.

### C4 — Regulation / liability (Dormant, medium)

No specific framework recorded. M3 (auditable, claim-bounded trail) is the
strongest answer. Action: monitor.

### C5 — Competitor trust layer (Warming, high)

Tracked organizations: `github.com/Auditware` (smart-contract auditing tooling:
radar static analysis, auditwizard AI auditing harness, W3OS opsec standard) and
`github.com/t54-labs` (Trusted Agentic Finance: AgenticRiskStandard, x402-secure,
Trustline underwriting, agent-commons private control plane). These validate the
market category but approach it with auditing tooling and underwriting
heuristics rather than evidence discipline. See `competitive-moat.md`. Action:
keep differentiation packets ready via the forge.

### C6 — Agent payment rails (Dormant, medium)

No standard adoption recorded. M5 answers if this fires. Action: monitor.

### Iteration 0001 nonclaims

No catalyst is marked Fired. Statuses reflect the maintainer's thesis and tracked
signals, not verified external trigger evidence. This iteration is a Level 0
design note, not evidence, not a prediction, and not a claim about any
competitor's capabilities or roadmap.
