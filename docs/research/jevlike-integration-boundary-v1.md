# Jevlike integration boundary V1

State slice: `proof-carrying-nano-interp-v1`.

Status: `REFERENCE_ONLY / NO_EXTERNAL_EXECUTION`.

Inspected upstream: [`vinnylarouge/jevlike`](https://github.com/vinnylarouge/jevlike)
at revision `94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452`. The upstream repository
is MIT-licensed and describes itself as an independent starter model for
one-pass scoring of a text context against a variable list of text options.

## Fit

Jevlike is a plausible implementation for a later `HypothesisRankingNano`.
Candidate options could be feature labels, circuit edges, intervention plans,
or falsifier controls. The one-pass variable-option interface is useful when
the candidate set changes per trace. Its attention head produces one score per
option and normalizes across options.

## Non-fit

Jevlike does not provide host-model activation hooks, causal interventions,
Lean statements, kernel proofs, proof composition, or contradiction authority.
Its probability is a ranking output, not a mechanistic explanation or proof.
The optional frozen-transformer path still requires the exact external encoder
and does not close the host-to-nano refinement gap.

## Admissible future adapter

An adapter may be added only as a separate nano action that records:

1. host checkpoint, layer/site, trace digest, and prompt/context digest;
2. the complete ordered option list and option-set digest;
3. Jevlike source revision, scorer checkpoint digest, encoder/runtime digests,
   seed, device, and configuration;
4. returned probabilities, selected option, and calibration/control outputs;
5. a proof attempt that covers only a deterministic property of the recorded
   result, such as finite-domain normalization or selected-index consistency.

The ranking output must remain `HypothesisOnly` until a separate nano or human
reviewer supplies an intervention result and a Lean contract that binds the
recorded host semantics. Network access, upstream vendoring, automatic model
download, host mutation, and claim promotion are outside this boundary.

## Decision

Use Jevlike as a reference for a candidate-ranking nano, not as the feature,
causal, or proof engine. The current V1 toy host remains the executable
implementation for the local synthetic lane. The separate
[proof-carrying Jevlike adapter slice](proof-carrying-nano-jevlike-adapter-v1.md)
now supplies the pinned external adapter with a new protocol identity; it
still records only a `HypothesisOnly` ranking and does not add a real host
runtime.

Every mutation governed by this record touches state slice
`proof-carrying-nano-interp-v1`.
