use hsai_agent_admission::{
    gateway_action_proposal_digest_preimage, ArtifactDigest, GatewayActionId, GatewayActionKind,
    GatewayActionProposal, GatewayModelLaneKind, GatewayModelLaneProvenance, GatewayThreatLabel,
    NonClaimLabel, GATEWAY_ACTION_PROPOSAL_DIGEST_TAG,
};
use hsai_claim_envelope::{Hash, SubjectId};
use hsai_gateway_digest_checker::{
    check_gateway_action_proposal_digest_v1, checker_independence_profile,
    checker_required_nonclaims, validate_checker_digest_result, CheckerArtifactDigest,
    CheckerComparisonClassification, CheckerDigestResult, CheckerGatewayActionId,
    CheckerGatewayActionKind, CheckerGatewayActionProposal, CheckerGatewayModelLaneKind,
    CheckerGatewayThreatLabel, CheckerModelLaneProvenance, CheckerNonclaim, CheckerSubjectId,
    CHECKER_CLAIM_BOUNDARY,
};
use proptest::prelude::*;
use std::collections::BTreeSet;

const PHASE665_GOLDEN_PREIMAGE_FIXTURE: &str =
    include_str!("../../../formal/hsai-gateway-digest/fixtures/phase660-golden-preimage.json");
const PHASE665_ORDERING_PREIMAGE_FIXTURE: &str =
    include_str!("../../../formal/hsai-gateway-digest/fixtures/phase662-ordering-preimage.json");

#[derive(Clone, Copy, Debug)]
enum Mutation {
    Id,
    Subject,
    ActionKind,
    Target,
    ValueUnits,
    SourceArtifactDigests,
    Nonclaims,
    ModelLaneKind,
    ModelFamily,
    ModelArtifactId,
    ModelRuntime,
    PromptTemplateDigest,
    InputCorpusDigest,
    OutputBundleDigest,
    ModelNonSecret,
    ThreatLabels,
    DirectAuthorityRequested,
    SignerBeforeAdmission,
}

const MUTATIONS: [Mutation; 18] = [
    Mutation::Id,
    Mutation::Subject,
    Mutation::ActionKind,
    Mutation::Target,
    Mutation::ValueUnits,
    Mutation::SourceArtifactDigests,
    Mutation::Nonclaims,
    Mutation::ModelLaneKind,
    Mutation::ModelFamily,
    Mutation::ModelArtifactId,
    Mutation::ModelRuntime,
    Mutation::PromptTemplateDigest,
    Mutation::InputCorpusDigest,
    Mutation::OutputBundleDigest,
    Mutation::ModelNonSecret,
    Mutation::ThreatLabels,
    Mutation::DirectAuthorityRequested,
    Mutation::SignerBeforeAdmission,
];

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
enum ComparisonIssue {
    DigestTag,
    ProductionPreimage,
    ProductionDigest,
    IndependenceProfile,
    ClaimBoundary,
    ExplicitNonclaims,
}

