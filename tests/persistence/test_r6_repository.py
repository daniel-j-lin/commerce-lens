from __future__ import annotations

import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import pytest

from commerce_lens.contracts.diagnostic import EvidenceReadiness
from commerce_lens.contracts.hypotheses import (
    GenerationParameters,
    GenerationProvenance,
    GovernedHypothesis,
    R6ToR7Handoff,
    generation_provenance_semantic_fingerprint,
    governed_hypothesis_semantic_fingerprint,
    r6_to_r7_handoff_semantic_fingerprint,
)
from commerce_lens.diagnostic.governance import AuthorityClass
from commerce_lens.evidence.identifiers import canonical_json_bytes, sha256_bytes
from commerce_lens.persistence import artifact_store as artifact_store_module
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.r6_repository import (
    R6ArtifactIntegrityError,
    R6ArtifactType,
    R6Repository,
)
from tests.diagnostic.test_r6_governance import (
    NOW,
    _all_assessments,
    _authority_registry,
    _proposition,
    _registry_from_records,
    _run,
)


@dataclass(frozen=True)
class Graph:
    repo: R6Repository
    registry: object
    proposition: object
    profile: object
    judgments: tuple
    evaluation: object
    provenance: GenerationProvenance
    hypothesis: GovernedHypothesis
    handoff: R6ToR7Handoff


