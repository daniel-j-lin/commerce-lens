from __future__ import annotations

import inspect
import json
import sqlite3

import pytest

from commerce_lens.application import r7_service
from commerce_lens.contracts.diagnostic import AuthorityBinding
from commerce_lens.contracts.r7 import (
    DiagnosticEvidenceInputSet, DiagnosticTestRequest, R7AuthorityReference,
    R7ValidationStatus, diagnostic_test_request_fingerprint,
    evidence_input_set_fingerprint, executed_result_fingerprint,
)
from commerce_lens.diagnostic.governance import (
    DiagnosticAdmissionState, EvidenceFitnessState,
    requirement_evidence_assessment_fingerprint,
)
from commerce_lens.diagnostic.r7_evidence_authentication import (
    R7EvidenceAuthenticationError, TrustedR7EvidenceAuthority,
)
from commerce_lens.diagnostic.r7_method_registry import METHOD_DEFINITION
from commerce_lens.engine.r7_execution import execute_r7_diagnostic
from commerce_lens.evidence.identifiers import canonical_json_bytes, sha256_bytes, stable_content_id
from commerce_lens.persistence.r7_repository import R7ArtifactIntegrityError, R7ArtifactType
from commerce_lens.validation import r7_validator
from commerce_lens.validation.r7_validator import validate_r7_result
from tests.r7.support import build_r7_context


def _request_with(request, **updates):
    data=request.model_dump(mode="python"); data.update(updates,request_fingerprint="0"*64,test_request_id="pending")
    fp=diagnostic_test_request_fingerprint(data); data.update(request_fingerprint=fp,test_request_id=stable_content_id("r7req",fp))
    return DiagnosticTestRequest(**data)


def _evidence_with(context, binding, *, trusted=None):
    data=context.evidence_inputs.model_dump(mode="python"); data.update(bindings=(binding,),evidence_input_set_fingerprint="0"*64,evidence_input_set_id="pending")
    fp=evidence_input_set_fingerprint(data); data.update(evidence_input_set_fingerprint=fp,evidence_input_set_id=stable_content_id("r7evid",fp))
    evidence=DiagnosticEvidenceInputSet(**data)
    request=_request_with(context.request,evidence_input_set_ref=evidence.evidence_input_set_id,evidence_input_set_fingerprint=evidence.evidence_input_set_fingerprint)
    return evidence,request,trusted or context.trusted_evidence


def _run(context, monkeypatch, request=None, evidence=None, trusted=None):
    calls=[]
    monkeypatch.setattr(r7_service,"execute_r7_diagnostic",lambda **kwargs: calls.append(kwargs))
    with pytest.raises((ValueError,R7EvidenceAuthenticationError)) as caught:
        r7_service.run_r7_diagnostic(
            request=request or context.request,evidence_inputs=evidence or context.evidence_inputs,
            canonical_dataset=context.canonical,baseline_population=context.baseline_population,
            comparison_population=context.comparison_population,r6_repository=context.r6_repository,
            r7_repository=context.r7_repository,authority_registry=context.r6_graph.registry,
            trusted_evidence_authority=trusted or context.trusted_evidence,
        )
    assert calls == []
    return str(caught.value)


def test_r7_independent_validation_rejects_self_consistent_wrong_execution_result(tmp_path):
    context=build_r7_context(tmp_path)
    execution=execute_r7_diagnostic(request=context.request,canonical_dataset=context.canonical,baseline_population=context.baseline_population,comparison_population=context.comparison_population,artifact_store=context.r7_repository.artifact_store)
    observations=list(execution.executed_result.observations)
    observations[0]=observations[0].model_copy(update={"jaccard_distance":0.125})
    data=execution.executed_result.model_dump(mode="python"); data.update(observations=tuple(observations),result_fingerprint="0"*64)
    data["result_fingerprint"]=executed_result_fingerprint(data)
    wrong=type(execution.executed_result)(**data)
    outcome=validate_r7_result(request=context.request,executed_result=wrong,canonical_dataset=context.canonical,baseline_population=context.baseline_population,comparison_population=context.comparison_population,artifact_store=context.r7_repository.artifact_store)
    assert outcome.validation_record.status is R7ValidationStatus.FAILED
    assert outcome.validated_result is None
    assert wrong.result_fingerprint == executed_result_fingerprint(wrong)
    source=inspect.getsource(r7_validator)
    assert "calculate_r7_result" not in source and "commerce_lens.engine.r7_execution" not in source


@pytest.mark.parametrize("field,kind",(
    ("support_criterion","fake"),("support_criterion","stale"),
    ("validation_profile","fake"),("validation_profile","stale"),
    ("implementation","fake"),("implementation","stale"),
))
def test_r7_method_bundle_authentication_fails_before_execution(tmp_path,monkeypatch,field,kind):
    context=build_r7_context(tmp_path)
    current=getattr(context.request,field)
    changed=current.model_copy(update={"authority_id":f"fake:{field}"}) if kind=="fake" else current.model_copy(update={"authority_fingerprint":"f"*64})
    request=_request_with(context.request,**{field:changed})
    error=_run(context,monkeypatch,request=request)
    assert {
        "support_criterion":"support_criterion_unregistered_or_stale",
        "validation_profile":"validation_profile_unregistered_or_stale",
        "implementation":"implementation_binding_unregistered_or_stale",
    }[field] in error


