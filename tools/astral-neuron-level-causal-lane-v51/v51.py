"""V51: null-calibrated instrument gate (v3) around the unchanged V50 run. State slices:
astral-neuron-level-causal-lane-v51-execution, instrument-validity-gate-v3. Protocol: doc 133."""
import math, os, sys
V50 = os.path.join(os.path.dirname(__file__), "..", "astral-neuron-level-causal-lane-v50")
sys.path.insert(0, V50)
import v50

FROZEN51 = {"z_null": 4.0, "z_signal": 10.0, "min_effect": 0.5, "spend_cap_usd": 5.50, "model": "pythia-2.8b"}
FROZEN51_DIGEST = v50.digest(FROZEN51)


def null_gate(kb, eff, s, z_null=None, z_signal=None, min_effect=None):
    """kb: sign-flip draws; s: analytic flip standard error. Returns list of failure names."""
    z_null = FROZEN51["z_null"] if z_null is None else z_null
    z_signal = FROZEN51["z_signal"] if z_signal is None else z_signal
    min_effect = FROZEN51["min_effect"] if min_effect is None else min_effect
    fails = []
    if not (s > 0 and math.isfinite(s)):
        return ["null_scale_invalid"]
    n = len(kb)
    if max(abs(x) for x in kb) > z_null * s or abs(sum(kb) / n) > z_null * s / math.sqrt(n):
        fails.append("null_consistency")
    if eff < z_signal * s:
        fails.append("signal_over_noise")
    if eff < min_effect:
        fails.append("min_effect")
    return fails


def instrument_gate_v3(backend, selected, scores, docs, controls_p, alpha=0.05):
    base = v50.instrument_gate_v2(backend, selected, scores, docs, controls_p, alpha)
    fails = [f for f in base["fails"] if f != "known_bad"]
    detail = dict(base["detail"])
    kb = [backend.known_bad_effect(sd, selected, docs) for sd in range(v50.FROZEN["known_bad_shuffles"])]
    s = backend.flip_scale(selected, docs)
    detail.update(known_bad_draws=kb, flip_scale=s, signal_over_noise=detail["selected_effect"] / s if s else None)
    fails += null_gate(kb, detail["selected_effect"], s)
    return {"status": "InstrumentValid" if not fails else "InstrumentNotValid", "fails": fails,
            "detail": detail, "ceiling": v50.CEILING, "gate": "v3"}


def run_v51(backend, cfg):
    if v50.digest(FROZEN51) != FROZEN51_DIGEST:
        raise v50.V50Error("V51 frozen values changed")
    orig = v50.instrument_gate_v2
    v50.instrument_gate_v2 = instrument_gate_v3
    try:
        return v50.run_v50(backend, cfg)
    finally:
        v50.instrument_gate_v2 = orig


def make_backend_class():
    from pythia_backend import PythiaBackend

    class V51Backend(PythiaBackend):
        def _margins(self, ids):
            groups = {}
            for pos, i in enumerate(ids):
                groups.setdefault(len(self.tok.encode(self._items[i][0])), []).append(pos)
            order = [p for poss in groups.values() for p in poss]
            vals = []
            with self.torch.no_grad():
                for enc, g, b in self._batches(list(ids)):
                    vals += self._readout(self.m(**enc).logits, g, b, "margin").tolist()
            out = [0.0] * len(ids)
            for k, p in enumerate(order):
                out[p] = vals[k]
            return out

        def flip_scale(self, units, docs):
            """s = sqrt(mean(d_i^2)/n): exact standard error of a random sign-flip mean of per-doc drops d_i."""
            docs = list(docs)
            self._reset()
            base = self._margins(docs)
            self._ablate(units)
            abl = self._margins(docs)
            self._reset()
            d = [x - y for x, y in zip(base, abl)]
            return math.sqrt(sum(x * x for x in d) / len(d) / len(d))
    return V51Backend
