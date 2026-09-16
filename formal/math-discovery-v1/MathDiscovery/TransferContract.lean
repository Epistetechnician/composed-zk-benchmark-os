import Std

namespace MathDiscovery

/-
State slice: proof-carrying-symbolic-transfer-formal-v1.
Protocol identity: weco-symbolic-discovery-transfer-formal-v1.

This file proves only the abstract M0 contract. It does not claim that a
Python, Rust, model, provider, or ZK implementation refines these definitions.
-/

abbrev Digest := String
abbrev Token := Nat
abbrev Program := List Token

structure PublicTask where
  id : Nat
  publicExamples : List (Nat × Nat)
  assessmentInputs : List Nat
  maxDepth : Nat
deriving DecidableEq, Repr

structure TruthTask where
  publicTask : PublicTask
  hiddenProgram : Program
  assessmentOutputs : List Nat
deriving DecidableEq, Repr

structure Episode where
  fit : List TruthTask
  assessment : List TruthTask
deriving DecidableEq, Repr

abbrev PublicEpisode := List PublicTask × List PublicTask
abbrev Candidate := PublicEpisode → List Program

def publicView (episode : Episode) : PublicEpisode :=
  (episode.fit.map TruthTask.publicTask, episode.assessment.map TruthTask.publicTask)

def candidateRun (candidate : Candidate) (episode : Episode) : List Program :=
  candidate (publicView episode)

/- The candidate interface has no term of either hidden-truth field. -/
def replaceTruth (episode : Episode) (replacement : Program) : Episode :=
  { episode with
    fit := episode.fit.map fun task => { task with hiddenProgram := replacement }
    assessment := episode.assessment.map
      fun task => { task with hiddenProgram := replacement }
  }

theorem publicView_replaceTruth (episode : Episode) (replacement : Program) :
    publicView (replaceTruth episode replacement) = publicView episode := by
  simp [publicView, replaceTruth]

theorem candidateRun_replaceTruth (candidate : Candidate) (episode : Episode)
    (replacement : Program) :
    candidateRun candidate (replaceTruth episode replacement) =
      candidateRun candidate episode := by
  unfold candidateRun
  rw [publicView_replaceTruth]

def ProgramValid (vocabulary : List Token) (maxDepth : Nat) (program : Program) : Prop :=
  program.length ≤ maxDepth ∧ ∀ token, token ∈ program → token ∈ vocabulary

def OutputsValid (vocabulary : List Token) (tasks : List PublicTask)
    (outputs : List Program) : Prop :=
  outputs.length = tasks.length ∧
    ∀ program task, (program, task) ∈ outputs.zip tasks →
      ProgramValid vocabulary task.maxDepth program

/- A bounded validator is required to establish this predicate; the theorem
   below records the fail-closed shape without pretending to implement the
   external candidate. -/
def CheckedOutputs (tasks : List PublicTask) (outputs : List Program) : Prop :=
  outputs.length = tasks.length ∧
    ∀ program task, (program, task) ∈ outputs.zip tasks →
      program.length ≤ task.maxDepth

theorem checkedOutputs_length (tasks : List PublicTask) (outputs : List Program)
    (h : CheckedOutputs tasks outputs) : outputs.length = tasks.length := by
  exact h.1

structure FamilyScore where
  correctScaled : Nat
  scale : Nat
  bounded : correctScaled ≤ scale
deriving DecidableEq, Repr

def familyScoresNumerator (scores : List FamilyScore) : Nat :=
  (scores.map FamilyScore.correctScaled).sum

def familyCount (scores : List FamilyScore) : Nat := scores.length

def familyScoresDenominator (scale : Nat) (scores : List FamilyScore) : Nat :=
  scores.length * scale

theorem familyScoresDenominator_is_family_count_times_scale
    (scale : Nat) (scores : List FamilyScore) :
    familyScoresDenominator scale scores = familyCount scores * scale := by
  rfl

theorem familyCount_is_length (scores : List FamilyScore) :
    familyCount scores = scores.length := by
  rfl

theorem sum_perm {left right : List Nat} (permutation : left.Perm right) :
    left.sum = right.sum := by
  induction permutation with
  | nil => rfl
  | cons value _ ih => simp [ih]
  | swap left right tail => simp [Nat.add_left_comm]
  | trans first second ihFirst ihSecond => exact ihFirst.trans ihSecond

theorem familyScoresNumerator_perm {left right : List FamilyScore}
    (permutation : left.Perm right) :
    familyScoresNumerator left = familyScoresNumerator right := by
  apply sum_perm
  exact permutation.map FamilyScore.correctScaled

structure ProofReceipt where
  protocolIdentity : String
  candidateDigest : Digest
  benchmarkDigest : Digest
  verifierDigest : Digest
  formalSourceDigest : Digest
  machineChecked : Bool
  independentReview : Bool
deriving DecidableEq, Repr

def scopedMachineChecked (receipt : ProofReceipt) : Prop :=
  receipt.machineChecked = true ∧
    receipt.protocolIdentity = "weco-symbolic-discovery-transfer-formal-v1"

def externallyReviewable (receipt : ProofReceipt) : Prop :=
  scopedMachineChecked receipt ∧ receipt.independentReview = true

theorem externallyReviewable_requires_machine_check (receipt : ProofReceipt)
    (h : externallyReviewable receipt) : receipt.machineChecked = true := by
  exact h.1.1

theorem externalReview_is_not_implicit (receipt : ProofReceipt)
    (h : scopedMachineChecked receipt) :
    externallyReviewable receipt ↔ receipt.independentReview = true := by
  constructor
  · intro reviewed
    exact reviewed.2
  · intro reviewed
    exact ⟨h, reviewed⟩

def claimCeiling : String :=
  "LocalMachineCheckedFormalContractOnly"

theorem claimCeiling_does_not_assert_scientific_validity :
    claimCeiling = "LocalMachineCheckedFormalContractOnly" := by
  rfl

end MathDiscovery
