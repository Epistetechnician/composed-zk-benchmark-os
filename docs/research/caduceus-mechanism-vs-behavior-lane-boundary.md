# Caduceus mechanism-vs-behavior admission lane — docs-first boundary

State slice: `caduceus-mechanism-vs-behavior-lane-boundary`
Claim ceiling: `Level0DesignNote`. Speculative preregistered design.

## Idea

Caduceus's admission core currently gates candidates on behavioral evidence.
The Goodfire essay (informal, unreviewed, no code or data) suggests a
candidate could additionally carry a mechanism-level claim (which units
mediate the behavior). This document proposes an optional lane in which a
mechanism claim is admitted only if it survives a matched-random-unit control.

## Proposed lane (not implemented)

- Candidate declares: behavior metric, unit set, layer, matched-control spec.
- Lane passes only if effect(unit set) exceeds the matched-random distribution
  by a pre-stated margin, with the instrument_validity lane already passed.
- A mechanism claim never upgrades a behavioral verdict; disagreement between
  mechanism and behavior is recorded as a finding, not resolved by averaging.
- The lane can only subtract admissions (fail closed), never add them.

## Honest base rates

Comparable lanes in this research are dominated by `NoCandidate`
(ai-discovery-os 12/14, research-selection-os 7/9). Expect most mechanism
claims to fail the control.

## Gate

Implementation requires a committed slice in the Caduceus repo and, for any
model-bearing evaluation, an independent signed ACCEPT, hard USD ceiling, and
allocation receipt (absent). No gman run is authorized by this document.

## Nonclaims

No admitted candidate, evidence, benchmark, SOTA, proof, or production claim.
