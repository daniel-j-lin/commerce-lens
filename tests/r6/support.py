from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

from pydantic import ConfigDict, Field, model_validator

import commerce_lens.contracts.r4 as r4_contract_module
import commerce_lens.engine.r4_execution as r4_execution_module
from commerce_lens.application.r4_service import run_r4_decomposition
from commerce_lens.application.r6_service import R6RunOutcome, run_r6
from commerce_lens.contracts.common import ClaimType, ContractBase, GroupingDimension
from commerce_lens.contracts.evidence import EvidenceRole
from commerce_lens.contracts.hypotheses import (
    CandidateProposal,
    CandidateProposalBatch,
    CandidateSlot,
    GenerationParameters,
)
from commerce_lens.contracts.r4 import R4DecompositionRequest
from commerce_lens.diagnostic.generator import (
    CandidateProducerDescriptor,
    FamilyActivation,
    build_generation_request,
)
from commerce_lens.evidence.admissibility import evaluate_evidence_admissibility
from commerce_lens.engine import execute_plan
from commerce_lens.engine.plan_builder import build_execution_plan
from commerce_lens.persistence.r6_repository import R6Repository
from tests.engine.test_execution import _row
from tests.engine.test_execution import _sufficiency
from tests.evidence.test_admissibility import _fixture, _validate


ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "fixtures/r6/cases.json"
NOW = datetime(2026, 9, 26, 0, 0, tzinfo=UTC)
HASH = "a" * 64

EXPECTED_FIXTURE_IDS = {
    "FX-R6-DESC-001A",
    "FX-R6-PROD-001A",
    "FX-R6-DISC-001A",
    "FX-R6-DISC-002A",
    "FX-R6-DISC-002B",
    "FX-R6-DISC-002C",
    "FX-R6-DISC-002D",
    "FX-R6-EXT-001A",
    "FX-R6-EXT-001B",
    "FX-R6-PEER-001A",
    "FX-R6-CLOSED-001A",
    "FX-R6-CLOSED-001B",
    "FX-R6-CLOSED-001C",
    "FX-R6-CLOSED-001D",
    "FX-R6-CLOSED-001E",
    "FX-R6-CLOSED-001F",
    "FX-R6-CLOSED-001G",
    "FX-R6-CLOSED-001H",
    "FX-R6-CLOSED-001I",
    "FX-R6-R4-001A",
    "FX-R6-TAMPER-001A",
    "FX-R6-TAMPER-001B",
    "FX-R6-IDENT-001A",
    "FX-R6-IDENT-002A",
    "FX-R6-IDENT-002B",
    "FX-R6-IDENT-002C",
    "FX-R6-IDENT-002D",
    "FX-R6-IDENT-002E",
    "FX-R6-IDENT-002F",
    "FX-R6-IDENT-003A",
    "FX-R6-NONDET-001A",
    "FX-R6-NONDET-001B",
    "FX-R6-NONDET-001C",
    "FX-R6-NONDET-001D",
}


class StrictModel(ContractBase):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ExpectedOutcome(StrictModel):
    completion_status: str | None = None
    accepted_families: tuple[str, ...] = ()
    rejected_proposals: tuple[str, ...] = ()
    diagnostic_code: str | None = None
    proposition_material: dict[str, Any] | None = None
    proposition_id: str | None = None
    proposition_fingerprint: str | None = None
    profile_dimension_expectations: dict[str, str] | None = None
    requirement_judgments: dict[str, str] | None = None
    first_controlling_blocker: str | None = None
    test_eligibility: str | None = None
    pretest_disposition: str | None = None
    analytical_outcome: str | None = None
    alternative_explanation_state: str | None = None
    persisted_artifact_types: tuple[str, ...] = ()
    handoff_expected: bool | None = None
    public_output_unchanged: bool | None = None


