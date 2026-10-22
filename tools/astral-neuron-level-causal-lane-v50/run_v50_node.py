"""V50 node runner (offline). Refuses to run unless the packet is strictly frozen, model files match
their recorded hashes, the corpus manifest matches, and a spend receipt exists.
State slices: astral-neuron-level-causal-lane-v50-execution, instrument-validity-gate-v2.
Usage: run_v50_node.py --packet P --model-key pythia-1.4b --model-dir D --corpus C.json
       --receipt R.json --usd-per-hour N --out OUT.json
Writes aggregate-only output. Raw traces are never written by this script."""
import argparse
import json
import os
import sys
import threading
import time

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
import packet as pk_mod
import pythia_plan
import v50


def main(argv=None, backend_factory=None):
    a = argparse.ArgumentParser()
    for n in ("packet", "model_key", "model_dir", "corpus", "receipt", "out"):
        a.add_argument("--" + n.replace("_", "-"), required=True)
    a.add_argument("--usd-per-hour", type=float, required=True)
    a.add_argument("--seed", type=int, default=71)
    a.add_argument("--code-commit", default=None)
    args = a.parse_args(argv)
    pk = json.load(open(args.packet))
    pk_mod.verify_packet(pk, strict=True)
    m = pk["models"][args.model_key]
    pythia_plan.verify_model_dir(args.model_dir, m["file_hashes"])
    corpus = json.load(open(args.corpus))
    if v50.digest(corpus["manifest"]) != pk["corpus"]["manifest_digest"]:
        raise v50.V50Error("corpus manifest differs from packet")
    receipt = json.load(open(args.receipt))
    if v50.digest(receipt) != pk["node"]["receipt_digest"] or not receipt.get("allocation_id"):
        raise v50.V50Error("receipt missing or differs from packet")
    guard = v50.SpendGuard(receipt["allocation_id"])
    max_s = guard.cap / args.usd_per_hour * 3600 * 0.95
    t0 = time.time()
    dog = threading.Timer(max_s, lambda: os._exit(3))  # hard stop before the cap can be breached
    dog.daemon = True
    dog.start()
    cfg = {"seed": args.seed, "k": v50.FROZEN["k"], "draws": v50.FROZEN["min_draws"], "alpha": 0.05,
           "target_layers": list(m["layers"]), "model_id": m["hf_id"] + "@" + m["revision"],
           "corpus_digest": pk["corpus"]["manifest_digest"], "code_commit": pk["code_commit"], "note": ""}
    factory = backend_factory or __import__("pythia_backend").PythiaBackend
    backend = factory(args.model_dir, corpus["split_items"], m["layers"])
    try:
        res = v50.run_v50(backend, cfg)
    finally:
        dog.cancel()
    guard.charge((time.time() - t0) / 3600 * args.usd_per_hour)
    res.update(packet_digest=pk["packet_digest"], spend_usd=round(guard.spent, 4), model_key=args.model_key)
    json.dump(res, open(args.out, "w"), indent=1, sort_keys=True)
    return res


if __name__ == "__main__":
    main()
