# Private Decision Model FHE Local IPC Contract V2 Closure

State slices: `private-decision-model-fhe-local-ipc-contract-v2` and
`global-experiment-assurance-lifecycle-v1`. Frozen dependency slice:
`private-decision-model-fhe-inference-v1`.

## Disposition

V2 is terminally closed as `QualificationFailedParserControl`. The frozen
focused suite ran 13 tests: 12 passed and one failed. The failed control showed
that `strict_json_loads("[]")` returned a list instead of rejecting a
non-object root, contrary to the frozen negative-control contract. No FHE
qualification ran. No result, ciphertext, key, or raw IPC envelope was
retained.

The V2 protocol and packet remain unchanged. V2 source, harness, and packet
must not be amended or rerun. Its maximum claim was
`LocalDevelopmentSyntheticFHEIPCContractQualificationV2`; that claim was not
earned.

## Evidence and custody

- Baseline revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`.
- Frozen V2 source composite SHA-256:
  `ce63aba37713d9e4fe6e36bb4117de8caf67b35d9c1028dd6971405c1eb5e51e`.
- Frozen V2 protocol SHA-256:
  `de03eb41b2aaf39bbc74557dc72b5bc2942119dd940c3a16de0fa39e78105a34`.
- Frozen V2 packet canonical SHA-256:
  `53e299d5033ff0617456e866ec84ff37bbb81c1a59504003c344f7d9b0e7c9d4`.
- Runtime smoke check passed with Python 3.12.13, Concrete 2.11.0,
  NumPy 1.26.4, and PyTorch 2.14.1. This is environment evidence only.
- The one parser-suite failure is the only V2 qualification evidence. FHE
  execution, score parity, and ranking checks were not attempted.
- Reviewer status: `EXTERNAL_REVIEW_UNAVAILABLE` for the separate V1 packet;
  no reviewer was contacted for this local V2 closure.
- Reproducibility status: `NOT_REPRODUCED`; no second environment was used.
- Custody: synthetic parser literals only; no model run or raw artifact
  retention. The temporary Python environment is local and disposable.

## Limits and continuation

No cryptographic security, remote-service, real-data, benchmark, commercial,
or production claim is supported. V2 failed before its local FHE path, so the
next local work requires a fresh state slice and packet. The only blocker for
that bounded continuation is a new frozen local packet; external review,
transfer, user data, provider spend, and deployment remain closed.
