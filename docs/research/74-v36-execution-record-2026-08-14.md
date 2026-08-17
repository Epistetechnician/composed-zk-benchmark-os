# V36 Execution Record — Fresh-Actor Custody Replay Manifest

State slice: `astral-fresh-actor-custody-replay-manifest-v36`

Date: 2026-08-14

Scope: pure-data synthetic packets and manifests only. No model, provider,
network, telemetry, credential, PII, raw trace, or assessment was used.

Focused test coverage:

- append-only two-packet chain and canonical round trip;
- duplicate nonce and predecessor mismatch quarantine;
- accepted-chain tamper rejection and unknown-field rejection; and
- invalid-packet quarantine without rejected-payload retention.

Disposition: V36 is local metadata-control evidence only. No execution gate,
Astral scientific claim, HSAI security claim, benchmark claim, or Evidence
Ledger mutation is created.
