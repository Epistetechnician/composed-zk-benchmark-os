"""r4: template-held-out V49 + Lane B gate (known-bad needs |z|<2 AND |effect|<10% of selected) (node-side, offline)."""
import json, math, os, random, statistics, sys, time
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
import torch
import v49
from torch_backend import TorchBackend, LAYERS

CFG = {"seed": 52, "k": 32, "draws": 1000, "min_effect": 0.5, "alpha": 0.05}


class B(TorchBackend):
    sig = None

    def _hook(self, k):
        base = super()._hook(k)

        def h(mod, args):
            if self.sig is not None:
                x = args[0][:, -1].float()
                idx = self.sig.get(k)
                if idx:
                    self.sig_vals.extend(x[:, idx].flatten().tolist())
            return base(mod, args)
        return h

    def lp(self, units, docs):
        self._ablate(units)
        with torch.no_grad():
            enc = self.tok([self._docs[i][0] for i in docs], return_tensors="pt").to("cuda")
            lg = self.m(**enc).logits[:, -1].float().log_softmax(-1)
            g = torch.tensor([self.tok.encode(self._docs[i][1])[0] for i in docs], device="cuda")
            v = float(lg.gather(1, g[:, None]).mean())
        self._reset()
        return v

    def lp_effect(self, units, docs):
        return self.lp([], docs) - self.lp(units, docs)

    def signed(self, units, docs):
        self._reset()
        self.sig = {}
        for u in units:
            self.sig.setdefault(u // self.I, []).append(u % self.I)
        self.sig_vals = []
        with torch.no_grad():
            self._margin(list(docs))
        self.sig = None
        return self.sig_vals


def z(effect, ce):
    sd = statistics.pstdev(ce) or 1e-9
    return (effect - statistics.mean(ce)) / sd


def kurt(v):
    m = statistics.mean(v); s = statistics.pstdev(v) or 1e-9
    return sum(((x - m) / s) ** 4 for x in v) / len(v) - 3


path, out = sys.argv[1], sys.argv[2]
be = B(path)
sp = be.split()
assert not (set(sp['fit']) & set(sp['assess'])) and not (set(sp['fit']) & set(sp['tune']))
sel = v49.select_units(be.scores(sp["fit"]), CFG["k"])
cand = v49.matched_pool(be.magnitude(), sel, be.layers())
ctl = v49.draw_controls(cand, sel, CFG["draws"], CFG["seed"] + 1)
A = sp["assess"]
e_margin = be.effect(sel, A)
c_margin = [be.effect(c, A) for c in ctl]
e_lp = be.lp_effect(sel, A)
c_lp = [be.lp_effect(c, A) for c in ctl]
p_m, p_l = v49.one_sided_p(e_margin, c_margin), v49.one_sided_p(e_lp, c_lp)
z_m, z_l = z(e_margin, c_margin), z(e_lp, c_lp)
vals = be.signed(sel, A)
# positive control: ablate top-512 attributed units; near miss: fit ranks 33-64
scores = be.scores(sp["fit"])
rank = sorted(scores, key=lambda u: (-abs(scores[u]), u))
pos = be.effect(rank[:512], A)
near = rank[CFG["k"]:2 * CFG["k"]]
e_near = be.effect(near, A)
# known-bad instrument: shuffled-label readout must not separate from matched controls
rng = random.Random(23)
flip = [rng.random() < 0.5 for _ in A]
def shuf(units):
    be._reset(); b0 = be._mean_margin(A, flip); be._ablate(units); e = b0 - be._mean_margin(A, flip); be._reset(); return e
e_bad = shuf(sel); c_bad = [shuf(c) for c in ctl[:300]]
z_bad = z(e_bad, c_bad)
# r4 lens criterion (preregistered): both readouts separate (z>=3, p<alpha), same sign; no scale tolerance
tol = 1e9 if (z_m >= 3 and z_l >= 3 and p_m < CFG['alpha'] and p_l < CFG['alpha']) else -1.0
gate = v49.instrument_validity_gate(
    {"margin_z": lambda v: z_m, "logprob_z": lambda v: z_l},
    {"values": vals, "lens_tol": tol, "positive_control": pos > e_margin,
     "near_miss_rejected": e_near < e_margin, "known_bad_fails": abs(z_bad) < 2.0 and abs(e_bad) < 0.1 * abs(e_margin)})
res = {"gate": gate, "readouts": {"margin": {"effect": e_margin, "p": p_m, "z": z_m},
       "logprob": {"effect": e_lp, "p": p_l, "z": z_l}},
       "tail": {"n": len(vals), "min": min(vals), "max": max(vals), "pos_frac": sum(x > 0 for x in vals) / len(vals),
                "excess_kurtosis": kurt(vals), "mean": statistics.mean(vals)},
       "positive_control_effect": pos, "near_miss_effect": e_near, "selected_effect": e_margin,
       "known_bad": {"effect": e_bad, "z": z_bad}, "lens_tol": tol, "cfg": CFG}
full = v49.run_v49(be, {**CFG, 'note': 'r3 template-heldout'})
res['v49_run'] = full
res['r3_verdict'] = 'Candidate+InstrumentValid' if (full['status']=='Candidate' and gate['status']=='InstrumentValid') else 'NotValidated'
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))
