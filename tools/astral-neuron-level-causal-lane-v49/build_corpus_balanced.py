"""Node-side: class-balanced natural-text items (equal is/are gold per document group; same verb pair)."""
import hashlib, json, re, sys
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

p = hf_hub_download("Salesforce/wikitext", "wikitext-103-raw-v1/train-00000-of-00002.parquet", repo_type="dataset")
txt = pq.read_table(p).column("text").to_pylist()
pat = re.compile(r"(?:^|(?<=\. ))(The [A-Za-z\-]+(?: [A-Za-z\-]+){0,7}) (is|are)\b")
flip = {"is": "are", "are": "is"}
CAP = 250
seen, cnt, items = set(), {}, []
for ln, line in enumerate(txt):
    if len(line) < 80 or line.strip().startswith("="):
        continue
    for m in pat.finditer(line):
        prefix, v = m.group(1), m.group(2)
        if prefix in seen or len(prefix.split()) < 3:
            continue
        grp = int(hashlib.sha256(str(ln // 150).encode()).hexdigest(), 16) % 3
        if cnt.get((grp, v), 0) >= CAP:
            continue
        seen.add(prefix)
        cnt[(grp, v)] = cnt.get((grp, v), 0) + 1
        items.append({"id": "b%d_%d" % (ln, m.start()), "text": prefix, "good": " " + v, "bad": " " + flip[v], "grp": grp})
json.dump(items, open(sys.argv[1], "w"))
print(len(items), {str(k): v for k, v in sorted(cnt.items())})
