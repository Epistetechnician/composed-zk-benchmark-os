import json, os, sys, time
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
import v49
from torch_backend import TorchBackend

path = sys.argv[1]
cfg = {"seed": 49, "k": 32, "draws": 1000, "min_effect": 0.5, "alpha": 0.05, "note": "preregistered V49 local run"}
t = time.time()
be = TorchBackend(path)
res = v49.run_v49(be, cfg)
res["cfg"] = cfg
res["n_docs"] = len(be.docs())
res["model_path"] = path
res["seconds"] = round(time.time() - t, 1)
json.dump(res, open(sys.argv[2], "w"), indent=1)
print(json.dumps({k: res[k] for k in ("status", "results", "controls", "holm_reject", "seconds")}, indent=1))
