"""Local BillSum model-update qualification; never uses a paid provider.

State slice: ``aligned-rsi-local-billsum-adaptation-internal-v1``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping


STATE_SLICE = "aligned-rsi-local-billsum-adaptation-internal-v1"
PROTOCOL_ID = "aligned-rsi-local-billsum-adaptation-v1"
CLAIM_CEILING = "LocalDevelopmentBillSumAdaptiveCurriculumQualificationV1"
MODEL_ID = "Qwen/Qwen3-0.6B"
MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
DATASET_ID = "FiscalNote/billsum"
DATASET_REVISION = "3d8510441c06a3d9dfb32eb0d7f80151730bcc4f"
DATA_FILES = (
    "data/train-00000-of-00001.parquet",
    "data/test-00000-of-00001.parquet",
)
FIT_POOL_SIZE = 512
ARM_EXAMPLES = 128
ASSESSMENT_SIZE = 128
SEEDS = (17, 29, 43)
MAX_SOURCE_TOKENS = 384
MAX_TARGET_TOKENS = 128
MAX_NEW_TOKENS = 128
LORA_RANK = 8
LORA_ALPHA = 16
LEARNING_RATE = 1e-4
LAYER_INDEX = 13
MECHANISTIC_ROWS = 16
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261006
MIN_EFFECT = 0.02
IDENTITY_PATCH_TOLERANCE = 1e-5
WALL_CLOCK_LIMIT_SECONDS = 180 * 60

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = REPO_ROOT / "docs/research/continual-learning/312-aligned-rsi-local-billsum-adaptation-v1.md"
MANIFEST_PATH = Path(__file__).with_name("aligned_rsi_local_billsum_v1.json")
OWNER_ROOT = Path.home() / ".local/share/aligned-rsi-local-billsum-adaptation-v1"
MODEL_ROOT = OWNER_ROOT / "inputs/model"
DATASET_ROOT = OWNER_ROOT / "inputs/billsum"
PREPARED_PATH = OWNER_ROOT / "prepared_inputs.json"
RUNS_ROOT = OWNER_ROOT / "runs"
RELEASE_ROOT = REPO_ROOT / "release/aligned_rsi_local_billsum_v1"
PUBLIC_REPORT_PATH = RELEASE_ROOT / "evaluation_report.json"


class ExperimentError(ValueError):
    """Raised when the frozen local experiment contract is invalid."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ExperimentError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ExperimentError(f"non-standard JSON value: {token}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"cannot read JSON: {path}") from exc


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False).encode() + b"\n")
    temporary.replace(path)


def document_id(text: str, summary: str) -> str:
    return sha256_bytes(text.encode("utf-8") + b"\0" + summary.encode("utf-8"))


def tree_manifest(root: Path) -> list[dict[str, str]]:
    if not root.is_dir() or root.is_symlink():
        raise ExperimentError(f"expected regular directory: {root}")
    files: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".cache" in relative.parts:
            continue
        if path.is_symlink():
            raise ExperimentError(f"input tree contains symlink: {relative}")
        if path.is_file():
            files.append({"path": relative.as_posix(), "sha256": sha256_file(path)})
    if not files:
        raise ExperimentError(f"empty input tree: {root}")
    return files


def _tree_digest(files: list[dict[str, str]]) -> str:
    return sha256_bytes(canonical_bytes(files))


def _assert_private_root(root: Path, *, create: bool) -> None:
    if root.is_symlink():
        raise ExperimentError("custody root cannot be a symlink")
    if not root.exists():
        if not create:
            raise ExperimentError("custody root is missing")
        root.mkdir(parents=True, mode=0o700)
    root.chmod(0o700)
    mode = root.stat().st_mode & 0o777
    if mode != 0o700:
        raise ExperimentError("custody root must have mode 0700")
    if not root.is_dir():
        raise ExperimentError("custody root must be a directory")


def _secure_tree_directories(root: Path) -> None:
    """Keep every custody directory owner-only, including Hub-created paths."""
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_symlink():
            raise ExperimentError(f"custody tree contains symlink: {path.relative_to(root)}")
        if path.is_dir():
            path.chmod(0o700)
    root.chmod(0o700)


