# V41R8 Exact-Runtime No-Model Parity Authorization

State slice: `V41R8ExactRuntimeNoModelParity`.

Status: `OneNoModelParityJobAuthorized / ModelExecutionUnauthorized`.

One clock-locked H100 job with zero restarts and a 30-minute run ceiling is
authorized to build and test the exact V41R8 image. It is bound to RGS commit
`d13fc6c8468f2dd3aa26a818fd468f09dc4af92e`, context `ctx-f71c03bd`, context
SHA-256 `007f52b0b9e9b1bb27101a10eda1500ed958d05bd11de91010f5210a78208ab0`,
and the pinned Torch 2.10.0/CUDA 12.8 base-image manifest recorded in RGS.

The build and run may verify exact dependencies, CUDA/H100 identity,
`Mxfp4Config(dequantize=false)`, and hermetic V41R8/V41R7/V41 tests. They may
not access the GPT-OSS tokenizer or checkpoint. The only passing receipt is:

```json
{"classification":"V41R8ExactRuntimeParityPassed","model_access":false,"scientific_execution":false}
```

Any failure consumes this parity identity. A pass does not authorize model
access or a scientific run; it opens only a separate review and authorization
decision.
