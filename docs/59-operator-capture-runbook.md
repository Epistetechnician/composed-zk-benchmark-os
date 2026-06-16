# Operator Capture Runbook

## Status And Claim Boundary

This runbook describes the operator-run, repo-external steps required to produce
one real HSAI-owned Phala/dstack artifact using the Phase 58 challenge-packet
tooling.

The runbook itself is documentation only. Following it does not, by itself,
produce accepted attestation evidence, proof, benchmark output, backend
execution evidence, or Phase 4 authorization. It merely states how an operator
may generate a real non-secret artifact bundle that could later be validated.

Phase 4 remains blocked until at least one real HSAI-owned artifact passes
validation under `docs/57-managed-attestation-real-artifact-promotion-spec.md`.
See `docs/54-proof-of-agent-anchor-phase4-boundary-note.md` for the active
boundary.

## What Is In Repo Versus Out Of Repo

In repo (deterministic, allowed, no network):

- `crates/hsai-attestation-phala` builds the HSAI-owned challenge packet and the
  non-secret capture workflow manifest.
- `crates/hsai-attestation-phala/examples/operator_capture_preflight.rs` emits
  those JSON documents from fixed sample inputs.

Out of repo (operator-controlled, network/hardware):

- Placing `expected_report_data_hex` into a Phala/dstack confidential virtual
  machine workload.
- Generating a real TDX quote or managed verifier response.
- Capturing the non-secret artifact bundle.
- Scrubbing secrets.
- Committing the artifact fixture back into the repo.

The repository cannot perform the out-of-repo steps, must not fabricate an
artifact to satisfy them, and must not commit secrets.

## Preflight

Run the example to obtain the challenge packet and capture manifest:

```sh
cargo run -p hsai-attestation-phala --example operator_capture_preflight
```

The example prints two JSON documents to stdout and the claim boundary plus the
operator next step to stderr. The first document is the challenge packet. The
second document is the capture workflow manifest.

The example uses fixed sample inputs. An operator who needs a challenge derived
from a real `AgentCase` and a real runtime anchor should construct the packet
programmatically via `build_agent_case_challenge_packet` with those inputs
rather than editing the sample inputs by hand.

The single field that must be carried byte-for-byte into the attested workload
is:

```text
challenge.expected_report_data_hex
```

This value is `report_data_binding(agent_pubkey, nonce, case_hash)` recomputed
deterministically inside the crate. It uses the shipped `hsai-attestation`
binding with the `hsai-attestation-report-data:v1` domain separator,
length-prefixed fields, big-endian nonce encoding, and SHA-256.

## Capture

The operator performs the following steps on infrastructure the repository does
not own and cannot reach.

### Step 1 — Choose the CVM product

In Phala Cloud, deploy a **Confidential VM (CVM)** with **CPU TEE (Intel TDX)**.
Do not select GPU TEE or Confidential Models for this capture — those are
separate products for model inference and are not needed for HSAI attestation
capture. A Small TDX instance (1 vCPU, 2GB RAM) is sufficient.

### Step 2 — Choose the capture mode

The capture manifest's `provider_mode` is one of:

- `local_quote`: the validator will be expected to verify a local quote and
  collateral;
- `managed_verifier`: a managed verifier response is consumed and the
  managed verifier is an explicit, disclosed trust root.

For the first real capture, `managed_verifier` is the lower-friction path: the
Phala Trust Center produces the verification report and the artifact bundle
shape matches the shipped validator.

### Step 3 — Deploy a CVM that mounts the dstack socket

Your `docker-compose.yml` must mount the dstack socket so the workload can call
`GetQuote`. Minimal skeleton:

```yaml
services:
  hsai-capture:
    image: <your-attested-workload-image>
    volumes:
      - /var/run/dstack.sock:/var/run/dstack.sock
    ports:
      - "8080:8080"
```

KMS Provider: select **Phala** (no wallet setup needed for testing). Region:
choose the closest region.

### Step 4 — Place the HSAI report data into the workload

The workload inside the CVM must call the dstack SDK `getQuote(reportData)`
with the exact 32 bytes of `challenge.expected_report_data_hex`.

Decode the hex to raw bytes and pass them directly as the `reportData`
parameter. The HSAI binding is a 32-byte SHA-256 digest, which fits the dstack
64-byte `reportData` field directly — do not hash it again, prefix it, or wrap
it.

Python (dstack-sdk):

```python
from dstack_sdk import DstackClient

client = DstackClient()
report_data_hex = challenge["expected_report_data_hex"]
report_data_bytes = bytes.fromhex(report_data_hex)
result = client.get_quote(report_data_bytes)

print("quote:", result.quote)
print("event_log:", result.event_log)
```

TypeScript (@phala/dstack-sdk):

```javascript
import { DstackClient } from '@phala/dstack-sdk';

const client = new DstackClient();
const reportData = Buffer.from(challenge.expected_report_data_hex, 'hex');
const result = await client.getQuote(reportData);

console.log('quote:', result.quote);
console.log('event_log:', result.event_log);
```

Direct Guest Agent (no SDK):

```sh
curl --unix-socket /var/run/dstack.sock \
  "http://localhost/GetQuote?report_data=0x${EXPECTED_REPORT_DATA_HEX}"
```

Trigger the quote generation inside the challenge validity window
(`challenge_created_at`, `challenge_expires_at`). After the window the challenge
is stale and the validator rejects it.

### Step 5 — Capture the non-secret artifact bundle

