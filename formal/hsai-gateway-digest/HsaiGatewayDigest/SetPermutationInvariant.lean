import HsaiGatewayDigest.Model

namespace HsaiGatewayDigest

private theorem canonicalizeEqOfPerm
    {α : Type} [Ord α] [Std.TransOrd α] [Std.LawfulEqOrd α]
    {left right : List α}
    (permutation : left.Perm right) :
    canonicalize left = canonicalize right := by
  apply List.Perm.eq_of_pairwise
  · intro a b _ _ hab hba
    apply Std.LawfulEqOrd.eq_of_compare
    exact Std.OrientedCmp.isLE_antisymm hab hba
  · simpa [canonicalize] using
      List.pairwise_mergeSort
        (le := fun a b : α => (compare a b).isLE)
        (l := left)
        (fun _ _ _ hab hbc => Std.TransOrd.isLE_trans hab hbc)
        (fun a b => by
          cases h : compare a b with
          | lt => simp [h]
          | eq => simp [h]
          | gt =>
              have hba := Std.OrientedCmp.lt_of_gt h
              simp [h, hba])
  · simpa [canonicalize] using
      List.pairwise_mergeSort
        (le := fun a b : α => (compare a b).isLE)
        (l := right)
        (fun _ _ _ hab hbc => Std.TransOrd.isLE_trans hab hbc)
        (fun a b => by
          cases h : compare a b with
          | lt => simp [h]
          | eq => simp [h]
          | gt =>
              have hba := Std.OrientedCmp.lt_of_gt h
              simp [h, hba])
  · simpa [canonicalize] using
      (List.mergeSort_perm left (fun a b : α => (compare a b).isLE)).trans
        (permutation.trans
          (List.mergeSort_perm right (fun a b : α => (compare a b).isLE)).symm)

-- THEOREM_STATEMENT_BEGIN
theorem gatewayProposalV1SetPermutationInvariant
    (base : GatewayActionProposalV1)
    (artifacts1 artifacts2 : List ArtifactDigest)
    (nonclaims1 nonclaims2 : List String)
    (threats1 threats2 : List GatewayThreatLabel)
    (artifactsPerm : artifacts1.Perm artifacts2)
    (nonclaimsPerm : nonclaims1.Perm nonclaims2)
    (threatsPerm : threats1.Perm threats2)
    (artifactsNodup : artifacts1.Nodup)
    (nonclaimsNodup : nonclaims1.Nodup)
    (threatsNodup : threats1.Nodup) :
    ∃ bytes,
      encodeGatewayActionProposalV1
          (base.withSets artifacts1 nonclaims1 threats1) = .ok bytes ∧
      encodeGatewayActionProposalV1
          (base.withSets artifacts2 nonclaims2 threats2) = .ok bytes := by
  -- THEOREM_STATEMENT_END
  have artifacts2Nodup := artifactsPerm.nodup artifactsNodup
  have nonclaims2Nodup := nonclaimsPerm.nodup nonclaimsNodup
  have threats2Nodup := threatsPerm.nodup threatsNodup
  have artifactsCanonical := canonicalizeEqOfPerm artifactsPerm
  have nonclaimsCanonical := canonicalizeEqOfPerm nonclaimsPerm
  have threatsCanonical := canonicalizeEqOfPerm threatsPerm
  let bytes :=
    (renderGatewayActionProposalV1
      (base.withSets
        (canonicalize artifacts1)
        (canonicalize nonclaims1)
        (canonicalize threats1))).toUTF8
  refine ⟨bytes, ?_, ?_⟩
  · simp [encodeGatewayActionProposalV1, GatewayActionProposalV1.withSets,
      artifactsNodup, nonclaimsNodup, threatsNodup, bytes]
  · simp [encodeGatewayActionProposalV1, GatewayActionProposalV1.withSets,
      artifacts2Nodup, nonclaims2Nodup, threats2Nodup,
      artifactsCanonical, nonclaimsCanonical, threatsCanonical, bytes]

end HsaiGatewayDigest
