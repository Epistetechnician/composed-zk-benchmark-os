# V41R33R1 Model-Custody Launch Identity V1

State slice: `V41R33R1ModelCustodyLaunchIdentityV1`.

This is an authorized custody extension after the original V41R33R1 target
preflight stopped on a missing model revision. It does not reuse the failed
launch identity, does not change the worker method, and does not claim a
scientific result.

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

- launch identity: `v41r33r1-model-custody-v1`;
- scientific worker run id remains the preregistered
  `v41r27-panel-8-seed-412019`;
- source archive, source commit, extracted-tree digest, wrapper, launcher, and
  validator identities remain those frozen by V41R33R1;
- model-custody coordinator SHA-256:
  `sha256:fc2280872d59a05f72127ee7fade09813577dc13f2ec2d604940884ad81fa8cf`;
- launch-contract test SHA-256:
  `sha256:f67e2d9864124f553078a9eedf4fb47a5584348dd5a5731eb8674b2effee2b8c`;
- the consuming coordinator is the new model-custody-bound implementation in
  this identity, not the prior coordinator;
- the coordinator records the model custody binding before either arm and
  writes `model-custody-binding.json` beside the campaign ledger;
- control remains first, validator acceptance remains required before
  intervention, and one H100 session remains the maximum.

## Exact launch shape

The resolved command is:

```text
<resolved-python> <resolved-model-custody-coordinator>
  --archive <resolved-custody-archive>
  --rgs-root <resolved-plain-rgs-root>
  --output-root <resolved-fresh-output-root>
  --model-root <resolved-model-custody-root>
  --hf-cache-root <resolved-local-hf-cache-root>
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
