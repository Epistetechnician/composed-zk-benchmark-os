from __future__ import annotations
import argparse,importlib.util,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;S=importlib.util.spec_from_file_location("v36_validator",H/"v36.py");assert S and S.loader;M=importlib.util.module_from_spec(S);sys.modules[S.name]=M;S.loader.exec_module(M)
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--artifact-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args(argv);r=M.validate(a.artifact_root.resolve());data=(json.dumps(r,allow_nan=False,indent=2,sort_keys=True)+"\n").encode()
 with a.output.open("xb") as f:f.write(data);f.flush();os.fsync(f.fileno())
 print(json.dumps(r,sort_keys=True));return 0 if r["valid"] else 1
if __name__=="__main__":raise SystemExit(main())
