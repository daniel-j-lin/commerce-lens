"""Public v0.1 Skill integration over the frozen application service."""

from __future__ import annotations

import csv
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from commerce_lens.application import evaluate_claim, run_analysis
from commerce_lens.application.public_r7_service import run_public_r7_flow
from commerce_lens.canonical import CanonicalizationRequest, EligibilityMode, EligibilityState, EligibilityValueMapping
from commerce_lens.canonical.mapping import CanonicalMapping, identity_mapping, validate_mapping
from commerce_lens.canonical.quality import DataQualityConsequence
from commerce_lens.canonical.models import PeriodCoverageEvidence
from commerce_lens.canonical.schema import CANONICAL_SCHEMA_VERSION
from commerce_lens.contracts.common import (
    AvailableEvidence,
    ClaimType,
    EvidenceRequirement,
    GroupingDimension,
    MetricState,
    PeriodDefinition,
    ScopeDefinition,
    SourceType,
)
from commerce_lens.contracts.evidence import (
    AdmissibleEvidence,
    ClaimCandidate,
    ClaimDecision,
    ClaimPropositionType,
    EvidenceAdmissibilityStatus,
    MetricReference,
)
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.results import AnalysisResult, MetricResult
from commerce_lens.contracts.validation import ValidatedResult
from commerce_lens.evidence.identifiers import generate_id, canonical_json_fingerprint
from commerce_lens.intake.csv_adapter import CsvInspectionAdapter
from commerce_lens.intake.excel_adapter import ExcelInspectionAdapter
from commerce_lens.intake.inspection import InspectionStatus
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.metrics import METRIC_REGISTRY_VERSION, get_metric_registry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.skill.public_response import (
    EvaluatedClaimAuthority,
    PublicMappingProposal,
    PublicResponse,
    project_public_response,
    with_public_diagnostic,
)
from commerce_lens.skill.schema_mapping import assess_schema_mapping
from commerce_lens.skill.coverage_intake import (
    DISCLOSURE, SOURCE_BASIS_ASSERTION, complete_coverage_proposal,
    coverage_proposal_fingerprint, declaration_template, validate_declarations,
    project_coverage,
)


PUBLIC_V0_1_METRICS = frozenset({"revenue", "orders", "aov", "revenue_change"})
PUBLIC_SINGLE_PERIOD_METRICS = frozenset({"revenue", "orders", "aov"})
PUBLIC_DIAGNOSTIC_FAMILY = "product_composition_association"
_SUPPORTED_SOURCE_TYPES = frozenset({SourceType.CSV, SourceType.EXCEL_XLSX})
_SUPPORTED_QUESTION_CLASSES = frozenset(
    {
        "single_period_metric",
        "revenue_change",
        "diagnostic_revenue_drop",
    }
)


class PublicQuestionClass(str, Enum):
    SINGLE_PERIOD_METRIC = "single_period_metric"
    REVENUE_CHANGE = "revenue_change"
    DIAGNOSTIC_REVENUE_DROP = "diagnostic_revenue_drop"


@dataclass(frozen=True)
class PublicSourceSelection:
    source_path: Path
    source_type: SourceType
    selected_sheet: str | None = None
    selected_table: str | None = None
    mapping: CanonicalMapping | None = None
    mapping_mode: str = "identity_canonical_columns"


@dataclass(frozen=True)
class PublicClaimIntent:
    claim_type: ClaimType = ClaimType.DESCRIPTIVE
    proposed_meaning: str = "Public v0.1 governed descriptive Metric claim"


@dataclass(frozen=True)
class PublicCoverageContext:
    """Host-supplied facts used only to render a complete coverage proposal.

    These facts are deliberately not trusted evidence.  The resulting proposal
    still has to be explicitly confirmed and pass ``CoverageDeclaration``
    validation before it can authorize analysis.
    """

    all_pages_included: bool | None = None
    all_records_included: bool | None = None
    paid_included: bool | None = None
    cancelled_excluded: bool | None = None
    no_additional_hidden_filters: bool | None = None
    data_availability_cutoff: datetime | None = None
    extracted_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in ("data_availability_cutoff", "extracted_at"):
            value = getattr(self, field_name)
            if value is None:
                continue
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("coverage timestamps require an explicit timezone")
            object.__setattr__(self, field_name, value.astimezone(UTC))

    def missing_facts(self) -> tuple[str, ...]:
        missing = []
        for name in (
            "all_pages_included",
            "all_records_included",
            "paid_included",
            "cancelled_excluded",
            "no_additional_hidden_filters",
        ):
            if getattr(self, name) is not True:
                missing.append(name)
        if self.data_availability_cutoff is None:
            missing.append("data_availability_cutoff")
        return tuple(missing)

    @property
    def complete(self) -> bool:
        return not self.missing_facts()


