#!/usr/bin/env python3
"""V23 fresh-concept Llama 1B perturbation-discrimination replication."""

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
from mlx_lm.models.base import create_attention_mask

HERE = Path(__file__).resolve()
V22_PATH = HERE.parents[1] / "astral-activation-discrimination-v22" / "v22.py"
MODEL_PATH = Path("/Users/shaanp/.lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit")
SITES = (3, 7, 11)
CONCEPTS = (
    "birch", "cello", "fjord", "beacon", "prairie", "bronze", "marina", "satin",
    "ravine", "granite", "lilac", "astrolabe",
    "poplar", "subway", "turmeric", "mooring",
)
CLAIM = "LocalDevelopmentCapabilityTierPerturbationReplication"


def import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


V22 = import_path("astral_v22_core_for_v23", V22_PATH)
V22.SITES = SITES
V22.CONCEPTS = CONCEPTS
V22.CLAIM = CLAIM
V17 = V22.V17


class LlamaRunner:
    def __init__(self) -> None:
        self.model, self.tokenizer = load(str(MODEL_PATH))
        self.layers = self.model.model.layers
        if len(self.layers) != 16 or self.model.args.hidden_size != 2048:
            raise RuntimeError("NotRunModelRevisionMismatch")

    def token_id(self, completion: str) -> int:
        ids = self.tokenizer.encode(completion, add_special_tokens=False)
        if len(ids) != 1:
            raise RuntimeError(f"NotRunCompletionNotSingleToken:{completion!r}:{ids}")
        return ids[0]

    def _forward(
        self, prompt: str, site: int | None = None,
        direction: np.ndarray | None = None, strength: float = 0.0,
        capture: bool = False,
    ) -> tuple[np.ndarray, dict[int, np.ndarray]]:
        ids = mx.array([self.tokenizer.encode(prompt, add_special_tokens=False)])
        hidden = self.model.model.embed_tokens(ids)
        mask = create_attention_mask(hidden, None)
        captured: dict[int, np.ndarray] = {}
        for index, layer in enumerate(self.layers):
            hidden = layer(hidden, mask, None)
            if index == site and strength != 0.0:
                if direction is None or direction.shape != (2048,):
                    raise ValueError("direction must have shape (2048,)")
                steered = hidden[:, -1:, :] + mx.array(direction)[None, None, :] * strength
                hidden = mx.concatenate([hidden[:, :-1, :], steered], axis=1)
            if capture and index in SITES:
                mx.eval(hidden)
                captured[index] = np.asarray(hidden[0, -1, :], dtype=np.float16)
        hidden = self.model.model.norm(hidden)
        logits = (
            self.model.model.embed_tokens.as_linear(hidden)
            if self.model.args.tie_word_embeddings
            else self.model.lm_head(hidden)
        )
        mx.eval(logits)
        return np.asarray(logits[0, -1, :], dtype=np.float32), captured

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
    runner: LlamaRunner, trials: list[Any],
    directions: dict[str, dict[int, np.ndarray]],
) -> dict[str, Any]:
    sample = trials[0].prompt
    ids = mx.array([runner.tokenizer.encode(sample, add_special_tokens=False)])
    native = np.asarray(runner.model(ids)[0, -1, :], dtype=np.float32)
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


def prepare(root: Path) -> None:
    if root.exists():
        raise RuntimeError("output root already exists")
    root.mkdir(parents=True)
    runner, trials = LlamaRunner(), V22.build_trials()
    V17.write_json(root / "corpus.json", [V22.asdict(row) for row in trials])
    V17.write_json(root / "model-inventory.json", V17.model_inventory(MODEL_PATH))
    directions, direction_state = V22.build_directions(runner)
    np.savez_compressed(
        root / "directions.npz",
        **{f"{concept}__{site}": vector for concept, values in directions.items() for site, vector in values.items()},
    )
    V17.write_json(root / "direction-state.json", direction_state)
    checks = integrity(runner, trials, directions)
    V17.write_json(root / "integrity.json", checks)
    sweep = []
    for site in SITES:
        for strength in V22.STRENGTHS:
            rows = V22.evaluate(runner, trials, directions, "fit", site, strength)
            sweep.append({"site": site, "strength": strength, "metrics": V22.metrics(rows)})
    selected = sorted(
        sweep,
        key=lambda row: (-row["metrics"]["macro_balanced_accuracy"], row["strength"], row["site"]),
    )[0]
    tune_rows = V22.evaluate(runner, trials, directions, "tune", selected["site"], selected["strength"])
    tune_metrics = V22.metrics(tune_rows)
    V17.write_json(root / "fit-sweep.json", sweep)
    V17.write_json(root / "selected-configuration.json", {"site": selected["site"], "strength": selected["strength"]})
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
            "classification": "NotRunCapabilityTierPerturbationQualification",
            "confirmation": "NotAuthorized", "stage_0c": "Blocked",
            "stage_1": "BlockedByStage0C", "claim_ceiling": CLAIM,
            "assessment_unopened": True,
        })
        write_manifest(root)
        return
    inputs = (
        "corpus.json", "model-inventory.json", "directions.npz", "direction-state.json",
        "integrity.json", "fit-sweep.json", "selected-configuration.json",
        "tune-results.json", "qualification.json",
    )
    V17.write_json(root / "configuration-lock.json", {
        "assessment_results_absent": not (root / "assessment-results.json").exists(),
        "inputs": {name: V17.digest_file(root / name) for name in inputs},
        "source_identity": {
            "v23_sha256": V17.digest_file(HERE),
            "validator_sha256": V17.digest_file(HERE.with_name("validator_v23.py")),
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
    runner, trials = LlamaRunner(), V22.build_trials()
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
        "classification": "CapabilityTierPerturbationReplicationObserved" if observed else "CapabilityTierPerturbationReplicationNoCandidate",
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
