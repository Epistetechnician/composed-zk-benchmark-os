"""Node-side: natural-text subject-verb items from wikitext (sentences starting 'The ...' before is/are/was/were)."""
import hashlib, json, re, sys
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

p = hf_hub_download("Salesforce/wikitext", "wikitext-103-raw-v1/train-00000-of-00002.parquet", repo_type="dataset")
txt = pq.read_table(p).column("text").to_pylist()[:400000]
pat = re.compile(r"(?:^|(?<=\. ))(The [A-Za-z\-]+(?: [A-Za-z\-]+){0,7}) (is|are|was|were)\b")
flip = {"is": "are", "are": "is", "was": "were", "were": "was"}
seen, items = set(), []
for ln, line in enumerate(txt):
    if len(line) < 80 or line.strip().startswith("="):
        continue
    for m in pat.finditer(line):
        prefix, v = m.group(1), m.group(2)
        if prefix in seen or len(prefix.split()) < 3:
            continue
        seen.add(prefix)
        doc = ln // 150  # documents = 150-line chunks (article blocks)
        grp = int(hashlib.sha256(str(doc).encode()).hexdigest(), 16) % 3
        items.append({"id": "w%d_%d" % (ln, m.start()), "text": prefix, "good": " " + v, "bad": " " + flip[v], "grp": grp, "doc": doc})
cnt = {0: 0, 1: 0, 2: 0}
kept = []
for it in items:
    if cnt[it['grp']] < 400:
        cnt[it['grp']] += 1
        kept.append(it)
items = kept
json.dump(items, open(sys.argv[1], "w"))
print(len(items), {g: sum(i["grp"] == g for i in items) for g in range(3)}, sum(i["good"] in (" is", " are") for i in items))
