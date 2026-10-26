"""Builds manifest.json for the V53-V56 review packet (run from repo root). Slice: v53-v56-review-packet-v1."""
import hashlib, json, subprocess, glob, os
A = "docs/research/astral-self-modeling/"
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def git(*a): return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()
def entry(p):
    log = git("log", "--format=%H", "--", p).splitlines()
    return {"path": p, "sha256": sha(p), "bytes": os.path.getsize(p), "first_commit": log[-1], "last_commit": log[0]}
code = sorted(p for v in range(50, 60) for p in glob.glob("tools/astral-neuron-level-causal-lane-v%d/*.py" % v) + glob.glob("tools/astral-neuron-level-causal-lane-v%d/tests/*.py" % v))
protocols = sorted(glob.glob(A + "1[34][0-9]-neuron-level-causal-lane-v5*-protocol.md"))
results = sorted(glob.glob(A + "v5[0-9]-run/results/*.json") + glob.glob(A + "v5[0-9]-run/**/corpus-public.json", recursive=True) + glob.glob(A + "v5[0-9]-run/**/label-audit.json", recursive=True))
records = sorted(glob.glob(A + "v5[0-9]-run/**/README.md", recursive=True) + glob.glob(A + "v5[0-9]-run/**/allocation-receipt.json", recursive=True) + glob.glob(A + "v5[34]-run/accepted-ledger/*") + [A + "neuron-v53-v54-summary.md"])
m = {"packet": "neuron-v53-v59-review-packet-v1", "status": "UNREVIEWED", "claim_ceiling": "OwnerSelfAttestedLocalDevelopment",
     "head_at_build": git("rev-parse", "HEAD"),
     "authorization": {"agents_md_slices": ["neuron-control-lanes-unreviewed-execution-v1", "v53-owner-self-attestation-v1", "v54-owner-self-attestation-v1"],
                       "owner_waived_independent_accept": True, "usd_ceiling": 50.0, "usd_spent_approx": 45.0,
                       "provider": "GiveMeANode h100-1, europe-north1, node v51-full-r1, id 6e1eaffb-2411-49bc-8d6d-f90ec5d73fe3"},
     "models": {"pythia-2.8b": "2a259cdd96a4beb1cdf467512e3904197345f6a9", "pythia-1.4b": "fedc38a16eea3bd36a96b906d78d11d2ce18ed79"},
     "corpora": {"V50-V53 books (item-disjoint re-draws)": "manifest digest 8e3d127c733b81019598493a4bdc6c2493e2c82bf0422a1d823752c219dacc30 (V51 corpus)",
                 "V54/V55 fresh books": "manifest digest 59c514f0c5a89a1cf046f94a64e4abbe1254158bf3e992f37fbcf5e754a33221"},
     "code": [entry(p) for p in code], "protocols": [entry(p) for p in protocols],
     "results": [entry(p) for p in results], "records": [entry(p) for p in records if os.path.isfile(p)]}
json.dump(m, open(A + "neuron-v53-v56-review-packet/manifest.json", "w"), indent=1, sort_keys=True)
print(hashlib.sha256(open(A + "neuron-v53-v56-review-packet/manifest.json", "rb").read()).hexdigest())
