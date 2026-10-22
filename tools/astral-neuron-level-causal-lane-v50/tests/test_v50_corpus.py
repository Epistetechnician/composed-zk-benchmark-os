import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import v50_corpus as c


def sent(words):
    """words: list of (text, tag, dep, head). Builds token dicts."""
    return [{"i": i, "text": w, "tag": t, "dep": d, "head": h} for i, (w, t, d, h) in enumerate(words)]


# "Her brother is tall"  (no 'The', no attractor)
S_PLAIN = sent([("Her", "PRP$", "poss", 1), ("brother", "NN", "nsubj", 2), ("is", "VBZ", "ROOT", 2), ("tall", "JJ", "acomp", 2)])
# "The keys to the cabinet are lost" (attractor: cabinet NN inside plural subject)
S_ATTR = sent([("The", "DT", "det", 1), ("keys", "NNS", "nsubj", 5), ("to", "IN", "prep", 1), ("the", "DT", "det", 4),
               ("cabinet", "NN", "pobj", 2), ("are", "VBP", "ROOT", 5), ("lost", "VBN", "acomp", 5)])
# pronoun subject: dropped
S_PRON = sent([("He", "PRP", "nsubj", 1), ("is", "VBZ", "ROOT", 1), ("here", "RB", "advmod", 1)])
# parser/verb number disagreement: dropped
S_DIS = sent([("The", "DT", "det", 1), ("dogs", "NNS", "nsubj", 2), ("is", "VBZ", "ROOT", 2), ("loud", "JJ", "acomp", 2)])


class T(unittest.TestCase):
    def test_extract_plain(self):
        it = c.extract_items("d1", 0, S_PLAIN)
        self.assertEqual(len(it), 1)
        self.assertEqual((it[0]["good"], it[0]["bad"], it[0]["cls"]), (" is", " are", "sing"))
        self.assertFalse(it[0]["attractor"]); self.assertFalse(it[0]["the_initial"])
        self.assertEqual(it[0]["text"], "Her brother")

    def test_extract_attractor(self):
        it = c.extract_items("d1", 1, S_ATTR)
        self.assertEqual(len(it), 1)
        self.assertEqual((it[0]["good"], it[0]["bad"], it[0]["cls"]), (" are", " is", "plur"))
        self.assertTrue(it[0]["attractor"]); self.assertTrue(it[0]["the_initial"])

    def test_dropped_not_guessed(self):
        self.assertEqual(c.extract_items("d", 0, S_PRON), [])
        self.assertEqual(c.extract_items("d", 0, S_DIS), [])

    def test_split_disjoint_and_deterministic(self):
        docs = ["doc%d" % i for i in range(60)]
        a, b = c.split_docs(docs, "s"), c.split_docs(docs, "s")
        self.assertEqual(a, b)
        allv = a["fit"] + a["tune"] + a["assess"]
        self.assertEqual(sorted(allv), sorted(docs))
        self.assertTrue(all(a[k] for k in a))
        with self.assertRaises(c.V50CorpusError):
            c.split_docs(["x", "x"], "s")

    def _pool(self, n_docs=60, per=6):
        docs = ["doc%d" % i for i in range(n_docs)]
        splits = c.split_docs(docs, "s")
        items = []
        for d in docs:
            for j in range(per):
                s = sent([("Her", "PRP$", "poss", 1), ("brother", "NN", "nsubj", 2), ("is", "VBZ", "ROOT", 2)]) if j % 3 else S_ATTR
                items += c.extract_items(d, j, s)
        return docs, splits, items

    def test_balance_exact_and_gates(self):
        docs, splits, items = self._pool()
        by = c.balance(items, splits)
        for k, v in by.items():
            self.assertEqual(sum(i["cls"] == "sing" for i in v), sum(i["cls"] == "plur" for i in v))
        g = c.corpus_gates(by)
        self.assertGreaterEqual(g["attractor_frac"], 0.3)

    def test_gate_failures(self):
        docs = ["doc%d" % i for i in range(60)]
        splits = c.split_docs(docs, "s")
        items = []
        for d in docs:
            items += c.extract_items(d, 0, S_PLAIN) + c.extract_items(d, 1, sent([("Her", "PRP$", "poss", 1), ("brothers", "NNS", "nsubj", 2), ("are", "VBP", "ROOT", 2)]))
        with self.assertRaises(c.V50CorpusError):
            c.corpus_gates(c.balance(items, splits))  # no attractors
        by = c.balance(items, splits)
        by["tune"] = by["tune"] + [dict(by["fit"][0], id="leak")]
        with self.assertRaises(c.V50CorpusError):
            c.corpus_gates(by)

    def test_balance_empty_class(self):
        docs = ["doc%d" % i for i in range(30)]
        splits = c.split_docs(docs, "s")
        items = [i for d in docs for i in c.extract_items(d, 0, S_PLAIN)]
        with self.assertRaises(c.V50CorpusError):
            c.balance(items, splits)

    def test_audit(self):
        _, splits, items = self._pool(n_docs=120, per=6)
        ids = c.audit_sample(items)
        self.assertEqual(len(ids), 200); self.assertEqual(ids, c.audit_sample(items))
        ok = {i: True for i in ids}
        self.assertEqual(c.audit_gate(ids, ok)["error"], 0.0)
        ten = dict(ok); [ten.__setitem__(i, False) for i in ids[:10]]
        self.assertAlmostEqual(c.audit_gate(ids, ten)["error"], 0.05)  # boundary passes
        eleven = dict(ok); [eleven.__setitem__(i, False) for i in ids[:11]]
        with self.assertRaises(c.V50CorpusError):
            c.audit_gate(ids, eleven)
        with self.assertRaises(c.V50CorpusError):
            c.audit_gate(ids, {i: True for i in ids[:-1]})
        with self.assertRaises(c.V50CorpusError):
            c.audit_gate(ids, {i: 1 for i in ids})
        with self.assertRaises(c.V50CorpusError):
            c.audit_sample(items[:10])

    def test_manifest(self):
        docs, splits, items = self._pool()
        by = c.balance(items, splits)
        hashes = {d: "0" * 64 for d in docs}
        m = c.manifest(by, hashes, "spacy-x")
        self.assertEqual(m, c.manifest(by, hashes, "spacy-x"))
        by2 = {k: list(v) for k, v in by.items()}; by2["fit"][0] = dict(by2["fit"][0], good=by2["fit"][0]["bad"])
        self.assertNotEqual(m["items_sha256"], c.manifest(by2, hashes, "spacy-x")["items_sha256"])
        with self.assertRaises(c.V50CorpusError):
            c.manifest(by, {}, "spacy-x")


if __name__ == "__main__":
    unittest.main()
