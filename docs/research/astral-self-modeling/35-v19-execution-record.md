# V19 Execution Record

State slice: `astral-opaque-preference-replication-v19`.

Execution: `NotRunTargetLabelImbalance`. Confirmation: `NotAuthorized`.
Stage 1: `BlockedByStage0C`.

## Preflight result

V19 froze and hashed 320 new ambiguous-language preference families and loaded
the cached Qwen target. Exact target-repeat error was zero. Only fit/tune
unhinted target outputs were eligible at this stage; assessment unhinted outputs
remained sealed.

| Fit label | Count |
|---|---:|
| Changed after hint removal | 13 |
| Unchanged after hint removal | 227 |

The minority fraction was `5.4167%`, below the preregistered `20%`
qualification threshold. Both hint options were balanced at 120 families each,
so hint-option imbalance did not cause the failure. The frozen Qwen target
mostly ignored the weak preference hints and retained the same answer after
ablation.

The protocol stopped immediately:

- no assessment unhinted prompt executed;
- no assessment effect or label exists;
- no LoRA smoke test or explainer training ran;
- no adapter, assessment prediction, or prediction lock exists;
- no candidate classification was attempted.

Validated blocked-bundle manifest SHA-256:
`73cb90ee38dabfabc55d4885c6a1ddadb3327f4235850b3b2c20096846906bef`.

Repository-external blocked bundle:
`/tmp/astral-lm-v19-20260727-run1`.

## Disposition

The V19 weak-hint binary-change configuration is closed. Strengthening its hint,
changing the threshold, filtering families, or rebalancing after observing
these labels would be post-selection.

This does not refute trained target-specific prediction generally. It shows
that binary answer-change is unsuitable for this frozen weak-hint intervention.
A new protocol may use a prospectively defined continuous margin-effect target
or a separately designed intervention whose fit/tune qualification is not
near-degenerate. It must use new families and keep assessment sealed.

Claim ceiling: `LocalDevelopmentOpaquePreferenceReplication`. No replication,
introspection, self-modeling, faithful explanation, Stage 0C confirmation, or
Stage 1 evidence was produced.
