"""V61 node runner (minimal-pair donor patching on the locked V54 selection, Pythia-2.8b). Log at <out>.jsonl."""
import argparse, json, os, sys, threading, time
os.environ["HF_HUB_OFFLINE"] = "1"; os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
import v61
from v61 import v50, v60
import v51, v52, v53
import pythia_plan


def main(argv=None, backend_factory=None):
    a = argparse.ArgumentParser()
    for n in ("v50_packet", "model_dir", "corpus", "receipt", "out", "expected_corpus_digest", "code_commit", "v54_out", "v58_out"):
        a.add_argument("--" + n.replace("_", "-"), required=True)
    a.add_argument("--usd-per-hour", type=float, required=True)
    a.add_argument("--seed", type=int, default=71)
    args = a.parse_args(argv)
    cap = v61.FROZEN61["spend_cap_usd"]
    m = json.load(open(args.v50_packet))["models"][v51.FROZEN51["model"]]
    pythia_plan.verify_model_dir(args.model_dir, m["file_hashes"])
    corpus = json.load(open(args.corpus))
    cd = v50.digest(corpus["manifest"])
    if cd != args.expected_corpus_digest:
        raise v50.V50Error("corpus manifest differs from expected digest")
    receipt = json.load(open(args.receipt))
    if not receipt.get("allocation_id"):
        raise v50.V50Error("receipt missing")
    guard = v50.SpendGuard(receipt["allocation_id"], cap=cap)
    holder = {}

    def kill():
        if "rec" in holder:
            holder["rec"].log("watchdog_kill", {})
        os._exit(3)
    dog = threading.Timer(cap / args.usd_per_hour * 3600 * 0.95, kill); dog.daemon = True; dog.start()
    t0 = time.time()
    cfg = {"seed": args.seed, "k": v50.FROZEN["k"], "target_layers": list(m["layers"]),
           "model_id": m["hf_id"] + "@" + m["revision"], "corpus_digest": cd, "code_commit": args.code_commit}
    items = dict(corpus["split_items"])
    items["minpair"], _ = v61.build_minpairs(v61.FROZEN61["pair_seed"], v61.FROZEN61["n_pairs"])
    backend = (backend_factory or v61.make_backend_class())(args.model_dir, items, m["layers"])
    holder["rec"] = v52.Recorder(backend, args.out + ".jsonl")
    try:
        res = v61.run_v61(holder["rec"], cfg, json.load(open(args.v54_out)), json.load(open(args.v58_out)))
    finally:
        dog.cancel()
    guard.charge((time.time() - t0) / 3600 * args.usd_per_hour)
    res.update(spend_usd=round(guard.spent, 4))
    json.dump(res, open(args.out, "w"), indent=1, sort_keys=True)
    return res


if __name__ == "__main__":
    main()
