/-! Slice: neuron-gate-formal-v1. Models (a) the per-layer quota arithmetic and top-|score|
selection of `select_per_layer` (v50.py) and (b) the finite combinatorial core of the
permutation p-value (ranks of distinct pooled values are exactly 1..n+1).
Harness/statistics logic only; nothing about the empirical finding.
Ceiling: LocalMachineCheckedFormalContractOnly. -/

/-! ## Quota arithmetic -/

def quota (base extra i : Nat) : Nat := base + (if i < extra then 1 else 0)

theorem sum_ind (extra : Nat) : ∀ n,
    ((List.range n).map (fun i => if i < extra then 1 else 0)).sum = min extra n := by
  intro n
  induction n with
  | zero => simp
  | succ n ih =>
    rw [List.range_succ, List.map_append, List.sum_append, ih]
    by_cases h : n < extra <;> simp [h] <;> omega

/-- quotas over `L` layers sum to `k = L*base + extra` whenever `extra ≤ L`. -/
theorem quota_sum (L base extra : Nat) (h : extra ≤ L) :
    ((List.range L).map (quota base extra)).sum = L * base + extra := by
  have key : ∀ n, ((List.range n).map (quota base extra)).sum =
      n * base + ((List.range n).map (fun i => if i < extra then 1 else 0)).sum := by
    intro n
    induction n with
    | zero => simp
    | succ n ih =>
      rw [List.range_succ, List.map_append, List.sum_append, ih,
          List.map_append, List.sum_append]
      simp [quota, Nat.succ_mul]; try omega
  rw [key L, sum_ind extra L]; omega

/-- quotas differ by at most one across layers. -/
theorem quota_spread (base extra i j : Nat) : quota base extra i ≤ quota base extra j + 1 := by
  unfold quota; split <;> split <;> omega

/-! ## Top-|score| selection (deterministic tie-break by id) -/

abbrev Unit' := Nat × Int

