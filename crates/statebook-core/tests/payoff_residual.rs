use serde_json::{json, Value};
use statebook_core::{
    analyze_terminal_residual_v1, derive_state_key, parse_normalization_profile_v1,
    parse_source_contract_v1, quantize_exact, validate_and_lower, ContractPositionV1,
    DeclaredStateDomainV1, DeclaredTerminalStateV1, ExactError, PayoffAnalysisError,
    PayoffCompletenessStatusV1, RoundingMode, SemanticField, SignedRational,
    StateEvaluationStatusV1, UnmodeledResidualClassV1, UnsupportedStateReasonV1, ValidatedContract,
    ValidatedNormalizationProfileV1, MAX_DECLARED_STATES_V1, MAX_PORTFOLIO_LEGS_V1,
};

const BASELINE: &[u8] = include_bytes!("fixtures/terminal_contract_baseline_v1.json");
const PROFILE: &[u8] = include_bytes!("fixtures/normalization_profile_v1.json");
const VECTORS: &str = include_str!("fixtures/payoff_residual_vectors_v1.json");
const USD: &str = "fixture.asset.USD";
const USDC: &str = "fixture.asset.USDC";

fn rational(numerator: i128, denominator: u128) -> SignedRational {
    SignedRational::new(numerator, denominator).unwrap()
}

fn profile() -> ValidatedNormalizationProfileV1 {
    parse_normalization_profile_v1(PROFILE).unwrap()
}

fn contract_with(update: impl FnOnce(&mut Value)) -> ValidatedContract {
    let mut value: Value = serde_json::from_slice(BASELINE).unwrap();
    update(&mut value);
    let bytes = serde_json::to_vec(&value).unwrap();
    validate_and_lower(parse_source_contract_v1(&bytes).unwrap(), &profile()).unwrap()
}

fn baseline_contract() -> ValidatedContract {
    validate_and_lower(parse_source_contract_v1(BASELINE).unwrap(), &profile()).unwrap()
}

fn comparator_contract(kind: &str) -> ValidatedContract {
    contract_with(|source| source["payoff"]["comparator"]["kind"] = json!(kind))
}

fn range_contract(endpoints: &str) -> ValidatedContract {
    contract_with(|source| {
        source["payoff"]["comparator"] = json!({
            "kind": "in_range",
            "lower": {"numerator":"100000","denominator":"1"},
            "upper": {"numerator":"100001","denominator":"1"},
            "endpoints": endpoints
        });
    })
}

fn state(id: impl Into<String>, numerator: i128) -> DeclaredTerminalStateV1 {
    DeclaredTerminalStateV1::try_new(id, rational(numerator, 1)).unwrap()
}

fn three_state_domain(order: &[usize]) -> DeclaredStateDomainV1 {
    let states = [
        state("below", 99_999),
        state("equal", 100_000),
        state("above", 100_001),
    ];
    DeclaredStateDomainV1::try_new(order.iter().map(|index| states[*index].clone())).unwrap()
}

fn position(
    contract: &ValidatedContract,
    numerator: i128,
    denominator: u128,
) -> ContractPositionV1<'_> {
    ContractPositionV1::new(contract, rational(numerator, denominator))
}

fn state_residual<'a>(
    report: &'a statebook_core::PayoffCompletenessReportV1,
    state_id: &str,
) -> &'a statebook_core::StateResidualV1 {
    report
        .states()
        .iter()
        .find(|state| state.state_id() == state_id)
        .unwrap()
}

