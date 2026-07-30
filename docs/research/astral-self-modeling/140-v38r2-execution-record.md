# V38R2 Fixed-Allocation Execution Record

Status: `ValidNegative / FixedProtectionAllocationBlocked`.

Artifact `astral-rgs-v38r2-fixed-allocation-772ecd50efff-r1` is independently
valid with no errors. All 16 cells, 2,048 gradient steps, 786,432 update
tokens, fixed schedules, adapter hashes, and reload checks passed.

Alternating task/protection replay restored protected V30 accuracy to 1.0 in
every joint cell. The cost exceeded the frozen task-memory limits:

- recent task-only retention `0.791667`; joint recent `0.59375`;
  retention drop `0.197917`;
- reservoir task-only retention `0.6875`; joint reservoir `0.541667`;
  retention drop `0.145833`;
- joint recent paraphrase `0.703125`; joint reservoir `0.664063`.

Neither joint arm met the `[0.60, 0.90]` retention band and `<=0.10` matched
retention-drop ceiling. The fixed 50/50 fourth-slot split overprotected at the
expense of task retention. This is outcome-informed development evidence, not
confirmation. Dynamic allocation, Astral routing, CL-bench, SOTA, and
breakthrough claims remain blocked.
