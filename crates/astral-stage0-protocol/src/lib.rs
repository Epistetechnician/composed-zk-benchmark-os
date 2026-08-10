//! Pure-data Astral Stage 0 protocol contracts.
//!
//! State slice: `astral-stage0-rust-protocol-parity-v9`.
//! This crate performs no training, scoring, intervention, or I/O.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::cmp::Ordering;
use std::collections::BTreeMap;

pub const DEAD_ZONE: f64 = 1e-4;
pub const PRACTICAL_MARGIN: f64 = 0.05;
pub const RESERVED_FUTURE_FAMILIES: std::ops::RangeInclusive<u16> = 512..=575;
pub const RESERVED_FUTURE_SEEDS: [u64; 3] = [173, 179, 181];

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DevelopmentSplit {
    Train,
    DevelopmentDesign,
    DevelopmentAssessment,
}

pub fn development_split(family: u16) -> Result<DevelopmentSplit, ProtocolError> {
    match family {
        0..=159 => Ok(DevelopmentSplit::Train),
        160..=175 => Ok(DevelopmentSplit::DevelopmentDesign),
        176..=191 => Ok(DevelopmentSplit::DevelopmentAssessment),
        _ => Err(ProtocolError::FamilySealed(family)),
    }
}

pub fn require_unreserved_seed(seed: u64) -> Result<(), ProtocolError> {
    if RESERVED_FUTURE_SEEDS.contains(&seed) {
        Err(ProtocolError::SeedSealed(seed))
    } else {
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CandidateMethod {
    SignedDotLegacy,
    AbsoluteProductL1,
    AbsoluteProductL2,
    AbsoluteProductLinf,
    SignCoherentMass,
}

impl CandidateMethod {
    pub const PANEL: [Self; 5] = [
        Self::SignedDotLegacy,
        Self::AbsoluteProductL1,
        Self::AbsoluteProductL2,
        Self::AbsoluteProductLinf,
        Self::SignCoherentMass,
    ];

    pub const ELIGIBLE_PANEL: [Self; 4] = [
        Self::AbsoluteProductL1,
        Self::AbsoluteProductL2,
        Self::AbsoluteProductLinf,
        Self::SignCoherentMass,
    ];
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CompetitiveBaseline {
    ActivationNorm,
    AttentionMass,
    GradientNorm,
}

impl CompetitiveBaseline {
    pub const PANEL: [Self; 3] = [
        Self::ActivationNorm,
        Self::AttentionMass,
        Self::GradientNorm,
    ];
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct MethodAssessment {
    pub method: CandidateMethod,
    pub coverage_by_seed: BTreeMap<u64, f64>,
    pub advantage_by_baseline_and_seed: BTreeMap<CompetitiveBaseline, BTreeMap<u64, f64>>,
    pub permutation_advantage_by_seed: BTreeMap<u64, f64>,
}

impl MethodAssessment {
    pub fn is_selection_eligible(&self) -> bool {
        if self.method == CandidateMethod::SignedDotLegacy
            || self.coverage_by_seed.is_empty()
            || self.permutation_advantage_by_seed.is_empty()
        {
            return false;
        }
        if self
            .coverage_by_seed
            .values()
            .any(|value| !value.is_finite() || *value < 0.80)
        {
            return false;
        }
        if self
            .permutation_advantage_by_seed
            .values()
            .any(|value| !value.is_finite() || *value <= 0.0)
        {
            return false;
        }
        if !matches!(
            mean(self.permutation_advantage_by_seed.values().copied()),
            Some(value) if value > 0.0
        ) {
            return false;
        }
        CompetitiveBaseline::PANEL.iter().all(|baseline| {
            let Some(per_seed) = self.advantage_by_baseline_and_seed.get(baseline) else {
                return false;
            };
            !per_seed.is_empty()
                && per_seed
                    .values()
                    .all(|value| value.is_finite() && *value > 0.0)
                && mean(per_seed.values().copied()).is_some_and(|value| value > PRACTICAL_MARGIN)
        })
    }

    fn minimum_cell(&self) -> Option<f64> {
        self.advantage_by_baseline_and_seed
            .values()
            .flat_map(|per_seed| per_seed.values().copied())
            .reduce(f64::min)
    }

    fn mean_cell(&self) -> Option<f64> {
        mean(
            self.advantage_by_baseline_and_seed
                .values()
                .flat_map(|per_seed| per_seed.values().copied()),
        )
    }
}

pub fn select_exploratory_method(assessments: &[MethodAssessment]) -> Option<CandidateMethod> {
    CandidateMethod::ELIGIBLE_PANEL
        .iter()
        .filter_map(|method| {
            let assessment = assessments
                .iter()
                .find(|assessment| assessment.method == *method)?;
            if !assessment.is_selection_eligible() {
                return None;
            }
            Some((*method, assessment.minimum_cell()?, assessment.mean_cell()?))
        })
        .max_by(|left, right| {
            left.1
                .partial_cmp(&right.1)
                .unwrap_or(Ordering::Less)
                .then_with(|| left.2.partial_cmp(&right.2).unwrap_or(Ordering::Less))
                .then_with(|| panel_index(right.0).cmp(&panel_index(left.0)))
        })
        .map(|row| row.0)
}

pub fn selected_head(scores: [f64; 4]) -> Result<usize, ProtocolError> {
    if scores.iter().any(|score| !score.is_finite()) {
        return Err(ProtocolError::NonFinite);
    }
    Ok((0..4)
        .min_by(|left, right| {
            scores[*right]
                .abs()
                .partial_cmp(&scores[*left].abs())
                .unwrap_or(Ordering::Equal)
                .then_with(|| left.cmp(right))
        })
        .expect("four scores are present"))
}

pub fn normalized_regret(
    effects: [f64; 4],
    scores: [f64; 4],
) -> Result<(f64, bool), ProtocolError> {
    if effects
        .iter()
        .chain(scores.iter())
        .any(|value| !value.is_finite())
    {
        return Err(ProtocolError::NonFinite);
    }
    let oracle = effects.iter().map(|value| value.abs()).fold(0.0, f64::max);
    if oracle <= DEAD_ZONE {
        return Ok((0.0, false));
    }
    let chosen = effects[selected_head(scores)?].abs();
    Ok((((oracle - chosen) / oracle).clamp(0.0, 1.0), true))
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct ClaimBoundary {
    pub local_cross_language_parity_only: bool,
    pub accepted_evidence: bool,
    pub stage0_pass: bool,
    pub independent_replication: bool,
    pub self_modeling: bool,
}

impl Default for ClaimBoundary {
    fn default() -> Self {
        Self {
            local_cross_language_parity_only: true,
            accepted_evidence: false,
            stage0_pass: false,
            independent_replication: false,
            self_modeling: false,
        }
    }
}

pub fn tagged_sha256(domain: &str, fields: &[&[u8]]) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update((domain.len() as u64).to_be_bytes());
    digest.update(domain.as_bytes());
    for field in fields {
        digest.update((field.len() as u64).to_be_bytes());
        digest.update(field);
    }
    digest.finalize().into()
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ProtocolError {
    FamilySealed(u16),
    SeedSealed(u64),
    NonFinite,
}

fn mean(values: impl Iterator<Item = f64>) -> Option<f64> {
    let values: Vec<_> = values.collect();
    (!values.is_empty()).then(|| values.iter().sum::<f64>() / values.len() as f64)
}

fn panel_index(method: CandidateMethod) -> usize {
    CandidateMethod::ELIGIBLE_PANEL
        .iter()
        .position(|candidate| *candidate == method)
        .expect("eligible method is in panel")
}