#[test]
fn exact_arithmetic_and_quantization_are_checked_and_canonical() {
    let half = rational(1, 2);
    let third = rational(1, 3);
    assert_eq!(half.checked_add(third).unwrap(), rational(5, 6));
    assert_eq!(half.checked_sub(third).unwrap(), rational(1, 6));
    assert_eq!(half.checked_mul(third).unwrap(), rational(1, 6));
    assert_eq!(half.checked_div(third).unwrap(), rational(3, 2));
    assert_eq!(half.checked_neg().unwrap(), rational(-1, 2));
    assert_eq!(rational(-1, 2).checked_abs().unwrap(), half);
    assert!(rational(0, 7).is_zero());
    assert_eq!(rational(0, 7), rational(0, 1));
    assert_eq!(
        rational(i128::MAX, 2)
            .checked_mul(rational(2, i128::MAX as u128))
            .unwrap(),
        rational(1, 1)
    );
    assert_eq!(
        rational(1, 1).checked_div(rational(0, 1)),
        Err(ExactError::ZeroDenominator)
    );
    assert!(rational(i128::MAX, 1).checked_add(rational(1, 1)).is_err());
    assert!(rational(i128::MIN, 1).checked_neg().is_err());
    assert_eq!(
        rational(i128::MIN, 1)
            .checked_sub(rational(i128::MIN, 1))
            .unwrap(),
        rational(0, 1)
    );
    assert_eq!(
        rational(i128::MIN, 1).checked_sub(rational(0, 1)).unwrap(),
        rational(i128::MIN, 1)
    );
    assert!(rational(0, 1).checked_sub(rational(i128::MIN, 1)).is_err());
    assert!(rational(i128::MAX, 1).checked_sub(rational(-1, 1)).is_err());

    let quantum = rational(1, 100);
    for (value, mode, expected) in [
        (rational(1, 200), RoundingMode::TowardZero, rational(0, 1)),
        (rational(1, 200), RoundingMode::Floor, rational(0, 1)),
        (rational(1, 200), RoundingMode::Ceiling, quantum),
        (rational(1, 200), RoundingMode::HalfEven, rational(0, 1)),
        (rational(3, 200), RoundingMode::HalfEven, rational(1, 50)),
        (rational(-1, 200), RoundingMode::TowardZero, rational(0, 1)),
        (rational(-1, 200), RoundingMode::Floor, rational(-1, 100)),
        (rational(-1, 200), RoundingMode::Ceiling, rational(0, 1)),
        (rational(-1, 200), RoundingMode::HalfEven, rational(0, 1)),
        (rational(-3, 200), RoundingMode::HalfEven, rational(-1, 50)),
    ] {
        assert_eq!(quantize_exact(value, quantum, mode).unwrap(), expected);
    }
    assert_eq!(
        quantize_exact(rational(1, 2), rational(0, 1), RoundingMode::Floor),
        Err(ExactError::NonPositiveQuantum)
    );
}

#[test]
fn frozen_decompositions_and_boundary_residual_match_the_vectors() {
    let vectors: Value = serde_json::from_str(VECTORS).unwrap();
    let target = baseline_contract();
    let equal = comparator_contract("equal");
    let greater = comparator_contract("greater_than");
    let domain = three_state_domain(&[0, 1, 2]);

    assert_eq!(
        derive_state_key(&target).state_key().to_hex(),
        vectors["baseline"]["p1_state_key_sha256"].as_str().unwrap()
    );
    assert_eq!(
        domain.digest().to_hex(),
        vectors["declared_domain"]["digest_sha256"]
            .as_str()
            .unwrap()
    );
    let exact = analyze_terminal_residual_v1(
        position(&target, 1, 1),
        &[position(&equal, 1, 1), position(&greater, 1, 1)],
        &domain,
    )
    .unwrap();
    assert_eq!(
        exact.status(),
        PayoffCompletenessStatusV1::ExactOnDeclaredDomain
    );
    assert!(exact
        .states()
        .iter()
        .all(|state| state.residual_by_asset().is_empty()));
    assert_eq!(exact.worst_case_by_asset().len(), 1);
    assert_eq!(exact.worst_case_by_asset()[0].asset(), USD);
    assert_eq!(
        exact.worst_case_by_asset()[0].absolute_amount(),
        rational(0, 1)
    );
    assert_eq!(
        exact.worst_case_by_asset()[0].state_ids(),
        &std::collections::BTreeSet::from([
            "above".to_owned(),
            "below".to_owned(),
            "equal".to_owned()
        ])
    );

    let approximate = analyze_terminal_residual_v1(
        position(&target, 1, 1),
        &[position(&greater, 1, 1)],
        &domain,
    )
    .unwrap();
    assert_eq!(
        approximate.status(),
        PayoffCompletenessStatusV1::ApproximateOnDeclaredDomain
    );
    assert_eq!(
        state_residual(&approximate, "equal").residual_by_asset()[USD],
        rational(1, 1)
    );
    assert!(state_residual(&approximate, "below")
        .residual_by_asset()
        .is_empty());
    assert!(state_residual(&approximate, "above")
        .residual_by_asset()
        .is_empty());
    assert_eq!(approximate.worst_case_by_asset().len(), 1);
    assert_eq!(approximate.worst_case_by_asset()[0].asset(), USD);
    assert_eq!(
        approximate.worst_case_by_asset()[0].absolute_amount(),
        rational(1, 1)
    );
    assert_eq!(
        approximate.worst_case_by_asset()[0].state_ids(),
        &std::collections::BTreeSet::from(["equal".to_owned()])
    );
}

