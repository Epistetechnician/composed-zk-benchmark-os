"""Rank-four structured-effect primitives for V16."""
from __future__ import annotations
import copy, hashlib, math, sys
from pathlib import Path
import torch
from torch import nn
TOOLS=Path(__file__).resolve().parents[1]
for name in ("astral-stage0-learned","astral-stage0-learned-v3","astral-stage0-causal-target-v13"):
    sys.path.insert(0,str(TOOLS/name))
from learned_stage0 import configure_runtime, examples_for, tensors  # noqa:E402
from learned_stage0_v3 import semantic_digest, trajectory_digest  # noqa:E402
from learned_stage0_v13 import CausalTargetActor, OPERATORS, SITES, effect_rows, metric_summary, telemetry_rows  # noqa:E402
STATE_SLICE="astral-stage0c-structured-effect-explainer-v16"
ACTOR_SEEDS=(283,293,307,311); RESERVED_SEEDS=(173,179,181)
FIT_FAMILIES=range(688,704); ASSESSMENT_FAMILIES=range(704,712)
TARGET_ORDER=tuple((site,op) for op in OPERATORS for site in SITES)
METHODS=("own_telemetry","other_actor_telemetry","pooled_telemetry","own_activation","own_text_io","own_shuffled_telemetry","own_constant","global_constant")
RANK=4; ALPHA=.001

def batch_indices(g):
    f=torch.randint(160,(8,),generator=g); return (f[:,None]*16+torch.arange(16)[None,:]).reshape(-1)
def train_actor(seed):
    if seed not in ACTOR_SEEDS or seed in RESERVED_SEEDS: raise ValueError("unauthorized V16 seed")
    configure_runtime(); torch.manual_seed(seed); actor=CausalTargetActor(seed)
    tr,dv=examples_for(range(160)),examples_for(range(160,192)); tx,ty=tensors(tr); dx,dy=tensors(dv)
    opt=torch.optim.AdamW(actor.parameters(),lr=.003,weight_decay=.01); g=torch.Generator().manual_seed(seed)
    plan=hashlib.sha256(); best=(float("inf"),0,None); trajectory=[]
    for step in range(1,2001):
        actor.train(); ix=batch_indices(g); plan.update(ix.numpy().tobytes()); opt.zero_grad(set_to_none=True)
        loss=nn.functional.cross_entropy(actor(tx[ix])[0],ty[ix]); loss.backward(); nn.utils.clip_grad_norm_(actor.parameters(),1.); opt.step()
        if step%25==0:
            actor.eval()
            with torch.no_grad(): dl=float(nn.functional.cross_entropy(actor(dx)[0],dy))
            trajectory.append({"dev_loss":dl,"step":step})
            if dl<best[0]: best=(dl,step,copy.deepcopy(actor.state_dict()))
    actor.load_state_dict(best[2]); actor.eval()
    with torch.no_grad(): ta=float((actor(tx)[0].argmax(1)==ty).float().mean()); da=float((actor(dx)[0].argmax(1)==dy).float().mean())
    return actor,{"batch_plan_sha256":plan.hexdigest(),"checkpoint_sha256":semantic_digest(actor),"dev_accuracy":da,"eligible":ta>=.95 and da>=.95,"selected_dev_loss":best[0],"selected_step":best[1],"seed":seed,"train_accuracy":ta,"trajectory_sha256":trajectory_digest(trajectory)}
def reproduce(seed):
    actor,a=train_actor(seed); _,b=train_actor(seed); keys=("batch_plan_sha256","checkpoint_sha256","selected_step","trajectory_sha256")
    ok=all(a[k]==b[k] for k in keys); return actor,{"eligible":bool(a["eligible"] and b["eligible"] and ok),"first":a,"reproducible":ok,"second":b,"seed":seed}
def target_key(site,operator): return f"{site}|{operator}"
def group_rows(telemetry,effects=None):
    groups={}
    for row in telemetry: groups.setdefault((row["seed"],row["family"],row["example_id"]),{"telemetry":{}})["telemetry"][target_key(row["site"],row["operator"])]=row
    if effects:
        for row in effects: groups.setdefault((row["seed"],row["family"],row["example_id"]),{"telemetry":{}}).setdefault("effects",{})[target_key(row["site"],row["operator"])]=row["effect"]
    out=[]
    for key,g in sorted(groups.items()):
        if len(g["telemetry"])!=10 or (effects and len(g.get("effects",{}))!=10): raise ValueError("incomplete structured group")
        base=g["telemetry"][target_key(*TARGET_ORDER[0])]
        item={"seed":key[0],"family":key[1],"example_id":key[2],"bits":base["bits"],"clean_logits":base["clean_logits"],"label":base["label"],"rows":g["telemetry"]}
        if effects: item["target"]=[float(g["effects"][target_key(*target)]) for target in TARGET_ORDER]
        out.append(item)
    return out
def feature(group,kind):
    prefix=[*map(float,group["bits"]),*map(float,group["clean_logits"]),float(group["label"])]
    rows=group["rows"]; field=[]
    for site in SITES:
        row=rows[target_key(site,OPERATORS[0])]
        vector=list(map(float,row["site_vector"]))
        if kind=="telemetry": field+=vector
        elif kind=="activation":
            size=8 if site.startswith("head") else 32
            field += [float(row[x]) for x in ("site_norm","site_mean","site_max_abs","site_attention")]+[0.]*(size-4)
        elif kind=="text": field += [0.]*(8 if site.startswith("head") else 32)
        else: raise ValueError("unknown feature kind")
    values=prefix+field
    if len(values)!=71 or not all(math.isfinite(x) for x in values): raise ValueError("invalid structured feature")
    return values
def basis(targets):
    y=torch.tensor(targets,dtype=torch.float64); mean=y.mean(0); _,s,vh=torch.linalg.svd(y-mean,full_matrices=False); v=vh[:RANK].T
    for col in range(RANK):
        index=int(v[:,col].abs().argmax())
        if v[index,col]<0: v[:,col]*=-1
    return mean,v,s
def fit_projection(x,y,mean,v):
    x=torch.tensor(x,dtype=torch.float64); y=torch.tensor(y,dtype=torch.float64); xm=x.mean(0); xs=x.std(0,unbiased=False); xs=torch.where(xs<1e-12,torch.ones_like(xs),xs)
    d=torch.cat((torch.ones((len(x),1),dtype=x.dtype),(x-xm)/xs),1); z=(y-mean)@v; p=torch.eye(d.shape[1],dtype=x.dtype)*ALPHA;p[0,0]=0
    w=torch.linalg.solve(d.T@d+p,d.T@z); return {"mean":xm.tolist(),"scale":xs.tolist(),"weights":w.tolist()}
def predict_projection(state,x,mean,v):
    x=torch.tensor(x,dtype=torch.float64); xm=torch.tensor(state["mean"],dtype=torch.float64); xs=torch.tensor(state["scale"],dtype=torch.float64); w=torch.tensor(state["weights"],dtype=torch.float64)
    d=torch.cat((torch.ones((len(x),1),dtype=x.dtype),(x-xm)/xs),1); return (mean+(d@w)@v.T).tolist()
def shuffled(groups,seed):
    result=[feature(g,"telemetry") for g in groups]; perm=torch.randperm(len(groups),generator=torch.Generator().manual_seed(seed)).tolist()
    return [row[:7]+result[perm[i]][7:] for i,row in enumerate(result)]
