"""PF3 controlled-case infrastructure and owner-approved controlled evaluators.

This module contains harness-local controlled evaluators for the approved PF3
Class C conformance tranche. These evaluators load verified synthetic facts,
resolve narrow governed authority bindings, and construct ActualProjection
objects for fixture conformance.

They do not constitute production diagnostic runtime behavior and never consult
expected fixture output.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from commerce_lens.fixture_runner.r5_adapters import AdapterRegistration, AdapterRegistry
from commerce_lens.fixture_runner.r5_manifest import (
    ActualProjection,
    ExecutionMode,
    FirstBlocker,
    LoadedR5Fixture,
    Reachability,
    StageName,
    StageProjection,
)
from commerce_lens.fixture_runner.r5_pf2_adapters import build_r5_pf2_adapter_registry


CONTROLLED_PRODUCER_PREFIX = "commerce_lens.fixture_runner.controlled."
_FORBIDDEN_INPUT_ROLES = frozenset({"expected", "fixture_expected", "manifest_expected"})


class ControlledInputError(ValueError):
    """Raised when controlled input facts cannot be loaded safely."""


@dataclass(frozen=True)
class ControlledReference:
    """An immutable identity/fingerprint/version binding from controlled state."""

    reference_id: str
    fingerprint: str | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        if not self.reference_id.strip():
            raise ControlledInputError("controlled reference ID must be nonblank")
        if self.fingerprint is not None and len(self.fingerprint) != 64:
            raise ControlledInputError("controlled fingerprint must be a SHA-256 hex string")
        if self.fingerprint is not None:
            try:
                int(self.fingerprint, 16)
            except ValueError as exc:
                raise ControlledInputError("controlled fingerprint must be hexadecimal") from exc
        if self.version is not None and not self.version.strip():
            raise ControlledInputError("controlled version must be nonblank when supplied")


@dataclass(frozen=True)
class ControlledAuthorityGraph:
    """Small, explicit authority graph used by later controlled evaluators."""

    records: tuple[ControlledReference, ...] = ()

    def resolve(self, reference_id: str) -> ControlledReference | None:
        matches = tuple(item for item in self.records if item.reference_id == reference_id)
        if len(matches) > 1:
            raise ControlledInputError(f"duplicate controlled authority reference: {reference_id}")
        return matches[0] if matches else None

    def require(self, reference_id: str) -> ControlledReference:
        resolved = self.resolve(reference_id)
        if resolved is None:
            raise ControlledInputError(f"controlled authority reference is absent: {reference_id}")
        return resolved


def build_r5_pf3_adapter_registry() -> AdapterRegistry:
    """Return PF2's registry extended with the approved PF3 boundary producers."""

    registry = build_r5_pf2_adapter_registry()
    for registration in (
        AdapterRegistration(
            adapter_id="controlled_diagnostic_admission",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_diagnostic_admission",
            capability_version="pf3_1_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}diagnostic_admission_authority"
            ),
            producer=_produce_diagnostic_admission,
        ),
        AdapterRegistration(
            adapter_id="controlled_alternative_evidence",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_alternative_evidence",
            capability_version="pf3_1_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}alternative_evidence_authority"
            ),
            producer=_produce_alternative_evidence,
        ),
        AdapterRegistration(
            adapter_id="controlled_diagnostic_boundary",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_diagnostic_boundary",
            capability_version="pf3_1_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}diagnostic_promotion_boundary"
            ),
            producer=_produce_diagnostic_boundary,
        ),
        AdapterRegistration(
            adapter_id="controlled_narrowing_boundary",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_narrowing_boundary",
            capability_version="pf3_1_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}narrowing_identity_boundary"
            ),
            producer=_produce_narrowing_boundary,
        ),
        AdapterRegistration(
            adapter_id="controlled_claim_decision_boundary",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_claim_decision",
            capability_version="pf3_2_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}claim_decision_boundary"
            ),
            producer=_produce_claim_decision_boundary,
        ),
        AdapterRegistration(
            adapter_id="controlled_finding_authority",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_finding_authority",
            capability_version="pf3_2_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}finding_authority_boundary"
            ),
            producer=_produce_finding_authority_boundary,
        ),
        AdapterRegistration(
            adapter_id="controlled_claim_rendering",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_claim_rendering",
            capability_version="pf3_2_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}claim_rendering_boundary"
            ),
            producer=_produce_claim_rendering_boundary,
        ),
        AdapterRegistration(
            adapter_id="controlled_causal_boundary",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_causal_boundary",
            capability_version="pf3_2_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}causal_boundary"
            ),
            producer=_produce_causal_boundary,
        ),
        AdapterRegistration(
            adapter_id="controlled_version_boundary",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_version_boundary",
            capability_version="pf3_3_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}version_binding_boundary"
            ),
            producer=_produce_version_boundary,
        ),
        AdapterRegistration(
            adapter_id="controlled_provenance_boundary",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_provenance_boundary",
            capability_version="pf3_3_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}provenance_binding_boundary"
            ),
            producer=_produce_provenance_boundary,
        ),
        AdapterRegistration(
            adapter_id="controlled_chain_boundary",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_chain_boundary",
            capability_version="pf3_3_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}chain_linkage_boundary"
            ),
            producer=_produce_chain_boundary,
        ),
        AdapterRegistration(
            adapter_id="controlled_precision_boundary",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_precision_boundary",
            capability_version="pf3_4_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}precision_precedence_boundary"
            ),
            producer=_produce_precision_boundary,
        ),
        AdapterRegistration(
            adapter_id="controlled_language_corpus",
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name="pf3_controlled_language_corpus",
            capability_version="pf3_5_v1",
            actual_output_producer=(
                f"{CONTROLLED_PRODUCER_PREFIX}language_corpus_boundary"
            ),
            producer=_produce_language_corpus_boundary,
        ),
    ):
        registry.register(registration)
    return registry


def register_controlled_adapter(
    registry: AdapterRegistry,
    *,
    adapter_id: str,
    capability_name: str,
    capability_version: str,
    actual_output_producer: str,
    producer,
) -> None:
    """Register one PF3 controlled producer with truthful namespace binding."""

    if not actual_output_producer.startswith(CONTROLLED_PRODUCER_PREFIX):
        raise ControlledInputError(
            "PF3 controlled producer identity must use the controlled namespace"
        )
    registry.register(
        AdapterRegistration(
            adapter_id=adapter_id,
            execution_mode=ExecutionMode.CONTROLLED_CASE,
            capability_name=capability_name,
            capability_version=capability_version,
            actual_output_producer=actual_output_producer,
            producer=producer,
        )
    )


def load_controlled_json(fixture: LoadedR5Fixture, role: str) -> Any:
    """Load one manifest-bound JSON input by role, never expected output."""

    path = _input_path_for_role(fixture, role)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ControlledInputError(f"controlled JSON input is invalid for role {role!r}") from exc
    _reject_non_finite_numbers(value)
    _reject_conclusion_valued_keys(value)
    return value


def load_controlled_object(fixture: LoadedR5Fixture, role: str) -> Mapping[str, Any]:
    """Load a JSON object input for a controlled evaluator."""

    value = load_controlled_json(fixture, role)
    if not isinstance(value, Mapping):
        raise ControlledInputError(f"controlled input role {role!r} must contain a JSON object")
    return value


def load_controlled_text(fixture: LoadedR5Fixture, role: str) -> str:
    """Load one manifest-bound UTF-8 text input by role."""

    path = _input_path_for_role(fixture, role)
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ControlledInputError(f"controlled text input is invalid for role {role!r}") from exc


def reference_from_mapping(value: Mapping[str, Any], *, field: str = "reference") -> ControlledReference:
    """Parse a lower-level reference record without accepting conclusion fields."""

    raw = value.get(field)
    if not isinstance(raw, Mapping):
        raise ControlledInputError(f"{field} must be an authority reference object")
    forbidden = {"outcome", "disposition", "blocker", "final", "valid", "admissible"}
    if forbidden.intersection(raw):
        raise ControlledInputError(f"{field} contains conclusion-valued fields")
    return ControlledReference(
        reference_id=_required_string(raw, "id", field),
        fingerprint=_optional_string(raw, "fingerprint", field),
        version=_optional_string(raw, "version", field),
    )


def references_match(left: ControlledReference, right: ControlledReference) -> bool:
    """Return true only when supplied identity, fingerprint, and version agree."""

    return (
        left.reference_id == right.reference_id
        and left.fingerprint == right.fingerprint
        and left.version == right.version
    )


def fingerprint_matches(value: bytes | str, fingerprint: str) -> bool:
    """Compare a controlled fingerprint to independently hashed content."""

    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest() == fingerprint


def versions_match(*versions: str | None) -> bool:
    """Require all supplied governed versions to be present and equal."""

    supplied = tuple(version for version in versions if version is not None)
    return bool(supplied) and len(set(supplied)) == 1


def controlled_stage(
    stage: StageName | str,
    reachability: Reachability | str,
    outcome: Any = None,
    *,
    chain_id: str = "main",
    controlling_reason: str | None = None,
    authority_ref: str | None = None,
    not_reached_due_to: StageName | str | None = None,
) -> StageProjection:
    """Construct one strictly validated controlled material-path stage."""

    return StageProjection.model_validate(
        {
            "stage": stage,
            "chain_id": chain_id,
            "reachability": reachability,
            "outcome": outcome,
            "controlling_reason": controlling_reason,
            "authority_ref": authority_ref,
            "not_reached_due_to": not_reached_due_to,
        }
    )