#[test]
fn duplicate_split_signed_and_additive_inverse_portfolios_are_invariant() {
    let target = baseline_contract();
    let converged_lineage = contract_with(|_| {});
    let equal = comparator_contract("equal");
    let greater = comparator_contract("greater_than");
    let domain = three_state_domain(&[0, 1, 2]);
    let duplicate = analyze_terminal_residual_v1(
        position(&target, 1, 1),
        &[position(&target, 1, 2), position(&converged_lineage, 1, 2)],
        &domain,
    )
    .unwrap();
    assert_eq!(
        duplicate.status(),
        PayoffCompletenessStatusV1::ExactOnDeclaredDomain
    );
    assert_eq!(duplicate.candidate().len(), 1);
    assert_eq!(duplicate.candidate()[0].quantity(), rational(1, 1));
    assert_eq!(
        duplicate.candidate()[0].validated_contract_digests().len(),
        2
    );

    let signed = analyze_terminal_residual_v1(
        position(&equal, 1, 1),
        &[position(&target, 1, 1), position(&greater, -1, 1)],
        &domain,
    )
    .unwrap();
    assert_eq!(
        signed.status(),
        PayoffCompletenessStatusV1::ExactOnDeclaredDomain
    );

    let baseline = analyze_terminal_residual_v1(position(&target, 1, 1), &[], &domain).unwrap();
    let cancellation = analyze_terminal_residual_v1(
        position(&target, 1, 1),
        &[position(&greater, 5, 7), position(&greater, -5, 7)],
        &domain,
    )
    .unwrap();
    assert_eq!(baseline, cancellation);
}

#[test]
fn assets_never_net_implicitly_and_coordinate_mismatch_has_no_partial_residual() {
    let target = baseline_contract();
    let usdc = contract_with(|source| source["settlement"]["asset"] = json!(USDC));
    let mismatch =
        contract_with(|source| source["economic_reference"]["identifier"] = json!("ETH-USD"));
    let domain = three_state_domain(&[0, 1, 2]);

    let asset_report =
        analyze_terminal_residual_v1(position(&target, 1, 1), &[position(&usdc, 1, 1)], &domain)
            .unwrap();
    assert_eq!(
        asset_report.status(),
        PayoffCompletenessStatusV1::ApproximateOnDeclaredDomain
    );
    for state_id in ["equal", "above"] {
        let residual = state_residual(&asset_report, state_id).residual_by_asset();
        assert_eq!(residual[USD], rational(1, 1));
        assert_eq!(residual[USDC], rational(-1, 1));
    }
    assert!(asset_report
        .unmodeled_residual_classes()
        .contains(&UnmodeledResidualClassV1::FxConversion));

    let incomplete = analyze_terminal_residual_v1(
        position(&target, 1, 1),
        &[position(&mismatch, 1, 1)],
        &domain,
    )
    .unwrap();
    assert_eq!(incomplete.status(), PayoffCompletenessStatusV1::Incomplete);
    assert!(incomplete.worst_case_by_asset().is_empty());
    for state in incomplete.states() {
        assert!(state.residual_by_asset().is_empty());
        match state.status() {
            StateEvaluationStatusV1::Unsupported { reasons } => assert!(reasons.iter().any(
                |reason| matches!(reason, UnsupportedStateReasonV1::ObservationCoordinateMismatch { differing_fields, .. } if differing_fields == &std::collections::BTreeSet::from([SemanticField::ReferenceIdentifier]))
            )),
            StateEvaluationStatusV1::Evaluated => panic!("coordinate mismatch evaluated"),
        }
    }
}

