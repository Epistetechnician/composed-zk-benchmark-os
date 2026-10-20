"""Astral V49 neuron-level causal lane + Goodfire lanes B-D (hermetic core).

State slices: astral-neuron-level-causal-lane-v49-execution,
instrument-validity-gate-v1, caduceus-mechanism-vs-behavior-lane-v1,
continual-learning-recursive-generalization-diagnostic-v1.
Claim ceiling: LocalDevelopmentUnreviewed. No I/O, no network; the model is an
injected backend so the same code runs on a fake or a cached local checkpoint.
"""
import hashlib
import json
import math
import random

CEILING = "LocalDevelopmentUnreviewed"
FORBIDDEN = ("sota", "breakthrough", "proven", "production", "accepted evidence", "introspection")


class V49Error(ValueError):
    pass


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_text(*texts):
    for t in texts:
        if any(f in str(t).lower() for f in FORBIDDEN):
            raise V49Error("claim text rejected")


def split_docs(doc_ids, seed):
    ids = sorted(set(doc_ids))
    if len(ids) != len(doc_ids) or len(ids) < 6:
        raise V49Error("need >=6 unique documents")
    rng = random.Random(seed)
    rng.shuffle(ids)
    n = len(ids) // 3
    return {"fit": ids[:n], "tune": ids[n:2 * n], "assess": ids[2 * n:]}


def select_units(scores, k):
    """Fit-only selection: top-k |score| units; ties by unit id."""
    if k < 1 or k > len(scores):
        raise V49Error("bad k")
    return sorted(sorted(scores, key=lambda u: (-abs(scores[u]), u))[:k])


def matched_pool(magnitude, selected, layer_of, pct_bins=10):
    """Per-selected-unit candidate lists matched on layer and magnitude percentile bin."""
    by_layer = {}
    for u in magnitude:
        by_layer.setdefault(layer_of[u], []).append(u)
    ranked = {}
    for l, us in by_layer.items():
        us = sorted(us, key=lambda x: (magnitude[x], x))
        ranked[l] = (us, {u: i for i, u in enumerate(us)})
    sel = set(selected)
    cand = {}
    for u in selected:
        us, rk = ranked[layer_of[u]]
        n = len(us)
        b = rk[u] * pct_bins // n
        lo, hi = -(-b * n // pct_bins), -(-(b + 1) * n // pct_bins)
        pool = [p for p in us[lo:hi] if p not in sel]
        if not pool:
            raise V49Error("no matched controls for %r" % (u,))
        cand[u] = pool
    return cand


def draw_controls(cand, selected, draws, seed):
    if draws < 1000:
        raise V49Error("draws>=1000")
    rng = random.Random(seed)
    out = []
    for _ in range(draws):
        s, used = [], set()
        for u in selected:
            opts = [c for c in cand[u] if c not in used] or cand[u]
            c = rng.choice(opts)
            used.add(c)
            s.append(c)
        out.append(sorted(s))
    return out


def holm(pvals, alpha):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    rej = [False] * len(pvals)
    for rank, i in enumerate(order):
        if pvals[i] <= alpha / (len(pvals) - rank):
            rej[i] = True
        else:
            break
    return rej


def one_sided_p(effect, control_effects):
    return (1 + sum(1 for c in control_effects if c >= effect)) / (1 + len(control_effects))


def run_v49(backend, cfg):
    """backend: object with docs(), scores(fit_docs), magnitude(), layers(), effect(units, docs)."""
    check_text(cfg.get("note", ""))
    sp = backend.split() if hasattr(backend, "split") else split_docs(backend.docs(), cfg["seed"])
    scores = backend.scores(sp["fit"])
    sel = select_units(scores, cfg["k"])
    lock = digest({"selected": sel, "cfg": cfg, "split": sp})  # prediction lock before assess effects
    cand = matched_pool(backend.magnitude(), sel, backend.layers())
    controls = draw_controls(cand, sel, cfg["draws"], cfg["seed"] + 1)
    results = {}
    for part in ("tune", "assess"):
        eff = backend.effect(sel, sp[part])
        ce = [backend.effect(c, sp[part]) for c in controls]
        gap = eff - sum(ce) / len(ce)
        results[part] = {"effect": eff, "p": one_sided_p(eff, ce), "gap": gap}
    # unchanged controls: text-only/shuffled/constant must not separate
    ctl = {}
    for name in ("text_only", "shuffled", "constant"):
        e = backend.control_effect(name, sel, sp["assess"])
        ctl[name] = {"effect": e, "separates": e >= cfg["min_effect"]}
    rej = holm([results["tune"]["p"], results["assess"]["p"]], cfg["alpha"])
    ok = (all(rej) and results["assess"]["gap"] >= cfg["min_effect"]
          and not any(c["separates"] for c in ctl.values()))
    return {"status": "Candidate" if ok else "NoCandidate", "lock": lock, "selected": sel,
            "results": results, "controls": ctl, "holm_reject": rej, "ceiling": CEILING}


# ---- Lane B: instrument-validity gate -------------------------------------
def instrument_validity_gate(readouts, instrument):
    """readouts: dict name->callable(values)->float. instrument: dict of checks."""
    v = instrument["values"]
    fails = []
    lo, hi = min(v), max(v)
    if not (math.isfinite(lo) and math.isfinite(hi)) or lo == hi:
        fails.append("activation_shape")
    if not (any(x > 0 for x in v) and any(x < 0 for x in v)):
        fails.append("both_sign")
    vals = [f(v) for f in readouts.values()]
    if len(readouts) < 2 or max(vals) - min(vals) > instrument["lens_tol"]:
        fails.append("lens_sensitivity")
    if not (instrument["positive_control"] and instrument["near_miss_rejected"]):
        fails.append("positive_control_near_miss")
    if not instrument["known_bad_fails"]:
        fails.append("known_bad_instrument")
    return {"status": "InstrumentValid" if not fails else "InstrumentNotValid", "fails": fails,
            "ceiling": CEILING}


# ---- Lane C: descriptive matched-random ablation delta ---------------------
def lane_c_report(behavior_gates, effect, control_effects):
    gap = effect - sum(control_effects) / len(control_effects)
    return {"descriptive_only": True, "is_gate": False, "is_score": False,
            "behavior_gates": dict(behavior_gates), "ablation_delta": gap, "ceiling": CEILING}


# ---- Lane D: read-only neighborhood diagnostic ----------------------------
def lane_d_diagnostic(checkpoints, adjacent):
    """checkpoints: list of dict input->activation of an updated unit; adjacent: set of inputs."""
    rows = []
    for ck in checkpoints:
        tot = sum(abs(a) for a in ck.values()) or 1.0
        loc = sum(abs(a) for i, a in ck.items() if i in adjacent) / tot
        rows.append(loc)
    return {"descriptive_only": True, "locality_by_checkpoint": rows,
            "grows_local": len(rows) > 1 and rows[-1] > rows[0], "ceiling": CEILING,
            "claims_retention_or_improvement": False}