@dataclass(frozen=True)
class PublicAnalysisIntent:
    question_class: PublicQuestionClass | str
    metric_id: str
    baseline_period: PeriodDefinition | None
    comparison_period: PeriodDefinition | None
    source: PublicSourceSelection
    original_question_text: str | None = None
    scope: ScopeDefinition = ScopeDefinition(scope_id="all_eligible")
    grouping: GroupingDimension = GroupingDimension.NONE
    result_period_role: str | None = None
    claim_intents: tuple[PublicClaimIntent, ...] = (PublicClaimIntent(),)
    diagnostic_family_id: str | None = None


@dataclass(frozen=True)
class PublicAnalysisOutcome:
    intent: PublicAnalysisIntent
    response: PublicResponse
    request: AnalysisRequest | None = None
    analysis_result: AnalysisResult | None = None
    claim_candidates: tuple[ClaimCandidate, ...] = ()
    claim_decisions: tuple[ClaimDecision, ...] = ()


def validate_public_intent(intent: PublicAnalysisIntent) -> tuple[str, ...]:
    """Validate host-interpreted intent fail-closed before constructing a request."""
    failures: list[str] = []
    question_class = _question_class_value(intent.question_class)
    if question_class not in _SUPPORTED_QUESTION_CLASSES:
        failures.append(f"unsupported question class: {question_class}")
    if intent.metric_id not in PUBLIC_V0_1_METRICS:
        failures.append(f"unsupported Public v0.1 Metric: {intent.metric_id}")
    if intent.metric_id == "revenue_change" and question_class == PublicQuestionClass.SINGLE_PERIOD_METRIC.value:
        failures.append("revenue_change requires an explicitly comparable period question class")
    if intent.metric_id in PUBLIC_SINGLE_PERIOD_METRICS and question_class != PublicQuestionClass.SINGLE_PERIOD_METRIC.value:
        failures.append(f"{intent.metric_id} requires a single-period question class")
    if intent.grouping is not GroupingDimension.NONE:
        failures.append("Public v0.1 supports grouping NONE only")
    if intent.source.source_type not in _SUPPORTED_SOURCE_TYPES:
        failures.append(f"unsupported Public v0.1 source type: {intent.source.source_type.value}")
    if intent.source.selected_table is not None:
        failures.append("Public v0.1 does not expose table selection as a headline CSV/XLSX workflow")
    if intent.source.mapping is None and intent.source.mapping_mode != "identity_canonical_columns":
        failures.append("mapping selection requires clarification")
    if intent.source.mapping is not None and intent.source.mapping_mode in {
        "proposed_unconfirmed_mapping",
        "mapping_rejected",
    }:
        failures.append("confirmed source-to-canonical mapping authority is required")
    if intent.baseline_period is None or intent.comparison_period is None:
        failures.append("explicit governed baseline and comparison periods are required by the current AnalysisRequest contract")
    if intent.metric_id in PUBLIC_SINGLE_PERIOD_METRICS and intent.result_period_role not in ("baseline", "comparison"):
        failures.append("single-period Metric intent requires an explicit result_period_role of baseline or comparison")
    if intent.metric_id == "revenue_change" and intent.result_period_role not in (None, "comparison"):
        failures.append("Revenue Change public response uses the governed comparison result")
    if not intent.claim_intents:
        failures.append("at least one Claim intent is required")
    if question_class == PublicQuestionClass.DIAGNOSTIC_REVENUE_DROP.value:
        if (
            intent.diagnostic_family_id is not None
            and intent.diagnostic_family_id != PUBLIC_DIAGNOSTIC_FAMILY
        ):
            failures.append(f"unsupported diagnostic family: {intent.diagnostic_family_id}")
    for claim_intent in intent.claim_intents:
        if (
            question_class == PublicQuestionClass.DIAGNOSTIC_REVENUE_DROP.value
            and intent.diagnostic_family_id == PUBLIC_DIAGNOSTIC_FAMILY
            and claim_intent.claim_type is ClaimType.DIAGNOSTIC
        ):
            continue
        if claim_intent.claim_type in (ClaimType.PREDICTIVE, ClaimType.CAUSAL, ClaimType.PRESCRIPTIVE):
            failures.append(f"unsupported Claim type: {claim_intent.claim_type.value}")
    return tuple(dict.fromkeys(failures))


