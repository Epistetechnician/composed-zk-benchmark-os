#!/usr/bin/env python3
"""Aggregate baseline metrics into human-readable report."""
import json, statistics
from pathlib import Path

def main(run_dir="experiments/astral_fsm/runs/2026-08-07"):
    p=Path(run_dir)/"evaluated/evaluated.jsonl"; rows=[json.loads(x) for x in p.read_text().splitlines() if x]
    n=len(rows); exact=sum(x["overall_exact"] for x in rows)
    by_stage={}
    for s in (1,2,3):
        r=[x for x in rows if x["stage"]==s]; by_stage[s]={"n":len(r),"exact_accuracy":sum(x["overall_exact"] for x in r)/len(r) if r else None,"mean_state_accuracy":statistics.mean(x["state_accuracy"] for x in r) if r else None}
    summary={"n":n,"exact_accuracy":exact/n if n else None,"strict_json_rate":sum(x["valid_json"] for x in rows)/n if n else None,"recoverable_json_rate":sum(x["recoverable_json"] for x in rows)/n if n else None,"mean_state_accuracy":statistics.mean(x["state_accuracy"] for x in rows) if rows else None,"median_state_accuracy":statistics.median(x["state_accuracy"] for x in rows) if rows else None,"final_state_accuracy":sum(x["final_state_exact"] for x in rows)/n if n else None,"acceptance_accuracy":sum(x["accepted_exact"] for x in rows)/n if n else None,"natural_failures":n-exact,"by_stage":by_stage,"first_divergence_positions":{str(k):sum(x["first_divergence_index"]==k for x in rows) for k in sorted({x["first_divergence_index"] for x in rows if x["first_divergence_index"] is not None})}}
    out=Path(run_dir).parent.parent/"reports"; out.mkdir(parents=True,exist_ok=True); (out/"baseline_summary.json").write_text(json.dumps(summary,indent=2)); (out/"baseline_summary.md").write_text("# Baseline Summary\n\n```json\n"+json.dumps(summary,indent=2)+"\n```\n")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("run_dir",nargs="?",default="experiments/astral_fsm/runs/2026-08-07")
    main(parser.parse_args().run_dir)
