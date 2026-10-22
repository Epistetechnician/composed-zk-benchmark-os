"""V50 torch backend for GPT-NeoX (Pythia). Node-side, offline only.

State slices: astral-neuron-level-causal-lane-v50-execution, instrument-validity-gate-v2.
NOT exercised in the authoring environment (no torch). Verified only by the torch-gated test
and by the contract tests. Units: MLP hidden neurons (input of dense_4h_to_h) at the plan
layers, id = k * I + i. Effect(S) = mean margin drop when S is zeroed at every position.
Path components are block-level (attention and MLP output per layer >= first target layer);
per-head components are not implemented (a deviation to freeze in the packet).
"""
import os
import random

PATH_DOCS = 64


class PythiaBackend:
    def __init__(self, model_dir, split_items, target_layers, device="cuda"):
        if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
            raise RuntimeError("offline env required: HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1")
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch, self.dev = torch, device
        self.tok = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        self.m = AutoModelForCausalLM.from_pretrained(
            model_dir, torch_dtype=torch.bfloat16, local_files_only=True).to(device).eval()
        if self.m.config.model_type != "gpt_neox":
            raise RuntimeError("not a gpt_neox model")
        for p in self.m.parameters():
            p.requires_grad_(False)
        self.LY = tuple(target_layers)
        self.n_layers = self.m.config.num_hidden_layers
        self.I = self.m.config.intermediate_size
        self.layers_mod = self.m.gpt_neox.layers
        self._items, self._split = {}, {}
        for part, items in split_items.items():
            for it in items:
                self._items[it["id"]] = (it["text"], it["good"], it["bad"])
                self._split.setdefault(part, []).append(it["id"])
        for it_id, (_, g, b) in self._items.items():
            for t in (g, b):
                if len(self.tok.encode(t, add_special_tokens=False)) != 1:
                    raise RuntimeError("verb not a single token: %r" % t)
        self.mask = {k: torch.ones(self.I, device=device, dtype=torch.float32) for k in range(len(self.LY))}
        for k, l in enumerate(self.LY):
            self.layers_mod[l].mlp.dense_4h_to_h.register_forward_pre_hook(self._mask_hook(k))
        self.capture, self.acts = False, {}
        self.locked, self._base, self._enc = None, {}, {}

    # ---- plumbing ----------------------------------------------------------------
    def _mask_hook(self, k):
        def h(mod, args):
            x = args[0]
            if self.capture:
                self.acts[k] = self.acts.get(k, 0) + x.detach().abs().float().sum((0, 1))
                self.acts[("n", k)] = self.acts.get(("n", k), 0) + x.shape[0] * x.shape[1]
            return (x * self.mask[k].to(x.dtype),)
        return h

    def _reset(self):
        for k in self.mask:
            self.mask[k] = self.torch.ones(self.I, device=self.dev, dtype=self.torch.float32)

    def _ablate(self, units):
        self._reset()
        for u in units:
            self.mask[u // self.I][u % self.I] = 0.0

    def _batches(self, ids, flip=None):
        key = (tuple(ids), tuple(flip) if flip else None)
        if key in self._enc:
            return self._enc[key]
        flips = list(flip) if flip else [False] * len(ids)
        groups = {}
        for pos, i in enumerate(ids):
            groups.setdefault(len(self.tok.encode(self._items[i][0])), []).append(pos)
        out = []
        for _, poss in groups.items():
            for j in range(0, len(poss), 128):
                ps = poss[j:j + 128]
                enc = self.tok([self._items[ids[p]][0] for p in ps], return_tensors="pt").to(self.dev)
                g = [self.tok.encode(self._items[ids[p]][1], add_special_tokens=False)[0] for p in ps]
                b = [self.tok.encode(self._items[ids[p]][2], add_special_tokens=False)[0] for p in ps]
                g, b = ([y if f else x for x, y, f in zip(g, b, [flips[p] for p in ps])],
                        [x if f else y for x, y, f in zip(g, b, [flips[p] for p in ps])])
                out.append((enc, self.torch.tensor(g, device=self.dev), self.torch.tensor(b, device=self.dev)))
        if len(self._enc) > 64:
            self._enc.clear()
        self._enc[key] = out
        return out

    def _readout(self, logits, g, b, readout):
        lg = logits[:, -1].float()
        if readout == "margin":
            return (lg.gather(1, g[:, None]) - lg.gather(1, b[:, None])).squeeze(1)
        return lg.log_softmax(-1).gather(1, g[:, None]).squeeze(1)

    def _mean(self, ids, readout="margin", flip=None):
        tot, n = 0.0, 0
        with self.torch.no_grad():
            for enc, g, b in self._batches(ids, flip):
                tot += float(self._readout(self.m(**enc).logits, g, b, readout).sum())
                n += len(g)
        return tot / n

    # ---- backend contract used by v50.run_v50 -------------------------------------------
    def split(self):
        return {k: sorted(v) for k, v in self._split.items()}

    def layers(self):
        return {k * self.I + i: self.LY[k] for k in range(len(self.LY)) for i in range(self.I)}

    def mark_locked(self, lock):
        self.locked = lock

    def scores(self, fit):
        self._reset()
        for k in self.mask:
            self.mask[k].requires_grad_(True)
        tot = {k: self.torch.zeros(self.I, device=self.dev) for k in self.mask}
        for enc, g, b in self._batches(list(fit)):
            for k in self.mask:
                self.mask[k].grad = None
            self._readout(self.m(**enc).logits, g, b, "margin").sum().backward()
            for k in self.mask:
                tot[k] += self.mask[k].grad
        self._reset()
        return {k * self.I + i: float(tot[k][i]) for k in tot for i in range(self.I)}

    def magnitude(self):
        self._reset()
        self.capture, self.acts = True, {}
        with self.torch.no_grad():
            ids = sorted(self._items)
            for enc, g, b in self._batches(ids):
                self.m(**enc)
        self.capture = False
        return {k * self.I + i: float(self.acts[k][i] / self.acts[("n", k)])
                for k in self.mask for i in range(self.I)}

    def effect(self, units, docs, readout="margin"):
        if self.locked is None and docs != self.split().get("fit"):
            raise RuntimeError("effect on non-fit docs before prediction lock")
        key = (tuple(docs), readout)
        if key not in self._base:
            self._reset()
            self._base[key] = self._mean(list(docs), readout)
        self._ablate(units)
        e = self._base[key] - self._mean(list(docs), readout)
        self._reset()
        return e

    def known_bad_effect(self, shuffle_seed, units, docs):
        rng = random.Random(1000 + shuffle_seed)
        flip = [rng.random() < 0.5 for _ in docs]
        self._reset()
        base = self._mean(list(docs), "margin", flip)
        self._ablate(units)
        e = base - self._mean(list(docs), "margin", flip)
        self._reset()
        return e

    def control_effect(self, name, units, docs):
        if name == "text_only":
            return 0.0
        if name == "shuffled":
            return self.known_bad_effect(11, units, docs)
        if name == "constant":
            first = self._items[docs[0]]
            self._items["_c"] = ("The", first[1], first[2])
            self._reset()
            base = self._mean(["_c"])
            self._ablate(units)
            e = base - self._mean(["_c"])
            self._reset()
            del self._items["_c"]
            return e
        raise ValueError(name)

    def activation_values(self, selected, docs):
        """Pre-activation (dense_h_to_4h output) at the last position, selected neurons, <=64 docs."""
        want = {}
        for u in selected:
            want.setdefault(u // self.I, []).append(u % self.I)
        vals, hs = [], []
        for k, idx in want.items():
            def hook(mod, args, out, idx=idx):
                vals.extend(out[:, -1][:, idx].float().flatten().tolist())
            hs.append(self.layers_mod[self.LY[k]].mlp.dense_h_to_4h.register_forward_hook(hook))
        self._reset()
        try:
            self._mean(sorted(docs)[:PATH_DOCS])
        finally:
            for h in hs:
                h.remove()
        return vals

    # ---- path analysis ----------------------------------------------------------------------
    def _path_docs(self, docs):
        return sorted(docs)[:PATH_DOCS]

    def total_effect(self, units, docs):
        ids = self._path_docs(docs)
        self._reset()
        base = self._mean(ids)
        self._ablate(units)
        e = base - self._mean(ids)
        self._reset()
        return e

    def direct_effect(self, units, docs):
        """Contribution of the units' outputs at the last position through the frozen final norm to
        the good-minus-bad unembedding direction (margin points). Compared against total_effect."""
        torch, ids = self.torch, self._path_docs(docs)
        want = {}
        for u in units:
            want.setdefault(u // self.I, []).append(u % self.I)
        ln, U = self.m.gpt_neox.final_layer_norm, self.m.embed_out.weight
        tot, n = 0.0, 0
        self._reset()
        for enc, g, b in self._batches(ids):
            cap = {}
            hs = []
            for k, idx in want.items():
                mod = self.layers_mod[self.LY[k]].mlp.dense_4h_to_h
                hs.append(mod.register_forward_pre_hook(
                    lambda m_, a, k=k, idx=idx: cap.__setitem__(k, a[0][:, -1][:, idx].float())))
            hs.append(ln.register_forward_pre_hook(lambda m_, a: cap.__setitem__("res", a[0][:, -1].float())))
            with torch.no_grad():
                self.m(**enc)
            for h in hs:
                h.remove()
            contrib = 0
            for k, idx in want.items():
                W = self.layers_mod[self.LY[k]].mlp.dense_4h_to_h.weight[:, idx].float()
                contrib = contrib + cap[k] @ W.T
            c = contrib - contrib.mean(-1, keepdim=True)
            res = cap["res"]
            sd = (res.var(-1, unbiased=False, keepdim=True) + ln.eps).sqrt()
            scaled = c / sd * ln.weight.float()
            d = (U[g].float() - U[b].float())
            tot += float((scaled * d).sum())
            n += len(g)
        return tot / n

    def mediators(self, units, docs):
        """Block-level patching: restore one downstream block's ablated output into the clean run.
        Returns component -> normalized share of positive restoring effects."""
        torch, ids = self.torch, self._path_docs(docs)
        lmin = min(self.LY)
        comps = [(t, l) for l in range(lmin, self.n_layers) for t in ("attn", "mlp")]

        def mod_of(c):
            t, l = c
            return self.layers_mod[l].attention if t == "attn" else self.layers_mod[l].mlp
        eff = {c: 0.0 for c in comps}
        n = 0
        for enc, g, b in self._batches(ids):
            self._reset()
            with torch.no_grad():
                clean = self._readout(self.m(**enc).logits, g, b, "margin")
            cap, hs = {}, []
            for c in comps:
                def cap_hook(m_, a, out, c=c):
                    cap[c] = (out[0] if isinstance(out, tuple) else out).detach()
                hs.append(mod_of(c).register_forward_hook(cap_hook))
            self._ablate(units)
            with torch.no_grad():
                self.m(**enc)
            for h in hs:
                h.remove()
            self._reset()
            for c in comps:
                def patch(m_, a, out, c=c):
                    return (cap[c],) + tuple(out[1:]) if isinstance(out, tuple) else cap[c]
                h = mod_of(c).register_forward_hook(patch)
                with torch.no_grad():
                    patched = self._readout(self.m(**enc).logits, g, b, "margin")
                h.remove()
                eff[c] += float((clean - patched).sum())
            n += len(g)
        pos = {"%s_L%d" % c: max(v / n, 0.0) for c, v in eff.items()}
        s = sum(pos.values())
        return {k: v / s for k, v in pos.items()} if s > 0 else {}
