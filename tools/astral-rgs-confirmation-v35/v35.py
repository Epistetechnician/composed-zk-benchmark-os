from __future__ import annotations
import importlib.util,json,math,statistics,sys
from pathlib import Path
H=Path(__file__).resolve().parent;PP=H/"protocol.json";P=json.loads(PP.read_text())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);assert s and s.loader;m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
V30=load("v30v35",H.parent/"astral-rgs-response-free-v30/v30.py");WORDS=V30.WORDS[8:16];LOCKS=("rgs_core","rgs_worker","rgs_coordinator","astral_protocol","astral_validator","astral_cli")
def fixture():
 cases=[]
 for i,t in enumerate(WORDS):
  key=f"v35confirm-{i:02d}";c=[t,WORDS[(i+1)%8],WORDS[(i+3)%8],WORDS[(i+5)%8]];q=i%4;c=c[q:]+c[:q];cases.append({"case_id":f"v35case-{i:02d}","key":key,"target":t,"candidates":c,"train_prompt":f"Confirmation registry key: {key}. Associated value:","direct_prompt":f"Confirmation registry query: which value maps from {key}?\\nReturn only the value.","paraphrase_prompt":f"Using the learned confirmation registry, give the value associated with {key}.\\nReturn only the value."})
 body={"version":"mesh.astral_v35_confirmation_fixture.v1","cases":cases,"protected_fixture":V30.expected_fixture(),"replay_ratio":.25,"seed":350035};return{**body,"fixture_sha256":V30.stable_hash(body)}
def summary(d,p,pr,loss,delta):
 da=sum(x["correct"]for x in d)/8;pa=sum(x["correct"]for x in p)/8;ra=sum(x["correct"]for x in pr)/32;v=[float(x["loss"])for x in loss];g={"direct":da>=.75,"paraphrase":pa>=.75,"protected":ra>=.95,"finite_loss":len(v)==32 and all(math.isfinite(x)for x in v),"nonincreasing_loss":statistics.mean(v[-8:])<=statistics.mean(v[:8]),"reload":delta<=1e-5};q=all(g.values());return{"direct_accuracy":da,"paraphrase_accuracy":pa,"protected_accuracy":ra,"initial_loss_mean":statistics.mean(v[:8]),"final_loss_mean":statistics.mean(v[-8:]),"reload_max_score_delta":delta,"gates":g,"qualified":q,"status":"FreshAcquisitionConfirmed"if q else"FreshAcquisitionConfirmationBlocked"}
def validate(root):
 e=[];names=("artifact-manifest.json","fixture.json","model-result.json","model-process.json","confirmation-packet.json","preflight-receipt.json")
 if any(not(root/n).is_file()for n in names):return{"valid":False,"status":"Invalid","errors":["required"]}
 man,f,r,proc,packet,pre=[V30.read(root/n)for n in names];entries=man.get("files",[])
 if man.get("manifest_sha256")!=V30.stable_hash(entries):e.append("manifest.hash")
 listed=set()
 for x in entries:
  path=root/x["path"];listed.add(x["path"])
  if not path.is_file()or path.is_symlink()or x["sha256"]!=V30.sha256_file(path)or x["size_bytes"]!=path.stat().st_size:e.append("manifest.entry")
 actual={p.relative_to(root).as_posix()for p in root.rglob("*")if p.is_file()and p.name!="artifact-manifest.json"and not p.name.startswith("astral-validation-")}
 if actual!=listed or root.name!=f"astral-rgs-v35-confirmation-{str(man.get('manifest_sha256',''))[7:19]}-r1":e.append("manifest.census")
 if f!=fixture():e.append("fixture")
 body={k:v for k,v in r.items()if k!="result_sha256"}
 if r.get("result_sha256")!=V30.stable_hash(body)or r.get("version")!=P["result_version"]:e.append("result")
 for rows in(r.get("post_direct",[]),r.get("reload_direct",[]),r.get("reload_paraphrase",[]),r.get("reload_protected",[])):
  for row in rows:
   sc=row["candidate_scores"];sel=min(row["candidates"],key=lambda w:(-sc[w],w))
   if row["selected"]!=sel or row["correct"]is not(sel==row["target"]):e.append("decision")
 try:
  delta=max(abs(a["candidate_scores"][w]-b["candidate_scores"][w])for a,b in zip(r["post_direct"],r["reload_direct"],strict=True)for w in a["candidates"]);d=summary(r["reload_direct"],r["reload_paraphrase"],r["reload_protected"],r["loss_trace"],delta)
 except Exception:e.append("summary");d=None
 if r.get("summary")!=d:e.append("summary.mismatch")
 adapter=root/"state/adapter/adapters.safetensors"
 if not adapter.is_file()or r.get("adapter_sha256")!=V30.sha256_file(adapter):e.append("adapter")
 locks=pre.get("source_locks",{})
 if set(locks)!=set(LOCKS)or packet.get("source_locks")!=locks or pre.get("protocol_sha256")!=V30.sha256_file(PP):e.append("sources")
 for n in LOCKS:
  path=root/f"source-locks/{n}.source"
  if not path.is_file()or locks.get(n)!=V30.sha256_file(path):e.append(f"source.{n}")
 for n,path in{"astral_protocol":PP,"astral_validator":Path(__file__),"astral_cli":H/"validate_confirmation.py"}.items():
  if locks.get(n)!=V30.sha256_file(path):e.append(f"local.{n}")
 pb={k:v for k,v in packet.items()if k!="packet_sha256"}
 if packet.get("packet_sha256")!=V30.stable_hash(pb)or packet.get("version")!=P["packet_version"]or packet.get("summary")!=d:e.append("packet")
 status=(d or{}).get("status","Invalid")if not e else"Invalid";return{"version":"astral.v35_validation_report.v1","valid":not e,"status":status,"errors":e,"artifact_manifest_sha256":man.get("manifest_sha256"),"claim_ceiling":P["claim_ceiling"],"model_execution":False,"external_review":"NotRun"}