def _build_graph(tmp_path, *, name: str = "main") -> Graph:
    proposition = _proposition(display_wording=f"{name} wording")
    assessments = _all_assessments(proposition)
    registry = _authority_registry(proposition, assessments)
    governed = _run(
        proposition=proposition,
        assessments=assessments,
        authority_registry=registry,
    )
    provenance_data = {
        "generation_provenance_id": f"genprov-{name}",
        "generator_id": "bounded-candidate-producer",
        "generator_version": "1.0.0",
        "prompt_template_id": "prompt:r6-candidates",
        "prompt_template_version": "1.0.0",
        "prompt_template_fingerprint": "a" * 64,
        "model_id": None,
        "generation_parameters": GenerationParameters(temperature=0.0, max_output_tokens=500),
        "raw_candidate_artifact_ref": None,
        "generated_at": NOW,
    }
    provenance_data["provenance_fingerprint"] = generation_provenance_semantic_fingerprint(
        provenance_data
    )
    provenance = GenerationProvenance(**provenance_data)
    hypothesis_data = {
        "governed_hypothesis_id": f"hyp-{name}",
        "governed_hypothesis_schema_version": "1.0.0",
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "pretest_evaluation_ref": governed.evaluation.evaluation_id,
        "pretest_evaluation_fingerprint": governed.evaluation.evaluation_fingerprint,
        "resolved_profile_ref": governed.resolved_profile.profile_id,
        "resolved_profile_fingerprint": governed.resolved_profile.profile_fingerprint,
        "generation_provenance_ref": provenance.generation_provenance_id,
        "generation_provenance_fingerprint": provenance.provenance_fingerprint,
    }
    hypothesis_data["governed_hypothesis_fingerprint"] = governed_hypothesis_semantic_fingerprint(
        hypothesis_data
    )
    hypothesis = GovernedHypothesis(**hypothesis_data)
    judgments = governed.requirement_judgments
    missing_internal = tuple(
        sorted(
            item.requirement_ref
            for item in judgments
            if item.dependency_classification is not None
            and item.dependency_classification.value == "INTERNAL"
            and item.outcome.value
            in {"FAILED", "MISSING", "UNRESOLVED", "PRESENT_BUT_INADMISSIBLE"}
        )
    )
    unmet_external = tuple(
        sorted(
            item.requirement_ref
            for item in judgments
            if item.dependency_classification is not None
            and item.dependency_classification.value == "EXTERNAL"
            and item.outcome.value
            in {
                "FAILED",
                "MISSING",
                "UNRESOLVED",
                "EXTERNAL_UNMET",
                "PRESENT_BUT_INADMISSIBLE",
            }
        )
    )
    handoff_data = {
        "handoff_id": f"handoff-{name}",
        "handoff_schema_version": "1.0.0",
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "pretest_evaluation_ref": governed.evaluation.evaluation_id,
        "pretest_evaluation_fingerprint": governed.evaluation.evaluation_fingerprint,
        "family_id": proposition.family_id,
        "family_version": proposition.family_version,
        "family_fingerprint": proposition.family_fingerprint,
        "resolved_profile_ref": governed.resolved_profile.profile_id,
        "resolved_profile_version": governed.resolved_profile.profile_version,
        "resolved_profile_fingerprint": governed.resolved_profile.profile_fingerprint,
        "scope_ref": proposition.scope_ref,
        "baseline_period_ref": proposition.baseline_period_ref,
        "comparison_period_ref": proposition.comparison_period_ref,
        "population_refs": (
            proposition.baseline_population_ref,
            proposition.comparison_population_ref,
        ),
        "metric_refs": proposition.metric_refs,
        "variable_refs": proposition.variable_refs,
        "source_observation_refs": proposition.source_observation_refs,
        "source_mechanical_result_refs": proposition.source_mechanical_result_refs,
        "requirement_judgment_refs": tuple(item.judgment_id for item in judgments),
        "evidence_readiness": governed.evaluation.evidence_readiness,
        "missing_internal_requirement_refs": missing_internal,
        "unmet_external_requirement_refs": unmet_external,
        "method_ref": None,
        "method_version": None,
        "support_criterion_ref": None,
        "support_criterion_version": None,
        "validation_profile_ref": None,
        "validation_profile_version": None,
        "test_eligibility": governed.evaluation.test_eligibility,
        "first_controlling_blocker": governed.evaluation.first_controlling_blocker,
        "governed_hypothesis_ref": hypothesis.governed_hypothesis_id,
        "governed_hypothesis_fingerprint": hypothesis.governed_hypothesis_fingerprint,
        "generation_provenance_ref": provenance.generation_provenance_id,
    }
    handoff_data["handoff_fingerprint"] = r6_to_r7_handoff_semantic_fingerprint(handoff_data)
    handoff = R6ToR7Handoff(**handoff_data)
    repo = R6Repository(
        ArtifactStore(tmp_path / "artifacts"),
        MetadataStore(tmp_path / "metadata.sqlite"),
    )
    repo.persist_diagnostic_proposition(proposition)
    repo.persist_resolved_required_evidence_profile(governed.resolved_profile)
    repo.persist_requirement_judgment_bundle(
        governed.requirement_judgment_bundle_ref,
        governed.requirement_judgment_bundle_fingerprint,
        judgments,
    )
    repo.persist_pretest_diagnostic_evaluation(governed.evaluation)
    repo.persist_generation_provenance(provenance)
    repo.persist_governed_hypothesis(hypothesis)
    repo.persist_r6_to_r7_handoff(handoff)
    return Graph(
        repo,
        registry,
        proposition,
        governed.resolved_profile,
        judgments,
        governed.evaluation,
        provenance,
        hypothesis,
        handoff,
    )


def _index(graph: Graph, artifact_type: R6ArtifactType, artifact_id: str):
    record = graph.repo.metadata_store.get_r6_artifact_index(artifact_type.value, artifact_id)
    assert record is not None
    reference = graph.repo.metadata_store.get_artifact_reference(record.artifact_reference_id)
    assert reference is not None
    return record, reference, graph.repo.artifact_store.safe_path(reference.path)


def _rewrite_bytes(graph: Graph, artifact_type: R6ArtifactType, artifact_id: str, raw: bytes) -> None:
    _, reference, path = _index(graph, artifact_type, artifact_id)
    path.write_bytes(raw)
    updated = reference.model_copy(update={"fingerprint": sha256_bytes(raw), "size_bytes": len(raw)})
    with sqlite3.connect(graph.repo.metadata_store.db_path) as conn:
        conn.execute(
            """
            UPDATE artifact_references
            SET fingerprint = ?, size_bytes = ?, record_json = ?
            WHERE artifact_id = ?
            """,
            (
                updated.fingerprint,
                updated.size_bytes,
                updated.model_dump_json(),
                reference.artifact_id,
            ),
        )


