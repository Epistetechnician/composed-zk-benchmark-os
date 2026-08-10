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
- source archive and tree SHA-256
  `sha256:1b2d2e6c96b89749cddd2e48a727f08a090a21634bf9c48c12734a2174968580`;
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
  `sha256:7429fe46ac4d8feb5f9a7aaa7b7f9fc6d32258d6466b9e2fe07abc6498a1a1e7`;
- wrapper launcher `tools/v41r33r1_history_prelude_launcher.py`, SHA-256
  `sha256:221a2864f8661dbdaa7db7e4a86411db79d4400fc46876b56e3c4501b6102f93`;
- validator `tools/astral-v41r27-agem-retention/validate_worker.py`, SHA-256
  `sha256:f1b9f45cfc7d58812b0f72fba890d3ccb274224b578a74e9f87d584af645dfd4`.

The control invokes the frozen worker in a fresh process. The intervention
uses the content-addressed launcher and wrapper, which import the same frozen
worker after the declared no-update scoring prelude. Both arms run on the same
physical node and disk in separate fresh processes, with no node reset between
arms. The source archive is uploaded and re-hashed on-node before either arm;
any mismatch is infrastructure-incomplete and consumes no scientific arm.

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
