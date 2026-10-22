"""V50 corpus preparation (network only for the fixed Gutenberg ID list; run in a spaCy venv).
State slices: astral-neuron-level-causal-lane-v50-execution, instrument-validity-gate-v2.
Fetched text stays outside the repository (RAW dir). Only ids, sizes, hashes, counts are published.
Publication years are operator-declared (AI-assisted, not machine-verified); titles are verified
against the Gutenberg header. A title mismatch drops the book; no replacement is chosen afterward.
"""
import hashlib, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import v50_corpus as c

BOOKS = [  # (gutenberg id, expected title substring, declared year)
    (1695, "Thursday", 1908), (974, "Secret Agent", 1907), (5658, "Lord Jim", 1900), (2021, "Nostromo", 1904),
    (2891, "Howards End", 1910), (2641, "Room with a View", 1908), (284, "House of Mirth", 1905),
    (4517, "Ethan Frome", 1911), (24, "O Pioneers", 1913), (242, "Antonia", 1918), (233, "Sister Carrie", 1900),
    (215, "Call of the Wild", 1903), (910, "White Fang", 1906), (1074, "Sea-Wolf", 1904),
    (2852, "Hound of the Baskervilles", 1902), (16, "Peter Pan", 1911), (2226, "Kim", 1901),
    (217, "Sons and Lovers", 1913), (2814, "Dubliners", 1914), (4217, "Portrait of the Artist", 1916),
    (144, "Voyage Out", 1915), (351, "Of Human Bondage", 1915), (2775, "Good Soldier", 1915),
    (62, "Princess of Mars", 1912), (45, "Anne of Green Gables", 1908), (289, "Wind in the Willows", 1908),
    (805, "This Side of Paradise", 1920), (416, "Winesburg", 1919), (543, "Main Street", 1920),
    (1300, "Riders of the Purple Sage", 1912), (558, "Thirty-Nine Steps", 1915), (204, "Innocence of Father Brown", 1911),
    (140, "Jungle", 1906), (541, "Age of Innocence", 1920), (718, "Tono-Bungay", 1909),
    (1056, "Martin Eden", 1909), (4300, "Ulysses", 1922), (219, "Heart of Darkness", 1899),
    (3600, "Montaigne", 1580), (1342, "Pride and Prejudice", 1813),  # last 3 are deliberate rejects (pre-1900/not novel)
]
MIN_YEAR = 1900
PER_DOC_CAP = 400


def fetch(gid):
    url = "https://www.gutenberg.org/cache/epub/%d/pg%d.txt" % (gid, gid)
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def body(text):
    a = re.search(r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", text, re.S)
    b = re.search(r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG EBOOK", text)
    if not a or not b:
        raise ValueError("no gutenberg markers")
    return text[a.end():b.start()]


def main(raw_dir, out_corpus, out_public):
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
    os.makedirs(raw_dir, exist_ok=True)
    docs, dropped = {}, []
    for gid, title, year in BOOKS:
        if year < MIN_YEAR:
            dropped.append({"id": gid, "reason": "declared year %d < %d" % (year, MIN_YEAR)}); continue
        path = os.path.join(raw_dir, "%d.txt" % gid)
        if not os.path.exists(path):
            open(path, "wb").write(fetch(gid))
        raw = open(path, "rb").read()
        text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
        head = text[:3000]
        if title.lower() not in head.lower():
            dropped.append({"id": gid, "reason": "title mismatch"}); continue
        docs[str(gid)] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "title": title, "year": year,
                          "body": body(text)}
    ids = sorted(docs)
    splits = c.split_docs(ids, "v50-docs")
    items = []
    for did in ids:
        paras = [re.sub(r"\s+", " ", p).strip() for p in docs[did]["body"].split("\n\n")]
        paras = [p for p in paras if 60 <= len(p) <= 1500]
        found = []
        for doc in nlp.pipe(paras, batch_size=64):
            for si, sent in enumerate(doc.sents):
                if not 6 <= len(sent) <= 60:
                    continue
                base = sent.start
                toks = [{"i": t.i - base, "text": t.text, "tag": t.tag_, "dep": t.dep_, "head": t.head.i - base} for t in sent]
                found += c.extract_items(did, len(found), toks)
        found.sort(key=lambda i: (not i["attractor"], c.digest(i["id"])))
        items += found[:PER_DOC_CAP]
    by = c.balance(items, splits)
    gates = c.corpus_gates(by)
    hashes = {d: docs[d]["sha256"] for d in ids}
    man = c.manifest(by, hashes, "spacy-%s/en_core_web_sm-%s" % (spacy.__version__, nlp.meta["version"]))
    sample = c.audit_sample([i for v in by.values() for i in v])
    json.dump({"manifest": man, "split_items": by}, open(out_corpus, "w"))
    json.dump({"documents": {d: {k: docs[d][k] for k in ("bytes", "sha256", "title", "year")} for d in ids},
               "dropped": dropped, "splits": splits, "gates": gates, "manifest": man, "audit_sample_ids": sample},
              open(out_public, "w"), indent=1, sort_keys=True)
    print(json.dumps({"docs": len(ids), "dropped": dropped, "counts": man["counts"], "gates": gates}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