def _rewrite_payload(
    graph: Graph,
    artifact_type: R6ArtifactType,
    artifact_id: str,
    mutate,
    *,
    index_fingerprint: str | None = None,
) -> dict:
    index, _, path = _index(graph, artifact_type, artifact_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload)
    raw = canonical_json_bytes(graph.repo._normalize_payload(artifact_type, payload))
    _rewrite_bytes(graph, artifact_type, artifact_id, raw)
    if index_fingerprint is not None:
        changed = index.model_copy(update={"semantic_fingerprint": index_fingerprint})
        with sqlite3.connect(graph.repo.metadata_store.db_path) as conn:
            conn.execute(
                """
                UPDATE r6_artifact_index
                SET semantic_fingerprint = ?, record_json = ?
                WHERE artifact_type = ? AND artifact_id = ?
                """,
                (
                    index_fingerprint,
                    changed.model_dump_json(),
                    artifact_type.value,
                    artifact_id,
                ),
            )
    return payload


def test_complete_graph_round_trip_duplicate_and_repository_reinstantiation(tmp_path) -> None:
    graph = _build_graph(tmp_path)
    first = graph.repo.persist_r6_to_r7_handoff(graph.handoff)
    second = graph.repo.persist_r6_to_r7_handoff(graph.handoff)
    assert first == second
    reopened = R6Repository(
        ArtifactStore(tmp_path / "artifacts"),
        MetadataStore(tmp_path / "metadata.sqlite"),
    )
    restored = reopened.load_r6_to_r7_handoff(
        graph.handoff.handoff_id,
        authority_registry=graph.registry,
    )
    assert restored.handoff_id == graph.handoff.handoff_id
    assert restored.handoff_fingerprint == graph.handoff.handoff_fingerprint
    assert len(reopened.metadata_store.list_r6_artifact_indexes()) == 7


def test_missing_artifact_and_wrong_type_are_distinct(tmp_path) -> None:
    graph = _build_graph(tmp_path)
    with pytest.raises(R6ArtifactIntegrityError) as missing:
        graph.repo.load_generation_provenance("missing")
    assert missing.value.code == "artifact_missing"

    provenance = graph.provenance.model_copy(update={"generation_provenance_id": "cross-type-id"})
    graph.repo.persist_generation_provenance(provenance)
    with pytest.raises(R6ArtifactIntegrityError) as wrong:
        graph.repo.load_diagnostic_proposition(
            "cross-type-id",
            authority_registry=graph.registry,
        )
    assert wrong.value.code == "wrong_artifact_type"


def test_tampered_bytes_fail_before_schema_or_semantics(tmp_path) -> None:
    graph = _build_graph(tmp_path)
    _, _, path = _index(
        graph, R6ArtifactType.DIAGNOSTIC_PROPOSITION, graph.proposition.proposition_id
    )
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(R6ArtifactIntegrityError) as error:
        graph.repo.load_diagnostic_proposition(
            graph.proposition.proposition_id,
            authority_registry=graph.registry,
        )
    assert error.value.code == "size_mismatch"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("semantic_fingerprint", "f" * 64, "semantic_fingerprint_mismatch"),
        ("proposition_id", "different-id", "artifact_id_mismatch"),
    ],
)
def test_body_identity_and_semantic_fingerprint_tamper_fail_closed(
    tmp_path, field, value, code
) -> None:
    graph = _build_graph(tmp_path)
    _rewrite_payload(
        graph,
        R6ArtifactType.DIAGNOSTIC_PROPOSITION,
        graph.proposition.proposition_id,
        lambda payload: payload.__setitem__(field, value),
    )
    with pytest.raises(R6ArtifactIntegrityError) as error:
        graph.repo.load_diagnostic_proposition(
            graph.proposition.proposition_id,
            authority_registry=graph.registry,
        )
    assert error.value.code == code