fn production_fixture(mutation: Option<Mutation>) -> GatewayActionProposal {
    let mut proposal = GatewayActionProposal {
        id: GatewayActionId("phase660-action".to_owned()),
        subject: SubjectId("agent-phase660".to_owned()),
        action_kind: GatewayActionKind::Payment,
        target: "treasury-safe".to_owned(),
        value_units: 50,
        source_artifact_digests: BTreeSet::new(),
        nonclaims: BTreeSet::new(),
        model_lane: GatewayModelLaneProvenance {
            lane_kind: GatewayModelLaneKind::Deterministic,
            model_family: "model-a".to_owned(),
            artifact_id: "artifact-a".to_owned(),
            runtime: "runtime-a".to_owned(),
            prompt_template_digest: Hash([1; 32]),
            input_corpus_digest: Hash([2; 32]),
            output_bundle_digest: Hash([3; 32]),
            non_secret: true,
        },
        threat_labels: BTreeSet::new(),
        direct_authority_requested: false,
        signer_or_tool_requested_before_admission: false,
    };
    if let Some(mutation) = mutation {
        match mutation {
            Mutation::Id => proposal.id = GatewayActionId("phase662-mutated".to_owned()),
            Mutation::Subject => proposal.subject = SubjectId("agent-phase662".to_owned()),
            Mutation::ActionKind => proposal.action_kind = GatewayActionKind::Trade,
            Mutation::Target => proposal.target = "phase662-target".to_owned(),
            Mutation::ValueUnits => proposal.value_units = 51,
            Mutation::SourceArtifactDigests => {
                proposal.source_artifact_digests = BTreeSet::from([ArtifactDigest {
                    id: "phase662-artifact".to_owned(),
                    sha256: Hash([31; 32]),
                }]);
            }
            Mutation::Nonclaims => {
                proposal.nonclaims =
                    BTreeSet::from([NonClaimLabel("phase662 nonclaim".to_owned())]);
            }
            Mutation::ModelLaneKind => {
                proposal.model_lane.lane_kind = GatewayModelLaneKind::PremiumEscalation;
            }
            Mutation::ModelFamily => {
                proposal.model_lane.model_family = "phase662-family".to_owned();
            }
            Mutation::ModelArtifactId => {
                proposal.model_lane.artifact_id = "phase662-artifact-id".to_owned();
            }
            Mutation::ModelRuntime => {
                proposal.model_lane.runtime = "phase662-runtime".to_owned();
            }
            Mutation::PromptTemplateDigest => {
                proposal.model_lane.prompt_template_digest = Hash([41; 32]);
            }
            Mutation::InputCorpusDigest => {
                proposal.model_lane.input_corpus_digest = Hash([42; 32]);
            }
            Mutation::OutputBundleDigest => {
                proposal.model_lane.output_bundle_digest = Hash([43; 32]);
            }
            Mutation::ModelNonSecret => proposal.model_lane.non_secret = false,
            Mutation::ThreatLabels => {
                proposal.threat_labels = BTreeSet::from([GatewayThreatLabel::WrongCounterparty]);
            }
            Mutation::DirectAuthorityRequested => proposal.direct_authority_requested = true,
            Mutation::SignerBeforeAdmission => {
                proposal.signer_or_tool_requested_before_admission = true;
            }
        }
    }
    proposal
}

fn checker_fixture(mutation: Option<Mutation>) -> CheckerGatewayActionProposal {
    let mut proposal = CheckerGatewayActionProposal {
        id: CheckerGatewayActionId("phase660-action".to_owned()),
        subject: CheckerSubjectId("agent-phase660".to_owned()),
        action_kind: CheckerGatewayActionKind::Payment,
        target: "treasury-safe".to_owned(),
        value_units: 50,
        source_artifact_digests: Vec::new(),
        nonclaims: Vec::new(),
        model_lane: CheckerModelLaneProvenance {
            lane_kind: CheckerGatewayModelLaneKind::Deterministic,
            model_family: "model-a".to_owned(),
            artifact_id: "artifact-a".to_owned(),
            runtime: "runtime-a".to_owned(),
            prompt_template_digest: [1; 32],
            input_corpus_digest: [2; 32],
            output_bundle_digest: [3; 32],
            non_secret: true,
        },
        threat_labels: Vec::new(),
        direct_authority_requested: false,
        signer_or_tool_requested_before_admission: false,
    };
    if let Some(mutation) = mutation {
        match mutation {
            Mutation::Id => {
                proposal.id = CheckerGatewayActionId("phase662-mutated".to_owned());
            }
            Mutation::Subject => {
                proposal.subject = CheckerSubjectId("agent-phase662".to_owned());
            }
            Mutation::ActionKind => proposal.action_kind = CheckerGatewayActionKind::Trade,
            Mutation::Target => proposal.target = "phase662-target".to_owned(),
            Mutation::ValueUnits => proposal.value_units = 51,
            Mutation::SourceArtifactDigests => {
                proposal.source_artifact_digests = vec![CheckerArtifactDigest {
                    id: "phase662-artifact".to_owned(),
                    sha256: [31; 32],
                }];
            }
            Mutation::Nonclaims => {
                proposal.nonclaims = vec![CheckerNonclaim("phase662 nonclaim".to_owned())];
            }
            Mutation::ModelLaneKind => {
                proposal.model_lane.lane_kind = CheckerGatewayModelLaneKind::PremiumEscalation;
            }
            Mutation::ModelFamily => {
                proposal.model_lane.model_family = "phase662-family".to_owned();
            }
            Mutation::ModelArtifactId => {
                proposal.model_lane.artifact_id = "phase662-artifact-id".to_owned();
            }
            Mutation::ModelRuntime => {
                proposal.model_lane.runtime = "phase662-runtime".to_owned();
            }
            Mutation::PromptTemplateDigest => {
                proposal.model_lane.prompt_template_digest = [41; 32];
            }
            Mutation::InputCorpusDigest => {
                proposal.model_lane.input_corpus_digest = [42; 32];
            }
            Mutation::OutputBundleDigest => {
                proposal.model_lane.output_bundle_digest = [43; 32];
            }
            Mutation::ModelNonSecret => proposal.model_lane.non_secret = false,
            Mutation::ThreatLabels => {
                proposal.threat_labels = vec![CheckerGatewayThreatLabel::WrongCounterparty];
            }
            Mutation::DirectAuthorityRequested => proposal.direct_authority_requested = true,
            Mutation::SignerBeforeAdmission => {
                proposal.signer_or_tool_requested_before_admission = true;
            }
        }
    }
    proposal
}

