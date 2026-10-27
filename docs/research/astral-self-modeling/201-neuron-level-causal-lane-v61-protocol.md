# V61 protocol: minimal-pair donor patching (removes the "donors are different sentences" caveat of V60)

Slices: astral-neuron-level-causal-lane-v61-execution, instrument-validity-gate-v3, governed by neuron-control-lanes-unreviewed-execution-v1. Ceiling: LocalDevelopmentUnreviewed. Authorized by the owner in chat 2026-10-26 ("okay go ahead and do so next step end to end", following the assistant's stated next step: minimal-pair donor protocol). Committed before any V61 code or model run. Exploratory, post-hoc relative to V54/V58/V60.

## Why
V60's donor patch (1.40 logits) used a different real sentence as donor, so sentence content, not only subject number, differed. V61 uses synthetic minimal pairs whose prefix differs ONLY in the subject noun's number, so the donor-recipient difference is the quantity of interest.

## Items (deterministic, no corpus, no download)
Generator `build_minpairs(seed=6161)`: 400 pairs from a fixed vocabulary of 22 subject nouns (singular/plural forms), 8 attractor nouns (either number, chosen per pair so that about half are number-mismatched with the subject), 4 prepositions, and verb pairs is/are, was/were, has/have (leading-space single tokens, checked by the backend). Prefix: "The {subject} {prep} the {attractor}" with no verb; good = verb agreeing with the subject, bad = the other form. Each pair yields a singular-subject item and a plural-subject item identical except for the subject noun form. 800 items; item ids "M:<pair>:s|p"; mate = the other member.

## Units and selection (fixed from V60)
swap_units = [20414, 25229, 2952, 28532, 24862, 13691, 22664]; the run aborts unless a fresh k=32 reselection equals the locked V54 selection and V58 top units equal the frozen list. Controls: 100 matched-random 7-unit sets (layer and magnitude matched), identical operation.

## Task M: minimal-pair donor patch (the gate)
For every item, the units' last-position activations are replaced by those captured from its mate (donor run unpatched); metric = baseline margin minus patched margin (correct verb minus wrong verb), singular-subject and plural-subject items reported separately and combined. Supported iff both directional drops exceed the control maxima and the combined drop >= 0.1 logits.
Diagnostics (not gates, reported with the same controls): (i) self-donor (identity patch) must be 0 to numerical precision, else the pipeline is invalid and the run is void; (ii) same-number donor: a different pair's item of the same number.

## Decision rule (frozen)
"Minimal-pair confirmed" iff Task M is supported and the self-donor check passes. If M fails, V60's donor effect is attributed in part to non-number sentence differences. V60's 1.40 is reported for comparison only; no magnitude expectation. No threshold changes after data. If synthetic prefixes are far out of distribution the baseline margin may be small; report the baseline margin.

## Budget and rules
Hard cap USD 1.00 on node v51-full-r1 (new receipt), expected about USD 0.3. Campaign ceiling USD 50.00 (about 45.5 spent). One run, no downloads, offline model. A selection mismatch, tokenization failure, failed self-donor check, spend breach or missing receipt closes V61 without retuning. Claims: single model, synthetic templates, 100 controls (p floor 0.0099); no mechanism, circuit, general, proof, Level2+, independent, SOTA, benchmark or production claim.
