use statebook_core::SignedRational;
use std::collections::BTreeMap;

use super::types::{ConservativeValuationProfileV1, DecisionReasonV1};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ValuationResult {
    pub ok: bool,
    pub reason: Option<DecisionReasonV1>,
    pub numeraire_capacity: SignedRational,
}

pub fn evaluate_valuation(
    profile: &ConservativeValuationProfileV1,
    asset: &str,
    now: i64,
) -> ValuationResult {
    if profile.observations.is_empty() {
        return ValuationResult {
            ok: false,
            reason: Some(DecisionReasonV1::ValuationMissing),
            numeraire_capacity: SignedRational::new(0, 1).unwrap(),
        };
    }
    let mut rates: BTreeMap<String, SignedRational> = BTreeMap::new();
    for observation in &profile.observations {
        if observation.observed_at > now || now - observation.observed_at > profile.max_age_seconds
        {
            return ValuationResult {
                ok: false,
                reason: Some(DecisionReasonV1::ValuationStale),
                numeraire_capacity: SignedRational::new(0, 1).unwrap(),
            };
        }
        if !profile.independence_roots.contains(&observation.root_id) {
            return ValuationResult {
                ok: false,
                reason: Some(DecisionReasonV1::ValuationConflict),
                numeraire_capacity: SignedRational::new(0, 1).unwrap(),
            };
        }
        let rate = observation
            .rate
            .to_signed_rational()
            .unwrap_or(SignedRational::new(0, 1).unwrap());
        if let Some(existing) = rates.insert(observation.asset.clone(), rate) {
            if existing != rate {
                return ValuationResult {
                    ok: false,
                    reason: Some(DecisionReasonV1::ValuationConflict),
                    numeraire_capacity: SignedRational::new(0, 1).unwrap(),
                };
            }
        }
    }
    let asset_rate = match rates.get(asset) {
        Some(value) => *value,
        None => {
            return ValuationResult {
                ok: false,
                reason: Some(DecisionReasonV1::ValuationMissing),
                numeraire_capacity: SignedRational::new(0, 1).unwrap(),
            };
        }
    };
    let capacity = asset_rate
        .checked_mul(profile.stress_multiplier)
        .unwrap_or(SignedRational::new(0, 1).unwrap());
    ValuationResult {
        ok: true,
        reason: None,
        numeraire_capacity: capacity,
    }
}
