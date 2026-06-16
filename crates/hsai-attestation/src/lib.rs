#![forbid(unsafe_code)]
//! The attestation verification lane (L4 data lane).
//!
//! This lane consumes a managed attestation [`Token`] and, if it checks out,
//! grants an [`Attested`](hsai_core::GuaranteeLevel::Attested) guarantee that
//! reuses [`Anchor::validity_assumption`] and [`Anchor::trust_root`] verbatim.
//! Because the guarantee rests on the anchor's open assumption, it discharges
//! the distinct-agent distinctness envelope exactly.
//!
//! # What the reference verifier checks
//!
//! [`ManagedTokenVerifier`] checks three things:
//!
//! 1. **nonce** — the token's nonce equals the expected nonce;
//! 2. **measurements** — the token's measurement set equals the expected set;
//! 3. **freshness** — the token is not expired at the verification time, and the
//!    verification time lies inside the intersection of the token's validity
//!    window, the verifier's accepted windows, and the case's accepted windows.
//!
//! # What it does NOT check (honesty boundary)
//!
//! The reference verifier does **not** verify the managed service's signature
//! over the token. That signature check is the deferred real step — the point
//! where this stack would stop trusting pure data and start trusting
//! cryptography. Until it is implemented:
//!
//! - a verified attestation is [`Attested`](hsai_core::GuaranteeLevel::Attested),
//!   never [`Proven`](hsai_core::GuaranteeLevel::Proven);
//! - [`VerifiedAttestation::signature_verified`] is always `false`;
//! - the guarantee is only as strong as [`Anchor::validity_assumption`], which
//!   states in prose that the binding is *assumed*, not proven.
//!
//! A rejected input adds no guarantee and no trust root: the lane returns
//! [`LaneOutcome::Withheld`]. Expired tokens never verify.

use hsai_agent_case::{Case, TimeWindow};
use hsai_core::{Anchor, EvidenceLane, Guarantee, GuaranteeLevel, LaneOutcome, TrustRoot};
use thiserror::Error;

/// The lane identifier reported by [`EvidenceLane::lane_id`].
pub const ATTESTATION_LANE_ID: &str = "hsai.lane.attestation";

/// A challenge nonce binding a token to a verification round.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Nonce(Vec<u8>);

impl Nonce {
    /// Wrap raw nonce bytes.
    pub fn new(bytes: impl Into<Vec<u8>>) -> Self {
        Self(bytes.into())
    }

    /// The nonce bytes.
    pub fn as_bytes(&self) -> &[u8] {
        &self.0
    }
}

/// The ordered set of platform measurements a token reports.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Measurements(Vec<Vec<u8>>);

impl Measurements {
    /// Wrap a list of measurement digests.
    pub fn new(values: impl Into<Vec<Vec<u8>>>) -> Self {
        Self(values.into())
    }

    /// The measurement digests.
    pub fn values(&self) -> &[Vec<u8>] {
        &self.0
    }
}

/// The managed service's signature over the token.
///
/// The reference verifier carries this through but does **not** check it. It is
/// kept on the token so the deferred real verifier has something to verify.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ManagedSignature(Vec<u8>);

impl ManagedSignature {
    /// Wrap raw signature bytes.
    pub fn new(bytes: impl Into<Vec<u8>>) -> Self {
        Self(bytes.into())
    }

    /// The signature bytes (never inspected by the reference verifier).
    pub fn as_bytes(&self) -> &[u8] {
        &self.0
    }
}

/// A managed attestation token: pure data until a verifier accepts it.
///
/// `issued_at..expires_at` is the token's validity window (half-open). A token
/// is expired at time `t` when `t >= expires_at`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Token {
    /// The managed service that issued the token.
    pub managed_service: String,
    /// The challenge nonce the token answers.
    pub nonce: Nonce,
    /// The platform measurements the token reports.
    pub measurements: Measurements,
    /// Inclusive start of the token's validity window.
    pub issued_at: u64,
    /// Exclusive end of the token's validity window (the token expires here).
    pub expires_at: u64,
    /// The managed service signature. Not verified by the reference backend.
    pub signature: ManagedSignature,
}

/// A token the verifier accepted.
///
/// Carries the granted guarantee (always [`Attested`](GuaranteeLevel::Attested)),
/// the verification time, the accepted-window intersection it fell inside, and an
/// honest `signature_verified` flag that the reference backend always leaves
/// `false`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedAttestation {
    guarantee: Guarantee,
    verified_at: u64,
    accepted_window: TimeWindow,
    signature_verified: bool,
}