fn compare(
    production: &GatewayActionProposal,
    checker: &CheckerDigestResult,
) -> (CheckerComparisonClassification, BTreeSet<ComparisonIssue>) {
    let mut issues = BTreeSet::new();
    if checker.digest_tag != GATEWAY_ACTION_PROPOSAL_DIGEST_TAG {
        issues.insert(ComparisonIssue::DigestTag);
    }
    if checker.encoded_preimage != gateway_action_proposal_digest_preimage(production) {
        issues.insert(ComparisonIssue::ProductionPreimage);
    }
    if checker.digest != production.digest().0 {
        issues.insert(ComparisonIssue::ProductionDigest);
    }
    if checker.independence_profile != checker_independence_profile() {
        issues.insert(ComparisonIssue::IndependenceProfile);
    }
    if checker.claim_boundary != CHECKER_CLAIM_BOUNDARY {
        issues.insert(ComparisonIssue::ClaimBoundary);
    }
    if checker.explicit_nonclaims != checker_required_nonclaims() {
        issues.insert(ComparisonIssue::ExplicitNonclaims);
    }
    let classification = if issues.is_empty() {
        CheckerComparisonClassification::LocalImplementationDiverseCheckerAgreement
    } else {
        CheckerComparisonClassification::LocalImplementationDiverseCheckerMismatch
    };
    (classification, issues)
}

fn assert_agreement(
    production: &GatewayActionProposal,
    checker_proposal: &CheckerGatewayActionProposal,
) -> CheckerDigestResult {
    let result = check_gateway_action_proposal_digest_v1(checker_proposal)
        .expect("phase662 checker execution succeeds");
    assert!(
        validate_checker_digest_result(checker_proposal, &result)
            .expect("phase662 checker result validates")
            .valid
    );
    assert_eq!(
        compare(production, &result),
        (
            CheckerComparisonClassification::LocalImplementationDiverseCheckerAgreement,
            BTreeSet::new()
        )
    );
    result
}

fn hash_from_hex(value: &str) -> [u8; 32] {
    assert_eq!(value.len(), 64);
    let mut out = [0; 32];
    for (index, byte) in out.iter_mut().enumerate() {
        let start = index * 2;
        *byte =
            u8::from_str_radix(&value[start..start + 2], 16).expect("phase662 digest hex parses");
    }
    out
}

