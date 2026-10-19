"""Hermetic fixture-only matched-random-control validator (no model, no I/O)."""
import math
import random

SLICE = "matched-control-validity-fixtures-v1"
CLAIM_CEILING = "Level1LocalReplay"
FORBIDDEN = ("sota", "breakthrough", "proven", "production", "accepted evidence")


class ControlError(ValueError):
    pass


def validate_request(req):
    keys = {"effect", "unit_set", "layer", "draws", "seed", "min_effect", "alpha", "note"}
    if not isinstance(req, dict) or set(req) - keys:
        raise ControlError("unknown or malformed fields")
    for k in ("effect", "unit_set", "layer", "draws", "seed", "min_effect", "alpha"):
        if k not in req:
            raise ControlError("missing " + k)
    if not math.isfinite(req["effect"]) or not math.isfinite(req["min_effect"]):
        raise ControlError("nonfinite")
    if req["draws"] < 1000 or req["min_effect"] <= 0 or not 0 < req["alpha"] < 1:
        raise ControlError("draws>=1000, min_effect>0, 0<alpha<1 required")
    if not req["unit_set"] or len(set(req["unit_set"])) != len(req["unit_set"]):
        raise ControlError("unit_set empty or duplicated")
    note = str(req.get("note", "")).lower()
    if any(f in note for f in FORBIDDEN):
        raise ControlError("claim text rejected")


def fake_effect(units, layer):
    """Deterministic synthetic stand-in for a model effect."""
    return sum(((u * 2654435761 + layer * 97) % 1000) / 1000.0 for u in units) / len(units)


def matched_draws(n_units, layer, pool, draws, seed):
    rng = random.Random(seed)
    return [fake_effect(rng.sample(pool, n_units), layer) for _ in range(draws)]


def compare(effect, controls, min_effect, alpha):
    n = len(controls)
    p = (1 + sum(1 for c in controls if c >= effect)) / (1 + n)
    gap = effect - sum(controls) / n
    ok = gap >= min_effect and p <= alpha
    return {"p": p, "gap": gap, "status": "SeparatesFromControl" if ok else "InstrumentNotValid",
            "slice": SLICE, "claim_ceiling": CLAIM_CEILING}


def shape_summary(values):
    s = sorted(values)
    pct = {q: s[min(len(s) - 1, int(q / 100 * len(s)))] for q in (5, 25, 50, 75, 95)}
    return {"percentiles": pct, "degenerate": s[0] == s[-1]}


def run(req, pool):
    validate_request(req)
    controls = matched_draws(len(req["unit_set"]), req["layer"], pool, req["draws"], req["seed"])
    out = compare(req["effect"], controls, req["min_effect"], req["alpha"])
    out["shape"] = shape_summary(controls)
    return out
