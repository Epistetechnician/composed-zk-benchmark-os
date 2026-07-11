# Phase 716 HSAI Gateway Threat Ordinal Charon Version Subcommand Closure

## Status

Complete as a documentation-first built-tool identity correction.

State slice:
`phase-716-hsai-gateway-threat-ordinal-charon-version-subcommand-closure`.

Classification: `ExactBuiltCharonVersionSubcommandSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 717 uses canonical run root `hsai-phase717-efa3782c` and witness
`phase717ExtractedThreatOrdinalWitnesses`.

The exact bounded sandboxed built-Charon identity command is:

```text
charon version
```

It must exit zero and print exactly `0.1.220` plus one newline. `--version`,
`-V`, help-text inference, or substring-only matching is prohibited. The pinned
[CLI enum](https://github.com/AeneasVerif/charon/blob/909ff09ad0f144f83d354f2c3d26f631fb9f8e9a/charon/src/bin/charon/cli.rs)
defines `Version` as a subcommand; the pinned
[entrypoint](https://github.com/AeneasVerif/charon/blob/909ff09ad0f144f83d354f2c3d26f631fb9f8e9a/charon/src/bin/charon/main.rs)
prints `charon_lib::VERSION`; and the pinned
[manifest](https://github.com/AeneasVerif/charon/blob/909ff09ad0f144f83d354f2c3d26f631fb9f8e9a/charon/Cargo.toml)
sets package version `0.1.220`.

After commit, clean-tree, and disk gates, Phase 717 may make one attempt. The
exact fixture sequence, Charon toolchain token, canonical UTF-8 client,
identity-log allowlist, component list, run-root order, bounded runner,
source/tool pins, cache closure, sandbox attribution, cleanup, evidence, and
claim rules remain.

Phase 716 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
