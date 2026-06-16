#![forbid(unsafe_code)]
//! L0 foundation for the Hyper Sacred AI stack.
//!
//! This crate defines the shared vocabulary every evidence lane speaks:
//!
//! - [`Anchor`] — the single fixed point the whole stack hangs from. It exposes
//!   [`Anchor::validity_assumption`] (the open assumption guarantees rest on
//!   until something discharges it) and [`Anchor::trust_root`] (the root of
//!   trust a granted guarantee anchors to). Both are constants; lanes reuse them
//!   verbatim rather than minting their own, so a guarantee produced by one lane
//!   is comparable to an assumption left open by another.
//! - [`Guarantee`] / [`GuaranteeLevel`] — what a lane grants and how strong it
//!   is. The strongest level a *data* lane can reach is [`GuaranteeLevel::Attested`].
//!   [`GuaranteeLevel::Proven`] exists in the type but is never produced from
//!   pure-data evidence; it is reserved for a machine-checked proof lane.
//! - [`LaneOutcome`] — the result of asking a lane to assess a case. A granted
//!   outcome carries a guarantee (and therefore a trust root); a withheld
//!   outcome carries neither. A rejection adds no guarantee and no trust root.
//! - [`EvidenceLane`] — the contract every lane implements.
//!
//! Honesty boundary: a guarantee at [`GuaranteeLevel::Attested`] means "an
//! evidence lane accepted the data it was shown under a stated assumption." It
//! is not a proof. The assumption it rests on is exactly
//! [`Anchor::validity_assumption`], and it is only as good as that assumption.

/// The open assumption a guarantee rests on until it is discharged.
///
/// Two assumptions are equal when their `id`s are equal; the `statement` is
/// human-facing prose. Lanes must reuse [`Anchor::validity_assumption`] rather
/// than constructing assumptions with fresh ids, so that an assumption left
/// open by one lane can be recognized and discharged by another.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ValidityAssumption {
    id: String,
    statement: String,
}

impl ValidityAssumption {
    /// Construct an assumption from a stable id and a human-facing statement.
    pub fn new(id: impl Into<String>, statement: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            statement: statement.into(),
        }
    }

    /// Stable identity of the assumption.
    pub fn id(&self) -> &str {
        &self.id
    }

    /// Human-facing statement of what is being assumed.
    pub fn statement(&self) -> &str {
        &self.statement
    }
}

/// The root of trust a granted guarantee anchors to.
///
/// Equality is by `id`. A rejected input never yields a trust root.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct TrustRoot {
    id: String,
    description: String,
}

impl TrustRoot {
    /// Construct a trust root from a stable id and a human-facing description.
    pub fn new(id: impl Into<String>, description: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            description: description.into(),
        }
    }

    /// Stable identity of the trust root.
    pub fn id(&self) -> &str {
        &self.id
    }

    /// Human-facing description of the root of trust.
    pub fn description(&self) -> &str {
        &self.description
    }
}

/// The single fixed point the Hyper Sacred AI stack hangs from.
///
/// `Anchor` is a namespace, not a value: it exposes the canonical assumption and
/// trust root as constants. Every lane that grants a guarantee reuses these
/// verbatim so guarantees and open assumptions across lanes stay comparable.
pub struct Anchor;

impl Anchor {
    /// The canonical open assumption.
    ///
    /// The distinct-agent lane leaves this assumption open; the attestation lane
    /// reuses it verbatim in the guarantees it grants, so a verified attestation
    /// discharges exactly the distinct-agent open assumption — no more.
    pub fn validity_assumption() -> ValidityAssumption {
        ValidityAssumption::new(
            "hsai.anchor.distinct-agent.open",
            "The managed attestation service correctly bound this measurement set \
             and nonce to a single distinct agent instance. This binding is \
             assumed, not proven: the managed service signature is not verified \
             by the reference backend.",
        )
    }

    /// The canonical root of trust a granted guarantee anchors to.
    pub fn trust_root() -> TrustRoot {
        TrustRoot::new(
            "hsai.anchor.managed-attestation-root",
            "The managed attestation service acting as the root of trust for \
             measurement/nonce binding.",
        )
    }
}

