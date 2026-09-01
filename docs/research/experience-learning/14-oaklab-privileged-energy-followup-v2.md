# Oak Lab privileged energy follow-up V2

State slice: `oaklab-experience-learning-benchmark-v2`

The same sealed real campaign still has no measured joule receipt. On
2026-08-30 the declared path was rechecked:

```text
powermetrics --samplers cpu_power -n 1 -i 1000
must be invoked as the superuser
sudo -n powermetrics --samplers cpu_power -n 1 -i 1000
sudo: a password is required
```

This is an environment authorization failure, not a zero-energy observation.
No synthetic joules were inserted and no publication requirement was relaxed.

## Operator execution contract

Run on the declared macOS Apple Silicon host with a terminal granted the
required privileged power-sampling entitlement. The capture must cover the
sealed campaign arm and retain its raw output:

```sh
sudo powermetrics --samplers cpu_power -i 1000 -n 30 > /ABSOLUTE/PATH/powermetrics.txt
```

Convert only the declared CPU power samples to a monotonic
`timestamp_s,power_w` CSV, then integrate with the repository tool:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.measure_energy_v1 \
  --trace /ABSOLUTE/PATH/cpu_power_trace.csv \
  --output /ABSOLUTE/PATH/energy_receipt.csv \
  --run-id oaklab-real-campaign-v2 \
  --hardware macos:powermetrics:cpu_power \
  --events EVENT_COUNT \
  --campaign-manifest-sha256 e76a080f51287382f996cc2d222d495400fdeb6ee3cde290ea456199fb268e0b \
  --matrix-digest c0cde1c6b47a785d2e54ac2a731be6a9bfe1cae53f4eb1812795ef4ef3410bce \
  --matrix-digest a45df58b9a9519466abef26babcd23dc62df35395ebb9ec0336b03a9c1a05d05 \
  --matrix-digest 8b89f81f7f88f6b0801f4c04ceefd9a0f50502e7be6a31162be9fe772f18c1cd \
  --guard-result-digest 74d61e35f8326f4044302ff6634c5eb2d2b66c6b2d97f825c76af7f852598199 \
  --guard-result-digest f9342b839475993a7ec3257c1426f62f6b467c141d27a6f0c8cf584f78011230 \
  --guard-result-digest fc3fe4cabedaf148dca5013719ed8e69a8ef4203a7e9409a898c228900bfb628 \
  --guard-result-digest ba6776b485e610813b992242ad8c3ea9ece58c8cecbe4bbba25b1816a6ce9129 \
  --backend-result-digest 17404d36f9e34b188c8c55ee4ac9c3e974f1d4f5fd5fc816bac8e5c164b9c9c2 \
  --backend-result-digest 6ccb85bbccdbf3c05fc505e67e3a1ce04c8e366cb5accc1158dcadacf52c53b0 \
  --backend-result-digest f1ef29942324db2ac46a45658acb72a9fd4bc7d436b3b15d557eb75059a67910 \
  --backend-result-digest 71451c48dbaddfbcf16b2b89f84ab37a7c4b9731575ae0e66d8e97fe423478d1
```

The receipt must contain exactly one row, a trace SHA-256, at least two
strictly increasing samples, non-negative finite watts, the fixed trapezoidal
integration rule, and the campaign run identifier. For the current sealed
campaign, pass the exact matrix, guard, and backend result digests listed below
to bind the trace to the workloads:

```text
campaign_manifest_sha256=e76a080f51287382f996cc2d222d495400fdeb6ee3cde290ea456199fb268e0b
matrix_digests=
  c0cde1c6b47a785d2e54ac2a731be6a9bfe1cae53f4eb1812795ef4ef3410bce
  a45df58b9a9519466abef26babcd23dc62df35395ebb9ec0336b03a9c1a05d05
  8b89f81f7f88f6b0801f4c04ceefd9a0f50502e7be6a31162be9fe772f18c1cd
guard_result_digests=
  74d61e35f8326f4044302ff6634c5eb2d2b66c6b2d97f825c76af7f852598199
  f9342b839475993a7ec3257c1426f62f6b467c141d27a6f0c8cf584f78011230
  fc3fe4cabedaf148dca5013719ed8e69a8ef4203a7e9409a898c228900bfb628
  ba6776b485e610813b992242ad8c3ea9ece58c8cecbe4bbba25b1816a6ce9129
backend_result_digests=
  17404d36f9e34b188c8c55ee4ac9c3e974f1d4f5fd5fc816bac8e5c164b9c9c2
  6ccb85bbccdbf3c05fc505e67e3a1ce04c8e366cb5accc1158dcadacf52c53b0
  f1ef29942324db2ac46a45658acb72a9fd4bc7d436b3b15d557eb75059a67910
  71451c48dbaddfbcf16b2b89f84ab37a7c4b9731575ae0e66d8e97fe423478d1
```

Append one `--matrix-digest`, `--guard-result-digest`, and
`--backend-result-digest` flag per digest, plus
`--campaign-manifest-sha256`, to the command. Validate the receipt through
the publication gate with the same backend receipts before any energy
statement. Operation counts remain a separate proxy and cannot substitute
for joules.
