"""V50 frozen-packet builder/verifier (pure). State slices: astral-neuron-level-causal-lane-v50-execution.
A packet is 'code-frozen-data-pending' until model hashes, corpus manifest, label audit and node
receipt are recorded; only status 'frozen' passes strict verification (what the node runner needs)."""
import json
import os

import pythia_plan
import v50

CODE = ["v50.py", "v50_corpus.py", "pythia_plan.py", "pythia_backend.py", "packet.py", "run_v50_node.py", "smoke_v50.py",
        "../astral-neuron-level-causal-lane-v49/v49.py"]
PROTOCOL = "../../docs/research/astral-self-modeling/132-neuron-level-causal-lane-v50-protocol.md"
PENDING_FIELDS = ("models.*.revision", "models.*.file_hashes", "models.*.license_checked",
                  "corpus.manifest_digest", "corpus.label_audit", "node.receipt_digest")


class PacketError(ValueError):
    pass


def _here(*p):
    return os.path.join(os.path.dirname(__file__), *p)


def build_packet(code_commit):
    models = {}
    for name, m in pythia_plan.MODELS.items():
        models[name] = {**m, "layers": pythia_plan.layers_for(m["n_layers"]),
                        "revision": None, "file_hashes": None, "license_checked": None}
    pk = {
        "packet": "astral-v50-packet-v1",
        "status": "code-frozen-data-pending",
        "ceiling": v50.CEILING,
        "code_commit": code_commit,
        "protocol_sha256": pythia_plan.file_sha256(_here(PROTOCOL)),
        "code": {c.split("/")[-1]: pythia_plan.file_sha256(_here(c)) for c in CODE},
        "frozen": v50.FROZEN, "frozen_digest": v50.FROZEN_DIGEST,
        "models": models,
        "corpus": {"manifest_digest": None, "label_audit": None},
        "node": {"receipt_digest": None},
        "deviations": ["path components are block-level (attn/mlp per layer), not per head",
                       "H2 uses indirect share and top-2 mediator share",
                       "path analysis runs on up to 64 same-token-length assessment documents (at least 16)"],
    }
    pk["packet_digest"] = v50.digest({k: v for k, v in pk.items() if k != "packet_digest"})
    return pk


def _has_none(pk):
    miss = []
    for n, m in pk["models"].items():
        for f in ("revision", "file_hashes", "license_checked"):
            if not m.get(f):
                miss.append("models.%s.%s" % (n, f))
    for f in ("manifest_digest", "label_audit"):
        if not pk["corpus"].get(f):
            miss.append("corpus." + f)
    if not pk["node"].get("receipt_digest"):
        miss.append("node.receipt_digest")
    return miss


def verify_packet(pk, strict):
    if pk.get("packet_digest") != v50.digest({k: v for k, v in pk.items() if k != "packet_digest"}):
        raise PacketError("packet digest mismatch")
    if pk["frozen_digest"] != v50.FROZEN_DIGEST or pk["frozen"] != v50.FROZEN:
        raise PacketError("frozen thresholds differ from code")
    if pk["protocol_sha256"] != pythia_plan.file_sha256(_here(PROTOCOL)):
        raise PacketError("protocol changed since freeze")
    for c in CODE:
        n = c.split("/")[-1]
        if pk["code"].get(n) != pythia_plan.file_sha256(_here(c)):
            raise PacketError("code changed since freeze: " + n)
    if strict:
        if pk["status"] != "frozen":
            raise PacketError("packet not frozen")
        miss = _has_none(pk)
        if miss:
            raise PacketError("pending fields: " + ", ".join(miss))
    return True


def finalize(pk, models, corpus_manifest_digest, label_audit, receipt_digest):
    """Fill pending data fields and recompute the digest. Returns a new packet with status 'frozen'
    only if nothing is missing."""
    out = json.loads(json.dumps(pk))
    for n, upd in models.items():
        out["models"][n].update(upd)
    out["corpus"] = {"manifest_digest": corpus_manifest_digest, "label_audit": label_audit}
    out["node"] = {"receipt_digest": receipt_digest}
    out["status"] = "frozen" if not _has_none(out) else "code-frozen-data-pending"
    out["packet_digest"] = v50.digest({k: v for k, v in out.items() if k != "packet_digest"})
    return out
