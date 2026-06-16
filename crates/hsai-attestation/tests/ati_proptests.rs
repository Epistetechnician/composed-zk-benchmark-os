//! Property invariants ATI-1..5 for the attestation verification lane.
//!
//! These hold for *all* inputs the strategies below can produce:
//!
//! - ATI-1: expired tokens never verify.
//! - ATI-2: a nonce mismatch is always rejected (never Ok).
//! - ATI-3: a measurement mismatch (with matching nonce) is always rejected.
//! - ATI-4: a rejected input adds no guarantee and no trust root; an accepted
//!   one always grants — verify-Err iff lane-Withheld.
//! - ATI-5: every verified attestation is Attested (never Proven), has an
//!   unverified signature, and reuses the anchor assumption and trust root
//!   verbatim, with `verified_at == observed_at` inside the accepted window.

use hsai_agent_case::{Case, TimeWindow};
use hsai_attestation::{
    AttestationLane, AttestationVerifier, ManagedSignature, ManagedTokenVerifier, Measurements,
    Nonce, Token, VerifyError,
};
use hsai_core::{Anchor, EvidenceLane, GuaranteeLevel, LaneOutcome};
use proptest::prelude::*;

fn bytes() -> impl Strategy<Value = Vec<u8>> {
    proptest::collection::vec(any::<u8>(), 0..6)
}

fn nonce_strat() -> impl Strategy<Value = Nonce> {
    bytes().prop_map(Nonce::new)
}

fn measurements_strat() -> impl Strategy<Value = Measurements> {
    proptest::collection::vec(bytes(), 0..4).prop_map(Measurements::new)
}

fn windows_strat() -> impl Strategy<Value = Vec<TimeWindow>> {
    proptest::collection::vec((0u64..60, 1u64..60), 0..3).prop_map(to_windows)
}

fn to_windows(raw: Vec<(u64, u64)>) -> Vec<TimeWindow> {
    raw.into_iter()
        .map(|(start, len)| TimeWindow::new(start, start + len).expect("len >= 1"))
        .collect()
}

prop_compose! {
    /// A fully arbitrary (verifier, token, case): the token's nonce/measurements
    /// independently either match the verifier's expectation or not, so the
    /// success and rejection paths are both exercised.
    fn scenario()(
        nonce in nonce_strat(),
        meas in measurements_strat(),
        match_nonce in any::<bool>(),
        match_meas in any::<bool>(),
        other_nonce in nonce_strat(),
        other_meas in measurements_strat(),
        issued in 0u64..50,
        dur in 1u64..50,
        observed in 0u64..120,
        sig in bytes(),
        vwins in windows_strat(),
        cwins in windows_strat(),
    ) -> (ManagedTokenVerifier, Token, Case) {
        let token_nonce = if match_nonce { nonce.clone() } else { other_nonce };
        let token_meas = if match_meas { meas.clone() } else { other_meas };
        let verifier = ManagedTokenVerifier::new(nonce, meas, vwins);
        let token = Token {
            managed_service: "managed.example".into(),
            nonce: token_nonce,
            measurements: token_meas,
            issued_at: issued,
            expires_at: issued + dur,
            signature: ManagedSignature::new(sig),
        };
        let case = Case::new("scenario", observed, cwins);
        (verifier, token, case)
    }
}

