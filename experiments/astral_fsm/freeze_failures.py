#!/usr/bin/env python3
"""Freeze naturally failed baseline cases for paired retry experiments."""
import argparse, json
from pathlib import Path

def main(run_dir):
    run=Path(run_dir)
    cases={c["case_id"]:c for c in json.loads((run/"cases_manifest.json").read_text())}
    evaluations=[json.loads(line) for line in (run/"evaluated/evaluated.jsonl").read_text().splitlines() if line]
    raw=[json.loads(line) for line in (run/"raw/actor_raw.jsonl").read_text().splitlines() if line]
    raw_by={r["case_id"]:r for r in raw}
    frozen=[]
    for evaluation in evaluations:
        if evaluation["overall_exact"]:
            continue
        case_id=evaluation["case_id"]
        frozen.append({"case":cases[case_id],"baseline_raw":raw_by[case_id],"baseline_evaluation":evaluation})
    output=run/"frozen_failures.json"
    if output.exists(): raise SystemExit(f"Refusing overwrite: {output}")
    output.write_text(json.dumps({"count":len(frozen),"source_run":str(run),"failures":frozen},indent=2))
    print(json.dumps({"source_run":str(run),"frozen_failures":len(frozen),"output":str(output)},indent=2))

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("run_dir")
    main(parser.parse_args().run_dir)
