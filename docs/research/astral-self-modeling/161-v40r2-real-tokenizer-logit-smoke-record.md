# V40R2 Real Tokenizer and Logit Smoke Record

State slice: `V40R2RealTokenizerLogitSmoke`.

Status: `Complete / IndependentlyValidated / ForwardPathOnly`.

The committed RGS runner loaded the cached Qwen2.5-0.5B-Instruct-4bit model
once and performed 12 offline forward passes using the model's real chat
tokenizer and real MLX output logits. The frozen panel was eight direct
`v40r2-fit-00` task-A cases plus one positive protected case from each of four
rungs.

Artifact:
`astral-rgs-v40r2-real-logit-smoke-7ff4abf93f4e-r1`.

Bindings and validation:

- RGS commit: `7ff4abf93f4e9d313eb0fa5b0ed625d8974c8674`;
- R3 probe file SHA-256:
  `97e7ebe81c9faef3e92fe0b04e62143ddaa1151ce55b484f6b6206707d4831b9`;
- checkpoint inventory:
  `sha256:0a321941ffa31f920284c932f98bd4dba7c7cb95acd797c01ec2fa0fdd1321ab`;
- tokenizer inventory:
  `sha256:43c4bf51c8db8d03b43a5c2b3d1c44adf886d12fe3eba979b9d41f6101d10f5b`;
- sealed result:
  `sha256:2dd1b7ee0688adcb60256518fc525b5fbf6dc4f7120f7248c0393c3e0747a858`;
- independent validator: `valid: true`, zero errors.

The untouched model scored `1/8` (`0.125`) on the fit direct cases and `4/4`
(`1.0`) on the positive protected cases. This is a small diagnostic panel:
the fit value is not an acquisition estimate and the protected value is not a
retention result. The result verifies only the real
tokenizer-to-candidate-logit plumbing.

No optimizer, adapter, gradient step, tune access, assessment access, retry,
or scientific-state promotion occurred. The claim ceiling is
`LocalForwardOnlyRealTokenizerLogitSmokeV40R2`. Acquisition, retention,
continual learning, routing advantage, introspection, and self-modeling remain
unvalidated.
