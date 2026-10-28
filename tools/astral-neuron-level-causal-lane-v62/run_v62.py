"""V62 runner: V61-local pipeline unchanged, one arm = (device, dtype). Protocol doc 202.
Slices: astral-neuron-level-causal-lane-v62-execution, instrument-validity-gate-v3."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "astral-neuron-level-causal-lane-v61-local"))
import run_v61_local as r61
import v60

ARMS = {"mps_f32": ("mps", "bf16", True), "cpu_f32": ("cpu", "bf16", True),
        "mps_bf16": ("mps", "bf16", False), "mps_fp16": ("mps", "fp16", False)}


def main(arm, argv):
    device, load, to_float = ARMS[arm]
    import torch, transformers
    orig = transformers.AutoModelForCausalLM.from_pretrained
    dt = {"bf16": torch.bfloat16, "fp16": torch.float16}[load]

    def patched(*a, **k):
        k["torch_dtype"] = dt
        return orig(*a, **k)
    transformers.AutoModelForCausalLM.from_pretrained = patched

    def factory(model_dir, items, layers):
        b = v60.make_backend_class()(model_dir, items, layers, device=device)
        if to_float:
            b.m.float()
        return b
    res = r61.main(argv, backend_factory=factory)
    return res


if __name__ == "__main__":
    arm = sys.argv[1]
    main(arm, sys.argv[2:])
