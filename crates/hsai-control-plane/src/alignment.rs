use crate::{hash_parts, Digest};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum AlignmentTrack {
    Behavioral,
    Mechanistic,
    ScalableOversight,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AlignmentPlan {
    pub plan_id: String,
    pub track: AlignmentTrack,
    pub requires_fit_tune_assessment: bool,
    pub requires_prediction_lock: bool,
    pub requires_independent_validator: bool,
    pub requires_held_out: bool,
    pub requires_causal_intervention: bool,
    pub evaluator_independent: bool,
}

impl AlignmentPlan {
    pub fn digest(&self) -> Digest {
        hash_parts(
            "hsai-control-plane:alignment-plan:v1",
            &[
                self.plan_id.clone(),
                format!("{:?}", self.track),
                self.requires_fit_tune_assessment.to_string(),
                self.requires_prediction_lock.to_string(),
                self.requires_independent_validator.to_string(),
                self.requires_held_out.to_string(),
                self.requires_causal_intervention.to_string(),
                self.evaluator_independent.to_string(),
            ],
        )
    }

    pub fn validate(&self) -> Result<(), AlignmentBlocker> {
        if self.plan_id.is_empty() {
            return Err(AlignmentBlocker::EmptyPlanId);
        }
        if self.requires_fit_tune_assessment && !self.requires_prediction_lock {
            return Err(AlignmentBlocker::AssessmentWithoutPredictionLock);
        }
        if self.requires_held_out && !self.requires_independent_validator {
            return Err(AlignmentBlocker::HeldOutWithoutIndependentValidator);
        }
        if self.requires_causal_intervention && self.track != AlignmentTrack::Mechanistic {
            return Err(AlignmentBlocker::CausalInterventionOnWrongTrack);
        }
        if !self.evaluator_independent {
            return Err(AlignmentBlocker::EvaluatorNotIndependent);
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AlignmentEvidence {
    pub plan_digest: Digest,
    pub fit_digest: Option<Digest>,
    pub tune_digest: Option<Digest>,
    pub assessment_digest: Option<Digest>,
    pub prediction_lock_digest: Option<Digest>,
    pub validator_digest: Option<Digest>,
    pub held_out: bool,
    pub causal_intervention_observed: bool,
    pub evaluator_independent: bool,
    pub model_controls_evaluator: bool,
}

impl AlignmentEvidence {
    pub fn digest(&self) -> Digest {
        hash_parts(
            "hsai-control-plane:alignment-evidence:v1",
            &[
                self.plan_digest.to_hex(),
                optional_digest(&self.fit_digest),
                optional_digest(&self.tune_digest),
                optional_digest(&self.assessment_digest),
                optional_digest(&self.prediction_lock_digest),
                optional_digest(&self.validator_digest),
                self.held_out.to_string(),
                self.causal_intervention_observed.to_string(),
                self.evaluator_independent.to_string(),
                self.model_controls_evaluator.to_string(),
            ],
        )
    }
}

fn optional_digest(digest: &Option<Digest>) -> String {
    digest
        .as_ref()
        .map(Digest::to_hex)
        .unwrap_or_else(|| "absent".to_owned())
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AlignmentBlocker {
    EmptyPlanId,
    AssessmentWithoutPredictionLock,
    HeldOutWithoutIndependentValidator,
    CausalInterventionOnWrongTrack,
    EvaluatorNotIndependent,
    PlanDigestMismatch,
    MissingFit,
    MissingTune,
    MissingAssessment,
    MissingPredictionLock,
    MissingValidator,
    HeldOutRequired,
    CausalInterventionRequired,
    EvaluatorCompromised,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AlignmentDecision {
    Blocked(Vec<AlignmentBlocker>),
    LocalCandidate {
        plan_digest: Digest,
        evidence_digest: Digest,
    },
}

pub fn evaluate_alignment(plan: &AlignmentPlan, evidence: &AlignmentEvidence) -> AlignmentDecision {
    let mut blockers = Vec::new();
    if let Err(blocker) = plan.validate() {
        blockers.push(blocker);
    }
    if evidence.plan_digest != plan.digest() {
        blockers.push(AlignmentBlocker::PlanDigestMismatch);
    }
    if plan.requires_fit_tune_assessment {
        if missing(&evidence.fit_digest) {
            blockers.push(AlignmentBlocker::MissingFit);
        }
        if missing(&evidence.tune_digest) {
            blockers.push(AlignmentBlocker::MissingTune);
        }
        if missing(&evidence.assessment_digest) {
            blockers.push(AlignmentBlocker::MissingAssessment);
        }
    }
    if plan.requires_prediction_lock && missing(&evidence.prediction_lock_digest) {
        blockers.push(AlignmentBlocker::MissingPredictionLock);
    }
    if plan.requires_independent_validator && missing(&evidence.validator_digest) {
        blockers.push(AlignmentBlocker::MissingValidator);
    }
    if plan.requires_held_out && !evidence.held_out {
        blockers.push(AlignmentBlocker::HeldOutRequired);
    }
    if plan.requires_causal_intervention && !evidence.causal_intervention_observed {
        blockers.push(AlignmentBlocker::CausalInterventionRequired);
    }
    if !evidence.evaluator_independent || !plan.evaluator_independent {
        blockers.push(AlignmentBlocker::EvaluatorNotIndependent);
    }
    if evidence.model_controls_evaluator {
        blockers.push(AlignmentBlocker::EvaluatorCompromised);
    }
    if blockers.is_empty() {
        AlignmentDecision::LocalCandidate {
            plan_digest: plan.digest(),
            evidence_digest: evidence.digest(),
        }
    } else {
        AlignmentDecision::Blocked(blockers)
    }
}

fn missing(digest: &Option<Digest>) -> bool {
    digest.as_ref().map_or(true, Digest::is_zero)
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum UpdateSurface {
    ModelAdapter,
    PromptPolicy,
    ToolPolicy,
    Evaluator,
    Validator,
    EvidenceLedger,
    CapabilityPolicy,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct LearningUpdateProposal {
    pub update_id: String,
    pub immutable_base_digest: Digest,
    pub candidate_digest: Digest,
    pub trajectory_digest: Digest,
    pub prediction_lock_digest: Option<Digest>,
    pub independent_evaluation_digest: Option<Digest>,
    pub rollback_target_digest: Option<Digest>,
    pub requested_surfaces: BTreeSet<UpdateSurface>,
    pub shadow_mode: bool,
    pub requested_promotion: bool,
    pub resource_budget_units: u64,
}

impl LearningUpdateProposal {
    pub fn digest(&self) -> Digest {
        hash_parts(
            "hsai-control-plane:learning-update-proposal:v1",
            &[
                self.update_id.clone(),
                self.immutable_base_digest.to_hex(),
                self.candidate_digest.to_hex(),
                self.trajectory_digest.to_hex(),
                optional_digest(&self.prediction_lock_digest),
                optional_digest(&self.independent_evaluation_digest),
                optional_digest(&self.rollback_target_digest),
                self.requested_surfaces
                    .iter()
                    .map(|surface| format!("{surface:?}"))
                    .collect::<Vec<_>>()
                    .join(","),
                self.shadow_mode.to_string(),
                self.requested_promotion.to_string(),
                self.resource_budget_units.to_string(),
            ],
        )
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum UpdateBlocker {
    EmptyUpdateId,
    MissingDigest,
    BaseEqualsCandidate,
    MissingPredictionLock,
    MissingIndependentEvaluation,
    MissingRollbackTarget,
    NotShadowMode,
    PromotionRequested,
    ZeroResourceBudget,
    ProtectedSurface(UpdateSurface),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum LearningDecision {
    Blocked(Vec<UpdateBlocker>),
    ShadowOnly {
        update_digest: Digest,
        promotion_allowed: bool,
    },
}

pub fn evaluate_learning_update(update: &LearningUpdateProposal) -> LearningDecision {
    let mut blockers = Vec::new();
    if update.update_id.is_empty() {
        blockers.push(UpdateBlocker::EmptyUpdateId);
    }
    if update.immutable_base_digest.is_zero()
        || update.candidate_digest.is_zero()
        || update.trajectory_digest.is_zero()
    {
        blockers.push(UpdateBlocker::MissingDigest);
    }
    if update.immutable_base_digest == update.candidate_digest {
        blockers.push(UpdateBlocker::BaseEqualsCandidate);
    }
    if update
        .prediction_lock_digest
        .as_ref()
        .map_or(true, Digest::is_zero)
    {
        blockers.push(UpdateBlocker::MissingPredictionLock);
    }
    if update
        .independent_evaluation_digest
        .as_ref()
        .map_or(true, Digest::is_zero)
    {
        blockers.push(UpdateBlocker::MissingIndependentEvaluation);
    }
    if update
        .rollback_target_digest
        .as_ref()
        .map_or(true, Digest::is_zero)
    {
        blockers.push(UpdateBlocker::MissingRollbackTarget);
    }
    if !update.shadow_mode {
        blockers.push(UpdateBlocker::NotShadowMode);
    }
    if update.requested_promotion {
        blockers.push(UpdateBlocker::PromotionRequested);
    }
    if update.resource_budget_units == 0 {
        blockers.push(UpdateBlocker::ZeroResourceBudget);
    }
    for surface in &update.requested_surfaces {
        if matches!(
            surface,
            UpdateSurface::Evaluator
                | UpdateSurface::Validator
                | UpdateSurface::EvidenceLedger
                | UpdateSurface::CapabilityPolicy
        ) {
            blockers.push(UpdateBlocker::ProtectedSurface(*surface));
        }
    }
    if blockers.is_empty() {
        LearningDecision::ShadowOnly {
            update_digest: update.digest(),
            promotion_allowed: false,
        }
    } else {
        LearningDecision::Blocked(blockers)
    }
}
