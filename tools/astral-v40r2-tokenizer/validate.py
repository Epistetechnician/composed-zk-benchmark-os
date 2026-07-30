from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def stable(v):return "sha256:"+hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(root):
 errors=[];path=root/"qualification.json"
 if not path.is_file():return {"valid":False,"errors":["required"]}
 x=json.loads(path.read_text());r=x.get("report",{});c=x.get("corpus")
 rows=r.get("rows",[]);selected=[q for q in rows if q.get("canonical_single")][:32]
 if r.get("selected")!=selected or len(selected)!=32 or any(len(q.get("token_ids",[]))!=1 for q in selected):errors.append("selection")
 rb={k:v for k,v in r.items() if k!="qualification_sha256"}
 if r.get("qualification_sha256")!=stable(rb):errors.append("qualification.hash")
 if not isinstance(c,dict):errors.append("corpus")
 else:
  cb={k:v for k,v in c.items() if k!="corpus_sha256"}
  if c.get("corpus_sha256")!=stable(cb) or c.get("qualification_sha256")!=r.get("qualification_sha256"):errors.append("corpus.hash")
  fam=c.get("families",[]);ids=[f["family_id"] for f in fam];cases=[q["case_id"] for f in fam for t in f["tasks"] for q in t["cases"]]
  if len(fam)!=12 or len(ids)!=len(set(ids)) or len(cases)!=384 or len(cases)!=len(set(cases)):errors.append("disjointness")
 body={"report":r,"corpus":c,"model_path":x.get("model_path"),"forward_pass":x.get("forward_pass")}
 if root.name!=f"astral-rgs-v40r2-tokenizer-{stable(body)[7:19]}-r1" or x.get("forward_pass") is not False:errors.append("identity")
 return {"version":"astral.v40r2_tokenizer_validation.v1","valid":not errors,"errors":errors,"qualification_sha256":r.get("qualification_sha256"),"corpus_sha256":(c or {}).get("corpus_sha256"),"model_execution":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--artifact-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();report=validate(a.artifact_root.resolve());a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");return 0 if report["valid"] else 1
if __name__=="__main__":raise SystemExit(main())
