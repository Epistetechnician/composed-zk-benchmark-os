#!/usr/bin/env python3
"""Retry arms for frozen naturally failed baseline cases."""
import argparse, hashlib, json, random, statistics, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if str(ROOT.parent.parent) not in sys.path: sys.path.insert(0,str(ROOT.parent.parent))
from experiments.astral_fsm.generate_cases import case_to_prompt
from experiments.astral_fsm.actor_client import call_actor, assistant_text
from experiments.astral_fsm.evaluate import evaluate

def feedback(condition, ev, case):
    idx=ev.get("first_divergence_index")
    if idx is None: idx=max(1,len(case["input"])//2)
    before=ev.get("state_before_first_divergence") or case["start"]
    expected=ev.get("expected_state_at_divergence")
    reported=ev.get("reported_state_at_divergence") or "another state"
    if condition=="control": return "Your previous answer was incorrect. Recompute the FSM carefully and return the complete required JSON."
    if condition=="localize": return f"Your previous trajectory first diverged at trajectory position {idx}. The input symbol at that transition was {ev.get('symbol_at_first_divergence')}. Immediately before it, the current state was {before}. You reported {reported} as the next state. Recompute that transition and the complete FSM, but do not assume any state beyond what you recompute. Return the complete required JSON."
    if condition=="corrective": return f"Your previous trajectory first diverged at trajectory position {idx}. Immediately before that transition the current state was {before}. You reported {reported} as the next state, but the correct next state for that transition is {expected}. Recompute from that point and return the complete required JSON."
    if condition=="random_fact":
        blocked={(before, ev.get("symbol_at_first_divergence"))}
        for state in case["states"]:
            for symbol in case["alphabet"]:
                if (state, symbol) not in blocked:
                    next_state=case["transitions"][state][symbol]
                    return f"One true transition fact: from state {state}, on input symbol {symbol}, the next state is {next_state}. This fact is not a diagnosis of your previous trajectory. Recompute the FSM and return the complete required JSON."
    # Deliberately false, different position; position is guaranteed not to be the actual one.
    false_idx=0 if idx!=0 else 1
    false_state=case["states"][-1] if before != case["states"][-1] else case["states"][0]
    return f"Your previous trajectory first diverged at trajectory position {false_idx}. Immediately before that transition, the current state was {false_state}. Recompute from that point and return the complete required JSON."

def retry_prompt(case, baseline_text, message):
    return case_to_prompt(case)+"\n\nPrevious answer:\n"+baseline_text+"\n\nFeedback:\n"+message

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--run",default="experiments/astral_fsm/runs/2026-08-07"); ap.add_argument("--model",default="openresearchtools/Qwen3.5-4B-GGUF:Q4_K_M"); ap.add_argument("--limit",type=int,default=0); args=ap.parse_args()
    run=Path(args.run); evals=[json.loads(x) for x in (run/"evaluated/evaluated.jsonl").read_text().splitlines() if x]; raws=[json.loads(x) for x in (run/"raw/actor_raw.jsonl").read_text().splitlines() if x]
    failed=[e for e in evals if not e.get("overall_exact")]; failed=failed[:args.limit] if args.limit else failed
    cases={c["case_id"]:c for c in json.loads((run/"cases_manifest.json").read_text())}; raw_by={r["case_id"]:r for r in raws}
    out=run/"retry"; rawdir=out/"raw"; evdir=out/"evaluated"; rawdir.mkdir(parents=True); evdir.mkdir(parents=True)
    records=[]
    for j,ev in enumerate(failed,1):
        case=cases[ev["case_id"]]; previous=assistant_text(raw_by[case["case_id"]])
        for condition in ("control","localize","corrective","sham","random_fact"):
            fb=feedback(condition,ev,case); prompt=retry_prompt(case,previous,fb)
            retry_case=dict(case); retry_case["_prompt_override"]=prompt
            # call_actor builds the canonical task prompt; use a local payload-equivalent direct call below
            from urllib.request import Request,urlopen
            payload={"model":args.model,"temperature":0.0,"max_tokens":1024,"chat_template_kwargs":{"enable_thinking":False},"messages":[{"role":"system","content":"You execute deterministic finite-state machines. Return only valid JSON matching the requested schema."},{"role":"user","content":prompt}]}
            body=json.dumps(payload,separators=(",",":")).encode(); started=time.perf_counter(); rec={"case_id":case["case_id"],"condition":condition,"feedback":fb,"request":payload,"prompt_sha256":hashlib.sha256(body).hexdigest(),"timestamp":time.time()}
            try:
                with urlopen(Request("http://127.0.0.1:8080/v1/chat/completions",data=body,headers={"Content-Type":"application/json"}),timeout=180) as resp: raw=resp.read().decode(); rec.update({"http_status":resp.status,"raw_http_response":raw,"response":json.loads(raw)})
            except Exception as exc: rec.update({"http_status":None,"raw_http_response":"","response":None,"error":repr(exc)})
            rec["latency_ms"]=round((time.perf_counter()-started)*1000,2); (rawdir/f"case_{case['case_id']}_{condition}.json").write_text(json.dumps(rec,indent=2))
            ev2=evaluate(case,rec); ev2.update({"condition":condition,"baseline_case_id":case["case_id"]}); (evdir/f"case_{case['case_id']}_{condition}.json").write_text(json.dumps(ev2,indent=2)); records.append(ev2)
        print(f"{j}/{len(failed)} failed cases retried",flush=True)
    summary={}
    for cond in ("control","localize","corrective","sham","random_fact"):
        r=[x for x in records if x["condition"]==cond]; summary[cond]={"n":len(r),"exact":sum(x["overall_exact"] for x in r),"accuracy":sum(x["overall_exact"] for x in r)/len(r) if r else None}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
if __name__=="__main__": main()
