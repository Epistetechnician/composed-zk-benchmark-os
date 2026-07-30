from __future__ import annotations
import importlib.util,json,math,statistics,sys
from pathlib import Path
H=Path(__file__).resolve().parent; PP=H/"protocol.json"; P=json.loads(PP.read_text())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p); assert s and s.loader; m=importlib.util.module_from_spec(s); sys.modules[n]=m; s.loader.exec_module(m); return m
V30=load("v30_v34",H.parent/"astral-rgs-response-free-v30/v30.py"); V33=load("v33_v34",H.parent/"astral-rgs-target-free-v33/v33.py"); LOCKS=("rgs_core","rgs_worker","rgs_coordinator","astral_protocol","astral_validator","astral_cli")
def fixture():
 p=V33.expected_fixture(); body={"version":"mesh.astral_v34_replay_fixture.v1","cases":p["cases"],"protected_fixture":p["protected_fixture"],"arms":P["arms"],"budget":p["budget"],"gates":{"direct_floor":.75,"paraphrase_floor":.75,"protected_floor":.95}}; return {**body,"fixture_sha256":V30.stable_hash(body)}
def summary(arms):
 out={}
 for aid in P["arms"]:
  a=arms[aid]; loss=[float(x["loss"]) for x in a["loss_trace"]]; d=sum(x["correct"] for x in a["direct"])/8; q=sum(x["correct"] for x in a["paraphrase"])/8; pr=sum(x["correct"] for x in a["protected"])/32; gates={"direct":d>=.75,"paraphrase":q>=.75,"protected":pr>=.95,"finite_loss":len(loss)==32 and all(math.isfinite(x) for x in loss),"nonincreasing_loss":statistics.mean(loss[-8:])<=statistics.mean(loss[:8])}; out[aid]={"direct_accuracy":d,"paraphrase_accuracy":q,"protected_accuracy":pr,"initial_loss_mean":statistics.mean(loss[:8]),"final_loss_mean":statistics.mean(loss[-8:]),"gates":gates,"qualified":all(gates.values())}
 sel=next((a for a in P["arms"] if out[a]["qualified"]),None); return {"arms":out,"selected_arm":sel,"qualified":sel is not None,"status":"ProtectedReplayQualified" if sel else "ProtectedReplayBlocked"}
def validate(root):
 e=[]; names=("artifact-manifest.json","fixture.json","model-result.json","model-process.json","replay-packet.json","preflight-receipt.json")
 if any(not(root/n).is_file() for n in names): return {"valid":False,"status":"Invalid","errors":["required"]}
 man,f,r,proc,packet,pre=[V30.read(root/n) for n in names]; entries=man.get("files",[])
 if man.get("manifest_sha256")!=V30.stable_hash(entries): e.append("manifest.hash")
 listed=set()
 for x in entries:
  p=root/x["path"]; listed.add(x["path"])
  if not p.is_file() or p.is_symlink() or x["sha256"]!=V30.sha256_file(p) or x["size_bytes"]!=p.stat().st_size:e.append("manifest.entry")
 actual={p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name!="artifact-manifest.json" and not p.name.startswith("astral-validation-")}
 if actual!=listed or root.name!=f"astral-rgs-v34-protected-replay-{str(man.get('manifest_sha256',''))[7:19]}-r1":e.append("manifest.census")
 if f!=fixture():e.append("fixture")
 body={k:v for k,v in r.items() if k!="result_sha256"}
 if r.get("result_sha256")!=V30.stable_hash(body) or r.get("version")!=P["result_version"]:e.append("result")
 for a in r.get("arms",{}).values():
  for rows in (a.get("direct",[]),a.get("paraphrase",[]),a.get("protected",[])):
   for row in rows:
    scores=row["candidate_scores"]; sel=min(row["candidates"],key=lambda w:(-scores[w],w))
    if row["selected"]!=sel or row["correct"] is not(sel==row["target"]):e.append("decision")
 try:d=summary(r["arms"])
 except Exception:e.append("summary");d=None
 if r.get("summary")!=d:e.append("summary.mismatch")
 for aid,a in r.get("arms",{}).items():
  p=root/f"states/{aid}/adapter/adapters.safetensors"
  if not p.is_file() or a.get("adapter_sha256")!=V30.sha256_file(p):e.append(f"adapter.{aid}")
 locks=pre.get("source_locks",{})
 if set(locks)!=set(LOCKS) or packet.get("source_locks")!=locks or pre.get("protocol_sha256")!=V30.sha256_file(PP):e.append("sources")
 for n in LOCKS:
  p=root/f"source-locks/{n}.source"
  if not p.is_file() or locks.get(n)!=V30.sha256_file(p):e.append(f"source.{n}")
 for n,p in {"astral_protocol":PP,"astral_validator":Path(__file__),"astral_cli":H/"validate_replay.py"}.items():
  if locks.get(n)!=V30.sha256_file(p):e.append(f"local.{n}")
 pb={k:v for k,v in packet.items() if k!="packet_sha256"}
 if packet.get("packet_sha256")!=V30.stable_hash(pb) or packet.get("version")!=P["packet_version"] or packet.get("summary")!=d:e.append("packet")
 status=(d or {}).get("status","Invalid") if not e else "Invalid"; return {"version":"astral.v34_validation_report.v1","valid":not e,"status":status,"errors":e,"artifact_manifest_sha256":man.get("manifest_sha256"),"claim_ceiling":P["claim_ceiling"],"model_execution":False,"external_review":"NotRun"}