def controlled_blocker(
    blocker_id: str,
    stage: StageName | str,
    reason: str,
    authority_ref: str,
    *,
    chain_id: str = "main",
) -> FirstBlocker:
    """Construct one explicit controlled first-blocker record."""

    return FirstBlocker(
        blocker_id=blocker_id,
        stage=stage,
        chain_id=chain_id,
        reason=reason,
        authority_ref=authority_ref,
    )


def controlled_projection(
    *,
    material_path: Iterable[StageProjection],
    chain_dispositions: Mapping[str, str],
    first_controlling_blocker: FirstBlocker | str,
    final_disposition: str,
    actual_output_producer: str,
    trace_integrity_state: Mapping[str, Any] | str | None = None,
    artifact_evidence_refs: Iterable[str] = (),
) -> ActualProjection:
    """Build an actual projection with controlled producer attribution."""

    if not actual_output_producer.startswith(CONTROLLED_PRODUCER_PREFIX):
        raise ControlledInputError("controlled projection producer is outside controlled namespace")
    return ActualProjection(
        material_path=tuple(material_path),
        chain_dispositions=dict(chain_dispositions),
        first_controlling_blocker=first_controlling_blocker,
        final_disposition=final_disposition,
        trace_integrity_state=trace_integrity_state,
        artifact_evidence_refs=tuple(artifact_evidence_refs),
        actual_output_producer=actual_output_producer,
    )


def _produce_diagnostic_admission(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "authority_state")
    observed_result = reference_from_mapping(state, field="observed_result")
    graph = ControlledAuthorityGraph(_references_from_records(state, "authority_records"))
    required_id = _required_string(state, "required_authority_id", "authority_state")
    authority = graph.resolve(required_id)
    trace = {
        "required_authority_id": required_id,
        "authority_reference_present": authority is not None,
        "observed_result_id": observed_result.reference_id,
    }
    if authority is None:
        stage = controlled_stage(
            "evidence_admissibility",
            "blocked",
            "AUTHORITY_BYPASS__DIAGNOSTIC_OUTPUT_BLOCKED",
            controlling_reason="diagnostic_intended_use_admission_absent",
            authority_ref="R3 v1.0 §26",
        )
        return controlled_projection(
            material_path=(stage, controlled_stage("claim_decision", "not_reached", not_reached_due_to="evidence_admissibility")),
            chain_dispositions={"main": "diagnostic_output_blocked"},
            first_controlling_blocker=controlled_blocker(
                "diagnostic_intended_use_admission",
                "evidence_admissibility",
                "diagnostic_intended_use_admission_absent",
                "R3 v1.0 §26",
            ),
            final_disposition="AUTHORITY_BYPASS__DIAGNOSTIC_OUTPUT_BLOCKED",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}diagnostic_admission_authority",
        )
    return controlled_projection(
        material_path=(controlled_stage("evidence_admissibility", "reached", "diagnostic_input_authority_present"),),
        chain_dispositions={"main": "diagnostic_input_authority_present"},
        first_controlling_blocker="NONE",
        final_disposition="DIAGNOSTIC_INPUT_AUTHORITY_PRESENT__NEXT_STAGE_ONLY",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}diagnostic_admission_authority",
    )


def _produce_alternative_evidence(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "alternative_state")
    observed_result = reference_from_mapping(state, field="observed_result")
    alternative = reference_from_mapping(state, field="alternative_assertion")
    graph = ControlledAuthorityGraph(_references_from_records(state, "evidence_records"))
    required_id = _required_string(state, "required_evidence_id", "alternative_state")
    evidence = graph.resolve(required_id)
    trace = {
        "required_evidence_id": required_id,
        "evidence_reference_present": evidence is not None,
        "observed_result_id": observed_result.reference_id,
        "alternative_assertion_id": alternative.reference_id,
    }
    if evidence is None:
        stage = controlled_stage(
            "alternative_explanation_check",
            "blocked",
            "NON_CONFORMING_ALTERNATIVE_GENERATION",
            controlling_reason="alternative_evidence_authority_absent",
            authority_ref="R1 v1.0 §15.2",
        )
        return controlled_projection(
            material_path=(stage, controlled_stage("claim_decision", "not_reached", not_reached_due_to="alternative_explanation_check")),
            chain_dispositions={"main": "alternative_check_blocked"},
            first_controlling_blocker=controlled_blocker(
                "alternative_evidence_authority",
                "alternative_explanation_check",
                "alternative_evidence_authority_absent",
                "R1 v1.0 §15.2",
            ),
            final_disposition="NON_CONFORMING_ALTERNATIVE_GENERATION",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}alternative_evidence_authority",
        )
    return controlled_projection(
        material_path=(controlled_stage("alternative_explanation_check", "reached", "alternative_evidence_authority_present"),),
        chain_dispositions={"main": "alternative_evidence_authority_present"},
        first_controlling_blocker="NONE",
        final_disposition="ALTERNATIVE_EVIDENCE_AUTHORITY_PRESENT__CHECK_CONTINUES",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}alternative_evidence_authority",
    )


def _produce_diagnostic_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "diagnostic_state")
    proposition = reference_from_mapping(state, field="proposition")
    observed_result = reference_from_mapping(state, field="observed_result")
    graph = ControlledAuthorityGraph(_references_from_records(state, "authority_records"))
    required_id = _required_string(state, "required_authority_id", "diagnostic_state")
    authority = graph.resolve(required_id)
    trace = {
        "required_authority_id": required_id,
        "authority_reference_present": authority is not None,
        "proposition_id": proposition.reference_id,
        "observed_result_id": observed_result.reference_id,
        "support_criterion_evaluated": False,
    }
    if authority is None:
        stage = controlled_stage(
            "analytical_outcome",
            "blocked",
            "DIAGNOSTIC_HYPOTHESIS_ONLY",
            controlling_reason="diagnostic_test_support_authority_absent",
            authority_ref="R1 v1.0 §19.1",
        )
        return controlled_projection(
            material_path=(stage, controlled_stage("claim_decision", "not_reached", not_reached_due_to="analytical_outcome")),
            chain_dispositions={"main": "promotion_blocked"},
            first_controlling_blocker=controlled_blocker(
                "diagnostic_test_support_authority",
                "analytical_outcome",
                "diagnostic_test_support_authority_absent",
                "R1 v1.0 §19.1",
            ),
            final_disposition="DIAGNOSTIC_HYPOTHESIS_ONLY",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}diagnostic_promotion_boundary",
        )
    return controlled_projection(
        material_path=(controlled_stage("analytical_outcome", "reached", "diagnostic_test_support_authority_present"),),
        chain_dispositions={"main": "promotion_prerequisite_resolved__support_not_evaluated"},
        first_controlling_blocker="NONE",
        final_disposition="DIAGNOSTIC_TEST_AUTHORITY_PRESENT__SUPPORT_NOT_EVALUATED",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}diagnostic_promotion_boundary",
    )


def _produce_narrowing_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "narrowing_state")
    original_proposition = reference_from_mapping(state, field="original_proposition")
    original_evaluation = reference_from_mapping(state, field="original_evaluation")
    rendered_proposition_raw = state.get("rendered_proposition")
    if not isinstance(rendered_proposition_raw, Mapping):
        raise ControlledInputError("narrowing_state.rendered_proposition must be an object")
    rendered_proposition = reference_from_mapping(state, field="rendered_proposition")
    rendered_evaluation = reference_from_mapping(state, field="rendered_evaluation")
    coverage = state.get("coverage")
    if not isinstance(coverage, Mapping):
        raise ControlledInputError("narrowing_state.coverage must be an object")
    original_population = _required_string(coverage, "original_population_id", "narrowing_state.coverage")
    covered_population = _required_string(coverage, "covered_population_id", "narrowing_state.coverage")
    identity_changed = not references_match(original_proposition, rendered_proposition) and not references_match(
        original_evaluation, rendered_evaluation
    )
    coverage_matches_rendered = covered_population == _population_id(rendered_proposition_raw, "rendered_proposition")
    trace = {
        "original_proposition_id": original_proposition.reference_id,
        "rendered_proposition_id": rendered_proposition.reference_id,
        "original_evaluation_id": original_evaluation.reference_id,
        "rendered_evaluation_id": rendered_evaluation.reference_id,
        "original_population_id": original_population,
        "covered_population_id": covered_population,
        "identity_changed": identity_changed,
        "coverage_matches_rendered": coverage_matches_rendered,
        "disclaimer_present": _disclaimer_present(state),
    }
    if not identity_changed or not coverage_matches_rendered:
        stage = controlled_stage(
            "analytical_outcome",
            "blocked",
            "BROAD_PROPOSITION_BLOCKED__DISCLAIMER_NO_REPAIR",
            controlling_reason="material_population_coverage_missing",
            authority_ref="R3 v1.0 §27",
        )
        return controlled_projection(
            material_path=(stage, controlled_stage("rendering", "not_reached", not_reached_due_to="analytical_outcome")),
            chain_dispositions={"main": "broad_proposition_blocked"},
            first_controlling_blocker=controlled_blocker(
                "material_population_coverage",
                "analytical_outcome",
                "material_population_coverage_missing",
                "R3 v1.0 §27",
            ),
            final_disposition="BROAD_PROPOSITION_BLOCKED__DISCLAIMER_NO_REPAIR",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}narrowing_identity_boundary",
        )
    return controlled_projection(
        material_path=(controlled_stage("analytical_outcome", "reached", "new_narrowed_identity_observed"),),
        chain_dispositions={"main": "new_evaluation_required"},
        first_controlling_blocker="NONE",
        final_disposition="NARROWED_IDENTITY_OBSERVED__NEW_EVALUATION_REQUIRED",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}narrowing_identity_boundary",
    )


