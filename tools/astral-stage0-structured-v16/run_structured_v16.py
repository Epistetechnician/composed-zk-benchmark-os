"""V16 runner with sealed structured predictions."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import torch
from structured_v16 import *
def canonical(v): return (json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
def dump(path,rows): raw=b"".join(canonical(r) for r in rows);path.write_bytes(raw);return hashlib.sha256(raw).hexdigest()
def prepare(root,repo):
    if root.is_symlink(): raise ValueError("symlink output")
    root,repo=root.resolve(),repo.resolve()
    if root==repo or repo in root.parents or root in repo.parents: raise ValueError("repository-external output required")
    if root.exists() and (not root.is_dir() or any(root.iterdir())): raise ValueError("empty output required")
    root.mkdir(parents=True,exist_ok=True);return root
def summarize(rows):
    out={}
    for method in METHODS:
        mr=[r for r in rows if r["method"]==method]; out[method]={}
        for op in OPERATORS:
            cells=[(r["actual"][i],r["predicted"][i]) for r in mr for i,t in enumerate(TARGET_ORDER) if t[1]==op]
            out[method][op]=metric_summary([a for a,_ in cells],[p for _,p in cells])
            for seed in ACTOR_SEEDS:
                c=[(r["actual"][i],r["predicted"][i]) for r in mr if r["seed"]==seed for i,t in enumerate(TARGET_ORDER) if t[1]==op]
                out[method][f"seed={seed};operator={op}"]=metric_summary([a for a,_ in c],[p for _,p in c])
    return out
def classify(m):
    own=m["own_telemetry"]
    for op in OPERATORS:
        if own[op]["correlation"] is None or own[op]["correlation"]<=0 or own[op]["calibration_slope"] is None or not .5<=own[op]["calibration_slope"]<=1.5:return "StructuredDevelopmentNoCandidate"
        for method in METHODS[1:]:
            if own[op]["mse"]>=m[method][op]["mse"]:return "StructuredDevelopmentNoCandidate"
    for seed in ACTOR_SEEDS:
        for op in OPERATORS:
            k=f"seed={seed};operator={op}"
            if own[k]["mse"]>.95*m["own_activation"][k]["mse"] or own[k]["mse"]>.9*m["other_actor_telemetry"][k]["mse"]:return "StructuredDevelopmentNoCandidate"
    return "StructuredDevelopmentCandidate"
def run(root,repo,protocol):
    root=prepare(root,repo);(root/"protocol.lock.json").write_bytes(canonical({"protocol_sha256":hashlib.sha256(protocol.read_bytes()).hexdigest(),"state_slice":STATE_SLICE}))
    actors={};quals=[]
    for seed in ACTOR_SEEDS:
        a,q=reproduce(seed);quals.append(q);(root/f"qualification-{seed}.json").write_bytes(canonical(q))
        if not q["eligible"]: return finalize(root,{"accepted_evidence":False,"classification":"DevelopmentQualificationFailed","confirmation_authorized":False,"stage0_pass":False,"state_slice":STATE_SLICE})
        actors[seed]=a
    tel=[];eff=[]
    for seed,a in actors.items():
        for ex in examples_for(FIT_FAMILIES):
            tel += [{**r,"seed":seed} for r in telemetry_rows(a,ex)]; eff += [{**r,"seed":seed} for r in effect_rows(a,ex)]
    fit=group_rows(tel,eff); fit_hash=dump(root/"fitting-groups.jsonl",fit); mean,v,s=basis([g["target"] for g in fit])
    states={}; byseed={seed:[g for g in fit if g["seed"]==seed] for seed in ACTOR_SEEDS}
    for seed in ACTOR_SEEDS:
        own=byseed[seed]; states[f"{seed}:own_telemetry"]=fit_projection([feature(g,"telemetry") for g in own],[g["target"] for g in own],mean,v)
        states[f"{seed}:own_activation"]=fit_projection([feature(g,"activation") for g in own],[g["target"] for g in own],mean,v)
        states[f"{seed}:own_text_io"]=fit_projection([feature(g,"text") for g in own],[g["target"] for g in own],mean,v)
        states[f"{seed}:own_shuffled_telemetry"]=fit_projection(shuffled(own,seed),[g["target"] for g in own],mean,v)
        for other in ACTOR_SEEDS:
            if other!=seed:
                og=byseed[other];states[f"{seed}:other:{other}"]=fit_projection([feature(g,"telemetry") for g in og],[g["target"] for g in og],mean,v)
    states["pooled"]=fit_projection([feature(g,"telemetry") for g in fit],[g["target"] for g in fit],mean,v)
    projection={"basis":v.tolist(),"singular_values":s.tolist(),"target_mean":mean.tolist(),"states":states,"target_order":[list(x) for x in TARGET_ORDER]}
    (root/"projection-state.json").write_bytes(canonical(projection)); projection_hash=hashlib.sha256((root/"projection-state.json").read_bytes()).hexdigest()
    at=[]
    for seed,a in actors.items():
        for ex in examples_for(ASSESSMENT_FAMILIES): at += [{**r,"seed":seed} for r in telemetry_rows(a,ex)]
    assessment=group_rows(at); assessment_hash=dump(root/"assessment-telemetry.jsonl",assessment)
    preds=[]
    global_const=mean.tolist()
    for seed in ACTOR_SEEDS:
        test=[g for g in assessment if g["seed"]==seed]; xt=[feature(g,"telemetry") for g in test]
        values={"own_telemetry":predict_projection(states[f"{seed}:own_telemetry"],xt,mean,v),"own_activation":predict_projection(states[f"{seed}:own_activation"],[feature(g,"activation") for g in test],mean,v),"own_text_io":predict_projection(states[f"{seed}:own_text_io"],[feature(g,"text") for g in test],mean,v),"own_shuffled_telemetry":predict_projection(states[f"{seed}:own_shuffled_telemetry"],xt,mean,v),"pooled_telemetry":predict_projection(states["pooled"],xt,mean,v),"global_constant":[global_const]*len(test),"own_constant":[torch.tensor([g["target"] for g in byseed[seed]],dtype=torch.float64).mean(0).tolist()]*len(test)}
        others=[predict_projection(states[f"{seed}:other:{o}"],xt,mean,v) for o in ACTOR_SEEDS if o!=seed]
        values["other_actor_telemetry"]=[[(others[0][i][j]+others[1][i][j]+others[2][i][j])/3 for j in range(10)] for i in range(len(test))]
        for method in METHODS:
            for g,p in zip(test,values[method]):preds.append({"example_id":g["example_id"],"family":g["family"],"method":method,"predicted":p,"seed":seed})
    preds.sort(key=lambda r:(r["method"],r["seed"],r["family"],r["example_id"])); pred_hash=dump(root/"predictions.jsonl",preds)
    lock={"assessment_telemetry_sha256":assessment_hash,"fitting_groups_sha256":fit_hash,"prediction_census":len(preds),"predictions_sha256":pred_hash,"projection_state_sha256":projection_hash,"state_slice":STATE_SLICE};(root/"prediction-lock.json").write_bytes(canonical(lock));lh=hashlib.sha256((root/"prediction-lock.json").read_bytes()).hexdigest()
    ae=[]
    for seed,a in actors.items():
        for ex in examples_for(ASSESSMENT_FAMILIES):ae += [{**r,"prediction_lock_sha256":lh,"seed":seed} for r in effect_rows(a,ex)]
    actual={ (g["seed"],g["family"],g["example_id"]):g["target"] for g in group_rows(at,ae)}
    joined=[{**r,"actual":actual[(r["seed"],r["family"],r["example_id"])]} for r in preds]; metrics=summarize(joined)
    dump(root/"assessment-effects.jsonl",ae)
    return finalize(root,{"accepted_evidence":False,"classification":classify(metrics),"confirmation_authorized":False,"metrics":metrics,"prediction_census":len(preds),"prediction_lock_sha256":lh,"stage0_pass":False,"state_slice":STATE_SLICE})
def finalize(root,summary):
    (root/"summary.json").write_bytes(canonical(summary));files=[]
    for p in sorted(root.iterdir()):raw=p.read_bytes();files.append({"bytes":len(raw),"path":p.name,"sha256":hashlib.sha256(raw).hexdigest()})
    (root/"manifest.json").write_bytes(canonical({"files":files,"state_slice":STATE_SLICE}));return summary

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--protocol",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.output,args.repo,args.protocol),indent=2,sort_keys=True))
