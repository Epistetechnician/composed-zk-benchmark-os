# Independent review communication boundary V1

State slice: `aligned-holistic-continual-learning-interpretability-monorepo-v1`.

This package implements a bounded, signed clarification mailbox and a sealed
independent-verdict contract. It is a local contract and does not run an SSH
server, invoke a reviewer, execute a model, call a provider, access raw traces,
or mutate the Evidence Ledger.

The two phases are intentionally separate:

1. `CLARIFICATION` permits an alternating advisory-reviewer question and
   operator answer chain. Every envelope is Ed25519-signed, body-digest bound,
   parent-linked, deadline-bound, and limited by `max_messages`.
2. `SEALED` closes the mailbox and binds the packet digest plus transcript
   digest into `sealed_packet_sha256`. The final reviewer must start a fresh
   review process and return one `ACCEPT` or `REJECT` signed by a registry-bound
   key marked `independently_administered=true` and `conflict_free=true`.

Every communication scope field is locked false:

- `model_execution`
- `provider_calls`
- `raw_trace_access`
- `evidence_ledger_mutation`

The verdict also carries `execution_enabled=false`,
`model_execution_authorized=false`, and `assessment_opened=false`. A valid
verdict therefore remains a review result, not an execution grant.

## Handoff procedure

The operator creates a frozen packet outside this package and computes its
canonical digest. The packet must include the exact source, runtime, custody,
validator, claim ceiling, and execution-disabled fields required by the active
research slice. The operator then creates a `FileMailbox` bound to that digest.

Each participant keeps a separate local mailbox. The advisory reviewer signs
and exports a `QUESTION`; the operator imports that envelope and its matching
body without re-signing it, then signs and exports an `ANSWER`. The loop stops
at the fixed message limit or deadline. The operator calls `FileMailbox.seal()`,
closes SFTP write access, and gives the final reviewer only the sealed packet,
mailbox contents, and externally published key registry. Do not mount one
writable mailbox on both hosts.

The final reviewer uses `verify_seal()` and `verify_verdict()`. A source,
protocol, runtime, corpus, custody, or configuration change requires a new
packet digest and a new mailbox. No receipt from the old digest transfers to
the new one.

## Transport boundary

Use Tailscale/WireGuard for private reachability and OpenSSH SFTP for file
exchange. The SSH account must be a dedicated unprivileged account with
password login, shell, TTY, port forwarding, X11 forwarding, agent forwarding,
and user environment disabled. Use a root-owned chroot with only `/incoming`
and `/outgoing` children writable under the external ACL. Transfer immutable
envelope files and body files only. Do not mount the operator checkout or grant
the reviewer an interactive shell.

Example `sshd_config` restriction:

```text
Match User review-drop
    ChrootDirectory /srv/review-drop
    ForceCommand internal-sftp -d /incoming
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    PermitTTY no
    AllowTcpForwarding no
    AllowAgentForwarding no
    X11Forwarding no
    PermitUserEnvironment no
    PermitUserRC no
    DisableForwarding yes
```

The chroot directory and every parent must be root-owned and not writable by
the review account. Only its `/incoming` and `/outgoing` children should be
writable, with direction enforced by the host ACL or an external custodian.
Verify the SSH host-key fingerprint out of band; `ssh-keyscan` alone is not a
trust decision.

The final reviewer key must be provisioned and published by an external
registry owner. A key generated or controlled by the operator, another task in
the same Codex account, or the same control plane is advisory only.

## Minimal Python shape

```python
from pathlib import Path

from tools.independent_review_communication_v1 import FileMailbox, sign_message

mailbox = FileMailbox(
    Path("/external/review-mailbox-P0"),
    packet_digest="sha256:<64 lowercase hex>",
    max_messages=6,
    deadline="2026-09-12T00:00:00Z",
    registry=trusted_keys,
)
question = sign_message(
    packet_digest=mailbox.packet_digest,
    parent_message_id=None,
    turn=0,
    kind="QUESTION",
    sender_id="advisory-reviewer",
    sender_role="ADVISORY_REVIEWER",
    recipient_role="OPERATOR",
    signing_key_id="advisory-key",
    created_at="2026-09-11T12:00:00Z",
    body=b"factual question",
    private_key=advisory_private_key,
)
mailbox.append(question, b"factual question")
```

This example is illustrative. It does not create a key registry, authorize
execution, or prove that a reviewer is independent. The external registry and
the active slice's packet validator remain authoritative.

## CLI

Run the CLI with the repository's managed Python launcher:

