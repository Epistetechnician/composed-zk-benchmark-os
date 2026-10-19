# Theseus instrument validity: matched-neuron controls — docs-first boundary

State slice: `theseus-neuron-control-instrument-validity-boundary`
Claim ceiling: `Level0DesignNote`.

## Purpose

Adopt one methodological idea from the Goodfire essay (informal, not peer
reviewed, no code or data): an instrument is only credible if its effect
exceeds a matched random control. Apply this as a validity requirement on
Theseus-style instruments, not as a new result.

## Requirement

Any instrument-validity claim must report, before interpretation:

1. the intervention effect;
2. a matched-random-control distribution (size-, layer-, and
   magnitude-matched) with the draw count and seed;
3. the effect minus control with a pre-stated minimum effect;
4. a raw-activation-shape summary (percentile profile) as a descriptive
   sanity check that the controlled units are not degenerate.

An instrument whose effect does not separate from the matched-random control
is classified `InstrumentNotValid`, regardless of other metrics.

## Scope

Documentation of the gate only. No code, no model execution, no new data.
Any implementation needs its own committed state slice and, for model-bearing
runs, an independent signed ACCEPT, hard USD ceiling, and gman allocation
receipt (all currently absent).

## Nonclaims

No instrument is declared valid by this document. No accepted evidence,
Level2+, benchmark, SOTA, proof, or production claim.