From the Trust Center or the CVM attestation endpoint, capture the non-secret
bundle. The manifest lists the required artifact fields. At minimum the bundle
must carry: `schema_version`, `source`, `captured_at`, `challenge_created_at`,
`challenge_expires_at`, `policy_id`, `subject`, `anchor_id`,
`agent_pubkey_spki_hex`, `nonce`, `case_hash_hex`, `expected_report_data_hex`,
`provider`, `provider_mode`, `quote_hex` or `managed_verifier_response`,
`report_data_hex`, `compose_hash`, `app_id`, `instance_id`, `os_image_hash`,
`rtmrs`, `rtmr_event_log`, `docker_image_digests`, and `trust_root_labels`.

The `report_data_hex` in the returned quote **must** equal
`challenge.expected_report_data_hex` — this is the RA-1 binding check. If they
differ, the workload did not receive the challenge correctly and the capture is
invalid.

### Step 6 — Scrub secrets

The manifest's `forbidden_artifact_fields` list is enforced: the bundle must not
contain `private_keys`, `api_tokens`, `session_cookies`, `bearer_tokens`, or
`live_service_credentials`. Do not commit secrets. If scrubbing would remove a
field the validator needs, the capture is not acceptable.

### Step 7 — Record trust roots

In `managed_verifier` mode the bundle must disclose the managed verifier service
as a trust root; the validator must not collapse managed-verifier evidence into
a pure Intel TDX trust claim. Record `phala-trust-center` and
`intel-trust-authority` explicitly.

## Binding Format Note

The HSAI Phase 57 challenge packet emits `expected_report_data_hex` as a
**32-byte SHA-256 digest** (64 hex chars), computed by the shipped
`hsai_attestation::report_data_binding` with domain separator
`hsai-attestation-report-data:v1`, length-prefixed fields, big-endian nonce,
and SHA-256.

The dstack `reportData` field accepts up to 64 bytes directly, so this digest is
placed into `reportData` byte-for-byte without hashing or wrapping. The returned
quote's `report_data` must equal this 64-hex-char value.

The existing `PhalaArtifactBundle` validator
(`crates/hsai-attestation-phala/src/artifact.rs`) enforces a *different*
captured-artifact binding format that expects a 64-byte (128 hex char)
`report_data_hex` structured as `nonce_hex || case_hash_hex || ...`.

The validator has been extended to accept **both** binding formats. The
discriminator is the hex length of `expected_report_data_hex`:

- 64 hex chars (32 bytes): Phase 57 HSAI-owned SHA-256 binding, recomputed
  via `report_data_binding(pubkey, nonce, case_hash)`.
- 128 hex chars (64 bytes): Phase 3 captured-artifact format, validated as a
  literal `nonce_hex || case_hash_hex` prefix.

The existing Phase 3 fixture continues to validate unchanged.

## Verification Order The Validator Will Apply

When the captured bundle is later brought back to the repo, the
`hsai-attestation-phala` validator applies the Phase 57 verification order:

```text
1. Parse the artifact without network access.
2. Reject expired challenge windows.
3. Recompute expected_report_data_hex from agent_pubkey, nonce, case_hash.
4. Check report_data_hex == expected_report_data_hex.
5. Check the quote or managed verifier response contains the same report data.
6. Verify quote authenticity or managed verifier authenticity.
7. Check freshness of the observed artifact.
8. Check compose hash equality.
9. Check optional Docker image digest equality when policy requires it.
10. Replay RTMR/event-log data when policy requires it.
11. Check anchor id alignment.
12. Emit all relied-on trust roots in the ClaimEnvelope.
```

Steps 5 and 6 are the points where local fixture validation ends and real
authenticity verification must occur. A future explicit phase must authorize
real managed-service signature verification, JWKS/JWT validation, or local Intel
DCAP implementation. The current crate does not perform these.

## Committing The Artifact

After a real, HSAI-owned capture passes the validator, a small non-secret
fixture may be committed under `crates/hsai-attestation-phala/tests/fixtures/`
and covered by an integration test. The fixture is local regression evidence
only.

Before committing:

- Confirm the artifact was generated with the HSAI-owned fresh challenge from
  this runbook, not a reused or third-party challenge.
- Confirm no forbidden secret field is present.
- Confirm the commit records the exact trust roots relied on.

Do not commit a fabricated artifact. Do not commit secrets. Do not build
`crates/hsai-agent-anchor-registry` until the Phase 57 acceptance record exists.

### First capture record (2026-06-16)

The first real HSAI-owned Phala/dstack artifact was captured and accepted on
2026-06-16 using this runbook. Record:

- Fixture: `crates/hsai-attestation-phala/tests/fixtures/phala_hsai_owned_real_2026_06_16.json`
- Integration test: `crates/hsai-attestation-phala/tests/phala_hsai_owned_real.rs`
- Capture target: `tdx.small` CVM on Phala Cloud (deleted after capture).
- Agent keypair: real P-256 key, private key not committed.
- Trust roots: `managed:phala-trust-center`, `managed:intel-trust-authority`,
  `dstack-os:<os_image_hash>`, `compose:<compose_hash>`.
- Maturity: `Attested`, never `Proven`.
- See `docs/57-managed-attestation-real-artifact-promotion-spec.md` "First Real
  HSAI-Owned Artifact Capture Record" for the full acceptance facts.

## What This Runbook Does Not Authorize

- Live Phala API calls from inside normal tests.
- Network access from the crate.
- Real Intel DCAP implementation.
- Real managed-service signature, JWKS, or JWT verification.
- Fabricated quote, verifier, or benchmark artifacts.
- Phase 4 `crates/hsai-agent-anchor-registry`.
- Any claim above `Attested`.

## State Slice

```text
crates/hsai-attestation-phala/examples/operator_capture_preflight.rs
docs/59-operator-capture-runbook.md
docs/58-managed-attestation-challenge-capture-tooling-notes.md
README.md
AGENTS.md
```
