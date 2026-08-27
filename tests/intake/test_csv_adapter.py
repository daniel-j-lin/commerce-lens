from commerce_lens.evidence.identifiers import sha256_file
from commerce_lens.intake.csv_adapter import CsvInspectionAdapter
from commerce_lens.intake.inspection import InspectionStatus
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore


def test_valid_csv_inspection_discovers_columns_and_preserves_source(tmp_path) -> None:
    source = tmp_path / "orders.csv"
    source.write_text("order_id,line_revenue\n1,10.5\n2,20\n", encoding="utf-8")
    before = sha256_file(source)
    registry = DatasetRegistry(ArtifactStore(tmp_path / "runtime"), MetadataStore(tmp_path / "registry.sqlite"))

    result = CsvInspectionAdapter(registry).inspect(source)

    assert result.status is InspectionStatus.SUPPORTED
    assert result.dataset_ref_id is not None
    assert [column.name for column in result.columns] == ["order_id", "line_revenue"]
    assert result.row_count == 2
    assert sha256_file(source) == before


def test_csv_rejects_inconsistent_rows(tmp_path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text("a,b\n1,2\n3\n", encoding="utf-8")

    result = CsvInspectionAdapter().inspect(source)

    assert result.status is InspectionStatus.FAILED
    assert "expected 2" in result.failure_detail.reason

