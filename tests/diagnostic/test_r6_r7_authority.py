from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import commerce_lens.diagnostic.r6_r7_authority as bridge
from commerce_lens.contracts.diagnostic import AuthorityBinding, TestEligibility as EligibilityState
from commerce_lens.diagnostic.governance import (
    DiagnosticAdmissionState,
    EvidenceFitnessState,
    GovernanceAuthenticationError,
    PreTestExecutionAuthority,
)
from commerce_lens.diagnostic.generator import R6GenerationRequest, build_generation_request
from commerce_lens.diagnostic.r7_method_registry import (
    IMPLEMENTATION_BINDING,
    METHOD_DEFINITION,
    R7_METHOD_REGISTRY,
    SUPPORT_CRITERION,
    VALIDATION_PROFILE,
    authority_ref,
)
from tests.diagnostic.test_r6_governance import (
    _all_assessments,
    _assessment,
    _authority_registry,
    _proposition,
    _run,
)


def _binding(value) -> AuthorityBinding:
    reference = authority_ref(value)
    return AuthorityBinding(
        authority_ref=reference.authority_id,
        authority_version=reference.authority_version,
        authority_fingerprint=reference.authority_fingerprint,
    )


def _execution_authority() -> PreTestExecutionAuthority:
    proposition = _proposition()
    return PreTestExecutionAuthority(
        family_id=proposition.family_id,
        family_version=proposition.family_version,
        family_fingerprint=proposition.family_fingerprint,
        method=_binding(METHOD_DEFINITION),
        support_criterion=_binding(SUPPORT_CRITERION),
        validation_profile=_binding(VALIDATION_PROFILE),
        implementation=_binding(IMPLEMENTATION_BINDING),
    )


def test_complete_current_bundle_is_required_for_eligible_pretest_identity() -> None:
    proposition = _proposition()
    assessments = _all_assessments(proposition)
    execution = _execution_authority()
    registry = _authority_registry(
        proposition,
        assessments,
        methods=execution.bindings,
    )

    first = _run(
        proposition=proposition,
        assessments=assessments,
        authority_registry=registry,
        execution_authority=execution,
    )
    second = _run(
        proposition=proposition,
        assessments=assessments,
        authority_registry=registry,
        execution_authority=execution,
    )

    assert first.evaluation.test_eligibility is EligibilityState.ELIGIBLE_NOT_EXECUTED
    assert first.evaluation.first_controlling_blocker is None
    assert first.evaluation.evaluation_id == second.evaluation.evaluation_id
    assert first.evaluation.evaluation_fingerprint == second.evaluation.evaluation_fingerprint
    assert set(execution.bindings).issubset(first.evaluation.authority_bindings)


def test_execution_authority_never_repairs_missing_failed_or_inadmissible_evidence() -> None:
    proposition = _proposition()
    current = list(_all_assessments(proposition))
    execution = _execution_authority()

    variants = []
    variants.append(tuple(current[1:]))
    target = current[0]
    variants.append(
        (
            _assessment(
                proposition,
                target.requirement_ref,
                target.dependency_classification,
                fitness_state=EvidenceFitnessState.FAILED,
                failure_reason="governed fitness failure",
            ),
            *current[1:],
        )
    )
    variants.append(
        (
            _assessment(
                proposition,
                target.requirement_ref,
                target.dependency_classification,
                admission_state=DiagnosticAdmissionState.INADMISSIBLE,
            ),
            *current[1:],
        )
    )

    for assessments in variants:
        result = _run(
            proposition=proposition,
            assessments=assessments,
            authority_registry=_authority_registry(
                proposition,
                assessments,
                methods=execution.bindings,
            ),
            execution_authority=execution,
        )
        assert result.evaluation.test_eligibility is EligibilityState.NOT_ELIGIBLE
        assert result.evaluation.first_controlling_blocker is not None


def test_wrong_family_and_stale_execution_bindings_fail_closed() -> None:
    proposition = _proposition()
    assessments = _all_assessments(proposition)
    execution = _execution_authority()
    registry = _authority_registry(
        proposition,
        assessments,
        methods=execution.bindings,
    )
    wrong_family = execution.model_copy(update={"family_id": "discounting_association"})
    with pytest.raises(GovernanceAuthenticationError, match="method_family_mismatch"):
        _run(
            proposition=proposition,
            assessments=assessments,
            authority_registry=registry,
            execution_authority=wrong_family,
        )

    stale = execution.model_copy(
        update={
            "method": execution.method.model_copy(
                update={"authority_fingerprint": "0" * 64}
            )
        }
    )
    with pytest.raises(GovernanceAuthenticationError, match="stale_or_untrusted_authority"):
        _run(
            proposition=proposition,
            assessments=assessments,
            authority_registry=registry,
            execution_authority=stale,
        )


@pytest.mark.parametrize(
    ("name", "code"),
    (
        ("METHOD_DEFINITION", "method_unregistered_or_stale"),
        ("SUPPORT_CRITERION", "support_criterion_unregistered_or_stale"),
        ("VALIDATION_PROFILE", "validation_profile_unregistered_or_stale"),
        ("IMPLEMENTATION_BINDING", "implementation_binding_unregistered_or_stale"),
    ),
)
def test_production_bridge_rejects_each_stale_r7_authority(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    code: str,
) -> None:
    current = getattr(bridge, name)
    fingerprint_field = {
        "METHOD_DEFINITION": "method_fingerprint",
        "SUPPORT_CRITERION": "criterion_fingerprint",
        "VALIDATION_PROFILE": "profile_fingerprint",
        "IMPLEMENTATION_BINDING": "implementation_fingerprint",
    }[name]
    monkeypatch.setattr(
        bridge,
        name,
        current.model_copy(update={fingerprint_field: "0" * 64}),
    )
    with pytest.raises(GovernanceAuthenticationError) as error:
        bridge.resolve_production_pretest_authority(
            _proposition(),
            (),
            method_registry=R7_METHOD_REGISTRY,
        )
    assert error.value.code == code


def test_production_bridge_rejects_noncurrent_registry_object() -> None:
    with pytest.raises(
        GovernanceAuthenticationError,
        match="stale_or_untrusted_r7_method_registry",
    ):
        bridge.resolve_production_pretest_authority(
            _proposition(),
            (),
            method_registry=type(R7_METHOD_REGISTRY)(),
        )


def test_generation_request_cannot_self_declare_method_authority() -> None:
    request = build_generation_request(analysis_request_ref="request:1")
    payload = request.model_dump(mode="python")
    payload["method_ref"] = "method:fake"
    with pytest.raises(ValidationError):
        R6GenerationRequest.model_validate(payload)


def test_production_bridge_has_no_test_or_fixture_dependency() -> None:
    project_root = Path(__file__).parents[2]
    sources = (
        project_root / "src/commerce_lens/diagnostic/r6_r7_authority.py",
        project_root / "src/commerce_lens/application/r6_service.py",
    )
    for source in sources:
        text = source.read_text(encoding="utf-8")
        assert "from tests" not in text
        assert "import tests" not in text
        assert "fixtures/r7" not in text
        assert "TEST / CONFORMANCE AUTHORITY ONLY" not in text
