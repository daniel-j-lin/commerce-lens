"""Governed canonical schema authority for the CommerceLens MVP."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from commerce_lens.contracts.common import ContractBase


CANONICAL_SCHEMA_VERSION = "canonical_mvp_v1"
UNCLASSIFIED_CATEGORY_ID = "__COMMERCE_LENS_UNCLASSIFIED__"
UNCLASSIFIED_CATEGORY_NAME = "Unclassified"


class RequirementLevel(str, Enum):
    REQUIRED = "required"
    CONDITIONALLY_REQUIRED = "conditionally_required"
    OPTIONAL = "optional"


class LogicalType(str, Enum):
    IDENTIFIER = "identifier"
    DATE = "date"
    INTEGER = "integer"
    DECIMAL = "decimal"
    CURRENCY_CODE = "currency_code"
    TEXT = "text"
    ELIGIBILITY_STATUS = "eligibility_status"


class NullPolicy(str, Enum):
    PROHIBITED = "prohibited"
    ALLOWED = "allowed"
    GOVERNED_UNCLASSIFIED = "governed_unclassified"


class CanonicalFieldDefinition(ContractBase):
    name: str = Field(min_length=1)
    requirement_level: RequirementLevel
    logical_type: LogicalType
    null_policy: NullPolicy
    participates_in_row_identity: bool = False
    governed_validation_refs: tuple[str, ...] = ()


CANONICAL_FIELDS: tuple[CanonicalFieldDefinition, ...] = (
    CanonicalFieldDefinition(
        name="order_id",
        requirement_level=RequirementLevel.REQUIRED,
        logical_type=LogicalType.IDENTIFIER,
        null_policy=NullPolicy.PROHIBITED,
        participates_in_row_identity=True,
        governed_validation_refs=("canonical_dictionary:7.1", "canonical_dictionary:9"),
    ),
    CanonicalFieldDefinition(
        name="order_line_id",
        requirement_level=RequirementLevel.REQUIRED,
        logical_type=LogicalType.IDENTIFIER,
        null_policy=NullPolicy.PROHIBITED,
        participates_in_row_identity=True,
        governed_validation_refs=("canonical_dictionary:7.1", "canonical_dictionary:9"),
    ),
    CanonicalFieldDefinition(
        name="order_date",
        requirement_level=RequirementLevel.REQUIRED,
        logical_type=LogicalType.DATE,
        null_policy=NullPolicy.PROHIBITED,
        governed_validation_refs=("canonical_dictionary:15", "canonical_dictionary:16"),
    ),
    CanonicalFieldDefinition(
        name="product_id",
        requirement_level=RequirementLevel.REQUIRED,
        logical_type=LogicalType.IDENTIFIER,
        null_policy=NullPolicy.PROHIBITED,
        governed_validation_refs=("canonical_dictionary:19",),
    ),
    CanonicalFieldDefinition(
        name="product_name",
        requirement_level=RequirementLevel.OPTIONAL,
        logical_type=LogicalType.TEXT,
        null_policy=NullPolicy.ALLOWED,
        governed_validation_refs=("canonical_dictionary:19",),
    ),
    CanonicalFieldDefinition(
        name="category_id",
        requirement_level=RequirementLevel.CONDITIONALLY_REQUIRED,
        logical_type=LogicalType.IDENTIFIER,
        null_policy=NullPolicy.GOVERNED_UNCLASSIFIED,
        governed_validation_refs=("canonical_dictionary:20", "canonical_dictionary:29.2"),
    ),
    CanonicalFieldDefinition(
        name="category_name",
        requirement_level=RequirementLevel.OPTIONAL,
        logical_type=LogicalType.TEXT,
        null_policy=NullPolicy.ALLOWED,
        governed_validation_refs=("canonical_dictionary:20",),
    ),
    CanonicalFieldDefinition(
        name="quantity",
        requirement_level=RequirementLevel.REQUIRED,
        logical_type=LogicalType.INTEGER,
        null_policy=NullPolicy.PROHIBITED,
        governed_validation_refs=("canonical_dictionary:31",),
    ),
    CanonicalFieldDefinition(
        name="line_revenue",
        requirement_level=RequirementLevel.REQUIRED,
        logical_type=LogicalType.DECIMAL,
        null_policy=NullPolicy.PROHIBITED,
        governed_validation_refs=("canonical_dictionary:32.1",),
    ),
    CanonicalFieldDefinition(
        name="currency",
        requirement_level=RequirementLevel.REQUIRED,
        logical_type=LogicalType.CURRENCY_CODE,
        null_policy=NullPolicy.PROHIBITED,
        governed_validation_refs=("canonical_dictionary:32.2",),
    ),
    CanonicalFieldDefinition(
        name="eligibility_status",
        requirement_level=RequirementLevel.CONDITIONALLY_REQUIRED,
        logical_type=LogicalType.ELIGIBILITY_STATUS,
        null_policy=NullPolicy.PROHIBITED,
        governed_validation_refs=("canonical_dictionary:12", "canonical_dictionary:27"),
    ),
    CanonicalFieldDefinition(
        name="unit_price",
        requirement_level=RequirementLevel.OPTIONAL,
        logical_type=LogicalType.DECIMAL,
        null_policy=NullPolicy.ALLOWED,
        governed_validation_refs=("canonical_dictionary:10",),
    ),
)

CANONICAL_FIELD_NAMES = tuple(field.name for field in CANONICAL_FIELDS)
CANONICAL_FIELD_DEFINITIONS = {field.name: field for field in CANONICAL_FIELDS}
REQUIRED_CANONICAL_FIELD_NAMES = tuple(
    field.name for field in CANONICAL_FIELDS if field.requirement_level is RequirementLevel.REQUIRED
)
