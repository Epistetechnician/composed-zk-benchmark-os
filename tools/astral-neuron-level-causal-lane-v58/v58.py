"""V58: per-neuron analysis of the locked V54 finding: single-unit ablation effects, direct logit attribution (DLA)
through the final norm, and class-conditional (singular vs plural) contributions, against matched-random units.
Slices: astral-neuron-level-causal-lane-v58-execution, instrument-validity-gate-v3. Protocol: doc 140."""
import os, sys
HERE = os.path.dirname(__file__)
for d in ("astral-neuron-level-causal-lane-v57", "astral-neuron-level-causal-lane-v56", "astral-neuron-level-causal-lane-v54",
          "astral-neuron-level-causal-lane-v53", "astral-neuron-level-causal-lane-v52", "astral-neuron-level-causal-lane-v51",
          "astral-neuron-level-causal-lane-v50"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
import v50

FROZEN58 = {"spend_cap_usd": 2.50, "total_ceiling_usd": 50.00, "k": 128, "ctl_units": 300, "top": 8,
            "conc_min_share": 0.5, "spearman_min": 0.5, "select_min_units": 6, "split": "assess"}
FROZEN58_DIGEST = v50.digest(FROZEN58)


def _ranks(x):
    order = sorted(range(len(x)), key=lambda i: (x[i], i))
    r = [0.0] * len(x)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for t in range(i, j + 1):
            r[order[t]] = (i + j) / 2.0
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = _ranks(a), _ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else 0.0


def run_v58(backend, cfg, v54):
    if v50.digest(FROZEN58) != FROZEN58_DIGEST:
        raise v50.V50Error("V58 frozen values changed")
    sp = backend.split()
    scores = backend.scores(sp["fit"])
    layer_of = backend.layers()
    sel32 = v50.select_per_layer(scores, layer_of, cfg["target_layers"], 32)
    if sel32 != v54["selected"]:
        raise v50.V50Error("k=32 reselection differs from the locked V54 selection")
    sel = v50.select_per_layer(scores, layer_of, cfg["target_layers"], FROZEN58["k"])
    dirs = {u: (1 if scores[u] >= 0 else -1) for u in sel}
    backend.mark_locked(v50.make_lock(sel, dirs, sp, cfg["model_id"], cfg["corpus_digest"], cfg["code_commit"]))
    mag = backend.magnitude()
    cand = v50.matched_pool(mag, sel, layer_of)
    draws = v50.draw_controls(cand, sel, 1000, cfg["seed"] + 1)
    ctl, seen = [], set(sel)
    for d in draws:
        for u in d:
            if u not in seen:
                seen.add(u); ctl.append(u)
            if len(ctl) >= FROZEN58["ctl_units"]:
                break
        if len(ctl) >= FROZEN58["ctl_units"]:
            break
    docs = sp[FROZEN58["split"]]
    allu = list(sel) + ctl
    st = backend.unit_stats(allu, docs)
    single = {u: backend.effect([u], docs, "margin") for u in allu}
    joint = backend.effect(sel, docs, "margin")
    rank = sorted(sel, key=lambda u: (-single[u], u))
    top = rank[:FROZEN58["top"]]
    topsum4 = sum(single[u] for u in rank[:4])
    topsum8 = sum(single[u] for u in top)
    joint8 = backend.effect(top, docs, "margin")
    sp_rho = spearman([single[u] for u in sel], [st[u]["dla"] for u in sel])
    ctl_eff_max = max(single[u] for u in ctl)
    ctl_dla_max = max(abs(st[u]["dla"]) for u in ctl)
    n_sel = sum(1 for u in top if st[u]["dla_sing"] > 0 and st[u]["dla_plur"] > 0)
    out = {"joint_k128_effect": joint, "top_units": [{"unit": u, "layer": layer_of[u], "single_effect": single[u], **st[u]} for u in top],
           "top4_single_sum": topsum4, "top8_single_sum": topsum8, "top8_joint_effect": joint8,
           "top4_share_of_joint128": topsum4 / joint if joint else None,
           "top8_share_of_joint128": topsum8 / joint if joint else None,
           "spearman_single_vs_dla_selected128": sp_rho,
           "ctl_single_effect_max": ctl_eff_max, "ctl_dla_abs_max": ctl_dla_max, "ctl_n": len(ctl),
           "top8_beat_all_controls_single": all(single[u] > ctl_eff_max for u in top),
           "n_top8_agreement_selective": n_sel}
    out["h_concentration"] = bool(out["top8_share_of_joint128"] is not None and out["top8_share_of_joint128"] >= FROZEN58["conc_min_share"])
    out["h_direct_path"] = bool(sp_rho >= FROZEN58["spearman_min"])
    out["h_agreement_selective"] = bool(n_sel >= FROZEN58["select_min_units"] and out["top8_beat_all_controls_single"])
    out["table_selected128"] = {str(u): {"single_effect": single[u], "dla": st[u]["dla"]} for u in sel}
    out.update(ceiling=v50.CEILING, frozen58_digest=FROZEN58_DIGEST)
    return out


def make_backend_class():
    import v53
    base = v53.make_backend_class()
    SING = {"is", "was", "does", "has"}

    class V58Backend(base):
        def unit_stats(self, units, docs):
            """Per unit over docs: dla (mean margin contribution through the final norm), dla_sing, dla_plur,
            act_sing, act_plur (mean last-position activation by class of the correct form)."""
            torch = self.torch
            ln, U = self.m.gpt_neox.final_layer_norm, self.m.get_output_embeddings().weight
            want = {}
            for u in units:
                want.setdefault(u // self.I, []).append(u % self.I)
            order = {k: v for k, v in want.items()}
            acc = {u: [0.0, 0.0, 0.0, 0.0, 0.0] for u in units}  # dla_s, dla_p, act_s, act_p, (unused)
            n = {"s": 0, "p": 0}
            ids = list(docs)
            groups = {}
            for i in ids:
                groups.setdefault(len(self.tok.encode(self._items[i][0])), []).append(i)
            self._reset()
            for _, gids in groups.items():
                for j in range(0, len(gids), 128):
                    chunk = gids[j:j + 128]
                    enc = self.tok([self._items[i][0] for i in chunk], return_tensors="pt").to(self.dev)
                    g = torch.tensor([self.tok.encode(self._items[i][1], add_special_tokens=False)[0] for i in chunk], device=self.dev)
                    b = torch.tensor([self.tok.encode(self._items[i][2], add_special_tokens=False)[0] for i in chunk], device=self.dev)
                    is_s = torch.tensor([self._items[i][1].strip() in SING for i in chunk], device=self.dev)
                    cap, hs = {}, []
                    for k, idx in order.items():
                        mod = self.layers_mod[self.LY[k]].mlp.dense_4h_to_h
                        hs.append(mod.register_forward_pre_hook(
                            lambda m_, a, k=k, idx=idx: cap.__setitem__(k, a[0][:, -1][:, idx].float())))
                    hs.append(ln.register_forward_pre_hook(lambda m_, a: cap.__setitem__("res", a[0][:, -1].float())))
                    with torch.no_grad():
                        self.m(**enc)
                    for h in hs:
                        h.remove()
                    res = cap["res"]
                    sd = (res.var(-1, unbiased=False, keepdim=True) + ln.eps).sqrt()
                    d = U[g].float() - U[b].float()
                    gd = d * ln.weight.float()
                    v = gd - gd.mean(-1, keepdim=True)  # (B, H)
                    for k, idx in order.items():
                        W = self.layers_mod[self.LY[k]].mlp.dense_4h_to_h.weight[:, idx].float()  # (H, m)
                        proj = v @ W  # (B, m)
                        dla = cap[k] / sd * proj
                        for t, ix in enumerate(idx):
                            u = k * self.I + ix
                            acc[u][0] += float(dla[is_s, t].sum()); acc[u][1] += float(dla[~is_s, t].sum())
                            acc[u][2] += float(cap[k][is_s, t].sum()); acc[u][3] += float(cap[k][~is_s, t].sum())
                    n["s"] += int(is_s.sum()); n["p"] += int((~is_s).sum())
            out = {}
            for u, a in acc.items():
                ds, dp = a[0] / max(n["s"], 1), a[1] / max(n["p"], 1)
                out[u] = {"dla_sing": ds, "dla_plur": dp, "dla": (a[0] + a[1]) / max(n["s"] + n["p"], 1),
                          "act_sing": a[2] / max(n["s"], 1), "act_plur": a[3] / max(n["p"], 1)}
            return out
    return V58Backend
