//! Claim-boundary escalation guard for Phase J.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::ClaimBoundary;

/// Guard that blocks accidental claim-boundary escalation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ClaimBoundaryEscalationGuard {
    /// Allow Level0DesignNote to Level1LocalReplay for strict local-only candidates.
    pub allow_level0_to_level1_local: bool,
    /// Always block accepted Level2+ evidence in Phase J.
    pub block_level2_plus_actual: bool,
    /// Always block formal evidence levels in Phase J.
    pub block_formal_levels: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ClaimBoundaryEscalationGuard {
    fn default() -> Self {
        Self {
            allow_level0_to_level1_local: false,
            block_level2_plus_actual: true,
            block_formal_levels: true,
            notes: vec![
                "Level2 eligibility is not Level2 evidence.".to_string(),
                "Evidence-record candidates are not accepted evidence.".to_string(),
            ],
        }
    }
}

impl ClaimBoundaryEscalationGuard {
    /// Build a guard that allows strict local-only Level1 candidate creation.
    pub fn allowing_level1_local_candidates() -> Self {
        Self {
            allow_level0_to_level1_local: true,
            ..Self::default()
        }
    }

    /// Check whether a claim-boundary transition is allowed in Phase J.
    pub fn check_escalation(
        &self,
        from: ClaimBoundary,
        to: ClaimBoundary,
    ) -> ClaimBoundaryEscalationGuardResult {
        let mut blocking_reasons = Vec::new();
        if to >= ClaimBoundary::Level2ReproducibleBenchmarkArtifact && self.block_level2_plus_actual
        {
            blocking_reasons.push("Level2+ actual evidence is blocked in Phase J".to_string());
        }
        if to >= ClaimBoundary::Level4FormalPropertyStatement && self.block_formal_levels {
            blocking_reasons.push("formal evidence levels are blocked in Phase J".to_string());
        }
        if from == ClaimBoundary::Level0DesignNote
            && to == ClaimBoundary::Level1LocalReplay
            && !self.allow_level0_to_level1_local
        {
            blocking_reasons.push(
                "Level0 to Level1 escalation requires explicit local-only policy".to_string(),
            );
        }
        if from > to {
            blocking_reasons
                .push("claim boundary downgrade should use explicit supersession".to_string());
        }
        ClaimBoundaryEscalationGuardResult {
            allowed: blocking_reasons.is_empty(),
            from,
            to,
            blocking_reasons,
        }
    }
}

/// Result of an escalation guard check.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ClaimBoundaryEscalationGuardResult {
    /// Whether the transition is allowed.
    pub allowed: bool,
    /// Source boundary.
    pub from: ClaimBoundary,
    /// Target boundary.
    pub to: ClaimBoundary,
    /// Blocking reasons.
    pub blocking_reasons: Vec<String>,
}

/// Check a claim-boundary escalation with the default guard.
pub fn guard_claim_boundary_escalation(
    from: ClaimBoundary,
    to: ClaimBoundary,
    allow_level1_local: bool,
) -> Result<ClaimBoundaryEscalationGuardResult> {
    let guard = if allow_level1_local {
        ClaimBoundaryEscalationGuard::allowing_level1_local_candidates()
    } else {
        ClaimBoundaryEscalationGuard::default()
    };
    let result = guard.check_escalation(from, to);
    if result.allowed {
        Ok(result)
    } else {
        Err(ZkBenchError::evidence_acceptance_policy(
            "claim_boundary_escalation_guard",
            format!(
                "claim boundary escalation blocked: {:?}",
                result.blocking_reasons
            ),
        ))
    }
}