def test_stale_authority_and_equal_looking_subject_substitution_fail(tmp_path) -> None:
    graph = _build_graph(tmp_path)
    records = list(graph.registry.authorities)
    intended_index = next(
        index
        for index, record in enumerate(records)
        if record.authority_class is AuthorityClass.INTENDED_USE
    )
    intended = records[intended_index]
    records[intended_index] = intended.model_copy(
        update={
            "binding": intended.binding.model_copy(update={"authority_version": "0.9.0"})
        }
    )
    stale = _registry_from_records(tuple(records))
    with pytest.raises(R6ArtifactIntegrityError) as stale_error:
        graph.repo.load_diagnostic_proposition(
            graph.proposition.proposition_id,
            authority_registry=stale,
        )
    assert stale_error.value.code == "authority_stale"

    records[intended_index] = intended.model_copy(update={"subject_refs": ("other-proposition",)})
    substitute = _registry_from_records(tuple(records))
    with pytest.raises(R6ArtifactIntegrityError) as substitution:
        graph.repo.load_diagnostic_proposition(
            graph.proposition.proposition_id,
            authority_registry=substitute,
        )
    assert substitution.value.code == "authority_mismatch"


@pytest.mark.parametrize(
    "field",
    ["diagnostic_proposition_ref", "resolved_profile_ref", "pretest_evaluation_ref"],
)
def test_wrong_referenced_proposition_profile_or_evaluation_is_rejected(tmp_path, field) -> None:
    graph = _build_graph(tmp_path)
    payload = _rewrite_payload(
        graph,
        R6ArtifactType.GOVERNED_HYPOTHESIS,
        graph.hypothesis.governed_hypothesis_id,
        lambda body: body.__setitem__(field, f"missing-{field}"),
    )
    payload["governed_hypothesis_fingerprint"] = governed_hypothesis_semantic_fingerprint(payload)
    _rewrite_bytes(
        graph,
        R6ArtifactType.GOVERNED_HYPOTHESIS,
        graph.hypothesis.governed_hypothesis_id,
        canonical_json_bytes(graph.repo._normalize_payload(R6ArtifactType.GOVERNED_HYPOTHESIS, payload)),
    )
    index, _, _ = _index(
        graph, R6ArtifactType.GOVERNED_HYPOTHESIS, graph.hypothesis.governed_hypothesis_id
    )
    changed = index.model_copy(
        update={"semantic_fingerprint": payload["governed_hypothesis_fingerprint"]}
    )
    with sqlite3.connect(graph.repo.metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE r6_artifact_index SET semantic_fingerprint = ?, record_json = ? "
            "WHERE artifact_type = ? AND artifact_id = ?",
            (
                changed.semantic_fingerprint,
                changed.model_dump_json(),
                R6ArtifactType.GOVERNED_HYPOTHESIS.value,
                graph.hypothesis.governed_hypothesis_id,
            ),
        )
    with pytest.raises(R6ArtifactIntegrityError) as error:
        graph.repo.load_governed_hypothesis(
            graph.hypothesis.governed_hypothesis_id,
            authority_registry=graph.registry,
        )
    assert error.value.code in {"artifact_missing", "wrong_artifact_type"}