/// How strong a guarantee is.
///
/// `Attested` is the ceiling for any lane that consumes pure data: the data was
/// accepted under [`Anchor::validity_assumption`]. `Proven` is strictly stronger
/// and is reserved for a machine-checked proof lane; no data lane ever produces
/// it.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum GuaranteeLevel {
    /// A data lane accepted the evidence under a stated, undischarged assumption.
    Attested,
    /// A machine-checked proof established the claim. Never produced by a data lane.
    Proven,
}

/// What a lane grants when it accepts evidence.
///
/// A guarantee always carries the assumption it rests on and the trust root it
/// anchors to. Construct guarantees via [`Guarantee::attested`]; there is no
/// constructor that yields [`GuaranteeLevel::Proven`] from this crate's data
/// path.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Guarantee {
    level: GuaranteeLevel,
    assumption: ValidityAssumption,
    trust_root: TrustRoot,
}

impl Guarantee {
    /// Construct an `Attested` guarantee resting on `assumption` and anchored to
    /// `trust_root`. This is the only guarantee constructor a data lane uses.
    pub fn attested(assumption: ValidityAssumption, trust_root: TrustRoot) -> Self {
        Self {
            level: GuaranteeLevel::Attested,
            assumption,
            trust_root,
        }
    }

    /// The strength of this guarantee.
    pub fn level(&self) -> GuaranteeLevel {
        self.level
    }

    /// True only for [`GuaranteeLevel::Proven`]. Always false for data lanes.
    pub fn is_proven(&self) -> bool {
        self.level == GuaranteeLevel::Proven
    }

    /// The assumption this guarantee rests on.
    pub fn assumption(&self) -> &ValidityAssumption {
        &self.assumption
    }

    /// The trust root this guarantee anchors to.
    pub fn trust_root(&self) -> &TrustRoot {
        &self.trust_root
    }
}

/// The result of asking a lane to assess a case.
///
/// `Granted` carries a guarantee (and therefore a trust root). `Withheld`
/// carries neither: a rejected input adds no guarantee and no trust root.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LaneOutcome {
    /// The lane accepted the evidence and grants this guarantee.
    Granted(Guarantee),
    /// The lane rejected the evidence. No guarantee, no trust root.
    Withheld,
}

impl LaneOutcome {
    /// True when the lane granted a guarantee.
    pub fn is_granted(&self) -> bool {
        matches!(self, LaneOutcome::Granted(_))
    }

    /// The granted guarantee, if any.
    pub fn guarantee(&self) -> Option<&Guarantee> {
        match self {
            LaneOutcome::Granted(g) => Some(g),
            LaneOutcome::Withheld => None,
        }
    }

    /// The granted trust root, if any. `None` for a withheld outcome.
    pub fn trust_root(&self) -> Option<&TrustRoot> {
        self.guarantee().map(Guarantee::trust_root)
    }
}

/// The contract every evidence lane implements.
///
/// A lane reads a case and a piece of evidence and returns a [`LaneOutcome`].
/// Lanes never panic on adversarial input; rejection is expressed as
/// [`LaneOutcome::Withheld`].
pub trait EvidenceLane {
    /// The case context a lane assesses against (carries the verification time).
    type Case;
    /// The evidence a lane consumes.
    type Evidence;

    /// Stable identifier for this lane.
    fn lane_id(&self) -> &'static str;

    /// Assess `evidence` against `case`, granting or withholding a guarantee.
    fn assess(&self, case: &Self::Case, evidence: &Self::Evidence) -> LaneOutcome;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn anchor_constants_are_stable() {
        assert_eq!(Anchor::validity_assumption(), Anchor::validity_assumption());
        assert_eq!(Anchor::trust_root(), Anchor::trust_root());
        assert_eq!(
            Anchor::validity_assumption().id(),
            "hsai.anchor.distinct-agent.open"
        );
        assert_eq!(
            Anchor::trust_root().id(),
            "hsai.anchor.managed-attestation-root"
        );
    }

    #[test]
    fn attested_guarantee_is_never_proven() {
        let g = Guarantee::attested(Anchor::validity_assumption(), Anchor::trust_root());
        assert_eq!(g.level(), GuaranteeLevel::Attested);
        assert!(!g.is_proven());
    }

    #[test]
    fn withheld_outcome_carries_no_guarantee_or_trust_root() {
        let outcome = LaneOutcome::Withheld;
        assert!(!outcome.is_granted());
        assert!(outcome.guarantee().is_none());
        assert!(outcome.trust_root().is_none());
    }
}
