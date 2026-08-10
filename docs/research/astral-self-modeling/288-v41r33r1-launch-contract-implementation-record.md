# V41R33R1 Launch-Contract Implementation Record

State slice: `V41R33R1FreshArchiveHistoryDependenceProbe`.

This additive implementation closes the launch-critical custody and orchestration
boundary without executing a model or GPU job.

## Implemented bindings

- The wrapper requires an explicit `--archive` path and hashes that uploaded
  archive before model/tokenizer import.
- The coordinator verifies the archive, embedded git-archive commit identifier,
  complete extracted-tree manifest, and locked source files before either arm;
  no `.git` directory is required in a plain archive extraction.
- The V41R33R1 launcher and wrapper hashes are checked before the wrapper is
  loaded for source preflight and are recorded in the wrapper receipt.
- The consuming coordinator freezes the control and intervention argv, records
  canonical command bytes and digests, fixes `PYTHONPATH` and the launch
  environment, and enforces control-before-intervention.
- The pinned validator is hash-checked and invoked against each arm before the
  next arm or final paired result is accepted.
- The coordinator requires one filesystem device for the RGS root and output,
  records hostname/device/working-directory/import-path bindings and arm
  timestamps, and refuses a consumed output root.
- The coordinator now requires and validates the intervention wrapper receipt,
  including archive, source, launcher, implementation, and run identities.
- The launcher hashes the explicit archive path before importing the wrapper,
  and the coordinator records exact control/intervention validator argv and
  digests before either arm starts.
- The campaign ledger preserves the exact environment mapping, per-arm pinned
  validator hashes, command digests, and validator-binding receipts.
- The coordinator rechecks node/filesystem identity before intervention and
  records validator recheck timestamps and exact per-arm validator digests.
- All launcher, archive, output, validator, and RGS-root command paths are
  canonicalized before argv and digest construction.
- The resolved Python interpreter path is also part of every worker, launcher,
  and validator argv and digest; child processes receive the resolved RGS root
  as their cwd.

## Content identities

- wrapper: `sha256:e3fb6e35082d078734375c4e93d070d2ad8a7107c7cf4c0dc320949f24f8b4a5`;
- launcher: `sha256:1c12648503f39c4c1aae4bcc5cddedcf7c545b37ca50d8e012445e76d3a4169e`;
- coordinator: `sha256:28d560e7b4d5c9603abeb2153ec5ccce84a361b3867f5b5911f5e868127967b0`;
- validator: `sha256:f1b9f45cfc7d58812b0f72fba890d3ccb274224b578a74e9f87d584af645dfd4`.

## Verification

`tools/test_v41r33r1_launch_contract.py` covers archive, tree, source-module,
launcher/wrapper, receipt, argv, per-arm validator command, arm-order,
same-disk, consumption, and validator mismatch fail-closed cases. The focused
V41R27 validator suite and launch-contract suite pass: `22 passed`.
No remote execution occurred.