impl VerifiedAttestation {
    /// The granted guarantee. Always at [`GuaranteeLevel::Attested`].
    pub fn guarantee(&self) -> &Guarantee {
        &self.guarantee
    }

    /// The trust root the guarantee anchors to ([`Anchor::trust_root`]).
    pub fn trust_root(&self) -> &TrustRoot {
        self.guarantee.trust_root()
    }

    /// The strength of the granted guarantee. Always [`GuaranteeLevel::Attested`].
    pub fn level(&self) -> GuaranteeLevel {
        self.guarantee.level()
    }

    /// The verification time used (the case's `observed_at`).
    pub fn verified_at(&self) -> u64 {
        self.verified_at
    }

    /// The accepted-window intersection the verification time fell inside.
    pub fn accepted_window(&self) -> &TimeWindow {
        &self.accepted_window
    }

    /// Whether the managed service signature was cryptographically verified.
    ///
    /// The reference backend always returns `false`: signature verification is
    /// the deferred real step.
    pub fn signature_verified(&self) -> bool {
        self.signature_verified
    }
}

/// Why a token failed verification.
///
/// Every variant means the lane grants nothing: no guarantee, no trust root.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum VerifyError {
    /// The token's nonce did not match the expected nonce.
    #[error("nonce mismatch")]
    NonceMismatch,

    /// The token's measurements did not match the expected measurements.
    #[error("measurement mismatch")]
    MeasurementMismatch,

    /// The token was expired at the verification time.
    #[error("token expired: expires_at={expires_at}, observed_at={observed_at}")]
    Expired {
        /// The token's expiry.
        expires_at: u64,
        /// The verification time.
        observed_at: u64,
    },

    /// The accepted windows (verifier, case, and token validity) had no overlap.
    #[error("accepted windows do not intersect")]
    EmptyAcceptedWindow,

    /// The verification time fell outside the accepted-window intersection.
    #[error("observed_at={observed_at} is outside the accepted window")]
    OutsideAcceptedWindow {
        /// The verification time.
        observed_at: u64,
    },
}

/// A backend that decides whether a [`Token`] verifies against a [`Case`].
pub trait AttestationVerifier {
    /// Verify `token` as observed by `case`, using `case.observed_at()` as the
    /// verification time. Returns a [`VerifiedAttestation`] on success.
    fn verify(&self, token: &Token, case: &Case) -> Result<VerifiedAttestation, VerifyError>;
}

/// The reference attestation backend.
///
/// Checks nonce, measurements, and freshness against fixed expectations. Does
/// **not** verify the managed service signature.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ManagedTokenVerifier {
    expected_nonce: Nonce,
    expected_measurements: Measurements,
    accepted_windows: Vec<TimeWindow>,
}

impl ManagedTokenVerifier {
    /// Construct a verifier expecting `expected_nonce` and `expected_measurements`,
    /// accepting verification times inside every window in `accepted_windows`
    /// (in addition to the token's own validity window and the case's windows).
    pub fn new(
        expected_nonce: Nonce,
        expected_measurements: Measurements,
        accepted_windows: Vec<TimeWindow>,
    ) -> Self {
        Self {
            expected_nonce,
            expected_measurements,
            accepted_windows,
        }
    }
}

impl AttestationVerifier for ManagedTokenVerifier {
    fn verify(&self, token: &Token, case: &Case) -> Result<VerifiedAttestation, VerifyError> {
        let observed_at = case.observed_at();

        // 1. Nonce.
        if token.nonce != self.expected_nonce {
            return Err(VerifyError::NonceMismatch);
        }

        // 2. Measurements.
        if token.measurements != self.expected_measurements {
            return Err(VerifyError::MeasurementMismatch);
        }

        // 3a. Freshness: expired tokens never verify.
        if observed_at >= token.expires_at {
            return Err(VerifyError::Expired {
                expires_at: token.expires_at,
                observed_at,
            });
        }

        // 3b. Freshness: intersect the token validity window with every accepted
        //     window (verifier-side and case-side). The verification time must
        //     fall inside the intersection.
        let token_window = TimeWindow::new(token.issued_at, token.expires_at)
            .ok_or(VerifyError::EmptyAcceptedWindow)?;
        let mut accepted = token_window;
        for window in self.accepted_windows.iter().chain(case.accepted_windows()) {
            accepted = accepted
                .intersect(window)
                .ok_or(VerifyError::EmptyAcceptedWindow)?;
        }
        if !accepted.contains(observed_at) {
            return Err(VerifyError::OutsideAcceptedWindow { observed_at });
        }

        // DEFERRED REAL STEP: the managed service signature (`token.signature`)
        // is not verified here. The guarantee below is Attested, not Proven, and
        // `signature_verified` stays false to record that the stack has not yet
        // left pure-data.
        Ok(VerifiedAttestation {
            guarantee: Guarantee::attested(Anchor::validity_assumption(), Anchor::trust_root()),
            verified_at: observed_at,
            accepted_window: accepted,
            signature_verified: false,
        })
    }
}

