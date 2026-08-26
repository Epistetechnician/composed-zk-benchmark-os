# V22 local model/runtime execution protocol

State slice: `continual-learning-runtime-execution-v22`  
Claim ceiling: `LocalDevelopmentRuntimeExecution`

V22 promotes the cached Qwen2.5-0.5B-Instruct-4bit checkpoint into a bounded,
offline runtime seam. `runtime_seam.py` loads the model through the existing
MLX `ChoiceModel`, performs one single-token four-label probe, records runtime
and model-manifest digests, binds a tokenizer policy derived from the local
`config.json` model type, and writes only to a repository-external output
root. `validate_runtime_receipt.py` independently checks the receipt digests,
model binding, label panel, and explicit `network_access=false` and
`training=false` controls.

The policy is inert for Qwen and Llama model types. For `nemotron_h`, it sets
Transformers' `fix_mistral_regex=true` option for both `ChoiceModel` readout
and the opt-in `safe_mlx_lora.py` training entrypoint. Historical protocol
commands retain the original `mlx_lm lora` invocation; candidate work must
choose `safe_training_command()` explicitly and record the resulting policy
line. This prevents a model-specific tokenizer repair from silently changing
prior experiment semantics.

`training_seam_smoke.py` is the bounded executable check for that opt-in path.
It trains one LoRA layer for exactly two iterations on four synthetic label
rows, performs one adapter-bound readout, and emits digest-bound config,
dataset, log, adapter, and receipt files outside the repository.
`validate_training_seam_receipt.py` independently checks those files and the
cached model's `config.json`. The smoke establishes tokenizer-corrected local
training compatibility only; it does not establish acquisition, retention,
continual learning, model quality, provider delivery, or production readiness.

Run:

```text
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
PYTHONDONTWRITEBYTECODE=1 python experiments/continual_learning/runtime_seam.py \
  --output /tmp/continual-learning-runtime-v22-smoke
PYTHONDONTWRITEBYTECODE=1 python experiments/continual_learning/validate_runtime_receipt.py \
  /tmp/continual-learning-runtime-v22-smoke \
  --model /Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit
```

The cached checkpoint must already exist. With `--model`, readback independently
re-hashes every regular checkpoint file and rejects missing, extra, unsafe, or
drifted files. The protocol performs no download, does not retain the prompt
text in the receipt, and does not claim learning, production serving, provider
behavior, scientific evidence, or benchmark evidence.