def run_public_analysis(
    intent: PublicAnalysisIntent,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    available_evidence: tuple[AvailableEvidence, ...] | None = None,
    period_coverage_evidence: tuple[PeriodCoverageEvidence, ...] | None = None,
    coverage_declarations: object | None = None,
    run_id: str | None = None,
    retention_session: object | None = None,
) -> PublicAnalysisOutcome:
    """Run the approved Public v0.1 integration chain.

    Missing authority stays unknown for the existing sufficiency gate. Request
    dates, requirements, and observed transaction dates do not establish it.
    available_evidence/period_coverage_evidence are trusted Python caller inputs.
    coverage_declarations is external input and must pass deterministic intake.
    Mixing the boundaries fails closed.
    """
    question_class = _question_class_value(intent.question_class)
    validation_failures = validate_public_intent(intent)
    if validation_failures:
        return PublicAnalysisOutcome(
            intent=intent,
            response=PublicResponse(clarification_required=validation_failures),
        )

    source_headers, source_failure = _source_headers(intent.source)
    if source_failure is not None:
        return PublicAnalysisOutcome(
            intent=intent,
            response=PublicResponse(clarification_required=(source_failure,)),
        )
    if intent.source.mapping is None:
        mapping_assessment = assess_schema_mapping(source_headers, intent.metric_id)
        if not mapping_assessment.identity_mapping_available:
            return PublicAnalysisOutcome(
                intent=intent,
                response=PublicResponse(
                    clarification_required=mapping_assessment.clarification_required,
                    mapping_proposals=tuple(
                        PublicMappingProposal(
                            source_field=proposal.source_field,
                            canonical_field=proposal.canonical_field,
                        )
                        for proposal in mapping_assessment.proposals
                    ),
                    required_mapping_fields=mapping_assessment.required_canonical_fields,
                    blocked=True,
                    insufficient_evidence_message="Insufficient evidence to conclude.",
                ),
            )

    artifact_store.ensure_layout()
    metadata_store.initialize()
    dataset = DatasetRegistry(artifact_store).register_source(
        intent.source.source_path,
        intent.source.source_type,
        selected_sheet=intent.source.selected_sheet,
        selected_table=intent.source.selected_table,
        metadata={"public_workflow": "public_v0_1"},
    )
    request = _analysis_request(intent, dataset.dataset_id)
    canonicalization_request = _canonicalization_request(intent, dataset.dataset_id, source_headers)
    if retention_session is not None:
        retention_session.capture_context(
            intent=intent,
            request=request,
            canonicalization_request=canonicalization_request,
        )
    coverage_provenance = ()
    if coverage_declarations is not None:
        try:
            if available_evidence is not None or period_coverage_evidence is not None:
                raise ValueError("do not mix external declarations with trusted evidence inputs")
            declaration = validate_declarations(
                coverage_declarations, dataset=dataset, context=canonicalization_request,
                scope=intent.scope, periods=(request.baseline_period, request.comparison_period),
                artifact_store=artifact_store,
            )
            semantic_evidence = _public_mapping_evidence(intent, canonicalization_request, source_headers)
            payload = declaration.model_dump(mode="json")
            fingerprint = canonical_json_fingerprint(payload)
            artifact = artifact_store.write_json_artifact(
                f"runs/coverage_declarations/{dataset.dataset_id}/{fingerprint}.json", payload,
            )
            metadata_store.insert_artifact_reference(artifact)
            if retention_session is not None:
                retention_session.capture_declaration(declaration, artifact)
            coverage_authority, coverage = project_coverage(declaration, artifact.path)
            available_evidence = (coverage_authority, semantic_evidence)
            period_coverage_evidence = (coverage,)
            coverage_provenance = ({**payload, "artifact": artifact.model_dump(mode="json")},)
        except ValueError as exc:
            return PublicAnalysisOutcome(
                intent=intent, request=request,
                response=PublicResponse(
                    blocked=True, clarification_required=(f"Coverage declaration rejected: {exc}",),
                    insufficient_evidence_message="Insufficient evidence to conclude.",
                ),
            )
    result = run_analysis(
        request,
        canonicalization_request=canonicalization_request,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        **({"dataset": dataset} if coverage_declarations is not None else {
            "source_path": intent.source.source_path, "source_type": intent.source.source_type,
            "selected_sheet": intent.source.selected_sheet, "selected_table": intent.source.selected_table,
        }),
        available_evidence=available_evidence if available_evidence is not None else (),
        period_coverage_evidence=(
            period_coverage_evidence
            if period_coverage_evidence is not None
            else ()
        ),
        run_id=run_id,
    )

    evaluated: list[EvaluatedClaimAuthority] = []
    candidates: list[ClaimCandidate] = []
    decisions: list[ClaimDecision] = []
    for claim_intent in intent.claim_intents:
        if (
            question_class == PublicQuestionClass.DIAGNOSTIC_REVENUE_DROP.value
            and intent.diagnostic_family_id == PUBLIC_DIAGNOSTIC_FAMILY
            and claim_intent.claim_type is ClaimType.DIAGNOSTIC
        ):
            continue
        try:
            candidate, validated, evidence = bind_claim_candidate_from_authority(
                intent,
                result,
                artifact_store=artifact_store,
                metadata_store=metadata_store,
                claim_type=claim_intent.claim_type,
                proposed_meaning=claim_intent.proposed_meaning,
            )
        except ValueError:
            continue
        decision = evaluate_claim(candidate, artifact_store=artifact_store, metadata_store=metadata_store)
        candidates.append(candidate)
        decisions.append(decision)
        evaluated.append(
            EvaluatedClaimAuthority(
                candidate=candidate,
                decision=decision,
                validated_result=validated,
                evidence=evidence,
            )
        )

    response = _with_coverage_disclosure(project_public_response(
        intent=intent,
        request=request,
        result=result,
        evaluated_claims=tuple(evaluated),
        metadata_store=metadata_store,
    ), coverage_provenance)
    if (
        question_class == PublicQuestionClass.DIAGNOSTIC_REVENUE_DROP.value
        and intent.diagnostic_family_id == PUBLIC_DIAGNOSTIC_FAMILY
    ):
        response = _run_public_diagnostic(
            intent=intent,
            result=result,
            source_headers=source_headers,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            response=response,
        )

    return PublicAnalysisOutcome(
        intent=intent,
        request=request,
        analysis_result=result,
        claim_candidates=tuple(candidates),
        claim_decisions=tuple(decisions),
        response=response,
    )