def _produce_claim_decision_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "claim_state")
    requested = _claim_structure(state, "requested_claim")
    decision = _claim_structure(state, "claim_decision")
    rendering = _rendering_structure(state, "attempted_rendering")
    decision_matches_request = _claim_structures_match(requested, decision)
    rendering_matches_decision = _rendering_matches_claim(rendering, decision)
    trace = {
        "requested_claim_class": requested["claim_class"],
        "decision_claim_class": decision["claim_class"],
        "requested_scope_id": requested["scope_id"],
        "decision_scope_id": decision["scope_id"],
        "decision_matches_request": decision_matches_request,
        "rendering_matches_decision": rendering_matches_decision,
        "decision_proposition_id": decision["proposition"].reference_id,
        "rendering_proposition_id": rendering["proposition"].reference_id,
    }
    if not decision_matches_request or not rendering_matches_decision:
        stage = controlled_stage(
            "rendering",
            "blocked",
            "CLAIMDECISION_SCOPE_OR_STRENGTH_MISMATCH__RENDER_BLOCKED",
            controlling_reason="claim_decision_scope_or_strength_mismatch",
            authority_ref="R1 v1.0 §20",
        )
        return controlled_projection(
            material_path=(
                controlled_stage("claim_decision", "reached", "claim_decision_record_observed"),
                stage,
            ),
            chain_dispositions={"main": "render_blocked"},
            first_controlling_blocker=controlled_blocker(
                "claimdecision_scope_or_strength",
                "rendering",
                "claim_decision_scope_or_strength_mismatch",
                "R1 v1.0 §20",
            ),
            final_disposition="CLAIMDECISION_SCOPE_OR_STRENGTH_MISMATCH__RENDER_BLOCKED",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}claim_decision_boundary",
        )
    return controlled_projection(
        material_path=(
            controlled_stage("claim_decision", "reached", "claim_decision_binding_matches"),
            controlled_stage("rendering", "reached", "rendering_binding_matches_claim_decision"),
        ),
        chain_dispositions={"main": "claim_decision_boundary_continues"},
        first_controlling_blocker="NONE",
        final_disposition="CLAIMDECISION_BOUNDARY_MATCHED__NEXT_STAGE_ONLY",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}claim_decision_boundary",
    )


def _produce_finding_authority_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "claim_state")
    candidate = _finding_candidate(state)
    requested = state.get("requested_materialization")
    if not isinstance(requested, Mapping):
        raise ControlledInputError("claim_state.requested_materialization must be an object")
    requested_kind = _required_string(requested, "kind", "claim_state.requested_materialization")
    requested_scope = _required_string(
        requested, "scope_id", "claim_state.requested_materialization"
    )
    candidate_scope_matches_requested = candidate["scope_id"] == requested_scope
    decision_reference = reference_from_mapping(state, field="claim_decision_reference")
    records = _authority_records_with_raw(state, "authority_records")
    matching = tuple(
        (reference, raw)
        for reference, raw in records
        if references_match(reference, decision_reference)
        and raw.get("record_type") == "claim_decision"
        and raw.get("claim_class") == requested_kind
        and raw.get("scope_id") == requested_scope
        and candidate_scope_matches_requested
        and _record_proposition_matches(raw, candidate["proposition"])
    )
    if len(matching) > 1:
        raise ControlledInputError("duplicate matching ClaimDecision authority records")
    decision_present = bool(matching)
    trace = {
        "claim_decision_reference_id": decision_reference.reference_id,
        "claim_decision_reference_present": decision_present,
        "candidate_proposition_id": candidate["proposition"].reference_id,
        "candidate_scope_id": candidate["scope_id"],
        "requested_materialization_kind": requested_kind,
        "requested_scope_id": requested_scope,
        "material_rendering_authority_resolved": decision_present,
    }
    if not decision_present:
        stage = controlled_stage(
            "claim_decision",
            "blocked",
            "AUTHORITY_BYPASS__FINDING_BLOCKED",
            controlling_reason="claim_decision_required_or_denied",
            authority_ref="R1 v1.0 §20",
        )
        return controlled_projection(
            material_path=(
                stage,
                controlled_stage("rendering", "not_reached", not_reached_due_to="claim_decision"),
            ),
            chain_dispositions={"main": "finding_blocked"},
            first_controlling_blocker=controlled_blocker(
                "claim_authority_boundary",
                "claim_decision",
                "claim_decision_required_or_denied",
                "R1 v1.0 §20",
            ),
            final_disposition="AUTHORITY_BYPASS__FINDING_BLOCKED",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}finding_authority_boundary",
        )
    return controlled_projection(
        material_path=(
            controlled_stage("claim_decision", "reached", "authoritative_claim_decision_resolved"),
            controlled_stage(
                "rendering",
                "reached",
                "material_finding_rendering_authority_resolved__next_stage_only",
            ),
        ),
        chain_dispositions={"main": "finding_boundary_continues"},
        first_controlling_blocker="NONE",
        final_disposition="CLAIMDECISION_PRESENT__FINDING_RENDERING_AUTHORITY_RESOLVED",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}finding_authority_boundary",
    )


def _produce_claim_rendering_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "claim_state")
    decision = _claim_structure(state, "claim_decision")
    rendering = _rendering_structure(state, "attempted_rendering")
    rendering_matches_decision = _rendering_matches_claim(rendering, decision)
    trace = {
        "decision_claim_class": decision["claim_class"],
        "rendering_class": rendering["rendering_class"],
        "decision_scope_id": decision["scope_id"],
        "rendering_scope_id": rendering["scope_id"],
        "rendering_matches_decision": rendering_matches_decision,
        "decision_proposition_id": decision["proposition"].reference_id,
        "rendering_proposition_id": rendering["proposition"].reference_id,
    }
    if not rendering_matches_decision:
        stage = controlled_stage(
            "rendering",
            "blocked",
            "RENDER_EXCEEDS_CLAIMDECISION__BLOCKED",
            controlling_reason="rendering_exceeds_claim_decision",
            authority_ref="R1 v1.0 §20",
        )
        return controlled_projection(
            material_path=(
                controlled_stage("claim_decision", "reached", "claim_decision_authority_observed"),
                stage,
            ),
            chain_dispositions={"main": "render_blocked"},
            first_controlling_blocker=controlled_blocker(
                "claim_rendering_strength_boundary",
                "rendering",
                "rendering_exceeds_claim_decision",
                "R1 v1.0 §20",
            ),
            final_disposition="RENDER_EXCEEDS_CLAIMDECISION__BLOCKED",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}claim_rendering_boundary",
        )
    return controlled_projection(
        material_path=(
            controlled_stage("claim_decision", "reached", "claim_decision_authority_observed"),
            controlled_stage("rendering", "reached", "rendering_within_claim_decision"),
        ),
        chain_dispositions={"main": "rendering_boundary_continues"},
        first_controlling_blocker="NONE",
        final_disposition="CLAIMDECISION_BOUNDARY_MATCHED__NEXT_STAGE_ONLY",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}claim_rendering_boundary",
    )


def _produce_causal_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "causal_state")
    requested = _claim_structure(state, "requested_claim")
    if requested["claim_class"] != "causal":
        raise ControlledInputError(
            "controlled causal boundary requires a governed causal requested Claim class"
        )
    basis = state.get("authenticated_supporting_basis")
    if not isinstance(basis, Mapping):
        raise ControlledInputError(
            "causal_state.authenticated_supporting_basis must be an object"
        )
    basis_kind = _required_string(
        basis, "basis_kind", "causal_state.authenticated_supporting_basis"
    )
    supporting_reference = reference_from_mapping(basis, field="reference")
    causal_reference = reference_from_mapping(state, field="causal_authority_reference")
    records = _authority_records_with_raw(state, "authority_records")
    exact_matches = tuple(
        reference
        for reference, raw in records
        if raw.get("record_type") == "causal_authority_reference"
        and references_match(reference, causal_reference)
    )
    if len(exact_matches) > 1:
        raise ControlledInputError(
            "duplicate exact causal authority references: "
            f"{causal_reference.reference_id}"
        )
    causal_authority = exact_matches[0] if exact_matches else None
    trace = {
        "requested_claim_class": requested["claim_class"],
        "requested_scope_id": requested["scope_id"],
        "basis_kind": basis_kind,
        "supporting_reference_id": supporting_reference.reference_id,
        "causal_authority_reference_id": causal_reference.reference_id,
        "causal_authority_reference_present": causal_authority is not None,
        "causal_support_evaluated": False,
    }
    if basis_kind not in _CAUSAL_BOUNDARY_RULES:
        raise ControlledInputError(f"unsupported controlled causal boundary basis: {basis_kind}")
    if causal_authority is None:
        blocker_id, reason, final_disposition = _CAUSAL_BOUNDARY_RULES[basis_kind]
        stage = controlled_stage(
            "claim_decision",
            "blocked",
            final_disposition,
            controlling_reason=reason,
            authority_ref="R1 v1.0 §16",
        )
        return controlled_projection(
            material_path=(stage,),
            chain_dispositions={"main": "claim_prohibited"},
            first_controlling_blocker=controlled_blocker(
                blocker_id,
                "claim_decision",
                reason,
                "R1 v1.0 §16",
            ),
            final_disposition=final_disposition,
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}causal_boundary",
        )
    return controlled_projection(
        material_path=(
            controlled_stage(
                "claim_decision",
                "reached",
                "causal_authority_reference_present__evaluation_continues",
            ),
        ),
        chain_dispositions={"main": "causal_boundary_continues"},
        first_controlling_blocker="NONE",
        final_disposition="CAUSAL_AUTHORITY_PRESENT__SUPPORT_NOT_EVALUATED",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}causal_boundary",
    )


