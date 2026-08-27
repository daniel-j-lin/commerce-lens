import pytest

from commerce_lens.persistence import artifact_store as artifact_store_module
from commerce_lens.evidence.identifiers import sha256_file
from commerce_lens.persistence.artifact_store import ArtifactStore


def test_artifact_store_creates_safe_layout(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "runtime")
    store.ensure_layout()
    for directory in ("sources", "canonical", "runs", "temporary"):
        assert (tmp_path / "runtime" / directory).is_dir()


def test_artifact_store_rejects_path_traversal(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "runtime")
    with pytest.raises(ValueError):
        store.safe_path("..", "outside")
    with pytest.raises(ValueError):
        store.safe_path(tmp_path / "absolute")


def test_source_snapshot_is_content_addressed_and_immutable(tmp_path) -> None:
    source = tmp_path / "orders.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    before = sha256_file(source)
    store = ArtifactStore(tmp_path / "runtime")

    first = store.snapshot_source(source)
    second = store.snapshot_source(source)

    assert first.path == second.path
    assert first.fingerprint == before
    assert sha256_file(source) == before
    snapshot_path = store.safe_path(first.path)
    assert sha256_file(snapshot_path) == before


def test_source_snapshot_verifies_bytes_after_copy(tmp_path, monkeypatch) -> None:
    source = tmp_path / "orders.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    store = ArtifactStore(tmp_path / "runtime")

    def corrupt_copy(source_path, destination_path):
        destination_path.write_text("changed\n", encoding="utf-8")

    monkeypatch.setattr(artifact_store_module.shutil, "copy2", corrupt_copy)

    with pytest.raises(ValueError, match="fingerprint mismatch after copy"):
        store.snapshot_source(source)
