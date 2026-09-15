# Phase 841: Universal Harness Interoperability V1

State slice: `universal-harness-interoperability-v1`.

Status: local pure-data contract implemented and independently validated. This
phase does not create a runtime adapter, open a network connection, spawn an
agent, invoke an MCP tool, call ACP/A2A, use OpenSSH, access credentials, call
a provider, execute a model, or write accepted evidence.

## Purpose

The protocol composes existing interoperability surfaces without pretending
that any one of them is a complete harness control plane:

| Binding | Role | Declared transport | Contract ceiling |
| --- | --- | --- | --- |
| `acp.agent_client.v1` | client to coding agent | local stdio JSON-RPC | proposal only |
| `mcp.tool_context.v1` | agent to tool/resource server | stdio or Streamable HTTP JSON-RPC | proposal only |
| `a2a.agent_delegate.v1` | agent to independent agent | Streamable HTTP task model | proposal only |
| `openssh.remote_transport.v1` | transport adapter to remote node | OpenSSH session or SFTP | transport only |

The manifest also freezes a closed lifecycle, envelope identity fields,
capability policy, trust zones, artifact retention, redacted observability,
and an all-false execution boundary. Discovery, transport reachability, tool
metadata, and model output cannot grant authority.

## Source and validation

The implementation is under
`tools/universal_harness_interoperability_v1/`:

- `protocol_v1.py` owns the closed-world specification and canonical digest
  rules.
- `compiler_v1.py` emits a one-time manifest with source identities.
- `validator_v1.py` independently recomputes source identities, protocol
  structure, protocol digest, manifest digest, and non-authorizing controls.
- `tests/test_v1.py` covers binding, transport, authority, duplicate-key,
  source-identity, digest, and overwrite failures.

Validation commands:

```text
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./scripts/python -B -m pytest -q tools/universal_harness_interoperability_v1/tests
./scripts/python -B -m tools.universal_harness_interoperability_v1.compiler_v1 --output /external/universal-harness-interoperability-v1/manifest.json
./scripts/python -B -m tools.universal_harness_interoperability_v1.validator_v1 --manifest /external/universal-harness-interoperability-v1/manifest.json
```

The example output path is external and illustrative. No generated manifest is
committed by this phase.

## Nonclaims and next gate

This is not a universal wire protocol, production harness, security proof,
independent acceptance system, remote-execution policy engine, or evidence
promotion mechanism. The next implementation gate requires an independent
review of the exact schema and current source digests before any concrete ACP,
MCP, A2A, OpenSSH, identity, or runtime adapter is added.

## Reference surfaces

- [Agent Client Protocol](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/docs/protocol/v1/overview.mdx)
- [Model Context Protocol transports](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
- [Agent2Agent protocol](https://a2a-protocol.org/)
- [Harness Protocol](https://harnessprotocol.io/docs/intro/)
- [ssh-mcp adapter](https://github.com/slepp/ssh-mcp)
