# V28R7 Single-Cell Acquisition Pilot Implementation

State slice:
`astral-rgs-v28r7-single-cell-acquisition-pilot-implementation`.

Status: `Implemented / HermeticValidationPassed / ModelExecutionNotAuthorized`.

The implementation audit identified an exact-budget defect before any V28R7
model access: modular subruns declared 192 steps but the shared trainer used
the global 768-step value. Four task-local adapters would have accumulated
3,072 steps and failed the common-budget gate.

The backward-compatible repair makes the trainer honor
`NativeSmokeConfig.gradient_steps`. The unchanged nonmodular configuration
still performs 768 total steps; each of four modular subruns performs 192, also
totaling 768. Hermetic tests cover both paths.

The independent Astral implementation now freezes the complete pilot protocol,
rederives every corpus family without importing the RGS implementation,
recomputes the seed-ranked panel, validates all observation and update
receipts, recomputes novelty and signal statistics, verifies the artifact
census and source snapshots, and enforces the development-only claim ceiling.

Three clean-room validator tests and 22 RGS focused tests pass. The corrected
R7 atom normalizer also passes the complete historical predecessor fingerprint
on a noncampaign deterministic fixture. No model has
been loaded by V28R7, no ledger has been claimed, and no pilot outcome exists.
Execution authorization requires clean immutable RGS and Astral commits.
