# Private Decision Model FHE Local IPC Receipt V5 Execution Record

State slices: `private-decision-model-fhe-local-ipc-receipt-v5` and
`global-experiment-assurance-lifecycle-v1`. Frozen implementation dependency:
`private-decision-model-fhe-local-ipc-contract-v3`; frozen workload
dependency: `private-decision-model-fhe-inference-v1`.

## Result

V5 passed both focused suites and its one local synthetic FHE qualification.
Assurance: `INTERNAL_PASS` for this exact local scope. Claim ceiling:
`LocalDevelopmentSyntheticFHEIPCReceiptQualificationV5`.

- Baseline revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`.
- V5 packet raw SHA-256:
  `c492742520960091486f6b17cbcaaf94b8d072621c822e0929f06a2dec7d7772`.
- V5 packet canonical SHA-256:
  `873a1733d73ae763f212588f4519f28cb1d39046d0603fa61c63e345626e6098`.
- V5 protocol SHA-256:
  `5b85b425a5b10f20e9c6075873c7ad206bd1ada683ed4c1365e8894e0df31cb4`.
- V5 source composite SHA-256:
  `f0abcac8c47d04b893aa6abad0b7dc5bcf8e724cd3c6a1a490d3af831b5f08dd`.
- Frozen V3 predecessor composite SHA-256:
  `4f2fd8b71459584b99f2672d3c9781e30c085aaf92e53c079b8260c4bb172d3c`.
- Locked runtime: Python 3.12.13, Concrete 2.11.0, NumPy 1.26.4, PyTorch
  2.14.1; macOS 26.6.1, arm64. Setup and runs were offline from the locked
  dependency cache.
- Focused validation: all 14 V3 parser/worker tests passed, then all 3 V5
  receipt tests passed. The V5 suite confirmed the runner import path, stable
  relative/absolute path normalization, packet and composite digests, result
  labeling, and restoration of the V3 digest supplier.
- One synthetic FHE qualification: the emitted V5 source digest exactly
  matched the packet; 32/32 encrypted scores matched the frozen clear scorer;
  8/8 top rankings matched. Client secret key and clear features were not sent
  to the worker; network use was false; temporary keys, bundle, ciphertexts,
  responses, and arrays were removed.
- V1 fixture SHA-256 matched the frozen value:
  `7144207ead235b20cea7a26b899c42fc7249a66b9dfc12a1f02d68fe2da534f7`.
- Reproducibility status: one local qualification only; not
  `REPRODUCED_LOCAL`.
- Reviewer status: `EXTERNAL_REVIEW_UNAVAILABLE` for the separate V1 packet.
  No V5 reviewer request, task, transfer, or external contact was made.
- Custody: V1 deterministic synthetic fixture only; no raw IPC or FHE output
  was retained. The FHE temporary directory and disposable Python environment
  were removed after execution.

## Predecessor failures and limits

V4 is terminally closed as `QualificationFailedReceiptTestImport`: its
inherited 14 V3 tests passed, but its own test module failed discovery because
the V4 directory was absent from `sys.path`. V4 FHE execution did not run.
See the [V4 closure record](private-decision-model-fhe-local-ipc-receipt-v4-closure.md).

V5 is same-host and same-user local process evidence. Model weights are clear
in the compiled server circuit. No cryptographic security, malicious-server
integrity, real-data, remote-service, benchmark, commercial, or production
claim is supported. Further bounded local development does not require
external-review contact. Any real-data, remote, paid, public, security, or
production step remains blocked on a fresh scope and packet plus applicable
owner or independent authority.
