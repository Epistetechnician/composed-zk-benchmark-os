# Independent review communication V1

State slice: `aligned-holistic-continual-learning-interpretability-monorepo-v1`.

Status: additive local contract implemented; no SSH endpoint provisioned, no
reviewer contacted, no model/provider executed, and no authorization granted.

## Purpose

This boundary makes recursive clarification useful without allowing recursive
operator/reviewer interaction to become the final authority path. The
clarification phase is an auditable engineering channel. The verdict phase is
an isolated, digest-bound review.

```text
signed clarification messages
        |
        v
sealed packet = packet digest + transcript digest
        |
        v
fresh independent review process
        |
        v
signed ACCEPT or REJECT
```

## State machine

| State | Permitted action | Exit artifact |
| --- | --- | --- |
| `CLARIFICATION_OPEN` | Alternating reviewer `QUESTION` and operator `ANSWER`; fixed limit and deadline | Signed message files |
| `SEALED` | No further mailbox writes; final reviewer receives the sealed bundle | `seal.json` and `sealed_packet_sha256` |
| `VERDICT` | Fresh final review process emits exactly `ACCEPT` or `REJECT` | Digest-bound Ed25519 verdict |
| `SUPERSEDED` | Any packet/configuration change | New packet identity and new cycle |

`ACCEPT` never sets execution permission. The verdict is valid only as an
independent review of the exact sealed packet. The active research slice must
perform its own authorization check before any model or provider action.

## End-to-end exchange

Use two local mailboxes, one per host. Exchange only immutable signed message
envelopes and their matching body files through the directionally restricted
SFTP drop:

```text
reviewer local mailbox --QUESTION--> operator SFTP inbox
operator imports QUESTION and signs ANSWER
operator local mailbox --ANSWER--> reviewer SFTP inbox
reviewer imports ANSWER
```

The recipient runs `import-message`; it verifies the original signature,
packet digest, role, parent chain, body digest, deadline, and message limit.
It never re-signs the received message. `inspect` reports the current chain
head so the next signer can use the exact parent id. A shared writable mailbox
is prohibited because it would allow one side to rewrite the other side's
local evidence boundary.

When clarification ends, both participants seal their complete local mailbox
with the same packet, transcript, deadline, claim ceiling, and operator
identity/key fields. They compare `sealed_packet_sha256` out of band; a
mismatch stops the cycle. Both SFTP write ACLs then close. The operator-side
sealed bundle contains the frozen packet, every signed envelope, every body,
the external key registry, and `seal.json`. The final reviewer copies that
bundle to a fresh independently administered host, verifies the seal, reviews
the exact packet, and emits one signed `ACCEPT` or `REJECT`. The operator
verifies the returned verdict against the same packet, seal, complete
transcript, registry, reviewer identity, and conflict-of-interest fields.

No live SSH endpoint is created by this repository. Host provisioning,
Tailscale/WireGuard ACLs, out-of-band host-key verification, key-registry
publication, and final reviewer custody remain external administrative steps.

## Independence conditions

The final registry entry must identify a reviewer key with:

- a separate identity from the operator;
- a separately administered system/account;
- no implementation or analysis role;
- control of its own logs and decision;
- a conflict-of-interest-free assertion.

SFTP, Tailscale, a second Codex task, a user-created subagent, or a valid local
signature does not establish these conditions. If those conditions are absent,
the result is `PRE_REVIEW` or advisory review, not independent acceptance.

## Transport boundary

Use Tailscale/WireGuard for private reachability and OpenSSH SFTP for file
exchange. The SSH account must be a dedicated unprivileged account with a
root-owned chroot, `internal-sftp`, password login disabled, and shell, TTY,
port forwarding, X11 forwarding, agent forwarding, and user environment
disabled. Only `/incoming` and `/outgoing` children should be writable under
the external ACL. Verify the SSH host-key fingerprint out of band;
`ssh-keyscan` alone is not a trust decision.

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

## Current repository boundary

For the current trace-completeness and causal-monitor work, this utility is
limited to exact source/protocol packet inspection, custody and digest checks,
hermetic contract validation, and confirmation that execution remains disabled.
It must not load models, call providers, retain raw traces, mutate accepted
Evidence Ledger state, reopen terminal V2 results, or raise the claim ceiling.

## Verification

The focused contract command is:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0 PYTEST_ADDOPTS= PYTEST_PLUGINS= PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./scripts/python -B -m pytest -q tools/independent_review_communication_v1/tests
```

The package uses strict JSON parsing, canonical sorted JSON, SHA-256 digest
binding, Ed25519 signatures, exclusive file creation with `O_NOFOLLOW` where
available, body/envelope closed-world checks, parent-chain validation, and
post-seal digest verification.
