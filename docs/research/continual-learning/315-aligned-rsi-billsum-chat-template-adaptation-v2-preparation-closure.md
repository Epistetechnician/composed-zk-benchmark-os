# Aligned RSI BillSum chat-template adaptation V2 preparation closure

State slice: aligned-rsi-billsum-chat-template-adaptation-v2.

Governance slice: global-experiment-assurance-lifecycle-v1.

Disposition: PreparationFailedDuplicateSourceIdentity. This packet is terminal.

## Result

The V2 preparation command failed while reading the pinned federal training
split. The runner used SHA-256 of source text as a unique row key and stopped
when two BillSum rows shared the same source text:

~~~text
ExperimentError: duplicate source document in federal train:
e9af7ca7f9c434f3696c223843bcf5ba0b8d4625e9a8de46ed1efca449321a26
~~~

The failure occurred before cohort preparation completed, before the model was
loaded, and before any fit scoring, adapter update, assessment, or activation
capture. The V2 private owner root exists with mode 0700, but it contains no
prepared-input receipt or run directory. No V2 aggregate release or local
acceptance receipt was created. Scientific disposition is NOT_RUN; local
acceptance was not issued.

A read-only count over the pinned federal splits found eight repeated-source
groups (16 rows) in train and none in test. The raw source text was not emitted
or retained by the V2 failure record. The duplicate groups are now a cohort
eligibility issue for a new protocol identity.

## Frozen V2 evidence

- Repository revision: 62bf2bfb5b6775327eb635d722bd2a715a2c6a42. The worktree was
  already dirty.
- Runner SHA-256:
  48aa467160dd0983742ee23efe3e6957b079031880ae7cc6479ed2608b576c0c.
- Protocol SHA-256:
  8406e41569b242d4d019e350037750df374bade706a7d8ffe033ea6a22931036.
- Machine-readable protocol SHA-256:
  bd2fb8b1b73581d43432d6a8256cf26768f41c08a544f763d2c2b971a7438341.
- Focused-test SHA-256:
  b56ac5b6ec61122fee77d1e5626b4ac0ceeb4e10a0a3e7aa4b7e76b62a6f4fd2.
- Requirements-lock SHA-256:
  1f4c09e920af247c0b3a795de3dcd5158583551de7bbe19cb35c2e43ae3b02a3.
- The V2 focused suite passed 9 checks. Those checks do not override the
  failed real-input preparation contract.
- Model and dataset were the same pinned Qwen3-0.6B and federal BillSum
  revisions specified in the frozen V2 packet. No V2 model weights or data
  were copied into the repository.

## Closure

Do not edit, rerun, or locally accept V2 under its existing identity. Its
failure is retained as a preparation-contract outcome, not interpreted as a
model result. V3 is a new state slice. It excludes every repeated-source group
within each split and excludes every source document from V1's previously
frozen rosters before selecting fresh V3 cohorts. V3 does not use V1 or V2
scientific outputs.

The user requested local acceptance without independent acceptance. No
independent review was requested or performed for V2.
