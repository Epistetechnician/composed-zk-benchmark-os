#!/usr/bin/env python3
"""Run frozen baseline cases; raw record is written before evaluation."""
import argparse, json, sys, hashlib, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if str(ROOT.parent.parent) not in sys.path: sys.path.insert(0,str(ROOT.parent.parent))
from experiments.astral_fsm.generate_cases import generate_cases
from experiments.astral_fsm.actor_client import call_actor
from experiments.astral_fsm.evaluate import evaluate

def append_jsonl(path,obj):
    with path.open("a",encoding="utf8") as f:
        f.write(json.dumps(obj,separators=(",",":"))+"\n"); f.flush()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="experiments/astral_fsm/runs/2026-08-07")
    ap.add_argument("--model",default="openresearchtools/Qwen3.5-4B-GGUF:Q4_K_M"); ap.add_argument("--temperature",type=float,default=0.0)
    ap.add_argument("--limit",type=int,default=100); ap.add_argument("--seed",type=int,default=None)
    ap.add_argument("--profile",choices=("initial","easy","micro","short","intermediate"),default="initial"); ap.add_argument("--case-offset",type=int,default=0); args=ap.parse_args()
    out=Path(args.output); rawdir=out/"raw"; evdir=out/"evaluated"; rawdir.mkdir(parents=True,exist_ok=True); evdir.mkdir(parents=True,exist_ok=True)
    cases=generate_cases(100, profile=args.profile, case_offset=args.case_offset)[:args.limit]
    manifest=out/"cases_manifest.json"; manifest.write_text(json.dumps(cases,indent=2))
    raw_path=rawdir/"actor_raw.jsonl"; eval_path=evdir/"evaluated.jsonl"
    if raw_path.exists() or eval_path.exists(): raise SystemExit(f"Refusing overwrite of immutable run: {out}")
    results=[]
    for i,case in enumerate(cases,1):
        raw=call_actor(case,args.model,args.temperature,args.seed)
        append_jsonl(raw_path,raw)  # freeze before oracle
        ev=evaluate(case,raw)
        ev.update({"http_status":raw.get("http_status"),"latency_ms":raw.get("latency_ms"),"error":raw.get("error")})
        append_jsonl(eval_path,ev); results.append(ev)
        print(f"{i}/{len(cases)} case={case['case_id']} stage={case['stage']} exact={ev['overall_exact']} json={ev['valid_json']}",flush=True)
    total=len(results); exact=sum(r["overall_exact"] for r in results)
    successful_http=sum(1 for r in results if r.get("http_status") is not None)
    transport_failures=total-successful_http
    evaluated_successes=[r for r in results if r.get("http_status") is not None]
    stages={}
    for stage in (1,2,3):
        rs=[r for r in evaluated_successes if r["stage"]==stage]
        stages[str(stage)]={"n":len(rs),"exact":sum(r["overall_exact"] for r in rs),"accuracy":sum(r["overall_exact"] for r in rs)/len(rs) if rs else None}
    summary={"n":total,"successful_http_calls":successful_http,"transport_failures":transport_failures,"exact":exact,"exact_accuracy":exact/successful_http if successful_http else None,"strict_json_rate":sum(r["valid_json"] for r in evaluated_successes)/successful_http if successful_http else None,"recoverable_json_rate":sum(r["recoverable_json"] for r in evaluated_successes)/successful_http if successful_http else None,"mean_state_accuracy":statistics.mean(r["state_accuracy"] for r in evaluated_successes) if evaluated_successes else None,"stages":stages,"natural_failures":successful_http-exact,"divergence_positions":{str(k):sum(r["first_divergence_index"]==k for r in evaluated_successes) for k in sorted({r["first_divergence_index"] for r in evaluated_successes if r["first_divergence_index"] is not None})}}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
if __name__=="__main__": main()
