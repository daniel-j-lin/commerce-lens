from commerce_lens.evidence.identifiers import (
    canonical_json_fingerprint,
    generate_id,
    sha256_bytes,
    sha256_file,
    stable_content_id,
)


def test_sha256_bytes_is_stable_and_content_sensitive() -> None:
    assert sha256_bytes(b"commerce") == sha256_bytes(b"commerce")
    assert sha256_bytes(b"commerce") != sha256_bytes(b"lens")


def test_streaming_file_hash_matches_byte_hash(tmp_path) -> None:
    path = tmp_path / "source.csv"
    content = b"a,b\n1,2\n"
    path.write_bytes(content)
    assert sha256_file(path) == sha256_bytes(content)


def test_canonical_json_fingerprint_ignores_key_order() -> None:
    assert canonical_json_fingerprint({"b": 2, "a": 1}) == canonical_json_fingerprint({"a": 1, "b": 2})


def test_generated_and_stable_ids_have_type_prefixes() -> None:
    assert generate_id("run").startswith("run_")
    fingerprint = sha256_bytes(b"dataset")
    assert stable_content_id("ds", fingerprint) == stable_content_id("ds", fingerprint)
    assert stable_content_id("ds", fingerprint).startswith("ds_")

