use core::cmp::Ordering;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use thiserror::Error;

pub const MAX_DECIMAL_SCALE_V1: u8 = 18;

#[derive(Clone, Debug, Eq, Error, PartialEq)]
pub enum ExactError {
    #[error("exact value is empty")]
    Empty,
    #[error("invalid exact decimal syntax")]
    InvalidSyntax,
    #[error("non-canonical signed zero")]
    NegativeZero,
    #[error("decimal scale {0} exceeds V1 maximum")]
    ScaleExceeded(usize),
    #[error("exact arithmetic overflow")]
    Overflow,
    #[error("rational denominator is zero")]
    ZeroDenominator,
    #[error("rounding quantum must be strictly positive")]
    NonPositiveQuantum,
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq, Serialize)]
pub struct ScaledInteger {
    coefficient: i128,
    scale: u8,
}

impl ScaledInteger {
    pub fn parse(value: &str) -> Result<Self, ExactError> {
        if value.is_empty() {
            return Err(ExactError::Empty);
        }
        if value.starts_with('+') || value.contains(['e', 'E']) || value.trim() != value {
            return Err(ExactError::InvalidSyntax);
        }

        let negative = value.starts_with('-');
        let unsigned = value.strip_prefix('-').unwrap_or(value);
        let (whole, fraction) = match unsigned.split_once('.') {
            Some((whole, fraction)) => (whole, fraction),
            None => (unsigned, ""),
        };
        if whole.is_empty()
            || !whole.bytes().all(|byte| byte.is_ascii_digit())
            || !fraction.bytes().all(|byte| byte.is_ascii_digit())
            || (unsigned.contains('.') && fraction.is_empty())
            || unsigned.matches('.').count() > 1
            || (whole.len() > 1 && whole.starts_with('0'))
        {
            return Err(ExactError::InvalidSyntax);
        }
        if fraction.len() > usize::from(MAX_DECIMAL_SCALE_V1) {
            return Err(ExactError::ScaleExceeded(fraction.len()));
        }
        if negative && whole == "0" && fraction.bytes().all(|byte| byte == b'0') {
            return Err(ExactError::NegativeZero);
        }

        let trimmed_fraction = fraction.trim_end_matches('0');
        let scale = u8::try_from(trimmed_fraction.len()).map_err(|_| ExactError::Overflow)?;
        let digits = if trimmed_fraction.is_empty() {
            whole.to_owned()
        } else {
            format!("{whole}{trimmed_fraction}")
        };
        let magnitude = digits.parse::<u128>().map_err(|_| ExactError::Overflow)?;
        let coefficient = signed_from_magnitude(magnitude, negative)?;
        Ok(Self { coefficient, scale })
    }

    pub const fn coefficient(self) -> i128 {
        self.coefficient
    }

    pub const fn scale(self) -> u8 {
        self.scale
    }

    pub fn checked_add(self, rhs: Self) -> Result<Self, ExactError> {
        let scale = self.scale.max(rhs.scale);
        let lhs = scale_coefficient(self.coefficient, scale - self.scale)?;
        let rhs = scale_coefficient(rhs.coefficient, scale - rhs.scale)?;
        normalize_scaled(lhs.checked_add(rhs).ok_or(ExactError::Overflow)?, scale)
    }

    pub fn checked_mul(self, rhs: Self) -> Result<Self, ExactError> {
        let scale = self
            .scale
            .checked_add(rhs.scale)
            .ok_or(ExactError::Overflow)?;
        let normalized = normalize_scaled(
            self.coefficient
                .checked_mul(rhs.coefficient)
                .ok_or(ExactError::Overflow)?,
            scale,
        )?;
        if normalized.scale > MAX_DECIMAL_SCALE_V1 {
            return Err(ExactError::ScaleExceeded(usize::from(normalized.scale)));
        }
        Ok(normalized)
    }
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq, Serialize)]
pub struct SignedRational {
    numerator: i128,
    denominator: u128,
}

impl SignedRational {
    pub fn new(numerator: i128, denominator: u128) -> Result<Self, ExactError> {
        if denominator == 0 {
            return Err(ExactError::ZeroDenominator);
        }
        if numerator == 0 {
            return Ok(Self {
                numerator: 0,
                denominator: 1,
            });
        }
        let divisor = gcd(numerator.unsigned_abs(), denominator);
        let magnitude = numerator.unsigned_abs() / divisor;
        let numerator = signed_from_magnitude(magnitude, numerator.is_negative())?;
        Ok(Self {
            numerator,
            denominator: denominator / divisor,
        })
    }