#[test]
fn comparator_and_range_endpoint_boundaries_are_exhaustive() {
    let domain = three_state_domain(&[0, 1, 2]);
    for (kind, expected) in [
        ("less_than", [true, false, false]),
        ("less_than_or_equal", [true, true, false]),
        ("equal", [false, true, false]),
        ("greater_than_or_equal", [false, true, true]),
        ("greater_than", [false, false, true]),
    ] {
        let contract = comparator_contract(kind);
        let report = analyze_terminal_residual_v1(position(&contract, 1, 1), &[], &domain).unwrap();
        for (state_id, expected) in ["below", "equal", "above"].into_iter().zip(expected) {
            assert_eq!(
                !state_residual(&report, state_id)
                    .residual_by_asset()
                    .is_empty(),
                expected,
                "{kind}"
            );
        }
    }

    let range_domain = DeclaredStateDomainV1::try_new([
        DeclaredTerminalStateV1::try_new("lower", rational(100_000, 1)).unwrap(),
        DeclaredTerminalStateV1::try_new("inside", rational(200_001, 2)).unwrap(),
        DeclaredTerminalStateV1::try_new("upper", rational(100_001, 1)).unwrap(),
    ])
    .unwrap();
    for (endpoints, expected) in [
        ("open_open", [false, true, false]),
        ("open_closed", [false, true, true]),
        ("closed_open", [true, true, false]),
        ("closed_closed", [true, true, true]),
    ] {
        let contract = range_contract(endpoints);
        let report =
            analyze_terminal_residual_v1(position(&contract, 1, 1), &[], &range_domain).unwrap();
        for (state_id, expected) in ["lower", "inside", "upper"].into_iter().zip(expected) {
            assert_eq!(
                !state_residual(&report, state_id)
                    .residual_by_asset()
                    .is_empty(),
                expected,
                "{endpoints}"
            );
        }
    }
}