```text
./scripts/python -B tools/independent_review_communication_v1/cli.py packet-digest --input packet.json
```

Generate keys only in an external owner-controlled directory. The private file
contains exactly 32 raw Ed25519 bytes and is created with mode `0600`:

```text
./scripts/python -B tools/independent_review_communication_v1/cli.py keygen \
  --private-output /external/operator.key \
  --public-output /external/operator-registry.json \
  --key-id operator-key \
  --identity operator \
  --role OPERATOR
```

The advisory reviewer uses `append` with `--kind QUESTION`. Transfer the
resulting `messages/<turn>-<message_id>.json` and matching
`bodies/<message_id>.bin` through the SFTP direction assigned to the operator.
The operator imports the signed files into its local mailbox; `import-message`
does not re-sign or change the sender identity:

```text
./scripts/python -B tools/independent_review_communication_v1/cli.py import-message \
  --mailbox /external/operator-mailbox-P0 \
  --packet-digest sha256:... \
  --max-messages 6 \
  --deadline 2026-09-12T00:00:00Z \
  --registry /external/key-registry.json \
  --message-file /external/incoming/messages/0000-<message-id>.json \
  --body-file /external/incoming/bodies/<message-id>.bin
```

Inspect the local chain to obtain the current parent id before signing the
next answer:

```text
./scripts/python -B tools/independent_review_communication_v1/cli.py inspect \
  --mailbox /external/operator-mailbox-P0 \
  --packet-digest sha256:... \
  --max-messages 6 \
  --deadline 2026-09-12T00:00:00Z \
  --registry /external/key-registry.json
```

The operator uses `append` with `--kind ANSWER` and the inspected previous
`message_id` as `--parent-message-id`. Transfer each answer back using the
opposite SFTP direction, and import it into the reviewer's local mailbox.
Neither side may append after the fixed deadline, message limit, or seal.
At the end of clarification, both participants seal their local mailbox with
the same packet, transcript, deadline, claim ceiling, and operator fields.
Compare `sealed_packet_sha256` out of band. The digests must match before
either SFTP write path is closed.

The operator seals the complete local mailbox:

```text
./scripts/python -B tools/independent_review_communication_v1/cli.py seal \
  --mailbox /external/review-mailbox-P0 \
  --packet-digest sha256:... \
  --max-messages 6 \
  --deadline 2026-09-12T00:00:00Z \
  --registry /external/key-registry.json \
  --claim-ceiling LocalDevelopmentInstrumentFeasibilityOnly \
  --operator-identity operator \
  --operator-key-id operator-key \
  --sealed-at 2026-09-11T12:02:00Z
```

The advisory reviewer runs the same `seal` command against its local mailbox
with the same values, verifies the same `sealed_packet_sha256`, and then stops
all writes. The operator transfers the frozen packet, the operator-side
`messages/`, `bodies/`, and `seal.json` bundle only after both mailboxes are
closed.

On the fresh final-review host, verify the copied sealed bundle before reading
the packet as evidence:

```text
./scripts/python -B tools/independent_review_communication_v1/cli.py verify-seal \
  --mailbox /external/final-review-mailbox-P0 \
  --packet-digest sha256:... \
  --max-messages 6 \
  --deadline 2026-09-12T00:00:00Z \
  --registry /external/key-registry.json
```

After a fresh process reviews only that sealed bundle, it emits exactly one
decision:

```text
./scripts/python -B tools/independent_review_communication_v1/cli.py sign-verdict \
  --mailbox /external/final-review-mailbox-P0 \
  --packet-digest sha256:... \
  --max-messages 6 \
  --deadline 2026-09-12T00:00:00Z \
  --registry /external/key-registry.json \
  --private-key /external/final-reviewer.key \
  --decision ACCEPT \
  --reviewer-identity external-reviewer \
  --signing-key-id final-key \
  --reviewed-at 2026-09-11T12:10:00Z \
  --output /external/outgoing/verdict.json
```

Transfer only `verdict.json` back to the operator and verify it against the
operator's sealed mailbox:

```text
./scripts/python -B tools/independent_review_communication_v1/cli.py verify-verdict \
  --mailbox /external/review-mailbox-P0 \
  --packet-digest sha256:... \
  --max-messages 6 \
  --deadline 2026-09-12T00:00:00Z \
  --registry /external/key-registry.json \
  --verdict /external/incoming/verdict.json
```

Use `REJECT` when any fixed prerequisite fails. Do not place private key files,
raw prompts, raw traces, or live custody material in this repository.