    pub fn parse(numerator: &str, denominator: &str) -> Result<Self, ExactError> {
        if numerator.starts_with('+')
            || denominator.starts_with(['+', '-'])
            || numerator.trim() != numerator
            || denominator.trim() != denominator
            || numerator.contains(['.', 'e', 'E'])
            || denominator.contains(['.', 'e', 'E'])
            || numerator == "-0"
            || has_leading_zero(numerator)
            || has_leading_zero(denominator)
        {
            return Err(ExactError::InvalidSyntax);
        }
        let numerator = numerator
            .parse::<i128>()
            .map_err(|_| ExactError::Overflow)?;
        let denominator = denominator
            .parse::<u128>()
            .map_err(|_| ExactError::Overflow)?;
        Self::new(numerator, denominator)
    }

    pub const fn numerator(self) -> i128 {
        self.numerator
    }

    pub const fn denominator(self) -> u128 {
        self.denominator
    }

    pub const fn is_zero(self) -> bool {
        self.numerator == 0
    }

    pub fn checked_neg(self) -> Result<Self, ExactError> {
        Self::new(
            self.numerator.checked_neg().ok_or(ExactError::Overflow)?,
            self.denominator,
        )
    }

    pub fn checked_abs(self) -> Result<Self, ExactError> {
        if self.numerator.is_negative() {
            self.checked_neg()
        } else {
            Ok(self)
        }
    }

    pub fn checked_add(self, rhs: Self) -> Result<Self, ExactError> {
        let rhs_denominator = rhs.denominator;
        let shared = gcd(self.denominator, rhs_denominator);
        let lhs_factor = rhs_denominator / shared;
        let rhs_factor = self.denominator / shared;
        let lhs_factor = i128::try_from(lhs_factor).map_err(|_| ExactError::Overflow)?;
        let rhs_factor = i128::try_from(rhs_factor).map_err(|_| ExactError::Overflow)?;
        let lhs = self
            .numerator
            .checked_mul(lhs_factor)
            .ok_or(ExactError::Overflow)?;
        let rhs = rhs
            .numerator
            .checked_mul(rhs_factor)
            .ok_or(ExactError::Overflow)?;
        let numerator = lhs.checked_add(rhs).ok_or(ExactError::Overflow)?;
        let final_cancel = gcd(numerator.unsigned_abs(), shared);
        let numerator = signed_from_magnitude(
            numerator.unsigned_abs() / final_cancel,
            numerator.is_negative(),
        )?;
        let denominator = (self.denominator / shared)
            .checked_mul(rhs_denominator / final_cancel)
            .ok_or(ExactError::Overflow)?;
        Self::new(numerator, denominator)
    }

    pub fn checked_sub(self, rhs: Self) -> Result<Self, ExactError> {
        let rhs_denominator = rhs.denominator;
        let shared = gcd(self.denominator, rhs_denominator);
        let lhs_factor =
            i128::try_from(rhs_denominator / shared).map_err(|_| ExactError::Overflow)?;
        let rhs_factor =
            i128::try_from(self.denominator / shared).map_err(|_| ExactError::Overflow)?;
        let lhs = self
            .numerator
            .checked_mul(lhs_factor)
            .ok_or(ExactError::Overflow)?;
        let rhs = rhs
            .numerator
            .checked_mul(rhs_factor)
            .ok_or(ExactError::Overflow)?;
        let numerator = lhs.checked_sub(rhs).ok_or(ExactError::Overflow)?;
        let final_cancel = gcd(numerator.unsigned_abs(), shared);
        let numerator = signed_from_magnitude(
            numerator.unsigned_abs() / final_cancel,
            numerator.is_negative(),
        )?;
        let denominator = (self.denominator / shared)
            .checked_mul(rhs_denominator / final_cancel)
            .ok_or(ExactError::Overflow)?;
        Self::new(numerator, denominator)
    }

    pub fn checked_mul(self, rhs: Self) -> Result<Self, ExactError> {
        if self.is_zero() || rhs.is_zero() {
            return Self::new(0, 1);
        }
        let left_cancel = gcd(self.numerator.unsigned_abs(), rhs.denominator);
        let right_cancel = gcd(rhs.numerator.unsigned_abs(), self.denominator);
        let left = signed_from_magnitude(
            self.numerator.unsigned_abs() / left_cancel,
            self.numerator.is_negative(),
        )?;
        let right = signed_from_magnitude(
            rhs.numerator.unsigned_abs() / right_cancel,
            rhs.numerator.is_negative(),
        )?;
        let numerator = left.checked_mul(right).ok_or(ExactError::Overflow)?;
        let denominator = (self.denominator / right_cancel)
            .checked_mul(rhs.denominator / left_cancel)
            .ok_or(ExactError::Overflow)?;
        Self::new(numerator, denominator)
    }

