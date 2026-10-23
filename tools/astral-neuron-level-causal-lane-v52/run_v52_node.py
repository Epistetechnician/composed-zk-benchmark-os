"""V52 node runner (offline). Same inputs as V51 runner; cap 10.00; incremental log at <out>.jsonl."""
import argparse, json, os, sys, threading, time
os.environ["HF_HUB_OFFLINE"] = "1"; os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
import v52
from v52 import v50, v51
import pythia_plan


def main(argv=None, backend_factory=None):
    a = argparse.ArgumentParser()
    for n in ("v50_packet", "model_dir", "corpus", "receipt", "out", "expected_corpus_digest", "code_commit"):
        a.add_argument("--" + n.replace("_", "-"), required=True)
    a.add_argument("--usd-per-hour", type=float, required=True)
    a.add_argument("--spent-so-far", type=float, default=0.0)
    a.add_argument("--seed", type=int, default=71)
    args = a.parse_args(argv)
    cap = v52.FROZEN52["spend_cap_usd"]
    pk = json.load(open(args.v50_packet))
    m = pk["models"][v51.FROZEN51["model"]]
    pythia_plan.verify_model_dir(args.model_dir, m["file_hashes"])
    corpus = json.load(open(args.corpus))
    cd = v50.digest(corpus["manifest"])
    if cd != args.expected_corpus_digest:
        raise v50.V50Error("corpus manifest differs from expected digest")
    receipt = json.load(open(args.receipt))
    if not receipt.get("allocation_id") or args.spent_so_far < 0 or args.spent_so_far >= cap:
        raise v50.V50Error("receipt missing or no budget")
    guard = v50.SpendGuard(receipt["allocation_id"], cap=cap - args.spent_so_far)
    log_path = args.out + ".jsonl"
    holder = {}

    def kill():
        if "rec" in holder:
            holder["rec"].log("watchdog_kill", {})
        os._exit(3)
    dog = threading.Timer(guard.cap / args.usd_per_hour * 3600 * 0.95, kill); dog.daemon = True; dog.start()
    t0 = time.time()
    cfg = {"seed": args.seed, "k": v50.FROZEN["k"], "draws": v50.FROZEN["min_draws"], "alpha": 0.05,
           "target_layers": list(m["layers"]), "model_id": m["hf_id"] + "@" + m["revision"],
           "corpus_digest": cd, "code_commit": args.code_commit, "note": ""}
    backend = (backend_factory or v52.make_backend_class())(args.model_dir, corpus["split_items"], m["layers"])
    holder["rec"] = v52.Recorder(backend, log_path)
    try:
        res = v51.run_v51(holder["rec"], cfg)
    finally:
        dog.cancel()
    guard.charge((time.time() - t0) / 3600 * args.usd_per_hour)
    res.update(spend_usd=round(guard.spent, 4), model_key=v51.FROZEN51["model"],
               frozen51_digest=v51.FROZEN51_DIGEST, frozen52_digest=v52.FROZEN52_DIGEST)
    json.dump(res, open(args.out, "w"), indent=1, sort_keys=True)
    return res


if __name__ == "__main__":
    main()
