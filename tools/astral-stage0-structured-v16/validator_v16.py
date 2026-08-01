"""V16 manifest and prediction-lock validator."""
import hashlib,json
from pathlib import Path
from structured_v16 import STATE_SLICE
from run_structured_v16 import canonical
def load(p):
    raw=p.read_bytes();v=json.loads(raw)
    if raw!=canonical(v):raise ValueError("noncanonical JSON")
    return v
def validate(root:Path,protocol:Path):
    m=load(root/"manifest.json")
    if m["state_slice"]!=STATE_SLICE:raise ValueError("state drift")
    expected={r["path"]:r for r in m["files"]};actual={p.name for p in root.iterdir() if p.name!="manifest.json"}
    if set(expected)!=actual:raise ValueError("census drift")
    for name,row in expected.items():
        raw=(root/name).read_bytes()
        if row!={"bytes":len(raw),"path":name,"sha256":hashlib.sha256(raw).hexdigest()}:raise ValueError("digest drift")
    if load(root/"protocol.lock.json")!={"protocol_sha256":hashlib.sha256(protocol.read_bytes()).hexdigest(),"state_slice":STATE_SLICE}:raise ValueError("protocol drift")
    s=load(root/"summary.json")
    if s["state_slice"]!=STATE_SLICE or any(s.get(k) for k in ("accepted_evidence","confirmation_authorized","stage0_pass")):raise ValueError("claim drift")
    lock=load(root/"prediction-lock.json")
    for field,name in (("fitting_groups_sha256","fitting-groups.jsonl"),("assessment_telemetry_sha256","assessment-telemetry.jsonl"),("predictions_sha256","predictions.jsonl"),("projection_state_sha256","projection-state.json")):
        if lock[field]!=hashlib.sha256((root/name).read_bytes()).hexdigest():raise ValueError("lock drift")
    lh=hashlib.sha256((root/"prediction-lock.json").read_bytes()).hexdigest()
    for line in (root/"assessment-effects.jsonl").read_bytes().splitlines():
        if json.loads(line)["prediction_lock_sha256"]!=lh:raise ValueError("ordering drift")
    return s
