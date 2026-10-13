# Private Decision Model FHE Inference V1

State slice: **`private-decision-model-fhe-inference-v1`**.

Status: **LOCAL SYNTHETIC INFERENCE COMPLETE**.

Baseline revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`.

Assurance: `INTERNAL_PASS` and `REPRODUCED_LOCAL` for the bounded local
synthetic implementation and qualification. Reviewer status: `NOT_REQUESTED`.
The exact frozen procedure passed in a fresh isolated Python 3.12 environment
on the same host and under the same owner account. Data and artifact custody:
deterministic synthetic data only; runtime keys, compiled circuit, ciphertexts,
and generated arrays were temporary and removed. This same-owner reproduction
is not independent review. Claim ceiling:
`LocalDevelopmentSyntheticFHEInferenceV1`. The next blocked authority gate is
a fresh reviewed slice before any real data, remote service, paid execution, or
public claim.

This continuation implements only the inference-first path selected after the
design-only proposal in
[private-decision-model-privacy-prd-v1.md](private-decision-model-privacy-prd-v1.md).
It does not change that earlier document's boundary. It does not use Jevlike
code, models, artifacts, or results.

## Frozen workload and privacy boundary

- **Task:** rank four options from six signed integer features per option.
- **Data:** deterministic, locally generated synthetic examples only. A small
  linear scorer is fit on 128 generated training rows; disjoint synthetic
  calibration requests are used to compile the FHE circuit; eight separate
  synthetic requests are held for the local execution check.
- **Runtime:** Python 3.12, exact `concrete-python==2.11.0`, and
  `setuptools==80.9.0`, in an isolated environment. The versions are pinned
  because the native Concrete runtime has explicit Python/platform support
  and the installed runtime still imports `pkg_resources`.
- **Client:** holds the secret key, encrypts the feature tensor, and decrypts
  the score vector.
- **Server:** a separate local process loads the compiled circuit and receives
  only encrypted features and public evaluation keys. It returns encrypted
  scores. It receives no client secret key and no clear feature array.
- **Model visibility:** scorer weights are compiled as clear server-side
  constants. This slice makes no model-weight privacy claim.
- **Output:** the client decrypts the four scores and computes the ranking
  locally. The option count and feature shape are fixed, so this example does
  not hide request shape or timing metadata.
- **Retention:** generated examples remain in memory; bundle, key objects,
  evaluation keys, ciphertexts, and serialized values are transient. Runtime
  files are created in a system temporary directory and removed on completion.

The scorer is a linear synthetic fixture, not an LLM, a Jev replica, or an
encrypted training protocol. A separate local process checks the
client/server API boundary, but it runs under the same user account and host.
This does not assess a remote deployment, malicious-server integrity,
cryptographic parameter suitability for sensitive production data,
access-pattern leakage, or formal security.

## Threat model and bounded red-team checks

The bounded attacker is a curious or malformed local server request attempting
to pass clear feature values or a client secret key to the evaluation worker.
The worker accepts exactly two request fields: serialized evaluation keys and
serialized encrypted arguments. A request containing extra clear-feature or
secret-key fields fails before ciphertext deserialization. The child process
receives only an allowlist of basic runtime environment variables, not the
parent's credential/configuration environment. The evaluation worker has no
client-key import or decryption path.

Hermetic checks exercise malformed feature shapes, non-integer inputs,
out-of-range values, extra request fields, and a credential-bearing parent
environment sentinel. A fixed-seed bounded input fuzz check compares 256
four-option requests against an independent integer dot-product formula. The
end-to-end run also confirms that the distinct server process rejects the
synthetic cleartext/key-field payload and that encrypted execution preserves
all scores.

Residual risks are explicit: processes share one host and user account, so this
does not isolate a hostile executable with OS-level controls; option count,
shape, request timing, and service availability remain visible; server model
weights are clear; a malicious server may deny service or return incorrect
results; and no cryptographic review or formal security analysis was done.
The bounded red-team checks cover this request boundary only.

## Implementation and validation

The implementation is in
[`tools/private_decision_model_fhe_inference_v1/`](../../tools/private_decision_model_fhe_inference_v1/README.md).
The project-local `uv.lock` records the resolved environment. The runner checks
that all 32 decrypted synthetic option scores exactly match the clear linear
scorer and that the top-ranked option matches for all eight requests. The
hermetic contract checks validate the synthetic split, fixed shapes, fitted
coefficients, deterministic fixture digest, boundary rejection, environment
filtering, and 256 bounded randomized formula comparisons.

Run the focused checks with:

```sh
cd tools/private_decision_model_fhe_inference_v1
export UV_PROJECT_ENVIRONMENT=/tmp/codex-private-decision-fhe-v1-venv
uv sync --locked --python 3.12
uv run --locked python -m unittest discover -s tests -v
uv run --locked python run_v1.py
```

Dependency acquisition is limited to the pinned public Concrete wheel and its
resolved Python dependencies in the isolated environment. Model/data
downloads, network services, provider calls, and paid execution are outside
this slice.

## Execution record

Final local run: **`INTERNAL_PASS`**. The first end-to-end attempt stopped
before inference because the library serialized client specifications as
bytes; the worker now transports those bytes with base64 and the final run
completed.

- Baseline revision and state slice: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`,
  `private-decision-model-fhe-inference-v1`.
