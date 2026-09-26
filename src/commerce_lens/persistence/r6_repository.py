"""Immutable artifact-first persistence and verification for approved R6 artifacts."""

from __future__ import annotations

import json
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, TypeVar

from pydantic import Field, ValidationError

from commerce_lens.contracts.common import ArtifactReference, ContractBase
from commerce_lens.contracts.diagnostic import (
    AuthorityBinding,
    DiagnosticProposition,
    PreTestDiagnosticEvaluation,
    diagnostic_proposition_semantic_fingerprint,
    pretest_evaluation_semantic_fingerprint,
)
from commerce_lens.contracts.hypotheses import (
    GenerationProvenance,
    GovernedHypothesis,
    R6ToR7Handoff,
    generation_provenance_semantic_fingerprint,
    governed_hypothesis_semantic_fingerprint,
    r6_to_r7_handoff_semantic_fingerprint,
)
from commerce_lens.contracts.required_evidence import (
    ApplicabilityState,
    DependencyClassification,
    RequirementJudgment,
    RequirementOutcome,
    ResolvedRequiredEvidenceProfile,
    resolved_profile_semantic_fingerprint,
    validate_profile_against_template,
)
from commerce_lens.diagnostic.family_registry import MVP_FAMILY_REGISTRY
from commerce_lens.diagnostic.governance import (
    EVALUATION_SCHEMA_VERSION,
    GOVERNANCE_VERSION,
    AuthorityClass,
    PreTestAuthorityRegistry,
    pretest_authority_registry_fingerprint,
    requirement_judgment_bundle_fingerprint,
)
from commerce_lens.evidence.identifiers import (
    canonical_json_bytes,
    canonical_json_fingerprint,
    sha256_bytes,
    sha256_file,
    stable_content_id,
)
from commerce_lens.metrics.registry import get_metric_registry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import (
    MetadataStore,
    R6ArtifactIndexRecord,
)


class R6ArtifactType(str, Enum):
    DIAGNOSTIC_PROPOSITION = "diagnostic_proposition"
    RESOLVED_REQUIRED_EVIDENCE_PROFILE = "resolved_required_evidence_profile"
    REQUIREMENT_JUDGMENT_BUNDLE = "requirement_judgment_bundle"
    PRETEST_DIAGNOSTIC_EVALUATION = "pretest_diagnostic_evaluation"
    GENERATION_PROVENANCE = "generation_provenance"
    GOVERNED_HYPOTHESIS = "governed_hypothesis"
    R6_TO_R7_HANDOFF = "r6_to_r7_handoff"


class R6ArtifactIntegrityError(RuntimeError):
    """Deterministic persistence/authentication failure, never evidence state."""

    def __init__(self, code: str, artifact_id: str, message: str) -> None:
        super().__init__(f"{code}: {message} [{artifact_id}]")
        self.code = code
        self.artifact_id = artifact_id


class _RequirementJudgmentBundleEnvelope(ContractBase):
    """Repository serialization envelope; it creates no analytical authority."""

    bundle_ref: str = Field(min_length=1)
    bundle_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    judgments: tuple[RequirementJudgment, ...] = Field(min_length=1)


ModelT = TypeVar("ModelT", bound=ContractBase)


