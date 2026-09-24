import Std

namespace NanoInterp

/-
State slice: proof-carrying-nano-interp-v1.

This is the V1 toy-host semantics. It proves exact feature lookup for a
captured finite activation list. It does not model a neural network or prove
that a real host implementation refines this definition.
-/

def featureActivation (values : List Int) (index : Nat) : Int :=
  values.getD index 0

theorem featureActivation_zero (value second : Int) :
    featureActivation [value, second] 0 = value := by
  rfl

theorem featureActivation_one (value second : Int) :
    featureActivation [value, second] 1 = second := by
  rfl

end NanoInterp
