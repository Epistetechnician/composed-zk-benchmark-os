# V39 Quarter-Protection Preregistration

Status: `PreregisteredAndImplementationAuthorized / ExecutionNotAuthorized`.

V39 preserves the V38R2 corpus, matched controls, checkpoints, seeds, orders,
budgets, evaluations, and gates. Joint arms use protected replay on exactly
steps `3,7,11,15,19,23,27,31` of each later stage and matched task replay on
the other 24 steps. This is 25% of the fourth slot and 6.25% of total examples.

All 16 cells are rerun. Qualification still requires all-cell protected
retention `>=0.95`, task retention `[0.60,0.90]`, paraphrase `>=0.70`, and
matched retention loss `<=0.10`. This is development-only. Execution requires
fresh exact-commit authorization. Dynamic routing, CL-bench, confirmation, and
higher claims remain forbidden.
