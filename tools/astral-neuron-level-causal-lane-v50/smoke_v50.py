"""V50 node smoke check: exercises every backend method on a handful of units/docs, times them, and
projects the cost of the full run. Produces no scientific result. Needs model dir, corpus, receipt.
State slices: astral-neuron-level-causal-lane-v50-execution, instrument-validity-gate-v2."""
import argparse, json, math, os, random, sys, time

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, os.path.dirname(__file__))
import v50


def timed(f, *a):
    t = time.time(); r = f(*a); return r, time.time() - t


def smoke(backend, usd_per_min, n_ctrl_draws=1000):
    out, checks = {}, {}
    sp = backend.split()
    checks["splits_nonempty"] = all(len(sp[k]) > 0 for k in ("fit", "tune", "assess"))
    sc, out["t_scores_fit"] = timed(backend.scores, sp["fit"][:64])
    checks["scores_finite_varied"] = all(math.isfinite(v) for v in sc.values()) and len(set(round(v, 9) for v in sc.values())) > 10
    layer_of = backend.layers()
    lys = sorted(set(layer_of.values()))
    sel = v50.select_per_layer(sc, layer_of, lys, v50.FROZEN["k"])
    mag, out["t_magnitude"] = timed(backend.magnitude)
    checks["magnitude_finite"] = all(math.isfinite(v) for v in mag.values())
    backend.mark_locked("smoke-lock")
    docs = sp["assess"]
    e0 = backend.effect([], docs, "margin")
    checks["empty_ablation_zero"] = abs(e0) < 1e-6
    e1, out["t_effect_assess"] = timed(backend.effect, sel, docs, "margin")
    e2 = backend.effect(sel, docs, "margin")
    checks["effect_repeatable"] = abs(e1 - e2) < 1e-3
    layer0 = [u for u in layer_of if layer_of[u] == lys[0]]
    checks["whole_layer_ablation_nonzero"] = abs(backend.effect(layer0, docs, "margin")) > 1e-3
    lp = backend.effect(sel, docs, "logprob")
    checks["logprob_finite"] = math.isfinite(lp)
    kb = [backend.known_bad_effect(s, sel, docs) for s in range(3)]
    checks["known_bad_finite"] = all(math.isfinite(x) for x in kb)
    vals = backend.activation_values(sel, docs)
    checks["activation_both_signs"] = any(v > 0 for v in vals) and any(v < 0 for v in vals)
    tot, _ = timed(backend.total_effect, sel, docs)
    dr, out["t_direct"] = timed(backend.direct_effect, sel, docs)
    med, out["t_mediators"] = timed(backend.mediators, sel, docs)
    checks["path_finite"] = math.isfinite(tot) and math.isfinite(dr)
    checks["mediators_normalized"] = (not med) or abs(sum(med.values()) - 1.0) < 1e-6
    rng = random.Random(0)
    rnd = sorted(rng.sample(sorted(mag), len(sel)))
    out["selected_effect"], out["random_effect"] = e1, backend.effect(rnd, docs, "margin")
    out["total_path"], out["direct_path"] = tot, dr
    out["top_mediators"] = sorted(med.items(), key=lambda kv: -kv[1])[:3]
    # projection: tune+assess margin + assess logprob per draw, plus one path call per draw
    t_eff = out["t_effect_assess"]
    proj_s = n_ctrl_draws * (3 * t_eff + out["t_mediators"] + out["t_direct"])
    out["projected_full_run_min"] = proj_s / 60
    out["projected_full_run_usd"] = proj_s / 60 * usd_per_min
    out["checks"], out["passed"] = checks, all(checks.values())
    return out


def main(argv=None, backend_factory=None):
    a = argparse.ArgumentParser()
    for n in ("model_dir", "corpus", "receipt", "layers", "out"):
        a.add_argument("--" + n.replace("_", "-"), required=True)
    a.add_argument("--usd-per-min", type=float, default=0.084)
    args = a.parse_args(argv)
    receipt = json.load(open(args.receipt))
    if not receipt.get("allocation_id"):
        raise v50.V50Error("no allocation receipt")
    corpus = json.load(open(args.corpus))
    layers = [int(x) for x in args.layers.split(",")]
    factory = backend_factory or __import__("pythia_backend").PythiaBackend
    res = smoke(factory(args.model_dir, corpus["split_items"], layers), args.usd_per_min)
    json.dump(res, open(args.out, "w"), indent=1, sort_keys=True)
    print(json.dumps({k: res[k] for k in ("passed", "checks", "projected_full_run_min", "projected_full_run_usd")}, indent=1))
    return res


if __name__ == "__main__":
    main()
