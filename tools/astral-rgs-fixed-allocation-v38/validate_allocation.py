import argparse, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
from v38 import validate
def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--artifact-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args(argv)
    report=validate(a.artifact_root.resolve());a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");return 0 if report["valid"] else 1
if __name__=="__main__":raise SystemExit(main())