def _produce_version_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "version_state")
    if "historical_binding" in state:
        return _produce_historical_version_boundary(state)
    if "lookup_request" in state:
        return _produce_exact_lookup_boundary(state)
    if "claim_decision_reference" in state:
        return _produce_claim_binding_version_boundary(state)
    if "cached_derivation" in state:
        return _produce_cached_derivation_boundary(state)
    raise ControlledInputError("version_state has no recognized governed binding structure")


def _exact_reference_records(
    records: tuple[tuple[ControlledReference, Mapping[str, Any]], ...],
    target: ControlledReference,
    record_type: str,
) -> tuple[ControlledReference, ...]:
    matches = tuple(
        reference
        for reference, raw in records
        if raw.get("record_type") == record_type and references_match(reference, target)
    )
    if len(matches) > 1:
        raise ControlledInputError(
            f"ambiguous exact PF3 authority binding for {record_type}: {target.reference_id}"
        )
    return matches


def _produce_historical_version_boundary(state: Mapping[str, Any]) -> ActualProjection:
    historical_evaluation = reference_from_mapping(state, field="historical_evaluation_reference")
    historical_binding = state.get("historical_binding")
    current_binding = state.get("current_binding")
    if not isinstance(historical_binding, Mapping) or not isinstance(current_binding, Mapping):
        raise ControlledInputError("historical and current version bindings must be objects")
    historical_binding_evaluation = reference_from_mapping(
        historical_binding, field="evaluation_reference"
    )
    current_binding_evaluation = reference_from_mapping(
        current_binding, field="evaluation_reference"
    )
    historical_authority = reference_from_mapping(
        historical_binding, field="authority_reference"
    )
    current_authority = reference_from_mapping(current_binding, field="authority_reference")
    records = _authority_records_with_raw(state, "authority_records")
    historical_record = _exact_reference_records(
        records, historical_authority, "historical_authority"
    )
    current_record = _exact_reference_records(records, current_authority, "later_authority")
    evaluation_binding_matches = (
        references_match(historical_evaluation, historical_binding_evaluation)
        and references_match(historical_evaluation, current_binding_evaluation)
    )
    historical_identity_preserved = (
        evaluation_binding_matches
        and bool(historical_record)
        and bool(current_record)
        and references_match(historical_authority, current_authority)
    )
    trace = {
        "historical_evaluation_id": historical_evaluation.reference_id,
        "historical_authority_id": historical_authority.reference_id,
        "historical_authority_version": historical_authority.version,
        "current_authority_id": current_authority.reference_id,
        "current_authority_version": current_authority.version,
        "historical_record_present": bool(historical_record),
        "current_record_present": bool(current_record),
        "evaluation_binding_matches": evaluation_binding_matches,
        "historical_identity_preserved": historical_identity_preserved,
    }
    if not historical_identity_preserved:
        stage = controlled_stage(
            "artifact_integrity",
            "blocked",
            "NON_CONFORMING_HISTORICAL_REWRITE",
            controlling_reason="historical_authority_rewritten",
            authority_ref="Architecture v1.0 §19",
        )
        return controlled_projection(
            material_path=(stage,),
            chain_dispositions={"main": "historical_authority_blocked"},
            first_controlling_blocker=controlled_blocker(
                "historical_authority_rewrite",
                "artifact_integrity",
                "historical_authority_rewritten",
                "Architecture v1.0 §19",
            ),
            final_disposition="NON_CONFORMING_HISTORICAL_REWRITE",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}version_binding_boundary",
        )
    return controlled_projection(
        material_path=(
            controlled_stage(
                "artifact_integrity", "reached", "historical_binding_preserved__next_stage_only"
            ),
        ),
        chain_dispositions={"main": "historical_authority_preserved"},
        first_controlling_blocker="NONE",
        final_disposition="HISTORICAL_BINDING_PRESERVED__NEXT_STAGE_ONLY",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}version_binding_boundary",
    )


def _produce_exact_lookup_boundary(state: Mapping[str, Any]) -> ActualProjection:
    required = reference_from_mapping(state, field="required_authority_reference")
    resolved = reference_from_mapping(state, field="resolved_authority_reference")
    lookup = state.get("lookup_request")
    if not isinstance(lookup, Mapping):
        raise ControlledInputError("version_state.lookup_request must be an object")
    resolution_mode = _required_string(lookup, "resolution_mode", "version_state.lookup_request")
    requested = reference_from_mapping(lookup, field="requested_reference")
    records = _authority_records_with_raw(state, "authority_records")
    record_present = bool(_exact_reference_records(records, required, "governed_authority"))
    exact_binding_resolved = (
        resolution_mode == "exact"
        and references_match(requested, required)
        and references_match(resolved, required)
        and record_present
    )
    trace = {
        "required_authority_id": required.reference_id,
        "required_authority_version": required.version,
        "resolved_authority_id": resolved.reference_id,
        "resolved_authority_version": resolved.version,
        "resolution_mode": resolution_mode,
        "authority_record_present": record_present,
        "exact_binding_resolved": exact_binding_resolved,
    }
    if not exact_binding_resolved:
        stage = controlled_stage(
            "evidence_admissibility",
            "blocked",
            "DYNAMIC_AUTHORITY_LOOKUP__BLOCKED",
            controlling_reason="dynamic_authority_lookup",
            authority_ref="Architecture v1.0 §19",
        )
        return controlled_projection(
            material_path=(stage,),
            chain_dispositions={"main": "dynamic_lookup_blocked"},
            first_controlling_blocker=controlled_blocker(
                "dynamic_authority_lookup",
                "evidence_admissibility",
                "dynamic_authority_lookup",
                "Architecture v1.0 §19",
            ),
            final_disposition="DYNAMIC_AUTHORITY_LOOKUP__BLOCKED",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}version_binding_boundary",
        )
    return controlled_projection(
        material_path=(
            controlled_stage(
                "evidence_admissibility", "reached", "exact_authority_binding__next_stage_only"
            ),
        ),
        chain_dispositions={"main": "exact_authority_binding_resolved"},
        first_controlling_blocker="NONE",
        final_disposition="EXACT_AUTHORITY_BINDING__NEXT_STAGE_ONLY",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}version_binding_boundary",
    )


def _produce_claim_binding_version_boundary(state: Mapping[str, Any]) -> ActualProjection:
    requested = _claim_structure(state, "requested_claim")
    decision_reference = reference_from_mapping(state, field="claim_decision_reference")
    records = _authority_records_with_raw(state, "authority_records")
    matches = tuple(
        (reference, raw)
        for reference, raw in records
        if raw.get("record_type") == "claim_decision"
        and references_match(reference, decision_reference)
        and raw.get("claim_class") == requested["claim_class"]
        and raw.get("scope_id") == requested["scope_id"]
        and _record_proposition_matches(raw, requested["proposition"])
    )
    if len(matches) > 1:
        raise ControlledInputError("duplicate matching version-bound ClaimDecision records")
    binding_matches = bool(matches)
    decision_proposition_id = (
        reference_from_mapping({"proposition": matches[0][1]["proposition"]}, field="proposition").reference_id
        if matches
        else None
    )
    trace = {
        "claim_decision_reference_id": decision_reference.reference_id,
        "claim_decision_reference_present": binding_matches,
        "requested_proposition_id": requested["proposition"].reference_id,
        "decision_proposition_id": decision_proposition_id,
        "binding_matches": binding_matches,
    }
    if not binding_matches:
        stage = controlled_stage(
            "claim_decision",
            "blocked",
            "CLAIMDECISION_BINDING_MISMATCH__BLOCKED",
            controlling_reason="claimdecision_proposition_binding_mismatch",
            authority_ref="Architecture v1.0 §19",
        )
        return controlled_projection(
            material_path=(stage,),
            chain_dispositions={"main": "decision_binding_blocked"},
            first_controlling_blocker=controlled_blocker(
                "claimdecision_proposition_binding",
                "claim_decision",
                "claimdecision_proposition_binding_mismatch",
                "Architecture v1.0 §19",
            ),
            final_disposition="CLAIMDECISION_BINDING_MISMATCH__BLOCKED",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}version_binding_boundary",
        )
    return controlled_projection(
        material_path=(
            controlled_stage(
                "claim_decision", "reached", "claimdecision_binding_matches__next_stage_only"
            ),
        ),
        chain_dispositions={"main": "decision_binding_resolved"},
        first_controlling_blocker="NONE",
        final_disposition="CLAIMDECISION_BINDING_MATCHED__NEXT_STAGE_ONLY",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}version_binding_boundary",
    )


