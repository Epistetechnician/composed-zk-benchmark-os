# Oak Lab fresh real-panel sensitivity V1 protocol

State slice: `oaklab-experience-learning-real-sensitivity-v1`.

This is a new real-panel slice. It does not modify the synthetic sensitivity
receipt or retune the closed plasticity guard. The source is the immutable
fresh-cohort custody root
`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-fresh-cohort-v1-r3`
with manifest digest
`ebd44b4e868cc3e987a8cdbb978a726814fd44c34c25cfafb10b7e920ddfb796`.

## Frozen contract

- four fresh custodied panels: `noisy_mnist`, `sensor`, `long_horizon`, and
  `event_camera`;
- 2,048 ordered rows per panel: 256 fit, 256 tune, and 1,536 assessment rows
  in twelve 128-row assessment cohorts;
- twelve surviving baseline arms; `plasticity_guard` and both rejected
  selective-credit families are excluded;
- three wider real-scale candidates per algorithm, sealed in the protocol
  manifest before assessment;
- minimum tune loss selects one candidate; assessment is rerun after the lock
  and never participates in selection;
- one experience per learner observation, explicit replay accounting, no hidden
  gradient accumulation, and no future reshuffling;
- paired tests use assessment cohorts; Benjamini-Hochberg correction is applied
  within each dataset across selected non-reference arms;
- the strict local gate requires lower loss and adaptation, non-inferior
  operations/storage, a strict resource reduction, and adjusted `p <= 0.05` in
  at least two panels.

The pre-assessment mechanical review must pass custody, grid, split, closed-arm,
multiplicity, and ordering checks. Its receipt authorizes assessment only for
this exact protocol digest.

The publication gate remains separate: a privileged measured-energy receipt is
mandatory, and a local real-sensitivity candidate is not publication approval.