def _check_private_tree(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ExperimentError(f"custody root is not a regular directory: {root}")
    if root.stat().st_mode & 0o777 != 0o700:
        raise ExperimentError(f"custody root is not owner-only: {root.name}")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ExperimentError(f"custody tree contains symlink: {path.relative_to(root)}")
        if path.is_dir() and path.stat().st_mode & 0o777 != 0o700:
            raise ExperimentError(f"custody directory is not owner-only: {path.relative_to(root)}")


def _runtime_manifest() -> dict[str, str]:
    try:
        from importlib.metadata import version

        packages = {
            "python": ".".join(map(str, sys.version_info[:3])),
            "platform": f"{sys.platform}-{__import__('platform').machine()}",
            "torch": version("torch"),
            "transformers": version("transformers"),
            "datasets": version("datasets"),
            "huggingface-hub": version("huggingface-hub"),
            "safetensors": version("safetensors"),
            "numpy": version("numpy"),
            "pyarrow": version("pyarrow"),
        }
    except Exception as exc:
        raise ExperimentError("runtime package inventory unavailable") from exc
    expected = {
        "python": "3.14.5",
        "platform": "darwin-arm64",
        "torch": "2.13.0",
        "transformers": "5.14.1",
        "datasets": "5.0.1",
        "huggingface-hub": "1.27.0",
        "safetensors": "0.8.0",
        "numpy": "2.5.1",
        "pyarrow": "25.0.0",
    }
    if packages != expected:
        raise ExperimentError(f"runtime package versions differ from protocol: {packages}")
    return packages


def _verify_protocol() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    required = {
        "schema_version": "aligned-rsi-local-billsum-v1-protocol",
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "status": "LOCAL_EXECUTION_AUTHORIZED_BY_USER",
        "claim_ceiling": CLAIM_CEILING,
    }
    for key, expected in required.items():
        if manifest.get(key) != expected:
            raise ExperimentError(f"protocol manifest mismatch: {key}")
    if manifest.get("runtime") != _runtime_manifest():
        raise ExperimentError("runtime differs from frozen manifest")
    if manifest.get("independent_acceptance_requested") is not False:
        raise ExperimentError("independent acceptance must remain false")
    model = manifest.get("model", {})
    dataset = manifest.get("dataset", {})
    if (model.get("repo_id"), model.get("revision")) != (MODEL_ID, MODEL_REVISION):
        raise ExperimentError("model identity mismatch")
    if (dataset.get("repo_id"), dataset.get("revision")) != (DATASET_ID, DATASET_REVISION):
        raise ExperimentError("dataset identity mismatch")
    return manifest


def prepare() -> dict[str, Any]:
    """Download only the pinned public model and federal BillSum files."""
    _verify_protocol()
    _assert_private_root(OWNER_ROOT, create=True)
    for path in (MODEL_ROOT, DATASET_ROOT, RUNS_ROOT):
        if path.exists() and path.is_symlink():
            raise ExperimentError(f"custody path cannot be a symlink: {path.name}")
        path.mkdir(parents=True, mode=0o700, exist_ok=True)
        path.chmod(0o700)

    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "0"
    try:
        from huggingface_hub import HfApi, snapshot_download
    except ImportError as exc:
        raise ExperimentError("huggingface_hub is required for pinned input preparation") from exc

    api = HfApi(token=False)
    model_info = api.model_info(MODEL_ID, revision=MODEL_REVISION)
    data_info = api.dataset_info(DATASET_ID, revision=DATASET_REVISION)
    if model_info.sha != MODEL_REVISION:
        raise ExperimentError("model revision resolved to a different commit")
    if data_info.sha != DATASET_REVISION:
        raise ExperimentError("dataset revision resolved to a different commit")
    sibling_paths = {item.rfilename for item in data_info.siblings}
    if not set(DATA_FILES).issubset(sibling_paths):
        raise ExperimentError("pinned BillSum revision is missing required federal split files")

    snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=str(MODEL_ROOT),
        token=False,
    )
    snapshot_download(
        repo_id=DATASET_ID,
        repo_type="dataset",
        revision=DATASET_REVISION,
        local_dir=str(DATASET_ROOT),
        allow_patterns=["README.md", *DATA_FILES],
        token=False,
    )
    _secure_tree_directories(OWNER_ROOT)
    for relative in DATA_FILES:
        if not (DATASET_ROOT / relative).is_file():
            raise ExperimentError(f"pinned dataset file missing: {relative}")

    package_versions = _runtime_manifest()
    payload = {
        "schema_version": "aligned-rsi-local-billsum-v1-prepared-inputs",
        "state_slice": STATE_SLICE,
        "model_repo_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_files": tree_manifest(MODEL_ROOT),
        "dataset_repo_id": DATASET_ID,
        "dataset_revision": DATASET_REVISION,
        "dataset_files": tree_manifest(DATASET_ROOT),
        "included_dataset_files": list(DATA_FILES),
        "excluded_split": "ca_test",
        "runtime": package_versions,
    }
    payload["prepared_inputs_sha256"] = sha256_bytes(canonical_bytes(payload))
    save_json(PREPARED_PATH, payload)
    return {
        "prepared": True,
        "model_revision": MODEL_REVISION,
        "dataset_revision": DATASET_REVISION,
        "model_files": len(payload["model_files"]),
        "dataset_files": len(payload["dataset_files"]),
        "prepared_inputs_sha256": payload["prepared_inputs_sha256"],
    }


def _validate_prepared() -> dict[str, Any]:
    _assert_private_root(OWNER_ROOT, create=False)
    payload = load_json(PREPARED_PATH)
    digest = payload.get("prepared_inputs_sha256")
    unsigned = {key: value for key, value in payload.items() if key != "prepared_inputs_sha256"}
    if digest != sha256_bytes(canonical_bytes(unsigned)):
        raise ExperimentError("prepared input manifest digest mismatch")
    if payload.get("model_revision") != MODEL_REVISION or payload.get("dataset_revision") != DATASET_REVISION:
        raise ExperimentError("prepared input revision mismatch")
    if payload.get("model_files") != tree_manifest(MODEL_ROOT):
        raise ExperimentError("model file digest mismatch")
    if payload.get("dataset_files") != tree_manifest(DATASET_ROOT):
        raise ExperimentError("dataset file digest mismatch")
    expected_dataset_paths = sorted(["README.md", *DATA_FILES])
    if sorted(item["path"] for item in payload.get("dataset_files", [])) != expected_dataset_paths:
        raise ExperimentError("prepared dataset contains an unapproved file or split")
    if payload.get("included_dataset_files") != list(DATA_FILES) or payload.get("excluded_split") != "ca_test":
        raise ExperimentError("prepared dataset split boundary mismatch")
    _check_private_tree(OWNER_ROOT)
    _runtime_manifest()
    return payload


def _load_federal_rows(split: str) -> list[dict[str, str]]:
    if split not in {"train", "test"}:
        raise ExperimentError("only federal train/test splits may be read")
    file_name = f"data/{split}-00000-of-00001.parquet"
    path = DATASET_ROOT / file_name
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise ExperimentError("pyarrow is required to read the pinned Parquet files") from exc
    rows = parquet.read_table(path).to_pylist()
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        text = row.get("text")
        summary = row.get("summary")
        if not isinstance(text, str) or not text.strip() or not isinstance(summary, str) or not summary.strip():
            raise ExperimentError(f"missing federal {split} text or summary")
        identifier = document_id(text, summary)
        if identifier in seen:
            raise ExperimentError(f"duplicate document id in {split}: {identifier}")
        seen.add(identifier)
        result.append({"doc_id": identifier, "text": text, "summary": summary})
    return sorted(result, key=lambda row: row["doc_id"])


