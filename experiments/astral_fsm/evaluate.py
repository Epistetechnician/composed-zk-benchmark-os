#!/usr/bin/env python3
"""Evaluate frozen actor records against oracle output."""
import json, re
from .actor_client import assistant_text
from .oracle import run

def parse_actor(text):
    strict = False; obj = None
    try: obj = json.loads(text); strict = True
    except Exception: pass
    recoverable = obj is not None
    if obj is None:
        for block in re.findall(r"```(?:json)?\s*(.*?)```", text, re.S|re.I):
            try: obj=json.loads(block.strip()); recoverable=True; break
            except Exception: pass
    if obj is None:
        match=re.search(r"\{.*\}", text, re.S)
        if match:
            try: obj=json.loads(match.group()); recoverable=True
            except Exception: pass
    return strict, recoverable, obj

def evaluate(case, raw):
    expected=run(case); text=assistant_text(raw); strict,recoverable,reported=parse_actor(text)
    result={"case_id":case["case_id"],"stage":case["stage"],"input_length":len(case["input"]),"num_states":len(case["states"]),
            "valid_json":strict,"recoverable_json":recoverable,"schema_valid":False,"expected_trajectory_length":len(expected["trajectory"]),
            "reported_trajectory_length":None,"trajectory_exact":False,"final_state_exact":False,"accepted_exact":False,
            "state_accuracy":0.0,"prefix_accuracy":0.0,"first_divergence_index":None,"symbol_at_first_divergence":None,
            "state_before_first_divergence":None,"expected_state_at_divergence":None,"reported_state_at_divergence":None,
            "overall_exact":False,"oracle_answer":expected,"parsed_response":reported}
    if not isinstance(reported,dict) or not all(k in reported for k in ("trajectory","final_state","accepted")) or not isinstance(reported.get("trajectory"),list): return result
    result["schema_valid"]=isinstance(reported["final_state"],str) and isinstance(reported["accepted"],bool)
    if not result["schema_valid"]: return result
    actual=reported["trajectory"]; result["reported_trajectory_length"]=len(actual)
    n=min(len(actual),len(expected["trajectory"]))
    matches=[i for i in range(n) if actual[i]==expected["trajectory"][i]]
    result["state_accuracy"]=len(matches)/len(expected["trajectory"])
    result["prefix_accuracy"]=(next((i for i in range(n) if actual[i]!=expected["trajectory"][i]),n))/len(expected["trajectory"])
    for i in range(n):
        if actual[i]!=expected["trajectory"][i]:
            result.update({"first_divergence_index":i,"symbol_at_first_divergence":case["input"][i-1] if i>0 else None,
              "state_before_first_divergence":expected["trajectory"][i-1] if i>0 else expected["trajectory"][0],
              "expected_state_at_divergence":expected["trajectory"][i],"reported_state_at_divergence":actual[i]}); break
    if result["first_divergence_index"] is None and len(actual)!=len(expected["trajectory"]): result["first_divergence_index"]=n
    result.update({"trajectory_exact":actual==expected["trajectory"],"final_state_exact":reported["final_state"]==expected["final_state"],"accepted_exact":reported["accepted"]==expected["accepted"]})
    result["overall_exact"]=result["trajectory_exact"] and result["final_state_exact"] and result["accepted_exact"]
    return result
