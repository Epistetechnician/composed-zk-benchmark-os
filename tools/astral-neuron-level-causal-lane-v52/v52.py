"""V52: V51 protocol unchanged (corpus, gate v3, thresholds) with a higher spend cap and incremental
JSONL checkpointing so no partial run is lost. State slices: astral-neuron-level-causal-lane-v52-execution,
instrument-validity-gate-v3. Protocol: doc 134."""
import hashlib, json, os, sys, time
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "astral-neuron-level-causal-lane-v51"))
sys.path.insert(0, os.path.join(HERE, "..", "astral-neuron-level-causal-lane-v50"))
import v50, v51

FROZEN52 = {"spend_cap_usd": 10.00, "total_ceiling_usd": 40.00, "inherits": "v51"}
FROZEN52_DIGEST = v50.digest(FROZEN52)


def _summ(x):
    try:
        s = json.dumps(x, sort_keys=True, default=str)
    except Exception:
        s = repr(x)
    if len(s) <= 4000:
        return {"value": json.loads(s) if s[:1] in "[{0123456789-" else s}
    return {"len": len(s), "sha256": hashlib.sha256(s.encode()).hexdigest()}


class Recorder:
    """Proxy: appends one fsync'd JSONL line per backend call."""
    def __init__(self, backend, path):
        self._b, self._f, self._t0 = backend, open(path, "a"), time.time()
        self.log("start", {})

    def log(self, name, extra):
        self._f.write(json.dumps({"t": round(time.time() - self._t0, 2), "call": name, **extra}, sort_keys=True) + "\n")
        self._f.flush(); os.fsync(self._f.fileno())

    def __getattr__(self, name):
        attr = getattr(self._b, name)
        if not callable(attr):
            return attr

        def call(*a, **k):
            r = attr(*a, **k)
            self.log(name, _summ(r))
            return r
        return call


def make_backend_class():
    return v51.make_backend_class()
