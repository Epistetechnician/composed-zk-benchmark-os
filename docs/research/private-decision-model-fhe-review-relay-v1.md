# Private Decision Model FHE Reviewer Relay Note V1

State slices: `private-decision-model-fhe-review-preparation-v1` and
`global-experiment-assurance-lifecycle-v1`; target:
`private-decision-model-fhe-inference-v1`.

## For the registered reviewer service owner

The configured public Agent Card URL
`https://huntsman-plenty-handwash.ngrok-free.dev/.well-known/agent-card.json`
returned HTTP 404 on two checks on 2026-10-01 and on a recheck on 2026-10-02.
Please restore the card at this pinned URL and confirm that it advertises the registered reviewer identity,
HTTP+JSON 1.0 binding, bearer-authenticated intake URL, and the agreed review
contract. If this registration must change, provide the authorized registry
update and new trust decision through the already authorized coordination
channel; the operator will not follow an unregistered URL or key.

No approved coordination conversation or secure artifact-transfer channel is
available in this workspace. Please identify the agreed secure file channel
out of band. Review artifacts must not be sent in A2A message bodies.

## Frozen target metadata

- Canonical target SHA-256:
  `43d300f3e910704016e6b953f417a7a457b2a9b69cd35f44d6620e832f39793d`.
- Protocol file SHA-256:
  `669e9e0f67e0b8b054a9dcfd28e893974503a6a36758a3005fa221356201b3c3`.
- Review packet file SHA-256:
  `61b575b8841dbcba1d0271942cf38ed9de1b4d92098e04a42d6fc1ced4ce209d`.
- Artifact manifest SHA-256:
  `e5526c254f1351584aa2dd9d0f4201da16119d518f940991cb6d7812f6b8d44f`.
- Archive SHA-256:
  `90836174530b563179a4e7ff95ca20109f15ea2ed806d5491139f07d702e9f3a`.
- Claim ceiling: `LocalDevelopmentSyntheticFHEInferenceV1`.

The target archive remains local and owner-only. No artifact bytes have been
transferred, and no review task has been created. This relay is a readiness
request, not a review submission or independent decision.

After the pinned card and secure file channel are restored, the operator will
re-run the read-only card, health, contract, key-pin, and authenticated
no-task-readiness checks. Submission remains closed until all checks pass and
the user explicitly authorizes this exact target.