def _produce_cached_derivation_boundary(state: Mapping[str, Any]) -> ActualProjection:
    current = reference_from_mapping(state, field="current_evaluation_reference")
    cached = state.get("cached_derivation")
    recomputed = state.get("recomputed_derivation")
    if not isinstance(cached, Mapping) or not isinstance(recomputed, Mapping):
        raise ControlledInputError("cached and recomputed derivations must be objects")
    cached_evaluation = reference_from_mapping(cached, field="evaluation_reference")
    recomputed_evaluation = reference_from_mapping(recomputed, field="evaluation_reference")
    cached_input = _required_string(cached, "input_fingerprint", "cached_derivation")
    recomputed_input = _required_string(
        recomputed, "input_fingerprint", "recomputed_derivation"
    )
    current_fingerprint = current.fingerprint
    if current_fingerprint is None:
        raise ControlledInputError("current evaluation requires a fingerprint")
    evaluation_binding_matches = references_match(current, cached_evaluation) and references_match(
        current, recomputed_evaluation
    )
    cache_matches_recomputation = (
        cached_input == current_fingerprint
        and recomputed_input == current_fingerprint
        and evaluation_binding_matches
    )
    trace = {
        "evaluation_id": current.reference_id,
        "evaluation_version": current.version,
        "cached_input_fingerprint": cached_input,
        "recomputed_input_fingerprint": recomputed_input,
        "evaluation_binding_matches": evaluation_binding_matches,
        "cache_matches_recomputation": cache_matches_recomputation,
    }
    if not cache_matches_recomputation:
        stage = controlled_stage(
            "analytical_outcome",
            "blocked",
            "CACHE_INVALID__AUTHORITATIVE_DERIVATION_WINS",
            controlling_reason="cached_derivation_mismatch",
            authority_ref="R2 v1.0 §14",
        )
        return controlled_projection(
            material_path=(stage,),
            chain_dispositions={"main": "cached_derivation_blocked"},
            first_controlling_blocker=controlled_blocker(
                "cached_derived_disposition",
                "analytical_outcome",
                "cached_derivation_mismatch",
                "R2 v1.0 §14",
            ),
            final_disposition="CACHE_INVALID__AUTHORITATIVE_DERIVATION_WINS",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}version_binding_boundary",
        )
    return controlled_projection(
        material_path=(
            controlled_stage(
                "analytical_outcome", "reached", "authoritative_derivation_current__next_stage_only"
            ),
        ),
        chain_dispositions={"main": "authoritative_derivation_current"},
        first_controlling_blocker="NONE",
        final_disposition="AUTHORITATIVE_DERIVATION_CURRENT__NEXT_STAGE_ONLY",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}version_binding_boundary",
    )


def _produce_provenance_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "provenance_state")
    source_kind = _required_string(state, "source_kind", "provenance_state")
    evidence = reference_from_mapping(state, field="evidence_reference")
    source = reference_from_mapping(state, field="source_reference")
    required_artifact = reference_from_mapping(
        state, field="required_retained_artifact_reference"
    )
    linkage = state.get("provenance_link")
    if not isinstance(linkage, Mapping):
        raise ControlledInputError("provenance_state.provenance_link must be an object")
    linked_evidence = reference_from_mapping(linkage, field="evidence_reference")
    linked_source = reference_from_mapping(linkage, field="source_reference")
    records = _authority_records_with_raw(state, "authority_records")
    evidence_record = _exact_reference_records(records, evidence, "evidence_reference")
    source_record = _exact_reference_records(records, source, "source_reference")
    artifact_record = _exact_reference_records(records, required_artifact, "retained_artifact")
    linkage_matches = references_match(evidence, linked_evidence) and references_match(
        source, linked_source
    )
    retained_binding_resolved = (
        source_kind == "retained_artifact"
        and bool(evidence_record)
        and bool(source_record)
        and bool(artifact_record)
        and linkage_matches
        and references_match(source, required_artifact)
    )
    trace = {
        "source_kind": source_kind,
        "evidence_reference_id": evidence.reference_id,
        "source_reference_id": source.reference_id,
        "required_retained_artifact_id": required_artifact.reference_id,
        "evidence_reference_present": bool(evidence_record),
        "source_reference_present": bool(source_record),
        "retained_artifact_reference_present": bool(artifact_record),
        "provenance_link_matches": linkage_matches,
        "retained_binding_resolved": retained_binding_resolved,
    }
    if retained_binding_resolved:
        return controlled_projection(
            material_path=(
                controlled_stage(
                    "evidence_admissibility",
                    "reached",
                    "retained_provenance_binding__next_stage_only",
                ),
            ),
            chain_dispositions={"main": "retained_provenance_binding_resolved"},
            first_controlling_blocker="NONE",
            final_disposition="RETAINED_PROVENANCE_BINDING__NEXT_STAGE_ONLY",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}provenance_binding_boundary",
        )
    if source_kind == "conversation_memory":
        final_disposition = "NON_AUTHORITATIVE_MEMORY__INADMISSIBLE"
        reason = "non_authoritative_memory"
        blocker_id = "non_authoritative_memory"
    elif source_kind == "public_prose":
        final_disposition = "PUBLIC_PROSE_NOT_RETAINED_AUTHORITY"
        reason = "public_prose_not_retained_authority"
        blocker_id = "retained_artifact_authority"
    else:
        final_disposition = "PROVENANCE_LINKAGE_MISMATCH__BLOCKED"
        reason = "provenance_linkage_mismatch"
        blocker_id = "provenance_linkage"
    stage = controlled_stage(
        "evidence_admissibility",
        "blocked",
        final_disposition,
        controlling_reason=reason,
        authority_ref="Architecture v1.0 §12",
    )
    return controlled_projection(
        material_path=(stage,),
        chain_dispositions={"main": "provenance_blocked"},
        first_controlling_blocker=controlled_blocker(
            blocker_id,
            "evidence_admissibility",
            reason,
            "Architecture v1.0 §12",
        ),
        final_disposition=final_disposition,
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}provenance_binding_boundary",
    )


def _produce_chain_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    state = load_controlled_object(fixture, "chain_state")
    diagnostic = state.get("diagnostic_chain")
    descriptive = state.get("descriptive_chain")
    links = state.get("stage_links")
    if not isinstance(diagnostic, Mapping) or not isinstance(descriptive, Mapping):
        raise ControlledInputError("chain_state chain records must be objects")
    if not isinstance(links, list):
        raise ControlledInputError("chain_state.stage_links must be a list")
    diagnostic_profile = reference_from_mapping(
        diagnostic, field="required_profile_reference"
    )
    descriptive_decision = reference_from_mapping(
        descriptive, field="claim_decision_reference"
    )
    descriptive_rendering = reference_from_mapping(descriptive, field="rendering_reference")
    records = _authority_records_with_raw(state, "authority_records")
    profile_record = _exact_reference_records(records, diagnostic_profile, "r3_profile")
    decision_record = _exact_reference_records(records, descriptive_decision, "claim_decision")
    rendering_record = _exact_reference_records(
        records, descriptive_rendering, "rendering_authority"
    )

    def linked_exact(chain_id: str, stage: str, target: ControlledReference) -> bool:
        matches = tuple(
            reference
            for link in links
            if isinstance(link, Mapping)
            and link.get("chain_id") == chain_id
            and link.get("stage") == stage
            for reference in (
                reference_from_mapping(link, field="reference"),
            )
            if references_match(reference, target)
        )
        if len(matches) > 1:
            raise ControlledInputError(
                f"ambiguous exact PF3 stage link for {chain_id}:{stage}: {target.reference_id}"
            )
        return bool(matches)

    diagnostic_link = linked_exact(
        "product_mix_diagnostic", "evidence_admissibility", diagnostic_profile
    )
    decision_link = linked_exact(
        "revenue_change_descriptive", "claim_decision", descriptive_decision
    )
    rendering_link = linked_exact(
        "revenue_change_descriptive", "rendering", descriptive_rendering
    )
    diagnostic_continuity = bool(profile_record) and diagnostic_link
    descriptive_continuity = bool(decision_record) and bool(rendering_record) and decision_link and rendering_link
    trace = {
        "diagnostic_profile_reference_present": bool(profile_record),
        "diagnostic_profile_link_exact": diagnostic_link,
        "descriptive_claim_decision_link_exact": decision_link,
        "descriptive_rendering_link_exact": rendering_link,
        "diagnostic_chain_continuity": diagnostic_continuity,
        "descriptive_chain_continuity": descriptive_continuity,
    }
    material_path: list[StageProjection] = []
    if diagnostic_continuity:
        material_path.append(
            controlled_stage(
                "evidence_admissibility",
                "reached",
                "exact_r3_profile_resolved",
                chain_id="product_mix_diagnostic",
            )
        )
    else:
        material_path.extend(
            (
                controlled_stage(
                    "evidence_admissibility",
                    "blocked",
                    "R3_PROFILE_NOT_RESOLVED",
                    chain_id="product_mix_diagnostic",
                    controlling_reason="exact_r3_profile_missing",
                    authority_ref="R3 v1.0 §29",
                ),
                controlled_stage(
                    "claim_decision",
                    "not_reached",
                    chain_id="product_mix_diagnostic",
                    not_reached_due_to="evidence_admissibility",
                ),
            )
        )
    if descriptive_continuity:
        material_path.extend(
            (
                controlled_stage(
                    "claim_decision",
                    "reached",
                    "descriptive_claim_decision_resolved",
                    chain_id="revenue_change_descriptive",
                ),
                controlled_stage(
                    "rendering",
                    "reached",
                    "descriptive_claim_rendering_resolved",
                    chain_id="revenue_change_descriptive",
                ),
            )
        )
    else:
        material_path.extend(
            (
                controlled_stage(
                    "claim_decision",
                    "blocked",
                    "DESCRIPTIVE_CHAIN_LINKAGE_BLOCKED",
                    chain_id="revenue_change_descriptive",
                    controlling_reason="descriptive_chain_linkage_missing",
                    authority_ref="Architecture v1.0 §14.7",
                ),
                controlled_stage(
                    "rendering",
                    "not_reached",
                    chain_id="revenue_change_descriptive",
                    not_reached_due_to="claim_decision",
                ),
            )
        )
    if not diagnostic_continuity and not descriptive_continuity:
        raise ControlledInputError(
            "simultaneous independent chain blockers have no governed precedence"
        )
    if not diagnostic_continuity:
        blocker = controlled_blocker(
            "exact_r3_profile_missing",
            "evidence_admissibility",
            "exact_r3_profile_missing",
            "R3 v1.0 §29",
            chain_id="product_mix_diagnostic",
        )
    elif not descriptive_continuity:
        blocker = controlled_blocker(
            "descriptive_chain_linkage",
            "claim_decision",
            "descriptive_chain_linkage_missing",
            "Architecture v1.0 §14.7",
            chain_id="revenue_change_descriptive",
        )
    else:
        blocker = "NONE"
    if not diagnostic_continuity and descriptive_continuity:
        final_disposition = (
            "PARTIAL_MATERIAL_RESULT__DESCRIPTIVE_CLAIM_RENDERABLE__DIAGNOSTIC_WITHHELD"
        )
    elif diagnostic_continuity and descriptive_continuity:
        final_disposition = (
            "PARTIAL_MATERIAL_RESULT__DESCRIPTIVE_CLAIM_RENDERABLE__DIAGNOSTIC_CHAIN_CONTINUES"
        )
    else:
        final_disposition = "CHAIN_LINKAGE_BLOCKED__AFFECTED_CHAIN_WITHHELD"
    return controlled_projection(
        material_path=tuple(material_path),
        chain_dispositions={
            "product_mix_diagnostic": (
                "diagnostic_chain_continues" if diagnostic_continuity else "diagnostic_withheld"
            ),
            "revenue_change_descriptive": (
                "descriptive_claim_renderable"
                if descriptive_continuity
                else "descriptive_chain_blocked"
            ),
        },
        first_controlling_blocker=blocker,
        final_disposition=final_disposition,
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}chain_linkage_boundary",
    )