fn phase665_fixture_bytes(value: &'static str, fixture_name: &str) -> &'static [u8] {
    let bytes = value.as_bytes();
    assert_eq!(
        bytes.last(),
        Some(&b'\n'),
        "{fixture_name} must end in exactly one LF"
    );
    assert_ne!(
        bytes.get(bytes.len().saturating_sub(2)),
        Some(&b'\n'),
        "{fixture_name} must end in exactly one LF"
    );
    &bytes[..bytes.len() - 1]
}

fn arbitrary_string() -> impl Strategy<Value = String> {
    proptest::collection::vec(any::<char>(), 0..24)
        .prop_map(|characters| characters.into_iter().collect())
}

fn production_action_kind(index: u8) -> GatewayActionKind {
    match index {
        0 => GatewayActionKind::Payment,
        1 => GatewayActionKind::Trade,
        2 => GatewayActionKind::ToolCall,
        3 => GatewayActionKind::DataAccess,
        4 => GatewayActionKind::ComputeRental,
        5 => GatewayActionKind::Deployment,
        _ => GatewayActionKind::Checkout,
    }
}

fn checker_action_kind(index: u8) -> CheckerGatewayActionKind {
    match index {
        0 => CheckerGatewayActionKind::Payment,
        1 => CheckerGatewayActionKind::Trade,
        2 => CheckerGatewayActionKind::ToolCall,
        3 => CheckerGatewayActionKind::DataAccess,
        4 => CheckerGatewayActionKind::ComputeRental,
        5 => CheckerGatewayActionKind::Deployment,
        _ => CheckerGatewayActionKind::Checkout,
    }
}

fn production_lane_kind(index: u8) -> GatewayModelLaneKind {
    match index {
        0 => GatewayModelLaneKind::Deterministic,
        1 => GatewayModelLaneKind::LocalOpenWeight,
        2 => GatewayModelLaneKind::RentedOpenWeight,
        3 => GatewayModelLaneKind::HostedSmall,
        _ => GatewayModelLaneKind::PremiumEscalation,
    }
}

fn checker_lane_kind(index: u8) -> CheckerGatewayModelLaneKind {
    match index {
        0 => CheckerGatewayModelLaneKind::Deterministic,
        1 => CheckerGatewayModelLaneKind::LocalOpenWeight,
        2 => CheckerGatewayModelLaneKind::RentedOpenWeight,
        3 => CheckerGatewayModelLaneKind::HostedSmall,
        _ => CheckerGatewayModelLaneKind::PremiumEscalation,
    }
}

fn production_threat_label(index: u8) -> GatewayThreatLabel {
    match index {
        0 => GatewayThreatLabel::Benign,
        1 => GatewayThreatLabel::PromptInjectionPayment,
        2 => GatewayThreatLabel::WrongCounterparty,
        3 => GatewayThreatLabel::AmountLimitBypass,
        4 => GatewayThreatLabel::SourceDigestDrift,
        5 => GatewayThreatLabel::StaleApprovalReplay,
        6 => GatewayThreatLabel::DuplicateJsonKeyPayload,
        7 => GatewayThreatLabel::PolicyDowngrade,
        8 => GatewayThreatLabel::DirectAuthorityRequest,
        9 => GatewayThreatLabel::ForgedAcceptedDecision,
        10 => GatewayThreatLabel::MissingNonclaim,
        11 => GatewayThreatLabel::MissingSourceDigest,
        12 => GatewayThreatLabel::StaleJournalTip,
        _ => GatewayThreatLabel::SignerBeforeAdmission,
    }
}

fn checker_threat_label(index: u8) -> CheckerGatewayThreatLabel {
    match index {
        0 => CheckerGatewayThreatLabel::Benign,
        1 => CheckerGatewayThreatLabel::PromptInjectionPayment,
        2 => CheckerGatewayThreatLabel::WrongCounterparty,
        3 => CheckerGatewayThreatLabel::AmountLimitBypass,
        4 => CheckerGatewayThreatLabel::SourceDigestDrift,
        5 => CheckerGatewayThreatLabel::StaleApprovalReplay,
        6 => CheckerGatewayThreatLabel::DuplicateJsonKeyPayload,
        7 => CheckerGatewayThreatLabel::PolicyDowngrade,
        8 => CheckerGatewayThreatLabel::DirectAuthorityRequest,
        9 => CheckerGatewayThreatLabel::ForgedAcceptedDecision,
        10 => CheckerGatewayThreatLabel::MissingNonclaim,
        11 => CheckerGatewayThreatLabel::MissingSourceDigest,
        12 => CheckerGatewayThreatLabel::StaleJournalTip,
        _ => CheckerGatewayThreatLabel::SignerBeforeAdmission,
    }
}

#[test]
fn phase662_checker_matches_production_and_the_phase660_golden_vector() {
    let production = production_fixture(None);
    let checker_proposal = checker_fixture(None);
    let result = assert_agreement(&production, &checker_proposal);
    let expected_digest =
        hash_from_hex("52de11c37c1492b7c9fb7c42660d693f5a7cbc6ed69f3bb371d66ad2686938fa");

    assert_eq!(production.digest().0, expected_digest);
    assert_eq!(result.digest, expected_digest);
    let expected_preimage = phase665_fixture_bytes(
        PHASE665_GOLDEN_PREIMAGE_FIXTURE,
        "phase660-golden-preimage.json",
    );
    assert_eq!(
        gateway_action_proposal_digest_preimage(&production),
        expected_preimage
    );
    assert_eq!(result.encoded_preimage, expected_preimage);
    assert_eq!(
        result.encoded_preimage,
        gateway_action_proposal_digest_preimage(&production)
    );
    assert_eq!(result.independence_profile.diverse_axes.len(), 7);
    assert_eq!(result.independence_profile.shared_axes.len(), 8);
    assert_eq!(result.independence_profile.imported_trust_axes.len(), 5);
    assert!(result
        .explicit_nonclaims
        .contains(&"not independent external reproduction".to_owned()));
    assert!(result
        .explicit_nonclaims
        .contains(&"not source correspondence proof".to_owned()));
}

#[test]
fn phase662_checker_matches_production_for_all_18_concrete_mutations() {
    let baseline_production = production_fixture(None);
    let baseline_checker = checker_fixture(None);
    let baseline = assert_agreement(&baseline_production, &baseline_checker);

    for mutation in MUTATIONS {
        let production = production_fixture(Some(mutation));
        let checker_proposal = checker_fixture(Some(mutation));
        let result = assert_agreement(&production, &checker_proposal);
        assert_ne!(
            gateway_action_proposal_digest_preimage(&production),
            gateway_action_proposal_digest_preimage(&baseline_production),
            "production preimage mutation must differ: {mutation:?}"
        );
        assert_ne!(
            result.encoded_preimage, baseline.encoded_preimage,
            "checker preimage mutation must differ: {mutation:?}"
        );
        assert_ne!(
            result.digest, baseline.digest,
            "checker digest mutation must differ: {mutation:?}"
        );
    }
}

#[test]
fn phase662_checker_matches_production_for_set_ordering_and_encoding_edges() {
    let artifact_a = CheckerArtifactDigest {
        id: "a-artifact".to_owned(),
        sha256: [8; 32],
    };
    let artifact_z = CheckerArtifactDigest {
        id: "z-artifact".to_owned(),
        sha256: [9; 32],
    };
    let mut production = production_fixture(None);
    production.source_artifact_digests.insert(ArtifactDigest {
        id: "z-artifact".to_owned(),
        sha256: Hash([9; 32]),
    });
    production.source_artifact_digests.insert(ArtifactDigest {
        id: "a-artifact".to_owned(),
        sha256: Hash([8; 32]),
    });
    production
        .nonclaims
        .insert(NonClaimLabel("z-nonclaim".to_owned()));
    production
        .nonclaims
        .insert(NonClaimLabel("a-nonclaim".to_owned()));
    production
        .threat_labels
        .insert(GatewayThreatLabel::StaleApprovalReplay);
    production.threat_labels.insert(GatewayThreatLabel::Benign);

    let mut checker_first = checker_fixture(None);
    checker_first.source_artifact_digests = vec![artifact_z.clone(), artifact_a.clone()];
    checker_first.nonclaims = vec![
        CheckerNonclaim("z-nonclaim".to_owned()),
        CheckerNonclaim("a-nonclaim".to_owned()),
    ];
    checker_first.threat_labels = vec![
        CheckerGatewayThreatLabel::StaleApprovalReplay,
        CheckerGatewayThreatLabel::Benign,
    ];
    let mut checker_second = checker_fixture(None);
    checker_second.source_artifact_digests = vec![artifact_a, artifact_z];
    checker_second.nonclaims = vec![
        CheckerNonclaim("a-nonclaim".to_owned()),
        CheckerNonclaim("z-nonclaim".to_owned()),
    ];
    checker_second.threat_labels = vec![
        CheckerGatewayThreatLabel::Benign,
        CheckerGatewayThreatLabel::StaleApprovalReplay,
    ];

    let first = assert_agreement(&production, &checker_first);
    let second = assert_agreement(&production, &checker_second);
    let expected_preimage = phase665_fixture_bytes(
        PHASE665_ORDERING_PREIMAGE_FIXTURE,
        "phase662-ordering-preimage.json",
    );
    assert_eq!(
        gateway_action_proposal_digest_preimage(&production),
        expected_preimage
    );
    assert_eq!(first.encoded_preimage, expected_preimage);
    assert_eq!(second.encoded_preimage, expected_preimage);
    assert_eq!(first.encoded_preimage, second.encoded_preimage);
    assert_eq!(first.digest, second.digest);

    let mut production_edge = production_fixture(None);
    production_edge.target = "quote\" slash\\ backspace\u{0008} tab\t newline\n formfeed\u{000c} carriage\r control\u{0001} snowman \u{2603}".to_owned();
    production_edge.value_units = u64::MAX;
    production_edge.source_artifact_digests = BTreeSet::from([ArtifactDigest {
        id: "edge-artifact".to_owned(),
        sha256: Hash([255; 32]),
    }]);
    production_edge.nonclaims = BTreeSet::from([NonClaimLabel("edge nonclaim".to_owned())]);
    production_edge.threat_labels = BTreeSet::from([GatewayThreatLabel::DuplicateJsonKeyPayload]);

    let mut checker_edge = checker_fixture(None);
    checker_edge.target = "quote\" slash\\ backspace\u{0008} tab\t newline\n formfeed\u{000c} carriage\r control\u{0001} snowman \u{2603}".to_owned();
    checker_edge.value_units = u64::MAX;
    checker_edge.source_artifact_digests = vec![CheckerArtifactDigest {
        id: "edge-artifact".to_owned(),
        sha256: [255; 32],
    }];
    checker_edge.nonclaims = vec![CheckerNonclaim("edge nonclaim".to_owned())];
    checker_edge.threat_labels = vec![CheckerGatewayThreatLabel::DuplicateJsonKeyPayload];
    assert_agreement(&production_edge, &checker_edge);
}

#[test]
fn phase662_checker_matches_production_for_every_enum_variant() {
    let action_variants = [
        (
            GatewayActionKind::Payment,
            CheckerGatewayActionKind::Payment,
        ),
        (GatewayActionKind::Trade, CheckerGatewayActionKind::Trade),
        (
            GatewayActionKind::ToolCall,
            CheckerGatewayActionKind::ToolCall,
        ),
        (
            GatewayActionKind::DataAccess,
            CheckerGatewayActionKind::DataAccess,
        ),
        (
            GatewayActionKind::ComputeRental,
            CheckerGatewayActionKind::ComputeRental,
        ),
        (
            GatewayActionKind::Deployment,
            CheckerGatewayActionKind::Deployment,
        ),
        (
            GatewayActionKind::Checkout,
            CheckerGatewayActionKind::Checkout,
        ),
    ];
    for (production_kind, checker_kind) in action_variants {
        let mut production = production_fixture(None);
        production.action_kind = production_kind;
        let mut checker = checker_fixture(None);
        checker.action_kind = checker_kind;
        assert_agreement(&production, &checker);
    }

    let lane_variants = [
        (
            GatewayModelLaneKind::Deterministic,
            CheckerGatewayModelLaneKind::Deterministic,
        ),
        (
            GatewayModelLaneKind::LocalOpenWeight,
            CheckerGatewayModelLaneKind::LocalOpenWeight,
        ),
        (
            GatewayModelLaneKind::RentedOpenWeight,
            CheckerGatewayModelLaneKind::RentedOpenWeight,
        ),
        (
            GatewayModelLaneKind::HostedSmall,
            CheckerGatewayModelLaneKind::HostedSmall,
        ),
        (
            GatewayModelLaneKind::PremiumEscalation,
            CheckerGatewayModelLaneKind::PremiumEscalation,
        ),
    ];
    for (production_kind, checker_kind) in lane_variants {
        let mut production = production_fixture(None);
        production.model_lane.lane_kind = production_kind;
        let mut checker = checker_fixture(None);
        checker.model_lane.lane_kind = checker_kind;
        assert_agreement(&production, &checker);
    }

    let threat_variants = [
        (
            GatewayThreatLabel::Benign,
            CheckerGatewayThreatLabel::Benign,
        ),
        (
            GatewayThreatLabel::PromptInjectionPayment,
            CheckerGatewayThreatLabel::PromptInjectionPayment,
        ),
        (
            GatewayThreatLabel::WrongCounterparty,
            CheckerGatewayThreatLabel::WrongCounterparty,
        ),
        (
            GatewayThreatLabel::AmountLimitBypass,
            CheckerGatewayThreatLabel::AmountLimitBypass,
        ),
        (
            GatewayThreatLabel::SourceDigestDrift,
            CheckerGatewayThreatLabel::SourceDigestDrift,
        ),
        (
            GatewayThreatLabel::StaleApprovalReplay,
            CheckerGatewayThreatLabel::StaleApprovalReplay,
        ),
        (
            GatewayThreatLabel::DuplicateJsonKeyPayload,
            CheckerGatewayThreatLabel::DuplicateJsonKeyPayload,
        ),
        (
            GatewayThreatLabel::PolicyDowngrade,
            CheckerGatewayThreatLabel::PolicyDowngrade,
        ),
        (
            GatewayThreatLabel::DirectAuthorityRequest,
            CheckerGatewayThreatLabel::DirectAuthorityRequest,
        ),
        (
            GatewayThreatLabel::ForgedAcceptedDecision,
            CheckerGatewayThreatLabel::ForgedAcceptedDecision,
        ),
        (
            GatewayThreatLabel::MissingNonclaim,
            CheckerGatewayThreatLabel::MissingNonclaim,
        ),
        (
            GatewayThreatLabel::MissingSourceDigest,
            CheckerGatewayThreatLabel::MissingSourceDigest,
        ),
        (
            GatewayThreatLabel::StaleJournalTip,
            CheckerGatewayThreatLabel::StaleJournalTip,
        ),
        (
            GatewayThreatLabel::SignerBeforeAdmission,
            CheckerGatewayThreatLabel::SignerBeforeAdmission,
        ),
    ];
    for (production_label, checker_label) in threat_variants {
        let mut production = production_fixture(None);
        production.threat_labels = BTreeSet::from([production_label]);
        let mut checker = checker_fixture(None);
        checker.threat_labels = vec![checker_label];
        assert_agreement(&production, &checker);
    }
}

#[test]
fn phase662_e2e_comparison_fails_closed_on_checker_drift() {
    let production = production_fixture(None);
    let checker_proposal = checker_fixture(None);
    let baseline = assert_agreement(&production, &checker_proposal);
    let mut cases = Vec::new();

    let mut result = baseline.clone();
    result.digest_tag = "hsai-agent-admission:gateway-action-proposal:v2".to_owned();
    cases.push((ComparisonIssue::DigestTag, result));

    let mut result = baseline.clone();
    result.encoded_preimage[0] ^= 1;
    cases.push((ComparisonIssue::ProductionPreimage, result));

    let mut result = baseline.clone();
    result.digest[0] ^= 1;
    cases.push((ComparisonIssue::ProductionDigest, result));

    let mut result = baseline.clone();
    result.independence_profile.shared_axes.clear();
    cases.push((ComparisonIssue::IndependenceProfile, result));

    let mut result = baseline.clone();
    result.claim_boundary = "independent formal verification".to_owned();
    cases.push((ComparisonIssue::ClaimBoundary, result));

    let mut result = baseline;
    result.explicit_nonclaims.clear();
    cases.push((ComparisonIssue::ExplicitNonclaims, result));

    for (expected_issue, result) in cases {
        let (classification, issues) = compare(&production, &result);
        assert_eq!(
            classification,
            CheckerComparisonClassification::LocalImplementationDiverseCheckerMismatch
        );
        assert!(issues.contains(&expected_issue));
    }
}

proptest! {
    #![proptest_config(ProptestConfig {
        cases: 256,
        failure_persistence: None,
        ..ProptestConfig::default()
    })]

    #[test]
    fn phase662_checker_differential_proptest_matches_generated_production_proposals(
        id in arbitrary_string(),
        subject in arbitrary_string(),
        target in arbitrary_string(),
        model_family in arbitrary_string(),
        model_artifact_id in arbitrary_string(),
        runtime in arbitrary_string(),
        artifact_id in arbitrary_string(),
        nonclaim in arbitrary_string(),
        value_units in any::<u64>(),
        artifact_digest in any::<[u8; 32]>(),
        prompt_digest in any::<[u8; 32]>(),
        input_digest in any::<[u8; 32]>(),
        output_digest in any::<[u8; 32]>(),
        action_index in 0u8..7,
        lane_index in 0u8..5,
        threat_index in 0u8..14,
        non_secret in any::<bool>(),
        direct_authority_requested in any::<bool>(),
        signer_before_admission in any::<bool>(),
    ) {
        let production = GatewayActionProposal {
            id: GatewayActionId(id.clone()),
            subject: SubjectId(subject.clone()),
            action_kind: production_action_kind(action_index),
            target: target.clone(),
            value_units,
            source_artifact_digests: BTreeSet::from([ArtifactDigest {
                id: artifact_id.clone(),
                sha256: Hash(artifact_digest),
            }]),
            nonclaims: BTreeSet::from([NonClaimLabel(nonclaim.clone())]),
            model_lane: GatewayModelLaneProvenance {
                lane_kind: production_lane_kind(lane_index),
                model_family: model_family.clone(),
                artifact_id: model_artifact_id.clone(),
                runtime: runtime.clone(),
                prompt_template_digest: Hash(prompt_digest),
                input_corpus_digest: Hash(input_digest),
                output_bundle_digest: Hash(output_digest),
                non_secret,
            },
            threat_labels: BTreeSet::from([production_threat_label(threat_index)]),
            direct_authority_requested,
            signer_or_tool_requested_before_admission: signer_before_admission,
        };
        let checker_proposal = CheckerGatewayActionProposal {
            id: CheckerGatewayActionId(id),
            subject: CheckerSubjectId(subject),
            action_kind: checker_action_kind(action_index),
            target,
            value_units,
            source_artifact_digests: vec![CheckerArtifactDigest {
                id: artifact_id,
                sha256: artifact_digest,
            }],
            nonclaims: vec![CheckerNonclaim(nonclaim)],
            model_lane: CheckerModelLaneProvenance {
                lane_kind: checker_lane_kind(lane_index),
                model_family,
                artifact_id: model_artifact_id,
                runtime,
                prompt_template_digest: prompt_digest,
                input_corpus_digest: input_digest,
                output_bundle_digest: output_digest,
                non_secret,
            },
            threat_labels: vec![checker_threat_label(threat_index)],
            direct_authority_requested,
            signer_or_tool_requested_before_admission: signer_before_admission,
        };
        let checker_result = check_gateway_action_proposal_digest_v1(&checker_proposal)
            .expect("generated checker proposal encodes");
        let checker_validation = validate_checker_digest_result(&checker_proposal, &checker_result)
            .expect("generated checker result validates");
        let (classification, issues) = compare(&production, &checker_result);

        prop_assert!(checker_validation.valid);
        prop_assert_eq!(
            classification,
            CheckerComparisonClassification::LocalImplementationDiverseCheckerAgreement
        );
        prop_assert!(issues.is_empty());
        prop_assert_eq!(
            checker_result.encoded_preimage,
            gateway_action_proposal_digest_preimage(&production)
        );
        prop_assert_eq!(checker_result.digest, production.digest().0);
    }
}

#[test]
fn phase662_checker_dependency_boundary_rejects_production_serde_and_sha2_imports() {
    const MANIFEST: &str = include_str!("../../hsai-gateway-digest-checker/Cargo.toml");
    const SOURCE: &str = include_str!("../../hsai-gateway-digest-checker/src/lib.rs");

    assert!(MANIFEST.contains("ring = \"=0.17.14\""));
    for forbidden in [
        "hsai-agent-admission",
        "hsai-claim-envelope",
        "hsai-agent-case",
        "serde =",
        "serde_json =",
        "sha2 =",
    ] {
        assert!(
            !MANIFEST.contains(forbidden),
            "checker manifest contains forbidden dependency: {forbidden}"
        );
    }
    for forbidden in [
        "use hsai_",
        "hsai_agent_admission::",
        "hsai_claim_envelope::",
        "use serde::",
        "use serde_json",
        "serde_json::",
        "use sha2",
        "sha2::",
        "derive(Serialize",
        "derive(Deserialize",
    ] {
        assert!(
            !SOURCE.contains(forbidden),
            "checker source contains forbidden coupling: {forbidden}"
        );
    }
}
