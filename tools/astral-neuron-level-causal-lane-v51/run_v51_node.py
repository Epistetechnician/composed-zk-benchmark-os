"""V51 node runner (offline). Requires receipt, model hashes (from the V50 packet), corpus digest, spend cap.
State slices: astral-neuron-level-causal-lane-v51-execution, instrument-validity-gate-v3."""
import argparse, json, os, sys, threading, time
os.environ["HF_HUB_OFFLINE"] = "1"; os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
V50 = os.path.join(os.path.dirname(__file__), "..", "astral-neuron-level-causal-lane-v50")
sys.path.insert(0, V50)
import pythia_plan, v50, v51


def main(argv=None, backend_factory=None):
    a = argparse.ArgumentParser()
    for n in ("v50_packet", "model_dir", "corpus", "receipt", "out", "expected_corpus_digest", "code_commit"):
        a.add_argument("--" + n.replace("_", "-"), required=True)
    a.add_argument("--usd-per-hour", type=float, required=True)
    a.add_argument("--spent-so-far", type=float, default=0.0)
    a.add_argument("--seed", type=int, default=71)
    args = a.parse_args(argv)
    pk = json.load(open(args.v50_packet))
    m = pk["models"][v51.FROZEN51["model"]]
    pythia_plan.verify_model_dir(args.model_dir, m["file_hashes"])
    corpus = json.load(open(args.corpus))
    cd = v50.digest(corpus["manifest"])
    if cd != args.expected_corpus_digest:
        raise v50.V50Error("corpus manifest differs from expected digest")
    receipt = json.load(open(args.receipt))
    if not receipt.get("allocation_id") or args.spent_so_far < 0 or args.spent_so_far >= v51.FROZEN51["spend_cap_usd"]:
        raise v50.V50Error("receipt missing or no budget")
    guard = v50.SpendGuard(receipt["allocation_id"], cap=min(v50.FROZEN["spend_cap_usd"], v51.FROZEN51["spend_cap_usd"]) - args.spent_so_far)
    dog = threading.Timer(guard.cap / args.usd_per_hour * 3600 * 0.95, lambda: os._exit(3)); dog.daemon = True; dog.start()
    t0 = time.time()
    cfg = {"seed": args.seed, "k": v50.FROZEN["k"], "draws": v50.FROZEN["min_draws"], "alpha": 0.05,
           "target_layers": list(m["layers"]), "model_id": m["hf_id"] + "@" + m["revision"],
           "corpus_digest": cd, "code_commit": args.code_commit, "note": ""}
    backend = (backend_factory or v51.make_backend_class())(args.model_dir, corpus["split_items"], m["layers"])
    try:
        res = v51.run_v51(backend, cfg)
    finally:
        dog.cancel()
    guard.charge((time.time() - t0) / 3600 * args.usd_per_hour)
    res.update(spend_usd=round(guard.spent, 4), model_key=v51.FROZEN51["model"], frozen51_digest=v51.FROZEN51_DIGEST)
    json.dump(res, open(args.out, "w"), indent=1, sort_keys=True)
    return res


if __name__ == "__main__":
    main()
