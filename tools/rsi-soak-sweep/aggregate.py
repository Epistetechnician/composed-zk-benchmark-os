"""Aggregate per-campaign soak summaries written by sweep.sh (JSON lines)."""
import collections
import json
import sys

KEYS = [
    "case_count", "replay_completed_count", "replay_failed_count", "traces_evaluated",
    "local_oracle_accepted_count", "local_oracle_rejected_count",
    "local_oracle_capability_gap_count", "mutation_variant_count",
    "mutation_no_target_count", "pack_write_count", "failure_count",
]


def main(path):
    rows = [json.loads(line) for line in open(path) if line.strip()]
    errors = [r for r in rows if r["rc"] != 0]
    print(f"runs={len(rows)} nonzero_rc={len(errors)}")
    per_family = collections.OrderedDict()
    for r in rows:
        if r["rc"] != 0:
            continue
        agg = per_family.setdefault(r["family"], collections.Counter())
        agg["runs"] += 1
        for k in KEYS:
            agg[k] += r["summary"][k]
        if r["summary"]["claim_boundary"] != "Level0DesignNote":
            agg["claim_boundary_violations"] += 1
    for fam, agg in per_family.items():
        print(fam, {k: agg[k] for k in ["runs"] + KEYS + ["claim_boundary_violations"]})


if __name__ == "__main__":
    main(sys.argv[1])
