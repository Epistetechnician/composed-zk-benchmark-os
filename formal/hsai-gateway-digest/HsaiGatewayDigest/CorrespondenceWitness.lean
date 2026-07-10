import HsaiGatewayDigest.Model

namespace HsaiGatewayDigest

private def phase665GoldenFixtureRaw : String :=
  include_str ".." / "fixtures" / "phase660-golden-preimage.json"

private def phase665OrderingFixtureRaw : String :=
  include_str ".." / "fixtures" / "phase662-ordering-preimage.json"

private noncomputable def fixtureBytes (value : String) : ByteArray :=
  value.toList.dropLast.utf8Encode

private theorem fixtureBytes_append_terminalLf (value : String) :
    fixtureBytes (value ++ "\n") = value.toUTF8 := by
  simp [fixtureBytes]

private def repeatedDigest (value : UInt8) : Digest32 :=
  List.replicate 32 value

private def phase665BaseProposal : GatewayActionProposalV1 :=
  {
    id := "phase660-action"
    subject := "agent-phase660"
    actionKind := ⟨0, by decide⟩
    target := "treasury-safe"
    valueUnits := 50
    sourceArtifactDigests := []
    nonclaims := []
    modelLane := {
      laneKind := ⟨0, by decide⟩
      modelFamily := "model-a"
      artifactId := "artifact-a"
      runtime := "runtime-a"
      promptTemplateDigest := repeatedDigest 1
      inputCorpusDigest := repeatedDigest 2
      outputBundleDigest := repeatedDigest 3
      nonSecret := true
    }
    threatLabels := []
    directAuthorityRequested := false
    signerOrToolRequestedBeforeAdmission := false
  }

private def phase665ArtifactA : ArtifactDigest :=
  ("a-artifact", repeatedDigest 8)

private def phase665ArtifactZ : ArtifactDigest :=
  ("z-artifact", repeatedDigest 9)

private def phase665Benign : GatewayThreatLabel :=
  ⟨0, by decide⟩

private def phase665StaleApprovalReplay : GatewayThreatLabel :=
  ⟨5, by decide⟩

private def phase665ReverseOrderProposal : GatewayActionProposalV1 :=
  phase665BaseProposal.withSets
    [phase665ArtifactZ, phase665ArtifactA]
    ["z-nonclaim", "a-nonclaim"]
    [phase665StaleApprovalReplay, phase665Benign]

private def phase665CanonicalOrderProposal : GatewayActionProposalV1 :=
  phase665BaseProposal.withSets
    [phase665ArtifactA, phase665ArtifactZ]
    ["a-nonclaim", "z-nonclaim"]
    [phase665Benign, phase665StaleApprovalReplay]

private theorem encode_eq_ok_of_nodup
    (proposal : GatewayActionProposalV1)
    (artifactsNodup : proposal.sourceArtifactDigests.Nodup)
    (nonclaimsNodup : proposal.nonclaims.Nodup)
    (threatsNodup : proposal.threatLabels.Nodup) :
    encodeGatewayActionProposalV1 proposal =
      .ok (renderGatewayActionProposalV1
        (proposal.withSets
          (canonicalize proposal.sourceArtifactDigests)
          (canonicalize proposal.nonclaims)
          (canonicalize proposal.threatLabels))).toUTF8 := by
  simp [encodeGatewayActionProposalV1, artifactsNodup, nonclaimsNodup, threatsNodup]

private theorem canonicalize_eq_of_perm
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

