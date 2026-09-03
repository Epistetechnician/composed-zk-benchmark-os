#!/usr/bin/env python3
"""MiniMind domain-sequence continual-learning harness.

State slice: continual-learning-minimind-domain-specific-v1.

The synthetic path is a deterministic contract fixture. The model path is a
real MiniMind adapter, but it is fail-closed until an independent,
packet-bound Ed25519 execution receipt is verified. No function in this
module downloads a model or contacts a provider.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence


STATE_SLICE = "continual-learning-minimind-domain-specific-v1"
SCHEMA_VERSION = "continual-learning-minimind-domain-sequence-result-v1"
PROTOCOL = "minimind-domain-specific-sequence-v1"
CLAIM_CEILING = "LocalDevelopmentMiniMindDomainSequenceSyntheticOnly"
MODEL_CLAIM_CEILING = "LocalDevelopmentMiniMindDomainSequenceQualificationV1"
RECEIPT_SCHEMA_VERSION = "minimind-domain-specific-v1-execution-receipt"
UPSTREAM_URL = "https://github.com/jingyaogong/minimind.git"
UPSTREAM_COMMIT = "7a6fddd63a30c06b2fdd5fac4089922b29bc841b"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = Path(
    "/Users/shaanp/Documents/research-artifacts/"
    "continual-learning-minimind-domain-specific-v1-source-20260902"
)
REVIEW_PACKET_PATH = REPO_ROOT / "docs/research/continual-learning/274-minimind-domain-specific-v1-review-packet.md"

DOMAINS = ("domain_a", "domain_b", "domain_c")
SPLITS = ("fit", "tune", "assessment")
ORDER_DIRECTIONS = ("forward", "reverse")
REPLICATE_SEEDS = (2026090201, 2026090202, 2026090203)
ORDER_SEEDS = (9401, 9402, 9403)
ARMS = (
    "untouched",
    "joint_oracle",
    "sequential_full",
    "sequential_lora",
    "sequential_replay",
    "domain_adapters",
)
MODEL_ARMS = ARMS
VECTOR_DIMENSION = 8
UPDATE_UNITS_PER_STAGE = 3
MAX_FORGETTING = 0.25
MAX_ORDER_DELTA = 0.20
MAX_CHECKPOINT_ERROR = 1e-12
MODEL_CONFIG = {
    "model_name": "minimind-3-dense",
    "hidden_size": 768,
    "num_hidden_layers": 8,
    "use_moe": False,
    "vocab_size": 6400,
    "max_seq_len": 340,
}
REQUIRED_SOURCE_FILES = (
    "LICENSE",
    "requirements.txt",
    "model/model_minimind.py",
    "model/model_lora.py",
    "model/tokenizer.json",
    "model/tokenizer_config.json",
    "trainer/train_pretrain.py",
    "trainer/train_full_sft.py",
    "trainer/train_lora.py",
    "dataset/lm_dataset.py",
)


class ProtocolError(ValueError):
    """Raised when the frozen boundary is violated."""


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _unit(*parts: object) -> float:
    payload = "|".join((STATE_SLICE, *(str(part) for part in parts))).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / float(1 << 64)


def _signed(*parts: object) -> float:
    return 2.0 * _unit(*parts) - 1.0


def _anchor() -> tuple[float, ...]:
    return tuple(0.08 * math.sin((index + 1) * 1.31) for index in range(VECTOR_DIMENSION))


def _target(domain: str, split: str, seed: int) -> tuple[float, ...]:
    scale = 0.42 + 0.08 * _unit("target-scale", domain, seed)
    return tuple(
        _anchor()[component]
        + scale * _signed("target", domain, seed, component)
        + 0.015 * _signed("split-noise", domain, split, seed, component)
        for component in range(VECTOR_DIMENSION)
    )


def _mean_vector(vectors: Sequence[Sequence[float]]) -> tuple[float, ...]:
    if not vectors:
        raise ProtocolError("cannot average an empty vector collection")
    return tuple(sum(vector[index] for vector in vectors) / len(vectors) for index in range(VECTOR_DIMENSION))


def _add(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a + b for a, b in zip(left, right))


def _sub(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a - b for a, b in zip(left, right))


def _scale(vector: Sequence[float], multiplier: float) -> tuple[float, ...]:
    return tuple(multiplier * value for value in vector)


def _loss(state: Sequence[float], target: Sequence[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(state, target)) / VECTOR_DIMENSION


def _domain_mask(domain: str) -> tuple[float, ...]:
    start = DOMAINS.index(domain) * 2
    return tuple(1.0 if start <= index < start + 2 else 0.0 for index in range(VECTOR_DIMENSION))


def _apply_mask(vector: Sequence[float], mask: Sequence[float]) -> tuple[float, ...]:
    return tuple(value * keep for value, keep in zip(vector, mask))


def _ordered_domains(order_seed: int, direction: str) -> tuple[str, ...]:
    indexed = list(enumerate(DOMAINS))
    indexed.sort(key=lambda item: (_unit("order", order_seed, item[1]), item[0]))
    if direction == "reverse":
        indexed.reverse()
    return tuple(domain for _, domain in indexed)


def _prediction_vector(
    arm: str,
    shared_state: Sequence[float],
    adapters: Mapping[str, Sequence[float]],
    domain: str,
) -> tuple[float, ...]:
    if arm == "domain_adapters":
        return _add(shared_state, adapters.get(domain, (0.0,) * VECTOR_DIMENSION))
    return tuple(shared_state)


def _run_trial(arm: str, split: str, seed: int, order_seed: int, direction: str) -> dict[str, Any]:
    if arm not in ARMS:
        raise ProtocolError(f"unknown arm: {arm}")
    if split not in SPLITS:
        raise ProtocolError(f"unknown split: {split}")
    if direction not in ORDER_DIRECTIONS:
        raise ProtocolError(f"unknown order direction: {direction}")

    base = _anchor()
    shared_state = base
    adapters: dict[str, tuple[float, ...]] = {}
    fit_targets = {domain: _target(domain, "fit", seed) for domain in DOMAINS}
    evaluation_targets = {domain: _target(domain, split, seed) for domain in DOMAINS}
    order = _ordered_domains(order_seed, direction)
    learned_losses: dict[str, float] = {}
    stage_metrics: list[dict[str, Any]] = []

    for stage_index, domain in enumerate(order, start=1):
        current_target = fit_targets[domain]
        if arm == "joint_oracle":
            shared_state = _scale(_add(shared_state, _mean_vector(tuple(fit_targets.values()))), 0.5)
        elif arm == "sequential_full":
            shared_state = _add(shared_state, _scale(_sub(current_target, shared_state), 0.42))
        elif arm == "sequential_lora":
            delta = _scale(_sub(current_target, shared_state), 0.78)
            shared_state = _add(shared_state, _apply_mask(delta, _domain_mask(domain)))
        elif arm == "sequential_replay":
            seen = [fit_targets[item] for item in order[: stage_index - 1]]
            replay_target = _mean_vector((current_target, *seen))
            shared_state = _add(shared_state, _scale(_sub(replay_target, shared_state), 0.42))
        elif arm == "domain_adapters":
            before = adapters.get(domain, (0.0,) * VECTOR_DIMENSION)
            desired = _sub(current_target, base)
            adapters[domain] = _add(before, _scale(_sub(desired, before), 0.78))

        domain_losses = {
            item: _loss(_prediction_vector(arm, shared_state, adapters, item), evaluation_targets[item])
            for item in DOMAINS
        }
        learned_losses.setdefault(domain, domain_losses[domain])
        max_forgetting = max(
            (max(0.0, domain_losses[item] - learned_losses[item]) for item in learned_losses),
            default=0.0,
        )
        stage_metrics.append(
            {
                "stage_index": stage_index,
                "domain": domain,
                "domain_losses": domain_losses,
                "mean_loss": sum(domain_losses.values()) / len(DOMAINS),
                "max_forgetting": max_forgetting,
                "update_units": UPDATE_UNITS_PER_STAGE,
            }
        )

    base_mean_loss = sum(_loss(base, evaluation_targets[domain]) for domain in DOMAINS) / len(DOMAINS)
    final_mean_loss = stage_metrics[-1]["mean_loss"]
    return {
        "arm": arm,
        "split": split,
        "replicate_seed": seed,
        "order_seed": order_seed,
        "order_direction": direction,
        "domain_order": list(order),
        "stage_metrics": stage_metrics,
        "base_mean_loss": base_mean_loss,
        "final_mean_loss": final_mean_loss,
        "primary_improvement": base_mean_loss - final_mean_loss,
        "max_forgetting": max(item["max_forgetting"] for item in stage_metrics),
        "compute_units": UPDATE_UNITS_PER_STAGE * len(DOMAINS),
        "checkpoint_restore_max_abs_error": 0.0,
        "hard_guards": {
            "forgetting": max(item["max_forgetting"] for item in stage_metrics) <= MAX_FORGETTING,
            "checkpoint_restore": True,
            "complete_stage_coverage": len(stage_metrics) == len(DOMAINS),
        },
    }


def _summary(trials: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_split_arm: dict[str, Any] = {}
    for split in SPLITS:
        for arm in ARMS:
            subset = [item for item in trials if item["split"] == split and item["arm"] == arm]
            mean_improvement = sum(item["primary_improvement"] for item in subset) / len(subset)
            mean_final_loss = sum(item["final_mean_loss"] for item in subset) / len(subset)
            max_forgetting = max(item["max_forgetting"] for item in subset)
            paired = {}
            for seed in REPLICATE_SEEDS:
                forward = next(item for item in subset if item["replicate_seed"] == seed and item["order_direction"] == "forward")
                reverse = next(item for item in subset if item["replicate_seed"] == seed and item["order_direction"] == "reverse")
                paired[str(seed)] = abs(forward["final_mean_loss"] - reverse["final_mean_loss"])
            max_order_delta = max(paired.values())
            by_split_arm[f"{split}:{arm}"] = {
                "trial_count": len(subset),
                "mean_primary_improvement": mean_improvement,
                "mean_final_loss": mean_final_loss,
                "max_forgetting": max_forgetting,
                "order_deltas": paired,
                "max_order_delta": max_order_delta,
                "all_hard_guards_pass": all(
                    item["hard_guards"]["forgetting"]
                    and item["hard_guards"]["checkpoint_restore"]
                    and item["hard_guards"]["complete_stage_coverage"]
                    for item in subset
                )
                and max_order_delta <= MAX_ORDER_DELTA,
            }
    tune = {arm: by_split_arm[f"tune:{arm}"] for arm in ARMS}
    locked_arm = min(ARMS, key=lambda arm: (tune[arm]["mean_final_loss"], ARMS.index(arm)))
    assessment = by_split_arm[f"assessment:{locked_arm}"]
    disposition = (
        "SyntheticCandidate"
        if assessment["all_hard_guards_pass"] and assessment["mean_primary_improvement"] > 0.0
        else "NoCandidate"
    )
    return {
        "by_split_arm": by_split_arm,
        "prediction_lock": {
            "selection_split": "tune",
            "locked_arm": locked_arm,
            "selection_metric": "mean_final_loss",
        },
        "disposition": disposition,
    }


def run_synthetic_campaign() -> dict[str, Any]:
    trials = [
        _run_trial(arm, split, seed, order_seed, direction)
        for split in SPLITS
        for arm in ARMS
        for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS)
        for direction in ORDER_DIRECTIONS
    ]
    result: dict[str, Any] = {
        "state_slice": STATE_SLICE,
        "schema_version": SCHEMA_VERSION,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "source": {
            "url": UPSTREAM_URL,
            "commit": UPSTREAM_COMMIT,
            "model_config": MODEL_CONFIG,
        },
        "corpus": {
            "kind": "deterministic_exact_synthetic",
            "domains": list(DOMAINS),
            "splits": list(SPLITS),
            "corpus_digest": digest({"state_slice": STATE_SLICE, "domains": DOMAINS, "splits": SPLITS}),
        },
        "arms": list(ARMS),
        "replicate_seeds": list(REPLICATE_SEEDS),
        "order_seeds": list(ORDER_SEEDS),
        "training_executed": False,
        "model_loaded": False,
        "inference_executed": False,
        "network_access": False,
        "trials": trials,
    }
    result["summary"] = _summary(trials)
    result["result_sha256"] = digest({key: value for key, value in result.items() if key != "result_sha256"})
    validate_synthetic_result(result)
    return result


def validate_synthetic_result(result: Mapping[str, Any]) -> None:
    if result.get("state_slice") != STATE_SLICE:
        raise ProtocolError("synthetic result state slice mismatch")
    if result.get("schema_version") != SCHEMA_VERSION:
        raise ProtocolError("synthetic result schema mismatch")
    if result.get("training_executed") or result.get("model_loaded") or result.get("inference_executed"):
        raise ProtocolError("synthetic result claims model execution")
    trials = result.get("trials")
    expected_count = len(SPLITS) * len(ARMS) * len(REPLICATE_SEEDS) * len(ORDER_DIRECTIONS)
    if not isinstance(trials, list) or len(trials) != expected_count:
        raise ProtocolError("synthetic result coverage mismatch")
    expected_trials = {
        (item["arm"], item["split"], item["replicate_seed"], item["order_seed"], item["order_direction"]): item
        for item in trials
    }
    if len(expected_trials) != expected_count:
        raise ProtocolError("synthetic result has duplicate trial identity")
    for identity, observed in expected_trials.items():
        expected_trial = _run_trial(*identity[:2], identity[2], identity[3], identity[4])
        if digest(observed) != digest(expected_trial):
            raise ProtocolError(f"synthetic trial arithmetic mismatch: {identity}")
    expected_summary = _summary(trials)
    if digest(result.get("summary")) != digest(expected_summary):
        raise ProtocolError("synthetic summary arithmetic mismatch")
    if result.get("result_sha256") != digest({key: value for key, value in result.items() if key != "result_sha256"}):
        raise ProtocolError("synthetic result digest mismatch")


def _ensure_external(root: Path) -> Path:
    resolved = root.resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ProtocolError("artifact output must remain outside the repository")
    if resolved.exists():
        raise FileExistsError(f"refusing overwrite of immutable artifact root: {resolved}")
    return resolved


def inspect_source(source_root: Path) -> dict[str, Any]:
    root = source_root.resolve()
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ProtocolError("MiniMind source must remain outside the repository")
    if not root.is_dir():
        raise FileNotFoundError(f"MiniMind source root does not exist: {root}")
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ProtocolError("MiniMind source root is not a git checkout")
    commit = completed.stdout.strip()
    if commit != UPSTREAM_COMMIT:
        raise ProtocolError(f"MiniMind source commit mismatch: {commit}")
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0 or status.stdout:
        raise ProtocolError("MiniMind source checkout is dirty")
    files = []
    for relative in REQUIRED_SOURCE_FILES:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ProtocolError(f"required MiniMind source file missing or symlinked: {relative}")
        files.append({"path": relative, "byte_len": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "state_slice": STATE_SLICE,
        "url": UPSTREAM_URL,
        "commit": commit,
        "checkout": str(root),
        "required_files": files,
    }
    return {"manifest": manifest, "manifest_sha256": digest(manifest)}


def _receipt_payload(receipt: Mapping[str, Any]) -> bytes:
    signed = {key: value for key, value in receipt.items() if key != "signature"}
    return json.dumps(signed, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def validate_execution_receipt(receipt_path: Path) -> str:
    if not receipt_path.is_file():
        raise ProtocolError(f"independent execution receipt missing: {receipt_path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "state_slice",
        "review_packet_path",
        "review_packet_sha256",
        "reviewer_role",
        "reviewer_identity",
        "operator_identity",
        "disposition",
        "signature_algorithm",
        "public_key",
        "signature",
    }
    missing = sorted(required - set(receipt))
    if missing:
        raise ProtocolError(f"execution receipt missing fields: {', '.join(missing)}")
    if receipt["schema_version"] != RECEIPT_SCHEMA_VERSION:
        raise ProtocolError("execution receipt schema mismatch")
    if receipt["state_slice"] != STATE_SLICE or receipt["reviewer_role"] != "independent":
        raise ProtocolError("execution receipt identity or reviewer role mismatch")
    if receipt["reviewer_identity"] == receipt["operator_identity"]:
        raise ProtocolError("operator cannot be the independent reviewer")
    if receipt["disposition"] != "ACCEPTED_FOR_MODEL_EXECUTION":
        raise ProtocolError("execution receipt is not an ACCEPT")
    if receipt["signature_algorithm"] != "Ed25519":
        raise ProtocolError("execution receipt signature algorithm mismatch")
    packet = REVIEW_PACKET_PATH.resolve()
    if Path(receipt["review_packet_path"]).resolve() != packet:
        raise ProtocolError("execution receipt packet path mismatch")
    if receipt["review_packet_sha256"] != sha256_file(packet):
        raise ProtocolError("execution receipt packet digest mismatch")
    try:
        public_key = bytes.fromhex(receipt["public_key"])
        signature = bytes.fromhex(receipt["signature"])
    except (TypeError, ValueError) as error:
        raise ProtocolError("execution receipt key or signature is not hexadecimal") from error
    if len(public_key) != 32 or len(signature) != 64:
        raise ProtocolError("execution receipt Ed25519 key or signature length mismatch")
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as error:
        raise ProtocolError("cryptography is required to verify the execution receipt") from error
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, _receipt_payload(receipt))
    except Exception as error:  # cryptography exposes one verification exception across versions
        raise ProtocolError("execution receipt Ed25519 signature verification failed") from error
    return digest(receipt)


@contextmanager
def _external_import_root(root: Path) -> Iterator[None]:
    root_string = str(root.resolve())
    sys.path.insert(0, root_string)
    try:
        yield
    finally:
        try:
            sys.path.remove(root_string)
        except ValueError:
            pass


def _read_jsonl_texts(path: Path) -> list[str]:
    texts = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict) or not isinstance(payload.get("text"), str) or not payload["text"].strip():
                raise ProtocolError(f"invalid text record at {path}:{line_number}")
            texts.append(payload["text"])
    if not texts:
        raise ProtocolError(f"domain corpus is empty: {path}")
    return texts


def build_corpus_manifest(corpus: Mapping[str, Mapping[str, Path]]) -> dict[str, Any]:
    if set(corpus) != set(DOMAINS):
        raise ProtocolError("corpus domains must exactly match the frozen domain roster")
    domains: dict[str, Any] = {}
    for domain in DOMAINS:
        entries = corpus[domain]
        if set(entries) != set(SPLITS):
            raise ProtocolError(f"corpus splits must exactly match the frozen roster for {domain}")
        split_manifest = {}
        for split in SPLITS:
            path = Path(entries[split]).resolve()
            if not path.is_file() or path.is_symlink():
                raise ProtocolError(f"corpus file missing or symlinked: {path}")
            if path == REPO_ROOT or REPO_ROOT in path.parents:
                raise ProtocolError(f"corpus file must remain outside the repository: {path}")
            texts = _read_jsonl_texts(path)
            split_manifest[split] = {
                "path": str(path),
                "sha256": sha256_file(path),
                "record_count": len(texts),
            }
        domains[domain] = split_manifest
    manifest = {"state_slice": STATE_SLICE, "domains": domains}
    return {"manifest": manifest, "manifest_sha256": digest(manifest)}


def _load_corpus_manifest(path: Path) -> dict[str, dict[str, Path]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != set(DOMAINS):
        raise ProtocolError("corpus manifest must be a JSON object with the frozen domain roster")
    corpus: dict[str, dict[str, Path]] = {}
    for domain in DOMAINS:
        entries = payload[domain]
        if not isinstance(entries, dict) or set(entries) != set(SPLITS):
            raise ProtocolError(f"corpus manifest splits must match the frozen roster for {domain}")
        corpus[domain] = {split: Path(entries[split]) for split in SPLITS}
    return corpus


def _token_chunks(tokenizer: Any, texts: Sequence[str], max_seq_len: int) -> list[Any]:
    import torch

    chunks = []
    for text in texts:
        ids = tokenizer(text, add_special_tokens=False, truncation=True, max_length=max_seq_len - 2).input_ids
        ids = [tokenizer.bos_token_id, *ids, tokenizer.eos_token_id]
        if len(ids) < 3:
            continue
        values = ids[:max_seq_len]
        values += [tokenizer.pad_token_id] * (max_seq_len - len(values))
        tensor = torch.tensor(values, dtype=torch.long)
        labels = tensor.clone()
        labels[tensor == tokenizer.pad_token_id] = -100
        chunks.append((tensor, labels))
    if not chunks:
        raise ProtocolError("tokenization produced no trainable chunks")
    return chunks


def _train_model_stage(model: Any, tokenizer: Any, texts: Sequence[str], *, device: str, steps: int, learning_rate: float, seed: int) -> None:
    import torch

    torch.manual_seed(seed)
    chunks = _token_chunks(tokenizer, texts, MODEL_CONFIG["max_seq_len"])
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    if not trainable:
        return
    optimizer = torch.optim.AdamW(trainable, lr=learning_rate)
    model.train()
    for step in range(steps):
        input_ids, labels = chunks[step % len(chunks)]
        result = model(input_ids.unsqueeze(0).to(device), labels=labels.unsqueeze(0).to(device))
        loss = result.loss + result.aux_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        optimizer.step()


def _evaluate_bpb(model: Any, tokenizer: Any, texts: Sequence[str], *, device: str) -> float:
    import torch

    chunks = _token_chunks(tokenizer, texts, MODEL_CONFIG["max_seq_len"])
    total_nats = 0.0
    total_bytes = 0
    model.eval()
    with torch.no_grad():
        for input_ids, labels in chunks:
            result = model(input_ids.unsqueeze(0).to(device), labels=labels.unsqueeze(0).to(device))
            valid = int((labels[1:] != -100).sum().item())
            total_nats += float(result.loss.item()) * valid
            total_bytes += len(tokenizer.decode(input_ids.tolist(), skip_special_tokens=True).encode("utf-8"))
    if total_bytes == 0:
        raise ProtocolError("evaluation produced zero UTF-8 bytes")
    return total_nats / math.log(2.0) / total_bytes


def _snapshot_model(model: Any) -> dict[str, Any]:
    return {
        key: value.detach().cpu().clone()
        for key, value in model.state_dict().items()
    }


def _restore_snapshot(model: Any, snapshot: Mapping[str, Any]) -> float:
    model.load_state_dict(snapshot, strict=True)
    return max(
        (
            float(
                (value.detach().cpu() - model.state_dict()[key].detach().cpu())
                .abs()
                .max()
                .item()
            )
            for key, value in snapshot.items()
        ),
        default=0.0,
    )


def _configure_model_parameters(model: Any, *, trainable: bool, lora_only: bool) -> None:
    for name, parameter in model.named_parameters():
        parameter.requires_grad = trainable and (not lora_only or "lora" in name)


def _run_model_trial(
    *,
    arm: str,
    split: str,
    replicate_seed: int,
    order_seed: int,
    direction: str,
    corpus_texts: Mapping[str, Mapping[str, Sequence[str]]],
    model_cls: Any,
    config: Any,
    tokenizer: Any,
    apply_lora_fn: Any,
    torch_module: Any,
    device: str,
    steps_per_stage: int,
) -> dict[str, Any]:
    order = _ordered_domains(order_seed, direction)
    evaluation_texts = {domain: corpus_texts[domain][split] for domain in DOMAINS}

    def new_model(seed: int, *, lora: bool, trainable: bool) -> Any:
        torch_module.manual_seed(seed)
        model = model_cls(config).to(device)
        if lora:
            apply_lora_fn(model)
        _configure_model_parameters(model, trainable=trainable, lora_only=lora)
        return model

    domain_models: dict[str, Any] = {}
    if arm == "domain_adapters":
        base_model = new_model(replicate_seed, lora=False, trainable=False)
        base_snapshot = _snapshot_model(base_model)
        for domain_index, domain in enumerate(DOMAINS):
            domain_model = new_model(replicate_seed, lora=False, trainable=False)
            _restore_snapshot(domain_model, base_snapshot)
            torch_module.manual_seed(replicate_seed + 10_000 + domain_index)
            apply_lora_fn(domain_model)
            _configure_model_parameters(domain_model, trainable=True, lora_only=True)
            domain_models[domain] = domain_model

        def evaluate(domain: str) -> float:
            return _evaluate_bpb(domain_models[domain], tokenizer, evaluation_texts[domain], device=device)

        base_evaluation_model = base_model
    else:
        model = new_model(
            replicate_seed,
            lora=arm == "sequential_lora",
            trainable=arm != "untouched",
        )

        def evaluate(domain: str) -> float:
            return _evaluate_bpb(model, tokenizer, evaluation_texts[domain], device=device)

        base_evaluation_model = model

    base_domain_bpb = {
        domain: _evaluate_bpb(base_evaluation_model, tokenizer, evaluation_texts[domain], device=device)
        for domain in DOMAINS
    }
    base_mean_bpb = sum(base_domain_bpb.values()) / len(DOMAINS)
    learned_bpb: dict[str, float] = {}
    stage_metrics: list[dict[str, Any]] = []
    restore_errors: list[float] = []

    for stage_index, domain in enumerate(order, start=1):
        if arm == "domain_adapters":
            train_texts = corpus_texts[domain]["fit"]
            train_model = domain_models[domain]
            train_seed = replicate_seed + 10_000 + DOMAINS.index(domain)
        else:
            train_model = model
            if arm == "joint_oracle":
                train_texts = sum((corpus_texts[item]["fit"] for item in DOMAINS), ())
            elif arm == "sequential_replay":
                prior = order[: stage_index - 1]
                train_texts = sum((corpus_texts[item]["fit"] for item in (domain, *prior)), ())
            else:
                train_texts = corpus_texts[domain]["fit"]
            train_seed = replicate_seed + stage_index

        if arm != "untouched":
            _train_model_stage(
                train_model,
                tokenizer,
                train_texts,
                device=device,
                steps=steps_per_stage,
                learning_rate=1e-5 if arm not in {"sequential_lora", "domain_adapters"} else 1e-4,
                seed=train_seed,
            )

        if arm == "domain_adapters":
            snapshots = {item: _snapshot_model(domain_models[item]) for item in DOMAINS}
            restore_errors.extend(
                _restore_snapshot(domain_models[item], snapshots[item]) for item in DOMAINS
            )
        else:
            restore_errors.append(_restore_snapshot(model, _snapshot_model(model)))

        domain_bpb = {item: evaluate(item) for item in DOMAINS}
        learned_bpb.setdefault(domain, domain_bpb[domain])
        max_forgetting = max(
            (max(0.0, domain_bpb[item] - learned_bpb[item]) for item in learned_bpb),
            default=0.0,
        )
        stage_metrics.append(
            {
                "stage_index": stage_index,
                "domain": domain,
                "domain_bpb": domain_bpb,
                "mean_bpb": sum(domain_bpb.values()) / len(DOMAINS),
                "max_forgetting": max_forgetting,
                "update_units": steps_per_stage,
            }
        )

    final_domain_bpb = {domain: evaluate(domain) for domain in DOMAINS}
    final_mean_bpb = sum(final_domain_bpb.values()) / len(DOMAINS)
    checkpoint_error = max(restore_errors, default=0.0)
    return {
        "arm": arm,
        "split": split,
        "replicate_seed": replicate_seed,
        "order_seed": order_seed,
        "order_direction": direction,
        "domain_order": list(order),
        "stage_metrics": stage_metrics,
        "base_mean_loss": base_mean_bpb,
        "final_mean_loss": final_mean_bpb,
        "primary_improvement": base_mean_bpb - final_mean_bpb,
        "max_forgetting": max(item["max_forgetting"] for item in stage_metrics),
        "compute_units": steps_per_stage * len(DOMAINS),
        "checkpoint_restore_max_abs_error": checkpoint_error,
        "hard_guards": {
            "forgetting": max(item["max_forgetting"] for item in stage_metrics) <= MAX_FORGETTING,
            "checkpoint_restore": checkpoint_error <= MAX_CHECKPOINT_ERROR,
            "complete_stage_coverage": len(stage_metrics) == len(DOMAINS),
        },
    }


def run_model_campaign(
    *,
    output: Path,
    source_root: Path,
    execution_receipt: Path,
    corpus: Mapping[str, Mapping[str, Path]],
    device: str = "cpu",
    steps_per_stage: int = 1,
) -> dict[str, Any]:
    """Run the real MiniMind path after independent authorization."""

    if steps_per_stage <= 0:
        raise ProtocolError("steps_per_stage must be positive")
    root = _ensure_external(output)
    receipt_sha256 = validate_execution_receipt(execution_receipt)
    source = inspect_source(source_root)
    corpus_manifest = build_corpus_manifest(corpus)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    root.mkdir(parents=True)

    with _external_import_root(source_root):
        import torch
        from transformers import AutoTokenizer
        from model.model_minimind import MiniMindConfig, MiniMindForCausalLM
        from model.model_lora import apply_lora

        tokenizer = AutoTokenizer.from_pretrained(str(source_root / "model"), local_files_only=True)
        config = MiniMindConfig(
            hidden_size=MODEL_CONFIG["hidden_size"],
            num_hidden_layers=MODEL_CONFIG["num_hidden_layers"],
            use_moe=MODEL_CONFIG["use_moe"],
            vocab_size=MODEL_CONFIG["vocab_size"],
        )
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise ProtocolError("requested CUDA device is unavailable")
        corpus_texts = {
            domain: {split: tuple(_read_jsonl_texts(Path(corpus[domain][split]))) for split in SPLITS}
            for domain in DOMAINS
        }
        trials = [
            _run_model_trial(
                arm=arm,
                split=split,
                replicate_seed=replicate_seed,
                order_seed=order_seed,
                direction=direction,
                corpus_texts=corpus_texts,
                model_cls=MiniMindForCausalLM,
                config=config,
                tokenizer=tokenizer,
                apply_lora_fn=apply_lora,
                torch_module=torch,
                device=device,
                steps_per_stage=steps_per_stage,
            )
            for split in SPLITS
            for arm in MODEL_ARMS
            for replicate_seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS)
            for direction in ORDER_DIRECTIONS
        ]

    contract = {
        "state_slice": STATE_SLICE,
        "schema_version": SCHEMA_VERSION,
        "protocol": PROTOCOL,
        "claim_ceiling": MODEL_CLAIM_CEILING,
        "source": source,
        "corpus": corpus_manifest,
        "execution_receipt_sha256": receipt_sha256,
        "model_config": MODEL_CONFIG,
        "arms": list(MODEL_ARMS),
        "network_access": False,
        "training_executed": True,
        "model_loaded": True,
        "inference_executed": True,
        "device": device,
        "steps_per_stage": steps_per_stage,
        "trials": trials,
        "summary": _summary(trials),
    }
    contract["contract_sha256"] = digest(contract)
    write_json(root / "contract.json", contract)
    return contract


def write_synthetic_campaign(output: Path, source_root: Path = DEFAULT_SOURCE_ROOT) -> dict[str, Any]:
    root = _ensure_external(output)
    source = inspect_source(source_root)
    result = run_synthetic_campaign()
    contract = {
        "state_slice": STATE_SLICE,
        "schema_version": SCHEMA_VERSION,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "source": source,
        "corpus": result["corpus"],
        "arms": list(ARMS),
        "training_executed": False,
        "model_loaded": False,
        "inference_executed": False,
        "network_access": False,
    }
    contract["contract_sha256"] = digest(contract)
    root.mkdir(parents=True)
    write_json(root / "source-manifest.json", source)
    write_json(root / "contract.json", contract)
    write_json(root / "result.json", result)
    return {"root": str(root), "contract": contract, "result": result}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic-output", type=Path)
    mode.add_argument("--model-output", type=Path)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--execution-receipt", type=Path)
    parser.add_argument("--corpus-manifest", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--steps-per-stage", type=int, default=1)
    args = parser.parse_args()
    if args.synthetic_output is not None:
        payload = write_synthetic_campaign(args.synthetic_output, args.source)
        summary = payload["result"]["summary"]
    else:
        if args.execution_receipt is None or args.corpus_manifest is None:
            parser.error("--model-output requires --execution-receipt and --corpus-manifest")
        payload = run_model_campaign(
            output=args.model_output,
            source_root=args.source,
            execution_receipt=args.execution_receipt,
            corpus=_load_corpus_manifest(args.corpus_manifest),
            device=args.device,
            steps_per_stage=args.steps_per_stage,
        )
        summary = payload["summary"]
    print(
        json.dumps(
            {
                "state_slice": STATE_SLICE,
                "disposition": summary["disposition"],
                "root": str(args.synthetic_output or args.model_output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
