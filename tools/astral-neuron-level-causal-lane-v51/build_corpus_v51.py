"""V51 corpus: same 36 local books and rules as V50, excluding every V50 item id. No network (raw bytes cached).
State slices: astral-neuron-level-causal-lane-v51-execution, instrument-validity-gate-v3."""
import hashlib, json, os, re, sys
V50 = os.path.join(os.path.dirname(__file__), "..", "astral-neuron-level-causal-lane-v50")
sys.path.insert(0, V50)
import v50_corpus as c
import prepare_corpus as p


def main(raw_dir, v50_corpus_path, out_corpus, out_public):
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
    old = json.load(open(v50_corpus_path))
    excluded = {i["id"] for v in old["split_items"].values() for i in v}
    docs, dropped = {}, []
    for gid, title, year in p.BOOKS:
        if year < p.MIN_YEAR:
            dropped.append({"id": gid, "reason": "declared year"}); continue
        raw = open(os.path.join(raw_dir, "%d.txt" % gid), "rb").read()
        text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
        if title.lower() not in text[:3000].lower():
            dropped.append({"id": gid, "reason": "title mismatch"}); continue
        docs[str(gid)] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "title": title, "year": year,
                          "body": p.body(text)}
    ids = sorted(docs)
    splits = c.split_docs(ids, "v50-docs")
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
        found = [i for i in found if i["id"] not in excluded]
        found.sort(key=lambda i: (not i["attractor"], c.digest(i["id"])))
        items += found[:p.PER_DOC_CAP]
    c.MIN_ATTRACTOR_FRAC = 0.0  # V51 waiver: V50 consumed the attractor pool (see protocol); fraction is reported, not gated
    by = c.balance(items, splits)
    used = {i["id"] for v in by.values() for i in v}
    assert not (used & excluded), "overlap with V50 items"
    gates = c.corpus_gates(by)
    man = c.manifest(by, {d: docs[d]["sha256"] for d in ids}, "spacy-%s/en_core_web_sm-%s" % (spacy.__version__, nlp.meta["version"]))
    man["protocol"] = "astral-neuron-level-causal-lane-v51"
    man["excluded_v50_items"] = len(excluded)
    sample = c.audit_sample([i for v in by.values() for i in v])[:100]
    json.dump({"manifest": man, "split_items": by}, open(out_corpus, "w"))
    json.dump({"splits": splits, "gates": gates, "manifest": man, "audit_sample_ids": sample, "dropped": dropped},
              open(out_public, "w"), indent=1, sort_keys=True)
    print(json.dumps({"counts": man["counts"], "gates": gates, "excluded": len(excluded)}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