def _run_public_diagnostic(
    *,
    intent: PublicAnalysisIntent,
    result: AnalysisResult,
    source_headers: tuple[str, ...],
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    response: PublicResponse,
) -> PublicResponse:
    mapping = intent.source.mapping or identity_mapping(source_headers, require_eligibility=True)
    if mapping.source_for("product_id") is None:
        return with_public_diagnostic(
            response,
            blocker="A governed product_id mapping is required for the product-composition test.",
        )
    metric = _metric_result(result, "revenue_change")
    if metric is None:
        return with_public_diagnostic(
            response,
            blocker="An authenticated Revenue Change result is required before diagnostic testing.",
        )
    try:
        validated = _select_validated_result_from_metric(
            metric, intent, artifact_store, metadata_store
        )
        diagnostic = run_public_r7_flow(
            analysis_result=result,
            revenue_change_validated_result_ref=validated.validated_result_id,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
        )
    except (ValueError, RuntimeError) as exc:
        return with_public_diagnostic(
            response,
            blocker=f"Diagnostic authority authentication failed: {exc}",
        )
    return with_public_diagnostic(
        response,
        lineage=diagnostic.authenticated_lineage,
        blocker=diagnostic.blocker,
    )


def _with_coverage_disclosure(response: PublicResponse, provenance: tuple) -> PublicResponse:
    if not provenance:
        return response
    return replace(response, coverage_provenance=provenance,
                   limitations=(*response.limitations, DISCLOSURE))


def _public_mapping_evidence(intent, context, headers) -> AvailableEvidence:
    # Separate input semantics gate. Coverage cannot authorize a Metric or mapping.
    if intent.source.mapping is not None and intent.source.mapping_mode != "confirmed_source_to_canonical_mapping":
        raise ValueError("external intake requires separately confirmed mapping authority")
    checks = validate_mapping(context.mapping, headers, require_eligibility=True)
    if any(check.consequence is DataQualityConsequence.BLOCKING for check in checks):
        raise ValueError("separate schema mapping validation failed")
    metric = get_metric_registry().require(intent.metric_id)
    return AvailableEvidence(
        evidence_id=f"public_mapping:{context.mapping.fingerprint}:{metric.metric_id}",
        description=f"Separate canonical mapping input authority for {metric.metric_id} {metric.definition_version}; currency and eligibility still require canonical validation",
        source_ref=context.mapping.mapping_id,
        satisfies_requirement_ids=(f"req_{metric.metric_id}",),
    )


