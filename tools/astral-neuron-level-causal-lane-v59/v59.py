"""V59: (A) class-swap sufficiency and (R) reflexive-pronoun transfer for the V58 top units, Pythia-2.8b.
Slices: astral-neuron-level-causal-lane-v59-execution, instrument-validity-gate-v3. Protocol: doc 141."""
import os, sys
HERE = os.path.dirname(__file__)
for d in ("astral-neuron-level-causal-lane-v58", "astral-neuron-level-causal-lane-v57", "astral-neuron-level-causal-lane-v54",
          "astral-neuron-level-causal-lane-v53", "astral-neuron-level-causal-lane-v52", "astral-neuron-level-causal-lane-v51",
          "astral-neuron-level-causal-lane-v50"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
import v50

FROZEN59 = {"spend_cap_usd": 2.50, "total_ceiling_usd": 50.00, "ctl_draws": 100, "min_effect": 0.1, "min_refl_per_class": 100,
            "swap_units": [20414, 25229, 2952, 28532, 24862, 13691, 22664], "ablate_units": [20414, 25229, 24862, 13691, 2952, 22664, 28532, 14134]}
FROZEN59_DIGEST = v50.digest(FROZEN59)


def _max(x):
    return max(x)


def run_v59(backend, cfg, v54, v58):
    if v50.digest(FROZEN59) != FROZEN59_DIGEST:
        raise v50.V50Error("V59 frozen values changed")
    if [t["unit"] for t in v58["top_units"]] != FROZEN59["ablate_units"]:
        raise v50.V50Error("V58 top units differ from the frozen list")
    sp = backend.split()
    core = {k: sp[k] for k in ("fit", "tune", "assess")}
    scores = backend.scores(sp["fit"])
    layer_of = backend.layers()
    sel32 = v50.select_per_layer(scores, layer_of, cfg["target_layers"], 32)
    if sel32 != v54["selected"]:
        raise v50.V50Error("k=32 reselection differs from the locked V54 selection")
    dirs = {u: (1 if scores[u] >= 0 else -1) for u in sel32}
    backend.mark_locked(v50.make_lock(sel32, dirs, core, cfg["model_id"], cfg["corpus_digest"], cfg["code_commit"]))
    mag = backend.magnitude()
    n = FROZEN59["ctl_draws"]
    out = {}
    # ---- A: class-swap sufficiency
    su = FROZEN59["swap_units"]
    cand = v50.matched_pool(mag, su, layer_of)
    ctl = v50.draw_controls(cand, su, 1000, cfg["seed"] + 1)[:n]
    allu = sorted(set(su) | {u for c in ctl for u in c})
    fit_stats = backend.unit_stats(allu, sp["fit"])
    means = {u: (fit_stats[u]["act_sing"], fit_stats[u]["act_plur"]) for u in allu}
    docs = sp["assess"]
    sel_swap = backend.swap_effect(su, docs, means)
    ctl_swap = [backend.swap_effect(c, docs, means) for c in ctl]
    cm = {k: max(c[k] for c in ctl_swap) for k in ("sing", "plur", "all")}
    out["swap"] = {"selected": sel_swap, "ctl_max": cm,
                   "ctl_mean": {k: sum(c[k] for c in ctl_swap) / len(ctl_swap) for k in ("sing", "plur", "all")},
                   "p_all": v50.one_sided_p(sel_swap["all"], [c["all"] for c in ctl_swap]),
                   "sufficiency_supported": bool(sel_swap["sing"] > cm["sing"] and sel_swap["plur"] > cm["plur"]
                                                 and sel_swap["all"] >= FROZEN59["min_effect"])}
    # ---- R: reflexive transfer
    refl = sp.get("refl")
    if refl:
        cls = backend.refl_class_counts(refl)
        if min(cls.values()) >= FROZEN59["min_refl_per_class"] and len(cls) == 2:
            au = FROZEN59["ablate_units"]
            cand8 = v50.matched_pool(mag, au, layer_of)
            ctl8 = v50.draw_controls(cand8, au, 1000, cfg["seed"] + 1)[:n]
            eff = backend.effect(au, refl, "margin")
            ce = [backend.effect(c, refl, "margin") for c in ctl8]
            out["reflexive"] = {"n_items": len(refl), "class_counts": cls, "effect": eff, "ctl_max": max(ce),
                                "ctl_mean": sum(ce) / len(ce), "p": v50.one_sided_p(eff, ce),
                                "transfer_supported": bool(eff > max(ce) and eff >= FROZEN59["min_effect"])}
        else:
            out["reflexive"] = {"skipped": "too few items per class", "class_counts": cls}
    else:
        out["reflexive"] = {"skipped": "no reflexive items"}
    out.update(ceiling=v50.CEILING, frozen59_digest=FROZEN59_DIGEST)
    return out


def make_backend_class():
    import v58
    base = v58.make_backend_class()
    SING = {"is", "was", "does", "has", "himself", "herself", "itself"}

    class V59Backend(base):
        def refl_class_counts(self, docs):
            c = {"sing": 0, "plur": 0}
            for i in docs:
                c["sing" if self._items[i][1].strip() in SING else "plur"] += 1
            return c

        def swap_effect(self, units, docs, means):
            """Replace the units' activations (all positions) by the opposite-class fit mean; returns the mean margin
            drop (base - swapped) on singular-correct items, plural-correct items, and all items."""
            torch = self.torch
            want = {}
            for u in units:
                want.setdefault(u // self.I, []).append(u)
            ids = list(docs)
            groups = {}
            for i in ids:
                groups.setdefault(len(self.tok.encode(self._items[i][0])), []).append(i)
            tot = {"sing": 0.0, "plur": 0.0}
            cnt = {"sing": 0, "plur": 0}
            self._reset()
            for _, gids in groups.items():
                for j in range(0, len(gids), 128):
                    chunk = gids[j:j + 128]
                    enc = self.tok([self._items[i][0] for i in chunk], return_tensors="pt").to(self.dev)
                    g = torch.tensor([self.tok.encode(self._items[i][1], add_special_tokens=False)[0] for i in chunk], device=self.dev)
                    b = torch.tensor([self.tok.encode(self._items[i][2], add_special_tokens=False)[0] for i in chunk], device=self.dev)
                    is_s = torch.tensor([self._items[i][1].strip() in SING for i in chunk], device=self.dev)
                    with torch.no_grad():
                        base = self._readout(self.m(**enc).logits, g, b, "margin")
                    hs = []
                    for k, us in want.items():
                        idx = torch.tensor([u % self.I for u in us], device=self.dev)
                        vs = torch.tensor([means[u][0] for u in us], device=self.dev, dtype=torch.float32)  # singular-class mean
                        vp = torch.tensor([means[u][1] for u in us], device=self.dev, dtype=torch.float32)  # plural-class mean

                        def pre(mod, args, idx=idx, vs=vs, vp=vp):
                            x = args[0].clone()
                            rep = torch.where(is_s[:, None], vp[None, :], vs[None, :]).to(x.dtype)  # opposite class
                            x[:, :, idx] = rep[:, None, :].expand(-1, x.shape[1], -1)
                            return (x,)
                        hs.append(self.layers_mod[self.LY[k]].mlp.dense_4h_to_h.register_forward_pre_hook(pre))
                    with torch.no_grad():
                        sw = self._readout(self.m(**enc).logits, g, b, "margin")
                    for h in hs:
                        h.remove()
                    d = (base - sw).float()
                    tot["sing"] += float(d[is_s].sum()); cnt["sing"] += int(is_s.sum())
                    tot["plur"] += float(d[~is_s].sum()); cnt["plur"] += int((~is_s).sum())
            r = {k: tot[k] / max(cnt[k], 1) for k in tot}
            r["all"] = (tot["sing"] + tot["plur"]) / max(cnt["sing"] + cnt["plur"], 1)
            return r
    return V59Backend
