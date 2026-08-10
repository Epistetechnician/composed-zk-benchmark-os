# Competitive Moat

State slice: `catalyst-strategy-competitive-moat-v1`.

The differentiation thesis against the organizations the maintainer tracks, and
the honest attack surface. Claim boundary: this is a Level 0 positioning
hypothesis, not a claim about competitors' internal capabilities, not evidence,
and not a guarantee of market outcome.

## The Category

All three efforts converge on the same category: **a trust layer for autonomous
agents** — infrastructure that lets a principal rely on an agent's actions
without blindly trusting the agent or its operator. The disagreement is about
*what kind of trust* is being sold.

## Named Competitors And Their Approach

| Org | Product surface | Approach to trust |
|---|---|---|
| `github.com/Auditware` | radar (Rust/Anchor/Stylus/Solidity static analysis), auditwizard (AI auditing harness), W3OS opsec standard, AuditVault | **Static analysis + audit tooling.** Trust via finding defects in code before deployment. Defensive code quality. |
| `github.com/t54-labs` | Trustline (underwriting engine), AgenticRiskStandard, x402-secure, agent-commons (private control plane), RLUSD skills | **Underwriting / risk scoring.** Trust via pricing agent risk probabilistically at the settlement layer. |

## The Differentiator

This repository's approach is **evidence discipline**:

- Every claim carries an explicit claim boundary (Level 0-6) and cannot be
  promoted without a reviewed, evidence-backed phase.
- Every module ships **nonclaims** — an explicit statement of what it does *not*
  prove.
- Unverifiable external input is **quarantined**, not trusted.
- Buyer-facing statements are **claim packets**: pinned, reproducible, and paired
  with a reproduction checker a buyer can run.

Where competitors sell a *score* (underwriting) or a *finding list* (static
analysis), this repository sells a *bounded, verifiable statement of exactly what
an agent did and did not prove*. When the privacy / discovery catalyst fires
(C1), "we can show you the evidence envelope, and you can re-run the checker" is
a structurally stronger answer than "we scored the risk" or "we audited the
code."

## The Attack Surface (honest)

1. **Discipline is harder to demo.** A single underwriting number or a findings
   table is easier to show a buyer than a claim-boundary framework. This is the
   biggest go-to-market risk. Mitigation: the claim-packet forge exists precisely
   to make discipline demoable.
2. **Depth without surface.** The repository has enormous phase depth but few
   buyer-facing packets. Until M1/M3 packets exist, the moat is invisible.
3. **Category timing.** If the trust-layer category is won on speed-to-market by
   heuristics before buyers demand verifiability, evidence discipline may arrive
   late. Mitigation: track C5 closely and keep differentiation packets staged.
4. **Not a moat until exercised.** Claim discipline is only a moat if each module
   can actually fire a packet when its catalyst appears. The targeting system
   (matrix + forge + ledger) is what converts the moat from potential to kinetic.

## Positioning Statement (Level 0, internal)

When an agent's actions must be relied on — in finance, in regulated work, in
anything that may later be scrutinized — a risk score tells you the price of
trusting it, and an audit tells you where the code was weak. Neither tells you
what the agent actually did, within what boundary, with evidence you can re-run.
That is what this stack provides.

## Nonclaims

This document does not claim the competitors are inferior, that their products do
not work, that this repository will win, that any module is production ready, or
that any catalyst will fire. It is a positioning hypothesis to be revisited by the
catalyst loop, and it grants no authority and executes nothing.
