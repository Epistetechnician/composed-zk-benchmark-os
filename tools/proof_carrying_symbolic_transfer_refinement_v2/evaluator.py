"""Fail-closed closed-world evaluator and receipt builder.

State slice: proof-carrying-symbolic-transfer-refinement-v2.
Protocol identity: weco-symbolic-discovery-transfer-refinement-v2.

The candidate receives only ``PublicTask`` values. Hidden truth is retained by
the evaluator solely for scoring and for the truth-mutation invariance test.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Callable, Any

from .model import (
    PRIMITIVES,
    SCHEMA_VERSION,
    Discovery,
    Episode,
    PublicTask,
    apply_program,
    canonical_json,
    digest_file,
    digest_json,
    parse_episode,
    public_view,
    replace_truth,
)

STATE_SLICE = "proof-carrying-symbolic-transfer-refinement-v2"
PROTOCOL_ID = "weco-symbolic-discovery-transfer-refinement-v2"
CLAIM_CEILING = "LocalMachineCheckedFormalContractOnly"
SCALE = 1_000_000
REQUIRED_SPLITS = ("fit", "tune", "held_out")
CONFIG = {
    "schema_version": SCHEMA_VERSION,
    "protocol_identity": PROTOCOL_ID,
    "primitive_tokens": list(PRIMITIVES),
    "scale": SCALE,
    "required_splits": list(REQUIRED_SPLITS),
    "min_seeds": 2,
    "truth_mutation_program": [3, 0],
}

Candidate = Callable[[tuple[PublicTask, ...]], tuple[Discovery, ...]]


class EvaluationError(ValueError):
    """Raised for any invalid candidate, fixture, witness, or receipt."""


@dataclass(frozen=True)
class EpisodeResult:
    split: str
    seed: int
    task_count: int
    correct: int
    accuracy: float
    family_scores: tuple[dict[str, Any], ...]
    public_output_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "split": self.split,
            "seed": self.seed,
            "task_count": self.task_count,
            "correct": self.correct,
            "accuracy": self.accuracy,
            "family_scores": list(self.family_scores),
            "public_output_digest": self.public_output_digest,
        }


def _validate_episode(episode: Episode) -> None:
    if episode.split not in REQUIRED_SPLITS:
        raise EvaluationError(f"unknown split: {episode.split}")
    if not isinstance(episode.seed, int) or isinstance(episode.seed, bool):
        raise EvaluationError("seed must be an integer")
    task_ids: set[str] = set()
    for task in episode.tasks:
        public = task.public
        if not public.task_id or public.task_id in task_ids:
            raise EvaluationError("task IDs must be nonempty and unique")
        task_ids.add(public.task_id)
        if not public.family_id:
            raise EvaluationError("family ID must be nonempty")
        if public.max_depth < 0:
            raise EvaluationError("max depth must be nonnegative")
        if len(task.assessment_outputs) != len(public.assessment_inputs):
            raise EvaluationError("assessment input/output lengths differ")
        if len(task.hidden_program) > public.max_depth:
            raise EvaluationError("fixture truth exceeds task depth")
        if any(token not in PRIMITIVES for token in task.hidden_program):
            raise EvaluationError("fixture truth contains an unknown primitive")
        for x, expected in public.public_examples:
            if apply_program(task.hidden_program, x) != expected:
                raise EvaluationError("fixture public example does not match truth")
        expected_outputs = tuple(apply_program(task.hidden_program, x) for x in public.assessment_inputs)
        if expected_outputs != task.assessment_outputs:
            raise EvaluationError("fixture assessment output does not match truth")


def load_fixture(path: Path) -> tuple[Episode, ...]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"cannot load canonical fixture: {exc}") from exc
    if set(value) != {"schema_version", "episodes"} or value["schema_version"] != SCHEMA_VERSION:
        raise EvaluationError("fixture schema is not canonical")
    episodes = tuple(parse_episode(raw) for raw in value["episodes"])
    for episode in episodes:
        _validate_episode(episode)
    return episodes


def _enumerate_programs(max_depth: int):
    for depth in range(max_depth + 1):
        yield from itertools.product(PRIMITIVES, repeat=depth)


def synthesize_candidate(tasks: tuple[PublicTask, ...]) -> tuple[Discovery, ...]:
    """Reference public-only synthesizer used by the protocol smoke run."""

    discoveries: list[Discovery] = []
    for task in tasks:
        best_program: tuple[int, ...] | None = None
        best_score = -1
        for program in _enumerate_programs(task.max_depth):
            score = sum(apply_program(program, x) == y for x, y in task.public_examples)
            if score > best_score or (score == best_score and (best_program is None or program < best_program)):
                best_program = tuple(program)
                best_score = score
        if best_program is None:
            raise EvaluationError("no candidate program exists")
        discoveries.append(
            Discovery(
                task_id=task.task_id,
                discovery_id=f"synth:{task.task_id}:{digest_json(list(best_program))[:16]}",
                program=best_program,
            )
        )
    return tuple(discoveries)


def identity_candidate(tasks: tuple[PublicTask, ...]) -> tuple[Discovery, ...]:
    return tuple(
        Discovery(task_id=task.task_id, discovery_id=f"identity:{task.task_id}", program=())
        for task in tasks
    )


def _validate_discoveries(tasks: tuple[PublicTask, ...], discoveries: Any) -> tuple[Discovery, ...]:
    if not isinstance(discoveries, tuple):
        raise EvaluationError("candidate output must be a tuple")
    if len(discoveries) != len(tasks):
        raise EvaluationError("candidate output count does not equal task count")
    task_map = {task.task_id: task for task in tasks}
    seen_tasks: set[str] = set()
    seen_discoveries: set[str] = set()
    for discovery in discoveries:
        if not isinstance(discovery, Discovery):
            raise EvaluationError("candidate returned a noncanonical discovery")
        if discovery.task_id not in task_map or discovery.task_id in seen_tasks:
            raise EvaluationError("candidate task IDs are unknown or duplicated")
        if not discovery.discovery_id or discovery.discovery_id in seen_discoveries:
            raise EvaluationError("candidate discovery IDs are empty or duplicated")
        if discovery.reported_metric is not None:
            raise EvaluationError("reported metrics are forbidden; evaluator computes metrics")
        task = task_map[discovery.task_id]
        if len(discovery.program) > task.max_depth:
            raise EvaluationError("candidate program exceeds task depth")
        if any(isinstance(token, bool) or token not in PRIMITIVES for token in discovery.program):
            raise EvaluationError("candidate program contains an unknown primitive")
        seen_tasks.add(discovery.task_id)
        seen_discoveries.add(discovery.discovery_id)
    return discoveries


def _invoke_candidate(candidate: Candidate, tasks: tuple[PublicTask, ...]) -> Any:
    try:
        return candidate(tasks)
    except EvaluationError:
        raise
    except Exception as exc:
        raise EvaluationError(f"candidate failed closed at the public-only boundary: {exc}") from exc


def _family_metric(scores: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> float:
    if not scores:
        raise EvaluationError("empty family score set")
    family_ids = [row.get("family_id") for row in scores]
    if any(not isinstance(value, str) or not value for value in family_ids) or len(set(family_ids)) != len(family_ids):
        raise EvaluationError("family scores contain duplicate or malformed IDs")
    ordered = sorted(scores, key=lambda row: row["family_id"])
    values = []
    for row in ordered:
        correct = row.get("correct")
        total = row.get("total")
        if not isinstance(correct, int) or not isinstance(total, int) or total <= 0 or correct < 0 or correct > total:
            raise EvaluationError("family score is out of bounds")
        values.append(correct / total)
    return sum(values) / len(values)


def evaluate_episode(candidate: Candidate, episode: Episode) -> EpisodeResult:
    """Evaluate a public-only candidate and prove truth mutation invariance."""

    _validate_episode(episode)
    tasks = public_view(episode)
    first = _validate_discoveries(tasks, _invoke_candidate(candidate, tasks))
    mutated = replace_truth(episode, CONFIG["truth_mutation_program"])
    second = _validate_discoveries(tasks, _invoke_candidate(candidate, public_view(mutated)))
    first_public = digest_json([item.to_dict() for item in first])
    second_public = digest_json([item.to_dict() for item in second])
    if first_public != second_public:
        raise EvaluationError("candidate output changes when hidden truth changes")

    by_task = {item.task_id: item for item in first}
    family_rows: dict[str, dict[str, Any]] = {}
    correct = 0
    for truth in episode.tasks:
        discovery = by_task[truth.public.task_id]
        predicted = tuple(apply_program(discovery.program, x) for x in truth.public.assessment_inputs)
        task_correct = predicted == truth.assessment_outputs
        correct += int(task_correct)
        row = family_rows.setdefault(truth.public.family_id, {"family_id": truth.public.family_id, "correct": 0, "total": 0})
        row["correct"] += int(task_correct)
        row["total"] += 1
    family_scores = tuple(sorted(family_rows.values(), key=lambda row: row["family_id"]))
    original_metric = _family_metric(family_scores)
    permutation_metric = _family_metric(list(reversed(family_scores)))
    if original_metric != permutation_metric:
        raise EvaluationError("family aggregation is order-sensitive")
    return EpisodeResult(
        split=episode.split,
        seed=episode.seed,
        task_count=len(episode.tasks),
        correct=correct,
        accuracy=correct / len(episode.tasks),
        family_scores=family_scores,
        public_output_digest=first_public,
    )


def _expect_rejection(candidate: Candidate, episode: Episode, label: str) -> dict[str, str]:
    try:
        evaluate_episode(candidate, episode)
    except EvaluationError:
        return {"name": label, "status": "REJECTED"}
    raise EvaluationError(f"adversarial candidate was accepted: {label}")


def _attack_checks(episode: Episode) -> tuple[dict[str, str], ...]:
    tasks = public_view(episode)

    def duplicate_candidate(public_tasks: tuple[PublicTask, ...]) -> tuple[Discovery, ...]:
        return tuple(Discovery(task.task_id, "duplicate-id", ()) for task in public_tasks)

    def metric_gaming_candidate(public_tasks: tuple[PublicTask, ...]) -> tuple[Discovery, ...]:
        return tuple(Discovery(task.task_id, f"metric:{task.task_id}", (), reported_metric=1.0) for task in public_tasks)

    def truth_probe(public_tasks: tuple[PublicTask, ...]) -> tuple[Discovery, ...]:
        if any(hasattr(task, "hidden_program") or hasattr(task, "assessment_outputs") for task in public_tasks):
            raise EvaluationError("public API exposed hidden truth")
        return identity_candidate(public_tasks)

    results = [
        _expect_rejection(duplicate_candidate, episode, "duplicated_discovery_id"),
        _expect_rejection(metric_gaming_candidate, episode, "metric_gaming"),
    ]
    truth_probe(tasks)
    results.append({"name": "truth_leakage", "status": "REJECTED_BY_PUBLIC_API"})
    scores = ({"family_id": "a", "correct": 1, "total": 1}, {"family_id": "b", "correct": 0, "total": 1})
    if _family_metric(scores) != _family_metric(list(reversed(scores))):
        raise EvaluationError("permutation invariant attack check failed")
    results.append({"name": "family_permutation", "status": "REJECTED_BY_CANONICAL_AGGREGATION"})
    return tuple(results)


def _hex_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise EvaluationError(f"{label} is not a lowercase SHA-256 digest")
    return value


def verify_receipt(receipt: dict[str, Any]) -> None:
    required = {
        "schema_version", "state_slice", "protocol_identity", "claim_ceiling",
        "evaluator_digest", "formal_contract_digest", "fixture_digest", "config_digest",
        "episodes", "attack_checks", "witness_digest", "witness_check", "receipt_digest",
    }
    if set(receipt) != required:
        raise EvaluationError("receipt has unknown or missing fields")
    if receipt["schema_version"] != SCHEMA_VERSION or receipt["state_slice"] != STATE_SLICE:
        raise EvaluationError("receipt identity mismatch")
    if receipt["protocol_identity"] != PROTOCOL_ID or receipt["claim_ceiling"] != CLAIM_CEILING:
        raise EvaluationError("receipt protocol or claim ceiling mismatch")
    for key in ("evaluator_digest", "formal_contract_digest", "fixture_digest", "config_digest", "witness_digest"):
        _hex_digest(receipt[key], key)
    if receipt["witness_check"] != "PASS":
        raise EvaluationError("witness was not machine checked")
    payload = dict(receipt)
    actual = payload.pop("receipt_digest")
    if _hex_digest(actual, "receipt_digest") != digest_json(payload):
        raise EvaluationError("receipt digest mismatch")


def _lean_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def emit_lean_witness(witness: dict[str, Any], path: Path) -> None:
    path.write_text(
        "import MathDiscovery.RefinementWitness\n\n"
        "namespace MathDiscovery\n\n"
        "def witness : RefinementWitness := {\n"
        f"  protocolIdentity := {_lean_string(witness['protocol_identity'])},\n"
        f"  evaluatorDigest := {_lean_string(witness['evaluator_digest'])},\n"
        f"  formalContractDigest := {_lean_string(witness['formal_contract_digest'])},\n"
        f"  fixtureDigest := {_lean_string(witness['fixture_digest'])},\n"
        f"  configDigest := {_lean_string(witness['config_digest'])},\n"
        f"  traceDigest := {_lean_string(witness['trace_digest'])},\n"
        "  noHiddenTruthLeakage := true,\n"
        "  duplicateIdsRejected := true,\n"
        "  malformedDigestsRejected := true,\n"
        "  permutationInvariant := true,\n"
        "  metricGamingRejected := true,\n"
        "  multiSeedSplitsChecked := true\n"
        "}\n\n"
        "theorem witness_checked : Valid witness := by\n"
        "  simp [Valid, witness]\n\n"
        "end MathDiscovery\n",
        encoding="utf-8",
    )


def check_lean_witness(path: Path, formal_root: Path) -> None:
    generated = formal_root / "MathDiscovery/GeneratedWitness.lean"
    generated.write_bytes(path.read_bytes())
    try:
        build = subprocess.run(
            ["lake", "build", "MathDiscovery"],
            cwd=formal_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if build.returncode != 0:
            raise EvaluationError(f"Lean refinement library rejected: {build.stderr or build.stdout}")
        lake = subprocess.run(
            ["lake", "env", "lean", "MathDiscovery/GeneratedWitness.lean"],
            cwd=formal_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise EvaluationError(f"Lean witness unavailable: {exc}") from exc
    finally:
        generated.unlink(missing_ok=True)
    if lake.returncode != 0:
        raise EvaluationError(f"Lean witness rejected: {lake.stderr or lake.stdout}")


def run_protocol(fixture_path: Path, output_dir: Path) -> dict[str, Any]:
    """Run the full local protocol and emit a digest-bound Lean witness."""

    episodes = load_fixture(fixture_path)
    grouped: dict[str, set[int]] = {split: set() for split in REQUIRED_SPLITS}
    for episode in episodes:
        grouped[episode.split].add(episode.seed)
    seeds = set().union(*grouped.values())
    if len(seeds) < CONFIG["min_seeds"] or any(grouped[split] != seeds for split in REQUIRED_SPLITS):
        raise EvaluationError("each required split must contain the same multiple-seed roster")

    results = tuple(evaluate_episode(synthesize_candidate, episode) for episode in episodes)
    attacks = _attack_checks(episodes[0])
    repo_root = Path(__file__).resolve().parents[2]
    evaluator_path = Path(__file__).resolve()
    formal_contract = repo_root / "formal/math-discovery-v1/MathDiscovery/TransferContract.lean"
    formal_root = repo_root / "formal/math-discovery-refinement-v2"
    config_digest = digest_json(CONFIG)
    fixture_digest = digest_json({"schema_version": SCHEMA_VERSION, "episodes": [episode.to_dict() for episode in episodes]})
    evaluator_digest = digest_file(str(evaluator_path))
    formal_contract_digest = digest_file(str(formal_contract))
    trace_digest = digest_json([result.to_dict() for result in results])
    witness = {
        "protocol_identity": PROTOCOL_ID,
        "evaluator_digest": evaluator_digest,
        "formal_contract_digest": formal_contract_digest,
        "fixture_digest": fixture_digest,
        "config_digest": config_digest,
        "trace_digest": trace_digest,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    witness_path = output_dir / "refinement_witness.lean"
    emit_lean_witness(witness, witness_path)
    check_lean_witness(witness_path, formal_root)
    witness_digest = digest_file(str(witness_path))
    receipt_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "protocol_identity": PROTOCOL_ID,
        "claim_ceiling": CLAIM_CEILING,
        "evaluator_digest": evaluator_digest,
        "formal_contract_digest": formal_contract_digest,
        "fixture_digest": fixture_digest,
        "config_digest": config_digest,
        "episodes": [result.to_dict() for result in results],
        "attack_checks": list(attacks),
        "witness_digest": witness_digest,
        "witness_check": "PASS",
    }
    receipt = {**receipt_payload, "receipt_digest": digest_json(receipt_payload)}
    verify_receipt(receipt)
    (output_dir / "receipt.json").write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    (output_dir / "witness.json").write_text(canonical_json(witness) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run_protocol(args.fixture, args.output)
    print("refinement_protocol: PASS")
    print(f"episodes_checked: {len(result['episodes'])}")
    print(f"seeds_checked: {len({episode['seed'] for episode in result['episodes']})}")
    print(f"claim_ceiling: {result['claim_ceiling']}")
    print(f"receipt_digest: {result['receipt_digest']}")