def _produce_precision_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    """Dispatch the three owner-approved PF3-4 paths by their fact shape only."""

    state = load_controlled_object(fixture, "precision_state")
    if "evidence_admissibility_request" in state:
        return _produce_evidence_precedence_boundary(state)
    if "causal_request" in state:
        return _produce_causal_precedence_boundary(state)
    if "external_dependency" in state:
        return _produce_external_dependency_precedence_boundary(state)
    raise ControlledInputError("precision_state has no recognized governed fact structure")


def _produce_evidence_precedence_boundary(state: Mapping[str, Any]) -> ActualProjection:
    request = state.get("evidence_admissibility_request")
    if not isinstance(request, Mapping):
        raise ControlledInputError("evidence_admissibility_request must be an object")
    evidence = reference_from_mapping(request, field="evidence_reference")
    validation = reference_from_mapping(request, field="validation_reference")
    authority = reference_from_mapping(request, field="admissibility_authority_reference")
    later_support = reference_from_mapping(request, field="later_support_assertion_reference")
    requested_use = request.get("requested_use")
    if not isinstance(requested_use, Mapping):
        raise ControlledInputError("evidence_admissibility_request.requested_use must be an object")
    requested_class = _required_string(
        requested_use, "claim_class", "evidence_admissibility_request.requested_use"
    )
    records = _authority_records_with_raw(request, "authority_records")
    evidence_record = _exact_reference_records(records, evidence, "evidence_reference")
    validation_record = _exact_reference_records(records, validation, "validation_reference")
    authority_record = _exact_reference_records(
        records, authority, "evidence_admissibility_authority"
    )
    support_record = _exact_reference_records(records, later_support, "later_support_assertion")
    if not evidence_record or not validation_record or not authority_record or not support_record:
        raise ControlledInputError("precision evidence path has incomplete exact authority bindings")
    authority_raw = next(
        raw
        for reference, raw in records
        if raw.get("record_type") == "evidence_admissibility_authority"
        and references_match(reference, authority)
    )
    supported_class = _required_string(
        authority_raw, "supported_claim_class", "evidence_admissibility_authority"
    )
    trace_failed = {
        "status": "failed",
        "failure_code": "unsupported_claim_type_for_p6_001",
    }
    if requested_class == supported_class:
        return controlled_projection(
            material_path=(
                controlled_stage(
                    "validation", "reached", "passed"
                ),
                controlled_stage(
                    "evidence_admissibility",
                    "reached",
                    "evidence_admissibility_authority_matches_requested_use__next_stage_only",
                ),
            ),
            chain_dispositions={"main": "analytical_support_continues"},
            first_controlling_blocker="NONE",
            final_disposition="EVIDENCE_ADMISSIBILITY_RESOLVED__NEXT_STAGE_ONLY",
            trace_integrity_state={"status": "passed", "failure_code": None},
            artifact_evidence_refs=(later_support.reference_id,),
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}precision_precedence_boundary",
        )
    return controlled_projection(
        material_path=(
            controlled_stage("validation", "reached", "passed"),
            controlled_stage(
                "evidence_admissibility",
                "blocked",
                "EVIDENCE_INADMISSIBLE__ANALYTICAL_SUPPORT_NOT_REACHED",
                controlling_reason="unsupported_claim_type_for_p6_001",
                authority_ref="R1 v1.0 §19.2",
            ),
            controlled_stage(
                "analytical_outcome",
                "not_reached",
                not_reached_due_to="evidence_admissibility",
            ),
        ),
        chain_dispositions={"main": "analytical_support_unreachable"},
        first_controlling_blocker=controlled_blocker(
            "evidence_admissibility",
            "evidence_admissibility",
            "unsupported_claim_type_for_p6_001",
            "R1 v1.0 §19.2",
        ),
        final_disposition="EVIDENCE_INADMISSIBLE__ANALYTICAL_SUPPORT_NOT_REACHED",
        trace_integrity_state=trace_failed,
        artifact_evidence_refs=(later_support.reference_id,),
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}precision_precedence_boundary",
    )


def _produce_causal_precedence_boundary(state: Mapping[str, Any]) -> ActualProjection:
    request = state.get("causal_request")
    if not isinstance(request, Mapping):
        raise ControlledInputError("causal_request must be an object")
    requested = _claim_structure(request, "requested_claim")
    evidence = reference_from_mapping(request, field="diagnostic_evidence_reference")
    causal_authority = reference_from_mapping(request, field="causal_authority_reference")
    evidence_kind = _required_string(request, "evidence_kind", "causal_request")
    records = _authority_records_with_raw(request, "authority_records")
    evidence_record = _exact_reference_records(records, evidence, "diagnostic_evidence")
    causal_record = _exact_reference_records(records, causal_authority, "causal_authority")
    if not evidence_record:
        raise ControlledInputError("precision causal path has incomplete exact evidence bindings")
    evidence_raw = next(
        raw
        for reference, raw in records
        if raw.get("record_type") == "diagnostic_evidence"
        and references_match(reference, evidence)
    )
    authenticated_evidence_form = _required_string(
        evidence_raw, "evidence_form", "diagnostic_evidence authority record"
    )
    if evidence_kind != authenticated_evidence_form:
        raise ControlledInputError(
            "declared evidence kind disagrees with authenticated diagnostic evidence form"
        )
    if authenticated_evidence_form != "diagnostic_association":
        raise ControlledInputError("precision causal path requires diagnostic association facts")
    trace = {
        "requested_claim_class": requested["claim_class"],
        "diagnostic_evidence_reference_present": True,
        "causal_authority_reference_present": bool(causal_record),
    }
    if requested["claim_class"] != "causal":
        return controlled_projection(
            material_path=(
                controlled_stage(
                    "claim_decision",
                    "reached",
                    "claim_class_boundary_changed__next_stage_only",
                ),
            ),
            chain_dispositions={"main": "claim_class_boundary_changed"},
            first_controlling_blocker="NONE",
            final_disposition="CLAIM_CLASS_BOUNDARY_CHANGED__NEXT_STAGE_ONLY",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}precision_precedence_boundary",
        )
    if causal_record:
        return controlled_projection(
            material_path=(
                controlled_stage(
                    "claim_decision",
                    "reached",
                    "causal_authority_reference_present__evaluation_continues",
                ),
            ),
            chain_dispositions={"main": "causal_boundary_continues"},
            first_controlling_blocker="NONE",
            final_disposition="CAUSAL_AUTHORITY_PRESENT__SUPPORT_NOT_EVALUATED",
            trace_integrity_state=trace,
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}precision_precedence_boundary",
        )
    return controlled_projection(
        material_path=(
            controlled_stage(
                "claim_decision",
                "blocked",
                "CLAIM_PROHIBITED__ASSOCIATION_IS_NOT_CAUSATION",
                controlling_reason="association_is_not_causation",
                authority_ref="R1 v1.0 §19.2",
            ),
        ),
        chain_dispositions={"main": "claim_prohibited"},
        first_controlling_blocker=controlled_blocker(
            "association_is_not_causation",
            "claim_decision",
            "association_is_not_causation",
            "R1 v1.0 §19.2",
        ),
        final_disposition="CLAIM_PROHIBITED__ASSOCIATION_IS_NOT_CAUSATION",
        trace_integrity_state=trace,
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}precision_precedence_boundary",
    )


