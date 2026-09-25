from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import duckdb

from commerce_lens.contracts.common import ArtifactReference, PeriodDefinition, ScopeDefinition
from commerce_lens.contracts.diagnostic import TestEligibility, pretest_evaluation_semantic_fingerprint
from commerce_lens.contracts.evidence import CanonicalDatasetReference
from commerce_lens.contracts.hypotheses import (
    GovernedHypothesis, R6ToR7Handoff, governed_hypothesis_semantic_fingerprint,
    r6_to_r7_handoff_semantic_fingerprint,
)
from commerce_lens.contracts.populations import PopulationDefinition, PopulationPeriodRole
from commerce_lens.contracts.r7 import (
    DiagnosticEvidenceInputBinding, DiagnosticEvidenceInputSet, DiagnosticTestRequest,
    diagnostic_test_request_fingerprint, evidence_input_set_fingerprint,
)
from commerce_lens.diagnostic.governance import AuthorityClass
from commerce_lens.diagnostic.r7_evidence_authentication import (
    TrustedR7EvidenceAuthority, TrustedR7EvidenceRole, requirement_judgment_fingerprint,
)
from commerce_lens.contracts.required_evidence import EvidenceRole
from commerce_lens.evidence.identifiers import sha256_file, stable_content_id
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.r6_repository import R6Repository
from commerce_lens.persistence.r7_repository import R7Repository
from tests.diagnostic.test_r6_governance import _all_assessments
from tests.engine.test_r7_execution import _request
from tests.persistence.test_r6_repository import _build_graph


@dataclass(frozen=True)
class R7Context:
    r6_graph: object
    r6_repository: R6Repository
    r7_repository: R7Repository
    request: DiagnosticTestRequest
    evidence_inputs: DiagnosticEvidenceInputSet
    trusted_evidence: TrustedR7EvidenceAuthority
    canonical: CanonicalDatasetReference
    baseline_population: PopulationDefinition
    comparison_population: PopulationDefinition


def build_eligible_r6_graph(tmp_path: Path):
    base = _build_graph(tmp_path / "base-r6", name="r7-conformance")
    evaluation_data = base.evaluation.model_dump(mode="python")
    evaluation_data.update(test_eligibility=TestEligibility.ELIGIBLE_NOT_EXECUTED, first_controlling_blocker=None, evaluation_fingerprint="0" * 64)
    evaluation_data["evaluation_fingerprint"] = pretest_evaluation_semantic_fingerprint(evaluation_data)
    evaluation = type(base.evaluation)(**evaluation_data)
    hypothesis_data = base.hypothesis.model_dump(mode="python")
    hypothesis_data.update(pretest_evaluation_fingerprint=evaluation.evaluation_fingerprint, governed_hypothesis_fingerprint="0" * 64)
    hypothesis_data["governed_hypothesis_fingerprint"] = governed_hypothesis_semantic_fingerprint(hypothesis_data)
    hypothesis = GovernedHypothesis(**hypothesis_data)
    handoff_data = base.handoff.model_dump(mode="python")
    handoff_data.update(
        pretest_evaluation_fingerprint=evaluation.evaluation_fingerprint,
        governed_hypothesis_fingerprint=hypothesis.governed_hypothesis_fingerprint,
        test_eligibility=TestEligibility.ELIGIBLE_NOT_EXECUTED,
        first_controlling_blocker=None,
        handoff_fingerprint="0" * 64,
    )
    handoff_data["handoff_fingerprint"] = r6_to_r7_handoff_semantic_fingerprint(handoff_data)
    handoff = R6ToR7Handoff(**handoff_data)
    repository = R6Repository(ArtifactStore(tmp_path / "r6-artifacts"), MetadataStore(tmp_path / "r6.sqlite"))
    repository.persist_diagnostic_proposition(base.proposition)
    repository.persist_resolved_required_evidence_profile(base.profile)
    repository.persist_requirement_judgment_bundle(
        evaluation.requirement_judgment_bundle_ref,
        evaluation.requirement_judgment_bundle_fingerprint,
        base.judgments,
    )
    repository.persist_pretest_diagnostic_evaluation(evaluation)
    repository.persist_generation_provenance(base.provenance)
    repository.persist_governed_hypothesis(hypothesis)
    repository.persist_r6_to_r7_handoff(handoff)
    return base.__class__(repository, base.registry, base.proposition, base.profile, base.judgments, evaluation, base.provenance, hypothesis, handoff)