proptest! {
    // ATI-1: a token whose expiry is at or before the verification time never
    // verifies, even with the correct nonce and measurements.
    #[test]
    fn ati_1_expired_never_verifies(
        nonce in nonce_strat(),
        meas in measurements_strat(),
        issued in 0u64..50,
        dur in 1u64..50,
        extra in 0u64..50,
        sig in bytes(),
    ) {
        let expires = issued + dur;
        let observed = expires + extra; // observed >= expires
        let verifier = ManagedTokenVerifier::new(nonce.clone(), meas.clone(), Vec::new());
        let token = Token {
            managed_service: "managed.example".into(),
            nonce,
            measurements: meas,
            issued_at: issued,
            expires_at: expires,
            signature: ManagedSignature::new(sig),
        };
        let case = Case::at("expired", observed);

        let result = verifier.verify(&token, &case);
        prop_assert!(result.is_err());
        prop_assert_eq!(
            result.unwrap_err(),
            VerifyError::Expired { expires_at: expires, observed_at: observed }
        );

        let lane = AttestationLane::new(verifier);
        prop_assert_eq!(lane.assess(&case, &token), LaneOutcome::Withheld);
    }

    // ATI-2: a token whose nonce differs from the expected nonce is always
    // rejected with NonceMismatch and never grants.
    #[test]
    fn ati_2_nonce_mismatch_always_rejected(
        n in bytes(),
        meas in measurements_strat(),
        issued in 0u64..50,
        dur in 1u64..50,
        observed in 0u64..120,
        sig in bytes(),
        vwins in windows_strat(),
    ) {
        // Token nonce differs from expected by an extra byte (guaranteed unequal).
        let expected_nonce = Nonce::new(n.clone());
        let mut differing = n;
        differing.push(0xFF);
        let token_nonce = Nonce::new(differing);

        let verifier = ManagedTokenVerifier::new(expected_nonce, meas.clone(), vwins);
        let token = Token {
            managed_service: "managed.example".into(),
            nonce: token_nonce,
            measurements: meas,
            issued_at: issued,
            expires_at: issued + dur,
            signature: ManagedSignature::new(sig),
        };
        let case = Case::at("nonce", observed);

        prop_assert_eq!(verifier.verify(&token, &case).unwrap_err(), VerifyError::NonceMismatch);
        let lane = AttestationLane::new(verifier);
        prop_assert!(!lane.assess(&case, &token).is_granted());
    }

    // ATI-3: a token whose measurements differ (with a matching nonce) is always
    // rejected with MeasurementMismatch.
    #[test]
    fn ati_3_measurement_mismatch_always_rejected(
        nonce in nonce_strat(),
        m in proptest::collection::vec(bytes(), 0..4),
        issued in 0u64..50,
        dur in 1u64..50,
        observed in 0u64..120,
        sig in bytes(),
    ) {
        let expected_meas = Measurements::new(m.clone());
        let mut differing = m;
        differing.push(vec![0xFF]); // guaranteed unequal length/content
        let token_meas = Measurements::new(differing);

        let verifier = ManagedTokenVerifier::new(nonce.clone(), expected_meas, Vec::new());
        let token = Token {
            managed_service: "managed.example".into(),
            nonce,
            measurements: token_meas,
            issued_at: issued,
            expires_at: issued + dur,
            signature: ManagedSignature::new(sig),
        };
        let case = Case::at("meas", observed);

        prop_assert_eq!(
            verifier.verify(&token, &case).unwrap_err(),
            VerifyError::MeasurementMismatch
        );
        let lane = AttestationLane::new(verifier);
        prop_assert!(lane.assess(&case, &token).trust_root().is_none());
    }

    // ATI-4: rejection adds no guarantee and no trust root; acceptance grants.
    // The lane outcome is Withheld exactly when verification errs.
    #[test]
    fn ati_4_rejection_grants_nothing((verifier, token, case) in scenario()) {
        let result = verifier.verify(&token, &case);
        let lane = AttestationLane::new(verifier);
        let outcome = lane.assess(&case, &token);

        match result {
            Ok(_) => prop_assert!(outcome.is_granted()),
            Err(_) => {
                prop_assert_eq!(outcome.clone(), LaneOutcome::Withheld);
                prop_assert!(outcome.guarantee().is_none());
                prop_assert!(outcome.trust_root().is_none());
            }
        }
    }

    // ATI-5: every accepted token yields an Attested (never Proven) guarantee,
    // with an unverified signature, reusing the anchor constants verbatim, and
    // verified_at == observed_at inside the accepted window.
    #[test]
    fn ati_5_verified_is_attested_and_honest((verifier, token, case) in scenario()) {
        if let Ok(va) = verifier.verify(&token, &case) {
            prop_assert_eq!(va.level(), GuaranteeLevel::Attested);
            prop_assert!(!va.guarantee().is_proven());
            prop_assert_ne!(va.level(), GuaranteeLevel::Proven);
            prop_assert!(!va.signature_verified());
            prop_assert_eq!(va.guarantee().assumption(), &Anchor::validity_assumption());
            prop_assert_eq!(va.trust_root(), &Anchor::trust_root());
            prop_assert_eq!(va.verified_at(), case.observed_at());
            prop_assert!(va.accepted_window().contains(case.observed_at()));
        }
    }
}
