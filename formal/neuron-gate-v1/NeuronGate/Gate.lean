/-! Slice: neuron-gate-formal-v1. Models the harness decision rule
`_supported` (v60.py) and `one_sided_p` (v49.py) over Int (fixed-point effects).
Machine-checks harness logic only; proves nothing about the empirical finding.
Claim ceiling: LocalMachineCheckedFormalContractOnly. -/
structure Eff where
  sing : Int
  plur : Int
  all  : Int

def supported (sel cm : Eff) (floor : Int) : Prop :=
  sel.sing > cm.sing ∧ sel.plur > cm.plur ∧ sel.all ≥ floor

instance (sel cm : Eff) (f : Int) : Decidable (supported sel cm f) := by
  unfold supported; infer_instance

/-- count of controls at least as large as the effect -/
def geCount (e : Int) (cs : List Int) : Nat := (cs.filter (fun c => c ≥ e)).length

/-- p = (1 + geCount) / (1 + n), kept as numerator/denominator -/
def pNum (e : Int) (cs : List Int) : Nat := 1 + geCount e cs
def pDen (cs : List Int) : Nat := 1 + cs.length

theorem supported_gt_sing {sel cm : Eff} {f : Int} (h : supported sel cm f) : sel.sing > cm.sing := h.1
theorem supported_gt_plur {sel cm : Eff} {f : Int} (h : supported sel cm f) : sel.plur > cm.plur := h.2.1
theorem supported_floor {sel cm : Eff} {f : Int} (h : supported sel cm f) : sel.all ≥ f := h.2.2

/-- equality with a control maximum never counts as support (strictness). -/
theorem not_supported_of_eq_sing {sel cm : Eff} {f : Int} (h : sel.sing = cm.sing) : ¬ supported sel cm f := by
  intro hs; have := hs.1; omega

/-- raising the floor can only remove support. -/
theorem supported_mono_floor {sel cm : Eff} {f g : Int} (hfg : f ≤ g) (h : supported sel cm g) : supported sel cm f :=
  ⟨h.1, h.2.1, Int.le_trans hfg h.2.2⟩

theorem pNum_pos (e : Int) (cs : List Int) : 0 < pNum e cs := by unfold pNum; omega
theorem pDen_pos (cs : List Int) : 0 < pDen cs := by unfold pDen; omega

theorem geCount_le (e : Int) (cs : List Int) : geCount e cs ≤ cs.length := by
  unfold geCount; exact List.length_filter_le _ _

/-- p ≤ 1: numerator never exceeds denominator. -/
theorem p_le_one (e : Int) (cs : List Int) : pNum e cs ≤ pDen cs := by
  unfold pNum pDen; have := geCount_le e cs; omega

/-- permutation-p floor: if the effect strictly exceeds every control, p = 1/(1+n). -/
theorem p_floor (e : Int) (cs : List Int) (h : ∀ c ∈ cs, c < e) : pNum e cs = 1 := by
  unfold pNum geCount
  have : cs.filter (fun c => c ≥ e) = [] := by
    apply List.filter_eq_nil_iff.mpr
    intro c hc; have := h c hc; simp; omega
  rw [this]; rfl

/-- with 100 controls, the smallest attainable p is 1/101 (denominator fixed). -/
theorem p_floor_100 (e : Int) (cs : List Int) (hl : cs.length = 100) : pDen cs = 101 := by
  unfold pDen; omega

/-- sel beating the control max implies p numerator is 1 (ties with max break it). -/
theorem supported_all_p_floor {e : Int} {cs : List Int} {m : Int}
    (hm : ∀ c ∈ cs, c ≤ m) (he : e > m) : pNum e cs = 1 :=
  p_floor e cs (fun c hc => Int.lt_of_le_of_lt (hm c hc) he)
