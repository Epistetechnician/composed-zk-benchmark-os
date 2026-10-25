"""V54 corpus: fresh Gutenberg books disjoint from V50, same extraction rules. Network only for the frozen
book list (<=60 docs, <=300 MB, gutenberg.org); run in a spaCy venv. Raw text stays outside the repo.
Slices: astral-neuron-level-causal-lane-v54-execution, instrument-validity-gate-v3."""
import hashlib, json, os, re, sys, urllib.request
HERE = os.path.dirname(__file__)
V50 = os.path.join(HERE, "..", "astral-neuron-level-causal-lane-v50")
sys.path.insert(0, V50); sys.path.insert(0, HERE)
import v50_corpus as c
import prepare_corpus as p
import books_v54 as b


def fetch(gid):
    url = "https://www.gutenberg.org/cache/epub/%d/pg%d.txt" % (gid, gid)
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read(8_000_000)


def main(raw_dir, out_corpus, out_public, v50_public):
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
    v50_ids = set(json.load(open(v50_public))["documents"])
    os.makedirs(raw_dir, exist_ok=True)
    docs, dropped = {}, []
    for gid, title, year in b.BOOKS:
        if str(gid) in v50_ids:
            dropped.append({"id": gid, "reason": "in V50"}); continue
        if year < b.MIN_YEAR:
            dropped.append({"id": gid, "reason": "declared year %d" % year}); continue
        path = os.path.join(raw_dir, "%d.txt" % gid)
        if not os.path.exists(path):
            try:
                open(path, "wb").write(fetch(gid))
            except Exception as e:
                dropped.append({"id": gid, "reason": "fetch failed: %s" % type(e).__name__}); continue
        raw = open(path, "rb").read()
        text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
        if title.lower() not in text[:3000].lower():
            dropped.append({"id": gid, "reason": "title mismatch"}); continue
        try:
            bd = p.body(text)
        except ValueError:
            dropped.append({"id": gid, "reason": "no markers"}); continue
        docs[str(gid)] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "title": title, "year": year, "body": bd}
    ids = sorted(docs)
    splits = c.split_docs(ids, "v54-docs")
    items = []
    for did in ids:
        paras = [re.sub(r"\s+", " ", q).strip() for q in docs[did]["body"].split("\n\n")]
        paras = [q for q in paras if 60 <= len(q) <= 1500]
        found = []
        for doc in nlp.pipe(paras, batch_size=64):
            for sent in doc.sents:
                if not 6 <= len(sent) <= 60:
                    continue
                base = sent.start
                toks = [{"i": t.i - base, "text": t.text, "tag": t.tag_, "dep": t.dep_, "head": t.head.i - base} for t in sent]
                found += c.extract_items(did, len(found), toks)
        found.sort(key=lambda i: (not i["attractor"], c.digest(i["id"])))
        items += found[:b.PER_DOC_CAP]
    c.MIN_ATTRACTOR_FRAC = 0.0  # same waiver as V51-V53: fraction reported, not gated
    by = c.balance(items, splits)
    gates = c.corpus_gates(by)
    man = c.manifest(by, {d: docs[d]["sha256"] for d in ids}, "spacy-%s/en_core_web_sm-%s" % (spacy.__version__, nlp.meta["version"]))
    man["protocol"] = "astral-neuron-level-causal-lane-v54"
    sample = c.audit_sample([i for v in by.values() for i in v], seed="v54-audit")
    json.dump({"manifest": man, "split_items": by}, open(out_corpus, "w"))
    json.dump({"documents": {d: {k: docs[d][k] for k in ("bytes", "sha256", "title", "year")} for d in ids},
               "dropped": dropped, "splits": splits, "gates": gates, "manifest": man, "audit_sample_ids": sample},
              open(out_public, "w"), indent=1, sort_keys=True)
    print(json.dumps({"docs": len(ids), "dropped": dropped, "counts": man["counts"], "gates": gates}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