- Source digest: `41bdd10bd882d7f7174fdfadae4f8b9688a28dab2bb839f11a93bbf660d5ad47`.
- Environment lock digest: `cf9852e2b16da1d6dabb13fd9fbcf368e36822043907aa0a5154589504b0a8b2`.
- Runtime: Python `3.12.13`, Concrete `2.11.0`, NumPy `1.26.4`, macOS
  `26.6.1` ARM64.
- Fixture digest: `7144207ead235b20cea7a26b899c42fc7249a66b9dfc12a1f02d68fe2da534f7`;
  128 synthetic training rows, 12 calibration requests, 8 evaluation
  requests, 6 features per option, 4 options per request.
- Results: 7 hermetic contract checks passed; 256 generated scorer requests
  matched the independent integer formula; all 32 FHE scores exactly matched
  clear scores; all 8 top-ranked options matched; the worker rejected the
  synthetic cleartext/key-field request; and the server process inherited no
  unapproved parent environment variables.
- Custody: no user or external data; temporary circuit, keys, ciphertexts,
  and arrays were removed. The repository retains source, lock metadata, and
  this aggregate record only.
- Reproduction: `REPRODUCED_LOCAL` in a fresh isolated Python `3.12.13`
  environment using `uv sync --locked --python 3.12.13`; the seven contract
  checks and FHE execution matched the original result. The same source digest,
  lock digest, fixture digest, and runtime were observed. The captured runner
  Test harness (`tests/test_contract.py`) SHA-256 is
  `0db58dd79e216a2f15b87d3e99a891f40ec4aafd24bb0ef00283addb842dc94d`; the
  project manifest (`pyproject.toml`) SHA-256 is
  `da7caa076b89c4d578c348c4bd8784984e71a8bd57eebf9577bdd2f502d579ae`.
  The captured runner receipt was produced with `UV_OFFLINE=1` and has SHA-256
  `ca8142bb1c45d0075fdf8eacae9427cb9ef7ff952a4dafc9368dad72235aa510`.
  The receipt contained aggregate output only and was removed after recording
  its digest. This was same-owner, same-host reproduction, not segregated or
  independent review. Reviewer status remains `NOT_REQUESTED`. No external or
  paid execution occurred.
- Limitations: synthetic linear utility only; server model weights are clear;
  same-host process separation; no remote service, real-data utility, formal
  cryptographic review, or production claim. Concrete emitted a non-fatal
  `pkg_resources` deprecation warning.
- Next blocked authority gate: a fresh packet, applicable independent review,
  and owner authorization before any real data, remote service, paid run, or
  public claim.

## Sources

- Zama, [Concrete quick start](https://docs.zama.ai/concrete/v/2.6/get-started/quick_start) and [client/server deployment](https://docs.zama.ai/concrete/2.9/guides/deploy). The deployment guide documents client-side key generation and encryption, server-side execution with evaluation keys, encrypted results, and client-side decryption.
- Zama, [Concrete repository and system requirements](https://github.com/zama-ai/concrete), including Python 3.9–3.12 and ARM64 support.
- PyPI, [concrete-python 2.11.0](https://pypi.org/project/concrete-python/2.11.0/), including the CPython 3.12 macOS ARM64 wheel.
- Zama, [Concrete releases](https://github.com/zama-ai/concrete/releases), version 2.11.0.
- Zama, [Concrete ML linear models](https://docs.zama.ai/concrete-ml/1.2/built-in-models/linear), which informed keeping V1 to a compact linear scorer. This slice uses the lower-level Concrete client/server API rather than Concrete ML's model wrapper.
- Zama, [Concrete issue on `pkg_resources` and setuptools 82](https://github.com/zama-ai/concrete/issues/1308), which motivates pinning setuptools below 81.

Sources checked: 2026-09-30. They document library capabilities and packaging,
not the security or utility of this specific workload.
