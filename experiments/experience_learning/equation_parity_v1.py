"""Multi-step IDBD/TIDBD equation-fidelity receipt.

State slice: ``oaklab-experience-learning-equation-parity-v1``.
The oracle transitions are independent functions in ``equations.py`` and are
compared against the learner implementation without importing learner code
into the oracle.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Mapping

from .equations import idbd_published_step, idbd_reference_step, tidbd_published_step, tidbd_reference_step
from .learners import IDBDLearner, TIDBDLearner
from .types import Experience


STATE_SLICE = "oaklab-experience-learning-equation-parity-v1"
SCHEMA_VERSION = "oaklab.experience-learning.equation-parity.v1"
IDBD_SOURCE = "https://cdn.aaai.org/AAAI/1992/AAAI92-027.pdf"
TIDBD_SOURCE = "https://arxiv.org/abs/1804.03334"
BOUND_MIN = -8.0
BOUND_MAX = 1.0


def _canonical(value):
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()
                if key != "result_digest"}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def _digest(payload: Mapping) -> str:
    encoded = json.dumps(_canonical(dict(payload)), sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _max_abs(values_a, values_b) -> float:
    return max((abs(float(a) - float(b)) for a, b in zip(values_a, values_b)), default=0.0)


def _idbd_case() -> dict:
    sequence = [Experience(step, (0.08 * ((step % 5) - 2), 0.06 * ((step % 7) - 3)),
                            0.12 * math.sin(step / 5.0)) for step in range(64)]
    learner = IDBDLearner(2, meta_step=0.01, initial_step=0.03)
    weights, beta, h = list(learner.weights), list(learner.beta), list(learner.h)
    max_diff = 0.0
    bound_hits = 0
    for item in sequence:
        expected = idbd_published_step(weights, beta, h, item.features, item.target,
                                        meta_step=0.01)
        learner.observe(item)
        weights, beta, h = expected
        max_diff = max(max_diff, _max_abs(learner.weights, weights),
                       _max_abs(learner.beta, beta), _max_abs(learner.h, h))
        bound_hits += sum(value <= BOUND_MIN or value >= BOUND_MAX for value in learner.beta)
    bounded_expected = [math.log(0.03)] * 2
    bounded_weights, bounded_h = [0.0] * 2, [0.0] * 2
    for item in sequence:
        bounded_weights, bounded_expected, bounded_h = idbd_reference_step(
            bounded_weights, bounded_expected, bounded_h, item.features, item.target,
            meta_step=0.01, beta_min=BOUND_MIN, beta_max=BOUND_MAX)
    bounded_diff = max(_max_abs(learner.weights, bounded_weights),
                       _max_abs(learner.beta, bounded_expected),
                       _max_abs(learner.h, bounded_h))
    return {"status": "passed" if max_diff <= 1e-12 and bounded_diff <= 1e-12 else "failed",
            "equation": "IDBD Algorithm pseudocode; unbounded core plus declared beta bound",
            "source": IDBD_SOURCE, "steps": len(sequence), "max_abs_diff": max_diff,
            "bounded_variant_max_abs_diff": bounded_diff, "bound_hits": bound_hits,
            "bounds": [BOUND_MIN, BOUND_MAX]}


def _tidbd_case() -> dict:
    sequence = []
    for step in range(64):
        features = (0.05 * ((step % 5) - 2), 0.04 * ((step % 7) - 3))
        next_features = (features[1], features[0]) if step % 9 else (0.0, 0.0)
        sequence.append(Experience(step, features, 0.0, reward=0.04 * ((step % 4) - 1.5),
                                   next_features=next_features, done=step % 16 == 15))
    learner = TIDBDLearner(2, gamma=0.9, trace_decay=0.8, meta_step=0.01, initial_step=0.03)
    weights, beta, h, eligibility = list(learner.weights), list(learner.beta), list(learner.h), list(learner.e)
    max_diff = 0.0
    bound_hits = 0
    for item in sequence:
        expected = tidbd_published_step(weights, beta, h, eligibility, item.features,
                                        item.reward, item.next_features, item.done,
                                        gamma=0.9, trace_decay=0.8, meta_step=0.01)
        learner.observe(item)
        weights, beta, h, eligibility = expected
        max_diff = max(max_diff, _max_abs(learner.weights, weights),
                       _max_abs(learner.beta, beta), _max_abs(learner.h, h),
                       _max_abs(learner.e, eligibility))
        bound_hits += sum(value <= BOUND_MIN or value >= BOUND_MAX for value in learner.beta)
    bounded_weights, bounded_beta = [0.0] * 2, [math.log(0.03)] * 2
    bounded_h, bounded_e = [0.0] * 2, [0.0] * 2
    for item in sequence:
        bounded_weights, bounded_beta, bounded_h, bounded_e = tidbd_reference_step(
            bounded_weights, bounded_beta, bounded_h, bounded_e, item.features,
            item.reward, item.next_features, item.done, gamma=0.9, trace_decay=0.8,
            meta_step=0.01, beta_min=BOUND_MIN, beta_max=BOUND_MAX)
    bounded_diff = max(_max_abs(learner.weights, bounded_weights),
                       _max_abs(learner.beta, bounded_beta), _max_abs(learner.h, bounded_h),
                       _max_abs(learner.e, bounded_e))
    return {"status": "passed" if max_diff <= 1e-12 and bounded_diff <= 1e-12 else "failed",
            "equation": "TIDBD(lambda) Algorithm 1; unbounded core plus declared beta bound",
            "source": TIDBD_SOURCE, "steps": len(sequence), "max_abs_diff": max_diff,
            "bounded_variant_max_abs_diff": bounded_diff, "bound_hits": bound_hits,
            "bounds": [BOUND_MIN, BOUND_MAX]}


def run_parity() -> dict:
    cases = {"idbd": _idbd_case(), "tidbd": _tidbd_case()}
    payload = {
        "schema_version": SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "protocol": "independent multi-step oracle parity; published unbounded core and declared bounded deployment variant",
        "references": {"idbd": IDBD_SOURCE, "tidbd": TIDBD_SOURCE},
        "bounds": {"beta_min": BOUND_MIN, "beta_max": BOUND_MAX,
                   "description": "implementation stabilization, not part of published core"},
        "cases": cases,
        "status": "PASSED" if all(case["status"] == "passed" for case in cases.values()) else "FAILED",
    }
    payload["result_digest"] = _digest(payload)
    return payload


def write_result(result: Mapping, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    write_result(run_parity(), args.output)