class R6Repository:
    """Persist and authenticate the fixed R6-3 artifact set."""

    def __init__(self, artifact_store: ArtifactStore, metadata_store: MetadataStore) -> None:
        self.artifact_store = artifact_store
        self.metadata_store = metadata_store
        self.metadata_store.initialize()

    def persist_diagnostic_proposition(self, artifact: DiagnosticProposition) -> ArtifactReference:
        return self._persist_model(
            R6ArtifactType.DIAGNOSTIC_PROPOSITION,
            artifact.proposition_id,
            artifact.semantic_fingerprint,
            artifact,
        )

    def persist_resolved_required_evidence_profile(
        self, artifact: ResolvedRequiredEvidenceProfile
    ) -> ArtifactReference:
        return self._persist_model(
            R6ArtifactType.RESOLVED_REQUIRED_EVIDENCE_PROFILE,
            artifact.profile_id,
            artifact.profile_fingerprint,
            artifact,
        )

    def persist_requirement_judgment_bundle(
        self,
        bundle_ref: str,
        bundle_fingerprint: str,
        judgments: tuple[RequirementJudgment, ...],
    ) -> ArtifactReference:
        envelope = _RequirementJudgmentBundleEnvelope(
            bundle_ref=bundle_ref,
            bundle_fingerprint=bundle_fingerprint,
            judgments=judgments,
        )
        if requirement_judgment_bundle_fingerprint(judgments) != bundle_fingerprint:
            self._fail("semantic_fingerprint_mismatch", bundle_ref, "judgment bundle fingerprint is invalid")
        return self._persist_model(
            R6ArtifactType.REQUIREMENT_JUDGMENT_BUNDLE,
            bundle_ref,
            bundle_fingerprint,
            envelope,
        )

    def persist_pretest_diagnostic_evaluation(
        self, artifact: PreTestDiagnosticEvaluation
    ) -> ArtifactReference:
        return self._persist_model(
            R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION,
            artifact.evaluation_id,
            artifact.evaluation_fingerprint,
            artifact,
        )

    def persist_generation_provenance(self, artifact: GenerationProvenance) -> ArtifactReference:
        return self._persist_model(
            R6ArtifactType.GENERATION_PROVENANCE,
            artifact.generation_provenance_id,
            artifact.provenance_fingerprint,
            artifact,
        )

    def persist_governed_hypothesis(self, artifact: GovernedHypothesis) -> ArtifactReference:
        return self._persist_model(
            R6ArtifactType.GOVERNED_HYPOTHESIS,
            artifact.governed_hypothesis_id,
            artifact.governed_hypothesis_fingerprint,
            artifact,
        )

    def persist_r6_to_r7_handoff(self, artifact: R6ToR7Handoff) -> ArtifactReference:
        return self._persist_model(
            R6ArtifactType.R6_TO_R7_HANDOFF,
            artifact.handoff_id,
            artifact.handoff_fingerprint,
            artifact,
        )

    def load_diagnostic_proposition(
        self,
        artifact_id: str,
        *,
        authority_registry: PreTestAuthorityRegistry,
    ) -> DiagnosticProposition:
        proposition = self._load_model(
            R6ArtifactType.DIAGNOSTIC_PROPOSITION,
            artifact_id,
            DiagnosticProposition,
        )
        self._authenticate_proposition(proposition, authority_registry)
        return proposition

    def load_resolved_required_evidence_profile(
        self,
        artifact_id: str,
        *,
        authority_registry: PreTestAuthorityRegistry,
    ) -> ResolvedRequiredEvidenceProfile:
        profile = self._load_model(
            R6ArtifactType.RESOLVED_REQUIRED_EVIDENCE_PROFILE,
            artifact_id,
            ResolvedRequiredEvidenceProfile,
        )
        proposition = self.load_diagnostic_proposition(
            profile.diagnostic_proposition_ref,
            authority_registry=authority_registry,
        )
        self._verify_profile(profile, proposition, authority_registry)
        return profile

    def load_requirement_judgment_bundle(
        self,
        bundle_ref: str,
        *,
        profile: ResolvedRequiredEvidenceProfile,
    ) -> tuple[RequirementJudgment, ...]:
        envelope = self._load_model(
            R6ArtifactType.REQUIREMENT_JUDGMENT_BUNDLE,
            bundle_ref,
            _RequirementJudgmentBundleEnvelope,
        )
        self._verify_judgment_bundle(envelope, profile)
        return envelope.judgments

    def load_pretest_diagnostic_evaluation(
        self,
        artifact_id: str,
        *,
        authority_registry: PreTestAuthorityRegistry,
    ) -> PreTestDiagnosticEvaluation:
        evaluation = self._load_model(
            R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION,
            artifact_id,
            PreTestDiagnosticEvaluation,
        )
        proposition = self.load_diagnostic_proposition(
            evaluation.diagnostic_proposition_ref,
            authority_registry=authority_registry,
        )
        profile = self.load_resolved_required_evidence_profile(
            evaluation.resolved_profile_ref,
            authority_registry=authority_registry,
        )
        judgments = self.load_requirement_judgment_bundle(
            evaluation.requirement_judgment_bundle_ref,
            profile=profile,
        )
        self._verify_evaluation(evaluation, proposition, profile, judgments)
        return evaluation

    def load_generation_provenance(self, artifact_id: str) -> GenerationProvenance:
        provenance = self._load_model(
            R6ArtifactType.GENERATION_PROVENANCE,
            artifact_id,
            GenerationProvenance,
        )
        if provenance.raw_candidate_artifact_ref is not None:
            reference = self.metadata_store.get_artifact_reference(provenance.raw_candidate_artifact_ref)
            if reference is None:
                self._fail(
                    "artifact_reference_missing",
                    artifact_id,
                    "raw candidate artifact reference is missing",
                )
            self._verify_generic_reference(reference, artifact_id)
        return provenance

    def load_governed_hypothesis(
        self,
        artifact_id: str,
        *,
        authority_registry: PreTestAuthorityRegistry,
    ) -> GovernedHypothesis:
        hypothesis = self._load_model(
            R6ArtifactType.GOVERNED_HYPOTHESIS,
            artifact_id,
            GovernedHypothesis,
        )
        proposition = self.load_diagnostic_proposition(
            hypothesis.diagnostic_proposition_ref,
            authority_registry=authority_registry,
        )
        profile = self.load_resolved_required_evidence_profile(
            hypothesis.resolved_profile_ref,
            authority_registry=authority_registry,
        )
        evaluation = self.load_pretest_diagnostic_evaluation(
            hypothesis.pretest_evaluation_ref,
            authority_registry=authority_registry,
        )
        provenance = self.load_generation_provenance(hypothesis.generation_provenance_ref)
        expected = {
            "diagnostic proposition": (
                hypothesis.diagnostic_proposition_fingerprint,
                proposition.semantic_fingerprint,
            ),
            "resolved profile": (hypothesis.resolved_profile_fingerprint, profile.profile_fingerprint),
            "pre-test evaluation": (
                hypothesis.pretest_evaluation_fingerprint,
                evaluation.evaluation_fingerprint,
            ),
            "generation provenance": (
                hypothesis.generation_provenance_fingerprint,
                provenance.provenance_fingerprint,
            ),
        }
        if any(actual != authoritative for actual, authoritative in expected.values()):
            self._fail("lineage_mismatch", artifact_id, "governed hypothesis fingerprint binding mismatch")
        if (
            profile.diagnostic_proposition_ref != proposition.proposition_id
            or evaluation.diagnostic_proposition_ref != proposition.proposition_id
            or evaluation.resolved_profile_ref != profile.profile_id
        ):
            self._fail("lineage_mismatch", artifact_id, "governed hypothesis combines different authority chains")
        return hypothesis

    def load_r6_to_r7_handoff(
        self,
        artifact_id: str,
        *,
        authority_registry: PreTestAuthorityRegistry,
    ) -> R6ToR7Handoff:
        handoff = self._load_model(
            R6ArtifactType.R6_TO_R7_HANDOFF,
            artifact_id,
            R6ToR7Handoff,
        )
        proposition = self.load_diagnostic_proposition(
            handoff.diagnostic_proposition_ref,
            authority_registry=authority_registry,
        )
        profile = self.load_resolved_required_evidence_profile(
            handoff.resolved_profile_ref,
            authority_registry=authority_registry,
        )
        evaluation = self.load_pretest_diagnostic_evaluation(
            handoff.pretest_evaluation_ref,
            authority_registry=authority_registry,
        )
        hypothesis = self.load_governed_hypothesis(
            handoff.governed_hypothesis_ref,
            authority_registry=authority_registry,
        )
        provenance = self.load_generation_provenance(handoff.generation_provenance_ref)
        judgments = self.load_requirement_judgment_bundle(
            evaluation.requirement_judgment_bundle_ref,
            profile=profile,
        )
        self._verify_handoff(
            handoff,
            proposition,
            profile,
            evaluation,
            judgments,
            hypothesis,
            provenance,
            authority_registry,
        )
        return handoff

    def _persist_model(
        self,
        artifact_type: R6ArtifactType,
        artifact_id: str,
        semantic_fingerprint: str,
        model: ContractBase,
    ) -> ArtifactReference:
        payload = self._normalize_payload(artifact_type, model.model_dump(mode="json"))
        content = canonical_json_bytes(payload)
        existing = self.metadata_store.get_r6_artifact_index(artifact_type.value, artifact_id)
        if existing is not None:
            reference = self.metadata_store.get_artifact_reference(existing.artifact_reference_id)
            if (
                existing.semantic_fingerprint != semantic_fingerprint
                or reference is None
                or reference.path != str(self._relative_path(artifact_type, artifact_id))
                or not self.artifact_store.safe_path(reference.path).is_file()
                or self.artifact_store.safe_path(reference.path).read_bytes() != content
            ):
                self._fail("overwrite_conflict", artifact_id, "immutable R6 identity already has different content")
            self._load_model(artifact_type, artifact_id, type(model))
            return reference

        relative_path = self._relative_path(artifact_type, artifact_id)
        try:
            reference = self.artifact_store.write_json_artifact(relative_path, payload)
        except ValueError as exc:
            self._fail("overwrite_conflict", artifact_id, str(exc), cause=exc)
        except OSError as exc:
            self._fail("artifact_write_failed", artifact_id, str(exc), cause=exc)
        if reference.fingerprint != sha256_bytes(content):
            self._fail("byte_hash_mismatch", artifact_id, "written artifact hash is not canonical byte hash")
        try:
            self.metadata_store.insert_artifact_reference(reference)
            self.metadata_store.insert_r6_artifact_index(
                R6ArtifactIndexRecord(
                    artifact_type=artifact_type.value,
                    artifact_id=artifact_id,
                    semantic_fingerprint=semantic_fingerprint,
                    artifact_reference_id=reference.artifact_id,
                )
            )
        except RuntimeError as exc:
            self._fail("index_conflict", artifact_id, str(exc), cause=exc)
        self._load_model(artifact_type, artifact_id, type(model))
        return reference

    def _load_model(
        self,
        artifact_type: R6ArtifactType | str,
        artifact_id: str,
        model_type: type[ModelT],
    ) -> ModelT:
        try:
            artifact_type = R6ArtifactType(artifact_type)
        except ValueError as exc:
            self._fail(
                "unsupported_artifact_type",
                artifact_id,
                f"unsupported R6 artifact type: {artifact_type}",
                cause=exc,
            )
        index = self.metadata_store.get_r6_artifact_index(artifact_type.value, artifact_id)
        if index is None:
            other_types = [
                item for item in self.metadata_store.list_r6_artifact_indexes()
                if item.artifact_id == artifact_id
            ]
            if other_types:
                self._fail("wrong_artifact_type", artifact_id, "artifact ID is indexed under a different R6 type")
            self._fail("artifact_missing", artifact_id, "R6 artifact index entry is missing")
        if index.artifact_type != artifact_type.value:
            self._fail("wrong_artifact_type", artifact_id, "indexed R6 artifact type does not match request")
        expected_path = str(self._relative_path(artifact_type, artifact_id))
        reference = self.metadata_store.get_artifact_reference(index.artifact_reference_id)
        if reference is None:
            self._fail("artifact_reference_missing", artifact_id, "generic artifact reference is missing")
        if reference.path != expected_path:
            self._fail("path_mismatch", artifact_id, "artifact reference path is not the deterministic R6 path")
        path = self.artifact_store.safe_path(reference.path)
        if not path.is_file():
            self._fail("artifact_missing", artifact_id, "indexed R6 artifact file is missing")
        raw = path.read_bytes()
        if reference.size_bytes is None or len(raw) != reference.size_bytes:
            self._fail("size_mismatch", artifact_id, "persisted byte size differs from artifact reference")
        if reference.fingerprint is None or sha256_bytes(raw) != reference.fingerprint:
            self._fail("byte_hash_mismatch", artifact_id, "persisted bytes differ from artifact reference")
        payload = self._parse_json(raw, artifact_id)
        normalized = self._normalize_payload(artifact_type, payload)
        if canonical_json_bytes(normalized) != raw:
            self._fail("noncanonical_json", artifact_id, "persisted JSON is not canonical")
        identity_field, fingerprint_field = self._identity_fields(artifact_type)
        if normalized.get(identity_field) != artifact_id:
            self._fail("artifact_id_mismatch", artifact_id, "body and requested identities differ")
        if normalized.get(fingerprint_field) != index.semantic_fingerprint:
            self._fail(
                "semantic_fingerprint_mismatch",
                artifact_id,
                "body and index semantic fingerprints differ",
            )
        try:
            model = model_type.model_validate(normalized)
        except ValidationError as exc:
            self._fail("schema_invalid", artifact_id, str(exc), cause=exc)
        body_id, body_fingerprint = self._identity_and_fingerprint(artifact_type, model)
        if body_id != artifact_id or index.artifact_id != artifact_id:
            self._fail("artifact_id_mismatch", artifact_id, "body, request, and index identities differ")
        if body_fingerprint != index.semantic_fingerprint:
            self._fail(
                "semantic_fingerprint_mismatch",
                artifact_id,
                "body and index semantic fingerprints differ",
            )
        self._verify_semantic_fingerprint(artifact_type, model, artifact_id, body_fingerprint)
        return model

    def _verify_semantic_fingerprint(
        self,
        artifact_type: R6ArtifactType,
        model: ContractBase,
        artifact_id: str,
        stored: str,
    ) -> None:
        calculators: dict[R6ArtifactType, Callable[[Any], str]] = {
            R6ArtifactType.DIAGNOSTIC_PROPOSITION: diagnostic_proposition_semantic_fingerprint,
            R6ArtifactType.RESOLVED_REQUIRED_EVIDENCE_PROFILE: resolved_profile_semantic_fingerprint,
            R6ArtifactType.REQUIREMENT_JUDGMENT_BUNDLE: lambda value: requirement_judgment_bundle_fingerprint(
                value.judgments
            ),
            R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION: pretest_evaluation_semantic_fingerprint,
            R6ArtifactType.GENERATION_PROVENANCE: generation_provenance_semantic_fingerprint,
            R6ArtifactType.GOVERNED_HYPOTHESIS: governed_hypothesis_semantic_fingerprint,
            R6ArtifactType.R6_TO_R7_HANDOFF: r6_to_r7_handoff_semantic_fingerprint,
        }
        if calculators[artifact_type](model) != stored:
            self._fail("semantic_fingerprint_mismatch", artifact_id, "approved semantic fingerprint is invalid")

    def _authenticate_proposition(
        self,
        proposition: DiagnosticProposition,
        registry: PreTestAuthorityRegistry,
    ) -> None:
        self._authenticate_registry(registry, proposition.proposition_id)
        try:
            family = MVP_FAMILY_REGISTRY.get_family(proposition.family_id, proposition.family_version)
        except ValueError as exc:
            self._fail("authority_stale", proposition.proposition_id, str(exc), cause=exc)
        if proposition.family_fingerprint != family.family_fingerprint:
            self._fail("authority_mismatch", proposition.proposition_id, "family fingerprint is not current")
        for binding in proposition.authority_bindings:
            try:
                registered = registry.authenticate_binding(AuthorityClass.INTENDED_USE, binding)
            except ValueError as exc:
                self._fail("authority_stale", proposition.proposition_id, str(exc), cause=exc)
            if proposition.intended_use not in registered.intended_uses:
                self._fail("authority_mismatch", proposition.proposition_id, "intended use is not authorized")
            if registered.subject_refs and proposition.proposition_id not in registered.subject_refs:
                self._fail("authority_mismatch", proposition.proposition_id, "authority subject substitution detected")
        context = {
            AuthorityClass.SCOPE: (proposition.scope_ref,),
            AuthorityClass.PERIOD: (proposition.baseline_period_ref, proposition.comparison_period_ref),
            AuthorityClass.POPULATION: (
                proposition.baseline_population_ref,
                proposition.comparison_population_ref,
            ),
            AuthorityClass.VARIABLE: proposition.variable_refs,
            AuthorityClass.SOURCE_REFERENCE: (
                *proposition.source_observation_refs,
                *proposition.source_mechanical_result_refs,
            ),
        }
        for authority_class, references in context.items():
            for reference in references:
                try:
                    registry.require_reference(authority_class, reference)
                except ValueError as exc:
                    self._fail("authority_mismatch", proposition.proposition_id, str(exc), cause=exc)
        metric_registry = get_metric_registry()
        for reference in proposition.metric_refs:
            if not reference.startswith("metric:") or "@" not in reference:
                self._fail("authority_mismatch", proposition.proposition_id, "invalid governed Metric reference")
            metric_id, version = reference.removeprefix("metric:").split("@", maxsplit=1)
            definition = metric_registry.get(metric_id)
            if definition is None:
                self._fail("authority_mismatch", proposition.proposition_id, "unknown governed Metric")
            if definition.definition_version != version:
                self._fail("authority_stale", proposition.proposition_id, "Metric version is not current")

    def _verify_profile(
        self,
        profile: ResolvedRequiredEvidenceProfile,
        proposition: DiagnosticProposition,
        registry: PreTestAuthorityRegistry,
    ) -> None:
        if (
            profile.diagnostic_proposition_ref != proposition.proposition_id
            or profile.diagnostic_proposition_fingerprint != proposition.semantic_fingerprint
        ):
            self._fail("lineage_mismatch", profile.profile_id, "profile does not bind the exact proposition")
        template = MVP_FAMILY_REGISTRY.get_requirement_template(proposition.family_id)
        try:
            validate_profile_against_template(profile, template)
        except ValueError as exc:
            self._fail("authority_mismatch", profile.profile_id, str(exc), cause=exc)
        for encoded in profile.method_requirement_refs:
            try:
                binding = AuthorityBinding.model_validate_json(encoded)
                registry.authenticate_binding(AuthorityClass.METHOD, binding)
            except (ValueError, ValidationError) as exc:
                self._fail("authority_stale", profile.profile_id, "method authority is not current", cause=exc)
        exact = {item.slot: item.bound_ref for item in profile.exact_slot_bindings}
        expected = {
            "outcome_ref": proposition.outcome_ref,
            "scope_ref": proposition.scope_ref,
            "baseline_period_ref": proposition.baseline_period_ref,
            "comparison_period_ref": proposition.comparison_period_ref,
            "baseline_population_ref": proposition.baseline_population_ref,
            "comparison_population_ref": proposition.comparison_population_ref,
            "source_observation_refs": "refs_sha256:"
            + canonical_json_fingerprint(sorted(proposition.source_observation_refs)),
        }
        if any(slot in exact and exact[slot] != value for slot, value in expected.items()):
            self._fail("lineage_mismatch", profile.profile_id, "exact slot binding contradicts proposition")

    def _verify_judgment_bundle(
        self,
        envelope: _RequirementJudgmentBundleEnvelope,
        profile: ResolvedRequiredEvidenceProfile,
    ) -> None:
        if requirement_judgment_bundle_fingerprint(envelope.judgments) != envelope.bundle_fingerprint:
            self._fail(
                "semantic_fingerprint_mismatch",
                envelope.bundle_ref,
                "judgment bundle fingerprint mismatch",
            )
        ids = [item.judgment_id for item in envelope.judgments]
        refs = [item.requirement_ref for item in envelope.judgments]
        if len(ids) != len(set(ids)) or len(refs) != len(set(refs)):
            self._fail("lineage_mismatch", envelope.bundle_ref, "judgment identities or requirements are duplicated")
        expected_requirements: dict[str, Any] = {}
        for decision in profile.dimension_applicability_decisions:
            reference = (
                f"{profile.template_id.removeprefix('r3-template:')}:{decision.dimension.value}"
                if decision.applicability is ApplicabilityState.NOT_APPLICABLE
                else decision.requirement_ref
            )
            if reference is not None:
                expected_requirements[reference] = decision.dimension
        expected_requirements.update(
            {item.requirement_ref: None for item in profile.dependency_classifications}
        )
        if set(refs) != set(expected_requirements):
            self._fail("lineage_mismatch", envelope.bundle_ref, "judgment requirement set mismatches profile")
        for judgment in envelope.judgments:
            if judgment.requirement_version != GOVERNANCE_VERSION or judgment.authority_version != GOVERNANCE_VERSION:
                self._fail("authority_stale", envelope.bundle_ref, "judgment authority version is not current")
            if judgment.dimension != expected_requirements[judgment.requirement_ref]:
                self._fail("lineage_mismatch", envelope.bundle_ref, "judgment dimension mismatches profile")
            if profile.template_id not in judgment.authority_refs:
                self._fail("authority_mismatch", envelope.bundle_ref, "judgment omits template authority")
            payload = {
                "requirement_ref": judgment.requirement_ref,
                "requirement_version": judgment.requirement_version,
                "outcome": judgment.outcome.value,
                "reason_code": judgment.reason_code,
                "evidence_refs": sorted(judgment.evidence_refs),
                "authority_refs": sorted(judgment.authority_refs),
                "dimension": judgment.dimension.value if judgment.dimension else None,
                "context": judgment.context,
                "dependency_classification": (
                    judgment.dependency_classification.value
                    if judgment.dependency_classification
                    else None
                ),
                "consequence": judgment.consequence.value,
                "authority_version": judgment.authority_version,
            }
            if judgment.judgment_id != stable_content_id("reqjud", canonical_json_fingerprint(payload)):
                self._fail("artifact_id_mismatch", envelope.bundle_ref, "judgment ID is not authentic")

    def _verify_evaluation(
        self,
        evaluation: PreTestDiagnosticEvaluation,
        proposition: DiagnosticProposition,
        profile: ResolvedRequiredEvidenceProfile,
        judgments: tuple[RequirementJudgment, ...],
    ) -> None:
        expected = (
            evaluation.diagnostic_proposition_ref == proposition.proposition_id
            and evaluation.diagnostic_proposition_fingerprint == proposition.semantic_fingerprint
            and evaluation.resolved_profile_ref == profile.profile_id
            and evaluation.resolved_profile_version == profile.profile_version
            and evaluation.resolved_profile_fingerprint == profile.profile_fingerprint
            and evaluation.requirement_judgment_bundle_fingerprint
            == requirement_judgment_bundle_fingerprint(judgments)
        )
        if not expected:
            self._fail("lineage_mismatch", evaluation.evaluation_id, "evaluation authority lineage mismatch")
        governance = AuthorityBinding(
            authority_ref="R6_2_DETERMINISTIC_PRETEST_GOVERNANCE",
            authority_version=GOVERNANCE_VERSION,
            authority_fingerprint=canonical_json_fingerprint(
                {"governance": "R6-2", "version": GOVERNANCE_VERSION}
            ),
        )
        required = {
            (
                proposition.proposition_id,
                proposition.proposition_schema_version,
                proposition.semantic_fingerprint,
            ),
            (profile.profile_id, profile.profile_version, profile.profile_fingerprint),
            (governance.authority_ref, governance.authority_version, governance.authority_fingerprint),
            *(
                (
                    binding.authority_ref,
                    binding.authority_version,
                    binding.authority_fingerprint,
                )
                for encoded in profile.method_requirement_refs
                for binding in (AuthorityBinding.model_validate_json(encoded),)
            ),
        }
        actual = {
            (item.authority_ref, item.authority_version, item.authority_fingerprint)
            for item in evaluation.authority_bindings
        }
        if actual != required or evaluation.evaluation_schema_version != EVALUATION_SCHEMA_VERSION:
            self._fail("authority_stale", evaluation.evaluation_id, "evaluation authority binding is not current")

    def _verify_handoff(
        self,
        handoff: R6ToR7Handoff,
        proposition: DiagnosticProposition,
        profile: ResolvedRequiredEvidenceProfile,
        evaluation: PreTestDiagnosticEvaluation,
        judgments: tuple[RequirementJudgment, ...],
        hypothesis: GovernedHypothesis,
        provenance: GenerationProvenance,
        registry: PreTestAuthorityRegistry,
    ) -> None:
        scalar_matches = (
            handoff.diagnostic_proposition_fingerprint == proposition.semantic_fingerprint,
            handoff.pretest_evaluation_fingerprint == evaluation.evaluation_fingerprint,
            handoff.family_id == proposition.family_id,
            handoff.family_version == proposition.family_version,
            handoff.family_fingerprint == proposition.family_fingerprint,
            handoff.resolved_profile_version == profile.profile_version,
            handoff.resolved_profile_fingerprint == profile.profile_fingerprint,
            handoff.scope_ref == proposition.scope_ref,
            handoff.baseline_period_ref == proposition.baseline_period_ref,
            handoff.comparison_period_ref == proposition.comparison_period_ref,
            handoff.evidence_readiness == evaluation.evidence_readiness,
            handoff.test_eligibility == evaluation.test_eligibility,
            handoff.first_controlling_blocker == evaluation.first_controlling_blocker,
            handoff.governed_hypothesis_fingerprint == hypothesis.governed_hypothesis_fingerprint,
            handoff.generation_provenance_ref == provenance.generation_provenance_id,
            hypothesis.generation_provenance_ref == provenance.generation_provenance_id,
        )
        set_matches = (
            set(handoff.population_refs)
            == {proposition.baseline_population_ref, proposition.comparison_population_ref},
            set(handoff.metric_refs) == set(proposition.metric_refs),
            set(handoff.variable_refs) == set(proposition.variable_refs),
            set(handoff.source_observation_refs) == set(proposition.source_observation_refs),
            set(handoff.source_mechanical_result_refs)
            == set(proposition.source_mechanical_result_refs),
            set(handoff.requirement_judgment_refs)
            == {judgment.judgment_id for judgment in judgments},
        )
        if not all((*scalar_matches, *set_matches)):
            self._fail("lineage_mismatch", handoff.handoff_id, "handoff projection contradicts R6 graph")
        blocking = {
            RequirementOutcome.FAILED,
            RequirementOutcome.MISSING,
            RequirementOutcome.UNRESOLVED,
            RequirementOutcome.EXTERNAL_UNMET,
            RequirementOutcome.PRESENT_BUT_INADMISSIBLE,
        }
        missing_internal = {
            item.requirement_ref
            for item in judgments
            if item.dependency_classification is DependencyClassification.INTERNAL
            and item.outcome in blocking
        }
        unmet_external = {
            item.requirement_ref
            for item in judgments
            if item.dependency_classification is DependencyClassification.EXTERNAL
            and item.outcome in blocking
        }
        if (
            set(handoff.missing_internal_requirement_refs) != missing_internal
            or set(handoff.unmet_external_requirement_refs) != unmet_external
        ):
            self._fail("lineage_mismatch", handoff.handoff_id, "handoff unmet requirements contradict judgments")
        method_bindings: dict[str, AuthorityBinding] = {}
        for encoded in profile.method_requirement_refs:
            binding = AuthorityBinding.model_validate_json(encoded)
            method_bindings[binding.authority_ref] = binding
        for reference, version in (
            (handoff.method_ref, handoff.method_version),
            (handoff.support_criterion_ref, handoff.support_criterion_version),
            (handoff.validation_profile_ref, handoff.validation_profile_version),
        ):
            if reference is None:
                continue
            binding = method_bindings.get(reference)
            if binding is None or binding.authority_version != version:
                self._fail("authority_mismatch", handoff.handoff_id, "handoff method authority is not profile-bound")
            try:
                registry.authenticate_binding(AuthorityClass.METHOD, binding)
            except ValueError as exc:
                self._fail("authority_stale", handoff.handoff_id, str(exc), cause=exc)

    def _authenticate_registry(self, registry: PreTestAuthorityRegistry, artifact_id: str) -> None:
        try:
            authenticated = PreTestAuthorityRegistry.model_validate(registry.model_dump(mode="python"))
        except ValidationError as exc:
            self._fail("authority_mismatch", artifact_id, "trusted authority registry is invalid", cause=exc)
        if (
            authenticated.registry_id != "commerce_lens_r6_pretest_authorities"
            or authenticated.registry_version != GOVERNANCE_VERSION
            or authenticated.registry_fingerprint != pretest_authority_registry_fingerprint(authenticated)
        ):
            self._fail("authority_stale", artifact_id, "trusted authority registry is not current")

    def _verify_generic_reference(self, reference: ArtifactReference, owner_id: str) -> None:
        path = self.artifact_store.safe_path(reference.path)
        if not path.is_file():
            self._fail("artifact_missing", owner_id, "referenced artifact file is missing")
        if reference.fingerprint is None or sha256_file(path) != reference.fingerprint:
            self._fail("byte_hash_mismatch", owner_id, "referenced artifact hash mismatch")
        if reference.size_bytes is None or path.stat().st_size != reference.size_bytes:
            self._fail("size_mismatch", owner_id, "referenced artifact size mismatch")

    @staticmethod
    def _identity_and_fingerprint(
        artifact_type: R6ArtifactType,
        model: ContractBase,
    ) -> tuple[str, str]:
        identity_field, fingerprint_field = R6Repository._identity_fields(artifact_type)
        return str(getattr(model, identity_field)), str(getattr(model, fingerprint_field))

    @staticmethod
    def _identity_fields(artifact_type: R6ArtifactType) -> tuple[str, str]:
        fields = {
            R6ArtifactType.DIAGNOSTIC_PROPOSITION: ("proposition_id", "semantic_fingerprint"),
            R6ArtifactType.RESOLVED_REQUIRED_EVIDENCE_PROFILE: ("profile_id", "profile_fingerprint"),
            R6ArtifactType.REQUIREMENT_JUDGMENT_BUNDLE: ("bundle_ref", "bundle_fingerprint"),
            R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION: ("evaluation_id", "evaluation_fingerprint"),
            R6ArtifactType.GENERATION_PROVENANCE: (
                "generation_provenance_id",
                "provenance_fingerprint",
            ),
            R6ArtifactType.GOVERNED_HYPOTHESIS: (
                "governed_hypothesis_id",
                "governed_hypothesis_fingerprint",
            ),
            R6ArtifactType.R6_TO_R7_HANDOFF: ("handoff_id", "handoff_fingerprint"),
        }
        return fields[artifact_type]

    @staticmethod
    def _normalize_payload(artifact_type: R6ArtifactType, payload: Mapping[str, Any]) -> dict[str, Any]:
        result = deepcopy(dict(payload))
        scalar_sets = {
            R6ArtifactType.DIAGNOSTIC_PROPOSITION: (
                "metric_refs",
                "variable_refs",
                "source_observation_refs",
                "source_mechanical_result_refs",
                "prohibited_meanings",
            ),
            R6ArtifactType.RESOLVED_REQUIRED_EVIDENCE_PROFILE: (
                "resolved_evidence_roles",
                "method_requirement_refs",
                "blocking_rules",
                "qualification_rules",
                "narrowing_rules",
            ),
            R6ArtifactType.R6_TO_R7_HANDOFF: (
                "population_refs",
                "metric_refs",
                "variable_refs",
                "source_observation_refs",
                "source_mechanical_result_refs",
                "requirement_judgment_refs",
                "missing_internal_requirement_refs",
                "unmet_external_requirement_refs",
            ),
        }
        for field in scalar_sets.get(artifact_type, ()):
            result[field] = sorted(result.get(field, ()))
        model_sets = {
            R6ArtifactType.DIAGNOSTIC_PROPOSITION: (("authority_bindings", "authority_ref"),),
            R6ArtifactType.RESOLVED_REQUIRED_EVIDENCE_PROFILE: (
                ("exact_slot_bindings", "slot"),
                ("dimension_applicability_decisions", "dimension"),
                ("dependency_classifications", "requirement_ref"),
                ("measurement_classifications", "requirement_ref"),
            ),
            R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION: (("authority_bindings", "authority_ref"),),
            R6ArtifactType.REQUIREMENT_JUDGMENT_BUNDLE: (("judgments", "requirement_ref"),),
        }
        for field, key in model_sets.get(artifact_type, ()):
            result[field] = sorted(result.get(field, ()), key=lambda item: item[key])
        return result

    @staticmethod
    def _parse_json(raw: bytes, artifact_id: str) -> dict[str, Any]:
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise R6ArtifactIntegrityError("malformed_json", artifact_id, "artifact is not strict UTF-8") from exc

        def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise R6ArtifactIntegrityError("duplicate_json_key", artifact_id, f"duplicate key: {key}")
                result[key] = value
            return result

        try:
            parsed = json.loads(text, object_pairs_hook=reject_duplicates)
        except R6ArtifactIntegrityError:
            raise
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise R6ArtifactIntegrityError("malformed_json", artifact_id, "artifact JSON is malformed") from exc
        if not isinstance(parsed, dict):
            raise R6ArtifactIntegrityError("schema_invalid", artifact_id, "artifact JSON root must be an object")
        return parsed

    @staticmethod
    def _relative_path(artifact_type: R6ArtifactType, artifact_id: str) -> Path:
        locator = sha256_bytes(f"{artifact_type.value}\0{artifact_id}".encode("utf-8"))
        return Path("r6") / "artifacts" / artifact_type.value / locator[:2] / f"{locator}.json"

    @staticmethod
    def _fail(
        code: str,
        artifact_id: str,
        message: str,
        *,
        cause: BaseException | None = None,
    ) -> None:
        error = R6ArtifactIntegrityError(code, artifact_id, message)
        if cause is not None:
            raise error from cause
        raise error


__all__ = ["R6ArtifactIntegrityError", "R6ArtifactType", "R6Repository"]
