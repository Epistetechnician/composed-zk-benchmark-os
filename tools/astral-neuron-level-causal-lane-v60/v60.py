"""V60: (L) last-position-only class swap and (P) counterfactual donor activation patching for the V59 swap units.
Slices: astral-neuron-level-causal-lane-v60-execution, instrument-validity-gate-v3. Protocol: doc 200."""
import os, random, sys
HERE = os.path.dirname(__file__)
for d in ("astral-neuron-level-causal-lane-v59", "astral-neuron-level-causal-lane-v58", "astral-neuron-level-causal-lane-v57",
          "astral-neuron-level-causal-lane-v54", "astral-neuron-level-causal-lane-v53", "astral-neuron-level-causal-lane-v52",
          "astral-neuron-level-causal-lane-v51", "astral-neuron-level-causal-lane-v50"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
import v50

FROZEN60 = {"spend_cap_usd": 1.50, "total_ceiling_usd": 50.00, "ctl_draws": 100, "min_effect": 0.1, "donor_seed": 6060,
            "swap_units": [20414, 25229, 2952, 28532, 24862, 13691, 22664],
            "v58_top_units": [20414, 25229, 24862, 13691, 2952, 22664, 28532, 14134]}
FROZEN60_DIGEST = v50.digest(FROZEN60)


def donors(classes, docs, seed, same=False):
    """Map each item to a donor item: opposite class (default) or a different item of the same class."""
    rng = random.Random(seed)
    by = {"sing": sorted(i for i in docs if classes[i] == "sing"), "plur": sorted(i for i in docs if classes[i] == "plur")}
    out = {}
    for i in docs:
        c = classes[i] if same else ("plur" if classes[i] == "sing" else "sing")
        pool = [j for j in by[c] if j != i]
        out[i] = rng.choice(pool)
    return out


def _supported(sel, cm, floor):
    return bool(sel["sing"] > cm["sing"] and sel["plur"] > cm["plur"] and sel["all"] >= floor)


def _summ(sel, ctl):
    cm = {k: max(c[k] for c in ctl) for k in ("sing", "plur", "all")}
    return {"selected": sel, "ctl_max": cm, "ctl_mean": {k: sum(c[k] for c in ctl) / len(ctl) for k in ("sing", "plur", "all")},
            "p_all": v50.one_sided_p(sel["all"], [c["all"] for c in ctl])}, cm


def run_v60(backend, cfg, v54, v58):
    if v50.digest(FROZEN60) != FROZEN60_DIGEST:
        raise v50.V50Error("V60 frozen values changed")
    if [t["unit"] for t in v58["top_units"]] != FROZEN60["v58_top_units"]:
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
    n = FROZEN60["ctl_draws"]
    su = FROZEN60["swap_units"]
    cand = v50.matched_pool(mag, su, layer_of)
    ctl = v50.draw_controls(cand, su, 1000, cfg["seed"] + 1)[:n]
    allu = sorted(set(su) | {u for c in ctl for u in c})
    docs = sp["assess"]
    fit_stats = backend.unit_stats(allu, sp["fit"])
    means = {u: (fit_stats[u]["act_sing"], fit_stats[u]["act_plur"]) for u in allu}
    out = {}
    # ---- L: last-position-only class swap
    sel_l = backend.swap_effect_last(su, docs, means)
    ctl_l = [backend.swap_effect_last(c, docs, means) for c in ctl]
    out["last_swap"], cm = _summ(sel_l, ctl_l)
    out["last_swap"]["supported"] = _supported(sel_l, cm, FROZEN60["min_effect"])
    # ---- P: counterfactual donor activation patching (last position)
    classes = backend.item_classes(docs)
    cap = backend.capture_last(allu, docs)
    don = donors(classes, docs, FROZEN60["donor_seed"])
    vals = lambda us, dm: {u: {i: cap[u][dm[i]] for i in docs} for u in us}
    sel_p = backend.patch_last(su, docs, vals(su, don))
    ctl_p = [backend.patch_last(c, docs, vals(c, don)) for c in ctl]
    out["donor_patch"], cm = _summ(sel_p, ctl_p)
    out["donor_patch"]["supported"] = _supported(sel_p, cm, FROZEN60["min_effect"])
    same = donors(classes, docs, FROZEN60["donor_seed"] + 1, same=True)
    out["donor_patch"]["same_class_donor_diagnostic"] = backend.patch_last(su, docs, vals(su, same))
    out["headline_hardened"] = bool(out["last_swap"]["supported"] and out["donor_patch"]["supported"])
    out.update(ceiling=v50.CEILING, frozen60_digest=FROZEN60_DIGEST)
    return out


def make_backend_class():
    import v59
    base = v59.make_backend_class()
    SING = {"is", "was", "does", "has"}

    class V60Backend(base):
        def item_classes(self, docs):
            return {i: ("sing" if self._items[i][1].strip() in SING else "plur") for i in docs}

        def _groups(self, docs):
            groups = {}
            for i in docs:
                groups.setdefault(len(self.tok.encode(self._items[i][0])), []).append(i)
            return groups

        def _want(self, units):
            want = {}
            for u in units:
                want.setdefault(u // self.I, []).append(u)
            return want

        def capture_last(self, units, docs):
            """{unit: {item: last-position input activation of its layer's dense_4h_to_h}}."""
            torch = self.torch
            want = self._want(units)
            res = {u: {} for u in units}
            self._reset()
            for _, gids in self._groups(docs).items():
                for j in range(0, len(gids), 128):
                    chunk = gids[j:j + 128]
                    enc = self.tok([self._items[i][0] for i in chunk], return_tensors="pt").to(self.dev)
                    store, hs = {}, []
                    for k, us in want.items():
                        idx = torch.tensor([u % self.I for u in us], device=self.dev)

                        def pre(mod, args, k=k, idx=idx):
                            store[k] = args[0][:, -1, idx].float().cpu()
                        hs.append(self.layers_mod[self.LY[k]].mlp.dense_4h_to_h.register_forward_pre_hook(pre))
                    with torch.no_grad():
                        self.m(**enc)
                    for h in hs:
                        h.remove()
                    for k, us in want.items():
                        for c, i in enumerate(chunk):
                            for t, u in enumerate(us):
                                res[u][i] = float(store[k][c, t])
            return res

        def _patched_drop(self, units, docs, getvals):
            """getvals(chunk, k, us) -> float tensor [B, len(us)] written at the last position; returns mean margin drop."""
            torch = self.torch
            want = self._want(units)
            tot = {"sing": 0.0, "plur": 0.0}
            cnt = {"sing": 0, "plur": 0}
            self._reset()
            for _, gids in self._groups(docs).items():
                for j in range(0, len(gids), 128):
                    chunk = gids[j:j + 128]
                    enc = self.tok([self._items[i][0] for i in chunk], return_tensors="pt").to(self.dev)
                    g = torch.tensor([self.tok.encode(self._items[i][1], add_special_tokens=False)[0] for i in chunk], device=self.dev)
                    b = torch.tensor([self.tok.encode(self._items[i][2], add_special_tokens=False)[0] for i in chunk], device=self.dev)
                    is_s = torch.tensor([self._items[i][1].strip() in SING for i in chunk], device=self.dev)
                    with torch.no_grad():
                        base_m = self._readout(self.m(**enc).logits, g, b, "margin")
                    hs = []
                    for k, us in want.items():
                        idx = torch.tensor([u % self.I for u in us], device=self.dev)
                        v = getvals(chunk, k, us, is_s).to(self.dev)

                        def pre(mod, args, idx=idx, v=v):
                            x = args[0].clone()
                            x[:, -1, idx] = v.to(x.dtype)
                            return (x,)
                        hs.append(self.layers_mod[self.LY[k]].mlp.dense_4h_to_h.register_forward_pre_hook(pre))
                    with torch.no_grad():
                        pm = self._readout(self.m(**enc).logits, g, b, "margin")
                    for h in hs:
                        h.remove()
                    d = (base_m - pm).float()
                    tot["sing"] += float(d[is_s].sum()); cnt["sing"] += int(is_s.sum())
                    tot["plur"] += float(d[~is_s].sum()); cnt["plur"] += int((~is_s).sum())
            r = {k: tot[k] / max(cnt[k], 1) for k in tot}
            r["all"] = (tot["sing"] + tot["plur"]) / max(cnt["sing"] + cnt["plur"], 1)
            return r

        def swap_effect_last(self, units, docs, means):
            torch = self.torch

            def getvals(chunk, k, us, is_s):
                vs = torch.tensor([means[u][0] for u in us], dtype=torch.float32, device=is_s.device)
                vp = torch.tensor([means[u][1] for u in us], dtype=torch.float32, device=is_s.device)
                return torch.where(is_s[:, None], vp[None, :], vs[None, :])  # opposite class
            return self._patched_drop(units, docs, getvals)

        def patch_last(self, units, docs, vals):
            torch = self.torch

            def getvals(chunk, k, us, is_s):
                return torch.tensor([[vals[u][i] for u in us] for i in chunk], dtype=torch.float32)
            return self._patched_drop(units, docs, getvals)
    return V60Backend
