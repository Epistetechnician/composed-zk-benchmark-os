# V40R2 Current-Margin Forward Correction

State slice: `V40R2NativeMLXRuntimeImplementation`.

Status: `CurrentMarginBudgetCorrected / NativeRuntimeIncomplete`.

The native-runtime audit found that a separate direct-query current margin
would consume an unbudgeted forward pass. Current margin is now computed from
the first current example in the exact scheduled gradient batch. Internal
telemetry uses that same forward. The protected-margin prompt remains the only
additional per-row feature forward and is already covered by the locked
25,728-token budget.

No model execution occurred.
