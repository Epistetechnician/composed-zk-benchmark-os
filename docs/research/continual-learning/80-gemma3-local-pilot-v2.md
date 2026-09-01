# Gemma3 local recirculation mechanics pilot V2

Date: 2026-08-27

State slice: `continual-learning-gemma3-local-pilot-v2`.

Claim ceiling: `LocalDevelopmentGemma3NewsroomIndependentRecirculationPilot`.

## Purpose

V2 is an independent fresh-cohort continuation of the V1 local mechanics
pilot. It uses the same cached pretrained Gemma3 1B BF16 MLX conversion, the
same one-additional-iteration normalized residual recurrence, the same 256-token
windows, candidate pairs, alpha values, controls, and validator. It changes
only the document cohort and immutable protocol identity.

The selection rule is fixed before execution: scan the registered NEWSROOM
`test.jsonl.gz` in source order, count records with at least 256 Gemma tokens,
skip the first four eligible records used by V1, and select the next four.
The first two selected documents are fit; the last two are assessment. No
metric or threshold is tuned from V1.

This is not a replication of the paper's C4 WebText-like or ten-dataset
Gemma3 evaluation. It does not authorize training, model downloads, network
access during inference, Evidence Ledger mutation, benchmark claims, Astral
claims, provider calls, or production traffic.

## Frozen endpoint

The primary metric is the held-out selected-minus-baseline mean next-token NLL
under the locked fit-selected pair. Lower is better. Parity, deterministic
repeat, custody, mirror equality, and repository gates are validity guards;
they are not post-hoc performance thresholds.

## Storage

PrimaryED active root:

`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-gemma3-local-pilot-v2-20260827-r1`

DAed immutable mirror:

`/Volumes/DAed/Archives/composed-zk-benchmark-os/continual-learning-gemma3-local-pilot-v2-20260827-r1`

The runner rejects existing roots, validates before publishing, mirrors the
complete artifact, and independently validates both published roots.

## Boundary

Even if V2 has the same effect direction as V1, the combined result remains a
small local NEWSROOM mechanics signal. It does not establish a general
recirculation effect, recover the paper's result, or replace the missing
paper-shaped C4 and assessment panels.
