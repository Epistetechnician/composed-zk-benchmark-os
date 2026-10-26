"""V57: robustness of the locked V54 finding on Pythia-2.8b: (A) dose-response over k, (B) mean-ablation.
Slices: astral-neuron-level-causal-lane-v57-execution, instrument-validity-gate-v3. Protocol: doc 139."""
import os, sys
HERE = os.path.dirname(__file__)
for d in ("astral-neuron-level-causal-lane-v56", "astral-neuron-level-causal-lane-v54", "astral-neuron-level-causal-lane-v53",
          "astral-neuron-level-causal-lane-v52", "astral-neuron-level-causal-lane-v51", "astral-neuron-level-causal-lane-v50"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
import v50

FROZEN57 = {"spend_cap_usd": 2.50, "total_ceiling_usd": 50.00, "ks": [4, 8, 16, 32, 64, 128], "ctl_draws": 100,
            "mean_min_frac": 0.5, "split": "assess"}
FROZEN57_DIGEST = v50.digest(FROZEN57)


def _mean(x):
    return sum(x) / len(x)


def run_v57(backend, cfg, v54):
    if v50.digest(FROZEN57) != FROZEN57_DIGEST:
        raise v50.V50Error("V57 frozen values changed")
    sp = backend.split()
    scores = backend.scores(sp["fit"])
    layer_of = backend.layers()
    sel32 = v50.select_per_layer(scores, layer_of, cfg["target_layers"], 32)
    if sel32 != v54["selected"]:
        raise v50.V50Error("k=32 reselection differs from the locked V54 selection")
    sels = {k: v50.select_per_layer(scores, layer_of, cfg["target_layers"], k) for k in FROZEN57["ks"]}
    big = sels[max(FROZEN57["ks"])]
    for k in FROZEN57["ks"]:  # nesting is needed for a clean dose-response reading
        if not set(sels[k]) <= set(big):
            raise v50.V50Error("selections are not nested")
    dirs = {u: (1 if scores[u] >= 0 else -1) for u in big}
    backend.mark_locked(v50.make_lock(big, dirs, sp, cfg["model_id"], cfg["corpus_digest"], cfg["code_commit"]))
    mag = backend.magnitude()
    docs = sp[FROZEN57["split"]]
    n = FROZEN57["ctl_draws"]
    dose = {}
    for k in FROZEN57["ks"]:
        cand = v50.matched_pool(mag, sels[k], layer_of)
        ctl = v50.draw_controls(cand, sels[k], 1000, cfg["seed"] + 1)[:n]
        eff = backend.effect(sels[k], docs, "margin")
        ce = [backend.effect(c, docs, "margin") for c in ctl]
        dose[str(k)] = {"effect": eff, "ctl_mean": _mean(ce), "ctl_max": max(ce), "p": v50.one_sided_p(eff, ce),
                        "beats_all_controls": eff > max(ce), "per_unit": eff / k}
    effs = [dose[str(k)]["effect"] for k in FROZEN57["ks"]]
    monotone = all(b > a for a, b in zip(effs, effs[1:]))
    # (B) mean ablation at k=32
    backend.compute_means(sp["fit"])
    cand = v50.matched_pool(mag, sel32, layer_of)
    ctl = v50.draw_controls(cand, sel32, 1000, cfg["seed"] + 1)[:n]
    zero = dose["32"]["effect"]
    m_eff = backend.effect_mean(sel32, docs)
    m_ce = [backend.effect_mean(c, docs) for c in ctl]
    mean_abl = {"effect": m_eff, "ctl_mean": _mean(m_ce), "ctl_max": max(m_ce), "p": v50.one_sided_p(m_eff, m_ce),
                "frac_of_zero": m_eff / zero if zero else None,
                "supported": bool(m_eff > max(m_ce) and zero and m_eff / zero >= FROZEN57["mean_min_frac"])}
    dose_ok = bool(monotone and all(dose[str(k)]["beats_all_controls"] for k in FROZEN57["ks"]))
    return {"dose_response": dose, "dose_monotone_increasing": monotone, "dose_response_supported": dose_ok,
            "mean_ablation": mean_abl, "ceiling": v50.CEILING, "frozen57_digest": FROZEN57_DIGEST}


def make_backend_class():
    import v53
    base = v53.make_backend_class()

    class V57Backend(base):
        mean_mode = False
        meanvec = None

        def _mask_hook(self, k):
            def h(mod, args):
                x = args[0]
                if self.capture:
                    self.acts[k] = self.acts.get(k, 0) + x.detach().abs().float().sum((0, 1))
                    self.acts[("n", k)] = self.acts.get(("n", k), 0) + x.shape[0] * x.shape[1]
                m = self.mask[k].to(x.dtype)
                if self.mean_mode and self.meanvec is not None:
                    return (x * m + (1 - m) * self.meanvec[k].to(x.dtype),)
                return (x * m,)
            return h

        def compute_means(self, fit):
            torch = self.torch
            self._reset()
            sums = {k: torch.zeros(self.I, device=self.dev) for k in self.mask}
            cnt = {"n": 0}
            hs = []
            for k, l in enumerate(self.LY):
                def pre(mod, args, k=k):
                    sums[k] += args[0].detach().float().sum((0, 1))
                    if k == 0:
                        cnt["n"] += args[0].shape[0] * args[0].shape[1]
                hs.append(self.layers_mod[l].mlp.dense_4h_to_h.register_forward_pre_hook(pre))
            try:
                self._mean(list(fit))
            finally:
                for h in hs:
                    h.remove()
            self.meanvec = {k: sums[k] / cnt["n"] for k in sums}

        def effect_mean(self, units, docs):
            self.mean_mode = True
            try:
                return self.effect(units, docs, "margin")
            finally:
                self.mean_mode = False
    return V57Backend