def prepare_public_coverage(
    intent: PublicAnalysisIntent,
    *,
    artifact_store: ArtifactStore,
    coverage_context: PublicCoverageContext | None = None,
    data_availability_cutoff: datetime | None = None,
    extracted_at: datetime | None = None,
) -> dict:
    """Inspect binding and propose a confirmation summary; never attest or execute."""
    coverage_context = _merge_coverage_context(
        coverage_context,
        data_availability_cutoff=data_availability_cutoff,
        extracted_at=extracted_at,
    )
    failures = validate_public_intent(intent)
    if failures:
        raise ValueError("; ".join(failures))
    headers, failure = _source_headers(intent.source)
    if failure:
        raise ValueError(failure)
    if intent.source.source_type is SourceType.EXCEL_XLSX and not intent.source.selected_sheet:
        raise ValueError("select the XLSX sheet explicitly before coverage confirmation")
    dataset = DatasetRegistry(artifact_store).register_source(
        intent.source.source_path, intent.source.source_type,
        selected_sheet=intent.source.selected_sheet, selected_table=intent.source.selected_table,
    )
    context = _canonicalization_request(intent, dataset.dataset_id, headers)
    _public_mapping_evidence(intent, context, headers)
    template = declaration_template(dataset, context, intent.scope,
                                    (intent.baseline_period, intent.comparison_period))
    proposal = None
    proposal_fingerprint = None
    if coverage_context is not None and coverage_context.complete:
        proposal = complete_coverage_proposal(
            template,
            data_availability_cutoff=coverage_context.data_availability_cutoff,
            extracted_at=coverage_context.extracted_at,
        )
        proposal_fingerprint = coverage_proposal_fingerprint(
            template, requested_periods=(intent.baseline_period, intent.comparison_period),
            data_availability_cutoff=coverage_context.data_availability_cutoff,
            extracted_at=coverage_context.extracted_at,
        )
    display_facts = _coverage_display_facts(
        intent=intent,
        context=context,
        template=template,
        coverage_context=coverage_context,
    )
    if coverage_context is not None:
        missing_facts = coverage_context.missing_facts()
    else:
        missing_facts = (
            "all_pages_included",
            "all_records_included",
            "paid_included",
            "cancelled_excluded",
            "no_additional_hidden_filters",
            "data_availability_cutoff",
        )
    summary = {
        "file": dataset.original_name,
        "sheet": dataset.selected_sheet,
        "requested_periods": [
            p.model_dump(mode="json") for p in (intent.baseline_period, intent.comparison_period)
        ],
        "time_boundary": "Inclusive UTC calendar dates; availability cutoff at or after the next UTC midnight",
        "population": intent.scope.model_dump(mode="json"),
        "eligibility": [item.model_dump(mode="json") for item in context.eligibility_value_mapping],
        "filters": template["filters_status"],
        "completeness_basis": (
            SOURCE_BASIS_ASSERTION
            if coverage_context is not None
            and all(
                getattr(coverage_context, name) is True
                for name in (
                    "all_pages_included",
                    "all_records_included",
                    "paid_included",
                    "cancelled_excluded",
                    "no_additional_hidden_filters",
                )
            )
            else None
        ),
        "coverage_facts": display_facts,
        "data_completeness_cutoff": (
            proposal["data_availability_cutoff"]
            if proposal is not None
            else _iso_timestamp(
                coverage_context.data_availability_cutoff
                if coverage_context is not None
                else None
            )
        ),
    }
    prepared = {
        "status": "coverage_confirmation_ready" if proposal is not None else "coverage_confirmation_required",
        "declaration_template": template,
        "coverage_proposal": proposal,
        "proposal_fingerprint": proposal_fingerprint,
        "confirmation_summary": summary,
        "coverage_facts": display_facts,
        "missing_facts": missing_facts,
        "confirmation_prompt": (
            "請確認以上資訊是否正確。"
            if proposal is not None
            else "需要補充以下資料後才能建立完整 coverage proposal：" + ", ".join(missing_facts)
        ),
        "choices": ["Confirm", "Correct", "I don't know"],
        "disclosure": DISCLOSURE,
    }
    prepared["confirmation_text"] = render_coverage_confirmation(prepared)
    return prepared


def _merge_coverage_context(
    coverage_context: PublicCoverageContext | None,
    *,
    data_availability_cutoff: datetime | None,
    extracted_at: datetime | None,
) -> PublicCoverageContext | None:
    """Merge legacy timestamp inputs into the structured proposal context.

    The timestamp parameters predate ``PublicCoverageContext``. Keeping this
    merge at the API boundary prevents a supplied cutoff from being discarded
    while preserving fail-closed handling for conflicting facts.
    """
    if coverage_context is None:
        if data_availability_cutoff is None and extracted_at is None:
            return None
        return PublicCoverageContext(
            data_availability_cutoff=data_availability_cutoff,
            extracted_at=extracted_at,
        )

    updates: dict[str, datetime] = {}
    for field_name, supplied in (
        ("data_availability_cutoff", data_availability_cutoff),
        ("extracted_at", extracted_at),
    ):
        if supplied is None:
            continue
        normalized = PublicCoverageContext(**{field_name: supplied})
        supplied_utc = getattr(normalized, field_name)
        existing = getattr(coverage_context, field_name)
        if existing is not None and existing != supplied_utc:
            raise ValueError(f"conflicting coverage context field: {field_name}")
        updates[field_name] = supplied_utc
    return replace(coverage_context, **updates) if updates else coverage_context


