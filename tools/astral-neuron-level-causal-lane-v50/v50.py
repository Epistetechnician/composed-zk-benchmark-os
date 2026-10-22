"""Astral V50 lane core: selection + prediction lock, instrument gate v2, path analysis, spend guard.

State slices: astral-neuron-level-causal-lane-v50-execution, instrument-validity-gate-v2,
neuron-control-lanes-unreviewed-execution-v1. Claim ceiling: LocalDevelopmentUnreviewed.
Pure code: no I/O, no network. The model is an injected backend (fake in tests).
Protocol: docs/research/astral-self-modeling/132-neuron-level-causal-lane-v50-protocol.md
Operationalizations added here and to be frozen in the packet: H2 uses indirect share and
top-2 mediator share, both must beat the matched-random distribution (Holm over the two).
"""
import importlib.util
import os

_p = os.path.join(os.path.dirname(__file__), "..", "astral-neuron-level-causal-lane-v49", "v49.py")
_spec = importlib.util.spec_from_file_location("v49_helpers", _p)
_v49 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v49)
digest, holm, one_sided_p = _v49.digest, _v49.holm, _v49.one_sided_p
matched_pool, draw_controls = _v49.matched_pool, _v49.draw_controls

CEILING = "LocalDevelopmentUnreviewed"
FORBIDDEN = _v49.FORBIDDEN
# Frozen before any data. Changing any value changes FROZEN_DIGEST and fails the tests.
FROZEN = {
    "known_bad_max_frac": 0.10,
    "known_bad_max_abs": 0.05,
    "known_bad_shuffles": 20,
    "min_effect": 0.5,
    "min_draws": 1000,
    "k": 32,
    "layers": 3,
    "top2_min_share": 0.5,
    "spend_cap_usd": 14.00,
}
FROZEN_DIGEST = digest(FROZEN)


class V50Error(ValueError):
    pass


def check_frozen():
    if digest(FROZEN) != FROZEN_DIGEST:
        raise V50Error("frozen thresholds were modified")


def check_text(*texts):
    for t in texts:
        if any(f in str(t).lower() for f in FORBIDDEN):
            raise V50Error("claim text rejected")


# ---- selection + prediction lock ---------------------------------------------
def select_per_layer(scores, layer_of, target_layers, k):
    """Fit-only: top |score| units with a near-equal quota per target layer."""
    if len(target_layers) != FROZEN["layers"] or len(set(target_layers)) != len(target_layers):
        raise V50Error("need exactly %d distinct target layers" % FROZEN["layers"])
    base, extra = divmod(k, len(target_layers))
    quota = {l: base + (1 if i < extra else 0) for i, l in enumerate(sorted(target_layers))}
    sel = []
    for l, q in quota.items():
        units = [u for u in scores if layer_of[u] == l]
        if len(units) < q:
            raise V50Error("layer %r has fewer than %d units" % (l, q))
        sel += sorted(units, key=lambda u: (-abs(scores[u]), u))[:q]
    return sorted(sel)


def make_lock(selected, directions, split, model_id, corpus_digest, code_commit):
    for d in directions.values():
        if d not in (-1, 1):
            raise V50Error("direction must be +1 or -1")
    return digest({"selected": selected, "directions": {str(k): v for k, v in directions.items()},
                   "min_effect": FROZEN["min_effect"], "split": split, "model": model_id,
                   "corpus": corpus_digest, "code": code_commit, "frozen": FROZEN_DIGEST})


def check_lock(lock, selected, directions, split, model_id, corpus_digest, code_commit):
    if make_lock(selected, directions, split, model_id, corpus_digest, code_commit) != lock:
        raise V50Error("prediction lock mismatch")


# ---- instrument gate v2 --------------------------------------------------------
def instrument_gate_v2(backend, selected, scores, docs, controls_p, alpha=0.05):
    """Absolute-effect known-bad rule; no z-score arm. Returns status and per-check detail."""
    check_frozen()
    eff = backend.effect(selected, docs, "margin")
    fails, detail = [], {"selected_effect": eff}
    bad = [backend.known_bad_effect(s, selected, docs) for s in range(FROZEN["known_bad_shuffles"])]
    worst = max(abs(b) for b in bad)
    detail["known_bad_max"] = worst
    if eff < FROZEN["min_effect"] or worst > FROZEN["known_bad_max_frac"] * eff or worst > FROZEN["known_bad_max_abs"]:
        fails.append("known_bad")
    k = len(selected)
    rank = sorted(scores, key=lambda u: (-abs(scores[u]), u))
    pos = backend.effect(sorted(rank[:16 * k]), docs, "margin")
    near = backend.effect(sorted(rank[k:2 * k]), docs, "margin")
    detail.update(positive_control=pos, near_miss=near)
    if not pos > eff:
        fails.append("positive_control")
    if not near < eff:
        fails.append("near_miss")
    vals = backend.activation_values()
    detail["both_signs"] = any(v > 0 for v in vals) and any(v < 0 for v in vals)
    if not detail["both_signs"] or min(vals) == max(vals):
        fails.append("activation_shape")
    lp = backend.effect(selected, docs, "logprob")
    detail["logprob_effect"] = lp
    if not (eff > 0 and lp > 0 and controls_p["margin"] <= alpha and controls_p["logprob"] <= alpha):
        fails.append("two_readouts")
    return {"status": "InstrumentValid" if not fails else "InstrumentNotValid", "fails": fails,
            "detail": detail, "ceiling": CEILING}


