import Std

namespace HsaiGatewayDigest

abbrev Digest32 := List UInt8
abbrev ArtifactDigest := String × Digest32
abbrev GatewayActionKind := Fin 7
abbrev GatewayModelLaneKind := Fin 5
abbrev GatewayThreatLabel := Fin 14

instance : Ord ArtifactDigest := lexOrd

structure ModelLaneProvenance where
  laneKind : GatewayModelLaneKind
  modelFamily : String
  artifactId : String
  runtime : String
  promptTemplateDigest : Digest32
  inputCorpusDigest : Digest32
  outputBundleDigest : Digest32
  nonSecret : Bool
deriving DecidableEq

structure GatewayActionProposalV1 where
  id : String
  subject : String
  actionKind : GatewayActionKind
  target : String
  valueUnits : Nat
  sourceArtifactDigests : List ArtifactDigest
  nonclaims : List String
  modelLane : ModelLaneProvenance
  threatLabels : List GatewayThreatLabel
  directAuthorityRequested : Bool
  signerOrToolRequestedBeforeAdmission : Bool
deriving DecidableEq

inductive EncodeError where
  | duplicateSourceArtifact
  | duplicateNonclaim
  | duplicateThreatLabel
deriving DecidableEq, Repr

def digestTag : String :=
  "hsai-agent-admission:gateway-action-proposal:v1"

def GatewayActionProposalV1.withSets
    (base : GatewayActionProposalV1)
    (artifacts : List ArtifactDigest)
    (nonclaims : List String)
    (threats : List GatewayThreatLabel) : GatewayActionProposalV1 :=
  { base with
    sourceArtifactDigests := artifacts
    nonclaims := nonclaims
    threatLabels := threats }

def canonicalize [Ord α] (values : List α) : List α :=
  values.mergeSort fun left right => (compare left right).isLE

def actionKindLabel (kind : GatewayActionKind) : String :=
  match kind.val with
  | 0 => "Payment"
  | 1 => "Trade"
  | 2 => "ToolCall"
  | 3 => "DataAccess"
  | 4 => "ComputeRental"
  | 5 => "Deployment"
  | _ => "Checkout"

def modelLaneKindLabel (kind : GatewayModelLaneKind) : String :=
  match kind.val with
  | 0 => "Deterministic"
  | 1 => "LocalOpenWeight"
  | 2 => "RentedOpenWeight"
  | 3 => "HostedSmall"
  | _ => "PremiumEscalation"

def threatLabel (threat : GatewayThreatLabel) : String :=
  match threat.val with
  | 0 => "Benign"
  | 1 => "PromptInjectionPayment"
  | 2 => "WrongCounterparty"
  | 3 => "AmountLimitBypass"
  | 4 => "SourceDigestDrift"
  | 5 => "StaleApprovalReplay"
  | 6 => "DuplicateJsonKeyPayload"
  | 7 => "PolicyDowngrade"
  | 8 => "DirectAuthorityRequest"
  | 9 => "ForgedAcceptedDecision"
  | 10 => "MissingNonclaim"
  | 11 => "MissingSourceDigest"
  | 12 => "StaleJournalTip"
  | _ => "SignerBeforeAdmission"

private def hexDigit (value : Nat) : Char :=
  if value < 10 then
    Char.ofNat ('0'.toNat + value)
  else
    Char.ofNat ('a'.toNat + value - 10)

private def jsonEscapeChar (value : Char) : String :=
  if value = '"' then
    "\\\""
  else if value = '\\' then
    "\\\\"
  else if value.toNat = 0x08 then
    "\\b"
  else if value = '\t' then
    "\\t"
  else if value = '\n' then
    "\\n"
  else if value.toNat = 0x0c then
    "\\f"
  else if value = '\r' then
    "\\r"
  else if value.toNat < 0x20 then
    "\\u00" ++
      String.singleton (hexDigit (value.toNat / 16)) ++
      String.singleton (hexDigit (value.toNat % 16))
  else
    String.singleton value

def jsonString (value : String) : String :=
  "\"" ++ String.join (value.toList.map jsonEscapeChar) ++ "\""

private def jsonArray (values : List String) : String :=
  "[" ++ String.intercalate "," values ++ "]"

private def jsonField (name value : String) : String :=
  jsonString name ++ ":" ++ value

private def jsonBool (value : Bool) : String :=
  if value then "true" else "false"

private def jsonDigest (value : Digest32) : String :=
  jsonArray (value.map fun byte => toString byte.toNat)

private def jsonArtifact (value : ArtifactDigest) : String :=
  "{" ++
    jsonField "id" (jsonString value.1) ++ "," ++
    jsonField "sha256" (jsonDigest value.2) ++
  "}"

private def jsonModelLane (value : ModelLaneProvenance) : String :=
  "{" ++
    jsonField "lane_kind" (jsonString (modelLaneKindLabel value.laneKind)) ++ "," ++
    jsonField "model_family" (jsonString value.modelFamily) ++ "," ++
    jsonField "artifact_id" (jsonString value.artifactId) ++ "," ++
    jsonField "runtime" (jsonString value.runtime) ++ "," ++
    jsonField "prompt_template_digest" (jsonDigest value.promptTemplateDigest) ++ "," ++
    jsonField "input_corpus_digest" (jsonDigest value.inputCorpusDigest) ++ "," ++
    jsonField "output_bundle_digest" (jsonDigest value.outputBundleDigest) ++ "," ++
    jsonField "non_secret" (jsonBool value.nonSecret) ++
  "}"

def renderGatewayActionProposalV1 (proposal : GatewayActionProposalV1) : String :=
  "[" ++ jsonString digestTag ++ ",{" ++
    jsonField "id" (jsonString proposal.id) ++ "," ++
    jsonField "subject" (jsonString proposal.subject) ++ "," ++
    jsonField "action_kind" (jsonString (actionKindLabel proposal.actionKind)) ++ "," ++
    jsonField "target" (jsonString proposal.target) ++ "," ++
    jsonField "value_units" (toString proposal.valueUnits) ++ "," ++
    jsonField "source_artifact_digests"
      (jsonArray (proposal.sourceArtifactDigests.map jsonArtifact)) ++ "," ++
    jsonField "nonclaims" (jsonArray (proposal.nonclaims.map jsonString)) ++ "," ++
    jsonField "model_lane" (jsonModelLane proposal.modelLane) ++ "," ++
    jsonField "threat_labels" (jsonArray (proposal.threatLabels.map (jsonString ∘ threatLabel))) ++ "," ++
    jsonField "direct_authority_requested" (jsonBool proposal.directAuthorityRequested) ++ "," ++
    jsonField "signer_or_tool_requested_before_admission"
      (jsonBool proposal.signerOrToolRequestedBeforeAdmission) ++
  "}]"

def encodeGatewayActionProposalV1
    (proposal : GatewayActionProposalV1) : Except EncodeError ByteArray :=
  if proposal.sourceArtifactDigests.Nodup then
    if proposal.nonclaims.Nodup then
      if proposal.threatLabels.Nodup then
        let canonical := proposal.withSets
          (canonicalize proposal.sourceArtifactDigests)
          (canonicalize proposal.nonclaims)
          (canonicalize proposal.threatLabels)
        .ok (renderGatewayActionProposalV1 canonical).toUTF8
      else
        .error .duplicateThreatLabel
    else
      .error .duplicateNonclaim
  else
    .error .duplicateSourceArtifact

end HsaiGatewayDigest