def _coverage_display_facts(*, intent, context, template, coverage_context) -> dict[str, Any]:
    """Build the host-facing facts beside the exact declaration template."""
    eligibility = {
        item.source_value: item.normalized_status.value
        for item in context.eligibility_value_mapping
    }
    return {
        "coverage_period": {
            "baseline": intent.baseline_period.model_dump(mode="json"),
            "comparison": intent.comparison_period.model_dump(mode="json"),
            "date_convention_ref": intent.baseline_period.date_convention_ref,
        },
        "all_pages_included": (
            coverage_context.all_pages_included if coverage_context is not None else None
        ),
        "all_records_included": (
            coverage_context.all_records_included if coverage_context is not None else None
        ),
        "status_scope": {
            "paid": {
                "mapping": eligibility.get("paid"),
                "included": (
                    coverage_context.paid_included if coverage_context is not None else None
                ),
            },
            "cancelled": {
                "mapping": eligibility.get("cancelled"),
                "excluded": (
                    coverage_context.cancelled_excluded if coverage_context is not None else None
                ),
            },
        },
        "no_additional_hidden_filters": (
            coverage_context.no_additional_hidden_filters
            if coverage_context is not None
            else None
        ),
        "data_availability_cutoff": _iso_timestamp(
            coverage_context.data_availability_cutoff
            if coverage_context is not None
            else None
        ),
        "scope": template["scope"],
        "disclosure": DISCLOSURE,
    }


def _iso_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("coverage timestamps require an explicit timezone")
    return value.isoformat().replace("+00:00", "Z")


def render_coverage_confirmation(prepared: Mapping[str, Any]) -> str:
    """Render one host-facing coverage proposal, never one prompt per field.

    A complete proposal is declarative: the facts are displayed as statements
    and the only follow-up is the single confirmation sentence.  An incomplete
    proposal reports only the facts that are actually unresolved; it must not
    turn every proposal field into a yes/no question.
    """
    proposal = prepared.get("coverage_proposal")
    if proposal is None:
        missing = tuple(prepared.get("missing_facts", ()))
        labels = {
            "all_pages_included": "all export pages included",
            "all_records_included": "all in-scope records included",
            "paid_included": "paid orders included",
            "cancelled_excluded": "cancelled orders excluded",
            "no_additional_hidden_filters": "no additional hidden filters",
            "data_availability_cutoff": "data-availability cutoff (UTC)",
        }
        if not missing:
            return "需要補充 coverage 資料後才能建立完整 proposal。"
        if len(missing) == 1:
            return f"需要補充：{labels.get(missing[0], missing[0])}。"
        return "需要補充以下 coverage 資料：" + "、".join(
            labels.get(item, item) for item in missing
        ) + "。"

    summary = prepared["confirmation_summary"]
    facts = prepared["coverage_facts"]
    periods = summary["requested_periods"]
    baseline, comparison = periods
    scope = facts["scope"]
    filters = scope.get("filters") or []
    filter_text = "none" if not filters else "; ".join(
        f"{item['field']} {item['operator']} {item['value']}" for item in filters
    )
    source_binding = (
        f"{proposal['source_filename']} ({proposal['source_type']}; "
        f"dataset {proposal['dataset_id']})"
    )
    return "\n".join((
        "Coverage proposal:",
        f"- Source: {source_binding}; sheet: {proposal['selected_sheet'] or 'none'}.",
        f"- Coverage periods: baseline = {baseline['label']}; "
        f"comparison = {comparison['label']}; "
        f"{facts['coverage_period']['date_convention_ref']} inclusive.",
        f"- Scope: {scope['scope_id']}; population: all eligible order lines.",
        "- Eligibility: paid orders are included; cancelled orders are excluded.",
        "- Completeness: all export pages and all in-scope records included.",
        f"- Additional hidden filters: {filter_text}.",
        f"- Data available through: {proposal['data_availability_cutoff']}.",
        "- Authority: USER_DECLARED; not independently verified by CommerceLens.",
        f"- {DISCLOSURE}",
        "請確認以上資訊是否正確。",
    ))


def normalize_coverage_confirmation(response: str) -> str | None:
    """Normalize ordinary host-language affirmative replies, without attesting."""
    normalized = response.strip().casefold()
    if normalized in {"確認", "是", "沒問題", "正確", "照這個執行", "yes", "looks right", "confirm"}:
        return "confirmed"
    return None


def confirm_public_coverage(
    intent: PublicAnalysisIntent,
    prepared: Mapping[str, Any],
    *,
    response: str,
    recorded_at: datetime,
    declaration_id: str,
):
    """Bind one host confirmation to the exact complete proposal shown."""
    confirmation_intent = normalize_coverage_confirmation(response)
    if confirmation_intent != "confirmed":
        raise ValueError("coverage is unconfirmed; correction or uncertainty requires clarification")
    proposal = prepared.get("coverage_proposal")
    if proposal is None or not prepared.get("proposal_fingerprint"):
        raise ValueError("coverage proposal is incomplete; ask only for its missing facts")
    from commerce_lens.skill.coverage_intake import confirm_declaration

    return confirm_declaration(
        prepared["declaration_template"],
        confirmation_intent=confirmation_intent,
        proposal_fingerprint=prepared["proposal_fingerprint"],
        requested_periods=(intent.baseline_period, intent.comparison_period),
        recorded_at=recorded_at,
        declaration_id=declaration_id,
        data_availability_cutoff=datetime.fromisoformat(
            proposal["data_availability_cutoff"].replace("Z", "+00:00")
        ),
        extracted_at=(
            datetime.fromisoformat(proposal["extracted_at"].replace("Z", "+00:00"))
            if proposal.get("extracted_at") is not None
            else None
        ),
    )


