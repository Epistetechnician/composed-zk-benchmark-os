import Std

namespace NanoInterpHostActivation

/-
State slice: proof-carrying-nano-host-activation-boundary-v1.

This is the declared record-level semantics for the read-only activation
boundary. It does not model a transformer, prove activation faithfulness, or
establish a causal intervention effect.
-/

def readOnlyActivationBinding (hookReached parametersUnchanged : Bool)
    (activationDigest parameterDigestBefore parameterDigestAfter : String) : Prop :=
  hookReached = true ∧ parametersUnchanged = true ∧ activationDigest ≠ "" ∧
    parameterDigestBefore = parameterDigestAfter

theorem readOnlyActivationBinding_refl (digest parameterDigest : String)
    (digest_nonempty : digest ≠ "") :
    readOnlyActivationBinding true true digest parameterDigest parameterDigest := by
  simp [readOnlyActivationBinding, digest_nonempty]

end NanoInterpHostActivation
