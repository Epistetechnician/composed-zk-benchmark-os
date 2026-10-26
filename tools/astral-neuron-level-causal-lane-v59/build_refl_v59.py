"""V59 reflexive-agreement items from the already-local V54 books (assess documents only). Run in the spaCy venv.
Slices: astral-neuron-level-causal-lane-v59-execution, instrument-validity-gate-v3. No network."""
import hashlib, json, os, re, sys
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "astral-neuron-level-causal-lane-v50"))
import v50_corpus as c

REFL_SING, REFL_PLUR = {"himself", "herself", "itself"}, {"themselves"}
PRON_SING, PRON_PLUR = {"he", "she", "it"}, {"they"}
PER_DOC_CAP, MIN_PREFIX = 400, 4


def extract_refl(doc_id, sent_idx, tokens):
    """tokens: dicts with i,text,tag,dep,head. Returns items whose reflexive agrees in number with a clear subject."""
    byi = {t["i"]: t for t in tokens}
    items = []
    for r in tokens:
        w = r["text"].lower()
        if w not in REFL_SING | REFL_PLUR or r["i"] < MIN_PREFIX:
            continue
        v, hops = byi[r["head"]] if r["head"] != r["i"] else None, 0
        while v is not None and not v["tag"].startswith("VB") and hops < 4:
            nxt = byi.get(v["head"])
            v = nxt if nxt is not None and nxt["i"] != v["i"] else None
            hops += 1
        if v is None or not v["tag"].startswith("VB"):
            continue
        subj = [t for t in tokens if t["head"] == v["i"] and t["dep"] in {"nsubj", "nsubjpass"} and t["i"] != v["i"]]
        if len(subj) != 1 or subj[0]["i"] >= r["i"]:
            continue
        s = subj[0]
        st = s["text"].lower()
        if s["tag"] in {"NN", "NNP"} or st in PRON_SING:
            num = "sing"
        elif s["tag"] in {"NNS", "NNPS"} or st in PRON_PLUR:
            num = "plur"
        else:
            continue
        if (num == "sing") != (w in REFL_SING):
            continue
        prefix = [t for t in tokens if t["i"] < r["i"]]
        items.append({"id": "R:%s:%d:%d" % (doc_id, sent_idx, r["i"]), "doc": doc_id,
                      "text": " ".join(t["text"] for t in prefix), "good": " " + w,
                      "bad": " themselves" if num == "sing" else " itself", "cls": num})
    return items


def main(raw_dir, public54, out_items, out_public):
    import spacy
    from importlib import import_module
    sys.path.insert(0, os.path.join(HERE, "..", "astral-neuron-level-causal-lane-v54"))
    b = import_module("books_v54"); p = import_module("prepare_corpus")
    nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
    pub = json.load(open(public54))
    assess = set(pub["documents"])  # addendum 1 (doc 141): all 35 books; units were selected on a different task
    items = []
    for did in sorted(assess):
        raw = open(os.path.join(raw_dir, "%s.txt" % did), "rb").read()
        if hashlib.sha256(raw).hexdigest() != pub["documents"][did]["sha256"]:
            raise SystemExit("raw hash mismatch for %s" % did)
        body = p.body(raw.decode("utf-8", "replace").replace("\r\n", "\n"))
        paras = [re.sub(r"\s+", " ", q).strip() for q in body.split("\n\n")]
        found = []
        for doc in nlp.pipe([q for q in paras if 60 <= len(q) <= 1500], batch_size=64):
            for sent in doc.sents:
                if not 6 <= len(sent) <= 60:
                    continue
                base = sent.start
                toks = [{"i": t.i - base, "text": t.text, "tag": t.tag_, "dep": t.dep_, "head": t.head.i - base} for t in sent]
                found += extract_refl(did, len(found), toks)
        found.sort(key=lambda i: c.digest(i["id"]))
        items += found[:PER_DOC_CAP]
    s = sorted((i for i in items if i["cls"] == "sing"), key=lambda i: c.digest(i["id"]))
    pl = sorted((i for i in items if i["cls"] == "plur"), key=lambda i: c.digest(i["id"]))
    n = min(len(s), len(pl))
    bal = sorted(s[:n] + pl[:n], key=lambda i: i["id"])
    sample = c.audit_sample(bal, n=min(60, len(bal)), seed="v59-audit") if len(bal) >= 60 else []
    json.dump(bal, open(out_items, "w"))
    json.dump({"n_items": len(bal), "per_class": n, "raw_counts": {"sing": len(s), "plur": len(pl)},
               "items_sha256": hashlib.sha256(json.dumps(bal, sort_keys=True).encode()).hexdigest(),
               "audit_sample_ids": sample, "parser": "spacy-%s/en_core_web_sm-%s" % (spacy.__version__, nlp.meta["version"])},
              open(out_public, "w"), indent=1, sort_keys=True)
    print(json.dumps({"raw": {"sing": len(s), "plur": len(pl)}, "per_class": n, "n_items": len(bal)}))


if __name__ == "__main__":
    main(*sys.argv[1:5])
