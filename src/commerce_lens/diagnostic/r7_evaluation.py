"""Policy-only mapping from validated R7 evidence to frozen R2 outcomes."""

from commerce_lens.contracts.common import utc_now
from commerce_lens.contracts.diagnostic import AnalyticalOutcome
from commerce_lens.contracts.r7 import (
    DiagnosticExecutionRecord, DiagnosticTestRequest, DiagnosticValidationRecord,
    PostTestDiagnosticEvaluation, R7EvaluationState, ValidatedDiagnosticResult,
    posttest_evaluation_fingerprint,
)
from commerce_lens.evidence.identifiers import generate_id


def map_r7_outcome(rho: float | None, inconclusive_reasons: tuple[str, ...] = ()) -> AnalyticalOutcome:
    if rho is None or inconclusive_reasons:
        return AnalyticalOutcome.NOT_EVALUATED
    if rho <= -0.50:
        return AnalyticalOutcome.CRITERION_MET
    if rho >= 0.50:
        return AnalyticalOutcome.PROPOSITION_CONTRADICTED
    return AnalyticalOutcome.CRITERION_NOT_MET


def build_posttest_evaluation(*, request: DiagnosticTestRequest, execution: DiagnosticExecutionRecord,
                              validation: DiagnosticValidationRecord | None,
                              validated: ValidatedDiagnosticResult | None,
                              state: R7EvaluationState | None = None,
                              reason: str | None = None) -> PostTestDiagnosticEvaluation:
    if state is None:
        if validated is None:
            state = R7EvaluationState.VALIDATION_FAILED
        elif validated.inconclusive_reasons:
            state = R7EvaluationState.INCONCLUSIVE
        else:
            state = R7EvaluationState.VALIDATED_OUTCOME
    outcome = map_r7_outcome(validated.spearman_rho, validated.inconclusive_reasons) if validated else AnalyticalOutcome.NOT_EVALUATED
    data = dict(
        evaluation_event_id=generate_id("r7eval"), evaluation_fingerprint="0" * 64,
        diagnostic_proposition_ref=request.diagnostic_proposition_ref,
        diagnostic_proposition_fingerprint=request.diagnostic_proposition_fingerprint,
        pretest_evaluation_ref=request.pretest_evaluation_ref,
        pretest_evaluation_fingerprint=request.pretest_evaluation_fingerprint,
        handoff_ref=request.handoff_ref, handoff_fingerprint=request.handoff_fingerprint,
        test_request_ref=request.test_request_id, request_fingerprint=request.request_fingerprint,
        execution_event_ref=execution.execution_event_id,
        validation_event_ref=validation.validation_event_id if validation else "NOT_RUN",
        validated_result_ref=validated.validated_result_id if validated else None,
        method=request.method, support_criterion=request.support_criterion,
        evaluation_state=state,
        controlling_reason=reason or (validated.inconclusive_reasons[0] if validated and validated.inconclusive_reasons else "VALIDATED_DECISION_BOUNDARY_APPLIED"),
        analytical_outcome=outcome, finalized_at=utc_now(),
    )
    data["evaluation_fingerprint"] = posttest_evaluation_fingerprint(data)
    return PostTestDiagnosticEvaluation(**data)
