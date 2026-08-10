#!/usr/bin/env python3
"""V24 hybrid-instrument capability-tier replication on the nemotron_h 4B tier.

Stage A develops and validates a controlled MLX forward seam for the cached
hybrid Mamba/attention checkpoint. Stage B, authorized only by a certified
instrument, runs the unchanged V22/V23 three-way discrimination protocol.
Protocol: docs/research/astral-self-modeling/44-hybrid-instrument-capability-tier-v24.md
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import mlx.core as mx
import numpy as np
from mlx_lm import load
from mlx_lm.models.base import create_attention_mask, create_ssm_mask

HERE = Path(__file__).resolve()
V22_PATH = HERE.parents[1] / "astral-activation-discrimination-v22" / "v22.py"
MODEL_PATH = Path(
    "/Users/shaanp/.lmstudio/models/mlx_lm_lora/mesh-brain-nemotron-3-nano-4b"
)
SITES = (10, 21, 32)
HIDDEN_SIZE = 3136
EXPECTED_LAYER_COUNT = 42
EXPECTED_PATTERN = "M-M-M-MM-M-M*-M-M*-M-M-M*-M-M-MM*-MMM-M-M-"
EXPECTED_MODEL_TYPE = "nemotron_h"
BEHAVIORAL_SILENCE_LOGIT_SHIFT = 1e-3
CONCEPTS = (
    "alcove", "bramble", "cinder", "driftwood", "ember", "fern", "gable", "heather",
    "inlet", "juniper", "kettle", "lagoon",
    "obsidian", "pebble", "quartz", "thicket",
)
V22_FROZEN_CONCEPTS = (
    "cedar", "violin", "glacier", "lantern", "meadow", "copper", "harbor", "velvet",
    "canyon", "marble", "orchid", "compass",
    "willow", "tunnel", "saffron", "anchor",
)
V23_FROZEN_CONCEPTS = (
    "birch", "cello", "fjord", "beacon", "prairie", "bronze", "marina", "satin",
    "ravine", "granite", "lilac", "astrolabe",
    "poplar", "subway", "turmeric", "mooring",
)
CLAIM = "LocalDevelopmentHybridInstrumentCapabilityTierReplication"

if set(CONCEPTS) & set(V22_FROZEN_CONCEPTS):
    raise RuntimeError("ConceptCollisionWithV22")
if set(CONCEPTS) & set(V23_FROZEN_CONCEPTS):
    raise RuntimeError("ConceptCollisionWithV23")
if len(set(CONCEPTS)) != len(CONCEPTS):
    raise RuntimeError("ConceptDuplicateWithinV24")


def import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


V22 = import_path("astral_v22_core_for_v24", V22_PATH)
V22.SITES = SITES
V22.CONCEPTS = CONCEPTS
V22.CLAIM = CLAIM
V17 = V22.V17


class NemotronRunner:
    """Controlled hybrid forward seam mirroring NemotronHModel.__call__.

    The native cache-less prefill passes the string sentinel "causal" to full
    attention blocks and None to Mamba blocks; MLP-only blocks ignore masks.
    The controlled loop reproduces that dispatch exactly and adds residual
    injection at the final position after the selected site.
    """

    def __init__(self) -> None:
        self.model, self.tokenizer = load(str(MODEL_PATH))
        args = self.model.args
        if getattr(args, "model_type", None) != EXPECTED_MODEL_TYPE:
            raise RuntimeError("NotRunModelTypeMismatch")
        if args.num_hidden_layers != EXPECTED_LAYER_COUNT or args.hidden_size != HIDDEN_SIZE:
            raise RuntimeError("NotRunModelRevisionMismatch")
        self.pattern = list(args.hybrid_override_pattern)
        if "".join(self.pattern) != EXPECTED_PATTERN:
            raise RuntimeError("InstrumentPatternMismatch")
        self.layers = self.model.backbone.layers
        if len(self.layers) != EXPECTED_LAYER_COUNT:
            raise RuntimeError("InstrumentPatternMismatch:layer-count")
        if any(layer.block_type != self.pattern[index] for index, layer in enumerate(self.layers)):
            raise RuntimeError("InstrumentPatternMismatch:block-type-map")
        for site in SITES:
            if site >= len(self.pattern):
                raise RuntimeError(f"InstrumentPatternMismatch:site-uncovered:{site}")

    def token_id(self, completion: str) -> int:
        ids = self.tokenizer.encode(completion, add_special_tokens=False)
        if len(ids) != 1:
            raise RuntimeError(f"InstrumentTokenizerMismatch:{completion!r}:{ids}")
        return ids[0]

    def tokenizer_gate(self) -> dict[str, Any]:
        return {
            token: self.tokenizer.encode(token, add_special_tokens=False)
            for token in V22.TOKENS
        }

    def _forward(
        self, prompt: str, site: int | None = None,
        direction: np.ndarray | None = None, strength: float = 0.0,
        capture: bool = False,
    ) -> tuple[np.ndarray, dict[int, np.ndarray]]:
        ids = mx.array([self.tokenizer.encode(prompt, add_special_tokens=False)])
        hidden = self.model.backbone.embeddings(ids)
        attn_mask = create_attention_mask(hidden, None)
        ssm_mask = create_ssm_mask(hidden, None)
        captured: dict[int, np.ndarray] = {}
        for index, layer in enumerate(self.layers):
            mask = attn_mask if layer.block_type == "*" else ssm_mask
            hidden = layer(hidden, mask=mask, cache=None)
            if index == site and strength != 0.0:
                if direction is None or direction.shape != (HIDDEN_SIZE,):
                    raise ValueError(f"direction must have shape ({HIDDEN_SIZE},)")
                steered = hidden[:, -1:, :] + mx.array(direction)[None, None, :] * strength
                hidden = mx.concatenate([hidden[:, :-1, :], steered], axis=1)
            if capture and index in SITES:
                mx.eval(hidden)
                captured[index] = np.asarray(
                    hidden[0, -1, :].astype(mx.float16), dtype=np.float16
                )
        hidden = self.model.backbone.norm_f(hidden)
        logits = self.model.lm_head(hidden)
        mx.eval(logits)
        return np.asarray(logits[0, -1, :].astype(mx.float32), dtype=np.float32), captured

    def forward(self, prompt: str) -> tuple[np.ndarray, dict[int, np.ndarray]]:
        return self._forward(prompt)

    def forward_steered(
        self, prompt: str, site: int | None = None,
        direction: np.ndarray | None = None, strength: float = 0.0,
        capture: bool = False,
    ) -> tuple[np.ndarray, dict[int, np.ndarray]]:
        return self._forward(prompt, site, direction, strength, capture)


def write_manifest(root: Path) -> None:
    V17.write_json(root / "manifest.json", {
        "files": {
            str(path.relative_to(root)): V17.digest_file(path)
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        }
    })


def integrity(
    runner: NemotronRunner, trials: list[Any],
    directions: dict[str, dict[int, np.ndarray]],
) -> dict[str, Any]:
    sample = trials[0].prompt
    ids = mx.array([runner.tokenizer.encode(sample, add_special_tokens=False)])
    native = np.asarray(runner.model(ids)[0, -1, :].astype(mx.float32), dtype=np.float32)
    controlled, _ = runner.forward_steered(sample)
    repeated, _ = runner.forward_steered(sample)
    zero, _ = runner.forward_steered(
        sample, site=SITES[0], direction=directions[CONCEPTS[0]][SITES[0]],
        strength=0.0,
    )
    return {
        "native_parity_max_abs_error": float(np.max(np.abs(native - controlled))),
        "repeat_max_abs_error": float(np.max(np.abs(controlled - repeated))),
        "zero_strength_max_abs_error": float(np.max(np.abs(controlled - zero))),
        "completion_token_ids": {token: runner.token_id(token) for token in V22.TOKENS},
        "activation_none_prompt_identity": all(
            next(row.prompt for row in trials if row.concept == concept and row.wrapper == wrapper and row.condition == "activation")
            == next(row.prompt for row in trials if row.concept == concept and row.wrapper == wrapper and row.condition == "none")
            for concept in CONCEPTS for wrapper in range(4)
        ),
    }


def behavioral_effect(rows: list[dict[str, Any]], site: int, strength: float) -> dict[str, Any]:
    """Paired activation-versus-none three-token logit shift for one sweep cell.

    Derived from the fit rows the protocol already computes: activation and
    no-intervention trials share byte-identical prompts, so the per-pair shift
    measures whether the injection moved the report distribution at all.
    """
    pairs: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for row in rows:
        if row["condition"] in ("activation", "none"):
            pairs.setdefault((row["concept"], row["wrapper"]), {})[row["condition"]] = row
    shifts: list[float] = []
    top1_changes = 0
    for (_, _), pair in sorted(pairs.items()):
        activation_logits = np.asarray(pair["activation"]["logits"], dtype=np.float64)
        none_logits = np.asarray(pair["none"]["logits"], dtype=np.float64)
        shifts.append(float(np.max(np.abs(activation_logits - none_logits))))
        if int(np.argmax(activation_logits)) != int(np.argmax(none_logits)):
            top1_changes += 1
    pair_count = len(shifts)
    max_shift = float(np.max(shifts))
    return {
        "site": site,
        "strength": strength,
        "pair_count": pair_count,
        "mean_abs_logit_shift": float(np.mean(shifts)),
        "max_abs_logit_shift": max_shift,
        "top1_token_change_rate": top1_changes / pair_count,
        "silent": bool(
            max_shift < BEHAVIORAL_SILENCE_LOGIT_SHIFT and top1_changes == 0
        ),
    }


def instrument_metadata(runner: NemotronRunner) -> dict[str, Any]:
    tokenizer_gate = runner.tokenizer_gate()
    for token, ids in tokenizer_gate.items():
        if len(ids) != 1:
            raise RuntimeError(f"InstrumentTokenizerMismatch:{token!r}:{ids}")
    return {
        "model_type": EXPECTED_MODEL_TYPE,
        "num_hidden_layers": EXPECTED_LAYER_COUNT,
        "hidden_size": HIDDEN_SIZE,
        "hybrid_override_pattern": "".join(runner.pattern),
        "sites": list(SITES),
        "site_layer_types": {str(site): runner.pattern[site] for site in SITES},
        "seam": "manual-hybrid-loop-v1",
        "mask_dispatch": {"attention": "causal-sentinel", "mamba": "none", "mlp": "ignored"},
        "compute_dtype": "bfloat16",
        "capture_dtype_conversion": "bfloat16-to-float16-in-mlx",
        "logit_dtype_conversion": "bfloat16-to-float32-in-mlx",
        "report_token_ids": {token: runner.token_id(token) for token, ids in tokenizer_gate.items()},
    }


def prepare(root: Path) -> None:
    if root.exists():
        raise RuntimeError("output root already exists")
    root.mkdir(parents=True)
    runner, trials = NemotronRunner(), V22.build_trials()
    V17.write_json(root / "corpus.json", [V22.asdict(row) for row in trials])
    V17.write_json(root / "model-inventory.json", V17.model_inventory(MODEL_PATH))
    V17.write_json(root / "instrument.json", instrument_metadata(runner))
    directions, direction_state = V22.build_directions(runner)
    np.savez_compressed(
        root / "directions.npz",
        **{f"{concept}__{site}": vector for concept, values in directions.items() for site, vector in values.items()},
    )
    V17.write_json(root / "direction-state.json", direction_state)
    checks = integrity(runner, trials, directions)
    V17.write_json(root / "integrity.json", checks)
    sweep, behavioral = [], []
    for site in SITES:
        for strength in V22.STRENGTHS:
            rows = V22.evaluate(runner, trials, directions, "fit", site, strength)
            sweep.append({"site": site, "strength": strength, "metrics": V22.metrics(rows)})
            behavioral.append(behavioral_effect(rows, site, strength))
    selected = sorted(
        sweep,
        key=lambda row: (-row["metrics"]["macro_balanced_accuracy"], row["strength"], row["site"]),
    )[0]
    selected_behavioral = next(
        cell for cell in behavioral
        if cell["site"] == selected["site"] and cell["strength"] == selected["strength"]
    )
    V17.write_json(root / "fit-sweep.json", sweep)
    V17.write_json(root / "behavioral-effect.json", behavioral)
    V17.write_json(root / "selected-configuration.json", {"site": selected["site"], "strength": selected["strength"]})
    if selected_behavioral["silent"]:
        V17.write_json(root / "result.json", {
            "classification": "InstrumentBehaviorallySilent",
            "confirmation": "NotAuthorized", "stage_0c": "Blocked",
            "stage_1": "BlockedByStage0C", "claim_ceiling": CLAIM,
            "assessment_unopened": True,
            "selected_configuration": {"site": selected["site"], "strength": selected["strength"]},
            "selected_behavioral_effect": selected_behavioral,
        })
        write_manifest(root)
        return
    tune_rows = V22.evaluate(runner, trials, directions, "tune", selected["site"], selected["strength"])
    tune_metrics = V22.metrics(tune_rows)
    V17.write_json(root / "tune-results.json", {"metrics": tune_metrics, "rows": tune_rows})
    qualified = (
        checks["native_parity_max_abs_error"] == 0
        and checks["repeat_max_abs_error"] == 0
        and checks["zero_strength_max_abs_error"] == 0
        and checks["activation_none_prompt_identity"]
        and selected["metrics"]["macro_balanced_accuracy"] >= 0.45
        and tune_metrics["macro_balanced_accuracy"] >= 0.40
        and tune_metrics["condition_recall"]["activation"] >= 0.25
        and tune_metrics["activation_vs_none_accuracy"] >= 0.60
    )
    qualification = {
        "qualified": qualified, "selected_fit_metrics": selected["metrics"],
        "tune_metrics": tune_metrics, **checks,
    }
    V17.write_json(root / "qualification.json", qualification)
    if not qualified:
        V17.write_json(root / "result.json", {
            "classification": "NotRunHybridInstrumentQualification",
            "confirmation": "NotAuthorized", "stage_0c": "Blocked",
            "stage_1": "BlockedByStage0C", "claim_ceiling": CLAIM,
            "assessment_unopened": True,
        })
        write_manifest(root)
        return
    inputs = (
        "corpus.json", "model-inventory.json", "instrument.json", "directions.npz",
        "direction-state.json", "integrity.json", "behavioral-effect.json",
        "fit-sweep.json", "selected-configuration.json", "tune-results.json",
        "qualification.json",
    )
    V17.write_json(root / "configuration-lock.json", {
        "assessment_results_absent": not (root / "assessment-results.json").exists(),
        "inputs": {name: V17.digest_file(root / name) for name in inputs},
        "source_identity": {
            "v24_sha256": V17.digest_file(HERE),
            "validator_sha256": V17.digest_file(HERE.with_name("validator_v24.py")),
            "v22_shared_core_sha256": V17.digest_file(V22_PATH),
            "v17_shared_core_sha256": V17.digest_file(V22.V17_PATH),
        },
    })


def load_directions(root: Path) -> dict[str, dict[int, np.ndarray]]:
    archive = np.load(root / "directions.npz")
    return {concept: {site: archive[f"{concept}__{site}"] for site in SITES} for concept in CONCEPTS}


def assess(root: Path) -> None:
    lock_path = root / "configuration-lock.json"
    if not lock_path.exists() or (root / "assessment-results.json").exists():
        raise RuntimeError("invalid assessment ordering")
    config = json.loads((root / "selected-configuration.json").read_text())
    runner, trials = NemotronRunner(), V22.build_trials()
    rows = V22.evaluate(runner, trials, load_directions(root), "assessment", config["site"], config["strength"])
    result_metrics, interval = V22.metrics(rows), V22.bootstrap(rows)
    observed = (
        result_metrics["macro_balanced_accuracy"] >= 0.50
        and result_metrics["condition_recall"]["activation"] >= 0.35
        and result_metrics["activation_vs_none_accuracy"] >= 0.65
        and interval["lower_95"] > 0
        and min(result_metrics["wrapper_accuracy"].values()) >= 0.40
    )
    V17.write_json(root / "assessment-results.json", {"rows": rows, "metrics": result_metrics, "bootstrap": interval})
    V17.write_json(root / "result.json", {
        "classification": "HybridCapabilityTierReplicationObserved" if observed else "HybridCapabilityTierReplicationNoCandidate",
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C", "claim_ceiling": CLAIM,
        "metrics": result_metrics, "bootstrap": interval,
        "configuration_lock_sha256": V17.digest_file(lock_path),
    })
    write_manifest(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "assess"))
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    try:
        (prepare if args.phase == "prepare" else assess)(args.root.resolve())
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "completed", "phase": args.phase, "root": str(args.root.resolve())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
