from commerce_lens.canonical.mapping import CanonicalFieldMapping, CanonicalMapping, identity_mapping, validate_mapping
from commerce_lens.canonical.quality import DataQualityConsequence


SOURCE_COLUMNS = (
    "order_id",
    "order_line_id",
    "order_date",
    "product_id",
    "quantity",
    "line_revenue",
    "currency",
)


def test_valid_explicit_mapping_passes() -> None:
    mapping = CanonicalMapping(
        mapping_id="map_explicit",
        entries=tuple(CanonicalFieldMapping(canonical_field=name, source_field=name) for name in SOURCE_COLUMNS),
    )

    results = validate_mapping(mapping, SOURCE_COLUMNS)

    assert [result.check_id for result in results] == ["canonical_mapping.valid"]


def test_exact_name_identity_mapping_is_recorded_explicitly() -> None:
    mapping = identity_mapping(SOURCE_COLUMNS)

    assert mapping.mapping_id.startswith("map_")
    assert {entry.canonical_field: entry.source_field for entry in mapping.entries} == {
        name: name for name in SOURCE_COLUMNS
    }


def test_missing_required_mapping_fails_closed() -> None:
    mapping = CanonicalMapping(
        mapping_id="map_missing_required",
        entries=tuple(
            CanonicalFieldMapping(canonical_field=name, source_field=name)
            for name in SOURCE_COLUMNS
            if name != "line_revenue"
        ),
    )

    results = validate_mapping(mapping, SOURCE_COLUMNS)

    assert any(result.check_id == "canonical_mapping.required_missing" for result in results)
    assert any(result.consequence is DataQualityConsequence.BLOCKING for result in results)


def test_source_field_that_does_not_exist_fails() -> None:
    mapping = CanonicalMapping(
        mapping_id="map_bad_source",
        entries=tuple(
            CanonicalFieldMapping(
                canonical_field=name,
                source_field="missing_column" if name == "currency" else name,
            )
            for name in SOURCE_COLUMNS
        ),
    )

    results = validate_mapping(mapping, SOURCE_COLUMNS)

    assert any(result.check_id == "canonical_mapping.missing_source_field" for result in results)


def test_duplicate_canonical_target_fails() -> None:
    entries = tuple(CanonicalFieldMapping(canonical_field=name, source_field=name) for name in SOURCE_COLUMNS)
    mapping = CanonicalMapping(
        mapping_id="map_duplicate_target",
        entries=entries + (CanonicalFieldMapping(canonical_field="currency", source_field="order_id"),),
    )

    results = validate_mapping(mapping, SOURCE_COLUMNS)

    assert any(result.check_id == "canonical_mapping.duplicate_canonical_target" for result in results)


def test_unknown_canonical_target_fails() -> None:
    entries = tuple(CanonicalFieldMapping(canonical_field=name, source_field=name) for name in SOURCE_COLUMNS)
    mapping = CanonicalMapping(
        mapping_id="map_unknown_target",
        entries=entries + (CanonicalFieldMapping(canonical_field="customer_id", source_field="order_id"),),
    )

    results = validate_mapping(mapping, SOURCE_COLUMNS)

    assert any(result.check_id == "canonical_mapping.unknown_target" for result in results)
