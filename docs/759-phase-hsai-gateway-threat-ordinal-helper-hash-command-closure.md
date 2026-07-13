# Phase 759 HSAI Gateway Threat Ordinal Helper Hash Command Closure

## Status

Complete as a documentation-first shell-semantics correction.

State slice:
`phase-759-hsai-gateway-threat-ordinal-helper-hash-command-closure`.

Classification: `ShellIndependentHelperHashAssertionsSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

Phase 760 uses run root `hsai-phase760-efa3782c`, detached repository root
`hsai-phase760-repo-efa3782c`, and witness
`phase760ExtractedThreatOrdinalWitnesses`.

Before helper compilation or execution, Phase 760 must run three explicit
`shasum -a 256` producers, one for each committed helper. Each producer must be
followed immediately by an assertion over only that producer's exact digest:

```text
bounded_runner.py      933c573a0820106df62b431db829668bf45a305b84a49a2d3bdcb6899b9b0198
raw_archive_validator.py 31fa2450fe7e3ce87c13dd844ac6fde1cde0a4a81e7d351276e5dd2a4ba32692
fixture_validator.py   75a0e13aa06123b7bcc7ffd8d1f13bed9d318eb89f9e378e7c7ab6ff5bdd4c07
```

The command may not depend on scalar word splitting, `set --`, shell arrays,
loop-parsed filename/digest pairs, `SH_WORD_SPLIT`, or a combined multi-helper
assertion. It must work under the repository's active zsh without changing
shell options. Only after all three independent assertions pass may helper
compilation, focused tests, and the parser self-test begin.

After this correction is committed and every inherited Phase 749-758 root,
disk, preservation, source, token, acquisition, archive, sandbox, extraction,
witness, cleanup, evidence, and claim gate passes, Phase 760 may make one
attempt. The first failure still stops the phase without repair or replay.

Phase 759 runs no helper, network, compiler, backend, or kernel command and
creates no proof, accepted evidence, Level2+, score axis, semantic correctness,
production readiness, SOTA, breakthrough, full-security claim, external audit,
or action authority.
