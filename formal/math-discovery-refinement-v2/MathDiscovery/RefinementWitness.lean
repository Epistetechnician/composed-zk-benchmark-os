import Std

namespace MathDiscovery

/-
State slice: proof-carrying-symbolic-transfer-refinement-v2.
Protocol identity: weco-symbolic-discovery-transfer-refinement-v2.

This is a kernel-checkable witness schema. It binds the concrete evaluator
run to digests and records the bounded adversarial checks. It does not claim
that Python execution is itself a verified implementation of the V1 contract.
-/

structure RefinementWitness where
  protocolIdentity : String
  evaluatorDigest : String
  formalContractDigest : String
  fixtureDigest : String
  configDigest : String
  traceDigest : String
  noHiddenTruthLeakage : Bool
  duplicateIdsRejected : Bool
  malformedDigestsRejected : Bool
  permutationInvariant : Bool
  metricGamingRejected : Bool
  multiSeedSplitsChecked : Bool
deriving DecidableEq, Repr

def Valid (witness : RefinementWitness) : Prop :=
  witness.protocolIdentity = "weco-symbolic-discovery-transfer-refinement-v2" ∧
  witness.noHiddenTruthLeakage = true ∧
  witness.duplicateIdsRejected = true ∧
  witness.malformedDigestsRejected = true ∧
  witness.permutationInvariant = true ∧
  witness.metricGamingRejected = true ∧
  witness.multiSeedSplitsChecked = true

def claimCeiling : String := "LocalMachineCheckedFormalContractOnly"

theorem valid_witness_preserves_claim_ceiling (witness : RefinementWitness)
    (_ : Valid witness) : claimCeiling = "LocalMachineCheckedFormalContractOnly" := by
  rfl

end MathDiscovery
