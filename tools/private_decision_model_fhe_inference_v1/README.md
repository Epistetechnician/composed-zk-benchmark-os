# Private Decision Model FHE Inference V1

State slice: `private-decision-model-fhe-inference-v1`.

This bounded example fits a tiny linear scorer on deterministic synthetic
examples, encrypts fixed-shape option features in the client process, evaluates
them in a separate local server process using Concrete, and decrypts/ranks the
scores in the client. The server process receives no client secret key or clear
feature array. Model weights are included in the clear server circuit.

Use Python 3.12 in an isolated environment outside the checkout. The dependency
is pinned to `concrete-python==2.11.0` and `setuptools==80.9.0` to avoid the
known `pkg_resources` compatibility issue. No model or corpus is downloaded.
The only data are deterministic synthetic arrays created in memory. The FHE
bundle, keys, and ciphertexts are written only below the system temporary
directory and removed at completion.

From this directory:

```sh
export UV_PROJECT_ENVIRONMENT=/tmp/codex-private-decision-fhe-v1-venv
uv sync --locked --python 3.12
uv run --locked python -m unittest discover -s tests -v
uv run --locked python run_v1.py
```

The last command must report exact encrypted/clear score equality for all 32
synthetic option scores across eight four-option requests. It makes no network
calls. Its result is an `INTERNAL_PASS` for this source and fixture only, with
claim ceiling `LocalDevelopmentSyntheticFHEInferenceV1`.
