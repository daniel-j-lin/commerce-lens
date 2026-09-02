from __future__ import annotations

from decimal import Decimal

from commerce_lens.contracts.common import ClaimState, MetricState
from commerce_lens.skill.public_response import PublicClaimProjection, PublicResponse


def test_public_response_separates_metric_state_claim_state_and_disposition() -> None:
    response = PublicResponse(
        supported_claims=(
            PublicClaimProjection(
                metric_ref="aov",
                metric_display_name="AOV",
                metric_state=MetricState.UNDEFINED,
                claim_state=ClaimState.ADMISSIBLE,
                public_disposition="supported_descriptive_state",
                value=None,
                undefined_reason="orders_equals_zero",
                period_label="Q4 2026",
            ),
        )
    )

    rendered = response.render_text()

    assert "Undefined" in rendered
    assert "Admissible" not in rendered
    assert response.supported_claims[0].metric_state is MetricState.UNDEFINED
    assert response.supported_claims[0].claim_state is ClaimState.ADMISSIBLE


def test_public_response_projection_performs_no_metric_arithmetic() -> None:
    response = PublicResponse(
        supported_claims=(
            PublicClaimProjection(
                metric_ref="revenue_change",
                metric_display_name="Revenue Change",
                metric_state=MetricState.VALID,
                claim_state=ClaimState.ADMISSIBLE,
                public_disposition="supported_descriptive_value",
                value=Decimal("20.00"),
                currency="USD",
                period_label="Q4 2026",
            ),
        )
    )

    rendered = response.render_text()

    assert "20.00 USD" in rendered
    assert "%" not in rendered
    assert "Recommendation" not in rendered
