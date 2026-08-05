"""V41R28 local surrogate acquisition-gate characterization runner.

State slice: V41R28LocalSurrogateAcquisitionGateCharacterization.

Mirrors the frozen V41R27 worker semantics (instruments, schedule, A-GEM
projection algebra, gates, thresholds) on a local MLX 4-bit substrate. The
substrate, tokenizer, LoRA target naming, and dtypes are declared surrogate
variables per the V41R28 preregistration; everything else is locked to the
V41R27 contract. No model is touched unless --execute is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V41R27_TOOL = ROOT / "tools" / "astral-v41r27-agem-retention" / "validate.py"
PREREGISTRATION = (ROOT / "docs" / "research" / "astral-self-modeling" /
                   "266-v41r28-local-surrogate-acquisition-gate-preregistration.md")

MARGIN_FLOOR = 2.0
LOSS_RATIO_MAXIMUM = 0.10
STEPS_PER_CASE = 64
PROTECTED_COUNT = 256
ACQUISITION_WEIGHT = 0.75
PROTECTED_WEIGHT = 0.25
LEARNING_RATE = 2.0e-4
OPTIMIZER_STEPS = 256
LORA_RANK = 8
LORA_ALPHA = 16
GRADIENT_CLIP = 1.0
PROJECTION_ROUNDOFF_FACTOR = 64.0
PROTECTED_ACCURACY_MINIMUM = 0.98
WALL_CLOCK_LIMIT_SECONDS = 25 * 60

SUBSTRATES = {
    "llama-3.2-1b": {
        "path": str(Path.home() / ".lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit"),
        "model_safetensors_sha256": "35e396644bca888eec399f9c0f843ec7fa78b8f8c5e06841661be62b4edf96dd",
        "tokenizer_json_sha256": "6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b",
    },
    "qwen2.5-0.5b": {
        "path": str(Path.home() / ".lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"),
        "model_safetensors_sha256": "ddffab9cbc7bf6dde941c6724841eeca8981fcfa81ca20ff8efff1396326d153",
        "tokenizer_json_sha256": "a8506e7111b80c6d8635951a02eab0f4e1a8e4e5772da83846579e97b16f61bf",
    },
}

CLAIM_CEILING = "LocalSurrogateAcquisitionGateCharacterizationV41R28"
STATE_SLICE = "V41R28LocalSurrogateAcquisitionGateCharacterization"
VERSION = "astral.v41r28_local_surrogate_runner.v1"


def _load_v41r27() -> Any:
    spec = importlib.util.spec_from_file_location("v41r27_validate", V41R27_TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V41R27 = _load_v41r27()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_contract_sha256() -> str:
    return V41R27.expected_contract()["contract_sha256"]


def acquisition_cases() -> list[dict[str, Any]]:
    return V41R27.acquisition()["cases"]


def protected_rows() -> list[dict[str, Any]]:
    return V41R27.protected()["rows"]


def run_spec(run_id: str) -> dict[str, Any]:
    cases = acquisition_cases()
    protected = protected_rows()
    panels = {}
    for panel in range(16):
        panel_id = f"v41r27-panel-{panel}"
        panels[panel_id] = {
            "panel_id": panel_id,
            "acquisition_indices": list(range(panel * 4, panel * 4 + 4)),
            "acquisition_case_ids": [c["case_id"] for c in cases[panel * 4:panel * 4 + 4]],
            "protected_indices": list(range(panel * 16, panel * 16 + 16)),
            "protected_case_ids": [r["case_id"] for r in protected[panel * 16:panel * 16 + 16]],
        }
    for seed in (412003, 412007, 412019):
        for panel_id, panel in panels.items():
            candidate = f"{panel_id}-seed-{seed}"
            if candidate == run_id:
                return {"run_id": candidate, "panel_id": panel_id, "seed": seed,
                        "contract_sha256": frozen_contract_sha256(),
                        "acquisition_case_ids": list(panel["acquisition_case_ids"]),
                        "protected_case_ids": list(panel["protected_case_ids"])}
    raise ValueError(f"V41R28 unknown run id: {run_id}")


def projection_roundoff_tolerance(projected_norm_sq: float, protected_norm_sq: float,
                                  dtype_epsilon: float) -> float:
    values = (projected_norm_sq, protected_norm_sq, dtype_epsilon)
    if any(not math.isfinite(value) for value in values):
        raise ValueError("V41R28 nonfinite projection tolerance")
    if projected_norm_sq < 0.0 or protected_norm_sq < 0.0 or dtype_epsilon <= 0.0:
        raise ValueError("V41R28 invalid projection tolerance")
    scale = math.sqrt(projected_norm_sq * protected_norm_sq)
    return PROJECTION_ROUNDOFF_FACTOR * dtype_epsilon * max(scale, 1.0)


def case_gate(score: dict[str, Any], receipts: list[dict[str, Any]], reload_exact: bool) -> dict[str, Any]:
    if len(receipts) != STEPS_PER_CASE:
        raise ValueError("V41R28 receipt census")
    first = sum(row["acquisition_loss"] for row in receipts[:8]) / 8
    last = sum(row["acquisition_loss"] for row in receipts[-8:]) / 8
    ratio = last / first if first > 0 else math.inf
    scores, target = score["candidate_log_probabilities"], score["target"]
    margin = float(scores[target]) - max(float(value) for key, value in scores.items() if key != target)
    errors = []
    if score.get("correct") is not True:
        errors.append("selected_target")
    if margin < MARGIN_FLOOR:
        errors.append("target_margin")
    if ratio > LOSS_RATIO_MAXIMUM:
        errors.append("loss_ratio")
    if reload_exact is not True:
        errors.append("reload_exact")
    return {"pass": not errors, "errors": errors, "target_margin_nats": margin,
            "first8_mean_acquisition_loss": first, "last8_mean_acquisition_loss": last,
            "last8_to_first8_acquisition_loss_ratio": ratio}


def message_tokens(tokenizer: Any, prompt: str, answer: str | None = None) -> list[int]:
    messages = [{"role": "user", "content": prompt}]
    if answer is not None:
        messages.append({"role": "assistant", "content": answer})
    return [int(token) for token in tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=answer is None)]


def trainable_inventory(model: Any, mx: Any) -> list[dict[str, Any]]:
    import numpy as np
    from mlx.utils import tree_flatten
    inventory = []
    pairs = sorted(tree_flatten(model.trainable_parameters()), key=lambda item: item[0])
    for path, array in pairs:
        if array is None:
            continue
        raw = np.asarray(array).tobytes()
        inventory.append({"name": path, "shape": list(array.shape), "dtype": str(array.dtype),
                          "sha256": hashlib.sha256(raw).hexdigest()})
    if not inventory:
        raise ValueError("V41R28 surrogate has no trainable parameters")
    return inventory


def trainable_state_sha256(model: Any, mx: Any) -> str:
    return canonical_hash(trainable_inventory(model, mx))


def _linear_dims(base: Any) -> tuple[int, int]:
    if hasattr(base, "dims"):
        dims = base.dims
        return int(dims[0]), int(dims[1])
    scales = base.scales
    output_dims = int(scales.shape[0])
    input_dims = int(scales.shape[1]) * int(base.group_size)
    return input_dims, output_dims


def attach_lora(model: Any, mx: Any, nn: Any) -> tuple[Any, list[str]]:
    class LoRALinear(nn.Module):
        def __init__(self, base: Any, rank: int, alpha: int):
            super().__init__()
            self.base = base
            input_dims, output_dims = _linear_dims(base)
            self.lora_a = (mx.random.normal((rank, input_dims)) * (1.0 / math.sqrt(input_dims)))
            self.lora_b = mx.zeros((output_dims, rank))
            self.scale = alpha / rank

        def __call__(self, x: Any) -> Any:
            return self.base(x) + ((x @ self.lora_a.T) @ self.lora_b.T) * self.scale

    inventory = []
    model.freeze(recurse=True)
    for layer_index, layer in enumerate(model.layers):
        attention = layer.self_attn
        for name in ("q_proj", "k_proj", "v_proj", "o_proj"):
            base = getattr(attention, name)
            wrapped = LoRALinear(base, LORA_RANK, LORA_ALPHA)
            setattr(attention, name, wrapped)
            wrapped.unfreeze(recurse=False)
            inventory.append(f"layers.{layer_index}.self_attn.{name}")
    return model, inventory


def forward_logits(model: Any, mx: Any, inputs: Any) -> Any:
    output = model(inputs)
    return output.logits if hasattr(output, "logits") else output


def candidate_log_probabilities(model: Any, tokenizer: Any, mx: Any, prompt: str,
                                candidates: list[str]) -> dict[str, float]:
    prompt_tokens = message_tokens(tokenizer, prompt)
    values = []
    for candidate in candidates:
        full = message_tokens(tokenizer, prompt, candidate)
        if full[:len(prompt_tokens)] != prompt_tokens:
            raise ValueError("V41R28 candidate prefix mismatch")
        inputs = mx.array([full])
        logits = forward_logits(model, mx, inputs)[0, :-1].astype(mx.float32)
        targets = mx.array(full[1:])
        start = len(prompt_tokens) - 1
        log_probs = logits[start:] - mx.logsumexp(logits[start:], axis=-1, keepdims=True)
        value = float(mx.sum(mx.take_along_axis(log_probs, targets[start:, None], axis=-1)).item())
        if not math.isfinite(value):
            raise ValueError("V41R28 candidate log probability nonfinite")
        values.append(value)
    maximum = max(values)
    normalizer = maximum + math.log(sum(math.exp(value - maximum) for value in values))
    return {candidate: value - normalizer for candidate, value in zip(candidates, values, strict=True)}


def score_rows(model: Any, tokenizer: Any, mx: Any, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    receipts = []
    for row in rows:
        scores = candidate_log_probabilities(model, tokenizer, mx, row["prompt"], row["candidates"])
        selected = min(row["candidates"], key=lambda candidate: (-scores[candidate], candidate))
        receipts.append({"case_id": row["case_id"], "target": row["target"],
                         "candidates": row["candidates"], "candidate_log_probabilities": scores,
                         "selected": selected, "correct": selected == row["target"]})
    return receipts


def accuracy(rows: list[dict[str, Any]]) -> float:
    if len(rows) != 16:
        raise ValueError("V41R28 protected census")
    return sum(row.get("correct") is True for row in rows) / 16


def training_row(case: dict[str, Any]) -> dict[str, str]:
    return {"prompt": case["composition_prompt"], "answer": case["target"]}


def protected_training_row(row: dict[str, Any]) -> dict[str, str]:
    return {"prompt": row["prompt"], "answer": row["target"]}


def collate(tokenizer: Any, mx: Any, rows: list[dict[str, str]]) -> tuple[Any, Any]:
    prompt_rows = [message_tokens(tokenizer, row["prompt"]) for row in rows]
    full_rows = [message_tokens(tokenizer, row["prompt"], row["answer"]) for row in rows]
    if any(full[:len(prompt)] != prompt for prompt, full in zip(prompt_rows, full_rows)):
        raise ValueError("V41R28 training prefix mismatch")
    width = max(len(row) for row in full_rows)
    pad = getattr(tokenizer, "pad_token_id", None)
    if pad is None:
        pad = tokenizer.eos_token_id
    inputs, labels = [], []
    for prompt, full in zip(prompt_rows, full_rows, strict=True):
        padding = [pad] * (width - len(full))
        inputs.append(full + padding)
        labels.append([-100] * len(prompt) + full[len(prompt):] + [-100] * len(padding))
    return mx.array(inputs), mx.array(labels)


def cross_entropy(model: Any, mx: Any, inputs: Any, labels: Any) -> Any:
    logits = forward_logits(model, mx, inputs)[:, :-1].astype(mx.float32)
    targets = labels[:, 1:]
    log_probs = logits - mx.logsumexp(logits, axis=-1, keepdims=True)
    gathered = mx.take_along_axis(log_probs, mx.maximum(targets, 0)[:, :, None], axis=-1)[:, :, 0]
    mask = (targets != -100).astype(mx.float32)
    masked = mx.where(targets == -100, mx.array(0.0), gathered)
    total = mx.sum(masked * mask)
    count = mx.sum(mask)
    return -total / count


def flatten_gradients(grads: Any) -> tuple[list[str], list[Any]]:
    from mlx.utils import tree_flatten
    pairs = sorted(tree_flatten(grads), key=lambda item: item[0])
    pairs = [(path, array) for path, array in pairs if array is not None]
    return [path for path, _ in pairs], [array for _, array in pairs]


def project_and_combine(mx: Any, paths: list[str], acquisition: list[Any], protected_: list[Any],
                        dtype_epsilon: float) -> tuple[list[Any], dict[str, float]]:
    import numpy as np
    a = [np.asarray(array, dtype=np.float64) for array in acquisition]
    p = [np.asarray(array, dtype=np.float64) for array in protected_]
    dot = float(sum(float(np.sum(ai * pi)) for ai, pi in zip(a, p)))
    norm_sq = float(sum(float(np.sum(pi * pi)) for pi in p))
    if not math.isfinite(dot) or not math.isfinite(norm_sq):
        raise ValueError("V41R28 gradient geometry")
    applied = dot < 0.0
    if applied:
        if norm_sq <= 0.0:
            raise ValueError("V41R28 zero protected gradient")
        coefficient = dot / norm_sq
        projected = [ai - coefficient * pi for ai, pi in zip(a, p)]
    else:
        coefficient = 0.0
        projected = list(a)
    post_dot = float(sum(float(np.sum(pi_j * pj)) for pi_j, pj in zip(projected, p)))
    projected_norm_sq = float(sum(float(np.sum(pi_j * pi_j)) for pi_j in projected))
    if not math.isfinite(post_dot) or not math.isfinite(projected_norm_sq):
        raise ValueError("V41R28 projection geometry")
    tolerance = projection_roundoff_tolerance(projected_norm_sq, norm_sq, dtype_epsilon)
    if post_dot < -tolerance:
        raise ValueError("V41R28 projection invariant")
    combined = [ACQUISITION_WEIGHT * pi_j + PROTECTED_WEIGHT * pj for pi_j, pj in zip(projected, p)]
    geometry = {"pre_projection_dot": dot, "post_projection_dot": post_dot,
                "projected_gradient_norm_sq": projected_norm_sq,
                "protected_gradient_norm_sq": norm_sq,
                "projection_dtype_epsilon": dtype_epsilon,
                "projection_roundoff_tolerance": tolerance,
                "projection_coefficient": coefficient, "projection_applied": applied}
    return [mx.array(pi_j.astype(np.float32)) for pi_j in combined], geometry


def clip_and_update(mx: Any, nn: Any, model: Any, optimizer: Any, paths: list[str],
                    combined: list[Any]) -> float:
    import numpy as np
    total = float(sum(float(np.sum(np.asarray(array, dtype=np.float64) ** 2)) for array in combined))
    norm = math.sqrt(total)
    scale = min(1.0, GRADIENT_CLIP / norm) if norm > 0 else 1.0
    from mlx.utils import tree_unflatten
    clipped = tree_unflatten([(path, array * scale) for path, array in zip(paths, combined, strict=True)])
    optimizer.update(model, clipped)
    mx.eval(model.parameters(), optimizer.state)
    return norm


def serialize_lora(model: Any, mx: Any) -> tuple[dict[str, Any], str]:
    from mlx.utils import tree_flatten
    state = {}
    pairs = sorted(tree_flatten(model.trainable_parameters()), key=lambda item: item[0])
    for path, array in pairs:
        if array is None:
            continue
        mx.eval(array)
        state[path] = array
    return state, trainable_state_sha256(model, mx)


def restore_lora(model: Any, mx: Any, state: dict[str, Any]) -> None:
    from mlx.utils import tree_flatten, tree_unflatten
    current = {path: array for path, array in tree_flatten(model.trainable_parameters())
               if array is not None}
    if set(current) != set(state):
        raise ValueError("V41R28 reload inventory")
    for path, array in state.items():
        if list(current[path].shape) != list(array.shape):
            raise ValueError("V41R28 reload shape")
    updates = tree_unflatten([(path, state[path]) for path in sorted(state)])
    model.update(updates)
    mx.eval(model.parameters())


def preflight(base_model: Any, tokenizer: Any, mx: Any, panel_index: int) -> dict[str, Any]:
    cases = acquisition_cases()
    protected = protected_rows()
    selected = cases[panel_index * 4:panel_index * 4 + 4]
    panel_protected = protected[panel_index * 16:panel_index * 16 + 16]
    protected_before = score_rows(base_model, tokenizer, mx, panel_protected)
    protected_accuracy = accuracy(protected_before)
    exact_rows = [{"case_id": case["case_id"], "prompt": case["composition_prompt"],
                   "target": case["target"], "candidates": list(case["candidates"])} for case in selected]
    exact_before = score_rows(base_model, tokenizer, mx, exact_rows)
    incorrect = sum(row.get("correct") is not True for row in exact_before)
    return {"protected_accuracy": protected_accuracy, "incorrect_acquisition_cases": incorrect,
            "protected_before_rows": protected_before, "exact_before_rows": exact_before}


def write_result(output: Path, result: dict[str, Any]) -> None:
    result_path = output / "worker-result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    manifest_lines = [f'{sha256_file(result_path)}  {result_path.name}']
    for name in ("worker-adapter-state.safetensors",):
        adapter_path = output / name
        if adapter_path.exists():
            manifest_lines.append(f'{sha256_file(adapter_path)}  {name}')
    (output / "MANIFEST.sha256").write_text("".join(line + "\n" for line in manifest_lines))


def run_cell(substrate_key: str, run_id: str, output: Path) -> dict[str, Any]:
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as mx_optimizers
    from mlx_lm import load as mlx_load

    spec = run_spec(run_id)
    panel_index = int(spec["panel_id"].rsplit("-", 1)[1])
    seed = int(spec["seed"])
    substrate = SUBSTRATES[substrate_key]
    for name, expected in (("model.safetensors", substrate["model_safetensors_sha256"]),
                           ("tokenizer.json", substrate["tokenizer_json_sha256"])):
        actual = sha256_file(Path(substrate["path"]) / name)
        if actual != expected:
            raise RuntimeError(f"V41R28 substrate pin mismatch for {name}")
    started = time.monotonic()
    failure = {"version": VERSION, "state_slice": STATE_SLICE,
               "classification": "V41R28SurrogateRuntimeIncomplete",
               "run_id": run_id, "substrate": substrate_key,
               "tune_opened": False, "assessment_opened": False}

    def deadline() -> None:
        if time.monotonic() - started > WALL_CLOCK_LIMIT_SECONDS:
            raise TimeoutError("V41R28 surrogate wall clock limit")

    try:
        mx.random.seed(seed)
        model, tokenizer = mlx_load(substrate["path"])
        pre = preflight(model, tokenizer, mx, panel_index)
        if pre["protected_accuracy"] != 1.0:
            blocked = {**failure, "classification": "V41R28SurrogatePreflightBlocked",
                       "reason": "protected_accuracy_below_1.0",
                       "preflight": {"protected_accuracy": pre["protected_accuracy"],
                                     "incorrect_acquisition_cases": pre["incorrect_acquisition_cases"]},
                       "elapsed_seconds": time.monotonic() - started}
            output.mkdir(parents=True, exist_ok=False)
            (output / "preflight-blocked.json").write_text(
                json.dumps(blocked, indent=2, sort_keys=True, allow_nan=False) + "\n")
            return blocked
        if pre["incorrect_acquisition_cases"] < 3:
            blocked = {**failure, "classification": "V41R28SurrogatePreflightBlocked",
                       "reason": "acquisition_novelty_below_3",
                       "preflight": {"protected_accuracy": pre["protected_accuracy"],
                                     "incorrect_acquisition_cases": pre["incorrect_acquisition_cases"]},
                       "elapsed_seconds": time.monotonic() - started}
            output.mkdir(parents=True, exist_ok=False)
            (output / "preflight-blocked.json").write_text(
                json.dumps(blocked, indent=2, sort_keys=True, allow_nan=False) + "\n")
            return blocked

        mx.random.seed(seed)
        model, lora_inventory = attach_lora(model, mx, nn)
        initial_hash = trainable_state_sha256(model, mx)
        optimizer = mx_optimizers.AdamW(learning_rate=LEARNING_RATE)
        dtype_epsilon = float(np_finfo_eps())

        cases = acquisition_cases()
        protected = protected_rows()
        selected = cases[panel_index * 4:panel_index * 4 + 4]
        panel_protected = protected[panel_index * 16:panel_index * 16 + 16]

        acquisition_batches = {}
        for index in range(panel_index * 4, panel_index * 4 + 4):
            inputs, labels = collate(tokenizer, mx, [training_row(cases[index])] * 4)
            acquisition_batches[index] = (inputs, labels)
        protected_batches = {}
        for offset in range(4):
            local_indices = [(offset * 4 + j) % PROTECTED_COUNT for j in range(4)]
            indices = [panel_index * 16 + index for index in local_indices]
            inputs, labels = collate(tokenizer, mx,
                                     [protected_training_row(panel_protected[index]) for index in local_indices])
            protected_batches[offset] = (indices, inputs, labels)

        loss_and_grad = nn.value_and_grad(model, lambda m, inputs, labels: cross_entropy(m, mx, inputs, labels))
        schedule = [index for _ in range(64) for index in range(panel_index * 4, panel_index * 4 + 4)]
        receipts = []
        for step, index in enumerate(schedule):
            deadline()
            if step % 64 == 0:
                print(f"cell={run_id} substrate={substrate_key} step={step}/256", flush=True)
            a_inputs, a_labels = acquisition_batches[index]
            p_indices, p_inputs, p_labels = protected_batches[step % 4]
            a_loss_value, a_grads = loss_and_grad(model, a_inputs, a_labels)
            p_loss_value, p_grads = loss_and_grad(model, p_inputs, p_labels)
            a_paths, a_arrays = flatten_gradients(a_grads)
            p_paths, p_arrays = flatten_gradients(p_grads)
            if a_paths != p_paths:
                raise RuntimeError("V41R28 gradient tree mismatch")
            combined, geometry = project_and_combine(mx, a_paths, a_arrays, p_arrays, dtype_epsilon)
            gradient_norm = clip_and_update(mx, nn, model, optimizer, a_paths, combined)
            a_loss, p_loss = float(a_loss_value.item()), float(p_loss_value.item())
            if not math.isfinite(a_loss) or not math.isfinite(p_loss):
                raise RuntimeError("V41R28 loss nonfinite")
            receipts.append({"step": step, "case_index": index, "case_id": cases[index]["case_id"],
                             "protected_indices": p_indices, "acquisition_examples": 4,
                             "protected_examples": 4, "acquisition_loss": a_loss, "protected_loss": p_loss,
                             "weighted_loss": ACQUISITION_WEIGHT * a_loss + PROTECTED_WEIGHT * p_loss,
                             "projection_applied": geometry["projection_applied"],
                             "pre_projection_dot": geometry["pre_projection_dot"],
                             "post_projection_dot": geometry["post_projection_dot"],
                             "projected_gradient_norm_sq": geometry["projected_gradient_norm_sq"],
                             "protected_gradient_norm_sq": geometry["protected_gradient_norm_sq"],
                             "projection_dtype_epsilon": geometry["projection_dtype_epsilon"],
                             "projection_roundoff_tolerance": geometry["projection_roundoff_tolerance"],
                             "projection_coefficient": geometry["projection_coefficient"],
                             "gradient_norm": gradient_norm})

        post_hash = trainable_state_sha256(model, mx)
        state, adapter_sha_state = serialize_lora(model, mx)
        output.mkdir(parents=True, exist_ok=False)
        mx.save_safetensors(str(output / "worker-adapter-state.safetensors"),
                            {path: array for path, array in state.items()})

        reloaded, _ = mlx_load(substrate["path"])
        reloaded, _ = attach_lora(reloaded, mx, nn)
        restore_lora(reloaded, mx, state)
        reload_hash = trainable_state_sha256(reloaded, mx)
        reload_exact = reload_hash == post_hash
        if not reload_exact:
            raise RuntimeError("V41R28 reload mismatch")

        exact_rows = [{"case_id": case["case_id"], "prompt": case["composition_prompt"],
                       "target": case["target"], "candidates": list(case["candidates"])} for case in selected]
        exact_after = score_rows(reloaded, tokenizer, mx, exact_rows)
        protected_after = score_rows(reloaded, tokenizer, mx, panel_protected)
        candidate = {
            "cases": {case["case_id"]: {"exact_after": exact_after[position],
                                        "receipts": [row for row in receipts if row["case_id"] == case["case_id"]]}
                      for position, case in enumerate(selected)},
            "exact_after_rows": exact_after,
            "protected_before": {"accuracy": pre["protected_accuracy"], "rows": pre["protected_before_rows"]},
            "protected_after": {"accuracy": accuracy(protected_after), "rows": protected_after},
            "update": {"optimizer_steps": len(receipts), "acquisition_examples": len(receipts) * 4,
                       "protected_examples": len(receipts) * 4, "receipts": receipts,
                       "projection_steps": sum(row["projection_applied"] is True for row in receipts),
                       "initial_state_sha256": initial_hash, "post_update_state_sha256": post_hash,
                       "adapter_file": "worker-adapter-state.safetensors",
                       "adapter_file_sha256": sha256_file(output / "worker-adapter-state.safetensors")},
            "reload": {"fresh_base_model": True, "state_sha256": reload_hash, "state_exact": reload_exact},
        }
        gates = {case_id: case_gate(packet["exact_after"], packet["receipts"], reload_exact)
                 for case_id, packet in candidate["cases"].items()}
        passing = sum(gate["pass"] for gate in gates.values())
        protected_accuracy = candidate["protected_after"]["accuracy"]
        worker_pass = passing == 4 and protected_accuracy >= PROTECTED_ACCURACY_MINIMUM and reload_exact
        decision = {"classification": "V41R28SurrogateWorkerComplete", "status": "completed",
                    "pass": worker_pass, "acquisition_cases_passing": passing, "case_gates": gates,
                    "protected_accuracy": protected_accuracy,
                    "protected_drop": pre["protected_accuracy"] - protected_accuracy,
                    "fresh_adapter": True, "fresh_optimizer": True, "optimizer_steps": OPTIMIZER_STEPS,
                    "governance_violations": 0,
                    "preflight": {"protected_accuracy": pre["protected_accuracy"],
                                  "incorrect_acquisition_cases": pre["incorrect_acquisition_cases"],
                                  "pass": True}}
        import importlib.metadata
        body = {"version": VERSION, "state_slice": STATE_SLICE, **decision,
                "source": {"rgs_contract_sha256": frozen_contract_sha256(),
                           "runner_sha256": sha256_file(Path(__file__)),
                           "preregistration_sha256": sha256_file(PREREGISTRATION),
                           "v41r27_tool_sha256": sha256_file(V41R27_TOOL)},
                "run_spec": spec, "run_id": run_id, "seed": seed,
                "substrate": {"key": substrate_key, "path": substrate["path"],
                              "model_safetensors_sha256": substrate["model_safetensors_sha256"],
                              "tokenizer_json_sha256": substrate["tokenizer_json_sha256"]},
                "surrogate_variables": ["substrate", "tokenizer", "lora_target_naming", "dtype_and_kernels"],
                "lora": {"rank": LORA_RANK, "alpha": LORA_ALPHA,
                         "targets": "q_proj,k_proj,v_proj,o_proj_all_layers",
                         "inventory": lora_inventory},
                "case_ids": [case["case_id"] for case in selected],
                "exact_score_rows": exact_rows, "exact_before_rows": pre["exact_before_rows"],
                "candidate": candidate,
                "runtime": {"python": platform.python_version(),
                            "mlx": importlib.metadata.version("mlx"),
                            "mlx_lm": importlib.metadata.version("mlx-lm"),
                            "platform": platform.platform()},
                "claim_ceiling": CLAIM_CEILING, "tune_opened": False, "assessment_opened": False,
                "elapsed_seconds": time.monotonic() - started}
        result = {**body, "result_sha256": canonical_hash(body)}
        write_result(output, result)
        return result
    except BaseException as error:
        failure.update({"error_type": type(error).__name__, "error": str(error),
                        "elapsed_seconds": time.monotonic() - started})
        output.mkdir(parents=True, exist_ok=True)
        (output / "failure-result.json").write_text(
            json.dumps(failure, indent=2, sort_keys=True) + "\n")
        (output / "INCOMPLETE").write_text("consumed V41R28 failure\n")
        raise


def np_finfo_eps() -> float:
    import numpy as np
    return float(np.finfo(np.float32).eps)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--substrate", required=True, choices=sorted(SUBSTRATES))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        return 0
    result = run_cell(args.substrate, args.run_id, args.output.resolve())
    print(json.dumps({"classification": result["classification"], "run_id": result.get("run_id"),
                      "substrate": args.substrate,
                      "protected_accuracy": result.get("protected_accuracy"),
                      "pass": result.get("pass"), "output": str(args.output)}))
    return 0 if (result.get("pass") is True or result.get("classification") == "V41R28SurrogatePreflightBlocked") else 2


if __name__ == "__main__":
    raise SystemExit(main())
