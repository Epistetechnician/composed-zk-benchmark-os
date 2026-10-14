# V41R26 Preflight Execution Authorization

State slice: `V41R26ModelBackedCampaignPreflightScorer`.

Status: `Consumed`.

One base-model-only execution identity, `astral-v41r26-preflight-r1`, is bound
to RGS `0062848861e342609153ac6f038ee9e2256e22c1`, Astral validator
`90cdab000d9c939638ebe3f9afad8952f7ab46fc`, finalized context `ctx-ca0af7b3`, context SHA-256
`99c768798d7753d0deca4927cb46587efce88240655a7beffdcfbe12f6823c3a`,
and bundle SHA-256
`eb65171ccb7a7c0d97df1100ec1c6fbb11c9e2c52b78a9c494f5db1ebfda8f16`.

Only frozen base-model scoring is permitted. No adapter, optimizer, training,
retry, tune, assessment, or campaign worker is authorized. The node must stop
immediately after export.
