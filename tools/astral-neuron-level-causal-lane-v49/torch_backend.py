"""CUDA/torch backend for V49 (node-side; run with HF_HUB_OFFLINE=1).

Units: MLP intermediate neurons (input to down_proj) at LAYERS of a cached Qwen3
checkpoint, id = k*I + i. Task: subject-verb agreement logit margin
(correct-verb minus wrong-verb logit at the final position). Effect(S) is the
margin drop when S is zeroed at every position, mean over docs. Fit score is
+d margin / d mask (first-order margin drop under ablation), positive part.
"""
import random

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

LAYERS = (10, 16, 22)
SUBJ = [("The {} keys to the cabinet", " are", " is"), ("The {} dogs near the door", " are", " is"),
        ("The {} author of the books", " is", " are"), ("The {} pilot of the planes", " is", " are"),
        ("The {} cars behind the house", " are", " is"), ("The {} teacher of the students", " is", " are")]
FILL = ["old", "red", "new", "big", "tiny", "dusty", "quiet", "loud", "green", "heavy",
        "small", "bright", "cold", "warm", "plain", "rusty", "silver", "golden"]


class TorchBackend:
    def __init__(self, path, ndocs=360, seed=0):
        self.tok = AutoTokenizer.from_pretrained(path, local_files_only=True)
        self.m = AutoModelForCausalLM.from_pretrained(
            path, torch_dtype=torch.bfloat16, local_files_only=True).cuda().eval()
        for p in self.m.parameters():
            p.requires_grad_(False)
        self.I = self.m.config.intermediate_size
        self.mask = {k: torch.ones(self.I, device="cuda", dtype=torch.float32) for k in range(len(LAYERS))}
        for k, l in enumerate(LAYERS):
            self.m.model.layers[l].mlp.down_proj.register_forward_pre_hook(self._hook(k))
        self.capture, self.acts = False, {}
        rng = random.Random(seed)
        cand = {}
        for i in range(ndocs * 3):
            t, good, bad = rng.choice(SUBJ)
            text = t.format(rng.choice(FILL))
            n = len(self.tok.encode(text))
            cand.setdefault(n, []).append((text, good, bad))
        n = max(cand, key=lambda x: len(cand[x]))
        self._docs = {"d%d" % i: d for i, d in enumerate(cand[n][:ndocs])}
        self._base = {}

    def _hook(self, k):
        def h(mod, args):
            x = args[0]
            if self.capture:
                self.acts[k] = self.acts.get(k, 0) + x.detach().abs().float().sum((0, 1))
                self.acts[("n", k)] = self.acts.get(("n", k), 0) + x.shape[0] * x.shape[1]
            return (x * self.mask[k].to(x.dtype),)
        return h

    def _margin(self, ids, labels_flip=None):
        enc = self.tok([self._docs[i][0] for i in ids], return_tensors="pt").to("cuda")
        out = self.m(**enc).logits[:, -1].float()
        g = [self.tok.encode(self._docs[i][1])[0] for i in ids]
        b = [self.tok.encode(self._docs[i][2])[0] for i in ids]
        if labels_flip:
            g, b = ([y if f else x for x, y, f in zip(g, b, labels_flip)], [x if f else y for x, y, f in zip(g, b, labels_flip)])
        g = torch.tensor(g, device="cuda")
        b = torch.tensor(b, device="cuda")
        return (out.gather(1, g[:, None]) - out.gather(1, b[:, None])).squeeze(1)

    def _reset(self):
        for k in self.mask:
            self.mask[k] = torch.ones(self.I, device="cuda", dtype=torch.float32)

    def _ablate(self, units):
        self._reset()
        for u in units:
            self.mask[u // self.I][u % self.I] = 0.0

    def docs(self):
        return list(self._docs)

    def layers(self):
        return {k * self.I + i: k for k in range(len(LAYERS)) for i in range(self.I)}

    def scores(self, fit):
        self._reset()
        for k in self.mask:
            self.mask[k].requires_grad_(True)
        tot = {k: torch.zeros(self.I, device="cuda") for k in self.mask}
        for j in range(0, len(fit), 32):
            for k in self.mask:
                self.mask[k].grad = None
            self._margin(fit[j:j + 32]).sum().backward()
            for k in self.mask:
                tot[k] += self.mask[k].grad
        self._reset()
        return {k * self.I + i: max(0.0, float(tot[k][i])) for k in tot for i in range(self.I)}

    def magnitude(self):
        self._reset()
        self.capture, self.acts = True, {}
        with torch.no_grad():
            ids = self.docs()
            for j in range(0, len(ids), 64):
                self._margin(ids[j:j + 64])
        self.capture = False
        mag = {}
        for k in self.mask:
            a = self.acts[k] / self.acts[("n", k)]
            for i in range(self.I):
                mag[k * self.I + i] = float(a[i])
        return mag

    def _mean_margin(self, docs, flip=None):
        with torch.no_grad():
            return float(self._margin(list(docs), flip).mean())

    def effect(self, units, docs):
        key = tuple(docs)
        if key not in self._base:
            self._reset()
            self._base[key] = self._mean_margin(docs)
        self._ablate(units)
        e = self._base[key] - self._mean_margin(docs)
        self._reset()
        return e

    def control_effect(self, name, units, docs):
        if name == "text_only":  # identity: ablating nothing
            return 0.0
        if name == "shuffled":  # labels swapped at random: effect should vanish
            rng = random.Random(11)
            flip = [rng.random() < 0.5 for _ in docs]
            self._reset()
            base = self._mean_margin(docs, flip)
            self._ablate(units)
            e = base - self._mean_margin(docs, flip)
            self._reset()
            return e
        if name == "constant":  # same ablation on an unrelated constant prompt
            self._docs["_c"] = ("The", self._docs[docs[0]][1], self._docs[docs[0]][2])
            self._reset()
            base = self._mean_margin(["_c"])
            self._ablate(units)
            e = base - self._mean_margin(["_c"])
            self._reset()
            del self._docs["_c"]
            return e
        raise ValueError(name)
