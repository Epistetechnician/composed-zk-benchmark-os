# Private Decision Model FHE Review Preflight V1

State slices: `private-decision-model-fhe-review-preparation-v1`,
`global-experiment-assurance-lifecycle-v1`; target:
`private-decision-model-fhe-inference-v1`.

## Status

The local packet is frozen and its manifest-bound archive is validated. The
configured review gateway is `EXTERNAL_REVIEW_UNAVAILABLE`: the registered
Agent Card URL returned HTTP 404 on two checks on 2026-10-01 and on the
registered-URL recheck on 2026-10-02. No alternate route was probed and no
health, contract, key-pin, or no-task readiness endpoint was called. No review
task was created, and no artifact bytes were transferred.

The local result remains `INTERNAL_PASS` and `REPRODUCED_LOCAL` for the named
synthetic-only target. Reproduction was same-owner and same-host; it is not
independent review. The claim ceiling remains
`LocalDevelopmentSyntheticFHEInferenceV1`.

## Frozen identities

- Baseline source revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`.
- Canonical target SHA-256: `43d300f3e910704016e6b953f417a7a457b2a9b69cd35f44d6620e832f39793d`.
- Target file SHA-256: `b77e6966e246a62a282f16a5b7535a59079253576f531b89900cd4b618c48339`.
- Canonical protocol SHA-256: `4ce1c4382da99e8b8e4bac171268f71f05944039edbc513ac33dea1ec57f5c82`.
- Protocol file SHA-256: `669e9e0f67e0b8b054a9dcfd28e893974503a6a36758a3005fa221356201b3c3`.
- Canonical packet SHA-256: `94ae6b4460aba7bbabab32f853a075d43dfd1e5a949103c7e4665853fc41defc`.
- Packet file SHA-256: `61b575b8841dbcba1d0271942cf38ed9de1b4d92098e04a42d6fc1ced4ce209d`.
- Artifact manifest SHA-256:
  `e5526c254f1351584aa2dd9d0f4201da16119d518f940991cb6d7812f6b8d44f`.
- Owner-only ZIP archive SHA-256:
  `90836174530b563179a4e7ff95ca20109f15ea2ed806d5491139f07d702e9f3a`.
- Archive entries: 13, exactly matching the manifest; no extra files or
  metadata sidecars.
- Local permissions: staging directory `0700`; archive `0600`.

The archive contains exactly the payload paths listed in the artifact
manifest. The manifest is separate control metadata and is excluded from the
archive to avoid a self-digest cycle. The target is included as a manifested
archive entry; the target binds the protocol and packet bytes. The archive is
staged owner-only outside the repository and has not been transferred.

## Evidence and custody

The frozen packet records seven hermetic contract checks, 256 fixed-seed
synthetic scorer checks, 32/32 encrypted score matches, and 8/8 top-rank
matches. Runtime was Python 3.12.13, Concrete Python 2.11.0, NumPy 1.26.4,
on macOS 26.6.1 arm64. Raw runtime keys, circuit bundle, ciphertexts, and
synthetic arrays were removed after execution. The aggregate output receipt
bytes are unavailable; only SHA-256
`ca8142bb1c45d0075fdf8eacae9427cb9ef7ff952a4dafc9368dad72235aa510` and the
summary retained in the execution report remain. No resource measurements
were retained.

The packet does not claim real-data utility, formal cryptographic security,
model-weight privacy, encrypted training, TEE protection, remote-service
qualification, benchmark evidence, commercial readiness, or production
readiness. The server is a separate local process under the same host and
user account; its compiled circuit contains clear model weights.

## Readiness blockers

- **Operator:** local target, protocol, packet, manifest, and archive hashes
  validate; no task has been created.
- **Reviewer/service:** registered Agent Card unavailable (HTTP 404); live
  identity, contract, key pin, health, and no-task readiness remain
  unverified.
- **Custody/transfer:** no agreed secure file-transfer channel is recorded;
  archive remains local and owner-only.
- **User authority:** a separate explicit authorization for submission of the
  exact canonical target digest above is still required after every live
  preflight gate passes.

## 404 follow-up

The A2A specification defines `/.well-known/agent-card.json` as the standard
discovery URI and requires an A2A server to make an Agent Card available there
([A2A specification](https://a2a-protocol.org/dev/specification/)). The
registered path therefore remains the one to check. The ngrok documentation
says agent endpoints exist for the lifetime of the agent process and forward
traffic to an upstream service ([ngrok endpoint guide](https://ngrok.com/docs/ai-gateway/guides/creating-endpoints/)).

Plausible service-side causes include a missing Agent Card route, a registered
host that no longer matches the active endpoint, or an upstream/path-routing
configuration that does not forward this URI. The observed 404 does not
distinguish these causes. The compatible repair is for the registered service
owner to restore the Agent Card at the pinned URI (or use the authorized
registry process to issue a new pin and trust decision). I cannot apply or
verify that external service change from this repository, so live preflight
remains stopped; three unsuccessful checks do not justify trying an
unregistered route.

## Fallback-channel check

The registered reviewer profile contains only the pinned HTTPS/ngrok endpoint;
it defines no Tailscale/SFTP route or secure artifact-transfer channel. The
repository's separate Tailscale/SFTP communication design belongs to
`aligned-holistic-continual-learning-interpretability-monorepo-v1` and records
that no SSH endpoint was provisioned. It is not an available or authorized
transport for this FHE target, so I did not reuse it or search for another
reviewer.

Resume only after the registered service owner restores the pinned endpoint
and an agreed secure transfer path is available. Re-run the read-only live
preflight against the registered card, health, contract, key pin, and
authenticated no-task readiness. If any value differs from the frozen
profile, stop and obtain an authorized trust update. Submit only after those
gates pass and the user explicitly authorizes this exact target digest.

## Offline local revalidation — 2026-10-03

State slices: `private-decision-model-fhe-review-preparation-v1` and
`global-experiment-assurance-lifecycle-v1`; frozen target remains
`private-decision-model-fhe-inference-v1`.

The repeatable offline validator
(`pnpm run verify:private-decision-model-fhe-review-v1`) passed. It recomputed
the canonical target, packet, and protocol digests; verified all 13 manifest
file digests and the target's 10 source-artifact bindings; then checked that
the owner-only ZIP contains exactly the 13 manifest paths with matching
payload bytes. The canonical target remained
`43d300f3e910704016e6b953f417a7a457b2a9b69cd35f44d6620e832f39793d`, the
manifest SHA-256 remained
`e5526c254f1351584aa2dd9d0f4201da16119d518f940991cb6d7812f6b8d44f`, and the
archive SHA-256 remained
`90836174530b563179a4e7ff95ca20109f15ea2ed806d5491139f07d702e9f3a`.
Staging permissions remained `0700`, archive permissions `0600`, and the
archive owner matched the current user. The verifier is operator-side code and
is intentionally not added to the frozen target or archive.

This was a local byte/custody recheck only. The registered Agent Card was not
re-probed because the prior three checks returned 404 and the boundary says to
stop on that unavailable endpoint. No health/readiness check, task submission,
artifact transfer, FHE/model execution, or spend occurred. External review
remains `EXTERNAL_REVIEW_UNAVAILABLE`; no independent acceptance or new
authority follows from this local pass.
