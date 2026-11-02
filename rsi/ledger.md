# RSI ledger

## 2026-10-31 — iteration 1, objective 1 (aeneas preflight classification)

- **Hypothesis:** keyword-only filename rules misfile stop docs; using each doc's
  explicit `Diagnostic:` line (mapped by documented meaning) gives evidence-backed
  causes.
- **Baseline:** 45 stop docs (phases 667-764), filename-keyword only:
  toolchain 18 / provenance 16 / ordering 11. Evidence: 45/45 filename.
- **Change:** `classify.py` adds `DIAGNOSTIC_CAUSES` map, primary evidence order
  diagnostic > stop code > filename; unmapped diagnostics stay `unclassified`.
  Added 3 tests (diagnostic overrides filename, unmapped not silently filed,
  filename-only evidence bounded).
- **Command:** `python3 tools/aeneas-preflight-classification/test_classify.py`
  and `python3 tools/aeneas-preflight-classification/classify.py docs`.
- **After:** 45 docs: toolchain 24 / provenance 14 / ordering 7.
  Evidence: diagnostic 41, code 4, filename 0. Tests: 6/6 pass.
- **Verdict: KEEP.** Real before/after measurement; all tests pass; no assertion
  removed. Caveat: the diagnostic→cause mapping is a judgment on documented
  meaning; reviewers should spot-check the 41 mapped entries.

## Open for next iteration

- Objective 2 (operator soak campaign aggregation) not yet started.

## 2026-10-31 — iteration 2, objective 2 (operator soak sweep)

- **Hypothesis:** the operator soak example, run over a large seed range one
  family at a time, surfaces replay, oracle, or claim-boundary failures.
- **Baseline / setup:** `operator_soak_campaign` (release) with the smoke
  profile. Default limits cap a campaign at 8 seeds and 3 families, and
  `max_shards` is 8, so "all families at >= 4096 seeds" was run as 9 families
  x 512 campaigns of 8 seeds (seeds 0..4095, 8 shards each).
- **Change:** no library or source change. Added the sweep harness
  `tools/rsi-soak-sweep/sweep.sh` and aggregator `aggregate.py`. Artifact
  trees are deleted after each campaign; only summaries are kept.
- **Command:** `tools/rsi-soak-sweep/sweep.sh`, then
  `python3 tools/rsi-soak-sweep/aggregate.py <sweep.jsonl>`.
- **Result (4608 campaigns, 36,864 cases, 167,936 traces):**
  nonzero exit 0; replay_failed 0; failure_count 0; pack_write 0;
  local_oracle_capability_gap 0; claim boundary Level0DesignNote in all runs.
  No failure, so no failing test was added (nothing to reproduce).
- **Per-family finding:** `mutation_no_target_count` is nonzero for four
  families. branching_fsm, memory_heavy_state_machine, and
  public_private_boundary_stress each have 4096 (one per seed); zkml_control_flow_mixed
  has 4096. The other five families have 0. These targetless mutations are
  skipped silently (`runner.rs` ~L563) and the aggregate counter cannot say
  which mutation class caused them.
- **Caveats:** the summary carries no per-class breakdown, and smoke writes no
  failure packs, so mutation-class failure detail is not retained. The
  measurement covers only the smoke profile's default mutation set.
- **Verdict: KEEP** (new measurement tooling and a real sweep with recorded
  numbers; no library behavior changed; no assertion touched).

## Open for next iteration

- Identify which mutation class produces the silent no-target skips for the four
  families. Needs a per-class probe in a test, not a library change.
- Expose per-class counters or failure packs for the smoke profile so
  objective 2 can report failure detail by mutation class.
