# V41R26 Multi-Panel Replay Qualification Preregistration

State slice: `V41R26MultiPanelReplayQualificationDesign`.

Status: `ProspectivelyFrozen / LocallyQualified / ImplementationPending / ExecutionUnauthorized`.

V41R26 freezes sixteen fresh panels by three fresh seeds, producing 48
unchanged-method runs. New deterministic 64-case acquisition and 256-row
protected instruments prevent reuse. Historical V41R24R2 and V41R25 results
do not enter the primary estimator.

The campaign preflight requires perfect base accuracy on all protected rows and
at least three initially incorrect acquisition cases in each panel. Any failure
stops before training. A run passes only with 4/4 acquisition gates, protected
accuracy at least 0.98, and exact reload. Qualification requires all eighteen
runs to pass, a 95% Wilson lower bound above 0.80, every panel passing every
seed, and zero governance violations.

The panel is the independent unit and passes only when all three seeds pass.
Qualification therefore requires 16/16 panels and 48/48 runs. The independent
local validator reconstructs all instruments, panel identities, method
constants, and the statistical rule. Runtime and claims above
`LocalMultiPanelReplayQualificationProtocolV41R26` remain unauthorized.
