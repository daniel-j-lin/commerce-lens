"""Narrow Public v0.1 response projection."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import TYPE_CHECKING

from commerce_lens.contracts.common import ClaimState, ClaimType, MetricState, RunStatus
from commerce_lens.contracts.diagnostic import AnalyticalOutcome
from commerce_lens.contracts.evidence import AdmissibleEvidence, ClaimCandidate, ClaimDecision
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.results import AnalysisResult
from commerce_lens.contracts.validation import ValidatedResult
from commerce_lens.metrics import get_metric_registry
from commerce_lens.persistence.metadata_store import MetadataStore

if TYPE_CHECKING:
    from commerce_lens.persistence.r7_repository import CompleteR7Lineage
    from commerce_lens.skill.integration import PublicAnalysisIntent


@dataclass(frozen=True)
class EvaluatedClaimAuthority:
    candidate: ClaimCandidate
    decision: ClaimDecision
    validated_result: ValidatedResult
    evidence: AdmissibleEvidence


@dataclass(frozen=True)
class PublicClaimProjection:
    metric_ref: str
    metric_display_name: str
    metric_state: MetricState
    claim_state: ClaimState
    public_disposition: str
    value: object | None = None
    undefined_reason: str | None = None
    unit: str | None = None
    currency: str | None = None
    period_label: str | None = None
    period_role: str | None = None


@dataclass(frozen=True)
class PublicEvidenceSummary:
    metric_ref: str
    metric_display_name: str
    metric_definition_version: str | None
    period_label: str | None
    period_role: str | None
    metric_state: MetricState
    evidence_status: str
    claim_state: ClaimState
    source_filename: str | None
    source_type: str | None
    validation_status: str = "passed"


@dataclass(frozen=True)
class PublicMappingProposal:
    source_field: str
    canonical_field: str


@dataclass(frozen=True)
class PublicDiagnosticProjection:
    family_id: str
    method_id: str
    analytical_outcome: AnalyticalOutcome
    evaluation_state: str
    controlling_reason: str
    explanation: tuple[str, ...]


@dataclass(frozen=True)
class PublicResponse:
    supported_claims: tuple[PublicClaimProjection, ...] = ()
    evidence_summary: tuple[PublicEvidenceSummary, ...] = ()
    mapping_proposals: tuple[PublicMappingProposal, ...] = ()
    required_mapping_fields: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    unsupported_conclusions: tuple[str, ...] = ()
    additional_evidence_needed: tuple[str, ...] = ()
    clarification_required: tuple[str, ...] = ()
    blocked: bool = False
    insufficient_evidence_message: str | None = None
    coverage_provenance: tuple[dict, ...] = ()
    diagnostic_analysis: PublicDiagnosticProjection | None = None

    def render_text(self) -> str:
        if self.clarification_required:
            lines = ["Clarification required: " + "; ".join(self.clarification_required)]
            if self.mapping_proposals:
                lines.append("Proposed source-to-canonical mapping")
                lines.extend(
                    f"- {proposal.source_field} -> {proposal.canonical_field}"
                    for proposal in self.mapping_proposals
                )
            return "\n".join(lines)
        lines: list[str] = []
        if self.supported_claims:
            lines.append("Supported Claims / Answer")
            for claim in self.supported_claims:
                lines.append(f"- {_claim_sentence(claim)}")
        if self.diagnostic_analysis is not None:
            lines.append("Diagnostic Analysis")
            lines.extend(f"- {item}" for item in self.diagnostic_analysis.explanation)
        if self.unsupported_conclusions:
            lines.append("Unsupported Conclusions")
            lines.extend(f"- {item}" for item in self.unsupported_conclusions)
        if self.insufficient_evidence_message:
            lines.append(self.insufficient_evidence_message)
        if self.evidence_summary:
            lines.append("Evidence Summary")
            for item in self.evidence_summary:
                source = item.source_filename or "governed source"
                lines.append(
                    f"- {item.metric_display_name}; {item.period_label or item.period_role}; "
                    f"MetricState={item.metric_state.value}; ClaimState={item.claim_state.value}; source={source}"
                )
        if self.additional_evidence_needed:
            lines.append("Additional Evidence Needed")
            lines.extend(f"- {item}" for item in self.additional_evidence_needed)
        if self.limitations:
            lines.append("Limitations")
            lines.extend(f"- {item}" for item in self.limitations)
        if not lines:
            return "Insufficient evidence to conclude."
        return "\n".join(lines)


def with_public_diagnostic(
    response: PublicResponse,
    *,
    lineage: CompleteR7Lineage | None = None,
    blocker: str | None = None,
) -> PublicResponse:
    """Attach only recursively authenticated R7 lineage or a fail-closed blocker."""

    if lineage is None:
        if blocker is None:
            return response
        return replace(
            response,
            blocked=True,
            insufficient_evidence_message="Insufficient evidence to conclude.",
            additional_evidence_needed=tuple(
                dict.fromkeys((*response.additional_evidence_needed, blocker))
            ),
        )
    evaluation = lineage.evaluation
    return replace(
        response,
        diagnostic_analysis=PublicDiagnosticProjection(
            family_id=lineage.r6_handoff.family_id,
            method_id=lineage.request.method.authority_id,
            analytical_outcome=evaluation.analytical_outcome,
            evaluation_state=evaluation.evaluation_state.value,
            controlling_reason=evaluation.controlling_reason,
            explanation=_diagnostic_explanation(lineage),
        ),
    )


def _diagnostic_explanation(lineage: CompleteR7Lineage) -> tuple[str, ...]:
    outcome = lineage.evaluation.analytical_outcome
    if outcome is AnalyticalOutcome.CRITERION_MET:
        return (
            "The data shows a consistent relationship between larger product-mix changes and lower weekly revenue. Under the current CommerceLens test, product mix is supported as one possible explanation.",
            "This does not prove that product mix caused the decline or that it was the only or primary reason.",
        )
    if outcome is AnalyticalOutcome.CRITERION_NOT_MET:
        return (
            "The current product-mix test did not reach the support threshold, so the available data does not support product mix as an explanation under this method.",
        )
    if outcome is AnalyticalOutcome.PROPOSITION_CONTRADICTED:
        return (
            "The observed relationship moved in the opposite direction from the tested explanation.",
        )
    reasons = lineage.validated_result.inconclusive_reasons
    rendered = tuple(_inconclusive_reason(reason) for reason in reasons)
    if not rendered:
        rendered = (lineage.evaluation.controlling_reason,)
    return ("The current product-mix test was not evaluated because " + "; ".join(rendered) + ".",)


def _inconclusive_reason(reason: str) -> str:
    translations = {
        "total_valid_weeks<8": "there were too few complete weeks overall",
        "MINIMUM_TOTAL_WEEKS_NOT_MET": "there were too few complete weeks overall",
        "baseline_valid_weeks<4": "there were too few complete baseline weeks",
        "MINIMUM_BASELINE_WEEKS_NOT_MET": "there were too few complete baseline weeks",
        "comparison_valid_weeks<4": "there were too few complete comparison weeks",
        "MINIMUM_COMPARISON_WEEKS_NOT_MET": "there were too few complete comparison weeks",
        "constant_distance": "there was no variation in product mix",
        "CONSTANT_JACCARD_VECTOR": "there was no variation in product mix",
        "constant_revenue_deviation": "there was no variation in weekly revenue performance",
        "CONSTANT_REVENUE_DEVIATION_VECTOR": "there was no variation in weekly revenue performance",
        "undefined_denominator": "the correlation was undefined",
        "UNDEFINED_SPEARMAN_DENOMINATOR": "the correlation was undefined",
        "observation_construction_failed": "complete weekly observations could not be constructed",
    }
    return translations.get(reason, reason.replace("_", " "))


def project_public_response(
    *,
    intent: PublicAnalysisIntent,
    request: AnalysisRequest,
    result: AnalysisResult,
    evaluated_claims: tuple[EvaluatedClaimAuthority, ...],
    metadata_store: MetadataStore,
) -> PublicResponse:
    """Project only authorized kernel facts into a public response."""
    supported: list[PublicClaimProjection] = []
    evidence_summary: list[PublicEvidenceSummary] = []
    unsupported: list[str] = []
    additional: list[str] = []
    limitations: list[str] = []
    dataset = metadata_store.get_dataset(request.dataset_ref_id)

    for detail in result.failure_details:
        limitations.append(detail.reason)

    for claim in evaluated_claims:
        if claim.decision.claim_state is ClaimState.ADMISSIBLE:
            supported.append(_supported_claim_projection(request, claim))
            evidence_summary.append(_evidence_summary(request, claim, dataset))
        else:
            unsupported.extend(_unsupported_messages(intent, claim.decision))
            additional.extend(_additional_evidence_needed(intent, claim.decision))

    blocked = not supported and result.run_status in (
        RunStatus.BLOCKED,
        RunStatus.VALIDATION_FAILED,
        RunStatus.EXECUTION_FAILED,
        RunStatus.CLARIFICATION_REQUIRED,
    )
    insufficient = "Insufficient evidence to conclude." if blocked else None
    return PublicResponse(
        supported_claims=tuple(supported),
        evidence_summary=tuple(evidence_summary),
        limitations=tuple(dict.fromkeys(limitations)),
        unsupported_conclusions=tuple(dict.fromkeys(unsupported)),
        additional_evidence_needed=tuple(dict.fromkeys(additional)),
        blocked=blocked,
        insufficient_evidence_message=insufficient,
    )


def _supported_claim_projection(
    request: AnalysisRequest,
    claim: EvaluatedClaimAuthority,
) -> PublicClaimProjection:
    metric = get_metric_registry().require(claim.validated_result.metric_ref)
    return PublicClaimProjection(
        metric_ref=claim.validated_result.metric_ref,
        metric_display_name=metric.display_name,
        metric_state=claim.validated_result.metric_state,
        claim_state=claim.decision.claim_state,
        public_disposition=(
            "supported_descriptive_state"
            if claim.validated_result.metric_state is MetricState.UNDEFINED
            else "supported_descriptive_value"
        ),
        value=claim.candidate.claimed_value,
        undefined_reason=claim.candidate.undefined_reason,
        unit=claim.candidate.unit,
        currency=claim.candidate.currency,
        period_label=_period_label(request, claim.validated_result.period_ref),
        period_role=claim.validated_result.period_role,
    )


def _evidence_summary(
    request: AnalysisRequest,
    claim: EvaluatedClaimAuthority,
    dataset,
) -> PublicEvidenceSummary:
    metric = get_metric_registry().require(claim.validated_result.metric_ref)
    return PublicEvidenceSummary(
        metric_ref=claim.validated_result.metric_ref,
        metric_display_name=metric.display_name,
        metric_definition_version=claim.validated_result.metric_definition_version,
        period_label=_period_label(request, claim.validated_result.period_ref),
        period_role=claim.validated_result.period_role,
        metric_state=claim.validated_result.metric_state,
        evidence_status="passed",
        claim_state=claim.decision.claim_state,
        source_filename=dataset.original_name if dataset is not None else None,
        source_type=dataset.source_type.value if dataset is not None else None,
    )


def _unsupported_messages(intent: PublicAnalysisIntent, decision: ClaimDecision) -> tuple[str, ...]:
    if decision.failure_code == "unsupported_claim_type" and any(
        claim_intent.claim_type is ClaimType.DIAGNOSTIC for claim_intent in intent.claim_intents
    ):
        return ("Insufficient evidence to conclude why Revenue declined.",)
    if decision.failure_code == "unsupported_claim_type":
        return ("Unsupported conclusion refused by ClaimDecision authority.",)
    return ("Insufficient evidence to conclude.",)


def _additional_evidence_needed(intent: PublicAnalysisIntent, decision: ClaimDecision) -> tuple[str, ...]:
    if decision.failure_code == "unsupported_claim_type" and any(
        claim_intent.claim_type is ClaimType.DIAGNOSTIC for claim_intent in intent.claim_intents
    ):
        return ("An approved diagnostic workflow and relevant diagnostic Evidence would be required.",)
    return ()


def _period_label(request: AnalysisRequest, period_ref: str | None) -> str | None:
    if period_ref == request.baseline_period.period_id:
        return request.baseline_period.label
    if period_ref == request.comparison_period.period_id:
        return request.comparison_period.label
    return period_ref


def _claim_sentence(claim: PublicClaimProjection) -> str:
    period = f" for {claim.period_label}" if claim.period_label else ""
    if claim.metric_state is MetricState.UNDEFINED:
        return f"{claim.metric_display_name}{period} is Undefined ({claim.undefined_reason})."
    value = _format_value(claim.value)
    suffix = f" {claim.currency}" if claim.currency else ""
    return f"{claim.metric_display_name}{period}: {value}{suffix}."


def _format_value(value: object | None) -> str:
    if isinstance(value, Decimal):
        return value.to_eng_string()
    return str(value)
