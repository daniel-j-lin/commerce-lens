from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from commerce_lens.contracts.r7 import (
    DiagnosticEvidenceInputBinding,
    DiagnosticEvidenceInputSet,
    DiagnosticTestRequest,
    R7AuthorityReference,
    diagnostic_test_request_fingerprint,
    evidence_input_set_fingerprint,
)
from commerce_lens.diagnostic.r7_method_registry import (
    FAMILY_FINGERPRINT,
    FAMILY_ID,
    FAMILY_VERSION,
    METHOD_DEFINITION,
    R7_METHOD_REGISTRY,
    authority_ref,
)
from commerce_lens.evidence.identifiers import stable_content_id
from commerce_lens.contracts.diagnostic import AuthorityBinding


HASH = "a" * 64


def _evidence_set():
    binding = DiagnosticEvidenceInputBinding(
        requirement_judgment_ref="judgment:1", evidence_ref="evidence:1", evidence_fingerprint=HASH,
        evidence_assessment_ref="assessment:1", evidence_assessment_fingerprint=HASH,
        diagnostic_admission_authority=AuthorityBinding(authority_ref="admission:1", authority_version="1", authority_fingerprint=HASH),
        admission_state="DIAGNOSTIC_ADMITTED", fitness_state="PASSED", source_class="GOVERNED_INTERNAL",
        scope_ref="scope:1", period_refs=("period:b", "period:c"), population_refs=("population:b", "population:c"),
        metric_refs=("metric:revenue_change@metric_dictionary_v1",), variable_refs=("field:product_id", "field:line_revenue"),
    )
    data = {"evidence_input_set_id":"pending", "diagnostic_proposition_ref":"prop:1", "diagnostic_proposition_fingerprint":HASH, "bindings":(binding,)}
    fp = evidence_input_set_fingerprint(data); data.update(evidence_input_set_fingerprint=fp, evidence_input_set_id=stable_content_id("r7evid", fp))
    return DiagnosticEvidenceInputSet(**data)


def test_registry_has_exactly_one_current_method_and_rejects_unknown_stale_or_family_mismatch():
    ref = authority_ref(METHOD_DEFINITION)
    assert R7_METHOD_REGISTRY.authenticate(ref, FAMILY_ID, FAMILY_VERSION, FAMILY_FINGERPRINT) is METHOD_DEFINITION
    for changed in (
        ref.model_copy(update={"authority_id":"unknown"}), ref.model_copy(update={"authority_version":"0"}),
        ref.model_copy(update={"authority_fingerprint":HASH}),
    ):
        with pytest.raises(ValueError, match="method_unregistered_or_stale"):
            R7_METHOD_REGISTRY.authenticate(changed, FAMILY_ID, FAMILY_VERSION, FAMILY_FINGERPRINT)
    with pytest.raises(ValueError, match="method_family_mismatch"):
        R7_METHOD_REGISTRY.authenticate(ref, "discounting_association", FAMILY_VERSION, FAMILY_FINGERPRINT)


def test_evidence_input_requires_existing_admission_and_fitness_states():
    data = _evidence_set().bindings[0].model_dump(mode="python")
    for field, value in (("admission_state", "DESCRIPTIVE_ONLY"), ("fitness_state", "FAILED")):
        with pytest.raises(ValidationError):
            DiagnosticEvidenceInputBinding(**{**data, field:value})


def test_request_identity_excludes_created_at_and_rejects_unknown_parameters():
    evidence = _evidence_set(); method = authority_ref(METHOD_DEFINITION)
    common = dict(
        test_request_id="pending", handoff_ref="handoff:1", handoff_fingerprint=HASH,
        governed_hypothesis_ref="hyp:1", governed_hypothesis_fingerprint=HASH,
        diagnostic_proposition_ref="prop:1", diagnostic_proposition_fingerprint=HASH,
        pretest_evaluation_ref="pre:1", pretest_evaluation_fingerprint=HASH,
        resolved_profile_ref="profile:1", resolved_profile_fingerprint=HASH,
        requirement_judgment_bundle_ref="bundle:1", requirement_judgment_bundle_fingerprint=HASH,
        method=method, support_criterion=METHOD_DEFINITION.support_criterion_ref,
        validation_profile=METHOD_DEFINITION.validation_profile_ref, implementation=METHOD_DEFINITION.implementation_ref,
        evidence_input_set_ref=evidence.evidence_input_set_id, evidence_input_set_fingerprint=evidence.evidence_input_set_fingerprint,
        canonical_dataset_ref="canonical:1", canonical_dataset_fingerprint=HASH, scope_ref="scope:1",
        baseline_period_ref="period:b", comparison_period_ref="period:c", baseline_start=date(2026,1,5), baseline_end=date(2026,2,1),
        comparison_start=date(2026,2,2), comparison_end=date(2026,3,1), baseline_population_ref="population:b",
        baseline_population_fingerprint=HASH, comparison_population_ref="population:c", comparison_population_fingerprint=HASH,
        metric_refs=("metric:revenue_change@metric_dictionary_v1",), variable_refs=("field:product_id","field:line_revenue"),
        normalized_parameters=METHOD_DEFINITION.fixed_parameters, created_at=datetime(2026,1,1,tzinfo=UTC),
    )
    fp = diagnostic_test_request_fingerprint(common); common.update(request_fingerprint=fp, test_request_id=stable_content_id("r7req", fp))
    first = DiagnosticTestRequest(**common)
    second_data = {**common, "created_at":datetime(2027,1,1,tzinfo=UTC)}
    assert DiagnosticTestRequest(**second_data).request_fingerprint == first.request_fingerprint
    with pytest.raises(ValidationError):
        DiagnosticTestRequest(**common, arbitrary_override=True)


def test_contracts_are_frozen():
    with pytest.raises(ValidationError):
        _evidence_set().evidence_input_set_id = "changed"
