"""Schema-mapping UX helpers for the Public CommerceLens Skill boundary."""

from __future__ import annotations

from dataclasses import dataclass

from commerce_lens.canonical.mapping import CanonicalFieldMapping, CanonicalMapping, identity_mapping
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id
from commerce_lens.metrics import get_metric_registry


_REQUIRED_CANONICALIZATION_FIELDS = (
    "order_id",
    "order_line_id",
    "order_date",
    "product_id",
    "quantity",
    "line_revenue",
    "currency",
)

_PUBLIC_ELIGIBILITY_FIELD = "eligibility_status"

_ALIASES_BY_CANONICAL_FIELD: dict[str, tuple[str, ...]] = {
    "order_id": ("Order ID", "Order Number", "orderId"),
    "order_line_id": ("Order Line ID", "Line Item ID", "orderLineId"),
    "order_date": ("Order Date", "Created At", "orderDate"),
    "product_id": ("Product ID", "SKU", "productId"),
    "product_name": ("Product Name", "Product", "productName"),
    "category_id": ("Category ID", "Product Type", "categoryId"),
    "category_name": ("Category Name", "Product Type Name", "categoryName"),
    "quantity": ("Quantity", "Qty", "quantity"),
    "line_revenue": ("Revenue", "Total Sales", "lineRevenue"),
    "currency": ("Currency", "currency"),
    "unit_price": ("Unit Price", "Price", "unitPrice"),
    "eligibility_status": ("Order Status", "Financial Status", "eligibilityStatus"),
}


@dataclass(frozen=True)
class SourceToCanonicalMappingProposal:
    source_field: str
    canonical_field: str


@dataclass(frozen=True)
class SchemaMappingAssessment:
    required_canonical_fields: tuple[str, ...]
    identity_mapping_available: bool
    proposals: tuple[SourceToCanonicalMappingProposal, ...] = ()
    clarification_required: tuple[str, ...] = ()
    missing_required_fields: tuple[str, ...] = ()
    ambiguous_required_fields: tuple[str, ...] = ()

    @property
    def confirmation_required(self) -> bool:
        return bool(self.proposals) and not self.identity_mapping_available

    @property
    def can_propose_complete_mapping(self) -> bool:
        proposed = {proposal.canonical_field for proposal in self.proposals}
        return (
            bool(self.proposals)
            and set(self.required_canonical_fields).issubset(proposed)
            and not self.clarification_required
        )


def required_public_mapping_fields(metric_id: str) -> tuple[str, ...]:
    """Return required canonical fields for the current public execution path."""
    registry = get_metric_registry()
    metric = registry.require(metric_id)
    fields: list[str] = []
    for field in (*_REQUIRED_CANONICALIZATION_FIELDS, _PUBLIC_ELIGIBILITY_FIELD, *metric.required_canonical_fields):
        if field not in fields:
            fields.append(field)
    return tuple(fields)


def assess_schema_mapping(source_headers: tuple[str, ...], metric_id: str) -> SchemaMappingAssessment:
    """Inspect headers and prepare non-authoritative source-to-canonical proposals."""
    required_fields = required_public_mapping_fields(metric_id)
    identity = identity_mapping(source_headers, require_eligibility=True)
    if all(identity.source_for(field) is not None for field in required_fields):
        return SchemaMappingAssessment(
            required_canonical_fields=required_fields,
            identity_mapping_available=True,
        )

    source_set = set(source_headers)
    proposals: list[SourceToCanonicalMappingProposal] = []
    missing: list[str] = []
    ambiguous: list[str] = []
    clarifications: list[str] = []
    for canonical_field in required_fields:
        if canonical_field in source_set:
            proposals.append(SourceToCanonicalMappingProposal(canonical_field, canonical_field))
            continue
        candidates = tuple(alias for alias in _ALIASES_BY_CANONICAL_FIELD.get(canonical_field, ()) if alias in source_set)
        if len(candidates) == 1:
            proposals.append(SourceToCanonicalMappingProposal(candidates[0], canonical_field))
            continue
        if len(candidates) > 1:
            ambiguous.append(canonical_field)
            clarifications.append(
                f"Which source column represents {canonical_field}: {', '.join(candidates)}, or another field?"
            )
            continue
        missing.append(canonical_field)
        clarifications.append(f"Which source column represents {canonical_field}?")

    if proposals:
        clarifications.append(
            "Confirm or correct the proposed source-to-canonical mapping before CommerceLens can analyze the file."
        )
    else:
        clarifications.append("Required mapping authority is missing; CommerceLens cannot analyze the file yet.")

    return SchemaMappingAssessment(
        required_canonical_fields=required_fields,
        identity_mapping_available=False,
        proposals=tuple(proposals),
        clarification_required=tuple(dict.fromkeys(clarifications)),
        missing_required_fields=tuple(missing),
        ambiguous_required_fields=tuple(ambiguous),
    )


def confirmed_mapping_from_source_to_canonical(source_to_canonical: dict[str, str]) -> CanonicalMapping:
    """Construct the existing deterministic mapping contract from confirmed UX input."""
    entries = tuple(
        CanonicalFieldMapping(canonical_field=canonical_field, source_field=source_field)
        for source_field, canonical_field in source_to_canonical.items()
    )
    return CanonicalMapping(
        mapping_id=stable_content_id(
            "map",
            canonical_json_fingerprint({"confirmed_source_to_canonical": source_to_canonical}),
        ),
        entries=entries,
    )