#[test]
fn ordering_bounds_and_domain_identity_are_deterministic() {
    let target = baseline_contract();
    let equal = comparator_contract("equal");
    let greater = comparator_contract("greater_than");
    let first_domain = three_state_domain(&[0, 1, 2]);
    let second_domain = three_state_domain(&[2, 0, 1]);
    assert_eq!(first_domain, second_domain);

    let first = analyze_terminal_residual_v1(
        position(&target, 1, 1),
        &[position(&equal, 1, 1), position(&greater, 1, 1)],
        &first_domain,
    )
    .unwrap();
    let second = analyze_terminal_residual_v1(
        position(&target, 1, 1),
        &[position(&greater, 1, 1), position(&equal, 1, 1)],
        &second_domain,
    )
    .unwrap();
    assert_eq!(first, second);

    let maximum_states = DeclaredStateDomainV1::try_new(
        (0..MAX_DECLARED_STATES_V1).map(|index| state(format!("s{index:03}"), index as i128)),
    )
    .unwrap();
    assert_eq!(maximum_states.len(), MAX_DECLARED_STATES_V1);
    let maximum_report =
        analyze_terminal_residual_v1(position(&target, 1, 1), &[], &maximum_states).unwrap();
    assert_eq!(maximum_report.states().len(), MAX_DECLARED_STATES_V1);
    assert!(maximum_report
        .states()
        .iter()
        .all(|state| matches!(state.status(), StateEvaluationStatusV1::Evaluated)));
    assert!(matches!(
        DeclaredStateDomainV1::try_new(
            (0..=MAX_DECLARED_STATES_V1).map(|index| state(format!("s{index:03}"), index as i128))
        ),
        Err(PayoffAnalysisError::TooManyStates { .. })
    ));
    assert!(matches!(
        DeclaredStateDomainV1::try_new(Vec::new()),
        Err(PayoffAnalysisError::EmptyStateDomain)
    ));
    assert!(DeclaredTerminalStateV1::try_new("bad state", rational(0, 1)).is_err());
    assert!(DeclaredStateDomainV1::try_new([state("same", 1), state("same", 2)]).is_err());

    let pulls = std::rc::Rc::new(std::cell::Cell::new(0_usize));
    let observed_pulls = std::rc::Rc::clone(&pulls);
    let guarded = std::iter::from_fn(move || {
        let next = observed_pulls.get() + 1;
        assert!(next <= MAX_DECLARED_STATES_V1 + 1, "iterator over-pulled");
        observed_pulls.set(next);
        Some(state(format!("guarded-{next:03}"), next as i128))
    });
    assert!(matches!(
        DeclaredStateDomainV1::try_new(guarded),
        Err(PayoffAnalysisError::TooManyStates {
            actual: 257,
            maximum: 256
        })
    ));
    assert_eq!(pulls.get(), MAX_DECLARED_STATES_V1 + 1);

    let sixty_four: Vec<_> = (0..MAX_PORTFOLIO_LEGS_V1)
        .map(|_| position(&target, 1, 64))
        .collect();
    assert_eq!(
        analyze_terminal_residual_v1(position(&target, 1, 1), &sixty_four, &first_domain)
            .unwrap()
            .status(),
        PayoffCompletenessStatusV1::ExactOnDeclaredDomain
    );
    let sixty_five: Vec<_> = (0..=MAX_PORTFOLIO_LEGS_V1)
        .map(|_| position(&target, 1, 65))
        .collect();
    assert!(matches!(
        analyze_terminal_residual_v1(position(&target, 1, 1), &sixty_five, &first_domain),
        Err(PayoffAnalysisError::TooManyPortfolioLegs { .. })
    ));
}