def _produce_external_dependency_precedence_boundary(state: Mapping[str, Any]) -> ActualProjection:
    dependency = state.get("external_dependency")
    if not isinstance(dependency, Mapping):
        raise ControlledInputError("external_dependency must be an object")
    dependency_ref = reference_from_mapping(dependency, field="dependency_reference")
    resolution_ref = reference_from_mapping(dependency, field="resolution_authority_reference")
    defect_ref = reference_from_mapping(dependency, field="later_internal_defect_reference")
    declared_resolution_state = _required_string(
        dependency, "resolution_state", "external_dependency"
    )
    records = _authority_records_with_raw(dependency, "authority_records")
    dependency_record = _exact_reference_records(records, dependency_ref, "external_dependency")
    resolution_record = _exact_reference_records(
        records, resolution_ref, "dependency_resolution_authority"
    )
    defect_record = _exact_reference_records(records, defect_ref, "later_internal_defect")
    if not dependency_record or not resolution_record or not defect_record:
        raise ControlledInputError("precision dependency path has incomplete exact authority bindings")
    dependency_raw = next(
        raw
        for reference, raw in records
        if raw.get("record_type") == "external_dependency"
        and references_match(reference, dependency_ref)
    )
    authenticated_resolution_state = _required_string(
        dependency_raw, "resolution_state", "external_dependency authority record"
    )
    if declared_resolution_state != authenticated_resolution_state:
        raise ControlledInputError(
            "declared resolution state disagrees with authenticated external dependency record"
        )
    independent = dependency.get("independent_stage_reference")
    if independent is not None:
        if not isinstance(independent, Mapping):
            raise ControlledInputError("independent_stage_reference must be an object")
        independent_ref = reference_from_mapping(
            {"independent_stage_reference": independent}, field="independent_stage_reference"
        )
        if _exact_reference_records(records, independent_ref, "independent_stage"):
            raise ControlledInputError(
                "independent simultaneous blockers have no governed precedence"
            )
    trace = {
        "dependency_resolution_state": authenticated_resolution_state,
        "external_dependency_reference_present": True,
        "later_internal_defect_present": True,
        "later_internal_defect_evaluated": False,
    }
    if authenticated_resolution_state == "resolved":
        return controlled_projection(
            material_path=(
                controlled_stage(
                    "evidence_admissibility",
                    "reached",
                    "external_dependency_resolved__next_stage_only",
                ),
            ),
            chain_dispositions={"main": "external_dependency_resolved"},
            first_controlling_blocker="NONE",
            final_disposition="EXTERNAL_DEPENDENCY_RESOLVED__NEXT_STAGE_ONLY",
            trace_integrity_state=trace,
            artifact_evidence_refs=(defect_ref.reference_id,),
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}precision_precedence_boundary",
        )
    if authenticated_resolution_state != "unresolved":
        raise ControlledInputError("external dependency resolution state is not governed")
    return controlled_projection(
        material_path=(
            controlled_stage(
                "evidence_admissibility",
                "blocked",
                "EXTERNAL_EVIDENCE_REQUIRED",
                controlling_reason="external_dependency_unresolved",
                authority_ref="R1 v1.0 §19.2",
            ),
            controlled_stage(
                "analytical_outcome",
                "not_reached",
                not_reached_due_to="evidence_admissibility",
            ),
        ),
        chain_dispositions={"main": "external_dependency_blocks_later_internal_stage"},
        first_controlling_blocker=controlled_blocker(
            "external_dependency",
            "evidence_admissibility",
            "external_dependency_unresolved",
            "R1 v1.0 §19.2",
        ),
        final_disposition="EXTERNAL_EVIDENCE_REQUIRED",
        trace_integrity_state=trace,
        artifact_evidence_refs=(defect_ref.reference_id,),
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}precision_precedence_boundary",
    )


@dataclass(frozen=True)
class _ControlledLanguageForm:
    classification: str
    authority_kind: str | None = None


_CONTROLLED_LANGUAGE_FORMS = {
    "Comparison-only products account for USD 100.00 of the mechanical Revenue difference under Product-Level Revenue Decomposition R4 v1.0.\n": _ControlledLanguageForm("PERMITTED_MECHANICAL"),
    "New products caused Revenue growth of USD 100.00.\n": _ControlledLanguageForm("PROHIBITED_CAUSAL"),
    "The Continuing-Product Revenue Change Component is USD −20.00 under Product-Level Revenue Decomposition R4 v1.0.\n": _ControlledLanguageForm("PERMITTED_MECHANICAL"),
    "Existing products drove the USD 20.00 decline.\n": _ControlledLanguageForm("PROHIBITED_DIAGNOSTIC_OR_CAUSAL"),
    "Under Product-Level Revenue Decomposition R4 v1.0, the Entry Component mechanically contributed USD 100.00.\n": _ControlledLanguageForm("PERMITTED_METHOD_RELATIVE_MECHANICAL"),
    "Entry products were the main reason Revenue increased by USD 100.00.\n": _ControlledLanguageForm("PROHIBITED_PRIMACY_AND_EXPLANATION"),
    "New products likely caused Revenue growth of USD 100.00.\n": _ControlledLanguageForm("PROHIBITED_CAUSAL__SOFTENER_NO_REPAIR"),
    "Continuing products appear to explain the USD 20.00 decline.\n": _ControlledLanguageForm("PROHIBITED_DIAGNOSTIC__SOFTENER_NO_REPAIR"),
    "The validated descriptive result shows Revenue declined by USD 20.00 for all eligible orders.\n": _ControlledLanguageForm("PERMITTED_OBSERVED_FINDING_WORDING", "claim_rendering"),
    "Under Product-Level Revenue Decomposition R4 v1.0, the Continuing-Product Revenue Change Component is USD −20.00.\n": _ControlledLanguageForm("PERMITTED_MECHANICAL_WORDING", "mechanical_method"),
    "Hypothesis: continuing products may explain the USD 20.00 decline; this is not a Finding.\n": _ControlledLanguageForm("PERMITTED_HYPOTHESIS_WORDING__NO_FINDING", "diagnostic_hypothesis"),
    "External evidence is required before evaluating this explanation.\n": _ControlledLanguageForm("PERMITTED_EXTERNAL_EVIDENCE_WORDING", "external_dependency"),
    "The causal claim is prohibited under current authority.\n": _ControlledLanguageForm("PERMITTED_CAUSAL_REFUSAL", "causal_refusal"),
    "Continuing products may appear to explain the USD 20.00 decline, but this remains unsupported.\n": _ControlledLanguageForm("PROHIBITED_MEANING__SOFTENER_NO_REPAIR"),
}


def _produce_language_corpus_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    utterance = load_controlled_text(fixture, "utterance")
    form = _CONTROLLED_LANGUAGE_FORMS.get(utterance)
    producer = f"{CONTROLLED_PRODUCER_PREFIX}language_corpus_boundary"
    if form is None:
        stage = controlled_stage(
            "rendering",
            "blocked",
            "CONTROLLED_LANGUAGE_FORM_UNRECOGNIZED",
            controlling_reason="exact_controlled_form_unrecognized",
            authority_ref="R5 v1.0 §22",
        )
        return controlled_projection(
            material_path=(stage,),
            chain_dispositions={"main": "controlled_language_form_unrecognized"},
            first_controlling_blocker=controlled_blocker(
                "exact_controlled_form_unrecognized",
                "rendering",
                "exact_controlled_form_unrecognized",
                "R5 v1.0 §22",
            ),
            final_disposition="CONTROLLED_LANGUAGE_FORM_UNRECOGNIZED",
            trace_integrity_state={
                "exact_form_match": False,
                "authority_required": False,
                "authority_binding_resolved": False,
            },
            actual_output_producer=producer,
        )
    authority_resolved, authority_refs = _language_authority_binding(fixture, form.authority_kind)
    trace = {
        "exact_form_match": True,
        "authority_required": form.authority_kind is not None,
        "authority_binding_resolved": authority_resolved,
    }
    if form.authority_kind is not None and not authority_resolved:
        stage = controlled_stage(
            "rendering",
            "blocked",
            "CONTROLLED_LANGUAGE_AUTHORITY_REQUIRED__BLOCKED",
            controlling_reason="required_structured_language_authority_absent_or_mismatched",
            authority_ref="R1 v1.0 §§21–22",
        )
        return controlled_projection(
            material_path=(stage,),
            chain_dispositions={"main": "controlled_language_authority_blocked"},
            first_controlling_blocker=controlled_blocker(
                "required_language_authority",
                "rendering",
                "required_structured_language_authority_absent_or_mismatched",
                "R1 v1.0 §§21–22",
            ),
            final_disposition="CONTROLLED_LANGUAGE_AUTHORITY_REQUIRED__BLOCKED",
            trace_integrity_state=trace,
            actual_output_producer=producer,
        )
    return controlled_projection(
        material_path=(
            controlled_stage(
                "rendering",
                "reached",
                {"classification": form.classification, "text": utterance},
            ),
        ),
        chain_dispositions={"main": "controlled_language_classification"},
        first_controlling_blocker="NONE",
        final_disposition=form.classification,
        trace_integrity_state=trace,
        artifact_evidence_refs=authority_refs,
        actual_output_producer=producer,
    )