# ---- path analysis (H2) ------------------------------------------------------
def path_stats(backend, units, docs):
    total = backend.total_effect(units, docs)
    if total <= 0:
        return None
    ind = total - backend.direct_effect(units, docs)
    if ind <= 0:
        return {"indirect_share": 0.0, "top2_share": 0.0, "mediators": []}
    med = backend.mediators(units, docs)  # component -> share of the indirect effect
    top = sorted(med.items(), key=lambda kv: (-kv[1], kv[0]))[:2]
    return {"indirect_share": ind / total, "top2_share": sum(v for _, v in top),
            "mediators": [n for n, _ in top]}


def path_analysis(backend, selected, controls, docs, alpha=0.05):
    s = path_stats(backend, selected, docs)
    if s is None:
        return {"h2": False, "reason": "no positive total effect", "mechanism_wording_allowed": False}
    cs = [c for c in (path_stats(backend, u, docs) for u in controls) if c is not None]
    if len(cs) < FROZEN["min_draws"] * 0.9:
        return {"h2": False, "reason": "too few valid control draws", "mechanism_wording_allowed": False}
    p_ind = one_sided_p(s["indirect_share"], [c["indirect_share"] for c in cs])
    p_top = one_sided_p(s["top2_share"], [c["top2_share"] for c in cs])
    rej = holm([p_ind, p_top], alpha)
    h2 = all(rej) and s["top2_share"] >= FROZEN["top2_min_share"]
    return {"h2": h2, "stats": s, "p": {"indirect_share": p_ind, "top2_share": p_top},
            "mediators": s["mediators"], "correlational_patching_only": True,
            "mechanism_wording_allowed": h2, "ceiling": CEILING}


# ---- orchestration -------------------------------------------------------------
def run_v50(backend, cfg):
    """One model, one run. No pooling across models: call once per model."""
    check_frozen()
    check_text(cfg.get("note", ""))
    if cfg["draws"] < FROZEN["min_draws"] or cfg["k"] != FROZEN["k"]:
        raise V50Error("draws/k below frozen protocol")
    sp = backend.split()
    scores = backend.scores(sp["fit"])  # fit only
    layer_of = backend.layers()
    sel = select_per_layer(scores, layer_of, cfg["target_layers"], cfg["k"])
    dirs = {u: (1 if scores[u] >= 0 else -1) for u in sel}
    lock = make_lock(sel, dirs, sp, cfg["model_id"], cfg["corpus_digest"], cfg["code_commit"])
    backend.mark_locked(lock)  # tune/assess effects may be read only after this
    cand = matched_pool(backend.magnitude(), sel, layer_of)
    controls = draw_controls(cand, sel, cfg["draws"], cfg["seed"] + 1)
    res = {}
    for part in ("tune", "assess"):
        eff = backend.effect(sel, sp[part], "margin")
        ce = [backend.effect(c, sp[part], "margin") for c in controls]
        res[part] = {"effect": eff, "p": one_sided_p(eff, ce), "gap": eff - sum(ce) / len(ce)}
    ctl = {}
    for name in ("text_only", "shuffled", "constant"):
        e = backend.control_effect(name, sel, sp["assess"])
        ctl[name] = {"effect": e, "separates": e >= FROZEN["min_effect"]}
    rej = holm([res["tune"]["p"], res["assess"]["p"]], cfg["alpha"])
    lp_eff = backend.effect(sel, sp["assess"], "logprob")
    lp_p = one_sided_p(lp_eff, [backend.effect(c, sp["assess"], "logprob") for c in controls])
    gate = instrument_gate_v2(backend, sel, scores, sp["assess"],
                              {"margin": res["assess"]["p"], "logprob": lp_p}, cfg["alpha"])
    h1 = all(rej) and res["assess"]["gap"] >= FROZEN["min_effect"] and not any(c["separates"] for c in ctl.values())
    if gate["status"] != "InstrumentValid":
        status = "InstrumentNotValid"
    else:
        status = "Candidate" if h1 else "NoCandidate"
    path = path_analysis(backend, sel, controls, sp["assess"], cfg["alpha"]) if status == "Candidate" else {
        "h2": False, "mechanism_wording_allowed": False, "reason": "path analysis only after a valid Candidate"}
    return {"status": status, "lock": lock, "selected": sel, "results": res, "controls": ctl,
            "holm_reject": rej, "gate": gate, "path": path, "ceiling": CEILING}


# ---- spend guard -----------------------------------------------------------------
class SpendGuard:
    """Hard cap; no charge without a recorded allocation receipt."""
    def __init__(self, receipt=None, cap=FROZEN["spend_cap_usd"]):
        if cap > FROZEN["spend_cap_usd"]:
            raise V50Error("cap above frozen ceiling")
        self.receipt, self.cap, self.spent = receipt, cap, 0.0

    def charge(self, usd):
        if not self.receipt:
            raise V50Error("no allocation receipt")
        if usd < 0 or self.spent + usd > self.cap:
            raise V50Error("spend ceiling breach")
        self.spent += usd
        return self.spent