    pub fn checked_div(self, rhs: Self) -> Result<Self, ExactError> {
        if rhs.is_zero() {
            return Err(ExactError::ZeroDenominator);
        }
        if self.is_zero() {
            return Self::new(0, 1);
        }
        let numerator_cancel = gcd(self.numerator.unsigned_abs(), rhs.numerator.unsigned_abs());
        let denominator_cancel = gcd(rhs.denominator, self.denominator);
        let magnitude = (self.numerator.unsigned_abs() / numerator_cancel)
            .checked_mul(rhs.denominator / denominator_cancel)
            .ok_or(ExactError::Overflow)?;
        let numerator = signed_from_magnitude(
            magnitude,
            self.numerator.is_negative() != rhs.numerator.is_negative(),
        )?;
        let denominator = (self.denominator / denominator_cancel)
            .checked_mul(rhs.numerator.unsigned_abs() / numerator_cancel)
            .ok_or(ExactError::Overflow)?;
        Self::new(numerator, denominator)
    }

    pub fn from_scaled(value: ScaledInteger) -> Result<Self, ExactError> {
        let denominator = 10_u128
            .checked_pow(u32::from(value.scale()))
            .ok_or(ExactError::Overflow)?;
        Self::new(value.coefficient(), denominator)
    }

    pub fn checked_cmp(self, rhs: Self) -> Result<Ordering, ExactError> {
        let lhs = self
            .numerator
            .checked_mul(i128::try_from(rhs.denominator).map_err(|_| ExactError::Overflow)?)
            .ok_or(ExactError::Overflow)?;
        let rhs = rhs
            .numerator
            .checked_mul(i128::try_from(self.denominator).map_err(|_| ExactError::Overflow)?)
            .ok_or(ExactError::Overflow)?;
        Ok(lhs.cmp(&rhs))
    }
}

pub fn quantize_exact(
    value: SignedRational,
    quantum: SignedRational,
    mode: crate::RoundingMode,
) -> Result<SignedRational, ExactError> {
    if quantum.numerator() <= 0 {
        return Err(ExactError::NonPositiveQuantum);
    }
    let units = value.checked_div(quantum)?;
    let magnitude = units.numerator().unsigned_abs();
    let denominator = units.denominator();
    let quotient = magnitude / denominator;
    let remainder = magnitude % denominator;
    let increment = match mode {
        crate::RoundingMode::TowardZero => false,
        crate::RoundingMode::Floor => units.numerator().is_negative() && remainder != 0,
        crate::RoundingMode::Ceiling => !units.numerator().is_negative() && remainder != 0,
        crate::RoundingMode::HalfEven => match remainder.cmp(&(denominator - remainder)) {
            Ordering::Less => false,
            Ordering::Greater => true,
            Ordering::Equal => quotient % 2 == 1,
        },
    };
    let rounded_magnitude = if increment {
        quotient.checked_add(1).ok_or(ExactError::Overflow)?
    } else {
        quotient
    };
    let rounded = signed_from_magnitude(rounded_magnitude, units.numerator().is_negative())?;
    SignedRational::new(rounded, 1)?.checked_mul(quantum)
}