def bind_claim_candidate_from_authority(
    intent: PublicAnalysisIntent,
    result: AnalysisResult,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    claim_type: ClaimType,
    proposed_meaning: str,
) -> tuple[ClaimCandidate, ValidatedResult, AdmissibleEvidence]:
    """Bind one schema-valid ClaimCandidate from exact AnalysisResult refs."""
    metric = _metric_result(result, intent.metric_id)
    if metric is None:
        raise ValueError(f"AnalysisResult has no MetricResult for {intent.metric_id}")
    validated = _select_validated_result_from_metric(metric, intent, artifact_store, metadata_store)
    evidence = _select_admissible_evidence_from_metric(metric, validated, artifact_store, metadata_store)
    execution_record = metadata_store.get_execution_record(validated.execution_id)
    if execution_record is None:
        raise ValueError(f"missing execution authority for {validated.execution_id}")

    update = {}
    if validated.metric_ref == "revenue_change":
        if len(execution_record.period_refs) != 2 or len(execution_record.population_refs) != 2:
            raise ValueError("Revenue Change execution authority lacks exact baseline/comparison context")
        update = {
            "baseline_period_ref": execution_record.period_refs[0],
            "comparison_period_ref": execution_record.period_refs[1],
            "baseline_population_ref": execution_record.population_refs[0],
            "comparison_population_ref": execution_record.population_refs[1],
            "baseline_population_fingerprint": execution_record.population_fingerprints[0],
            "comparison_population_fingerprint": execution_record.population_fingerprints[1],
        }

    return (
        ClaimCandidate(
            claim_candidate_id=generate_id("clmcand_public_v0_1"),
            claim_id=generate_id("claim_public_v0_1"),
            claim_type=claim_type,
            metric_ref=validated.metric_ref,
            metric_definition_version=validated.metric_definition_version,
            request_id=result.request_id,
            dataset_ref_id=evidence.dataset_ref_id,
            canonical_dataset_ref_id=evidence.canonical_dataset_ref_id,
            canonical_dataset_fingerprint=evidence.canonical_dataset_fingerprint,
            intended_scope=evidence.scope,
            population_ref=validated.population_ref,
            population_fingerprint=validated.population_fingerprint,
            period_ref=validated.period_ref,
            period_role=validated.period_role,
            proposition_type=(
                ClaimPropositionType.METRIC_STATE_IS
                if validated.metric_state is MetricState.UNDEFINED
                else ClaimPropositionType.METRIC_VALUE_EQUALS
            ),
            claimed_value=None if validated.metric_state is MetricState.UNDEFINED else validated.value,
            claimed_metric_state=MetricState.UNDEFINED if validated.metric_state is MetricState.UNDEFINED else None,
            undefined_reason=validated.undefined_reason,
            unit=validated.unit,
            currency=validated.currency,
            supporting_evidence_refs=(evidence.evidence_id,),
            supporting_validated_result_refs=evidence.validated_result_ids,
            proposed_meaning=proposed_meaning,
            **update,
        ),
        validated,
        evidence,
    )


def _question_class_value(question_class: PublicQuestionClass | str) -> str:
    if isinstance(question_class, PublicQuestionClass):
        return question_class.value
    return str(question_class)


def _source_headers(source: PublicSourceSelection) -> tuple[tuple[str, ...], str | None]:
    if source.source_type is SourceType.CSV:
        inspection = CsvInspectionAdapter().inspect(source.source_path)
        if inspection.status is not InspectionStatus.SUPPORTED:
            reason = inspection.failure_detail.reason if inspection.failure_detail is not None else inspection.status.value
            return (), reason
        return _csv_headers(source.source_path), None
    if source.source_type is SourceType.EXCEL_XLSX:
        inspection = ExcelInspectionAdapter().inspect(source.source_path, sheet_name=source.selected_sheet)
        if inspection.status is not InspectionStatus.SUPPORTED:
            reason = inspection.failure_detail.reason if inspection.failure_detail is not None else inspection.status.value
            return (), reason
        return tuple(column.name for column in inspection.columns), None
    return (), f"unsupported Public v0.1 source type: {source.source_type.value}"


def _csv_headers(path: Path) -> tuple[str, ...]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as file_obj:
        return tuple(next(csv.reader(file_obj)))


