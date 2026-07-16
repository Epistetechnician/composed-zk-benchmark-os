use statebook_core::SignedRational;

use super::types::{DecisionReasonV1, DirectionV1, ExternalizationRequestV1};

pub struct AmountValidation {
    pub reason: Option<DecisionReasonV1>,
}

pub fn validate_amount_before_valuation(
    request: &ExternalizationRequestV1,
) -> Result<SignedRational, AmountValidation> {
    let amount = request.total_amount();
    if amount.is_zero() {
        return Err(AmountValidation {
            reason: Some(DecisionReasonV1::AmountZero),
        });
    }
    if amount.numerator() < 0 {
        return Err(AmountValidation {
            reason: Some(DecisionReasonV1::AmountNegative),
        });
    }
    if request.direction() == DirectionV1::Inbound && amount.numerator() > 0 {
        return Err(AmountValidation {
            reason: Some(DecisionReasonV1::AmountWrongSign),
        });
    }
    if amount.denominator() == 0 {
        return Err(AmountValidation {
            reason: Some(DecisionReasonV1::AmountNoncanonical),
        });
    }
    amount
        .checked_mul(SignedRational::new(1, 1).unwrap())
        .map_err(|_| AmountValidation {
            reason: Some(DecisionReasonV1::AmountOverflow),
        })?;
    Ok(amount)
}