def keyLe (a b : Unit') : Bool :=
  decide (a.2.natAbs > b.2.natAbs ∨ (a.2.natAbs = b.2.natAbs ∧ a.1 ≤ b.1))

theorem keyLe_trans : ∀ a b c : Unit', keyLe a b = true → keyLe b c = true → keyLe a c = true := by
  intro a b c hab hbc
  simp only [keyLe, decide_eq_true_eq] at *
  omega

theorem keyLe_total : ∀ a b : Unit', (keyLe a b || keyLe b a) = true := by
  intro a b
  simp only [keyLe, Bool.or_eq_true, decide_eq_true_eq]
  omega

def sorted (us : List Unit') : List Unit' := us.mergeSort keyLe
def selectTop (q : Nat) (us : List Unit') : List Unit' := (sorted us).take q

theorem selectTop_length (q : Nat) (us : List Unit') :
    (selectTop q us).length = min q us.length := by
  unfold selectTop sorted
  rw [List.length_take, List.length_mergeSort]

theorem selectTop_subset (q : Nat) (us : List Unit') : ∀ x ∈ selectTop q us, x ∈ us := by
  intro x hx
  unfold selectTop sorted at hx
  exact (List.mergeSort_perm us keyLe).subset (List.mem_of_mem_take hx)

/-- every selected unit is at least as strong (in the strict total order) as every unselected one -/
theorem selectTop_optimal (q : Nat) (us : List Unit') :
    ∀ s ∈ selectTop q us, ∀ u ∈ (sorted us).drop q, keyLe s u = true := by
  intro s hs u hu
  have hsorted : (sorted us).Pairwise (fun a b => keyLe a b = true) :=
    List.pairwise_mergeSort keyLe_trans keyLe_total us
  have := List.take_append_drop q (sorted us)
  rw [← this] at hsorted
  exact (List.pairwise_append.mp hsorted).2.2 s hs u hu

/-- selection is a pure function of the scores: the same input gives the same output. -/
theorem selectTop_deterministic (q : Nat) (us vs : List Unit') (h : us = vs) :
    selectTop q us = selectTop q vs := by subst h; rfl

/-! ## Rank uniformity (finite core of permutation-test validity) -/

def gt (x : Int) (xs : List Int) : Nat := (xs.filter (fun y => decide (y > x))).length

def phi (r g : Nat) : Nat := if g ≥ r then g + 1 else g

theorem range_phi (r n : Nat) (h : r ≤ n) :
    (r :: (List.range n).map (phi r)).Perm (List.range (n + 1)) := by
  induction n with
  | zero =>
    have : r = 0 := by omega
    subst this; simp
  | succ n ih =>
    by_cases hr : r ≤ n
    · have h1 := ih hr
      have h2 : (List.range (n + 1 + 1)) = List.range (n + 1) ++ [n + 1] := List.range_succ
      have h3 : (List.range (n + 1)).map (phi r) = (List.range n).map (phi r) ++ [phi r n] := by
        rw [List.range_succ, List.map_append]; rfl
      have hp : phi r n = n + 1 := by unfold phi; simp [hr]
      rw [h3, hp, h2]
      have : (r :: ((List.range n).map (phi r) ++ [n + 1])).Perm
          (r :: (List.range n).map (phi r) ++ [n + 1]) := by simp
      exact this.trans (h1.append_right [n + 1])
    · have hrn : r = n + 1 := by omega
      subst hrn
      have h3 : (List.range (n + 1)).map (phi (n + 1)) = List.range (n + 1) := by
        rw [List.map_congr_left (g := id)]
        · simp
        · intro g hg
          have := List.mem_range.mp hg
          unfold phi; simp; omega
      have h2 : List.range (n + 1 + 1) = List.range (n + 1) ++ [n + 1] := List.range_succ
      rw [h3, h2]
      exact (List.perm_append_singleton (n + 1) (List.range (n + 1))).symm

theorem gt_cons (x h : Int) (t : List Int) : gt x (h :: t) = gt x t + (if h > x then 1 else 0) := by
  unfold gt; rw [List.filter_cons]; by_cases c : h > x <;> simp [c]

theorem gt_nil (x : Int) : gt x [] = 0 := by simp [gt]

theorem gt_mono (y a : Int) (hy : y < a) : ∀ t : List Int, gt a t ≤ gt y t := by
  intro t; induction t with
  | nil => simp [gt_nil]
  | cons h t ih => rw [gt_cons, gt_cons]; split <;> split <;> omega

theorem gt_strict (y a : Int) (hy : a < y) : ∀ t : List Int, y ∈ t → gt y t + 1 ≤ gt a t := by
  intro t; induction t with
  | nil => intro h; simp at h
  | cons h t ih =>
    intro hm
    rw [gt_cons, gt_cons]
    have hmono := gt_mono a y hy t
    rcases List.mem_cons.mp hm with e | hm'
    · subst e; split <;> (try split) <;> omega
    · have := ih hm'; split <;> (try split) <;> omega

/-- Main rank lemma: for pairwise-distinct values, the "number strictly greater" statistic
over the pool is a permutation of 0..n-1. -/
theorem gt_perm (xs : List Int) (hn : xs.Nodup) : (xs.map (fun x => gt x xs)).Perm (List.range xs.length) := by
  induction xs with
  | nil => simp
  | cons a t ih =>
    have hat : a ∉ t := (List.nodup_cons.mp hn).1
    have ht : t.Nodup := (List.nodup_cons.mp hn).2
    have ih' := ih ht
    obtain ⟨r, hr⟩ : ∃ r, r = gt a t := ⟨_, rfl⟩
    have hrle : r ≤ t.length := by rw [hr]; exact List.length_filter_le _ _
    have hy : ∀ y ∈ t, gt y (a :: t) = phi r (gt y t) := by
      intro y hy
      have hya : y ≠ a := fun h => hat (h ▸ hy)
      rw [gt_cons]
      unfold phi
      rcases Int.lt_or_gt_of_ne hya with hlt | hgt
      · have := gt_mono y a hlt t
        have h1 : a > y := hlt
        simp [h1]; omega
      · have := gt_strict y a hgt t hy
        have h1 : ¬ a > y := by omega
        simp [h1]; omega
    have hnew : gt a (a :: t) = r := by
      rw [gt_cons, hr]; simp
    have hmap : ((a :: t).map (fun x => gt x (a :: t))) = r :: t.map (fun y => phi r (gt y t)) := by
      simp only [List.map_cons, hnew]
      congr 1
      exact List.map_congr_left hy
    rw [hmap, List.length_cons]
    have : (t.map (fun y => phi r (gt y t))) = (t.map (fun y => gt y t)).map (phi r) := by
      rw [List.map_map]; rfl
    rw [this]
    refine List.Perm.trans ?_ (range_phi r t.length hrle)
    exact List.Perm.cons r (ih'.map (phi r))

/-- Exact uniformity: among n pooled distinct values, exactly min j n have p-numerator
(1 + #greater) at most j.  So if the "selected" role is exchangeable among the pool,
P(p ≤ j/n) = j/n exactly (no ties) -- the finite core of permutation-test validity. -/
theorem p_uniform (xs : List Int) (hn : xs.Nodup) (j : Nat) :
    (xs.filter (fun x => decide (gt x xs + 1 ≤ j))).length = min j xs.length := by
  have hp := gt_perm xs hn
  have h1 : (xs.filter (fun x => decide (gt x xs + 1 ≤ j))).length
      = (xs.map (fun x => gt x xs)).countP (fun g => decide (g + 1 ≤ j)) := by
    rw [List.countP_map, List.countP_eq_length_filter]; rfl
  rw [h1, hp.countP_eq]
  clear h1 hp
  generalize xs.length = n
  induction n with
  | zero => simp
  | succ n ih =>
    rw [List.range_succ, List.countP_append, ih]
    by_cases h : n + 1 ≤ j <;> simp [h] <;> omega
