"""V53: V52 unchanged except the single-item 'constant' control is replaced by a many-item constant control
with a paired specificity test. State slices: astral-neuron-level-causal-lane-v53-execution,
instrument-validity-gate-v3. Protocol: doc 135."""
import math, os, sys
HERE = os.path.dirname(__file__)
for d in ("astral-neuron-level-causal-lane-v52", "astral-neuron-level-causal-lane-v51", "astral-neuron-level-causal-lane-v50"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
import v50, v51, v52

FROZEN53 = {"spend_cap_usd": 6.00, "total_ceiling_usd": 40.00, "const_abs_max": 0.5,
            "specific_min_gap": 0.5, "specific_min_z": 4.0, "inherits": "v52"}
FROZEN53_DIGEST = v50.digest(FROZEN53)


def specificity(real_drops, const_drops):
    """Per-document paired test. real/const: per-doc margin drops under ablation. Returns stats + pass flag."""
    n = len(real_drops)
    diff = [r - c for r, c in zip(real_drops, const_drops)]
    mean = sum(diff) / n
    var = sum((x - mean) ** 2 for x in diff) / (n - 1)
    se = math.sqrt(var / n) if var > 0 else float("inf")
    z = mean / se if se not in (0, float("inf")) else 0.0
    cm = sum(const_drops) / n
    ok = cm < FROZEN53["const_abs_max"] and mean >= FROZEN53["specific_min_gap"] and z >= FROZEN53["specific_min_z"]
    return {"n": n, "real_mean": sum(real_drops) / n, "const_mean": cm, "specific_gap": mean, "se": se, "z": z,
            "const_frac_of_real": cm / (sum(real_drops) / n) if sum(real_drops) else None, "pass": ok}


def make_backend_class():
    base = v51.make_backend_class()

    class V53Backend(base):
        spec_stats = None

        def paired_drops(self, units, docs):
            docs = list(docs)
            for i in docs:
                t = self._items[i]
                self._items["_c" + i] = ("The", t[1], t[2])
            cids = ["_c" + i for i in docs]
            self._reset()
            b_real, b_c = self._margins(docs), self._margins(cids)
            self._ablate(units)
            a_real, a_c = self._margins(docs), self._margins(cids)
            self._reset()
            for c in cids:
                del self._items[c]
            return [x - y for x, y in zip(b_real, a_real)], [x - y for x, y in zip(b_c, a_c)]

        def control_effect(self, name, units, docs):
            if name != "constant":
                return super().control_effect(name, units, docs)
            r, c = self.paired_drops(units, docs)
            self.spec_stats = specificity(r, c)
            e = self.spec_stats["const_mean"]
            # v50's 'separates' is e >= min_effect; a failed specificity test must also separate.
            return e if self.spec_stats["pass"] else max(e, v50.FROZEN["min_effect"])
    return V53Backend


def run_v53(backend, cfg):
    if v50.digest(FROZEN53) != FROZEN53_DIGEST:
        raise v50.V50Error("V53 frozen values changed")
    res = v51.run_v51(backend, cfg)
    inner = getattr(backend, "_b", backend)
    res["specificity"] = inner.spec_stats
    return res