set_option maxRecDepth 100000 in
set_option maxHeartbeats 2000000 in
-- THEOREM_STATEMENT_BEGIN
theorem phase665ModelCheckerPreimageWitnesses :
    encodeGatewayActionProposalV1 phase665BaseProposal =
      .ok (fixtureBytes phase665GoldenFixtureRaw) ∧
    encodeGatewayActionProposalV1 phase665ReverseOrderProposal =
      .ok (fixtureBytes phase665OrderingFixtureRaw) ∧
    encodeGatewayActionProposalV1 phase665CanonicalOrderProposal =
      .ok (fixtureBytes phase665OrderingFixtureRaw) := by
  -- THEOREM_STATEMENT_END
  have goldenText :
      renderGatewayActionProposalV1 phase665BaseProposal ++ "\n" =
        phase665GoldenFixtureRaw := by
    decide
  have orderingText :
      renderGatewayActionProposalV1 phase665CanonicalOrderProposal ++ "\n" =
        phase665OrderingFixtureRaw := by
    decide
  have goldenBytes :
      fixtureBytes phase665GoldenFixtureRaw =
        (renderGatewayActionProposalV1 phase665BaseProposal).toUTF8 := by
    rw [← goldenText]
    exact fixtureBytes_append_terminalLf _
  have orderingBytes :
      fixtureBytes phase665OrderingFixtureRaw =
        (renderGatewayActionProposalV1 phase665CanonicalOrderProposal).toUTF8 := by
    rw [← orderingText]
    exact fixtureBytes_append_terminalLf _
  have canonicalArtifacts :
      canonicalize [phase665ArtifactA, phase665ArtifactZ] =
        [phase665ArtifactA, phase665ArtifactZ] := by
    unfold canonicalize
    apply List.mergeSort_of_pairwise
    decide +kernel
  have canonicalNonclaims :
      canonicalize ["a-nonclaim", "z-nonclaim"] =
        ["a-nonclaim", "z-nonclaim"] := by
    unfold canonicalize
    apply List.mergeSort_of_pairwise
    decide +kernel
  have canonicalThreats :
      canonicalize [phase665Benign, phase665StaleApprovalReplay] =
        [phase665Benign, phase665StaleApprovalReplay] := by
    unfold canonicalize
    apply List.mergeSort_of_pairwise
    decide +kernel
  have reverseArtifacts :
      canonicalize [phase665ArtifactZ, phase665ArtifactA] =
        [phase665ArtifactA, phase665ArtifactZ] :=
    (canonicalize_eq_of_perm
      (List.Perm.swap phase665ArtifactA phase665ArtifactZ [])).trans canonicalArtifacts
  have reverseNonclaims :
      canonicalize ["z-nonclaim", "a-nonclaim"] =
        ["a-nonclaim", "z-nonclaim"] :=
    (canonicalize_eq_of_perm
      (List.Perm.swap "a-nonclaim" "z-nonclaim" [])).trans canonicalNonclaims
  have reverseThreats :
      canonicalize [phase665StaleApprovalReplay, phase665Benign] =
        [phase665Benign, phase665StaleApprovalReplay] :=
    (canonicalize_eq_of_perm
      (List.Perm.swap phase665Benign phase665StaleApprovalReplay [])).trans canonicalThreats
  have baseNormalized :
      phase665BaseProposal.withSets
          (canonicalize phase665BaseProposal.sourceArtifactDigests)
          (canonicalize phase665BaseProposal.nonclaims)
          (canonicalize phase665BaseProposal.threatLabels) =
        phase665BaseProposal := by
    change phase665BaseProposal.withSets
      (canonicalize []) (canonicalize []) (canonicalize []) = phase665BaseProposal
    simp [canonicalize, GatewayActionProposalV1.withSets, phase665BaseProposal]
  have reverseNormalized :
      phase665ReverseOrderProposal.withSets
          (canonicalize phase665ReverseOrderProposal.sourceArtifactDigests)
          (canonicalize phase665ReverseOrderProposal.nonclaims)
          (canonicalize phase665ReverseOrderProposal.threatLabels) =
        phase665CanonicalOrderProposal := by
    change phase665BaseProposal.withSets
      (canonicalize [phase665ArtifactZ, phase665ArtifactA])
      (canonicalize ["z-nonclaim", "a-nonclaim"])
      (canonicalize [phase665StaleApprovalReplay, phase665Benign]) =
        phase665BaseProposal.withSets
          [phase665ArtifactA, phase665ArtifactZ]
          ["a-nonclaim", "z-nonclaim"]
          [phase665Benign, phase665StaleApprovalReplay]
    rw [reverseArtifacts, reverseNonclaims, reverseThreats]
  have canonicalNormalized :
      phase665CanonicalOrderProposal.withSets
          (canonicalize phase665CanonicalOrderProposal.sourceArtifactDigests)
          (canonicalize phase665CanonicalOrderProposal.nonclaims)
          (canonicalize phase665CanonicalOrderProposal.threatLabels) =
        phase665CanonicalOrderProposal := by
    change phase665BaseProposal.withSets
      (canonicalize [phase665ArtifactA, phase665ArtifactZ])
      (canonicalize ["a-nonclaim", "z-nonclaim"])
      (canonicalize [phase665Benign, phase665StaleApprovalReplay]) =
        phase665BaseProposal.withSets
          [phase665ArtifactA, phase665ArtifactZ]
          ["a-nonclaim", "z-nonclaim"]
          [phase665Benign, phase665StaleApprovalReplay]
    rw [canonicalArtifacts, canonicalNonclaims, canonicalThreats]
  have baseEncode :
      encodeGatewayActionProposalV1 phase665BaseProposal =
        .ok (renderGatewayActionProposalV1 phase665BaseProposal).toUTF8 := by
    rw [encode_eq_ok_of_nodup phase665BaseProposal
      (by decide) (by decide) (by decide), baseNormalized]
  have reverseEncode :
      encodeGatewayActionProposalV1 phase665ReverseOrderProposal =
        .ok (renderGatewayActionProposalV1 phase665CanonicalOrderProposal).toUTF8 := by
    rw [encode_eq_ok_of_nodup phase665ReverseOrderProposal
      (by decide) (by decide) (by decide), reverseNormalized]
  have canonicalEncode :
      encodeGatewayActionProposalV1 phase665CanonicalOrderProposal =
        .ok (renderGatewayActionProposalV1 phase665CanonicalOrderProposal).toUTF8 := by
    rw [encode_eq_ok_of_nodup phase665CanonicalOrderProposal
      (by decide) (by decide) (by decide), canonicalNormalized]
  constructor
  · rw [goldenBytes]
    exact baseEncode
  constructor
  · rw [orderingBytes]
    exact reverseEncode
  · rw [orderingBytes]
    exact canonicalEncode

end HsaiGatewayDigest
