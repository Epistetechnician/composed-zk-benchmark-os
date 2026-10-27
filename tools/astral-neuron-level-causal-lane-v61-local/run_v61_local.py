"""V61-local runner (Apple MPS, float32, offline, no provider). Protocol doc 201."""
import argparse, json, os, sys, time
os.environ["HF_HUB_OFFLINE"] = "1"; os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
import v61
from v61 import v50
import v60, v51, v52, pythia_plan


def main(argv=None, backend_factory=None):
    a = argparse.ArgumentParser()
    for n in ("v50_packet", "model_dir", "corpus", "out", "expected_corpus_digest", "code_commit", "v54_out"):
        a.add_argument("--" + n.replace("_", "-"), required=True)
    a.add_argument("--seed", type=int, default=71)
    args = a.parse_args(argv)
    m = json.load(open(args.v50_packet))["models"][v51.FROZEN51["model"]]
    pythia_plan.verify_model_dir(args.model_dir, m["file_hashes"])
    corpus = json.load(open(args.corpus))
    cd = v50.digest(corpus["manifest"])
    if cd != args.expected_corpus_digest:
        raise v50.V50Error("corpus manifest differs from expected digest")
    cfg = {"seed": args.seed, "target_layers": list(m["layers"]), "model_id": m["hf_id"] + "@" + m["revision"],
           "corpus_digest": cd, "code_commit": args.code_commit}
    if backend_factory is None:
        def backend_factory(model_dir, items, layers):
            b = v60.make_backend_class()(model_dir, items, layers, device=os.environ.get("V61_DEVICE", "mps"))
            b.m.float()
            return b
    backend = backend_factory(args.model_dir, dict(corpus["split_items"]), m["layers"])
    rec = v52.Recorder(backend, args.out + ".jsonl")
    t0 = time.time()
    res = v61.run_v61(rec, cfg, json.load(open(args.v54_out))["selected"],
                      log=lambda *x: print("%.0fs" % (time.time() - t0), *x, flush=True))
    res.update(wall_seconds=round(time.time() - t0, 1), device=os.environ.get("V61_DEVICE", "mps"), spend_usd=0.0)
    json.dump(res, open(args.out, "w"), indent=1, sort_keys=True)
    return res


if __name__ == "__main__":
    main()
