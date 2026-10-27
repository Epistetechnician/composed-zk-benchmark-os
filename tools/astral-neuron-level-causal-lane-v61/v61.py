"""V61: minimal-pair donor patching for the V59/V60 swap units. Slices: astral-neuron-level-causal-lane-v61-execution,
instrument-validity-gate-v3. Protocol: doc 201."""
import os, random, sys
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "astral-neuron-level-causal-lane-v60"))
import v60
from v60 import v50

FROZEN61 = {"spend_cap_usd": 1.00, "total_ceiling_usd": 50.00, "ctl_draws": 100, "min_effect": 0.1, "pair_seed": 6161,
            "n_pairs": 400, "self_tol": 1e-3, "same_seed": 6162,
            "swap_units": list(v60.FROZEN60["swap_units"]), "v58_top_units": list(v60.FROZEN60["v58_top_units"])}
FROZEN61_DIGEST = v50.digest(FROZEN61)

NOUNS = [("key", "keys"), ("dog", "dogs"), ("book", "books"), ("car", "cars"), ("girl", "girls"), ("boy", "boys"),
         ("student", "students"), ("teacher", "teachers"), ("doctor", "doctors"), ("painting", "paintings"),
         ("window", "windows"), ("letter", "letters"), ("chair", "chairs"), ("bird", "birds"), ("farmer", "farmers"),
         ("horse", "horses"), ("river", "rivers"), ("house", "houses"), ("soldier", "soldiers"), ("child", "children"),
         ("man", "men"), ("woman", "women")]
ATTR = [("cabinet", "cabinets"), ("table", "tables"), ("road", "roads"), ("garden", "gardens"), ("school", "schools"),
        ("building", "buildings"), ("shop", "shops"), ("bridge", "bridges")]
PREPS = ["near", "behind", "next to", "beside"]
VERBS = [(" is", " are"), (" was", " were"), (" has", " have")]


def build_minpairs(seed, n):
    """Deterministic items [{id,text,good,bad}] and mate map; each pair differs only in the subject noun number."""
    rng = random.Random(seed)
    combos = [(a, b, c, d) for a in range(len(NOUNS)) for b in range(len(ATTR)) for c in range(len(PREPS)) for d in range(len(VERBS))]
    rng.shuffle(combos)
    items, mate = [], {}
    for p, (ni, ai, pi, vi) in enumerate(combos[:n]):
        attr = ATTR[ai][rng.randrange(2)]
        sg_id, pl_id = "M:%d:s" % p, "M:%d:p" % p
        for iid, num in ((sg_id, 0), (pl_id, 1)):
            text = "The %s %s the %s" % (NOUNS[ni][num], PREPS[pi], attr)
            good, bad = VERBS[vi][num], VERBS[vi][1 - num]
            items.append({"id": iid, "text": text, "good": good, "bad": bad})
        mate[sg_id], mate[pl_id] = pl_id, sg_id
    return items, mate


def same_number_donors(ids, mate_of, seed):
    rng = random.Random(seed)
    by = {"s": sorted(i for i in ids if i.endswith(":s")), "p": sorted(i for i in ids if i.endswith(":p"))}
    return {i: rng.choice([j for j in by[i[-1]] if j.split(":")[1] != i.split(":")[1]]) for i in ids}


def run_v61(backend, cfg, v54, v58):
    if v50.digest(FROZEN61) != FROZEN61_DIGEST:
        raise v50.V50Error("V61 frozen values changed")
    if [t["unit"] for t in v58["top_units"]] != FROZEN61["v58_top_units"]:
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
    su = FROZEN61["swap_units"]
    cand = v50.matched_pool(mag, su, layer_of)
    ctl = v50.draw_controls(cand, su, 1000, cfg["seed"] + 1)[:FROZEN61["ctl_draws"]]
    allu = sorted(set(su) | {u for c in ctl for u in c})
    docs = sp["minpair"]
    mate = {i: (i[:-1] + ("p" if i.endswith("s") else "s")) for i in docs}
    if any(m not in set(docs) for m in mate.values()):
        raise v50.V50Error("minimal-pair mate missing")
    cap = backend.capture_last(allu, docs)
    vals = lambda us, dm: {u: {i: cap[u][dm[i]] for i in docs} for u in us}
    out = {"n_items": len(docs)}
    # self-donor sanity (identity patch must be ~0)
    selfm = {i: i for i in docs}
    out["self_donor"] = backend.patch_last(su, docs, vals(su, selfm))
    out["self_donor_ok"] = bool(max(abs(out["self_donor"][k]) for k in ("sing", "plur", "all")) <= FROZEN61["self_tol"])
    # M: minimal-pair donor
    sel = backend.patch_last(su, docs, vals(su, mate))
    ctl_m = [backend.patch_last(c, docs, vals(c, mate)) for c in ctl]
    res, cm = v60._summ(sel, ctl_m)
    res["supported"] = v60._supported(sel, cm, FROZEN61["min_effect"])
    out["minpair_patch"] = res
    # diagnostic: same-number donor from a different pair
    out["same_number_donor_diagnostic"] = backend.patch_last(su, docs, vals(su, same_number_donors(docs, mate, FROZEN61["same_seed"])))
    out["baseline_margin"] = backend.baseline_margin(docs) if hasattr(backend, "baseline_margin") else None
    out["minimal_pair_confirmed"] = bool(res["supported"] and out["self_donor_ok"])
    out.update(ceiling=v50.CEILING, frozen61_digest=FROZEN61_DIGEST)
    return out


def make_backend_class():
    base = v60.make_backend_class()

    class V61Backend(base):
        def baseline_margin(self, docs):
            """Mean unpatched (correct - wrong) verb margin over docs; sanity for out-of-distribution prefixes."""
            torch = self.torch
            self._reset()
            tot, cnt = 0.0, 0
            for _, gids in self._groups(docs).items():
                for j in range(0, len(gids), 128):
                    chunk = gids[j:j + 128]
                    enc = self.tok([self._items[i][0] for i in chunk], return_tensors="pt").to(self.dev)
                    g = torch.tensor([self.tok.encode(self._items[i][1], add_special_tokens=False)[0] for i in chunk], device=self.dev)
                    b = torch.tensor([self.tok.encode(self._items[i][2], add_special_tokens=False)[0] for i in chunk], device=self.dev)
                    with torch.no_grad():
                        m = self._readout(self.m(**enc).logits, g, b, "margin")
                    tot += float(m.float().sum()); cnt += len(chunk)
            return tot / max(cnt, 1)
    return V61Backend