def test_swapped_valid_reference_with_unswapped_fingerprint_is_rejected(tmp_path) -> None:
    graph = _build_graph(tmp_path)
    other_data = graph.provenance.model_dump(mode="python")
    other_data["generation_provenance_id"] = "genprov-other"
    other_data["generator_version"] = "1.0.1"
    other_data["provenance_fingerprint"] = generation_provenance_semantic_fingerprint(other_data)
    other = GenerationProvenance(**other_data)
    graph.repo.persist_generation_provenance(other)
    payload = _rewrite_payload(
        graph,
        R6ArtifactType.GOVERNED_HYPOTHESIS,
        graph.hypothesis.governed_hypothesis_id,
        lambda body: body.__setitem__("generation_provenance_ref", other.generation_provenance_id),
    )
    payload["governed_hypothesis_fingerprint"] = governed_hypothesis_semantic_fingerprint(payload)
    _rewrite_bytes(
        graph,
        R6ArtifactType.GOVERNED_HYPOTHESIS,
        graph.hypothesis.governed_hypothesis_id,
        canonical_json_bytes(payload),
    )
    index, _, _ = _index(
        graph, R6ArtifactType.GOVERNED_HYPOTHESIS, graph.hypothesis.governed_hypothesis_id
    )
    changed = index.model_copy(
        update={"semantic_fingerprint": payload["governed_hypothesis_fingerprint"]}
    )
    with sqlite3.connect(graph.repo.metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE r6_artifact_index SET semantic_fingerprint = ?, record_json = ? "
            "WHERE artifact_type = ? AND artifact_id = ?",
            (
                changed.semantic_fingerprint,
                changed.model_dump_json(),
                R6ArtifactType.GOVERNED_HYPOTHESIS.value,
                graph.hypothesis.governed_hypothesis_id,
            ),
        )
    with pytest.raises(R6ArtifactIntegrityError) as error:
        graph.repo.load_governed_hypothesis(
            graph.hypothesis.governed_hypothesis_id,
            authority_registry=graph.registry,
        )
    assert error.value.code == "lineage_mismatch"


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        (b"{", "malformed_json"),
        (b'{"x":1,"x":2}', "duplicate_json_key"),
    ],
)
def test_malformed_and_duplicate_key_json_are_rejected(tmp_path, raw, code) -> None:
    graph = _build_graph(tmp_path)
    _rewrite_bytes(
        graph,
        R6ArtifactType.GENERATION_PROVENANCE,
        graph.provenance.generation_provenance_id,
        raw,
    )
    with pytest.raises(R6ArtifactIntegrityError) as error:
        graph.repo.load_generation_provenance(graph.provenance.generation_provenance_id)
    assert error.value.code == code


@pytest.mark.parametrize("mutation", ["extra", "missing", "evidence", "copied_body"])
def test_strict_schema_rejects_unknown_missing_and_authority_copy_fields(tmp_path, mutation) -> None:
    graph = _build_graph(tmp_path)
    if mutation in {"extra", "missing", "evidence"}:
        artifact_type = R6ArtifactType.GENERATION_PROVENANCE
        artifact_id = graph.provenance.generation_provenance_id
        loader = lambda: graph.repo.load_generation_provenance(artifact_id)
    else:
        artifact_type = R6ArtifactType.GOVERNED_HYPOTHESIS
        artifact_id = graph.hypothesis.governed_hypothesis_id
        loader = lambda: graph.repo.load_governed_hypothesis(
            artifact_id, authority_registry=graph.registry
        )

    def mutate(payload):
        if mutation == "missing":
            payload.pop("generator_id")
        elif mutation == "evidence":
            payload["evidence_refs"] = ["evidence:fake"]
        elif mutation == "copied_body":
            payload["proposition_body"] = graph.proposition.model_dump(mode="json")
        else:
            payload["unknown"] = True

    _rewrite_payload(graph, artifact_type, artifact_id, mutate)
    with pytest.raises(R6ArtifactIntegrityError) as error:
        loader()
    assert error.value.code == "schema_invalid"


