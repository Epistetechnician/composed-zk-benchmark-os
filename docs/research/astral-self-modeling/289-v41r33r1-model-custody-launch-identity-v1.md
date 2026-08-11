# V41R33R1 Source-Binding Runtime-Custody Launch Identity V4

State slice: `V41R33R1SourceBindingRuntimeCustodyLaunchIdentityV4`.

This is an authorized runtime-custody extension after the target preflight
stopped on an incomplete base image. It does not bypass the failed launch
identity, does not change the worker method, and does not claim a scientific
result.

The first runtime-custody launch also stopped before model loading because the
worker requires a source-binding sidecar that is not part of the plain archive
tree. This identity seals that deterministic sidecar and preserves the failed
control output under its original output root.

## Source-binding sidecar

- target path: `/home/dev/v41r33r1/rgs/.astral-source-binding.json`;
- exact fields: `source_commit`, `source_archive_sha256`, and
  `source_tree_sha256`;
- values are bound to the frozen archive and extracted-tree digest already
  checked by the wrapper;
- the coordinator verifies the sidecar before either arm;
- fresh consuming output root for this identity:
  `/home/dev/v41r33r1/output-runtime-v2`.

## Runtime custody

- isolated interpreter: `/home/dev/v41r33r1/runtime/python/bin/python`;
- Python: `3.10.12`;
- torch distribution: `2.10.0+cu128`, base version `2.10.0`;
- CUDA runtime reported by torch: `12.8`;
- transformers: `4.57.6`;
- peft: `0.18.1`;
- corrected package manifest: `runtime-custody-manifest-v2.json`;
- manifest digest:
  `sha256:65608b8799eab02afc04151ef77cbb45956bbad4dc806a97de8164d36858aa50`;
- model loading and worker import were both false during provisioning;
- the earlier v1 manifest is retained as invalid audit residue because its
  `pip freeze` was captured through the resolved system interpreter.

## Model custody

- model: `openai/gpt-oss-20b`;
- revision: `d0e2aa76789354d715f8b22553b9feb6c462fcf0`;
- source: pinned public Hugging Face revision API and resolve URLs;
- custody file count: 20;
- canonical custody-row digest:
  `sha256:5c768d8f240f7a1b6f49b008e6d0f21a235d8509f62fb85b099afdd50a060213`;
- raw custody-manifest file digest:
  `sha256:4d9726e0c665de76f960ed3dc77d939374ab60b040351872f0e4c0731f5c3370`;
- model custody is external to the repository and is accepted only when the
  target coordinator verifies both manifest digests, every listed file hash,
  and every listed byte size;
- the local Hugging Face cache view must hard-bind every snapshot file to the
  custody file by device and inode;
- launch environment sets `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and
  `HF_DATASETS_OFFLINE=1`; launch may not download or substitute model bytes.

The custody acquisition used network access only for this newly authorized
model-custody phase. Acquisition completed before launch-contract acceptance.

## New launch identity

- launch identity: `v41r33r1-source-binding-runtime-custody-v4`;
- scientific worker run id remains the preregistered
  `v41r27-panel-8-seed-412019`;
- source archive and source commit remain frozen by V41R33R1;
- the extracted-tree digest excludes only the designated sidecar and remains
  `sha256:652633475af44cd6053b9dec6f44c7420c2668eb0e9253c4b994e9199ff9b9f5`;
- runtime-custody coordinator SHA-256:
  `sha256:bdc66ed562313034b799d12ddc95203a502dabb9ae4e73306063f0e590f360bd`;
- wrapper SHA-256 for the sidecar-aware extracted tree:
  `sha256:6b1fe655980033235ac9e925b1b7fdfa321404551c6087a2e05d748b4a001379`;
- launch-contract test SHA-256:
  `sha256:28726914c56259de6fa67d742d4be4a94f60b91544cfe296213bc3af33091cec`;
- coordinator must verify the runtime manifest digest before model custody or
  either arm;
- launch-contract tests include runtime-custody acceptance and mismatch cases;
- the consuming coordinator is the new source-binding/runtime-custody-bound implementation in
  this identity, not the prior coordinator;
- the coordinator records the model custody binding before either arm and
  writes `model-custody-binding.json` beside the campaign ledger;
- control remains first, validator acceptance remains required before
  intervention, and one H100 session remains the maximum.

## Exact launch shape

The resolved command is:

```text
<resolved-python> <resolved-runtime-custody-coordinator>
  --archive <resolved-custody-archive>
  --rgs-root <resolved-plain-rgs-root>
  --output-root <resolved-fresh-output-root>
  --model-root <resolved-model-custody-root>
  --hf-cache-root <resolved-local-hf-cache-root>
  --runtime-manifest <resolved-runtime-custody-manifest>
```

The coordinator refuses missing, altered, incomplete, symlinked, or
unbound model custody; source drift; cache-view drift; output reuse; device
drift; validator drift; or any receipt mismatch before model/tokenizer loading.

## Claim boundary

The custody phase establishes only local model-byte custody for this new launch
identity. A completed pair, if it passes all validators and is sealed, remains
only a process-history-associated observation under
`RemoteH100V41R33R1FreshArchiveHistoryDependenceProbe`. It is not a
breakthrough, replication, mechanism result, production result, or claim about
the model beyond the preregistered ceiling.
