"""Canonicalization request and result models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import Field

from commerce_lens.canonical.mapping import CanonicalMapping
from commerce_lens.canonical.quality import DataQualityCheckResult
from commerce_lens.canonical.schema import CANONICAL_SCHEMA_VERSION
from commerce_lens.contracts.common import ContractBase, Qualification
from commerce_lens.contracts.evidence import CanonicalDatasetReference, CanonicalizationRecord


CANONICALIZATION_VERSION = "phase2_canonicalization_v1"
SUPPORTED_DATE_POLICY_REF = "order_date_iso_date_only"


class EligibilityMode(str, Enum):
    UPSTREAM_ELIGIBLE_ONLY = "upstream_eligible_only"
    EXPLICIT_STATUS_MAPPING = "explicit_status_mapping"


class EligibilityState(str, Enum):
    ELIGIBLE = "Eligible"
    EXCLUDED = "Excluded"


class EligibilityValueMapping(ContractBase):
    source_value: str = Field(min_length=1)
    normalized_status: EligibilityState


class CanonicalizationRequest(ContractBase):
    source_dataset_id: str = Field(min_length=1)
    canonical_schema_version: str = CANONICAL_SCHEMA_VERSION
    selected_sheet: str | None = None
    selected_table: str | None = None
    mapping: CanonicalMapping
    eligibility_mode: EligibilityMode
    eligibility_value_mapping: tuple[EligibilityValueMapping, ...] = ()
    require_category: bool = False
    unsupported_partial_refund_evidence: bool = False
    date_policy_ref: str = SUPPORTED_DATE_POLICY_REF
    currency_basis_ref: str | None = None


class PeriodCoverageEvidence(ContractBase):
    coverage_ref_id: str = Field(min_length=1)
    dataset_ref_id: str = Field(min_length=1)
    observed_start_date: date
    observed_end_date: date
    date_convention_ref: str = Field(min_length=1)
    governing_note_ref: str | None = None


class CanonicalLineRecord(ContractBase):
    source_row_number: int = Field(ge=1)
    order_id: str = Field(min_length=1)
    order_line_id: str = Field(min_length=1)
    order_date: date
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    line_revenue: Decimal = Field(ge=Decimal("0"))
    currency: str = Field(min_length=1)
    eligibility_status: EligibilityState
    product_name: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    unit_price: Decimal | None = None


class CanonicalizationResult(ContractBase):
    record: CanonicalizationRecord
    canonical_dataset: CanonicalDatasetReference | None = None
    data_quality_results: tuple[DataQualityCheckResult, ...] = ()
    qualifications: tuple[Qualification, ...] = ()
    failures: tuple[str, ...] = ()
    canonical_rows: tuple[CanonicalLineRecord, ...] = ()

    @property
    def has_blocking_failures(self) -> bool:
        return bool(self.failures)
