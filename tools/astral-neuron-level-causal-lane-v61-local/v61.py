"""V61-local: fit-select, tune-rank, assess-test class-swap sufficiency (T0 all-position, L last-position, P donor patching).
Slices: astral-neuron-level-causal-lane-v61-local-execution, instrument-validity-gate-v3. Protocol: doc 201."""
import os, sys
HERE = os.path.dirname(__file__)
for d in ("astral-neuron-level-causal-lane-v60", "astral-neuron-level-causal-lane-v59", "astral-neuron-level-causal-lane-v58",
          "astral-neuron-level-causal-lane-v57", "astral-neuron-level-causal-lane-v54", "astral-neuron-level-causal-lane-v53",
          "astral-neuron-level-causal-lane-v52", "astral-neuron-level-causal-lane-v51", "astral-neuron-level-causal-lane-v50"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
import v50, v60

FROZEN61 = {"k_per_layer": 32, "swap_size": 8, "ctl_draws": 100, "min_effect": 0.1, "donor_seed": 6060, "dtype": "float32"}
FROZEN61_DIGEST = v50.digest(FROZEN61)


def run_v61(backend, cfg, v54_selected=None, log=None):
    if v50.digest(FROZEN61) != FROZEN61_DIGEST:
        raise v50.V50Error("V61 frozen values changed")
    say = log or (lambda *a: None)
    sp = backend.split()
    layer_of = backend.layers()
    scores = backend.scores(sp["fit"])
    cand_units = v50.select_per_layer(scores, layer_of, cfg["target_layers"], FROZEN61["k_per_layer"] * len(cfg["target_layers"]))
    dirs = {u: (1 if scores[u] >= 0 else -1) for u in cand_units}
    lock = v50.make_lock(cand_units, dirs, {k: sp[k] for k in ("fit", "tune", "assess")}, cfg["model_id"],
                         cfg["corpus_digest"], cfg["code_commit"])
    backend.mark_locked(lock)
    say("candidates", len(cand_units))
    # rank on tune only
    single = {u: backend.effect([u], sp["tune"], "margin") for u in cand_units}
    swap = sorted(sorted(cand_units, key=lambda u: (-single[u], u))[:FROZEN61["swap_size"]])
    swap_digest = v50.digest({"lock": lock, "swap": swap, "tune_single": {str(u): single[u] for u in swap}})
    say("swap set", swap)
    mag = backend.magnitude()
    cand = v50.matched_pool(mag, swap, layer_of)
    cset = set(cand_units)
    cand = {u: ([c for c in v if c not in cset] or v) for u, v in cand.items()}
    ctl = v50.draw_controls(cand, swap, 1000, cfg["seed"] + 1)[:FROZEN61["ctl_draws"]]
    allu = sorted(set(swap) | {u for c in ctl for u in c})
    fs = backend.unit_stats(allu, sp["fit"])
    means = {u: (fs[u]["act_sing"], fs[u]["act_plur"]) for u in allu}
    docs = sp["assess"]
    out = {"candidates_digest": v50.digest(cand_units), "swap_units": swap, "swap_lock_digest": swap_digest,
           "tune_single_effects": {str(u): single[u] for u in swap},
           "overlap_with_v54_selection": (len(set(cand_units) & set(v54_selected)) if v54_selected else None),
           "overlap_with_v59_units": len(set(swap) & set([20414, 25229, 2952, 28532, 24862, 13691, 22664, 14134]))}
    floor = FROZEN61["min_effect"]

    def task(name, fn):
        sel = fn(swap)
        cs = []
        for i, c in enumerate(ctl):
            cs.append(fn(c))
            if i % 20 == 19:
                say(name, "controls", i + 1)
        r, cm = v60._summ(sel, cs)
        r["supported"] = v60._supported(sel, cm, floor)
        return r
    out["t0_all_position_swap"] = task("T0", lambda us: backend.swap_effect(us, docs, means))
    out["l_last_position_swap"] = task("L", lambda us: backend.swap_effect_last(us, docs, means))
    classes = backend.item_classes(docs)
    cap = backend.capture_last(allu, docs)
    don = v60.donors(classes, docs, FROZEN61["donor_seed"])
    vals = lambda us, dm: {u: {i: cap[u][dm[i]] for i in docs} for u in us}
    out["p_donor_patch"] = task("P", lambda us: backend.patch_last(us, docs, vals(us, don)))
    same = v60.donors(classes, docs, FROZEN61["donor_seed"] + 1, same=True)
    out["p_donor_patch"]["same_class_donor_diagnostic"] = backend.patch_last(swap, docs, vals(swap, same))
    out["headline_reproduced_and_hardened"] = bool(out["t0_all_position_swap"]["supported"] and out["l_last_position_swap"]["supported"]
                                                   and out["p_donor_patch"]["supported"])
    out.update(ceiling=v50.CEILING, frozen61_digest=FROZEN61_DIGEST)
    return out