#[test]
fn same_state_key_aggregation_is_exact_and_permutation_invariant_at_sign_edges() {
    let contract = baseline_contract();
    let domain = three_state_domain(&[0, 1, 2]);
    let permutations = [
        [0_usize, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
    ];

    for (values, expected) in [
        (
            [rational(i128::MAX, 1), rational(1, 1), rational(-1, 1)],
            rational(i128::MAX, 1),
        ),
        (
            [rational(i128::MIN, 1), rational(-1, 1), rational(1, 1)],
            rational(i128::MIN, 1),
        ),
        (
            [rational(1, 2), rational(1, 3), rational(-2, 3)],
            rational(1, 6),
        ),
        (
            [
                rational(1, u128::MAX),
                rational(-1, u128::MAX),
                rational(i128::MAX, 1),
            ],
            rational(i128::MAX, 1),
        ),
    ] {
        let mut reference = None;
        for order in permutations {
            let candidate: Vec<_> = order
                .iter()
                .map(|index| ContractPositionV1::new(&contract, values[*index]))
                .collect();
            let report = analyze_terminal_residual_v1(
                ContractPositionV1::new(&contract, expected),
                &candidate,
                &domain,
            )
            .unwrap();
            assert_eq!(
                report.status(),
                PayoffCompletenessStatusV1::ExactOnDeclaredDomain
            );
            assert_eq!(report.candidate()[0].quantity(), expected);
            if let Some(reference) = &reference {
                assert_eq!(reference, &report);
            } else {
                reference = Some(report);
            }
        }
    }

    for values in [
        [rational(i128::MAX, 1), rational(1, 1)],
        [rational(i128::MIN, 1), rational(-1, 1)],
        [rational(1, u128::MAX), rational(1, u128::MAX - 1)],
    ] {
        let mut reference = None;
        for order in [[0_usize, 1], [1, 0]] {
            let candidate: Vec<_> = order
                .iter()
                .map(|index| ContractPositionV1::new(&contract, values[*index]))
                .collect();
            let report =
                analyze_terminal_residual_v1(position(&contract, 0, 1), &candidate, &domain)
                    .unwrap();
            assert_eq!(report.status(), PayoffCompletenessStatusV1::Incomplete);
            assert!(report
                .states()
                .iter()
                .all(|state| state.residual_by_asset().is_empty()));
            if let Some(reference) = &reference {
                assert_eq!(reference, &report);
            } else {
                reference = Some(report);
            }
        }
    }
}

#[test]
fn rounding_precedes_quantity_and_report_level_overflow_attribution_is_truthful() {
    let rounded = contract_with(|source| {
        source["payoff"]["amount"] = json!({"numerator":"1","denominator":"2"});
        source["settlement"]["rounding_mode"] = json!("ceiling");
    });
    let baseline = baseline_contract();
    let equal = comparator_contract("equal");
    let domain = three_state_domain(&[0, 1, 2]);

    let rounding_report =
        analyze_terminal_residual_v1(position(&rounded, 1, 2), &[], &domain).unwrap();
    assert_eq!(
        state_residual(&rounding_report, "equal").residual_by_asset()[USD],
        rational(1, 200)
    );

    let comparison_report = analyze_terminal_residual_v1(
        position(&baseline, 0, 1),
        &[position(&baseline, i128::MAX, 1), position(&equal, 1, 1)],
        &domain,
    )
    .unwrap();
    assert_eq!(
        comparison_report.status(),
        PayoffCompletenessStatusV1::Incomplete
    );
    assert!(comparison_report.worst_case_by_asset().is_empty());
    for state in comparison_report.states() {
        assert!(state.residual_by_asset().is_empty());
        match state.status() {
            StateEvaluationStatusV1::Unsupported { reasons } => assert_eq!(
                reasons,
                &std::collections::BTreeSet::from([
                    UnsupportedStateReasonV1::ResidualComparisonOverflow {
                        asset: USD.to_owned()
                    }
                ])
            ),
            StateEvaluationStatusV1::Evaluated => panic!("comparison overflow evaluated"),
        }
    }
}

#[test]
fn aggregation_overflow_reason_retains_every_contributing_lineage_digest() {
    let first = contract_with(|source| source["source_revision"] = json!("overflow-a"));
    let second = contract_with(|source| source["source_revision"] = json!("overflow-b"));
    let third = contract_with(|source| source["source_revision"] = json!("overflow-c"));
    let domain = three_state_domain(&[0, 1, 2]);
    let report = analyze_terminal_residual_v1(
        position(&first, 0, 1),
        &[
            position(&first, i128::MAX, 1),
            position(&second, 1, 1),
            position(&third, 0, 1),
        ],
        &domain,
    )
    .unwrap();
    assert_eq!(report.status(), PayoffCompletenessStatusV1::Incomplete);
    match report.states()[0].status() {
        StateEvaluationStatusV1::Unsupported { reasons } => {
            let digests = reasons
                .iter()
                .find_map(|reason| match reason {
                    UnsupportedStateReasonV1::PortfolioAggregationOverflow {
                        validated_contract_digests,
                        ..
                    } => Some(validated_contract_digests),
                    _ => None,
                })
                .expect("aggregation overflow reason");
            assert_eq!(digests.len(), 3);
        }
        StateEvaluationStatusV1::Evaluated => panic!("aggregation overflow evaluated"),
    }
}

#[test]
fn arithmetic_failure_paths_are_typed_incomplete_and_never_partial() {
    let target = baseline_contract();
    let domain = three_state_domain(&[0, 1, 2]);

    let aggregation = analyze_terminal_residual_v1(
        position(&target, 1, 1),
        &[position(&target, i128::MAX, 1), position(&target, 1, 1)],
        &domain,
    )
    .unwrap();
    assert_eq!(aggregation.status(), PayoffCompletenessStatusV1::Incomplete);
    assert!(aggregation
        .states()
        .iter()
        .all(|state| state.residual_by_asset().is_empty()));
    assert!(aggregation.worst_case_by_asset().is_empty());

    let payout_two = contract_with(|source| {
        source["payoff"]["amount"] = json!({"numerator":"200","denominator":"1"})
    });
    let multiplication =
        analyze_terminal_residual_v1(position(&payout_two, i128::MAX, 1), &[], &domain).unwrap();
    assert_eq!(
        multiplication.status(),
        PayoffCompletenessStatusV1::Incomplete
    );
    assert!(multiplication
        .states()
        .iter()
        .all(|state| state.residual_by_asset().is_empty()));
    assert!(multiplication.worst_case_by_asset().is_empty());

    let denominator = contract_with(|source| {
        source["payoff"]["amount"] = json!({
            "numerator":"1",
            "denominator":u128::MAX.to_string()
        })
    });
    let denominator_report =
        analyze_terminal_residual_v1(position(&denominator, 1, 1), &[], &domain).unwrap();
    assert_eq!(
        denominator_report.status(),
        PayoffCompletenessStatusV1::Incomplete
    );
    assert!(denominator_report
        .states()
        .iter()
        .all(|state| state.residual_by_asset().is_empty()));
    assert!(denominator_report.worst_case_by_asset().is_empty());

    let quantization = contract_with(|source| {
        source["payoff"]["amount"] = json!({"numerator":i128::MAX.to_string(),"denominator":"1"});
        source["settlement"]["unit_scale"] = json!("1");
        source["settlement"]["rounding_quantum"] = json!("0.000000000000000001");
    });
    let quantization_report =
        analyze_terminal_residual_v1(position(&quantization, 1, 1), &[], &domain).unwrap();
    assert_eq!(
        quantization_report.status(),
        PayoffCompletenessStatusV1::Incomplete
    );
    assert!(quantization_report
        .states()
        .iter()
        .all(|state| state.residual_by_asset().is_empty()));
    assert!(quantization_report.worst_case_by_asset().is_empty());
}

#[test]
fn bounded_reference_arithmetic_agrees_with_exact_operations() {
    for left_numerator in -8_i128..=8 {
        for left_denominator in 1_u128..=8 {
            for right_numerator in -8_i128..=8 {
                for right_denominator in 1_u128..=8 {
                    let left = rational(left_numerator, left_denominator);
                    let right = rational(right_numerator, right_denominator);
                    let reference_add_numerator = left_numerator * right_denominator as i128
                        + right_numerator * left_denominator as i128;
                    let reference_add_denominator = left_denominator * right_denominator;
                    assert_eq!(
                        left.checked_add(right).unwrap(),
                        rational(reference_add_numerator, reference_add_denominator)
                    );
                    let reference_sub_numerator = left_numerator * right_denominator as i128
                        - right_numerator * left_denominator as i128;
                    assert_eq!(
                        left.checked_sub(right).unwrap(),
                        rational(reference_sub_numerator, reference_add_denominator)
                    );
                    let reference_mul_numerator = left_numerator * right_numerator;
                    let reference_mul_denominator = left_denominator * right_denominator;
                    assert_eq!(
                        left.checked_mul(right).unwrap(),
                        rational(reference_mul_numerator, reference_mul_denominator)
                    );
                }
            }
        }
    }
}