def _tokenize_rows(tokenizer: Any, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    encoded: list[dict[str, Any]] = []
    for row in rows:
        prompt = (
            "Summarize this United States federal bill concisely. Preserve its main purpose "
            "and key provisions without adding unsupported claims.\n\nBILL:\n"
            + row["text"]
            + "\n\nSUMMARY:\n"
        )
        prompt_ids = tokenizer(
            prompt,
            add_special_tokens=True,
            truncation=True,
            max_length=MAX_SOURCE_TOKENS,
        )["input_ids"]
        target_ids = tokenizer(row["summary"], add_special_tokens=False)["input_ids"][:MAX_TARGET_TOKENS]
        if tokenizer.eos_token_id is not None:
            target_ids = [*target_ids, tokenizer.eos_token_id]
        if not prompt_ids or not target_ids:
            raise ExperimentError(f"empty tokenized row: {row['doc_id']}")
        input_ids = [*prompt_ids, *target_ids]
        labels = [-100] * len(prompt_ids) + target_ids
        encoded.append(
            {
                "doc_id": row["doc_id"],
                "text": row["text"],
                "summary": row["summary"],
                "prompt_ids": prompt_ids,
                "target_ids": target_ids,
                "input_ids": input_ids,
                "labels": labels,
                "target_start": len(prompt_ids),
            }
        )
    return encoded


def _normal_tokens(text: str) -> list[str]:
    return re.findall(r"\w+|[^\w\s]", text.lower(), flags=re.UNICODE)


def rouge_l_f1(prediction: str, reference: str) -> float:
    predicted = _normal_tokens(prediction)
    expected = _normal_tokens(reference)
    if not predicted or not expected:
        return 0.0
    previous = [0] * (len(expected) + 1)
    for token in predicted:
        current = [0]
        for index, expected_token in enumerate(expected, start=1):
            if token == expected_token:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    overlap = previous[-1]
    precision = overlap / len(predicted)
    recall = overlap / len(expected)
    return (2 * precision * recall / (precision + recall)) if precision + recall else 0.0


def bootstrap_interval(values: list[float]) -> tuple[float, float]:
    if not values or any(not math.isfinite(value) for value in values):
        raise ExperimentError("bootstrap input is empty or non-finite")
    generator = random.Random(BOOTSTRAP_SEED)
    samples = sorted(
        sum(values[generator.randrange(len(values))] for _ in values) / len(values)
        for _ in range(BOOTSTRAP_RESAMPLES)
    )
    return samples[int(0.025 * len(samples))], samples[min(len(samples) - 1, int(0.975 * len(samples)))]


def _mean(values: list[float]) -> float:
    if not values or any(not math.isfinite(value) for value in values):
        raise ExperimentError("mean input is empty or non-finite")
    return sum(values) / len(values)


def _import_torch() -> tuple[Any, Any, Any]:
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as functional
    except ImportError as exc:
        raise ExperimentError("PyTorch is required for local adapter training") from exc
    if not torch.backends.mps.is_available():
        raise ExperimentError("Apple MPS is required by the frozen local packet")
    return torch, nn, functional


def _create_model_and_tokenizer(model_root: Path) -> tuple[Any, Any, list[Any], str]:
    torch, nn, functional = _import_torch()
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise ExperimentError("Transformers is required for local model execution") from exc
    tokenizer = AutoTokenizer.from_pretrained(model_root, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_root,
        local_files_only=True,
        trust_remote_code=False,
        dtype=torch.float16,
        attn_implementation="eager",
    )
    if not hasattr(model, "model") or not hasattr(model.model, "layers"):
        raise ExperimentError("unexpected Qwen3 decoder structure")
    if len(model.model.layers) <= LAYER_INDEX:
        raise ExperimentError("fixed mechanistic layer is outside the decoder")
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    class LoRALinear(nn.Module):
        def __init__(self, base: Any) -> None:
            super().__init__()
            self.base = base
            self.rank = LORA_RANK
            self.scale = LORA_ALPHA / LORA_RANK
            self.enabled = True
            self.lora_A = nn.Parameter(torch.empty((LORA_RANK, base.in_features), dtype=torch.float32))
            self.lora_B = nn.Parameter(torch.zeros((base.out_features, LORA_RANK), dtype=torch.float32))

        def reset(self, seed: int) -> None:
            torch.manual_seed(seed)
            nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
            nn.init.zeros_(self.lora_B)

        def forward(self, inputs: Any) -> Any:
            output = self.base(inputs)
            if not self.enabled:
                return output
            update = functional.linear(functional.linear(inputs.float(), self.lora_A), self.lora_B)
            return output + (update * self.scale).to(dtype=output.dtype)

    wrappers: list[Any] = []
    for name, module in list(model.named_modules()):
        if name.endswith(".self_attn.q_proj") or name.endswith(".self_attn.v_proj"):
            if not isinstance(module, nn.Linear):
                raise ExperimentError(f"unexpected LoRA target type: {name}")
            parent_name, child_name = name.rsplit(".", 1)
            wrapper = LoRALinear(module)
            setattr(model.get_submodule(parent_name), child_name, wrapper)
            wrappers.append(wrapper)
    if not wrappers:
        raise ExperimentError("no Qwen3 q_proj/v_proj targets found")
    model.to(torch.device("mps"))
    model.eval()
    model.config.use_cache = False
    for wrapper in wrappers:
        wrapper.base.requires_grad_(False)
    return model, tokenizer, wrappers, str(torch.device("mps"))


def _reset_adapters(wrappers: list[Any], seed: int) -> list[Any]:
    for index, wrapper in enumerate(wrappers):
        wrapper.reset(seed + index)
        wrapper.enabled = True
    return [parameter for wrapper in wrappers for parameter in (wrapper.lora_A, wrapper.lora_B)]


def _set_adapters(wrappers: list[Any], enabled: bool) -> None:
    for wrapper in wrappers:
        wrapper.enabled = enabled


def _adapter_state(wrappers: list[Any]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for index, wrapper in enumerate(wrappers):
        state[f"layer_target_{index}.lora_A"] = wrapper.lora_A.detach().cpu().contiguous()
        state[f"layer_target_{index}.lora_B"] = wrapper.lora_B.detach().cpu().contiguous()
    return state


def _save_adapter(wrappers: list[Any], path: Path) -> str:
    try:
        from safetensors.torch import save_file
    except ImportError as exc:
        raise ExperimentError("Safetensors is required for adapter custody") from exc
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    save_file(_adapter_state(wrappers), str(path))
    path.chmod(0o600)
    return sha256_file(path)


def _tensor_batch(sample: Mapping[str, Any], device: Any) -> tuple[Any, Any]:
    torch, _, _ = _import_torch()
    inputs = torch.tensor([sample["input_ids"]], dtype=torch.long, device=device)
    mask = torch.ones_like(inputs)
    return inputs, mask


def _target_nll(
    model: Any,
    sample: Mapping[str, Any],
    *,
    device: Any,
    layer_patch: Any | None = None,
    capture_layer: bool = False,
) -> tuple[float, Any | None]:
    torch, _, functional = _import_torch()
    inputs, mask = _tensor_batch(sample, device)
    layer = model.model.layers[LAYER_INDEX]
    captured: dict[str, Any] = {}
    target_start = int(sample["target_start"])
    target_count = len(sample["target_ids"])
    patch_start = max(0, target_start - 1)
    patch_end = patch_start + target_count

    def hook(_module: Any, _arguments: Any, output: Any) -> Any:
        hidden = output[0] if isinstance(output, tuple) else output
        if capture_layer:
            captured["hidden"] = hidden.detach().to(device="cpu", dtype=torch.float32)
        if layer_patch is not None:
            replacement = hidden.clone()
            patch = layer_patch.to(device=hidden.device, dtype=hidden.dtype)
            replacement[:, patch_start:patch_end, :] = patch[:, patch_start:patch_end, :]
            if isinstance(output, tuple):
                return (replacement, *output[1:])
            return replacement
        return output

    handle = layer.register_forward_hook(hook)
    try:
        with torch.inference_mode():
            output = model(input_ids=inputs, attention_mask=mask, use_cache=False, return_dict=True)
            logits = output.logits[0, patch_start:patch_end, :].float()
            target = torch.tensor(sample["target_ids"], dtype=torch.long, device=device)
            loss = functional.cross_entropy(logits, target, reduction="mean")
            value = float(loss.detach().cpu())
    finally:
        handle.remove()
    if not math.isfinite(value):
        raise ExperimentError(f"non-finite target NLL for {sample['doc_id']}")
    return value, captured.get("hidden")


def _generate(model: Any, tokenizer: Any, sample: Mapping[str, Any], device: Any) -> str:
    torch, _, _ = _import_torch()
    prompt_ids = sample["prompt_ids"]
    inputs = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    mask = torch.ones_like(inputs)
    model.eval()
    with torch.inference_mode():
        generated = model.generate(
            input_ids=inputs,
            attention_mask=mask,
            do_sample=False,
            max_new_tokens=MAX_NEW_TOKENS,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )
    output_ids = generated[0, inputs.shape[1] :].detach().cpu().tolist()
    return tokenizer.decode(output_ids, skip_special_tokens=True).strip()


def _train_one_epoch(
    model: Any,
    wrappers: list[Any],
    samples: list[dict[str, Any]],
    seed: int,
    *,
    deadline: float,
) -> list[float]:
    torch, _, _ = _import_torch()
    parameters = _reset_adapters(wrappers, seed)
    optimizer = torch.optim.AdamW(parameters, lr=LEARNING_RATE)
    device = torch.device("mps")
    losses: list[float] = []
    order = list(samples)
    random.Random(seed ^ 0x5A17).shuffle(order)
    model.train()
    model.config.use_cache = False
    for sample in order:
        if time.monotonic() > deadline:
            raise ExperimentError("180-minute wall-clock limit reached during adapter training")
        inputs, mask = _tensor_batch(sample, device)
        labels = torch.tensor([sample["labels"]], dtype=torch.long, device=device)
        optimizer.zero_grad(set_to_none=True)
        output = model(input_ids=inputs, attention_mask=mask, labels=labels, use_cache=False, return_dict=True)
        loss = output.loss
        if not bool(torch.isfinite(loss).item()):
            raise ExperimentError(f"non-finite training loss for {sample['doc_id']}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(parameters, max_norm=1.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    model.eval()
    return losses


def _percentiles(values: list[float]) -> tuple[float, float]:
    ordered = sorted(values)
    if not ordered:
        raise ExperimentError("cannot compute an interval over no values")
    lower_index = int(0.025 * (len(ordered) - 1))
    upper_index = int(0.975 * (len(ordered) - 1))
    return ordered[lower_index], ordered[upper_index]


def _evaluate_arm(
    model: Any,
    tokenizer: Any,
    rows: list[dict[str, Any]],
    device: Any,
    *,
    deadline: float,
) -> dict[str, Any]:
    result: dict[str, Any] = {"generation": {}, "nll": {}}
    for sample in rows:
        if time.monotonic() > deadline:
            raise ExperimentError("180-minute wall-clock limit reached during held-out evaluation")
        result["generation"][sample["doc_id"]] = _generate(model, tokenizer, sample, device)
        nll, _ = _target_nll(model, sample, device=device)
        result["nll"][sample["doc_id"]] = nll
    return result


def _mechanistic_row(
    model: Any,
    wrappers: list[Any],
    sample: dict[str, Any],
    device: Any,
) -> dict[str, Any]:
    _set_adapters(wrappers, False)
    base_nll, base_hidden = _target_nll(model, sample, device=device, capture_layer=True)
    if base_hidden is None:
        raise ExperimentError("base layer capture missing")
    _set_adapters(wrappers, True)
    adapted_nll, adapted_hidden = _target_nll(model, sample, device=device, capture_layer=True)
    if adapted_hidden is None:
        raise ExperimentError("adapted layer capture missing")
    identity_nll, _ = _target_nll(model, sample, device=device, layer_patch=adapted_hidden)
    patched_nll, _ = _target_nll(model, sample, device=device, layer_patch=base_hidden)
    identity_error = abs(identity_nll - adapted_nll)
    return {
        "doc_id": sample["doc_id"],
        "base_nll": base_nll,
        "adapted_nll": adapted_nll,
        "identity_patch_nll": identity_nll,
        "base_activation_patch_nll": patched_nll,
        "identity_patch_abs_error": identity_error,
        "activation_patch_delta_nll": patched_nll - adapted_nll,
    }


def _report_from_private(private: Mapping[str, Any], references: Mapping[str, str]) -> dict[str, Any]:
    assessment_ids = private["assessment_ids"]
    base = private["arms"]["untouched_base"]
    update_arms = ("loss_selected", "random_control")
    for arm in ("untouched_base", *update_arms):
        if arm not in private["arms"]:
            raise ExperimentError(f"missing arm: {arm}")

    rouge_by_arm_seed: dict[str, dict[int, dict[str, float]]] = {arm: {} for arm in update_arms}
    nll_by_arm_seed: dict[str, dict[int, dict[str, float]]] = {arm: {} for arm in update_arms}
    for arm in update_arms:
        for repeat in private["arms"][arm]:
            seed = int(repeat["seed"])
            if seed in rouge_by_arm_seed[arm]:
                raise ExperimentError("duplicate training seed")
            generations = repeat["generation"]
            nlls = repeat["nll"]
            if set(generations) != set(assessment_ids) or set(nlls) != set(assessment_ids):
                raise ExperimentError("assessment cells are incomplete or duplicated")
            if any(not isinstance(text, str) or not text.strip() for text in generations.values()):
                raise ExperimentError("assessment contains an empty generation")
            if any(not math.isfinite(float(value)) for value in nlls.values()):
                raise ExperimentError("assessment contains non-finite NLL")
            rouge_by_arm_seed[arm][seed] = {
                doc_id: rouge_l_f1(generations[doc_id], references[doc_id]) for doc_id in assessment_ids
            }
            nll_by_arm_seed[arm][seed] = {doc_id: float(nlls[doc_id]) for doc_id in assessment_ids}

    if set(rouge_by_arm_seed["loss_selected"]) != set(SEEDS) or set(rouge_by_arm_seed["random_control"]) != set(SEEDS):
        raise ExperimentError("training seed roster mismatch")
    if set(base["generation"]) != set(assessment_ids) or set(base["nll"]) != set(assessment_ids):
        raise ExperimentError("base assessment roster mismatch")
    if any(not isinstance(text, str) or not text.strip() for text in base["generation"].values()):
        raise ExperimentError("base assessment contains an empty generation")
    if any(not math.isfinite(float(value)) for value in base["nll"].values()):
        raise ExperimentError("base assessment contains non-finite NLL")

    per_doc_effects: list[float] = []
    selected_mean_rows: list[float] = []
    random_mean_rows: list[float] = []
    base_mean_rows: list[float] = []
    selected_nll_rows: list[float] = []
    base_nll_rows: list[float] = []
    for doc_id in assessment_ids:
        selected = _mean([rouge_by_arm_seed["loss_selected"][seed][doc_id] for seed in SEEDS])
        random_value = _mean([rouge_by_arm_seed["random_control"][seed][doc_id] for seed in SEEDS])
        base_value = rouge_l_f1(base["generation"][doc_id], references[doc_id])
        selected_nll = _mean([nll_by_arm_seed["loss_selected"][seed][doc_id] for seed in SEEDS])
        base_nll = float(base["nll"][doc_id])
        per_doc_effects.append(selected - random_value)
        selected_mean_rows.append(selected)
        random_mean_rows.append(random_value)
        base_mean_rows.append(base_value)
        selected_nll_rows.append(selected_nll)
        base_nll_rows.append(base_nll)

    mean_effect = _mean(per_doc_effects)
    ci = bootstrap_interval(per_doc_effects)
    selected_rouge = _mean(selected_mean_rows)
    random_rouge = _mean(random_mean_rows)
    base_rouge = _mean(base_mean_rows)
    selected_nll = _mean(selected_nll_rows)
    base_nll = _mean(base_nll_rows)
    mechanism = private["mechanistic"]
    max_identity_error = max(float(row["identity_patch_abs_error"]) for row in mechanism)
    if len(mechanism) != MECHANISTIC_ROWS * len(SEEDS) * 2:
        raise ExperimentError("mechanistic row count mismatch")
    if max_identity_error > IDENTITY_PATCH_TOLERANCE:
        raise ExperimentError("identity patch control failed")

    all_generations = [
        base["generation"][doc_id] for doc_id in assessment_ids
    ] + [
        repeat["generation"][doc_id]
        for arm in update_arms
        for repeat in private["arms"][arm]
        for doc_id in assessment_ids
    ]
    complete_outputs = len(all_generations) == len(assessment_ids) * (1 + 2 * len(SEEDS)) and all(
        isinstance(text, str) and bool(text.strip()) for text in all_generations
    )
    candidate = (
        mean_effect >= MIN_EFFECT
        and ci[0] > 0.0
        and selected_rouge >= base_rouge
        and selected_nll - base_nll <= 0.05
        and complete_outputs
    )
    return {
        "schema_version": "aligned-rsi-local-billsum-v1-evaluation-report",
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "assurance_level": "PENDING_LOCAL_VERIFICATION",
        "reviewer_status": "LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT",
        "reproducibility_status": "SINGLE_LOCAL_EXECUTION",
        "local_acceptance": "PENDING_LOCAL_VERIFICATION",
        "independent_acceptance": False,
        "candidate_disposition": "Candidate" if candidate else "NoCandidate",
        "claim_ceiling": CLAIM_CEILING,
        "model": {"repo_id": MODEL_ID, "revision": MODEL_REVISION},
        "dataset": {
            "repo_id": DATASET_ID,
            "revision": DATASET_REVISION,
            "included_splits": ["train", "test"],
            "excluded_splits": ["ca_test"],
        },
        "counts": {
            "fit_pool": len(private["fit_pool_ids"]),
            "assessment_documents": len(assessment_ids),
            "training_seeds": list(SEEDS),
            "training_examples_per_arm_per_seed": ARM_EXAMPLES,
            "mechanistic_rows": len(mechanism),
        },
        "primary": {
            "metric": "paired_rouge_l_f1_loss_selected_minus_random_control",
            "mean_effect": mean_effect,
            "ci95_lower": ci[0],
            "ci95_upper": ci[1],
            "minimum_meaningful_effect": MIN_EFFECT,
            "loss_selected_mean_rouge_l_f1": selected_rouge,
            "random_control_mean_rouge_l_f1": random_rouge,
            "untouched_base_mean_rouge_l_f1": base_rouge,
        },
        "secondary": {
            "loss_selected_minus_base_mean_target_nll": selected_nll - base_nll,
            "identity_patch_max_abs_nll_error": max_identity_error,
            "mean_activation_patch_delta_nll": _mean(
                [float(row["activation_patch_delta_nll"]) for row in mechanism]
            ),
            "mean_fraction_base_activation_recovered": _mean(
                [
                    (float(row["base_activation_patch_nll"]) - float(row["adapted_nll"]))
                    / (float(row["base_nll"]) - float(row["adapted_nll"]))
                    for row in mechanism
                    if abs(float(row["base_nll"]) - float(row["adapted_nll"])) > 1e-12
                ]
            ) if any(
                abs(float(row["base_nll"]) - float(row["adapted_nll"])) > 1e-12
                for row in mechanism
            ) else None,
            "complete_finite_outputs": complete_outputs,
        },
        "custody": {
            "raw_inputs_and_generations_external_owner_only": True,
            "adapter_weights_external_owner_only": True,
            "repository_outputs_aggregate_only": True,
        },
        "nonclaims": [
            "independent_acceptance",
            "general_alignment",
            "general_recursive_self_improvement",
            "feature_level_mechanistic_explanation",
            "benchmark_leaderboard_result",
            "production_readiness",
        ],
    }


def run() -> dict[str, Any]:
    """Execute the frozen local fit/selection/update/held-out/patch loop."""
    manifest = _verify_protocol()
    prepared = _validate_prepared()
    if not (sys.platform == "darwin" and __import__("platform").machine() == "arm64"):
        raise ExperimentError("frozen execution target is Apple Silicon macOS")
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
        }
    )
    torch, _, _ = _import_torch()
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise ExperimentError("Transformers unavailable") from exc

    start_time = time.monotonic()
    deadline = start_time + WALL_CLOCK_LIMIT_SECONDS
    run_id = dt.datetime.now(dt.timezone.utc).strftime("run-%Y%m%dT%H%M%S%fZ")
    run_root = RUNS_ROOT / run_id
    if run_root.exists():
        raise ExperimentError("refusing to overwrite an existing run")
    run_root.mkdir(parents=True, mode=0o700)
    run_root.chmod(0o700)
    _write_run_status(run_root, run_id, "RUNNING", "input_validation")

    train_rows = _load_federal_rows("train")
    assessment_rows = _load_federal_rows("test")
    fit_pool = train_rows[:FIT_POOL_SIZE]
    assessment_rows = assessment_rows[:ASSESSMENT_SIZE]
    fit_ids = [row["doc_id"] for row in fit_pool]
    assessment_ids = [row["doc_id"] for row in assessment_rows]
    if len(fit_ids) != FIT_POOL_SIZE or len(assessment_ids) != ASSESSMENT_SIZE:
        raise ExperimentError("pinned dataset has fewer rows than frozen cohort size")
    if len(set(fit_ids) & set(assessment_ids)) != 0:
        raise ExperimentError("fit and assessment documents overlap")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ROOT, local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    encoded_fit = _tokenize_rows(tokenizer, fit_pool)
    encoded_assessment = _tokenize_rows(tokenizer, assessment_rows)
    model, tokenizer, wrappers, device_name = _create_model_and_tokenizer(MODEL_ROOT)
    model_weights_sha256 = _tree_digest(prepared["model_files"])

    _write_run_status(run_root, run_id, "RUNNING", "fit_loss_scoring")
    print(f"run_id={run_id} phase=fit_loss rows={len(encoded_fit)} device={device_name}", flush=True)
    fit_losses: dict[str, float] = {}
    device = torch.device("mps")
    _set_adapters(wrappers, False)
    for index, sample in enumerate(encoded_fit, start=1):
        if time.monotonic() > deadline:
            raise ExperimentError("180-minute wall-clock limit reached during fit scoring")
        fit_losses[sample["doc_id"]], _ = _target_nll(model, sample, device=device)
        if index % 64 == 0:
            print(f"phase=fit_loss completed={index}", flush=True)

    assessment_refs = {row["doc_id"]: row["summary"] for row in assessment_rows}
    print(f"run_id={run_id} phase=untouched_base rows={len(encoded_assessment)}", flush=True)
    _write_run_status(run_root, run_id, "RUNNING", "untouched_base_assessment")
    base_result = _evaluate_arm(model, tokenizer, encoded_assessment, device, deadline=deadline)
    arms: dict[str, Any] = {"untouched_base": base_result, "loss_selected": [], "random_control": []}
    mechanistic: list[dict[str, Any]] = []
    fit_id_to_sample = {sample["doc_id"]: sample for sample in encoded_fit}
    assessment_mechanistic = encoded_assessment[:MECHANISTIC_ROWS]
    selected_ids = sorted(fit_losses, key=lambda identifier: (-fit_losses[identifier], identifier))[:ARM_EXAMPLES]
    if len(selected_ids) != ARM_EXAMPLES:
        raise ExperimentError("loss-selected arm has wrong training roster size")
    selected_set = set(selected_ids)

    for seed in SEEDS:
        random_rows = random.Random(seed).sample(encoded_fit, ARM_EXAMPLES)
        arm_specs = (
            ("loss_selected", [fit_id_to_sample[item] for item in selected_ids]),
            ("random_control", random_rows),
        )
        for arm_name, selected_rows in arm_specs:
            if time.monotonic() > deadline:
                raise ExperimentError("180-minute wall-clock limit reached before assessment completed")
            print(f"run_id={run_id} phase=train arm={arm_name} seed={seed} rows={len(selected_rows)}", flush=True)
            _write_run_status(run_root, run_id, "RUNNING", f"train_{arm_name}_seed_{seed}")
            train_losses = _train_one_epoch(model, wrappers, selected_rows, seed, deadline=deadline)
            adapter_path = run_root / "adapters" / f"{arm_name}-seed-{seed}.safetensors"
            adapter_sha256 = _save_adapter(wrappers, adapter_path)
            _write_run_status(run_root, run_id, "RUNNING", f"assessment_{arm_name}_seed_{seed}")
            evaluation = _evaluate_arm(model, tokenizer, encoded_assessment, device, deadline=deadline)
            arms[arm_name].append(
                {
                    "seed": seed,
                    "selection_ids": [row["doc_id"] for row in selected_rows],
                    "adapter_sha256": adapter_sha256,
                    "train_loss_mean": _mean(train_losses),
                    "train_steps": len(train_losses),
                    **evaluation,
                }
            )
            for sample in assessment_mechanistic:
                if time.monotonic() > deadline:
                    raise ExperimentError("180-minute wall-clock limit reached during activation patching")
                measurement = _mechanistic_row(model, wrappers, sample, device)
                measurement.update({"arm": arm_name, "seed": seed})
                mechanistic.append(measurement)

    if tree_manifest(MODEL_ROOT) != prepared["model_files"]:
        raise ExperimentError("base checkpoint bytes changed during adapter training")
    private = {
        "schema_version": "aligned-rsi-local-billsum-v1-private-run",
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "run_id": run_id,
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "manifest_sha256": sha256_file(MANIFEST_PATH),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "prepared_inputs_sha256": prepared["prepared_inputs_sha256"],
        "model_weights_manifest_sha256": model_weights_sha256,
        "base_checkpoint_unchanged": True,
        "device": device_name,
        "package_versions": prepared["runtime"],
        "fit_pool_ids": fit_ids,
        "assessment_ids": assessment_ids,
        "fit_nll_by_id": fit_losses,
        "loss_selected_ids": selected_ids,
        "loss_selected_excluded_ids": sorted(set(fit_ids) - selected_set),
        "arms": arms,
        "mechanistic": mechanistic,
        "elapsed_seconds": time.monotonic() - start_time,
    }
    private_path = run_root / "private_run.json"
    save_json(private_path, private)
    report = _report_from_private(private, assessment_refs)
    git_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    report.update(
        {
            "run_id": run_id,
            "source_revision": git_revision,
            "source_worktree_dirty": bool(subprocess.run(
                ["git", "status", "--porcelain", "--", str(Path(__file__).resolve()), str(PROTOCOL_PATH), str(MANIFEST_PATH)],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()),
            "source_code_sha256": private["runner_sha256"],
            "protocol_sha256": private["protocol_sha256"],
            "manifest_sha256": private["manifest_sha256"],
            "prepared_inputs_sha256": private["prepared_inputs_sha256"],
            "model_weights_manifest_sha256": private["model_weights_manifest_sha256"],
            "private_run_sha256": sha256_file(private_path),
            "elapsed_seconds": private["elapsed_seconds"],
            "device": device_name,
            "package_versions": prepared["runtime"],
            "paid_provider_cost_usd": 0.0,
            "energy_measurement": "not_measured",
        }
    )
    _write_run_status(run_root, run_id, "RUNNING", "aggregate_report")
    RELEASE_ROOT.mkdir(parents=True, exist_ok=False)
    save_json(PUBLIC_REPORT_PATH, report)
    release_manifest = {
        "schema_version": "aligned-rsi-local-billsum-v1-aggregate-release",
        "state_slice": STATE_SLICE,
        "files": [{"path": "evaluation_report.json", "sha256": sha256_file(PUBLIC_REPORT_PATH)}],
        "raw_data_included": False,
        "model_weights_included": False,
        "generated_summaries_included": False,
        "independent_acceptance": False,
    }
    save_json(RELEASE_ROOT / "release_manifest.json", release_manifest)
    _write_run_status(run_root, run_id, "COMPLETE", "verified_pending_local_acceptance")
    return report


def _write_run_status(run_root: Path, run_id: str, status: str, phase: str, error: str | None = None) -> None:
    payload: dict[str, Any] = {
        "schema_version": "aligned-rsi-local-billsum-v1-run-status",
        "state_slice": STATE_SLICE,
        "run_id": run_id,
        "status": status,
        "phase": phase,
        "updated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if error is not None:
        payload["error"] = error
    save_json(run_root / "execution_status.json", payload)


def verify() -> dict[str, Any]:
    """Recompute aggregate claims from owner-only generations and references."""
    _verify_protocol()
    prepared = _validate_prepared()
    report = load_json(PUBLIC_REPORT_PATH)
    if report.get("state_slice") != STATE_SLICE or report.get("claim_ceiling") != CLAIM_CEILING:
        raise ExperimentError("public report identity mismatch")
    private_path = RUNS_ROOT / report["run_id"] / "private_run.json"
    status = load_json(RUNS_ROOT / report["run_id"] / "execution_status.json")
    if status.get("status") not in {"COMPLETE", "LOCAL_ACCEPTED"}:
        raise ExperimentError("execution status is not complete")
    if sha256_file(private_path) != report.get("private_run_sha256"):
        raise ExperimentError("private run digest mismatch")
    private = load_json(private_path)
    if private.get("protocol_sha256") != sha256_file(PROTOCOL_PATH):
        raise ExperimentError("private result protocol digest differs from current protocol")
    if private.get("manifest_sha256") != sha256_file(MANIFEST_PATH):
        raise ExperimentError("private result manifest digest differs from current manifest")
    if private.get("runner_sha256") != sha256_file(Path(__file__).resolve()):
        raise ExperimentError("private result runner digest differs from current runner")
    if report.get("source_code_sha256") != private.get("runner_sha256"):
        raise ExperimentError("public source code digest mismatch")
    if report.get("protocol_sha256") != private.get("protocol_sha256"):
        raise ExperimentError("public protocol digest mismatch")
    if report.get("manifest_sha256") != private.get("manifest_sha256"):
        raise ExperimentError("public manifest digest mismatch")
    if private.get("prepared_inputs_sha256") != prepared.get("prepared_inputs_sha256"):
        raise ExperimentError("private result input digest mismatch")
    if private.get("base_checkpoint_unchanged") is not True:
        raise ExperimentError("base checkpoint immutability receipt missing")
    if _tree_digest(prepared["model_files"]) != private.get("model_weights_manifest_sha256"):
        raise ExperimentError("model manifest digest differs")
    assessment_rows = _load_federal_rows("test")
    expected_roster = [row["doc_id"] for row in assessment_rows[:ASSESSMENT_SIZE]]
    expected_ids = private.get("assessment_ids")
    if expected_ids != expected_roster:
        raise ExperimentError("assessment roster schema mismatch")
    references = {row["doc_id"]: row["summary"] for row in assessment_rows[:ASSESSMENT_SIZE]}
    train_rows = _load_federal_rows("train")
    expected_fit_ids = [row["doc_id"] for row in train_rows[:FIT_POOL_SIZE]]
    if private.get("fit_pool_ids") != expected_fit_ids:
        raise ExperimentError("fit pool roster differs from the frozen train prefix")
    fit_nll = private.get("fit_nll_by_id", {})
    if set(fit_nll) != set(expected_fit_ids) or any(not math.isfinite(float(value)) for value in fit_nll.values()):
        raise ExperimentError("fit-pool NLL roster is incomplete or non-finite")
    expected_selected = sorted(expected_fit_ids, key=lambda identifier: (-float(fit_nll[identifier]), identifier))[:ARM_EXAMPLES]
    if private.get("loss_selected_ids") != expected_selected:
        raise ExperimentError("loss-selected roster differs from frozen fit-pool NLL ranking")
    if private.get("loss_selected_excluded_ids") != sorted(set(expected_fit_ids) - set(expected_selected)):
        raise ExperimentError("loss-selected exclusion roster mismatch")
    run_root = RUNS_ROOT / report["run_id"]
    for arm_name in ("loss_selected", "random_control"):
        repeats = private.get("arms", {}).get(arm_name)
        if not isinstance(repeats, list) or len(repeats) != len(SEEDS):
            raise ExperimentError(f"invalid repeat roster for {arm_name}")
        for repeat, seed in zip(repeats, SEEDS, strict=True):
            expected_selection = expected_selected if arm_name == "loss_selected" else [
                row["doc_id"] for row in random.Random(seed).sample(train_rows[:FIT_POOL_SIZE], ARM_EXAMPLES)
            ]
            if repeat.get("seed") != seed or repeat.get("selection_ids") != expected_selection:
                raise ExperimentError(f"training selection mismatch for {arm_name} seed {seed}")
            if repeat.get("train_steps") != ARM_EXAMPLES:
                raise ExperimentError(f"training step count mismatch for {arm_name} seed {seed}")
            if not math.isfinite(float(repeat.get("train_loss_mean", float("nan")))):
                raise ExperimentError(f"training loss is non-finite for {arm_name} seed {seed}")
            adapter_path = run_root / "adapters" / f"{arm_name}-seed-{seed}.safetensors"
            if not adapter_path.is_file() or sha256_file(adapter_path) != repeat.get("adapter_sha256"):
                raise ExperimentError(f"adapter digest mismatch for {arm_name} seed {seed}")
    expected_mechanism_rows = {
        (arm_name, seed, doc_id)
        for arm_name in ("loss_selected", "random_control")
        for seed in SEEDS
        for doc_id in expected_ids[:MECHANISTIC_ROWS]
    }
    observed_mechanism_rows = {
        (row.get("arm"), row.get("seed"), row.get("doc_id"))
        for row in private.get("mechanistic", [])
    }
    if observed_mechanism_rows != expected_mechanism_rows:
        raise ExperimentError("mechanistic diagnostic roster mismatch")
    reconstructed = _report_from_private(private, references)
    for key in ("candidate_disposition", "primary", "secondary", "counts"):
        if canonical_bytes(reconstructed.get(key)) != canonical_bytes(report.get(key)):
            raise ExperimentError(f"report reconstruction mismatch: {key}")
    if report.get("assurance_level") not in {"PENDING_LOCAL_VERIFICATION", "INTERNAL_PASS"}:
        raise ExperimentError("assurance label mismatch")
    if report.get("reviewer_status") != "LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT":
        raise ExperimentError("reviewer status mismatch")
    if report.get("independent_acceptance") is not False:
        raise ExperimentError("report claims independent acceptance")
    release_manifest = load_json(RELEASE_ROOT / "release_manifest.json")
    manifest_files = release_manifest.get("files")
    if not isinstance(manifest_files, list) or not all(isinstance(item, dict) for item in manifest_files):
        raise ExperimentError("aggregate release manifest schema mismatch")
    for item in manifest_files:
        file_path = RELEASE_ROOT / item.get("path", "")
        if not file_path.is_file() or sha256_file(file_path) != item.get("sha256"):
            raise ExperimentError("aggregate release manifest digest mismatch")
    if {item.get("path") for item in manifest_files} not in (
        {"evaluation_report.json"},
        {"evaluation_report.json", "local_acceptance.json"},
    ):
        raise ExperimentError("aggregate release contains an unapproved file")
    if any(
        release_manifest.get(flag) is not False
        for flag in ("raw_data_included", "model_weights_included", "generated_summaries_included", "independent_acceptance")
    ):
        raise ExperimentError("release contains a forbidden claim or artifact")
    core_report = dict(report)
    core_report["assurance_level"] = "PENDING_LOCAL_VERIFICATION"
    core_report["local_acceptance"] = "PENDING_LOCAL_VERIFICATION"
    core_report.pop("local_acceptance_receipt_sha256", None)
    expected_core_digest = sha256_bytes(canonical_bytes(core_report))
    acceptance = {
        "schema_version": "aligned-rsi-local-billsum-v1-local-acceptance",
        "state_slice": STATE_SLICE,
        "assurance_level": "INTERNAL_PASS",
        "reviewer_status": "LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT",
        "local_acceptance": "INTERNAL_PASS",
        "independent_acceptance": False,
        "claim_ceiling": CLAIM_CEILING,
        "candidate_disposition": report["candidate_disposition"],
        "accepted_report_core_sha256": expected_core_digest,
        "private_run_sha256": report["private_run_sha256"],
        "prepared_inputs_sha256": report["prepared_inputs_sha256"],
        "source_code_sha256": report["source_code_sha256"],
        "protocol_sha256": report["protocol_sha256"],
        "manifest_sha256": report["manifest_sha256"],
    }
    acceptance_path = RELEASE_ROOT / "local_acceptance.json"
    save_json(acceptance_path, acceptance)
    report["assurance_level"] = "INTERNAL_PASS"
    report["local_acceptance"] = "INTERNAL_PASS"
    report["local_acceptance_receipt_sha256"] = sha256_file(acceptance_path)
    save_json(PUBLIC_REPORT_PATH, report)
    release_manifest["files"] = [
        {"path": "evaluation_report.json", "sha256": sha256_file(PUBLIC_REPORT_PATH)},
        {"path": "local_acceptance.json", "sha256": sha256_file(acceptance_path)},
    ]
    save_json(RELEASE_ROOT / "release_manifest.json", release_manifest)
    _write_run_status(RUNS_ROOT / report["run_id"], report["run_id"], "LOCAL_ACCEPTED", "local_verification_passed")
    return {
        "valid": True,
        "assurance_level": "INTERNAL_PASS",
        "local_acceptance": "INTERNAL_PASS",
        "candidate_disposition": report["candidate_disposition"],
        "run_id": report["run_id"],
        "claim_ceiling": CLAIM_CEILING,
        "independent_acceptance": False,
        "public_report_sha256": sha256_file(PUBLIC_REPORT_PATH),
        "private_run_sha256": sha256_file(private_path),
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description="local BillSum curriculum/update experiment")
    parser.add_argument("command", choices=("prepare", "run", "verify"))
    args = parser.parse_args()
    try:
        result = {"prepare": prepare, "run": run, "verify": verify}[args.command]()
    except Exception as exc:
        if args.command == "run" and RUNS_ROOT.is_dir():
            for status_path in sorted(RUNS_ROOT.glob("run-*/execution_status.json")):
                try:
                    status = load_json(status_path)
                except ExperimentError:
                    continue
                if status.get("status") == "RUNNING":
                    _write_run_status(
                        status_path.parent,
                        str(status.get("run_id")),
                        "FAILED",
                        str(status.get("phase", "unknown")),
                        error=f"{type(exc).__name__}: {exc}",
                    )
        raise
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
