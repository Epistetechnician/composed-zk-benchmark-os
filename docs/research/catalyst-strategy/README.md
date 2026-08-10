# Catalyst Strategy Operating Model

State slice: `catalyst-strategy-operating-model-v1`.

Status: Level 0 design note. This is the entry point for the market-facing
strategy layer.

## Purpose

The repository has spent its effort building **ammunition**: evidence-disciplined
modules with claim boundaries, nonclaims, quarantine, and verifiable claim
packets. What it has not had is a **targeting system** — a durable mechanism that
decides *which* module to aim when a *market catalyst* appears.

This layer closes that gap. It treats market catalysts the same way the
autoresearch loop treats architecture assumptions: as falsifiable, routable,
append-only signals — and it treats each evidence-disciplined module as an option
that is exercised when its catalyst fires.

The strategic core: **modular evolution is not "build more depth." It is a
targeting system that fires pre-verified ammunition when a catalyst emerges.**

## Claim Boundary

Everything in this layer is a Level 0 design note.

- A catalyst being "fired" is a market observation, not evidence. It never
  raises the maturity of any claim in any module.
- A module being "promoted" or "packaged" does not change its evidence class.
  Packaging surfaces existing evidence; it does not create new evidence.
- Strategy verdicts (which module to prioritize) are prioritization aids, not
  proof, not benchmark evidence, not accepted evidence, not production
  readiness, not SOTA, not a breakthrough, and not full security.
- Competitive statements are positioning hypotheses, not claims about
  competitors' internal capabilities.

## Relationship To The Autoresearch Loop

Two complementary learning loops now exist:

| Loop | Backtests against | Ledger | Cadence |
|---|---|---|---|
| Autoresearch loop (`autoresearch-loop.md`) | Technical evidence on architecture assumptions | `assumption-ledger.md` | Weekly + after doc-22 edits |
| Catalyst loop (this layer) | Market signals on strategy | `catalyst-ledger.md` | Weekly + after competitor/platform events |

The autoresearch loop asks "is the architecture still defensible given technical
evidence?" The catalyst loop asks "which module should we surface given what the
market is doing?" Both are propose-only; both require human acceptance to change
anything durable; both append dated iterations and never overwrite.

## The Catalyst Loop

```text
MONITOR -> DETECT -> PROMOTE -> PACKAGE -> RE-VERIFY -> RECORD
```

1. **MONITOR.** Scan for catalyst signals: competitor releases, platform moves
   (Apple, model providers), regulation, reported agent incidents, discovery /
   privacy events. Sources are recorded in the ledger, not assumed.
2. **DETECT.** Register or update a catalyst in `catalyst-ledger.md`. Each
   catalyst carries *trigger evidence* — the observation that would prove it has
   fired — and a status: dormant / warming / fired.
3. **PROMOTE.** Consult `module-sensitivity-matrix.md`. Identify which modules'
   value rose and by how much. Rank. This step produces a prioritization, not a
   decision.
4. **PACKAGE.** For the highest-ranked module, fire its claim packet via the
   recipe in `claim-packet-forge.md`. If the module has no packet yet, the forge
   defines how to stamp one out.
5. **RE-VERIFY.** Run the module's reproduction checker so the packet stays
   aligned with committed repository state. A packet that fails its checker is
   not shareable.
6. **RECORD.** Append a dated iteration to the catalyst ledger: what fired, what
   was promoted, what was packaged, what was re-verified, and the nonclaims.

## Artifacts In This Layer

| File | Role |
|---|---|
| `README.md` | This operating model; loop, claim boundary, cadence, index. |
| `catalyst-ledger.md` | Append-only ledger of catalysts, statuses, and dated iterations. |
| `module-sensitivity-matrix.md` | The targeting system: module -> catalyst -> exercise action. |
| `claim-packet-forge.md` | Repeatable recipe to stamp a verifiable claim packet for a module. |
| `competitive-moat.md` | Differentiation thesis vs. named competitors and the attack surface. |

## Cadence And Triggers

- Run the catalyst scan on the same weekly cadence as the autoresearch loop.
- Run an on-demand scan immediately after any of: a named competitor release, a
  platform privacy/on-device announcement, a reported agent-autonomy incident, a
  regulatory action, or a discovery/privacy legal event.
- Each run appends a dated iteration to the catalyst ledger; prior iterations are
  never overwritten, so the trajectory of each catalyst is auditable.

## Nonclaims

This layer does not claim: that any catalyst will fire; that any module is
production ready; that the strategy is validated, proven, or accepted evidence;
that competitors are inferior; that packaging creates evidence; or that any
action here grants authority, executes a backend, or settles anything. It is a
targeting and packaging discipline only.
