use super::types::{ExternalizationRequestV1, FinancialBasisKindV1, ReleaseClassV1};

pub fn classify_release_class(request: &ExternalizationRequestV1) -> ReleaseClassV1 {
    let declared = request.declared_release_class();
    match declared {
        ReleaseClassV1::InternalRiskState => {
            if request.linked_plan().is_some() || request.obligation().is_some() {
                ReleaseClassV1::SystemicOrExceptional
            } else {
                ReleaseClassV1::InternalRiskState
            }
        }
        ReleaseClassV1::AtomicLinkedExchange => {
            if request.linked_plan().is_some() {
                ReleaseClassV1::AtomicLinkedExchange
            } else {
                ReleaseClassV1::SystemicOrExceptional
            }
        }
        ReleaseClassV1::ExternalRiskReducingObligation => {
            if request.obligation().is_some() {
                ReleaseClassV1::ExternalRiskReducingObligation
            } else {
                ReleaseClassV1::SystemicOrExceptional
            }
        }
        ReleaseClassV1::ExternalUnconditional => {
            if request.linked_plan().is_some()
                || request.obligation().is_some()
                || (request.financial_basis().kind() == FinancialBasisKindV1::ContractDerived
                    && request.financial_basis().composition_digest().is_none())
            {
                ReleaseClassV1::SystemicOrExceptional
            } else {
                ReleaseClassV1::ExternalUnconditional
            }
        }
        ReleaseClassV1::SystemicOrExceptional => ReleaseClassV1::SystemicOrExceptional,
    }
}
