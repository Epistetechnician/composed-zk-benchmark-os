from __future__ import annotations
import importlib.util,json,math,statistics,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; PROTOCOL_PATH=HERE/"protocol.json"; PROTOCOL=json.loads(PROTOCOL_PATH.read_text())
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path); assert s and s.loader; m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m
V30=load("v30_for_v33",HERE.parent/"astral-rgs-response-free-v30/v30.py"); V32=load("v32_for_v33",HERE.parent/"astral-rgs-optimizer-v32/v32.py")
SOURCE_LOCKS=("rgs_core","rgs_worker","rgs_coordinator","astral_protocol","astral_validator","astral_cli")
def expected_fixture():
    prior=V32.expected_fixture(); cases=[{**c,"train_prompt":f"Development registry key: {c['key']}. Associated value:"} for c in prior["cases"]]
    body={"version":"mesh.astral_v33_target_free_fixture.v1","cases":cases,"protected_fixture":prior["protected_fixture"],"arm":{"arm_id":"fp32_clip_lr1e4","learning_rate":1e-4},"budget":prior["budget"],"gates":prior["gates"]}; return {**body,"fixture_sha256":V30.stable_hash(body)}
def summary(base,arm):
    ba=sum(r["correct"] for r in base)/32; losses=[float(r["loss"]) for r in arm["loss_trace"]]; direct=sum(r["correct"] for r in arm["direct"])/8; para=sum(r["correct"] for r in arm["paraphrase"])/8; protected=sum(r["correct"] for r in arm["protected"])/32
    gates={"direct":direct>=.75,"paraphrase":para>=.625,"protected":ba-protected<=.05,"finite_loss":len(losses)==32 and all(math.isfinite(x) for x in losses),"nonincreasing_loss":statistics.mean(losses[-8:])<=statistics.mean(losses[:8]),"max_loss":max(losses)<=10}
    a={"direct_accuracy":direct,"paraphrase_accuracy":para,"protected_accuracy":protected,"protected_drop":ba-protected,"initial_loss_mean":statistics.mean(losses[:8]),"final_loss_mean":statistics.mean(losses[-8:]),"maximum_loss":max(losses),"gates":gates,"qualified":all(gates.values())}; return {"base_protected_accuracy":ba,"arm":a,"qualified":a["qualified"],"status":"TargetFreeObjectiveQualified" if a["qualified"] else "TargetFreeObjectiveBlocked"}
def validate(root):
    errors=[]; names=("artifact-manifest.json","fixture.json","model-result.json","model-process.json","objective-packet.json","preflight-receipt.json")
    if any(not(root/n).is_file() for n in names): return {"valid":False,"status":"Invalid","errors":["required"]}
    manifest,fixture,result,process,packet,preflight=[V30.read(root/n) for n in names]; entries=manifest.get("files",[])
    if manifest.get("manifest_sha256")!=V30.stable_hash(entries): errors.append("manifest.hash")
    listed=set()
    for e in entries:
        p=root/e["path"]; listed.add(e["path"])
        if not p.is_file() or p.is_symlink() or e["sha256"]!=V30.sha256_file(p) or e["size_bytes"]!=p.stat().st_size: errors.append("manifest.entry")
    actual={p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name!="artifact-manifest.json" and not p.name.startswith("astral-validation-")}
    if actual!=listed or root.name!=f"astral-rgs-v33-target-free-{str(manifest.get('manifest_sha256',''))[7:19]}-r1": errors.append("manifest.census")
    if fixture!=expected_fixture(): errors.append("fixture")
    body={k:v for k,v in result.items() if k!="result_sha256"}
    if result.get("result_sha256")!=V30.stable_hash(body) or result.get("version")!=PROTOCOL["result_version"]: errors.append("result")
    for rows in [result.get("base_protected",[])]+[result.get("arm",{}).get(k,[]) for k in ("direct","paraphrase","protected")]:
        for row in rows:
            scores=row.get("candidate_scores",{}); selected=min(row["candidates"],key=lambda w:(-scores[w],w))
            if set(scores)!=set(row["candidates"]) or row.get("selected")!=selected or row.get("correct") is not(selected==row["target"]): errors.append("decision")
    try: derived=summary(result["base_protected"],result["arm"])
    except Exception: errors.append("summary"); derived=None
    if result.get("summary")!=derived: errors.append("summary.mismatch")
    inv=result.get("model_inventory",{})
    if inv.get("checkpoint_sha256")!=PROTOCOL["checkpoint_sha256"] or inv.get("tokenizer_sha256")!=PROTOCOL["tokenizer_sha256"]: errors.append("model")
    adapter=root/"state/adapter/adapters.safetensors"
    if not adapter.is_file() or result.get("arm",{}).get("adapter_sha256")!=V30.sha256_file(adapter): errors.append("adapter")
    locks=preflight.get("source_locks",{})
    if set(locks)!=set(SOURCE_LOCKS) or packet.get("source_locks")!=locks or preflight.get("protocol_sha256")!=V30.sha256_file(PROTOCOL_PATH): errors.append("sources")
    for n in SOURCE_LOCKS:
        p=root/f"source-locks/{n}.source"
        if not p.is_file() or locks.get(n)!=V30.sha256_file(p): errors.append(f"source.{n}")
    for n,p in {"astral_protocol":PROTOCOL_PATH,"astral_validator":Path(__file__),"astral_cli":HERE/"validate_objective.py"}.items():
        if locks.get(n)!=V30.sha256_file(p): errors.append(f"local.{n}")
    pb={k:v for k,v in packet.items() if k!="packet_sha256"}
    if packet.get("packet_sha256")!=V30.stable_hash(pb) or packet.get("version")!=PROTOCOL["packet_version"] or packet.get("summary")!=derived: errors.append("packet")
    status=(derived or {}).get("status","Invalid") if not errors else "Invalid"; return {"version":"astral.v33_validation_report.v1","valid":not errors,"status":status,"errors":errors,"artifact_manifest_sha256":manifest.get("manifest_sha256"),"claim_ceiling":PROTOCOL["claim_ceiling"],"model_execution":False,"external_review":"NotRun"}