pub(crate) fn sum_rationals_canonical(
    values: &[SignedRational],
) -> Result<SignedRational, ExactError> {
    let mut counts: BTreeMap<(u128, u128), (usize, usize)> = BTreeMap::new();
    for value in values.iter().filter(|value| !value.is_zero()) {
        let entry = counts
            .entry((value.denominator(), value.numerator().unsigned_abs()))
            .or_default();
        if value.numerator().is_negative() {
            entry.1 += 1;
        } else {
            entry.0 += 1;
        }
    }

    let mut remaining = Vec::with_capacity(values.len());
    for ((denominator, magnitude), (positive, negative)) in counts {
        let (count, is_negative) = if positive >= negative {
            (positive - negative, false)
        } else {
            (negative - positive, true)
        };
        let numerator = signed_from_magnitude(magnitude, is_negative)?;
        remaining
            .extend(std::iter::repeat(SignedRational::new(numerator, denominator)?).take(count));
    }
    remaining.sort_by_key(|value| {
        (
            value.denominator(),
            value.numerator().unsigned_abs(),
            value.numerator().is_negative(),
        )
    });

    let mut values = remaining.into_iter();
    let Some(mut total) = values.next() else {
        return SignedRational::new(0, 1);
    };
    for value in values {
        total = total.checked_add(value)?;
    }
    Ok(total)
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct RationalInput {
    pub numerator: String,
    pub denominator: String,
}

fn normalize_scaled(mut coefficient: i128, mut scale: u8) -> Result<ScaledInteger, ExactError> {
    if coefficient == 0 {
        return Ok(ScaledInteger {
            coefficient: 0,
            scale: 0,
        });
    }
    while scale > 0 && coefficient % 10 == 0 {
        coefficient /= 10;
        scale -= 1;
    }
    Ok(ScaledInteger { coefficient, scale })
}

fn scale_coefficient(value: i128, places: u8) -> Result<i128, ExactError> {
    let factor = 10_i128
        .checked_pow(u32::from(places))
        .ok_or(ExactError::Overflow)?;
    value.checked_mul(factor).ok_or(ExactError::Overflow)
}

fn signed_from_magnitude(magnitude: u128, negative: bool) -> Result<i128, ExactError> {
    if negative {
        if magnitude == (1_u128 << 127) {
            return Ok(i128::MIN);
        }
        let value = i128::try_from(magnitude).map_err(|_| ExactError::Overflow)?;
        value.checked_neg().ok_or(ExactError::Overflow)
    } else {
        i128::try_from(magnitude).map_err(|_| ExactError::Overflow)
    }
}

fn has_leading_zero(value: &str) -> bool {
    let unsigned = value.strip_prefix('-').unwrap_or(value);
    unsigned.len() > 1 && unsigned.starts_with('0')
}

fn gcd(mut left: u128, mut right: u128) -> u128 {
    while right != 0 {
        let remainder = left % right;
        left = right;
        right = remainder;
    }
    left
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn decimals_and_rationals_normalize_without_float() {
        assert_eq!(
            ScaledInteger::parse("10.5000").unwrap(),
            ScaledInteger {
                coefficient: 105,
                scale: 1
            }
        );
        assert_eq!(
            ScaledInteger::parse("0.000").unwrap(),
            ScaledInteger {
                coefficient: 0,
                scale: 0
            }
        );
        assert_eq!(
            SignedRational::new(2, 4).unwrap(),
            SignedRational::new(1, 2).unwrap()
        );
        assert_eq!(
            SignedRational::new(i128::MIN, 1_u128 << 127).unwrap(),
            SignedRational::new(-1, 1).unwrap()
        );
        assert_eq!(
            ScaledInteger::parse("0.000000000000000002")
                .unwrap()
                .checked_mul(ScaledInteger::parse("0.5").unwrap())
                .unwrap(),
            ScaledInteger::parse("0.000000000000000001").unwrap()
        );
        assert_eq!(
            ScaledInteger::parse("0.000000000000000001")
                .unwrap()
                .scale(),
            MAX_DECIMAL_SCALE_V1
        );
    }

    #[test]
    fn invalid_and_overflowing_values_fail_closed() {
        for value in ["", "+1", "-0", "01", "1e2", " 1", "1.", "1.2.3"] {
            assert!(ScaledInteger::parse(value).is_err(), "{value}");
        }
        assert_eq!(SignedRational::new(1, 0), Err(ExactError::ZeroDenominator));
        assert!(ScaledInteger::parse("0.0000000000000000001").is_err());
        assert!(SignedRational::parse("170141183460469231731687303715884105728", "1").is_err());
        assert!(SignedRational::parse("1", "340282366920938463463374607431768211456").is_err());
        assert!(
            ScaledInteger::parse("170141183460469231731687303715884105727")
                .unwrap()
                .checked_add(ScaledInteger::parse("1").unwrap())
                .is_err()
        );
        assert!(ScaledInteger::parse("99999999999999999999")
            .unwrap()
            .checked_mul(ScaledInteger::parse("99999999999999999999").unwrap())
            .is_err());
        for (numerator, denominator) in [
            ("+1", "1"),
            ("01", "1"),
            ("-0", "1"),
            ("1.0", "1"),
            ("1e2", "1"),
            ("1", "-1"),
            ("1", "01"),
        ] {
            assert!(SignedRational::parse(numerator, denominator).is_err());
        }
    }
}