def test_noncanonical_json_rejected_even_when_external_hash_is_recomputed(tmp_path) -> None:
    graph = _build_graph(tmp_path)
    _, _, path = _index(
        graph, R6ArtifactType.GENERATION_PROVENANCE, graph.provenance.generation_provenance_id
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = json.dumps(payload, indent=2, sort_keys=False).encode("utf-8")
    _rewrite_bytes(
        graph,
        R6ArtifactType.GENERATION_PROVENANCE,
        graph.provenance.generation_provenance_id,
        raw,
    )
    with pytest.raises(R6ArtifactIntegrityError) as error:
        graph.repo.load_generation_provenance(graph.provenance.generation_provenance_id)
    assert error.value.code == "noncanonical_json"


def test_unordered_contract_fields_serialize_identically_and_material_change_does_not(tmp_path) -> None:
    first = _proposition(
        variable_refs=("field:product_id", "field:line_revenue"),
        prohibited_meanings=("causality", "support", "explanation"),
    )
    reordered = _proposition(
        variable_refs=("field:line_revenue", "field:product_id"),
        prohibited_meanings=("explanation", "causality", "support"),
    )
    changed = _proposition(scope_ref="scope:different")
    assert first.proposition_id == reordered.proposition_id
    assert first.semantic_fingerprint == reordered.semantic_fingerprint
    assert changed.proposition_id != first.proposition_id
    repo = R6Repository(ArtifactStore(tmp_path / "artifacts"), MetadataStore(tmp_path / "db.sqlite"))
    one = repo.persist_diagnostic_proposition(first)
    two = repo.persist_diagnostic_proposition(reordered)
    assert one == two


def test_conflicting_duplicate_fails_and_original_bytes_remain(tmp_path) -> None:
    graph = _build_graph(tmp_path)
    _, _, path = _index(
        graph, R6ArtifactType.DIAGNOSTIC_PROPOSITION, graph.proposition.proposition_id
    )
    original = path.read_bytes()
    conflict = graph.proposition.model_copy(update={"display_wording": "different nonsemantic bytes"})
    with pytest.raises(R6ArtifactIntegrityError) as error:
        graph.repo.persist_diagnostic_proposition(conflict)
    assert error.value.code == "overwrite_conflict"
    assert path.read_bytes() == original


def test_partial_write_failure_never_creates_valid_index(tmp_path, monkeypatch) -> None:
    repo = R6Repository(ArtifactStore(tmp_path / "artifacts"), MetadataStore(tmp_path / "db.sqlite"))
    proposition = _proposition()

    def fail_before_publish(destination, content):
        raise OSError("simulated interrupted write")

    monkeypatch.setattr(repo.artifact_store, "_atomic_create_bytes", fail_before_publish)
    with pytest.raises(R6ArtifactIntegrityError) as error:
        repo.persist_diagnostic_proposition(proposition)
    assert error.value.code == "artifact_write_failed"
    assert repo.metadata_store.get_r6_artifact_index(
        R6ArtifactType.DIAGNOSTIC_PROPOSITION.value,
        proposition.proposition_id,
    ) is None


def test_tampered_index_and_missing_generic_reference_fail_closed(tmp_path) -> None:
    graph = _build_graph(tmp_path)
    artifact_type = R6ArtifactType.GENERATION_PROVENANCE
    artifact_id = graph.provenance.generation_provenance_id
    index, reference, _ = _index(graph, artifact_type, artifact_id)
    changed = index.model_copy(update={"semantic_fingerprint": "f" * 64})
    with sqlite3.connect(graph.repo.metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE r6_artifact_index SET semantic_fingerprint = ?, record_json = ? "
            "WHERE artifact_type = ? AND artifact_id = ?",
            ("f" * 64, changed.model_dump_json(), artifact_type.value, artifact_id),
        )
    with pytest.raises(R6ArtifactIntegrityError) as tampered:
        graph.repo.load_generation_provenance(artifact_id)
    assert tampered.value.code == "semantic_fingerprint_mismatch"

    with sqlite3.connect(graph.repo.metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE r6_artifact_index SET semantic_fingerprint = ?, record_json = ? "
            "WHERE artifact_type = ? AND artifact_id = ?",
            (
                index.semantic_fingerprint,
                index.model_dump_json(),
                artifact_type.value,
                artifact_id,
            ),
        )
        conn.execute("DELETE FROM artifact_references WHERE artifact_id = ?", (reference.artifact_id,))
    with pytest.raises(R6ArtifactIntegrityError) as missing:
        graph.repo.load_generation_provenance(artifact_id)
    assert missing.value.code == "artifact_reference_missing"


def test_handoff_readiness_cannot_contradict_persisted_evaluation(tmp_path) -> None:
    graph = _build_graph(tmp_path)
    payload = _rewrite_payload(
        graph,
        R6ArtifactType.R6_TO_R7_HANDOFF,
        graph.handoff.handoff_id,
        lambda body: body.__setitem__(
            "evidence_readiness", EvidenceReadiness.MISSING_INTERNAL_EVIDENCE.value
        ),
    )
    payload["handoff_fingerprint"] = r6_to_r7_handoff_semantic_fingerprint(payload)
    _rewrite_bytes(
        graph,
        R6ArtifactType.R6_TO_R7_HANDOFF,
        graph.handoff.handoff_id,
        canonical_json_bytes(graph.repo._normalize_payload(R6ArtifactType.R6_TO_R7_HANDOFF, payload)),
    )
    index, _, _ = _index(graph, R6ArtifactType.R6_TO_R7_HANDOFF, graph.handoff.handoff_id)
    changed = index.model_copy(update={"semantic_fingerprint": payload["handoff_fingerprint"]})
    with sqlite3.connect(graph.repo.metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE r6_artifact_index SET semantic_fingerprint = ?, record_json = ? "
            "WHERE artifact_type = ? AND artifact_id = ?",
            (
                changed.semantic_fingerprint,
                changed.model_dump_json(),
                R6ArtifactType.R6_TO_R7_HANDOFF.value,
                graph.handoff.handoff_id,
            ),
        )
    with pytest.raises(R6ArtifactIntegrityError) as error:
        graph.repo.load_r6_to_r7_handoff(
            graph.handoff.handoff_id,
            authority_registry=graph.registry,
        )
    assert error.value.code == "lineage_mismatch"


def test_persistence_failure_is_not_analytical_missing_evidence(tmp_path) -> None:
    graph = _build_graph(tmp_path)
    with pytest.raises(R6ArtifactIntegrityError) as error:
        graph.repo.load_generation_provenance("absent")
    assert error.value.code == "artifact_missing"
    assert error.value.code not in {"MISSING_EVIDENCE", "EXTERNAL_EVIDENCE_REQUIRED"}


def test_concurrent_conflicting_write_cannot_replace_winner(tmp_path, monkeypatch) -> None:
    repo = R6Repository(ArtifactStore(tmp_path / "artifacts"), MetadataStore(tmp_path / "db.sqlite"))
    first = _proposition(display_wording="writer one")
    second = _proposition(display_wording="writer two")
    assert first.proposition_id == second.proposition_id
    barrier = threading.Barrier(2)
    real_link = artifact_store_module.os.link

    def racing_link(source, destination):
        barrier.wait(timeout=5)
        return real_link(source, destination)

    monkeypatch.setattr(artifact_store_module.os, "link", racing_link)

    def persist(item):
        try:
            return repo.persist_diagnostic_proposition(item)
        except R6ArtifactIntegrityError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(persist, (first, second)))
    successes = [item for item in outcomes if not isinstance(item, Exception)]
    failures = [item for item in outcomes if isinstance(item, R6ArtifactIntegrityError)]
    assert len(successes) == 1
    assert len(failures) == 1
    assert failures[0].code == "overwrite_conflict"
    index = repo.metadata_store.get_r6_artifact_index(
        R6ArtifactType.DIAGNOSTIC_PROPOSITION.value,
        first.proposition_id,
    )
    assert index is not None
    reference = repo.metadata_store.get_artifact_reference(index.artifact_reference_id)
    assert reference is not None
    stored = repo.artifact_store.safe_path(reference.path).read_bytes()
    possible = {
        canonical_json_bytes(repo._normalize_payload(
            R6ArtifactType.DIAGNOSTIC_PROPOSITION, item.model_dump(mode="json")
        ))
        for item in (first, second)
    }
    assert stored in possible
