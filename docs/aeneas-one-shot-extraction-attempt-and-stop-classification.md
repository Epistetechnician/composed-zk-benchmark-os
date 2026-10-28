# Aeneas one-shot extraction attempt and stop classification

Claim ceiling: `Level0DesignNote`. Local observation only; not proof, not accepted evidence.

## What was done

- Downloaded the pinned release asset `aeneas-macos-aarch64.tar.gz`
  (tag `nightly-2026.07.10-c2015b8`) into a new empty directory outside the repo,
  `/Users/shaanp/aeneas-tool-1/`. Size `123234656` and SHA-256
  `fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45`
  match the pin in doc 666. Extracted into `/Users/shaanp/aeneas-tool-1/x/`.
- Static inspection only (`file`, `otool -L`, `rust-toolchain`). No downloaded
  binary was executed: the harness auto-mode classifier denied running
  `aeneas`/`charon`, so **no extraction was performed**.

## Static findings (resolve nothing yet, confirm doc 669)

- `aeneas` links only `@executable_path/libs/libgmp.10.dylib` (shipped): runnable in principle.
- `charon` and `charon-driver` link absolute `/nix/store/...` libiconv and zlib
  paths that do not exist on this host (doc 669, `DriverDynamicLinkUnavailable`).
- Charon needs Rust `nightly-2026-06-01` plus `rustc-dev`; this host has
  `nightly-2026-10-25` and others but not the pinned one (doc 668/679 territory).

## Classification of the Aeneas-lane stop docs (667-764)

`tools/aeneas-preflight-classification/classify.py` buckets the 45 stop/failure/
mismatch docs by filename keyword (heuristic, first match wins):

| cause | count |
|---|---|
| toolchain (Charon/Rust/Lean/Lake identity, linkage, versions) | 18 |
| provenance (acquisition, archive, metadata, helper/fixture specs) | 16 |
| ordering (protocol order, worktree, shell/orchestration, sandbox) | 11 |

Toolchain is the largest bucket. Many "ordering"/"provenance" stops are
self-imposed protocol-strictness stops (doc 764 `ManualExecutionProtocolThresholdReached`),
not Aeneas faults. Counts are keyword-based, not a reading of each doc.

## Blocker

Executing the downloaded Aeneas/Charon binaries needs explicit user permission
in the harness, and Charon additionally needs the nix libs (or a source build
per doc 670) and the pinned nightly. Test: `cd tools/aeneas-preflight-classification && /usr/bin/python3 -I -m unittest discover -s .`
