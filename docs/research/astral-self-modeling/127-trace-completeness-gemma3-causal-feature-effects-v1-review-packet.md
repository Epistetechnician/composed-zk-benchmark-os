# Gemma 3 causal feature-effects V1 review packet

State slice: `astral-trace-completeness-gemma3-causal-feature-effects-v1`.

The executable packet is compiled by
`tools/astral-trace-completeness-gemma3-causal-feature-effects-v1/review_v1.py`.
Its packet digest binds the complete V1 contract, source manifest, frozen V4
qualification digest, exact model/runtime/asset identities, fresh corpus
identity, module registry, estimand, intervention operators, controls,
missingness, multiplicity, power, repeats, attrition, retention, runner,
validator, operator, node-provider boundary, and custody root.

The reviewer must be outside operator identity `shaanp` and must sign the exact
packet digest with Ed25519. A valid receipt must contain:

- verdict `ACCEPT`;
- reviewer role distinct from the operator;
- the exact V1 packet SHA-256;
- Ed25519 algorithm, 32-byte public key, and 64-byte signature;
- explicit acceptance of the exact node, spend ceiling, custody root, and
  assessment ordering.

The V1 code never creates this receipt. A validator receipt or a user
authorization is not an independent review. Without the external signed
receipt, model execution and assessment effects remain closed.

Current compiled packet digest:
`15fbe22956eda7cf2e5d50c255086419ddb5716ee27ae31c9b9765c03c836034`.
The source manifest digest inside that packet is
`d41bbb879e450e4c8f048590abff4101fcac7989dd8e35d7387c4e789bc5c194`, and the
contract digest is
`d50f67e9c8ebcb1ccdfce7ecc0f51b34bab0e77cabe66a44df12c85d24040c27`.

The reseal added typed intervention metadata validation, full-logit and
sampled-token parity checks, fail-closed causal-scrub estimability, aggregate
raw-expiry validation, and aggregate-only parity digests rather than token
IDs. Prior packet bytes remain in the external review root under an explicit
stale filename.
