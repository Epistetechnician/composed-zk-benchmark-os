# Private Decision Model FHE Local IPC Contract V3 Execution Record

State slices: `private-decision-model-fhe-local-ipc-contract-v3` and
`global-experiment-assurance-lifecycle-v1`. Frozen dependency slice:
`private-decision-model-fhe-inference-v1`.

## Result

V3 passed its local focused and synthetic FHE qualification. Assurance:
`INTERNAL_PASS` for the stated local scope. The claim ceiling is
`LocalDevelopmentSyntheticFHEIPCContractQualificationV3`.

- Baseline revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`.
- V3 packet raw SHA-256:
  `f78ba5dcfd820ec92b2783cdff66c0895e1a563f53e0cc5dad3fbea5490c87dc`.
- V3 packet canonical SHA-256:
  `5d709c44ea4dceabc966ad26d4e584d3f7724cd6224d1a899cac1ac6a11e59f8`.
- V3 protocol SHA-256:
  `8e3267561b70bba779b9ee261580265022d4cd25d2ae77f100a37c823dee0143`.
- Frozen V3 source composite SHA-256, recomputed before tests and after the
  run: `4f2fd8b71459584b99f2672d3c9781e30c085aaf92e53c079b8260c4bb172d3c`.
- Locked runtime: Python 3.12.13, Concrete 2.11.0, NumPy 1.26.4, PyTorch
  2.14.1; macOS 26.6.1, arm64. Dependency setup and both runs used offline
  locked mode.
- Focused validation: 14 tests passed, including object-root enforcement,
  duplicate-key and malformed-envelope controls, canonical Base64, exact
  schemas, worker environment filtering, and malformed-root rejection before
  bundle loading.
- One synthetic FHE qualification: 32/32 encrypted scores equaled the frozen
  clear scorer; 8/8 top rankings matched; the client secret key and clear
  features were not sent to the worker; network use was false; temporary
  keys, bundle, ciphertexts, responses, and arrays were removed.
- V1 fixture SHA-256 matched the frozen value:
  `7144207ead235b20cea7a26b899c42fc7249a66b9dfc12a1f02d68fe2da534f7`.
- Reproducibility status: one local qualification only; not
  `REPRODUCED_LOCAL`.
- Reviewer status: `EXTERNAL_REVIEW_UNAVAILABLE` for the separate V1 packet.
  No V3 reviewer request, task, transfer, or external contact was made.
- Custody: V1-generated synthetic data only. Raw IPC and FHE artifacts were
  not retained. The external owner-only V1 review archive was not accessed or
  changed by this execution.

## Receipt limitation

The runner emitted source digest
`88ca96c728080e8721d1929dd380f1138c56adc7ce55edc297a7ffde585e0126`, which
does not equal the frozen packet composite. The discrepancy is in the receipt
path encoding: the runner hashed an invocation path containing
`tools/private_decision_model_fhe_inference_v1/../private_decision_model_fhe_inference_v3/`
instead of the canonical repository-relative path. This value was
independently reproduced from the unnormalized paths. Every V3 source file,
the V1 scorer, the protocol, and the packet were rehashed after execution and
matched their frozen values, so this was not source drift. The frozen V3
files are not amended or rerun to repair the receipt field.

## V2 predecessor and limits

The separate V2 identity remains terminally closed as
`QualificationFailedParserControl`: 12 of 13 focused tests passed, and the
non-object-root control failed. V2 FHE execution was not attempted. See the
[V2 closure record](private-decision-model-fhe-local-ipc-contract-v2-closure.md).

V3 is same-host, same-user local process evidence only. It does not establish
cryptographic security, model-weight privacy, malicious-server integrity,
real-data utility, remote-service behavior, benchmark performance,
commercial readiness, or production authorization. The next blocked authority
gate is any future real-data, remote, paid, public, security, or production
step, which requires a fresh scope and packet plus the applicable owner or
independent authority. Further bounded local work does not require contacting
the currently unavailable external reviewer.