def test_r7_evidence_admission_and_fitness_cannot_self_bootstrap(tmp_path,monkeypatch):
    context=build_r7_context(tmp_path); binding=context.evidence_inputs.bindings[0]
    original=next(item for item in context.trusted_evidence.assessments if item.assessment_id==binding.evidence_assessment_ref)
    for updates,code in (
        ({"admission_state":DiagnosticAdmissionState.UNRESOLVED,"diagnostic_admission_authority":None},"R7_EVIDENCE_NOT_DIAGNOSTICALLY_ADMITTED"),
        ({"fitness_state":EvidenceFitnessState.FAILED,"failure_reason":"trusted failure"},"R7_EVIDENCE_FITNESS_NOT_PASSED"),
    ):
        data=original.model_dump(mode="python"); data.update(updates,assessment_fingerprint="0"*64,assessment_id="pending")
        fp=requirement_evidence_assessment_fingerprint(data); data.update(assessment_fingerprint=fp,assessment_id=stable_content_id("reqevid",fp))
        assessment=type(original)(**data)
        changed=binding.model_copy(update={"evidence_assessment_ref":assessment.assessment_id,"evidence_assessment_fingerprint":assessment.assessment_fingerprint})
        evidence,request,_=_evidence_with(context,changed)
        trusted=TrustedR7EvidenceAuthority(context.trusted_evidence.authority_label,(assessment,),context.trusted_evidence.roles)
        assert code in _run(context,monkeypatch,request=request,evidence=evidence,trusted=trusted)


@pytest.mark.parametrize("updates,code",(
    ({"requirement_judgment_fingerprint":"f"*64},"R7_EVIDENCE_JUDGMENT_MISMATCH"),
    ({"evidence_assessment_fingerprint":"f"*64},"R7_EVIDENCE_ASSESSMENT_MISMATCH"),
    ({"diagnostic_admission_authority":AuthorityBinding(authority_ref="fake",authority_version="1",authority_fingerprint="f"*64)},"R7_EVIDENCE_ADMISSION_AUTHORITY_MISMATCH"),
    ({"evidence_fingerprint":"f"*64},"R7_EVIDENCE_ARTIFACT_FINGERPRINT_MISMATCH"),
    ({"scope_ref":"scope:wrong"},"R7_EVIDENCE_SCOPE_MISMATCH"),
    ({"period_refs":("period:wrong","period:other")},"R7_EVIDENCE_PERIOD_MISMATCH"),
    ({"population_refs":("population:wrong","population:other")},"R7_EVIDENCE_POPULATION_MISMATCH"),
    ({"metric_refs":("metric:wrong",)},"R7_EVIDENCE_METRIC_MISMATCH"),
    ({"variable_refs":("field:wrong",)},"R7_EVIDENCE_VARIABLE_MISMATCH"),
))
def test_r7_evidence_admission_authentication_hostile_bindings(tmp_path,monkeypatch,updates,code):
    context=build_r7_context(tmp_path); changed=context.evidence_inputs.bindings[0].model_copy(update=updates)
    evidence,request,trusted=_evidence_with(context,changed)
    assert code in _run(context,monkeypatch,request=request,evidence=evidence,trusted=trusted)


def test_r7_complete_lineage_reload_rejects_locally_valid_deep_tamper(tmp_path):
    context=build_r7_context(tmp_path)
    outcome=r7_service.run_r7_diagnostic(
        request=context.request,evidence_inputs=context.evidence_inputs,canonical_dataset=context.canonical,
        baseline_population=context.baseline_population,comparison_population=context.comparison_population,
        r6_repository=context.r6_repository,r7_repository=context.r7_repository,
        authority_registry=context.r6_graph.registry,trusted_evidence_authority=context.trusted_evidence,
    )
    complete=context.r7_repository.load_complete_posttest_evaluation(
        outcome.evaluation.evaluation_event_id,r6_repository=context.r6_repository,
        authority_registry=context.r6_graph.registry,trusted_evidence_authority=context.trusted_evidence,
    )
    result=complete.executed_result
    index=context.r7_repository.metadata_store.get_r7_artifact_index(R7ArtifactType.EXECUTED_RESULT.value,result.executed_result_id)
    reference=context.r7_repository.metadata_store.get_artifact_reference(index.artifact_reference_id)
    path=context.r7_repository.artifact_store.safe_path(reference.path)
    payload=json.loads(path.read_text()); payload["test_request_ref"]="r7req:locally-valid-but-wrong"
    payload["result_fingerprint"]=executed_result_fingerprint(payload)
    raw=canonical_json_bytes(payload); path.write_bytes(raw); digest=sha256_bytes(raw)
    updated_ref=reference.model_copy(update={"fingerprint":digest,"size_bytes":len(raw)})
    updated_index=index.model_copy(update={"semantic_fingerprint":payload["result_fingerprint"]})
    with sqlite3.connect(context.r7_repository.metadata_store.db_path) as connection:
        connection.execute("UPDATE artifact_references SET fingerprint=?,size_bytes=?,record_json=? WHERE artifact_id=?",(digest,len(raw),updated_ref.model_dump_json(),reference.artifact_id))
        connection.execute("UPDATE r7_artifact_index SET semantic_fingerprint=?,record_json=? WHERE artifact_type=? AND artifact_id=?",(payload["result_fingerprint"],updated_index.model_dump_json(),R7ArtifactType.EXECUTED_RESULT.value,result.executed_result_id))
    assert context.r7_repository.load(R7ArtifactType.EXECUTED_RESULT,result.executed_result_id).test_request_ref.endswith("wrong")
    with pytest.raises(R7ArtifactIntegrityError,match="lineage_mismatch"):
        context.r7_repository.load_complete_posttest_evaluation(
            outcome.evaluation.evaluation_event_id,r6_repository=context.r6_repository,
            authority_registry=context.r6_graph.registry,trusted_evidence_authority=context.trusted_evidence,
        )
