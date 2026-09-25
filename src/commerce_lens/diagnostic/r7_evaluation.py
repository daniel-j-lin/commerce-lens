"""Policy-only mapping from validated R7 evidence to frozen R2 outcomes."""

from commerce_lens.contracts.diagnostic import AnalyticalOutcome


def map_r7_outcome(rho: float | None, inconclusive_reasons: tuple[str, ...] = ()) -> AnalyticalOutcome:
    if rho is None or inconclusive_reasons:
        return AnalyticalOutcome.NOT_EVALUATED
    if rho <= -0.50:
        return AnalyticalOutcome.CRITERION_MET
    if rho >= 0.50:
        return AnalyticalOutcome.PROPOSITION_CONTRADICTED
    return AnalyticalOutcome.CRITERION_NOT_MET
