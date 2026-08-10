# Module x Catalyst Sensitivity Matrix

State slice: `catalyst-strategy-module-sensitivity-matrix-v1`.

This is the targeting system. It maps each evidence-disciplined module to the
catalysts that raise its value and to the pre-declared **exercise action** taken
when one fires. When a catalyst fires you do not rebuild — you look up the row,
fire the claim packet that is already proven, and run its reproduction checker.

Claim boundary: sensitivity ratings (High / Medium / Low) are Level 0
prioritization notes, not evidence and not a commitment. "Packet-ready" means a
claim packet and reproduction checker exist or are defined by the forge; it does
not mean the module is production ready.

## Module Inventory

Product-facing modules, grouped over the actual crates. Crate list verified
against `crates/` on 2026-08-04.

| ID | Module | Underlying crates / surfaces |
|---|---|---|
| M1 | Attestation & agent identity | `hsai-attestation`, `hsai-attestation-phala`, `hsai-agent-anchor-registry`, `hsai-distinct-agent` |
| M2 | Gateway admission & bounded authority | `hsai-agent-admission`, `hsai-claim-envelope`, `hsai-agent-case` |
| M3 | Evidence ledger & audit trail | `zkbench-core` (evidence ledger, audit index, report bundle, packs, promotion) |
| M4 | Formal verification lane | `formal/`, tiny-Z3 / Lean / extraction work in `hsai-agent-admission` |
| M5 | Agent economy & settlement | `hsai-economy`, `hsai-membrane`, `hsai-economy-sim`, `statebook-core`, `statebook-settlement` |
| M6 | Verifiable packaging | claim packets + reproduction checkers (Phase 214 / 254 / 255 pattern) |
| M7 | Interpretability & self-modeling | `astral-stage0-protocol`, `tools/astral-*` |

## Sensitivity Matrix

Cells: High / Medium / Low sensitivity of the module (row) to the catalyst
(column). Catalyst IDs from `catalyst-ledger.md`.

| Module \ Catalyst | C1 discovery | C2 on-device | C3 incident | C4 regulation | C5 competitor | C6 payments |
|---|---|---|---|---|---|---|
| M1 Attestation & identity | **High** | **High** | Medium | Medium | Medium | Medium |
| M2 Bounded authority | Medium | Low | **High** | **High** | Medium | Low |
| M3 Evidence ledger & audit | **High** | Medium | Medium | **High** | Medium | Low |
| M4 Formal lane | Low | Medium | Medium | Medium | Low | Low |
| M5 Economy & settlement | Low | Low | Low | Low | Low | **High** |
| M6 Verifiable packaging | Medium | Medium | Medium | Medium | **High** | Low |
| M7 Self-modeling | Medium | Medium | Medium | Medium | Low | Low |

## Exercise Actions

What to do when a catalyst fires, per highest-sensitivity module.

| Catalyst fired | Primary module(s) | Exercise action |
|---|---|---|
| C1 discovery | M1, M3 | Fire "prove what the agent did and retained, on-device, with an auditable trail" packet. Run M1+M3 reproduction checkers. |
| C2 on-device | M1, M4 | Fire "verifiable without cloud custody" packet (TEE attestation + local formal lane). Run checkers. |
| C3 incident | M2 | Fire "bounded authority: proposals admitted, quarantined, and gated before any action" packet. Run M2 checker. |
| C4 regulation | M3, M2 | Fire "claim-bounded, auditable agent trail" packet. Run checkers. |
| C5 competitor | M6 (+ M2, M3) | Fire differentiation packet per `competitive-moat.md`; point it at the module substance behind the claim. Run checkers. |
| C6 payments | M5 | Fire settlement/finality packet when an agent-payment standard is adopted. Run M5 checker. |

## Current Packaging State

Whether each module already has a claim packet + reproduction checker, or needs
one stamped via `claim-packet-forge.md`. Verified against the navigation table on
2026-08-04.

| Module | Has claim packet? | Has reproduction checker? | Forge priority |
|---|---|---|---|
| M1 Attestation & identity | Partial (attestation artifacts, no buyer packet) | No | High |
| M2 Bounded authority / gateway | Yes (Phase 214 proof packet; Phase 254 claim packet) | Yes (Phase 255 checker) | Reference template |
| M3 Evidence ledger & audit | No | No | High |
| M4 Formal lane | No | No | Medium |
| M5 Economy & settlement | No | No | Low (until C6 warms) |
| M6 Verifiable packaging | The forge itself | The forge itself | n/a |
| M7 Self-modeling | No | No | Low |

The gateway (M2) is the canonical worked example: Phase 214 proof packet, Phase
254 claim packet, Phase 255 reproduction checker. The forge generalizes that
pattern. Priority order for stamping new packets: M1 and M3 first (they answer
the privacy thesis directly), then M4, then M5/M7 as their catalysts warm.

## Nonclaims

Sensitivity ratings are Level 0 prioritization notes. This matrix does not claim
any module is production ready, that any catalyst will fire, that packaging
creates evidence, or that any exercise action grants authority or executes a
backend. Firing a packet surfaces existing, already-bounded evidence only.
