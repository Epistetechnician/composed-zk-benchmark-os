"""V56: exploratory path analysis (H2') on the LOCKED V54 selection with absolute-effect statistics.
Slices: astral-neuron-level-causal-lane-v56-execution, instrument-validity-gate-v3. Protocol: doc 138.
Why: V50-V55 H2 compared ratio shares, undefined for control draws with non-positive total effect, so
fewer than 90% of draws were valid and the test always aborted. Here every draw has defined statistics."""
import os, sys
HERE = os.path.dirname(__file__)
for d in ("astral-neuron-level-causal-lane-v54", "astral-neuron-level-causal-lane-v53", "astral-neuron-level-causal-lane-v52",
          "astral-neuron-level-causal-lane-v51", "astral-neuron-level-causal-lane-v50"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
import v50

FROZEN56 = {"spend_cap_usd": 3.00, "total_ceiling_usd": 50.00, "draws": 1000, "alpha": 0.05,
            "top2_min_share": 0.5, "stat_ind": "total-direct (logits)", "stat_top2": "top2 mediator share * max(indirect,0)"}
FROZEN56_DIGEST = v50.digest(FROZEN56)


def path_stats_abs(backend, units, docs):
    total = backend.total_effect(units, docs)
    ind = total - backend.direct_effect(units, docs)
    if ind <= 0:
        return {"total": total, "indirect_abs": ind, "top2_share": 0.0, "top2_abs": 0.0, "mediators": []}
    med = backend.mediators(units, docs)
    top = sorted(med.items(), key=lambda kv: (-kv[1], kv[0]))[:2]
    share = sum(v for _, v in top)
    return {"total": total, "indirect_abs": ind, "top2_share": share, "top2_abs": share * ind, "mediators": [n for n, _ in top]}


def run_v56(backend, cfg, v54):
    if v50.digest(FROZEN56) != FROZEN56_DIGEST:
        raise v50.V50Error("V56 frozen values changed")
    sp = backend.split()
    scores = backend.scores(sp["fit"])
    layer_of = backend.layers()
    sel = v50.select_per_layer(scores, layer_of, cfg["target_layers"], cfg["k"])
    if sel != v54["selected"]:
        raise v50.V50Error("reselection differs from the locked V54 selection")
    dirs = {u: (1 if scores[u] >= 0 else -1) for u in sel}
    backend.mark_locked(v50.make_lock(sel, dirs, sp, cfg["model_id"], cfg["corpus_digest"], cfg["code_commit"]))
    cand = v50.matched_pool(backend.magnitude(), sel, layer_of)
    controls = v50.draw_controls(cand, sel, FROZEN56["draws"], cfg["seed"] + 1)
    s = path_stats_abs(backend, sel, sp["assess"])
    cs = [path_stats_abs(backend, c, sp["assess"]) for c in controls]
    p_ind = v50.one_sided_p(s["indirect_abs"], [c["indirect_abs"] for c in cs])
    p_top = v50.one_sided_p(s["top2_abs"], [c["top2_abs"] for c in cs])
    rej = v50.holm([p_ind, p_top], FROZEN56["alpha"])
    h2 = bool(all(rej) and s["top2_share"] >= FROZEN56["top2_min_share"])
    return {"h2_prime": h2, "selected": s, "p": {"indirect_abs": p_ind, "top2_abs": p_top}, "holm_reject": rej,
            "control_n": len(cs), "control_indirect_mean": sum(c["indirect_abs"] for c in cs) / len(cs),
            "control_top2_abs_mean": sum(c["top2_abs"] for c in cs) / len(cs), "mediators": s["mediators"],
            "correlational_patching_only": True, "mechanism_wording_allowed": h2,
            "ceiling": v50.CEILING, "frozen56_digest": FROZEN56_DIGEST}