def _language_authority_binding(
    fixture: LoadedR5Fixture, authority_kind: str | None
) -> tuple[bool, tuple[str, ...]]:
    if authority_kind is None:
        return True, ()
    state = load_controlled_object(fixture, "language_state")
    records = _authority_records_with_raw(state, "authority_records")
    if authority_kind == "claim_rendering":
        requested = _claim_structure(state, "requested_claim")
        result = reference_from_mapping(state, field="validated_result_reference")
        decision = reference_from_mapping(state, field="claim_decision_reference")
        rendering = reference_from_mapping(state, field="rendering_authority_reference")
        result_match = _exact_reference_records(records, result, "validated_result")
        decision_match = _exact_reference_records(records, decision, "claim_decision")
        rendering_match = _exact_reference_records(records, rendering, "rendering_authority")
        if not result_match or not decision_match or not rendering_match:
            return False, ()
        decision_raw = next(
            raw
            for reference, raw in records
            if raw.get("record_type") == "claim_decision"
            and references_match(reference, decision)
        )
        rendering_raw = next(
            raw
            for reference, raw in records
            if raw.get("record_type") == "rendering_authority"
            and references_match(reference, rendering)
        )
        bound = (
            decision_raw.get("claim_class") == requested["claim_class"]
            and decision_raw.get("scope_id") == requested["scope_id"]
            and _record_proposition_matches(decision_raw, requested["proposition"])
            and rendering_raw.get("rendering_class") == requested["claim_class"]
            and rendering_raw.get("scope_id") == requested["scope_id"]
            and _record_proposition_matches(rendering_raw, requested["proposition"])
        )
        return bound, (result.reference_id, decision.reference_id, rendering.reference_id) if bound else ()
    if authority_kind == "mechanical_method":
        method = reference_from_mapping(state, field="method_reference")
        matches = _exact_reference_records(records, method, "method_authority")
        if not matches:
            return False, ()
        raw = next(
            raw
            for reference, raw in records
            if raw.get("record_type") == "method_authority"
            and references_match(reference, method)
        )
        return raw.get("method_kind") == "revenue_decomposition", (method.reference_id,)
    if authority_kind == "diagnostic_hypothesis":
        hypothesis = reference_from_mapping(state, field="hypothesis_reference")
        proposition = reference_from_mapping(state, field="proposition_reference")
        matches = _exact_reference_records(records, hypothesis, "hypothesis_authority")
        if not matches:
            return False, ()
        raw = next(
            raw
            for reference, raw in records
            if raw.get("record_type") == "hypothesis_authority"
            and references_match(reference, hypothesis)
        )
        bound = raw.get("hypothesis_form") == "explicit_diagnostic_hypothesis" and _record_proposition_matches(raw, proposition)
        return bound, (hypothesis.reference_id,) if bound else ()
    if authority_kind == "external_dependency":
        dependency = reference_from_mapping(state, field="dependency_reference")
        matches = _exact_reference_records(records, dependency, "external_dependency")
        if not matches:
            return False, ()
        raw = next(
            raw
            for reference, raw in records
            if raw.get("record_type") == "external_dependency"
            and references_match(reference, dependency)
        )
        return raw.get("resolution_state") == "unresolved", (dependency.reference_id,)
    if authority_kind == "causal_refusal":
        requested = _claim_structure(state, "requested_claim")
        refusal = reference_from_mapping(state, field="causal_refusal_reference")
        matches = _exact_reference_records(records, refusal, "causal_refusal")
        if not matches:
            return False, ()
        raw = next(
            raw
            for reference, raw in records
            if raw.get("record_type") == "causal_refusal"
            and references_match(reference, refusal)
        )
        bound = requested["claim_class"] == "causal" and raw.get("refusal_kind") == "causal_claim_class_restriction"
        return bound, (refusal.reference_id,) if bound else ()
    raise ControlledInputError(f"unsupported controlled language authority kind: {authority_kind}")


_CAUSAL_BOUNDARY_RULES = {
    "historical_transactional_correlation": (
        "causal_standard_absent",
        "causal_standard_absent",
        "CLAIM_PROHIBITED__CAUSAL_STANDARD_ABSENT",
    ),
    "mechanical_decomposition": (
        "mechanical_is_not_causal",
        "mechanical_is_not_causal",
        "CLAIM_PROHIBITED__MECHANICAL_IS_NOT_CAUSAL",
    ),
    "diagnostic_association": (
        "association_is_not_causation",
        "association_is_not_causation",
        "CLAIM_PROHIBITED__ASSOCIATION_IS_NOT_CAUSATION",
    ),
    "statistical_significance": (
        "significance_is_not_causal_authority",
        "significance_is_not_causal_authority",
        "CLAIM_PROHIBITED__SIGNIFICANCE_IS_NOT_CAUSAL_AUTHORITY",
    ),
    "partial_alternative_removal": (
        "causal_standard_absent",
        "causal_standard_absent",
        "CLAIM_PROHIBITED__CAUSAL_STANDARD_ABSENT",
    ),
    "direct_causal_request": (
        "causal_authority_unavailable",
        "causal_authority_unavailable",
        "CLAIM_PROHIBITED__CAUSAL_AUTHORITY_UNAVAILABLE",
    ),
}


def _claim_structure(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    raw = value.get(field)
    if not isinstance(raw, Mapping):
        raise ControlledInputError(f"{field} must be a structured Claim record")
    proposition = raw.get("proposition")
    if not isinstance(proposition, Mapping):
        raise ControlledInputError(f"{field}.proposition must be an authority reference object")
    return {
        "claim_class": _required_string(raw, "claim_class", field),
        "scope_id": _required_string(raw, "scope_id", field),
        "proposition": reference_from_mapping(raw, field="proposition"),
    }


def _rendering_structure(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    raw = value.get(field)
    if not isinstance(raw, Mapping):
        raise ControlledInputError(f"{field} must be a structured rendering record")
    return {
        "rendering_class": _required_string(raw, "rendering_class", field),
        "scope_id": _required_string(raw, "scope_id", field),
        "proposition": reference_from_mapping(raw, field="proposition"),
    }


def _claim_structures_match(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return (
        left["claim_class"] == right["claim_class"]
        and left["scope_id"] == right["scope_id"]
        and references_match(left["proposition"], right["proposition"])
    )


def _rendering_matches_claim(
    rendering: Mapping[str, Any], claim: Mapping[str, Any]
) -> bool:
    return (
        rendering["rendering_class"] == claim["claim_class"]
        and rendering["scope_id"] == claim["scope_id"]
        and references_match(rendering["proposition"], claim["proposition"])
    )


def _finding_candidate(value: Mapping[str, Any]) -> dict[str, Any]:
    raw = value.get("finding_candidate")
    if not isinstance(raw, Mapping):
        raise ControlledInputError("claim_state.finding_candidate must be a structured record")
    proposition = raw.get("proposition")
    if not isinstance(proposition, Mapping):
        raise ControlledInputError(
            "claim_state.finding_candidate.proposition must be an authority reference object"
        )
    return {
        "proposition": reference_from_mapping(raw, field="proposition"),
        "scope_id": _required_string(raw, "scope_id", "claim_state.finding_candidate"),
    }


def _authority_records_with_raw(
    value: Mapping[str, Any], key: str
) -> tuple[tuple[ControlledReference, Mapping[str, Any]], ...]:
    records = value.get(key)
    if not isinstance(records, list):
        raise ControlledInputError(f"{key} must be a list of authority records")
    parsed: list[tuple[ControlledReference, Mapping[str, Any]]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise ControlledInputError(f"{key} entries must be authority records")
        parsed.append((reference_from_mapping({"authority": record}, field="authority"), record))
    return tuple(parsed)


def _record_proposition_matches(
    record: Mapping[str, Any], proposition: ControlledReference
) -> bool:
    raw = record.get("proposition")
    if not isinstance(raw, Mapping):
        return False
    record_proposition = reference_from_mapping(
        {"proposition": raw}, field="proposition"
    )
    return references_match(record_proposition, proposition)


def _input_path_for_role(fixture: LoadedR5Fixture, role: str) -> Path:
    if not role.strip() or role in _FORBIDDEN_INPUT_ROLES:
        raise ControlledInputError(f"input role is not permitted for controlled evaluation: {role!r}")
    matches = tuple(
        path
        for spec, path in zip(fixture.manifest.inputs, fixture.input_paths, strict=True)
        if spec.role == role
    )
    if len(matches) != 1:
        raise ControlledInputError(f"expected exactly one controlled input for role {role!r}")
    return matches[0]


def _required_string(value: Mapping[str, Any], key: str, field: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ControlledInputError(f"{field}.{key} must be a nonblank string")
    return item


def _optional_string(value: Mapping[str, Any], key: str, field: str) -> str | None:
    item = value.get(key)
    if item is not None and (not isinstance(item, str) or not item.strip()):
        raise ControlledInputError(f"{field}.{key} must be a nonblank string when supplied")
    return item


def _reject_non_finite_numbers(value: Any) -> None:
    if isinstance(value, float):
        raise ControlledInputError("binary floating-point values are forbidden in controlled input")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_non_finite_numbers(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_non_finite_numbers(item)


def _reject_conclusion_valued_keys(value: Any) -> None:
    forbidden = {
        "expected",
        "outcome",
        "disposition",
        "blocker",
        "final",
        "valid",
        "admissible",
        "chain_valid",
        "continuity_ok",
        "provenance_valid",
        "version_valid",
        "support_evaluated",
        "causal_support_evaluated",
        "diagnostic_support_evaluated",
        "final_disposition",
        "chain_disposition",
    }
    if isinstance(value, Mapping):
        if forbidden.intersection(value):
            raise ControlledInputError("controlled input contains conclusion-valued fields")
        for item in value.values():
            _reject_conclusion_valued_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_conclusion_valued_keys(item)


def _references_from_records(value: Mapping[str, Any], key: str) -> tuple[ControlledReference, ...]:
    records = value.get(key)
    if not isinstance(records, list):
        raise ControlledInputError(f"{key} must be a list of authority references")
    parsed: list[ControlledReference] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise ControlledInputError(f"{key} entries must be authority reference objects")
        parsed.append(reference_from_mapping({"authority": record}, field="authority"))
    return tuple(parsed)


def _population_id(value: Mapping[str, Any], field: str) -> str:
    population_id = value.get("population_id")
    if not isinstance(population_id, str) or not population_id.strip():
        raise ControlledInputError(f"{field}.population_id must be a nonblank string")
    return population_id


def _disclaimer_present(value: Mapping[str, Any]) -> bool:
    rendering = value.get("rendering")
    if not isinstance(rendering, Mapping):
        raise ControlledInputError("narrowing_state.rendering must be an object")
    text = rendering.get("disclaimer_text")
    return isinstance(text, str) and bool(text.strip())


__all__ = (
    "CONTROLLED_PRODUCER_PREFIX",
    "ControlledAuthorityGraph",
    "ControlledInputError",
    "ControlledReference",
    "build_r5_pf3_adapter_registry",
    "controlled_blocker",
    "controlled_projection",
    "controlled_stage",
    "fingerprint_matches",
    "load_controlled_json",
    "load_controlled_object",
    "load_controlled_text",
    "reference_from_mapping",
    "register_controlled_adapter",
    "references_match",
    "versions_match",
)
