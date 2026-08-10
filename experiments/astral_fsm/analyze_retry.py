#!/usr/bin/env python3
"""Paired retry-arm analysis with deterministic bootstrap intervals."""
import argparse, json, math, random, statistics
from pathlib import Path

CONDITIONS=("control","localize","corrective","sham","random_fact")

def binom_two_sided_p(discordant_a, discordant_b):
    n=discordant_a+discordant_b
    if not n: return 1.0
    k=min(discordant_a,discordant_b)
    return min(1.0, 2*sum(math.comb(n,i) for i in range(k+1))/(2**n))

def main(run_dir):
    run=Path(run_dir); files=list((run/"retry/evaluated").glob("case_*.json"))
    rows=[json.loads(p.read_text()) for p in files]
    by_case={}
    for row in rows: by_case.setdefault(row["case_id"],{})[row["condition"]]=row["overall_exact"]
    paired={cid:v for cid,v in by_case.items() if all(c in v for c in CONDITIONS)}
    rng=random.Random(20260810); n=len(paired)
    def acc(cond, sample): return sum(by_case[cid][cond] for cid in sample)/len(sample)
    def delta(a,b,sample): return acc(a,sample)-acc(b,sample)
    def bootstrap(a,b,iterations=10000):
        ids=list(paired); vals=[]
        for _ in range(iterations): vals.append(delta(a,b,[ids[rng.randrange(n)] for _ in ids]))
        vals.sort(); return {"estimate":delta(a,b,ids),"ci95":[vals[int(.025*iterations)],vals[int(.975*iterations)-1]],"bootstrap_seed":20260810,"iterations":iterations}
    summary={"n_paired_cases":n,"accuracy":{c:sum(by_case[cid][c] for cid in paired)/n for c in CONDITIONS},"effects":{"localize_minus_control":bootstrap("localize","control"),"corrective_minus_control":bootstrap("corrective","control"),"localize_minus_sham":bootstrap("localize","sham"),"corrective_minus_localize":bootstrap("corrective","localize")},"mcnemar":{}}
    for a,b in (("localize","control"),("corrective","control"),("localize","sham"),("random_fact","control")):
        ab=sum(by_case[cid][a] and not by_case[cid][b] for cid in paired); ba=sum(by_case[cid][b] and not by_case[cid][a] for cid in paired)
        summary["mcnemar"][f"{a}_vs_{b}"]={"a_only":ab,"b_only":ba,"two_sided_p":binom_two_sided_p(ab,ba)}
    out=run/"retry"; (out/"analysis.json").write_text(json.dumps(summary,indent=2)); (out/"analysis.md").write_text("# Retry Analysis\n\n```json\n"+json.dumps(summary,indent=2)+"\n```\n")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("run_dir"); main(p.parse_args().run_dir)
