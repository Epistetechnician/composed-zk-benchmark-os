# V41R33R1 Fresh-Archive History-Dependence Probe Preregistration

State slice: `V41R33R1FreshArchiveHistoryDependenceProbe`.

This is a new identity after the historical V41R27R19 archive became
unrecoverable. It binds a fresh, durable source archive and does not claim to
reproduce the lost failure.

## Locked inputs

- two arms, control first, one worker per arm:
  `v41r27-panel-8-seed-412019`;
- RGS commit `754220f7fc360d8dd15e5837190b895ea0550f30`;
- source archive custody path
  `/Users/shaanp/.codex/source-freezes/v41r33r1-rgs-754220f7.tar`;
- uploaded source archive SHA-256
  `sha256:1b2d2e6c96b89749cddd2e48a727f08a090a21634bf9c48c12734a2174968580`;
- extracted-tree manifest SHA-256
  `sha256:652633475af44cd6053b9dec6f44c7420c2668eb0e9253c4b994e9199ff9b9f5`;
- entrypoint SHA-256
  `sha256:cccc6a69caace07871274a929785c75de98a3fe6975acd67d4866ee4c7ae8859`;
- method SHA-256
  `sha256:f9fa45c268fccdecde2f3dfb2c6720ed0a47e2004f1f4b50d9c4c89767ba98dd`;
- requirements SHA-256
  `sha256:0a114a8f7abaee60c0aff87e27354e2eae5090772b20b1bbd30093ad6d1c3541`;
- model `openai/gpt-oss-20b`, revision
  `d0e2aa76789354d715f8b22553b9feb6c462fcf0`;
- runtime Python `3.10.12`, torch `2.10.0`, CUDA `12.8`, transformers
  `4.57.6`, peft `0.18.1`, GPU `NVIDIA H100 80GB HBM3`;
- wrapper implementation
  `tools/v41r32r1_history_prelude_wrapper.py`, SHA-256
  `sha256:e3fb6e35082d078734375c4e93d070d2ad8a7107c7cf4c0dc320949f24f8b4a5`;
- wrapper launcher `tools/v41r33r1_history_prelude_launcher.py`, SHA-256
  `sha256:1c12648503f39c4c1aae4bcc5cddedcf7c545b37ca50d8e012445e76d3a4169e`;
- consuming coordinator `tools/v41r33r1_history_dependence_coordinator.py`,
  SHA-256
  `sha256:28d560e7b4d5c9603abeb2153ec5ccce84a361b3867f5b5911f5e868127967b0`;
- validator `tools/astral-v41r27-agem-retention/validate_worker.py`, SHA-256
  `sha256:f1b9f45cfc7d58812b0f72fba890d3ccb274224b578a74e9f87d584af645dfd4`.

The consuming coordinator first hashes the uploaded archive at its explicit
on-node path, verifies the archive's embedded commit, complete extracted-tree
manifest, and locked source files, and verifies the launcher, wrapper, and
validator hashes. Any mismatch occurs before model/tokenizer loading and is
`InfrastructureSourceFreezeIncomplete`.

## Exact launch contract

The coordinator runs from the extracted RGS root with the resolved Python
interpreter,
`PYTHONPATH=<rgs-root>/scripts`, `RGS_ROOT=<rgs-root>`,
`RGS_SOURCE_COMMIT=<locked commit>`,
`RGS_SOURCE_ARCHIVE_SHA256=<locked archive hash>`, and the two launcher/wrapper
hash environment bindings. It uses only the frozen runtime identities, with no
caller-supplied expected-hash overrides, and records the complete child-environment mapping passed
(the child does not receive an unrecorded ambient environment) and
requires the output parent and RGS root to share
the same filesystem device, records the hostname, working directory, device
identities, import path, arm timestamps, and canonical JSON command bytes and
SHA-256 for each arm plus the environment digest.

All command paths are resolved to absolute paths before argv construction and
receipt hashing. The exact control argv is:

`<resolved-python-interpreter> <resolved-rgs-root>/scripts/run_v41r27_worker.py --output <control-output> --run-id v41r27-panel-8-seed-412019 --execute`

The exact intervention argv, with the launcher path resolved and recorded by
the coordinator, is:

`<resolved-python-interpreter> <resolved-v41r33r1-launcher-path> --output <intervention-output> --archive <uploaded-archive-path>`

The launcher is the V41R33R1 launcher, not the V41R32R1 wrapper command. It
passes the explicit archive path to the implementation wrapper, which verifies
both runtime hashes and records the launcher path, implementation path, archive
path, and archive hash in its receipt. The coordinator enforces control first, rechecks hostname and filesystem-device
identity before intervention, then runs intervention on the same node and disk
in a separate fresh process; no node reset occurs between arms.

Before either arm starts, the coordinator records exact per-arm validator
argv, validator source SHA-256, and command SHA-256 receipts. It re-hashes the
validator immediately before each invocation and writes a per-arm validator
binding receipt containing the recheck timestamp and command digest. After each
arm, it invokes the pinned validator with the corresponding artifact path:

`<resolved-python-interpreter> <resolved-validator-path> --artifact <arm-output> --rgs-root <rgs-root>`

The validator hash is rechecked before invocation. A failed validator, missing
receipt, custody mismatch, or reversed arm order stops the identity and is not a
scientific arm result.

## Gates and governance

Record terminal acquisition gates, protected accuracy, receipt rows, adapter
hashes, runtime/source bindings, wrapper receipt, validator result, and export
hashes. No retries, substitutions, tuning, threshold changes, assessment,
census update, qualification continuation, or production action. Maximum one
1x H100 minimum session. A complete arm difference supports only a
process-history-associated difference under this wrapper; equal arms weaken
that explanation. Claim ceiling:
`RemoteH100V41R33R1FreshArchiveHistoryDependenceProbe`.

V41R27 remains terminal at census `30/48`, qualification `NotAssessed`.
