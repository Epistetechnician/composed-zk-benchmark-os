"""Lanes C and D, real: governed weight update with checkpoints (node-side, offline, fp32).

Update: AdamW (lr 1e-5, batch 32) on correct-verb cross-entropy over fit-template prompts.
Checkpoints at STEPS. Lane C (descriptive, never a gate): matched-random ablation delta of
the step-0 selected set next to behavioral gates. Lane D (descriptive): share of the strongest
selected neurons' activation mass on adjacent (held-out agreement templates) vs unrelated inputs.
Deviation from the Lane D spec: measured on this run's checkpoints, not on closed-family artifacts.
"""
import json, os, random, statistics, sys, time
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
import torch
import v49
from torch_backend import TorchBackend

STEPS = (0, 10, 20, 40, 80)
CFG = {"seed": 60, "k": 32, "draws": 1000, "ctl_draws_per_ckpt": 200, "lr": 1e-5}
UNRELATED = ["The weather today was", "She walked slowly toward the", "In 1990 the company", "He opened the old",
             "My favorite color is", "The meeting will begin at", "A small bird landed on the",
             "They decided to travel to", "The recipe calls for two", "It was a quiet", "Water boils at",
             "The film starts at"]


class C(TorchBackend):
    sig = None

    def _hook(self, k):
        base = super()._hook(k)

        def h(mod, args):
            if self.sig is not None and self.sig.get(k):
                self.sig_vals.append(args[0][:, -1].float()[:, self.sig[k]].detach())
            return base(mod, args)
        return h

    def per_doc_act(self, units, ids):
        out = {}
        for i in ids:
            self.sig = {}
            for u in units:
                self.sig.setdefault(u // self.I, []).append(u % self.I)
            self.sig_vals = []
            with torch.no_grad():
                self._margin([i])
            self.sig = None
            out[i] = float(torch.cat([t.flatten() for t in self.sig_vals]).abs().mean())
        return out

    def accuracy(self, docs):
        with torch.no_grad():
            return float((self._margin(list(docs)) > 0).float().mean())


path, out = sys.argv[1], sys.argv[2]
be = C(path)
be.m.float()
for p in be.m.parameters():
    p.requires_grad_(True)
sp = be.split()
sel = v49.select_units(be.scores(sp["fit"]), CFG["k"])
cand = v49.matched_pool(be.magnitude(), sel, be.layers())
ctl = v49.draw_controls(cand, sel, CFG["draws"], CFG["seed"] + 1)
A = sp["assess"]
for j, t in enumerate(UNRELATED):
    be._docs["u%d" % j] = (t, " are", " is")
U = ["u%d" % j for j in range(len(UNRELATED))]
# strongest selected neurons by step-0 mean |activation| on assess docs
a0 = be.per_doc_act(sel, A[:1])
tops = []
for u in sel:
    v = be.per_doc_act([u], A[:24])
    tops.append((statistics.mean(v.values()), u))
top8 = [u for _, u in sorted(tops, reverse=True)[:8]]
opt = torch.optim.AdamW([p for p in be.m.parameters()], lr=CFG["lr"])
rng = random.Random(CFG["seed"])
fit = sp["fit"]
rows, d_ck = [], []
step = 0
for target in STEPS:
    be.m.eval()
    while step < target:
        be.m.train()
        batch = rng.sample(fit, 32)
        be._reset()
        loss = -be._margin(batch).mean()  # increase correct-minus-wrong margin
        opt.zero_grad(); loss.backward(); opt.step(); step += 1
        be.m.eval()
    be._base = {}
    eff = be.effect(sel, A)
    ce = [be.effect(c, A) for c in ctl[:CFG["ctl_draws_per_ckpt"]]]
    base_margin = be._base[tuple(A)]
    be._reset()
    rows.append({"step": target, "behavior": {"mean_margin": base_margin, "accuracy": be.accuracy(A)},
                 "lane_c": v49.lane_c_report({"accuracy_nonregression": True}, eff, ce) | {
                     "effect": eff, "control_mean": statistics.mean(ce), "control_sd": statistics.pstdev(ce)}})
    acts = {}
    acts.update(be.per_doc_act(top8, A[:24]))
    acts.update(be.per_doc_act(top8, U))
    d_ck.append(acts)
adj = set(A[:24])
laneD = v49.lane_d_diagnostic(d_ck, adj)
base_acc = rows[0]["behavior"]["accuracy"]
for r in rows:
    r["lane_c"]["behavior_gates"] = {"accuracy_nonregression": r["behavior"]["accuracy"] >= base_acc - 0.02}
res = {"cfg": CFG, "selected": sel, "top8": top8, "checkpoints": rows, "lane_d": laneD,
       "note": "descriptive only; Lane D measured on this run's checkpoints (spec deviation)"}
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({"lane_c": [(r["step"], round(r["lane_c"]["effect"], 3), round(r["lane_c"]["ablation_delta"], 3), round(r["behavior"]["accuracy"], 3)) for r in rows], "lane_d": laneD}, indent=1))
