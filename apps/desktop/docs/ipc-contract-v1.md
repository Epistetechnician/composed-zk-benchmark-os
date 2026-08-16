# Platform IPC contract v1

State slice: `electron-release-0-desktop-shell`.

This document defines the Release 0 request/response boundary between the
Electron renderer and main process. It mirrors the platform's accepted
`src/ipc.rs` contract. The renderer is an untrusted UI client; the preload is
the only exposed API surface. The main process validates the envelope and
dispatches a fixed, read-only operation set.

## Contract identity

- Contract version: `platform-ipc.v1`
- Electron channel: `desktop:request`
- Transport: `ipcRenderer.invoke` through a context-isolated preload
- Payload policy: arbitrary JSON with a SHA-256 digest over canonical compact
  JSON; the current Release 0 operations use `{}`
- Execution policy: no process spawning, shell execution, arbitrary commands,
  filesystem commands, or native sidecar lifecycle in this slice

## Request envelope

```json
{
  "schema_version": "platform-ipc.v1",
  "request_id": "renderer-generated-opaque-id",
  "operation": "catalog.list",
  "payload": {},
  "payload_digest": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
}
```

`request_id` and `operation` are bounded, non-empty, control-free strings of at
most 128 characters. `payload_digest` is a 64-character lowercase SHA-256
digest of canonical compact UTF-8 JSON. The main process rejects wrong schema
versions, digest drift, unknown fields, malformed JSON values, and unsupported
operations before dispatch.

## Response envelope

Success:

```json
{
  "schema_version": "platform-ipc.v1",
  "request_id": "renderer-generated-opaque-id",
  "status": "Ok",
  "payload": {},
  "error": null
}
```

Failure:

```json
{
  "schema_version": "platform-ipc.v1",
  "request_id": "renderer-generated-opaque-id",
  "status": "Error",
  "payload": null,
  "error": {
    "code": "sidecar_unavailable",
    "message": "Human-readable diagnostic",
    "retryable": true
  }
}
```

Success responses contain a payload and `error: null`. Error responses contain
`payload: null` and one bounded error with a boolean `retryable` field. The
preload verifies the schema version, exact response shape, and request-id match
before returning data to React. A failure response becomes a rejected Promise
in the preload API.

## Release 0 methods

| Operation | Return value | Boundary |
| --- | --- | --- |
| `catalog.list` | `capability-catalog.v1` | Static catalog of the shell's local capability surface. |
| `replay.status` | `local-replay-status.v1` | Explicit unavailable state from the `rust-sidecar` adapter seam. |

The `rust-sidecar` adapter is a typed seam only. It does not own a command
path, spawn a process, load a binary, or read a repository. A future slice must
define those authority and custody decisions separately before adding runtime
execution. This envelope is transport and integrity metadata; it is not an
authorization system.

## Renderer security boundary

The `BrowserWindow` uses `contextIsolation: true`, `nodeIntegration: false`,
and `sandbox: true`. Only `window.desktopApi` is exposed through
`contextBridge`; the renderer cannot import Electron, Node built-ins, or an
arbitrary IPC channel. New methods must be added to the typed contract,
validated in the main process, and surfaced through an explicit preload method.