class R6FixtureCase(StrictModel):
    fixture_id: str = Field(pattern=r"^FX-R6-(DESC|PROD|DISC|EXT|PEER|CLOSED|R4|TAMPER|IDENT|NONDET)-\d{3}[A-Z]$")
    case_letter: Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    scenario: str = Field(min_length=1)
    execution_surface: str = Field(min_length=1)
    analysis_recipe: str | None = None
    requested_family_ids: tuple[str, ...] = ()
    family_activations: tuple[str, ...] = ()
    producer_recipe: str = Field(min_length=1)
    authority_recipe: str | None = None
    expected: ExpectedOutcome
    success_criteria: tuple[int, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def one_authoritative_outcome(self) -> "R6FixtureCase":
        if len(set(self.success_criteria)) != len(self.success_criteria):
            raise ValueError("success criteria must be unique")
        if any(item < 1 or item > 20 for item in self.success_criteria):
            raise ValueError("success criteria must be between 1 and 20")
        if self.expected.diagnostic_code and "," in self.expected.diagnostic_code:
            raise ValueError("one fixture variant may declare only one diagnostic code")
        return self


class R6FixtureSuite(StrictModel):
    schema_version: Literal["1.0.0"]
    fixtures: tuple[R6FixtureCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def exact_inventory(self) -> "R6FixtureSuite":
        ids = [item.fixture_id for item in self.fixtures]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate R6 fixture IDs")
        if set(ids) != EXPECTED_FIXTURE_IDS:
            missing = sorted(EXPECTED_FIXTURE_IDS - set(ids))
            extra = sorted(set(ids) - EXPECTED_FIXTURE_IDS)
            raise ValueError(f"R6 fixture inventory mismatch; missing={missing}, extra={extra}")
        return self


def load_cases(path: Path = CASES_PATH) -> tuple[R6FixtureCase, ...]:
    suite = R6FixtureSuite.model_validate_json(path.read_text(encoding="utf-8"))
    return tuple(sorted(suite.fixtures, key=lambda item: item.fixture_id))


def case(fixture_id: str) -> R6FixtureCase:
    return next(item for item in load_cases() if item.fixture_id == fixture_id)


def _rows(recipe: str) -> list[dict[str, str]]:
    if recipe == "descriptive_flat_aov":
        return [
            _row(order_id=f"b{index}", order_line_id=f"bl{index}", order_date="2026-01-01", product_id=f"p{index}", line_revenue="100.00")
            for index in range(1, 5)
        ] + [
            _row(order_id=f"c{index}", order_line_id=f"cl{index}", order_date="2026-01-03", product_id=f"p{index}", line_revenue="100.00")
            for index in range(1, 3)
        ]
    if recipe == "large_r4_entry":
        return [
            _row(order_id="b1", order_line_id="bl1", order_date="2026-01-01", product_id="p1", line_revenue="100.00"),
            _row(order_id="c1", order_line_id="cl1", order_date="2026-01-03", product_id="p1", line_revenue="100.00"),
            _row(order_id="c2", order_line_id="cl2", order_date="2026-01-03", product_id="p2", line_revenue="1000.00"),
        ]
    return [
        _row(order_id="b1", order_line_id="bl1", order_date="2026-01-01", product_id="p1", line_revenue="100.00", unit_price="90.00"),
        _row(order_id="b2", order_line_id="bl2", order_date="2026-01-02", product_id="p2", line_revenue="100.00", unit_price="95.00"),
        _row(order_id="c1", order_line_id="cl1", order_date="2026-01-03", product_id="p1", line_revenue="70.00", unit_price="80.00"),
        _row(order_id="c2", order_line_id="cl2", order_date="2026-01-04", product_id="p2", line_revenue="50.00", unit_price="75.00"),
    ]


@dataclass(frozen=True)
class SyntheticAnalysis:
    scalar: Any
    baseline_revenue: Any
    comparison_revenue: Any
    revenue_change: Any
    baseline_orders: Any
    comparison_orders: Any
    baseline_aov: Any
    comparison_aov: Any
    r4_outcome: Any


def build_synthetic_analysis(tmp_path: Path, recipe: str = "product_decline") -> SyntheticAnalysis:
    seed = _fixture(
        tmp_path,
        ("revenue_change", "revenue", "orders", "aov"),
        _rows(recipe),
    )
    request = type(seed.request)(
        **{
            **seed.request.model_dump(mode="python", exclude={"request_id", "created_at"}),
            "request_id": "req_r6_5_" + recipe,
            "created_at": NOW,
            "original_question_text": "Why did Revenue decrease from the baseline period to the comparison period?",
        }
    )
    sufficiency = _sufficiency(request, seed.canonical.canonical_dataset_id).model_copy(
        update={
            "required_evidence": request.required_evidence,
            "available_evidence": seed.sufficiency.available_evidence,
        }
    )
    plan = build_execution_plan(request, sufficiency)
    seed.metadata_store.insert_analysis_request(request, seed.artifact_store)
    seed.metadata_store.insert_data_sufficiency_result(sufficiency, seed.artifact_store)
    seed.metadata_store.insert_artifact_reference(seed.canonical.artifact)
    seed.metadata_store.insert_canonical_dataset(seed.canonical)
    outcome = execute_plan(plan, seed.canonical, seed.artifact_store, seed.metadata_store)
    scalar = SimpleNamespace(
        request=request,
        sufficiency=sufficiency,
        plan=plan,
        canonical=seed.canonical,
        artifact_store=seed.artifact_store,
        metadata_store=seed.metadata_store,
        outcome=outcome,
    )

    baseline_revenue = _validate(scalar, "revenue", period_ref="baseline").validated_result
    comparison_revenue = _validate(scalar, "revenue", period_ref="comparison").validated_result
    baseline_orders = _validate(scalar, "orders", period_ref="baseline").validated_result
    comparison_orders = _validate(scalar, "orders", period_ref="comparison").validated_result
    baseline_aov = _validate(
        scalar,
        "aov",
        period_ref="baseline",
        dependencies=(baseline_revenue, baseline_orders),
    ).validated_result
    comparison_aov = _validate(
        scalar,
        "aov",
        period_ref="comparison",
        dependencies=(comparison_revenue, comparison_orders),
    ).validated_result
    revenue_change = _validate(
        scalar,
        "revenue_change",
        period_ref="comparison",
        dependencies=(baseline_revenue, comparison_revenue),
    ).validated_result

    admitted = []
    for result in (baseline_revenue, comparison_revenue, revenue_change):
        outcome = evaluate_evidence_admissibility(
            request_id=scalar.request.request_id,
            sufficiency_id=scalar.sufficiency.sufficiency_id,
            validated_result_id=result.validated_result_id,
            claim_type=ClaimType.DESCRIPTIVE,
            evidence_role=EvidenceRole.METRIC_VALUE,
            artifact_store=scalar.artifact_store,
            metadata_store=scalar.metadata_store,
        )
        assert outcome.admissible_evidence is not None
        admitted.append(outcome.admissible_evidence)

    baseline_population = next(
        item for item in scalar.plan.population_definitions
        if item.period_role.value == "baseline" and item.grouping is GroupingDimension.NONE
    )
    comparison_population = next(
        item for item in scalar.plan.population_definitions
        if item.period_role.value == "comparison" and item.grouping is GroupingDimension.NONE
    )
    r4_request = R4DecompositionRequest(
        r4_request_id=f"r4req-r6-5-{recipe}",
        analysis_request_ref=scalar.request.request_id,
        sufficiency_ref=scalar.sufficiency.sufficiency_id,
        plan_ref=scalar.plan.plan_id,
        plan_fingerprint=scalar.plan.plan_fingerprint,
        canonical_dataset_ref=scalar.canonical.canonical_dataset_id,
        canonical_dataset_fingerprint=scalar.canonical.content_fingerprint,
        baseline_population_ref=baseline_population.population_id,
        baseline_population_fingerprint=baseline_population.population_fingerprint,
        comparison_population_ref=comparison_population.population_id,
        comparison_population_fingerprint=comparison_population.population_fingerprint,
        baseline_revenue_validated_result_ref=baseline_revenue.validated_result_id,
        comparison_revenue_validated_result_ref=comparison_revenue.validated_result_id,
        revenue_change_validated_result_ref=revenue_change.validated_result_id,
        baseline_revenue_evidence_ref=admitted[0].evidence_id,
        baseline_revenue_evidence_fingerprint=admitted[0].evidence_fingerprint,
        comparison_revenue_evidence_ref=admitted[1].evidence_id,
        comparison_revenue_evidence_fingerprint=admitted[1].evidence_fingerprint,
        revenue_change_evidence_ref=admitted[2].evidence_id,
        revenue_change_evidence_fingerprint=admitted[2].evidence_fingerprint,
    )
    counters: dict[str, int] = {}

    def deterministic_r4_id(prefix: str) -> str:
        counters[prefix] = counters.get(prefix, 0) + 1
        return f"{prefix}_r6_5_{recipe}_{counters[prefix]}"

    original_contract_generate = r4_contract_module.generate_id
    original_execution_generate = r4_execution_module.generate_id
    r4_contract_module.generate_id = deterministic_r4_id
    r4_execution_module.generate_id = deterministic_r4_id
    try:
        r4_outcome = run_r4_decomposition(
            request=r4_request,
            plan=scalar.plan,
            canonical_dataset=scalar.canonical,
            artifact_store=scalar.artifact_store,
            metadata_store=scalar.metadata_store,
        )
    finally:
        r4_contract_module.generate_id = original_contract_generate
        r4_execution_module.generate_id = original_execution_generate
    return SyntheticAnalysis(
        scalar,
        baseline_revenue,
        comparison_revenue,
        revenue_change,
        baseline_orders,
        comparison_orders,
        baseline_aov,
        comparison_aov,
        r4_outcome,
    )


def descriptor() -> CandidateProducerDescriptor:
    return CandidateProducerDescriptor(
        producer_id="producer:r6-5-fixture",
        producer_version="1.0.0",
        template_id="template:r6-5-fixture",
        template_version="1.0.0",
        template_fingerprint=HASH,
        generation_parameters=GenerationParameters(temperature=0.0, max_output_tokens=500),
    )


def external_activation() -> FamilyActivation:
    return FamilyActivation(
        family_id="external_market_association",
        activation_ref="activation:explicit-economy-request",
        external_factor_ref="external:consumer_sentiment",
        external_dependency_ref="dependency:governed-external-evidence",
    )


def _candidate(context: Any, family: str, *, wording: str = "candidate") -> CandidateProposal:
    values: dict[str, Any] = {
        "outcome_ref": context.outcome_metric_ref,
        "scope_ref": context.scope_ref,
        "baseline_period_ref": context.baseline_period_ref,
        "comparison_period_ref": context.comparison_period_ref,
        "baseline_population_ref": context.baseline_population_ref,
        "comparison_population_ref": context.comparison_population_ref,
    }
    source_refs: tuple[str, ...] = ()
    if family == "product_composition_association":
        source = next(
            item.authority_ref for item in context.source_authority_views
            if item.authority_class.value == "SOURCE_REFERENCE"
            and item.dependency_classification.value == "INTERNAL"
        )
        values.update(
            product_identity_ref="field:product_id",
            monetary_observation_ref="field:line_revenue",
            source_observation_refs=(source,),
        )
        source_refs = (source,)
        if context.source_mechanical_result_ref is not None:
            values["optional_r4_result_ref"] = context.source_mechanical_result_ref
            source_refs = (*source_refs, context.source_mechanical_result_ref)
        template = "r6-product-composition-untested-v1"
    elif family == "discounting_association":
        source = next(
            item.authority_ref for item in context.source_authority_views
            if item.authority_class.value == "SOURCE_REFERENCE"
            and item.dependency_classification.value == "INTERNAL"
        )
        values.update(
            original_or_list_price_ref="requirement:original_or_list_price",
            discount_semantics_ref="requirement:governed_discount_semantics",
            monetary_observation_ref="field:line_revenue",
            source_observation_refs=(source,),
        )
        source_refs = (source,)
        template = "r6-discounting-untested-v1"
    else:
        activation = next(item for item in context.family_activations if item.family_id == family)
        values.update(
            external_factor_ref=activation.external_factor_ref,
            external_evidence_dependency_ref=activation.external_dependency_ref,
            source_observation_refs=(activation.external_dependency_ref,),
            explicit_activation_ref=activation.activation_ref,
        )
        source_refs = (activation.external_dependency_ref,)
        template = "r6-external-market-untested-v1"
    return CandidateProposal(
        family_id=family,
        family_version="1.0.0",
        structured_slot_values=tuple(CandidateSlot(slot=key, value=value) for key, value in values.items()),
        source_reference_proposals=source_refs,
        display_template_id=template,
        non_authoritative_wording=wording,
    )


def _mutate_slot(candidate: CandidateProposal, slot: str, value: Any) -> CandidateProposal:
    slots = tuple(
        item.model_copy(update={"value": value}) if item.slot == slot else item
        for item in candidate.structured_slot_values
    )
    updates: dict[str, Any] = {"structured_slot_values": slots}
    if slot == "source_observation_refs":
        updates["source_reference_proposals"] = value
    return candidate.model_copy(update=updates)


class FixtureCandidateProducer:
    def __init__(self, recipe: str) -> None:
        self.recipe = recipe
        self.context: Any = None

    def produce_candidates(self, context: Any) -> Any:
        self.context = context
        recipe = self.recipe
        if recipe == "raise_exception":
            raise RuntimeError("deterministic R6-5 producer exception")
        if recipe == "extra_confidence_field":
            raw = self._batch(context, (_candidate(context, "product_composition_association"),)).model_dump(mode="python")
            raw["candidates"][0]["confidence"] = "forbidden"
            return raw
        if recipe in {"unknown_family", "unknown_family_orders_change"}:
            candidate = _candidate(context, "product_composition_association").model_copy(
                update={"family_id": "orders_change" if recipe.endswith("orders_change") else "unknown_family"}
            )
            return self._batch(context, (candidate,))
        if recipe == "external_without_activation":
            candidate = _candidate(context, "product_composition_association").model_copy(
                update={"family_id": "external_market_association"}
            )
            return self._batch(context, (candidate,))
        if recipe == "valid_product_plus_disallowed_external":
            product = _candidate(context, "product_composition_association")
            external = product.model_copy(update={"family_id": "external_market_association"})
            return self._batch(context, (product, external))

        family = "discounting_association" if recipe in {
            "valid_discount", "valid_discount_then_product",
            "discount_substitute_unit_price", "discount_substitute_line_revenue",
            "discount_substitute_revenue", "discount_substitute_aov",
        } else "external_market_association" if recipe == "valid_external" else "product_composition_association"
        candidate = _candidate(
            context,
            family,
            wording="new products caused growth" if recipe == "valid_product_hostile_wording" else "candidate",
        )
        substitutions = {
            "discount_substitute_unit_price": "field:unit_price",
            "discount_substitute_line_revenue": "field:line_revenue",
            "discount_substitute_revenue": "metric:Revenue",
            "discount_substitute_aov": "metric:AOV",
        }
        if recipe in substitutions:
            candidate = _mutate_slot(candidate, "original_or_list_price_ref", substitutions[recipe])
        mutations = {
            "invented_metric": ("outcome_ref", "metric:invented"),
            "invented_variable": ("product_identity_ref", "field:invented"),
            "invented_source": ("source_observation_refs", ("source:invented",)),
            "period_mismatch": ("baseline_period_ref", "period:invented"),
            "population_mismatch": ("comparison_population_ref", "population:invented"),
        }
        if recipe in mutations:
            candidate = _mutate_slot(candidate, *mutations[recipe])
        if recipe == "valid_discount_then_product":
            candidates = (candidate, _candidate(context, "product_composition_association"))
        elif recipe == "omit_requested_external_emit_product":
            candidates = (_candidate(context, "product_composition_association"),)
        elif recipe == "reordered_duplicate_peers":
            product = _candidate(context, "product_composition_association", wording="first")
            product_reordered = product.model_copy(
                update={
                    "structured_slot_values": tuple(reversed(product.structured_slot_values)),
                    "source_reference_proposals": tuple(reversed(product.source_reference_proposals)),
                    "non_authoritative_wording": "different wording",
                }
            )
            candidates = (
                _candidate(context, "discounting_association"),
                product_reordered,
                product,
            )
        else:
            candidates = (candidate,)
        return self._batch(context, candidates)

    @staticmethod
    def _batch(context: Any, candidates: tuple[CandidateProposal, ...]) -> CandidateProposalBatch:
        return CandidateProposalBatch(
            batch_schema_version="1.0.0",
            producer_ref="producer:r6-5-fixture",
            generation_request_ref=context.generation_request_ref,
            candidates=candidates,
        )


@dataclass(frozen=True)
class ServiceCaseRun:
    case: R6FixtureCase
    analysis: SyntheticAnalysis
    producer: FixtureCandidateProducer
    outcome: R6RunOutcome

    @property
    def repository(self) -> R6Repository:
        return R6Repository(self.analysis.scalar.artifact_store, self.analysis.scalar.metadata_store)


def run_service_case(
    tmp_path: Path,
    fixture_case: R6FixtureCase,
    *,
    handoff: bool = False,
    analysis: SyntheticAnalysis | None = None,
) -> ServiceCaseRun:
    analysis = analysis or build_synthetic_analysis(tmp_path, fixture_case.analysis_recipe or "product_decline")
    activations = (external_activation(),) if fixture_case.family_activations else ()
    request = build_generation_request(
        analysis_request_ref=analysis.scalar.request.request_id,
        requested_family_ids=fixture_case.requested_family_ids,
        family_activations=activations,
    )
    producer = FixtureCandidateProducer(fixture_case.producer_recipe)
    outcome = run_r6(
        generation_request=request,
        producer=producer,
        producer_descriptor=descriptor(),
        analysis_request_ref=analysis.scalar.request.request_id,
        sufficiency_ref=analysis.scalar.sufficiency.sufficiency_id,
        plan=analysis.scalar.plan,
        revenue_change_validated_result_ref=analysis.revenue_change.validated_result_id,
        artifact_store=analysis.scalar.artifact_store,
        metadata_store=analysis.scalar.metadata_store,
        generated_at=NOW,
        finalized_at=NOW,
        r4_validated_result_artifact=analysis.r4_outcome.validation.validated_result_artifact,
        persist_handoff=handoff,
    )
    return ServiceCaseRun(fixture_case, analysis, producer, outcome)


def metric_values(analysis: SyntheticAnalysis) -> dict[str, tuple[Decimal | int, Decimal | int]]:
    return {
        "revenue": (analysis.baseline_revenue.value, analysis.comparison_revenue.value),
        "orders": (analysis.baseline_orders.value, analysis.comparison_orders.value),
        "aov": (analysis.baseline_aov.value, analysis.comparison_aov.value),
    }


def raw_artifact_payload(run: ServiceCaseRun, artifact_type: str, artifact_id: str) -> dict[str, Any]:
    index = run.analysis.scalar.metadata_store.get_r6_artifact_index(artifact_type, artifact_id)
    assert index is not None
    reference = run.analysis.scalar.metadata_store.get_artifact_reference(index.artifact_reference_id)
    assert reference is not None
    return json.loads(run.analysis.scalar.artifact_store.safe_path(reference.path).read_text(encoding="utf-8"))
