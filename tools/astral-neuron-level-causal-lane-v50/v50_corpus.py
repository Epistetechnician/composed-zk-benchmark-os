"""V50 corpus + label audit (pure, offline, no model/network).

State slices: astral-neuron-level-causal-lane-v50-execution, instrument-validity-gate-v2.
Parser-agnostic: input is pre-parsed sentences (token dicts). The spaCy adapter is a thin
optional wrapper; the logic below is what the hermetic tests exercise.
Token dict keys: i, text, tag (PTB), dep, head (index of head token).
"""
import hashlib
import json
import random

# present/past forms of be, do, have; gold = observed verb, bad = number-flipped form.
SING = {"is": "are", "was": "were", "does": "do", "has": "have"}
PLUR = {"are": "is", "were": "was", "do": "does", "have": "has"}
NOUN_SING, NOUN_PLUR = {"NN", "NNP"}, {"NNS", "NNPS"}

AUDIT_N = 200
AUDIT_MAX_ERROR = 0.05
MIN_ATTRACTOR_FRAC = 0.30
MIN_NON_THE_FRAC = 0.30  # implementation parameter; freeze in the packet before any run


class V50CorpusError(ValueError):
    pass


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def split_docs(doc_ids, seed):
    """Deterministic document-disjoint fit/tune/assess split."""
    if len(set(doc_ids)) != len(doc_ids):
        raise V50CorpusError("duplicate document ids")
    out = {"fit": [], "tune": [], "assess": []}
    for d in sorted(doc_ids):
        r = int(hashlib.sha256(("%s:%s" % (seed, d)).encode()).hexdigest(), 16) % 100
        out["fit" if r < 50 else "tune" if r < 75 else "assess"].append(d)
    return out


def _number(tok):
    t = tok["text"].lower()
    if t in SING:
        return "sing"
    if t in PLUR:
        return "plur"
    return None


def _subtree_span(tokens, root):
    keep = {root}
    changed = True
    while changed:
        changed = False
        for t in tokens:
            if t["head"] in keep and t["i"] not in keep and t["i"] != t["head"]:
                keep.add(t["i"])
                changed = True
    return min(keep), max(keep)


def extract_items(doc_id, sent_idx, tokens):
    """Items: prefix text up to (not including) a finite be/do/have verb with an nsubj."""
    byi = {t["i"]: t for t in tokens}
    items = []
    for v in tokens:
        num = _number(v)
        if num is None or v["tag"] not in {"VBZ", "VBP", "VBD"}:
            continue
        # auxiliaries (is/are/was/were/does/do/has/have as aux/auxpass) take the subject of their head verb
        sh = byi[v["head"]] if v["dep"] in {"aux", "auxpass"} and v["head"] != v["i"] else v
        subj = [t for t in tokens if t["head"] == sh["i"] and t["dep"] in {"nsubj", "nsubjpass"} and t["i"] != sh["i"]]
        if len(subj) != 1:
            continue
        s = subj[0]
        lo, hi = _subtree_span(tokens, s["i"])
        if hi >= v["i"] or v["i"] == 0:
            continue
        prefix_toks = [t for t in tokens if t["i"] < v["i"]]
        if len(prefix_toks) < 2:
            continue
        subj_num = "sing" if s["tag"] in NOUN_SING else "plur" if s["tag"] in NOUN_PLUR else None
        if subj_num is None or subj_num != num:
            continue  # pronoun/ambiguous subjects and parser disagreements are dropped, not guessed
        between = [t for t in prefix_toks if lo <= t["i"] <= hi and t["i"] != s["i"]]
        opp = NOUN_PLUR if subj_num == "sing" else NOUN_SING
        attractor = any(t["tag"] in opp for t in between)
        good = v["text"].lower()
        bad = (SING if num == "sing" else PLUR)[good]
        items.append({
            "id": "%s:%d:%d" % (doc_id, sent_idx, v["i"]),
            "doc": doc_id,
            "text": " ".join(t["text"] for t in prefix_toks),
            "good": " " + good,
            "bad": " " + bad,
            "cls": num,
            "attractor": attractor,
            "the_initial": prefix_toks[0]["text"].lower() == "the",
        })
    return items


