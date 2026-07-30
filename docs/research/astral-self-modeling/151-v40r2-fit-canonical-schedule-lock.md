# V40R2 Fit Canonical Schedule Lock

State slice: `V40R2FitCanonicalScheduleLock`.

Status: `ModelFreeScheduleLocked / ModelAcquisitionNotAuthorized`.

A public versioned seed deterministically selects exactly eight protected
continuations among 32 steps for each of four fit families and stages 2, 3,
and 4. All other steps continue through task replay.

The schedule constructor accepts only protocol and corpus hashes. Feature
values, counterfactual outcomes, tune families, and assessment families are
not inputs. The validator reconstructs all 12 cells from the public seed and
rejects altered seeds, family leakage, missing or duplicate cells, unequal
budgets, continuation mismatches, and hash tampering.

The schedule is a balanced fit-data acquisition instrument. It is not a router
baseline and produces no scientific evidence. Model execution, feature
acquisition, counterfactual labels, fitting, tune access, and assessment access
remain unauthorized.
