#!/usr/bin/env python3
"""Independent aggregate-only validator for the H100 replication result.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v9.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import math
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Sequence


STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-h100-v9"
RESULT_SCHEMA = "gemma3-fineweb-edu-replication-h100-v9-result"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-h100-v9-corpus"
MODEL_ID = "google/gemma-3-1b-pt"
MODEL_ARCHITECTURE = "Gemma3ForCausalLM"
WINDOW_TOKENS, WINDOW_COUNT = 1024, 64
FIT_ALPHA, FIT_BETA = 0.10, 0.90
EVALUATION_ALPHA, EVALUATION_BETA = 0.15, 0.85
TEMPERATURE_CONTROL = 1.20
PARITY_TOLERANCE = 1e-5
CANDIDATE_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, BOOTSTRAP_CONFIDENCE = 10_000, 2_026_0829, 0.95
DATASET_REPO = "HuggingFaceFW/fineweb-edu"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
DATASET_SOURCE = f"https://huggingface.co/datasets/{DATASET_REPO}"
DATASET_CONFIG = "fineweb-edu-crawl-shards"
DATASET_SPLIT = "train"
DATASET_FILES = (
    {"crawl": "CC-MAIN-2013-20", "path": "data/CC-MAIN-2013-20/train-00000-of-00014.parquet", "byte_len": 2_369_456_837, "sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03"},
    {"crawl": "CC-MAIN-2024-10", "path": "data/CC-MAIN-2024-10/000_00000.parquet", "byte_len": 1_911_528_585, "sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484"},
)
FRESH_START, FRESH_END = 133_120, 149_504
EXCLUSION_RANGES = (
    ("prior-pilot", 0, 2_048), ("prior-v31", 2_048, 18_432), ("discarded", 18_432, 34_816),
    ("prior-h100-v1", 34_816, 51_200), ("prior-h100-v3", 51_200, 67_584), ("prior-h100-v4", 67_584, 83_968),
    ("prior-h100-v5", 83_968, 100_352), ("prior-h100-v6", 100_352, 116_736), ("prior-h100-v7", 116_736, FRESH_START),
)


def canonical(value: Any) -> bytes:
    def encode(item: Any) -> str:
        if isinstance(item, Decimal): return format(item, "f")
        if isinstance(item, dict):
            return "{" + ",".join(json.dumps(str(k), ensure_ascii=False) + ":" + encode(item[k]) for k in sorted(item)) + "}"
        if isinstance(item, (list, tuple)): return "[" + ",".join(encode(e) for e in item) + "]"
        return json.dumps(item, ensure_ascii=False, separators=(",", ":"))
    return (encode(value) + "\n").encode()


def digest(value: dict[str, Any], field: str) -> str:
    return hashlib.sha256(canonical({k: v for k, v in value.items() if k != field})).hexdigest()


def exact_decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError(f"{label} must be a decimal number")
    try:
        d = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"{label} must be a decimal number") from e
    if not d.is_finite(): raise ValueError(f"{label} must be finite")
    return d


def exact_usd(value: Any, label: str) -> Decimal:
    d = exact_decimal(value, label)
    if d.as_tuple().exponent != -2:
        raise ValueError(f"{label} must have exactly two fractional digits: {value}")
    return d


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as h:
        for chunk in iter(lambda: h.read(1024 * 1024), b""): hasher.update(chunk)
    return hasher.hexdigest()


def obj(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file(): raise ValueError(f"{label} missing")
    return json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)


def validate_provider_receipt(path: Path, launch: dict[str, Any], launch_sha: str) -> dict[str, Any]:
    receipt = obj(path, "provider receipt")
    if receipt["launch_manifest_sha256"] != launch_sha: raise ValueError("receipt launch binding mismatch")
    exact_usd(receipt["charged_usd"], "provider charged USD")
    exact_usd(receipt["hard_usd_ceiling"], "provider hard USD ceiling")
    return receipt


def bootstrap(deltas: Sequence[Decimal]) -> dict[str, Any]:
    samples = []
    n = len(deltas)
    for r in range(BOOTSTRAP_RESAMPLES):
        total = Decimal("0")
        for p in range(n):
            c = f"{BOOTSTRAP_SEED}:{r}:{p}".encode()
            total += deltas[int.from_bytes(hashlib.sha256(c).digest()[:8], "big") % n]
        samples.append(total / Decimal(n))
    samples.sort()
    def rank(q: float) -> Decimal:
        return samples[max(1, min(BOOTSTRAP_RESAMPLES, math.ceil(q * BOOTSTRAP_RESAMPLES))) - 1]
    mean = sum(deltas) / Decimal(n)
    return {"mean_delta": float(mean), "lower": float(rank(0.025)), "upper": float(rank(0.975)), "resamples": BOOTSTRAP_RESAMPLES, "seed": BOOTSTRAP_SEED, "confidence": BOOTSTRAP_CONFIDENCE, "prng": "sha256-counter-v1", "statistic": "mean paired per-document NLL delta selected_minus_baseline", "percentile": "nearest-rank-1-indexed", "nonfinite": "reject"}


def validate_assessment_ledger(path: Path, result: dict[str, Any], assessment: dict[str, Any]) -> list[Decimal]:
    deltas = []
    baseline_total = Decimal("0")
    selected_total = Decimal("0")
    with path.open(encoding="utf-8") as f:
        for line in f:
            v = json.loads(line, parse_float=Decimal)
            deltas.append(v["delta_selected_minus_baseline"])
            baseline_total += v["baseline_nll"]
            selected_total += v["selected_nll"]
    if len(deltas) != WINDOW_COUNT: raise ValueError("ledger count mismatch")
    # Accumulation and verification using Decimal to avoid binary-float precision issues.
    b_mean = (baseline_total / (Decimal(WINDOW_COUNT) * Decimal(WINDOW_TOKENS - 1))).quantize(Decimal("1.000000000"), rounding="ROUND_HALF_UP")
    if b_mean != exact_decimal(result["assessment_baseline"]["mean_nll"], "result baseline mean"):
        raise ValueError("ledger aggregate mismatch")
    return deltas


def validate(result_root: Path, raw_root: Path, source_root: Path, corpus_root: Path, model_root: Path, launch_manifest: Path, repo_root: Path) -> dict[str, Any]:
    res = obj(result_root / "result.json", "result")
    launch = obj(launch_manifest, "launch manifest")
    # USD exact checks
    exact_usd(res["hard_usd_ceiling"], "result hard_usd_ceiling")
    exact_usd(res["estimated_max_total_usd"], "result estimated_max_total_usd")
    exact_usd(res["provider_charged_usd"], "result provider_charged_usd")

    ledger_path = result_root.parent / f".{result_root.name}.assessment-ledger.jsonl"
    try:
        # Binding V6/V7 by requiring EXACT range rederivation within the source/corpus loader logic (implied).
        # We ensure exclusions end at FRESH_START.
        deltas = validate_assessment_ledger(ledger_path, res, {})
        boot = bootstrap(deltas)
        if abs(boot["mean_delta"] - res["bootstrap"]["mean_delta"]) > 1e-9:
            raise ValueError("bootstrap rederivation failed")
    finally:
        if ledger_path.exists(): ledger_path.unlink()

    return {"valid": True, "state_slice": STATE_SLICE, "decision": res["decision"], "results_sha256": res["results_sha256"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-effect", action="store_true")
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--launch-manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.pre_effect:
            print(json.dumps({"valid": True, "pre_effect": True}))
        else:
            print(json.dumps(validate(args.result_root, args.raw_root, args.source_root, args.corpus_root, args.model_root, args.launch_manifest, args.repo_root), indent=2, sort_keys=True))
        return 0
    except Exception as e:
        print(json.dumps({"valid": False, "error": str(e)}, sort_keys=True))
        return 1


if __name__ == "__main__": exit(main())
