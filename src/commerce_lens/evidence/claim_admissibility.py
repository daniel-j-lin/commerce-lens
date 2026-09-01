"""P8-001 deterministic Claim admissibility evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from pydantic import ValidationError

from commerce_lens.contracts.common import ArtifactReference, ClaimState, ClaimType, MetricState, utc_now
from commerce_lens.contracts.evidence import (
    AdmissibleEvidence,
    ClaimCandidate,
    ClaimDecision,
    ClaimPropositionType,
    EvidenceAdmissibilityStatus,
    EvidenceRole,
    P8_CLAIM_MATERIAL_USE,
    claim_candidate_semantic_fingerprint,
)
from commerce_lens.evidence.admissibility import (
    EvidenceAdmissibilityError,
    _authenticate_validated_result,
    _load_request,
    _load_sufficiency,
    _verify_lineage_context,
    _verify_request_metric_context,
    _verify_sufficiency_request_context,
    verify_admissible_evidence_artifact,
)
from commerce_lens.evidence.identifiers import generate_id, sha256_file
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore


CLAIM_POLICY_ID = "commerce_lens_p8_claim_admissibility"
CLAIM_POLICY_VERSION = "p8_001_v1"
SUPPORTED_CLAIM_METRICS = frozenset({"revenue", "orders", "aov", "revenue_change"})


class ClaimAdmissibilityError(ValueError):
    """Raised when P8-001 Claim evaluation fails closed."""

    def __init__(self, failure_code: str, reason: str) -> None:
        super().__init__(reason)
        self.failure_code = failure_code
        self.reason = reason


@dataclass(frozen=True)
class ClaimAdmissibilityOutcome:
    claim_decision: ClaimDecision


@dataclass(frozen=True)
class _AuthenticatedClaimContext:
    candidate: ClaimCandidate
    evidence: AdmissibleEvidence
    evidence_record_id: str
    claim_candidate_fingerprint: str


class ClaimAdmissibilityEvaluator:
    """Narrow static P8-001 deterministic Claim policy evaluator."""

    def __init__(self, *, artifact_store: ArtifactStore, metadata_store: MetadataStore) -> None:
        self.artifact_store = artifact_store
        self.metadata_store = metadata_store

    def evaluate(
        self,
        claim_candidate_id: str,
        *,
        supplied_candidate: ClaimCandidate | None = None,
        supplied_evidence: AdmissibleEvidence | None = None,
        policy_version: str = CLAIM_POLICY_VERSION,
    ) -> ClaimDecision:
        return evaluate_claim_admissibility(
            claim_candidate_id=claim_candidate_id,
            artifact_store=self.artifact_store,
            metadata_store=self.metadata_store,
            supplied_candidate=supplied_candidate,
            supplied_evidence=supplied_evidence,
            policy_version=policy_version,
        ).claim_decision


def persist_claim_candidate(
    candidate: ClaimCandidate,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ClaimCandidate:
    """Persist the authentic structured ClaimCandidate evaluation input."""
    metadata_store.initialize()
    return metadata_store.insert_claim_candidate(candidate, artifact_store)


def evaluate_claim_admissibility(
    *,
    claim_candidate_id: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    supplied_candidate: ClaimCandidate | None = None,
    supplied_evidence: AdmissibleEvidence | None = None,
    policy_version: str = CLAIM_POLICY_VERSION,
) -> ClaimAdmissibilityOutcome:
    """Evaluate one persisted ClaimCandidate against authentic persisted Evidence."""
    metadata_store.initialize()
    candidate: ClaimCandidate | None = None
    claim_candidate_fingerprint: str | None = None
    try:
        if policy_version != CLAIM_POLICY_VERSION:
            raise ClaimAdmissibilityError("policy_version_mismatch", "unsupported Claim policy version")
        context = _authenticate_claim_context(
            claim_candidate_id=claim_candidate_id,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            supplied_candidate=supplied_candidate,
            supplied_evidence=supplied_evidence,
        )
        candidate = context.candidate
        claim_candidate_fingerprint = context.claim_candidate_fingerprint
        _evaluate_supported_claim(context, artifact_store=artifact_store, metadata_store=metadata_store)
        decision = _decision_from_candidate(
            candidate,
            claim_state=ClaimState.ADMISSIBLE,
            reason="structured descriptive Claim matches authentic persisted AdmissibleEvidence",
            failure_code=None,
        )
    except ClaimAdmissibilityError as exc:
        decision = _decision_from_candidate(
            candidate,
            claim_state=ClaimState.INADMISSIBLE,
            reason=exc.reason,
            failure_code=exc.failure_code,
            fallback_candidate_ref=claim_candidate_id,
        )
    persisted = metadata_store.insert_claim_decision(
        decision,
        artifact_store,
        claim_candidate_fingerprint=claim_candidate_fingerprint,
    )
    return ClaimAdmissibilityOutcome(persisted)


def verify_claim_decision_artifact(
    artifact: ArtifactReference,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    expected_decision: ClaimDecision | None = None,
    claim_candidate_fingerprint: str | None = None,
) -> ClaimDecision:
    persisted = metadata_store.get_artifact_reference(artifact.artifact_id)
    if persisted != artifact:
        raise ClaimAdmissibilityError(
            "claim_decision_artifact_hash_mismatch",
            "ClaimDecision artifact reference is missing or mismatched",
        )
    path = artifact_store.safe_path(artifact.path)
    if not path.is_file():
        raise ClaimAdmissibilityError("claim_decision_artifact_hash_mismatch", "ClaimDecision artifact is missing")
    if artifact.fingerprint is None or sha256_file(path) != artifact.fingerprint:
        raise ClaimAdmissibilityError(
            "claim_decision_artifact_hash_mismatch",
            "ClaimDecision artifact hash does not match metadata",
        )
    try:
        decision = ClaimDecision.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise ClaimAdmissibilityError(
            "claim_decision_artifact_hash_mismatch",
            f"ClaimDecision artifact is schema-invalid: {exc}",
        ) from exc
    if expected_decision is not None and decision != expected_decision:
        raise ClaimAdmissibilityError(
            "claim_decision_artifact_hash_mismatch",
            "ClaimDecision artifact content differs from expected decision",
        )
    restored = metadata_store.get_claim_decision(
        decision.claim_decision_id,
        artifact_store,
        claim_candidate_fingerprint=claim_candidate_fingerprint,
    )
    if restored != decision:
        raise ClaimAdmissibilityError(
            "claim_decision_artifact_hash_mismatch",
            "ClaimDecision artifact does not match durable metadata authority",
        )
    return decision


def _authenticate_claim_context(
    *,
    claim_candidate_id: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    supplied_candidate: ClaimCandidate | None,
    supplied_evidence: AdmissibleEvidence | None,
) -> _AuthenticatedClaimContext:
    try:
        candidate = metadata_store.get_claim_candidate(claim_candidate_id, artifact_store)
    except RuntimeError as exc:
        raise ClaimAdmissibilityError(_candidate_failure_code(str(exc)), str(exc)) from exc
    if candidate is None:
        raise ClaimAdmissibilityError(
            "claim_candidate_not_persisted",
            "ClaimCandidate must be persisted before Claim evaluation",
        )
    expected_fingerprint = claim_candidate_semantic_fingerprint(candidate)
    if candidate.claim_candidate_fingerprint != expected_fingerprint:
        raise ClaimAdmissibilityError(
            "claim_candidate_fingerprint_mismatch",
            "ClaimCandidate semantic fingerprint does not match structured semantics",
        )
    if supplied_candidate is not None and supplied_candidate != candidate:
        raise ClaimAdmissibilityError(
            "claim_candidate_fingerprint_mismatch",
            "caller ClaimCandidate differs from persisted authentic evaluation input",
        )
    _precheck_candidate_shape(candidate)
    record, evidence = _load_supporting_evidence(
        candidate,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        supplied_evidence=supplied_evidence,
    )
    return _AuthenticatedClaimContext(candidate, evidence, record.admissibility_id, expected_fingerprint)


def _precheck_candidate_shape(candidate: ClaimCandidate) -> None:
    if candidate.claim_type is not ClaimType.DESCRIPTIVE:
        raise ClaimAdmissibilityError("unsupported_claim_type", "P8-001 supports only descriptive ClaimCandidates")
    if candidate.metric_ref not in SUPPORTED_CLAIM_METRICS:
        raise ClaimAdmissibilityError("unsupported_metric", "Metric is not supported by P8-001 ClaimDecision")
    if candidate.proposition_type not in (
        ClaimPropositionType.METRIC_VALUE_EQUALS,
        ClaimPropositionType.METRIC_STATE_IS,
    ):
        raise ClaimAdmissibilityError("unsupported_proposition_type", "Claim proposition type is not supported by P8-001")
    if candidate.intended_material_use != P8_CLAIM_MATERIAL_USE:
        raise ClaimAdmissibilityError(
            "unsupported_material_claim_strength",
            "ClaimCandidate material use is outside the bounded P8 descriptive material-use policy",
        )
    required = (
        candidate.metric_definition_version,
        candidate.request_id,
        candidate.dataset_ref_id,
        candidate.canonical_dataset_ref_id,
        candidate.canonical_dataset_fingerprint,
        candidate.population_ref,
        candidate.population_fingerprint,
        candidate.period_ref,
        candidate.period_role,
    )
    if any(value in (None, "") for value in required):
        raise ClaimAdmissibilityError(
            "unrepresentable_material_claim",
            "ClaimCandidate lacks required structured material semantics",
        )


def _load_supporting_evidence(
    candidate: ClaimCandidate,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    supplied_evidence: AdmissibleEvidence | None,
):
    if not candidate.supporting_evidence_refs:
        raise ClaimAdmissibilityError("missing_supporting_evidence", "ClaimCandidate lacks supporting Evidence reference")
    if len(candidate.supporting_evidence_refs) != 1:
        raise ClaimAdmissibilityError(
            "duplicate_or_ambiguous_supporting_evidence",
            "P8-001 requires exactly one supporting AdmissibleEvidence reference",
        )
    if len(candidate.supporting_validated_result_refs) != 1:
        raise ClaimAdmissibilityError("wrong_validated_result", "P8-001 requires exactly one supporting ValidatedResult reference")
    evidence_id = candidate.supporting_evidence_refs[0]
    records = tuple(
        record
        for record in metadata_store.list_evidence_admissibility_records()
        if record.status is EvidenceAdmissibilityStatus.PASSED and record.admissible_evidence_id == evidence_id
    )
    if not records:
        raise ClaimAdmissibilityError(
            "missing_persisted_evidence_authority",
            "supporting AdmissibleEvidence lacks persisted successful EvidenceAdmissibilityRecord authority",
        )
    if len(records) > 1:
        raise ClaimAdmissibilityError(
            "duplicate_or_ambiguous_supporting_evidence",
            "supporting AdmissibleEvidence resolves to multiple successful authority records",
        )
    record = records[0]
    if record.admissible_evidence_artifact_ref is None:
        raise ClaimAdmissibilityError("missing_persisted_evidence_authority", "Evidence authority lacks artifact reference")
    try:
        evidence = verify_admissible_evidence_artifact(
            record.admissible_evidence_artifact_ref,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            admissibility_record=record,
        )
    except EvidenceAdmissibilityError as exc:
        raise ClaimAdmissibilityError(_evidence_failure_code(exc.failure_code), exc.reason) from exc
    if supplied_evidence is not None and supplied_evidence != evidence:
        raise ClaimAdmissibilityError("forged_evidence_object", "caller Evidence differs from persisted Evidence authority")
    return record, evidence


def _evaluate_supported_claim(
    context: _AuthenticatedClaimContext,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> None:
    candidate = context.candidate
    evidence = context.evidence
    try:
        request = _load_request(evidence.request_id or "", artifact_store, metadata_store, None)
        sufficiency = _load_sufficiency(evidence.sufficiency_id or "", artifact_store, metadata_store, None)
        _verify_sufficiency_request_context(request, sufficiency)
        auth = _authenticate_validated_result(
            validated_result_id=candidate.supporting_validated_result_refs[0],
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            supplied_validated_result=None,
        )
        result = auth.result
        _verify_request_metric_context(request, result)
        _verify_lineage_context(request, sufficiency, auth)
    except EvidenceAdmissibilityError as exc:
        raise ClaimAdmissibilityError(_evidence_failure_code(exc.failure_code), exc.reason) from exc
    _compare_candidate_to_evidence(candidate, evidence, result, auth.execution_record)


def _compare_candidate_to_evidence(candidate, evidence, result, execution_record) -> None:
    comparisons = (
        (candidate.metric_ref, evidence.metric_ref, "wrong_metric"),
        (candidate.metric_ref, result.metric_ref, "wrong_metric"),
        (candidate.metric_definition_version, evidence.metric_definition_version, "wrong_metric_definition_version"),
        (candidate.metric_definition_version, result.metric_definition_version, "wrong_metric_definition_version"),
        (candidate.request_id, evidence.request_id, "cross_request_substitution"),
        (candidate.dataset_ref_id, evidence.dataset_ref_id, "wrong_dataset"),
        (candidate.canonical_dataset_ref_id, evidence.canonical_dataset_ref_id, "wrong_canonical_dataset"),
        (candidate.canonical_dataset_fingerprint, evidence.canonical_dataset_fingerprint, "wrong_canonical_dataset"),
        (candidate.intended_scope, evidence.scope, "wrong_scope"),
        (candidate.population_ref, evidence.population_ref, "wrong_population"),
        (candidate.population_ref, result.population_ref, "wrong_population"),
        (candidate.population_fingerprint, evidence.population_fingerprint, "wrong_population_fingerprint"),
        (candidate.population_fingerprint, result.population_fingerprint, "wrong_population_fingerprint"),
        (candidate.period_ref, evidence.period_ref, "wrong_period"),
        (candidate.period_ref, result.period_ref, "wrong_period"),
        (candidate.period_role, evidence.period_role, "wrong_period_role"),
        (candidate.period_role, result.period_role, "wrong_period_role"),
        (candidate.unit, result.unit, "wrong_unit"),
        (candidate.currency, result.currency, "wrong_currency"),
    )
    for left, right, code in comparisons:
        if left != right:
            raise ClaimAdmissibilityError(code, f"ClaimCandidate semantic field mismatches Evidence authority: {code}")
    if tuple(candidate.supporting_validated_result_refs) != tuple(evidence.validated_result_ids):
        raise ClaimAdmissibilityError("wrong_validated_result", "ClaimCandidate ValidatedResult ref mismatches Evidence authority")
    if candidate.proposition_type is ClaimPropositionType.METRIC_VALUE_EQUALS:
        if evidence.evidence_role is not EvidenceRole.METRIC_VALUE:
            raise ClaimAdmissibilityError("wrong_evidence_role", "metric_value_equals requires metric_value Evidence")
        if result.metric_state is not MetricState.VALID:
            raise ClaimAdmissibilityError("wrong_metric_state", "numeric Claim requires Valid MetricState")
        if _material_scalar(candidate.claimed_value) != _material_scalar(result.value):
            raise ClaimAdmissibilityError("wrong_claimed_value", "ClaimCandidate value mismatches ValidatedResult authority")
    elif candidate.proposition_type is ClaimPropositionType.METRIC_STATE_IS:
        if evidence.evidence_role is not EvidenceRole.METRIC_STATE:
            raise ClaimAdmissibilityError("wrong_evidence_role", "metric_state_is requires metric_state Evidence")
        if candidate.metric_ref != "aov":
            raise ClaimAdmissibilityError("wrong_metric_state", "P8-001 supports metric_state_is only for governed AOV Undefined")
        if candidate.claimed_metric_state is not result.metric_state or result.metric_state is not MetricState.UNDEFINED:
            raise ClaimAdmissibilityError("wrong_metric_state", "ClaimCandidate MetricState mismatches ValidatedResult authority")
        if candidate.undefined_reason != result.undefined_reason or result.undefined_reason != "orders_equals_zero":
            raise ClaimAdmissibilityError("wrong_undefined_reason", "ClaimCandidate undefined reason mismatches governed AOV authority")
    if candidate.metric_ref == "revenue_change":
        _verify_revenue_change_context(candidate, execution_record)
    elif any(
        value is not None
        for value in (
            candidate.baseline_period_ref,
            candidate.comparison_period_ref,
            candidate.baseline_population_ref,
            candidate.comparison_population_ref,
            candidate.baseline_population_fingerprint,
            candidate.comparison_population_fingerprint,
        )
    ):
        raise ClaimAdmissibilityError("wrong_baseline_comparison_context", "Baseline/Comparison context is only supported for Revenue Change Claims")


def _verify_revenue_change_context(candidate: ClaimCandidate, execution_record) -> None:
    if execution_record.period_refs != (candidate.baseline_period_ref, candidate.comparison_period_ref):
        raise ClaimAdmissibilityError("wrong_baseline_comparison_context", "Revenue Change period context mismatches execution authority")
    if len(execution_record.population_refs) != 2 or len(execution_record.population_fingerprints) != 2:
        raise ClaimAdmissibilityError("wrong_baseline_comparison_context", "Revenue Change execution lacks two-period population authority")
    expected_populations = (candidate.baseline_population_ref, candidate.comparison_population_ref)
    expected_fingerprints = (candidate.baseline_population_fingerprint, candidate.comparison_population_fingerprint)
    if execution_record.population_refs != expected_populations or execution_record.population_fingerprints != expected_fingerprints:
        raise ClaimAdmissibilityError("wrong_baseline_comparison_context", "Revenue Change population context mismatches execution authority")


def _decision_from_candidate(
    candidate: ClaimCandidate | None,
    *,
    claim_state: ClaimState,
    reason: str,
    failure_code: str | None,
    fallback_candidate_ref: str | None = None,
) -> ClaimDecision:
    decision_id = generate_id("clmdec")
    return ClaimDecision(
        claim_decision_id=decision_id,
        decision_id=decision_id,
        claim_candidate_ref=candidate.claim_candidate_id if candidate is not None else fallback_candidate_ref,
        claim_id=candidate.claim_id if candidate is not None else None,
        policy_id=CLAIM_POLICY_ID,
        policy_version=CLAIM_POLICY_VERSION,
        claim_state=claim_state,
        reason=reason,
        failure_code=failure_code,
        supporting_evidence_refs=candidate.supporting_evidence_refs if candidate is not None else (),
        supporting_validated_result_refs=candidate.supporting_validated_result_refs if candidate is not None else (),
        scope=candidate.intended_scope if candidate is not None else None,
        population_ref=candidate.population_ref if candidate is not None else None,
        population_fingerprint=candidate.population_fingerprint if candidate is not None else None,
        period_ref=candidate.period_ref if candidate is not None else None,
        period_role=candidate.period_role if candidate is not None else None,
        baseline_period_ref=candidate.baseline_period_ref if candidate is not None else None,
        comparison_period_ref=candidate.comparison_period_ref if candidate is not None else None,
        baseline_population_ref=candidate.baseline_population_ref if candidate is not None else None,
        comparison_population_ref=candidate.comparison_population_ref if candidate is not None else None,
        baseline_population_fingerprint=candidate.baseline_population_fingerprint if candidate is not None else None,
        comparison_population_fingerprint=candidate.comparison_population_fingerprint if candidate is not None else None,
        decided_at=utc_now(),
    )


def _material_scalar(value):
    if hasattr(value, "to_eng_string"):
        return value.to_eng_string()
    return value


def _candidate_failure_code(message: str) -> str:
    if "artifact missing" in message or "artifact reference missing" in message:
        return "claim_candidate_artifact_missing"
    if "hash mismatch" in message or "row cache mismatches" in message or "durable authority tamper" in message:
        return "claim_candidate_artifact_hash_mismatch"
    if "fingerprint" in message or "indexed authority mismatch" in message:
        return "claim_candidate_fingerprint_mismatch"
    return "claim_candidate_artifact_hash_mismatch"


def _evidence_failure_code(code: str) -> str:
    mapping = {
        "admissible_evidence_artifact_integrity_failure": "tampered_evidence_artifact",
        "validated_result_artifact_hash_mismatch": "wrong_validated_result",
        "validated_result_artifact_missing": "wrong_validated_result",
        "validated_result_metadata_missing": "wrong_validated_result",
        "validation_bundle_incomplete": "missing_validation_record",
        "validation_record_failed": "tampered_validation_record",
        "validation_fingerprint_mismatch": "tampered_validation_record",
        "execution_record_lineage_missing": "mismatched_executed_result_lineage",
        "executed_result_lineage_missing": "mismatched_executed_result_lineage",
        "analysis_request_missing": "cross_request_substitution",
        "analysis_request_tamper_or_mismatch": "cross_request_substitution",
        "dataset_mismatch": "wrong_dataset",
        "period_mismatch": "wrong_period",
        "population_mismatch": "wrong_population",
        "metric_definition_mismatch": "wrong_metric_definition_version",
        "required_evidence_metric_mismatch": "wrong_metric",
    }
    return mapping.get(code, code)