CAP_PER_CLASS = 400  # per class per split; keeps the attractor minimum reachable (set before any model effect)


def balance(items, splits, cap=CAP_PER_CLASS):
    """Exact class balance per split. Subsampling prefers attractor items (corpus-construction rule fixed
    before any model effect), then id hash, so the protocol's attractor minimum is reachable."""
    out = {}
    doc2split = {d: k for k, ds in splits.items() for d in ds}
    for k in splits:
        pool = [it for it in items if doc2split.get(it["doc"]) == k]
        s = sorted((i for i in pool if i["cls"] == "sing"), key=lambda i: (not i["attractor"], digest(i["id"])))
        p = sorted((i for i in pool if i["cls"] == "plur"), key=lambda i: (not i["attractor"], digest(i["id"])))
        n = min(len(s), len(p), cap)
        if n == 0:
            raise V50CorpusError("split %s has an empty class" % k)
        out[k] = sorted(s[:n] + p[:n], key=lambda i: i["id"])
    return out


def corpus_gates(by_split):
    allitems = [i for v in by_split.values() for i in v]
    if not allitems:
        raise V50CorpusError("empty corpus")
    af = sum(i["attractor"] for i in allitems) / len(allitems)
    nt = sum(not i["the_initial"] for i in allitems) / len(allitems)
    if af < MIN_ATTRACTOR_FRAC:
        raise V50CorpusError("attractor fraction %.3f below %.2f" % (af, MIN_ATTRACTOR_FRAC))
    if nt < MIN_NON_THE_FRAC:
        raise V50CorpusError("non-'The' fraction %.3f below %.2f" % (nt, MIN_NON_THE_FRAC))
    docs = {k: {i["doc"] for i in v} for k, v in by_split.items()}
    ks = list(docs)
    for a in range(len(ks)):
        for b in range(a + 1, len(ks)):
            if docs[ks[a]] & docs[ks[b]]:
                raise V50CorpusError("document leakage between %s and %s" % (ks[a], ks[b]))
    return {"attractor_frac": af, "non_the_frac": nt, "n": len(allitems)}


def audit_sample(items, n=AUDIT_N, seed="v50-audit"):
    if len(items) < n:
        raise V50CorpusError("fewer items (%d) than audit size %d" % (len(items), n))
    rng = random.Random(seed)
    return sorted(rng.sample(sorted(i["id"] for i in items), n))


def audit_gate(sample_ids, judgements):
    """judgements: id -> True if the gold label is correct. Every sampled id must be judged."""
    missing = [i for i in sample_ids if i not in judgements]
    if missing:
        raise V50CorpusError("%d sampled labels unjudged" % len(missing))
    if any(not isinstance(judgements[i], bool) for i in sample_ids):
        raise V50CorpusError("judgements must be booleans")
    err = sum(not judgements[i] for i in sample_ids) / len(sample_ids)
    if err > AUDIT_MAX_ERROR:
        raise V50CorpusError("label error %.3f exceeds %.2f; corpus rejected" % (err, AUDIT_MAX_ERROR))
    return {"error": err, "n": len(sample_ids)}


def manifest(by_split, doc_hashes, parser_id):
    """Digest-bound corpus manifest. doc_hashes: doc id -> sha256 of source bytes."""
    used = {i["doc"] for v in by_split.values() for i in v}
    if not used <= set(doc_hashes):
        raise V50CorpusError("items reference documents without recorded hashes")
    return {
        "protocol": "astral-neuron-level-causal-lane-v50",
        "parser": parser_id,
        "doc_hashes": {d: doc_hashes[d] for d in sorted(used)},
        "counts": {k: len(v) for k, v in by_split.items()},
        "items_sha256": digest(by_split),
    }


def spacy_tokens(nlp, text):
    """Optional adapter (not exercised by hermetic tests): spaCy Doc -> sentences of token dicts."""
    out = []
    for sent in nlp(text).sents:
        base = sent.start
        out.append([{"i": t.i - base, "text": t.text, "tag": t.tag_, "dep": t.dep_, "head": t.head.i - base} for t in sent])
    return out