def build_r7_context(tmp_path: Path) -> R7Context:
    graph = build_eligible_r6_graph(tmp_path)
    assessments = _all_assessments(graph.proposition)
    assessment_by_requirement = {item.requirement_ref: item for item in assessments}
    judgment = next(item for item in graph.judgments if item.requirement_ref == "governed_product_id")
    assessment = assessment_by_requirement[judgment.requirement_ref]
    evidence_ref = assessment.evidence_refs[0]
    evidence_authority = graph.registry.require_reference(AuthorityClass.EVIDENCE, evidence_ref)
    binding = DiagnosticEvidenceInputBinding(
        requirement_judgment_ref=judgment.judgment_id,
        requirement_judgment_fingerprint=requirement_judgment_fingerprint(judgment),
        evidence_ref=evidence_ref,
        evidence_fingerprint=evidence_authority.binding.authority_fingerprint,
        evidence_assessment_ref=assessment.assessment_id,
        evidence_assessment_fingerprint=assessment.assessment_fingerprint,
        diagnostic_admission_authority=assessment.diagnostic_admission_authority,
        admission_state="DIAGNOSTIC_ADMITTED", fitness_state="PASSED",
        source_class="GOVERNED_INTERNAL", evidence_role=EvidenceRole.EXPLANATORY_VARIABLE,
        scope_ref=assessment.scope_ref,
        period_refs=(assessment.baseline_period_ref, assessment.comparison_period_ref),
        population_refs=(assessment.baseline_population_ref, assessment.comparison_population_ref),
        metric_refs=assessment.metric_refs, variable_refs=assessment.variable_refs,
    )
    evidence_data = {
        "evidence_input_set_id":"pending", "evidence_input_set_fingerprint":"0"*64,
        "diagnostic_proposition_ref":graph.proposition.proposition_id,
        "diagnostic_proposition_fingerprint":graph.proposition.semantic_fingerprint,
        "bindings":(binding,),
    }
    evidence_fp = evidence_input_set_fingerprint(evidence_data)
    evidence_data.update(evidence_input_set_fingerprint=evidence_fp, evidence_input_set_id=stable_content_id("r7evid", evidence_fp))
    evidence_inputs = DiagnosticEvidenceInputSet(**evidence_data)

    store = ArtifactStore(tmp_path / "r7-artifacts"); store.ensure_layout()
    parquet = store.safe_path("canonical", "r7-hardening.parquet")
    connection = duckdb.connect(":memory:")
    connection.execute("CREATE TABLE sales(order_date DATE, product_id VARCHAR, line_revenue DECIMAL(18,2), eligibility_status VARCHAR)")
    products = tuple(f"P{i}" for i in range(10)); rows=[]
    for week in range(8):
        active=products[:10-week]; monday=date(2026,1,5)+timedelta(days=week*7); total=Decimal(800-week*100)
        rows.extend((monday, product, total if index==0 else Decimal(0), "Eligible") for index,product in enumerate(active))
    connection.executemany("INSERT INTO sales VALUES (?, ?, ?, ?)", rows)
    connection.execute("COPY sales TO ? (FORMAT PARQUET)", [str(parquet)])
    canonical_fp=sha256_file(parquet)
    artifact=ArtifactReference(artifact_id=stable_content_id("art",canonical_fp),path="canonical/r7-hardening.parquet",fingerprint=canonical_fp,media_type="application/vnd.apache.parquet",size_bytes=parquet.stat().st_size)
    canonical=CanonicalDatasetReference(canonical_dataset_id="canonical:1",source_dataset_id="dataset:1",canonical_schema_version="1",content_fingerprint=canonical_fp,artifact=artifact,row_count=len(rows))
    bp=PeriodDefinition(period_id=graph.proposition.baseline_period_ref,label="Baseline",start_date=date(2026,1,5),end_date=date(2026,2,1),date_convention_ref="canonical:order_date")
    cp=PeriodDefinition(period_id=graph.proposition.comparison_period_ref,label="Comparison",start_date=date(2026,2,2),end_date=date(2026,3,1),date_convention_ref="canonical:order_date")
    scope=ScopeDefinition(scope_id=graph.proposition.scope_ref)
    def population(role, period, identifier):
        return PopulationDefinition(population_id=identifier,canonical_dataset_ref_id="canonical:1",dataset_ref_id="dataset:1",period=period,period_role=role,currency_basis_ref="currency:USD",scope=scope,population_fingerprint="a"*64)
    baseline=population(PopulationPeriodRole.BASELINE,bp,graph.proposition.baseline_population_ref)
    comparison=population(PopulationPeriodRole.COMPARISON,cp,graph.proposition.comparison_population_ref)
    request_data=_request().model_dump(mode="python")
    request_data.update(
        handoff_ref=graph.handoff.handoff_id, handoff_fingerprint=graph.handoff.handoff_fingerprint,
        governed_hypothesis_ref=graph.hypothesis.governed_hypothesis_id, governed_hypothesis_fingerprint=graph.hypothesis.governed_hypothesis_fingerprint,
        diagnostic_proposition_ref=graph.proposition.proposition_id, diagnostic_proposition_fingerprint=graph.proposition.semantic_fingerprint,
        pretest_evaluation_ref=graph.evaluation.evaluation_id, pretest_evaluation_fingerprint=graph.evaluation.evaluation_fingerprint,
        resolved_profile_ref=graph.profile.profile_id, resolved_profile_fingerprint=graph.profile.profile_fingerprint,
        requirement_judgment_bundle_ref=graph.evaluation.requirement_judgment_bundle_ref,
        requirement_judgment_bundle_fingerprint=graph.evaluation.requirement_judgment_bundle_fingerprint,
        evidence_input_set_ref=evidence_inputs.evidence_input_set_id, evidence_input_set_fingerprint=evidence_inputs.evidence_input_set_fingerprint,
        canonical_dataset_fingerprint=canonical_fp, scope_ref=graph.proposition.scope_ref,
        baseline_period_ref=graph.proposition.baseline_period_ref, comparison_period_ref=graph.proposition.comparison_period_ref,
        baseline_population_ref=baseline.population_id, comparison_population_ref=comparison.population_id,
        metric_refs=graph.proposition.metric_refs, variable_refs=graph.proposition.variable_refs,
        request_fingerprint="0"*64, test_request_id="pending",
    )
    request_fp=diagnostic_test_request_fingerprint(request_data)
    request_data.update(request_fingerprint=request_fp,test_request_id=stable_content_id("r7req",request_fp))
    request=DiagnosticTestRequest(**request_data)
    trusted=TrustedR7EvidenceAuthority(
        "TEST / CONFORMANCE AUTHORITY ONLY — NOT PRODUCTION R6 OUTPUT", assessments,
        (TrustedR7EvidenceRole(
            judgment.requirement_ref, EvidenceRole.EXPLANATORY_VARIABLE,
            assessment.authority_bindings[0],
        ),),
    )
    return R7Context(graph,graph.repo,R7Repository(store,MetadataStore(tmp_path/"r7.sqlite")),request,evidence_inputs,trusted,canonical,baseline,comparison)
