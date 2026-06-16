#![forbid(unsafe_code)]
//! The distinct-agent distinctness envelope.
//!
//! A [`DistinctnessEnvelope`] starts *open*: it carries the open assumption that
//! a measurement/nonce pair binds to a single distinct agent instance. That open
//! assumption is exactly [`Anchor::validity_assumption`] — the envelope does not
//! mint its own.
//!
//! The envelope is *closed* by discharging it with a [`Guarantee`] that rests on
//! the same assumption and anchors to [`Anchor::trust_root`]. Because the
//! attestation lane grants guarantees built from the very same anchor constants,
//! a verified attestation discharges this envelope exactly — and a withheld
//! outcome (which carries no guarantee) cannot.
//!
//! [`DistinctnessEnvelope::require_closed`] is the admission guard: downstream
//! consumers call it to obtain the discharging trust root, and it fails while the
//! envelope is still open.

use hsai_core::{Anchor, Guarantee, TrustRoot, ValidityAssumption};
use thiserror::Error;

/// Why an envelope could not be closed or admitted.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum EnvelopeError {
    /// The envelope is still open: nothing has discharged its assumption.
    #[error("distinctness envelope is open: assumption not discharged")]
    Open,

    /// The discharging guarantee rests on a different assumption.
    #[error("guarantee assumption does not match the envelope's open assumption")]
    AssumptionMismatch,

    /// The discharging guarantee anchors to a different trust root.
    #[error("guarantee trust root does not match the anchor trust root")]
    TrustRootMismatch,
}

/// An assumption that a measurement/nonce pair binds to a single distinct agent,
/// open until discharged by a matching guarantee.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DistinctnessEnvelope {
    open_assumption: ValidityAssumption,
    discharged_by: Option<TrustRoot>,
}

impl DistinctnessEnvelope {
    /// Open a fresh envelope carrying the anchor's open assumption verbatim.
    pub fn open() -> Self {
        Self {
            open_assumption: Anchor::validity_assumption(),
            discharged_by: None,
        }
    }

    /// The open assumption this envelope is waiting to have discharged.
    pub fn open_assumption(&self) -> &ValidityAssumption {
        &self.open_assumption
    }

    /// True once a matching guarantee has discharged the assumption.
    pub fn is_closed(&self) -> bool {
        self.discharged_by.is_some()
    }

    /// Discharge the envelope with `guarantee`.
    ///
    /// Succeeds only when the guarantee rests on this envelope's open assumption
    /// and anchors to [`Anchor::trust_root`]. A guarantee that matches closes the
    /// envelope; anything else leaves it open and returns an error.
    pub fn discharge(&mut self, guarantee: &Guarantee) -> Result<(), EnvelopeError> {
        if guarantee.assumption() != &self.open_assumption {
            return Err(EnvelopeError::AssumptionMismatch);
        }
        if guarantee.trust_root() != &Anchor::trust_root() {
            return Err(EnvelopeError::TrustRootMismatch);
        }
        self.discharged_by = Some(guarantee.trust_root().clone());
        Ok(())
    }

    /// Admission guard: return the discharging trust root, or [`EnvelopeError::Open`]
    /// while the envelope is still open.
    pub fn require_closed(&self) -> Result<&TrustRoot, EnvelopeError> {
        self.discharged_by.as_ref().ok_or(EnvelopeError::Open)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn opens_with_anchor_assumption() {
        let env = DistinctnessEnvelope::open();
        assert_eq!(env.open_assumption(), &Anchor::validity_assumption());
        assert!(!env.is_closed());
        assert_eq!(env.require_closed(), Err(EnvelopeError::Open));
    }

    #[test]
    fn matching_guarantee_closes_envelope() {
        let mut env = DistinctnessEnvelope::open();
        let g = Guarantee::attested(Anchor::validity_assumption(), Anchor::trust_root());
        assert_eq!(env.discharge(&g), Ok(()));
        assert!(env.is_closed());
        assert_eq!(env.require_closed(), Ok(&Anchor::trust_root()));
    }

    #[test]
    fn foreign_assumption_does_not_close() {
        let mut env = DistinctnessEnvelope::open();
        let g = Guarantee::attested(
            ValidityAssumption::new("other", "unrelated"),
            Anchor::trust_root(),
        );
        assert_eq!(env.discharge(&g), Err(EnvelopeError::AssumptionMismatch));
        assert!(!env.is_closed());
    }
}