def _analysis_request(intent: PublicAnalysisIntent, dataset_ref_id: str) -> AnalysisRequest:
    registry = get_metric_registry()
    metric = registry.require(intent.metric_id)
    assert intent.baseline_period is not None
    assert intent.comparison_period is not None
    return AnalysisRequest(
        canonical_business_question_id=f"public_v0_1:{_question_class_value(intent.question_class)}",
        original_question_text=intent.original_question_text,
        metrics=(MetricReference(metric_id=metric.metric_id, definition_version=metric.definition_version),),
        baseline_period=intent.baseline_period,
        comparison_period=intent.comparison_period,
        scope=intent.scope,
        grouping=GroupingDimension.NONE,
        required_evidence=_requirements((intent.metric_id,)),
        dataset_ref_id=dataset_ref_id,
        selected_sheet=intent.source.selected_sheet,
        selected_table=intent.source.selected_table,
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
        metric_registry_version=METRIC_REGISTRY_VERSION,
    )


def _canonicalization_request(
    intent: PublicAnalysisIntent,
    dataset_ref_id: str,
    source_headers: tuple[str, ...],
) -> CanonicalizationRequest:
    return CanonicalizationRequest(
        source_dataset_id=dataset_ref_id,
        selected_sheet=intent.source.selected_sheet,
        selected_table=intent.source.selected_table,
        mapping=intent.source.mapping or identity_mapping(source_headers, require_eligibility=True),
        eligibility_mode=EligibilityMode.EXPLICIT_STATUS_MAPPING,
        eligibility_value_mapping=(
            EligibilityValueMapping(source_value="paid", normalized_status=EligibilityState.ELIGIBLE),
            EligibilityValueMapping(source_value="cancelled", normalized_status=EligibilityState.EXCLUDED),
        ),
    )


def _requirements(metrics: tuple[str, ...]) -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(requirement_id="req_global", description="global source authority"),
        *(
            EvidenceRequirement(requirement_id=f"req_{metric}", description=f"{metric} authority", metric_ref=metric)
            for metric in metrics
        ),
    )


def _metric_result(result: AnalysisResult, metric_ref: str) -> MetricResult | None:
    matches = tuple(item for item in result.metric_results if item.metric_ref == metric_ref)
    if len(matches) != 1:
        return None
    return matches[0]


def _select_validated_result_from_metric(
    metric: MetricResult,
    intent: PublicAnalysisIntent,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ValidatedResult:
    candidates = tuple(_load_validated_result(ref, artifact_store, metadata_store) for ref in metric.validated_result_refs)
    if intent.metric_id in PUBLIC_SINGLE_PERIOD_METRICS:
        candidates = tuple(result for result in candidates if result.period_role == intent.result_period_role)
    elif intent.metric_id == "revenue_change":
        candidates = tuple(result for result in candidates if result.metric_ref == "revenue_change")
    if len(candidates) != 1:
        raise ValueError(f"expected one exact ValidatedResult authority, observed {len(candidates)}")
    return candidates[0]


def _load_validated_result(
    validated_result_id: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ValidatedResult:
    records = tuple(
        record
        for record in metadata_store.list_validation_records()
        if record.validated_result_ref == validated_result_id
        and record.validated_result_artifact_ref is not None
    )
    if not records:
        raise ValueError(f"ValidatedResult authority is not exact for {validated_result_id}")
    artifact_paths = tuple(dict.fromkeys(record.validated_result_artifact_ref.path for record in records))
    if len(artifact_paths) != 1:
        raise ValueError(f"ValidatedResult authority is not exact for {validated_result_id}")
    validated = ValidatedResult.model_validate_json(
        artifact_store.safe_path(artifact_paths[0]).read_text(encoding="utf-8")
    )
    if validated.validated_result_id != validated_result_id:
        raise ValueError(f"ValidatedResult artifact identity mismatch for {validated_result_id}")
    return validated


def _select_admissible_evidence_from_metric(
    metric: MetricResult,
    validated: ValidatedResult,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> AdmissibleEvidence:
    wanted_refs = set(metric.admissible_evidence_refs)
    records = tuple(
        record
        for record in metadata_store.list_evidence_admissibility_records()
        if record.status is EvidenceAdmissibilityStatus.PASSED
        and record.admissible_evidence_id in wanted_refs
        and record.validated_result_id == validated.validated_result_id
    )
    if len(records) != 1 or records[0].admissible_evidence_artifact_ref is None:
        raise ValueError(f"AdmissibleEvidence authority is not exact for {validated.validated_result_id}")
    evidence = AdmissibleEvidence.model_validate_json(
        artifact_store.safe_path(records[0].admissible_evidence_artifact_ref.path).read_text(encoding="utf-8")
    )
    if evidence.validated_result_ids != (validated.validated_result_id,):
        raise ValueError("AdmissibleEvidence does not bind the selected exact ValidatedResult")
    return evidence
