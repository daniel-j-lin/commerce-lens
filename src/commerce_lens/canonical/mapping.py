"""Explicit source-to-canonical mapping contract."""

from __future__ import annotations

from pydantic import Field, model_validator

from commerce_lens.canonical.quality import DataQualityCheckResult, blocking, passed
from commerce_lens.canonical.schema import (
    CANONICAL_FIELD_DEFINITIONS,
    CANONICAL_FIELD_NAMES,
    REQUIRED_CANONICAL_FIELD_NAMES,
)
from commerce_lens.contracts.common import ContractBase
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id


class CanonicalFieldMapping(ContractBase):
    canonical_field: str = Field(min_length=1)
    source_field: str | None = Field(default=None, min_length=1)
    unavailable_reason: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def source_or_unavailable(self) -> "CanonicalFieldMapping":
        if (self.source_field is None) == (self.unavailable_reason is None):
            raise ValueError("exactly one of source_field or unavailable_reason is required")
        return self


class CanonicalMapping(ContractBase):
    mapping_id: str = Field(min_length=1)
    entries: tuple[CanonicalFieldMapping, ...]

    @property
    def fingerprint(self) -> str:
        return canonical_json_fingerprint(self.model_dump(mode="json"))

    def source_for(self, canonical_field: str) -> str | None:
        for entry in self.entries:
            if entry.canonical_field == canonical_field:
                return entry.source_field
        return None


def identity_mapping(
    source_columns: tuple[str, ...] | list[str],
    *,
    unavailable_required_fields: tuple[str, ...] = (),
    require_category: bool = False,
    require_eligibility: bool = False,
) -> CanonicalMapping:
    """Build exact-name identity mappings only for canonical fields present in the source."""
    source_set = set(source_columns)
    entries: list[CanonicalFieldMapping] = []
    required = set(REQUIRED_CANONICAL_FIELD_NAMES)
    if require_category:
        required.add("category_id")
    if require_eligibility:
        required.add("eligibility_status")
    for field_name in CANONICAL_FIELD_NAMES:
        if field_name in source_set:
            entries.append(CanonicalFieldMapping(canonical_field=field_name, source_field=field_name))
        elif field_name in unavailable_required_fields:
            entries.append(
                CanonicalFieldMapping(
                    canonical_field=field_name,
                    unavailable_reason="explicitly unavailable in source",
                )
            )
    payload = tuple(entry.model_dump(mode="json") for entry in entries)
    return CanonicalMapping(
        mapping_id=stable_content_id(
            "map",
            canonical_json_fingerprint({"identity_mapping": payload, "source_columns": tuple(source_columns)}),
        ),
        entries=tuple(entries),
    )


def validate_mapping(
    mapping: CanonicalMapping,
    source_columns: tuple[str, ...] | list[str],
    *,
    require_category: bool = False,
    require_eligibility: bool = False,
) -> tuple[DataQualityCheckResult, ...]:
    source_set = set(source_columns)
    results: list[DataQualityCheckResult] = []
    seen_canonical: set[str] = set()
    seen_source: set[str] = set()
    has_blocking = False
    for entry in mapping.entries:
        if entry.canonical_field not in CANONICAL_FIELD_DEFINITIONS:
            has_blocking = True
            results.append(
                blocking(
                    "canonical_mapping.unknown_target",
                    entry.canonical_field,
                    "phase2:source_to_canonical_mapping",
                    f"unknown canonical field target: {entry.canonical_field}",
                )
            )
            continue
        if entry.canonical_field in seen_canonical:
            has_blocking = True
            results.append(
                blocking(
                    "canonical_mapping.duplicate_canonical_target",
                    entry.canonical_field,
                    "phase2:source_to_canonical_mapping",
                    f"canonical field maps more than once: {entry.canonical_field}",
                )
            )
        seen_canonical.add(entry.canonical_field)
        if entry.source_field is None:
            continue
        if entry.source_field not in source_set:
            has_blocking = True
            results.append(
                blocking(
                    "canonical_mapping.missing_source_field",
                    entry.source_field,
                    "phase2:source_to_canonical_mapping",
                    f"mapped source field does not exist: {entry.source_field}",
                )
            )
        if entry.source_field in seen_source:
            has_blocking = True
            results.append(
                blocking(
                    "canonical_mapping.duplicate_source_field",
                    entry.source_field,
                    "phase2:source_to_canonical_mapping",
                    f"source field maps to more than one canonical field: {entry.source_field}",
                )
            )
        seen_source.add(entry.source_field)

    required = set(REQUIRED_CANONICAL_FIELD_NAMES)
    if require_category:
        required.add("category_id")
    if require_eligibility:
        required.add("eligibility_status")
    mapped_or_declared = {entry.canonical_field for entry in mapping.entries}
    for field_name in sorted(required - mapped_or_declared):
        has_blocking = True
        results.append(
            blocking(
                "canonical_mapping.required_missing",
                field_name,
                "canonical_dictionary:9",
                f"required canonical field is not mapped or explicitly unavailable: {field_name}",
            )
        )
    for entry in mapping.entries:
        if entry.canonical_field in required and entry.unavailable_reason is not None:
            has_blocking = True
            results.append(
                blocking(
                    "canonical_mapping.required_unavailable",
                    entry.canonical_field,
                    "canonical_dictionary:9",
                    f"required canonical field is explicitly unavailable: {entry.canonical_field}",
                )
            )
    if not has_blocking:
        results.append(
            passed(
                "canonical_mapping.valid",
                mapping.mapping_id,
                "phase2:source_to_canonical_mapping",
                "source-to-canonical mapping is explicit and valid",
            )
        )
    return tuple(results)