/// The attestation evidence lane, parameterized over a verifier backend.
///
/// Implements [`EvidenceLane`]: a verified token yields
/// [`LaneOutcome::Granted`] with an `Attested` guarantee; a rejected token
/// yields [`LaneOutcome::Withheld`] (no guarantee, no trust root).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AttestationLane<V> {
    verifier: V,
}

impl<V: AttestationVerifier> AttestationLane<V> {
    /// Wrap a verifier backend in the attestation lane.
    pub fn new(verifier: V) -> Self {
        Self { verifier }
    }

    /// Borrow the underlying verifier.
    pub fn verifier(&self) -> &V {
        &self.verifier
    }

    /// Run verification directly, exposing the full [`VerifiedAttestation`] on
    /// success. [`EvidenceLane::assess`] is the guarantee-only view of this.
    pub fn verify(&self, case: &Case, token: &Token) -> Result<VerifiedAttestation, VerifyError> {
        self.verifier.verify(token, case)
    }
}

impl<V: AttestationVerifier> EvidenceLane for AttestationLane<V> {
    type Case = Case;
    type Evidence = Token;

    fn lane_id(&self) -> &'static str {
        ATTESTATION_LANE_ID
    }

    fn assess(&self, case: &Self::Case, evidence: &Self::Evidence) -> LaneOutcome {
        match self.verifier.verify(evidence, case) {
            Ok(verified) => LaneOutcome::Granted(verified.guarantee),
            Err(_) => LaneOutcome::Withheld,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hsai_distinct_agent::DistinctnessEnvelope;

    fn nonce() -> Nonce {
        Nonce::new(vec![1, 2, 3, 4])
    }

    fn measurements() -> Measurements {
        Measurements::new(vec![vec![0xaa, 0xbb], vec![0xcc]])
    }

    /// A verifier expecting the fixtures above, accepting any time inside the
    /// token window (no extra verifier-side window restriction).
    fn verifier() -> ManagedTokenVerifier {
        ManagedTokenVerifier::new(nonce(), measurements(), Vec::new())
    }

    /// A well-formed token valid over `[100, 200)`.
    fn good_token() -> Token {
        Token {
            managed_service: "managed.example".into(),
            nonce: nonce(),
            measurements: measurements(),
            issued_at: 100,
            expires_at: 200,
            signature: ManagedSignature::new(vec![0xde, 0xad]),
        }
    }

    // AT-1: a well-formed, in-window token verifies and grants an Attested
    // guarantee that reuses Anchor::validity_assumption and Anchor::trust_root
    // verbatim.
    #[test]
    fn at_1_valid_token_verifies_and_reuses_anchor() {
        let lane = AttestationLane::new(verifier());
        let case = Case::at("at-1", 150);
        let verified = lane.verify(&case, &good_token()).expect("should verify");

        assert_eq!(verified.level(), GuaranteeLevel::Attested);
        assert_eq!(verified.verified_at(), 150);
        // Reused verbatim from the anchor.
        assert_eq!(
            verified.guarantee().assumption(),
            &Anchor::validity_assumption()
        );
        assert_eq!(verified.trust_root(), &Anchor::trust_root());

        // The lane view grants the same guarantee.
        let outcome = lane.assess(&case, &good_token());
        assert_eq!(
            outcome,
            LaneOutcome::Granted(Guarantee::attested(
                Anchor::validity_assumption(),
                Anchor::trust_root()
            ))
        );
    }

    // AT-2: a verified attestation discharges the distinct-agent distinctness
    // envelope, which is then admitted under require_closed.
    #[test]
    fn at_2_verified_attestation_closes_distinctness_envelope() {
        let lane = AttestationLane::new(verifier());
        let case = Case::at("at-2", 150);

        // The envelope starts open and is not admissible.
        let mut envelope = DistinctnessEnvelope::open();
        assert!(!envelope.is_closed());
        assert!(envelope.require_closed().is_err());

        // The lane grants a guarantee...
        let outcome = lane.assess(&case, &good_token());
        let guarantee = outcome.guarantee().expect("lane should grant");

        // ...which discharges the envelope exactly.
        envelope.discharge(guarantee).expect("should discharge");
        assert!(envelope.is_closed());

        // Now it is admitted, anchored to the same trust root.
        let trust_root = envelope.require_closed().expect("should be admitted");
        assert_eq!(trust_root, &Anchor::trust_root());
    }

    // AT-3: expired tokens never verify. The envelope stays open.
    #[test]
    fn at_3_expired_token_never_verifies() {
        let lane = AttestationLane::new(verifier());
        // observed_at == expires_at is already expired (half-open window).
        let case = Case::at("at-3", 200);
        let err = lane.verify(&case, &good_token()).unwrap_err();
        assert_eq!(
            err,
            VerifyError::Expired {
                expires_at: 200,
                observed_at: 200,
            }
        );

        // Lane withholds; an open envelope cannot be discharged by it.
        let outcome = lane.assess(&case, &good_token());
        assert_eq!(outcome, LaneOutcome::Withheld);
        assert!(outcome.guarantee().is_none());

        let envelope = DistinctnessEnvelope::open();
        assert!(envelope.require_closed().is_err());
        // Nothing to discharge with: withheld carries no guarantee.
        assert!(outcome.guarantee().is_none());
        assert!(!envelope.is_closed());
    }

    // AT-4: a rejected input adds no guarantee and no trust root.
    #[test]
    fn at_4_rejected_input_adds_no_guarantee_or_trust_root() {
        let lane = AttestationLane::new(verifier());
        let case = Case::at("at-4", 150);

        // Wrong nonce.
        let mut bad = good_token();
        bad.nonce = Nonce::new(vec![9, 9, 9]);
        assert_eq!(
            lane.verify(&case, &bad).unwrap_err(),
            VerifyError::NonceMismatch
        );
        let outcome = lane.assess(&case, &bad);
        assert_eq!(outcome, LaneOutcome::Withheld);
        assert!(outcome.guarantee().is_none());
        assert!(outcome.trust_root().is_none());

        // Wrong measurements.
        let mut bad = good_token();
        bad.measurements = Measurements::new(vec![vec![0x00]]);
        assert_eq!(
            lane.verify(&case, &bad).unwrap_err(),
            VerifyError::MeasurementMismatch
        );
        assert!(lane.assess(&case, &bad).trust_root().is_none());

        // A withheld outcome cannot discharge the distinctness envelope.
        let envelope = DistinctnessEnvelope::open();
        assert!(lane.assess(&case, &bad).guarantee().is_none());
        assert!(!envelope.is_closed());
        assert!(envelope.require_closed().is_err());
    }

    // AT-5: honesty — a verified attestation is Attested, never Proven, and the
    // managed service signature is never verified by the reference backend.
    #[test]
    fn at_5_attested_never_proven_signature_unverified() {
        let lane = AttestationLane::new(verifier());
        let case = Case::at("at-5", 150);
        let verified = lane.verify(&case, &good_token()).expect("should verify");

        assert_eq!(verified.level(), GuaranteeLevel::Attested);
        assert!(!verified.guarantee().is_proven());
        assert_ne!(verified.level(), GuaranteeLevel::Proven);
        // The deferred real step: signature is never checked.
        assert!(!verified.signature_verified());
    }

    // The accepted-window intersection rejects an in-validity but out-of-policy
    // observation, and an empty intersection is reported distinctly.
    #[test]
    fn accepted_window_intersection_is_enforced() {
        // Verifier only accepts [160, 170); token is valid [100, 200).
        let v = ManagedTokenVerifier::new(
            nonce(),
            measurements(),
            vec![TimeWindow::new(160, 170).unwrap()],
        );
        let lane = AttestationLane::new(v);

        // 150 is in the token window but outside the policy window.
        let case = Case::at("outside", 150);
        assert_eq!(
            lane.verify(&case, &good_token()).unwrap_err(),
            VerifyError::OutsideAcceptedWindow { observed_at: 150 }
        );

        // 165 is inside both.
        let case = Case::at("inside", 165);
        assert!(lane.verify(&case, &good_token()).is_ok());

        // A case window disjoint from the verifier window => empty intersection.
        let case = Case::new("disjoint", 165, vec![TimeWindow::new(100, 120).unwrap()]);
        assert_eq!(
            lane.verify(&case, &good_token()).unwrap_err(),
            VerifyError::EmptyAcceptedWindow
        );
    }
}
