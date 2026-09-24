"""Strict, non-executable contracts for future R5 physical fixtures."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from yaml.tokens import AliasToken, AnchorToken, TagToken

from commerce_lens.evidence.identifiers import sha256_file


R5_FAMILIES = (
    "EVID", "MEAS", "ADMIT", "R4", "DIAG", "ALT", "CLAIM",
    "CAUSE", "NARROW", "LANG", "VERSION", "PROV", "CHAIN", "PREC",
)
R5_ACTIVE_ID_PATTERN = re.compile(
    rf"^FX-R5-({'|'.join(R5_FAMILIES)})-[0-9]{{3}}[A-Z]$"
)
R5_DEFERRED_ID_PATTERN = re.compile(
    rf"^DF-R5-({'|'.join(R5_FAMILIES)})-[0-9]{{3}}$"
)
FROZEN_AUTHORITY_VERSIONS = MappingProxyType(
    {
        "PROJECT_MASTER_INSTRUCTIONS.md": "v1.1",
        "SKILL_SCOPE_SPECIFICATION.md": "v1.0",
        "EVIDENCE_CONTRACT_SPECIFICATION.md": "v1.0",
        "ARCHITECTURE_SPECIFICATION.md": "v1.0",
        "CANONICAL_DATASET_AND_METRIC_DICTIONARY.md": "v1.0",
        "EVALUATION_FIXTURES_SPECIFICATION.md": "v1.0",
        "DIAGNOSTIC_REASONING_SPECIFICATION.md": "R1 v1.0",
        "HYPOTHESIS_FINDING_STATE_MODEL_SPECIFICATION.md": "R2 v1.0",
        "REQUIRED_EVIDENCE_MATRIX_SPECIFICATION.md": "R3 v1.0",
        "DETERMINISTIC_REVENUE_DECOMPOSITION_SPECIFICATION.md": "R4 v1.0",
        "DIAGNOSTIC_SYNTHETIC_FIXTURE_SUITE_SPECIFICATION.md": "R5 v1.0",
    }
)
R5_AUTHORITY_DOCUMENTS = frozenset(FROZEN_AUTHORITY_VERSIONS)
MAX_YAML_BYTES = 1_000_000
MAX_YAML_DEPTH = 30
MAX_YAML_NODES = 5_000


class R5ManifestError(ValueError):
    """Raised when an R5 manifest or referenced input fails closed."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class R5Family(str, Enum):
    EVID = "EVID"
    MEAS = "MEAS"
    ADMIT = "ADMIT"
    R4 = "R4"
    DIAG = "DIAG"
    ALT = "ALT"
    CLAIM = "CLAIM"
    CAUSE = "CAUSE"
    NARROW = "NARROW"
    LANG = "LANG"
    VERSION = "VERSION"
    PROV = "PROV"
    CHAIN = "CHAIN"
    PREC = "PREC"


class R5Layer(str, Enum):
    EVIDENCE_ELIGIBILITY = "A"
    MECHANICAL_METHOD = "B"
    DIAGNOSTIC_CLAIM = "C"
    LANGUAGE_PROMOTION = "D"
    CROSS_CUTTING = "CROSS_CUTTING"


FAMILY_LAYER = {
    R5Family.EVID: R5Layer.EVIDENCE_ELIGIBILITY,
    R5Family.MEAS: R5Layer.EVIDENCE_ELIGIBILITY,
    R5Family.ADMIT: R5Layer.EVIDENCE_ELIGIBILITY,
    R5Family.R4: R5Layer.MECHANICAL_METHOD,
    R5Family.DIAG: R5Layer.DIAGNOSTIC_CLAIM,
    R5Family.ALT: R5Layer.DIAGNOSTIC_CLAIM,
    R5Family.CLAIM: R5Layer.DIAGNOSTIC_CLAIM,
    R5Family.CAUSE: R5Layer.DIAGNOSTIC_CLAIM,
    R5Family.NARROW: R5Layer.LANGUAGE_PROMOTION,
    R5Family.LANG: R5Layer.LANGUAGE_PROMOTION,
    R5Family.VERSION: R5Layer.CROSS_CUTTING,
    R5Family.PROV: R5Layer.CROSS_CUTTING,
    R5Family.CHAIN: R5Layer.CROSS_CUTTING,
    R5Family.PREC: R5Layer.CROSS_CUTTING,
}


class ExecutionMode(str, Enum):
    APPLICATION_SERVICE = "application_service"
    COMPONENT_BOUNDARY = "component_boundary"
    CONTROLLED_CASE = "controlled_case"
    DEPENDENCY_GATE = "dependency_gate"


class StageName(str, Enum):
    DATA_SUFFICIENCY = "data_sufficiency"
    REQUIRED_EVIDENCE = "required_evidence"
    EVIDENCE_ADMISSIBILITY = "evidence_admissibility"
    R4_METHOD_ELIGIBILITY = "r4_method_eligibility"
    EXECUTION = "execution"
    VALIDATION = "validation"
    EVIDENCE_CONFLICT_ASSESSMENT = "evidence_conflict_assessment"
    ANALYTICAL_OUTCOME = "analytical_outcome"
    ALTERNATIVE_EXPLANATION_CHECK = "alternative_explanation_check"
    CLAIM_DECISION = "claim_decision"
    DERIVED_MATERIAL_DISPOSITION = "derived_material_disposition"
    RENDERING = "rendering"
    ARTIFACT_INTEGRITY = "artifact_integrity"


class Reachability(str, Enum):
    REACHED = "reached"
    BLOCKED = "blocked"
    NOT_REACHED = "not_reached"


class ExpectationKind(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    PRECEDENCE = "precedence"


class AuthorityReference(StrictModel):
    document: str = Field(min_length=1)
    frozen_version: str = Field(min_length=1)
    section: str = Field(min_length=1)
    controlling_rule: str = Field(min_length=1)

    @field_validator("document")
    @classmethod
    def known_document(cls, value: str) -> str:
        if value not in R5_AUTHORITY_DOCUMENTS:
            raise ValueError(f"authority document is not allowlisted: {value}")
        return value

    @field_validator("frozen_version", "controlling_rule")
    @classmethod
    def nonblank_authority_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("authority reference fields must not be blank")
        return value

    @field_validator("section")
    @classmethod
    def section_reference_format(cls, value: str) -> str:
        if re.search(r"§\s*\d", value) is None:
            raise ValueError("authority section must contain a section-sign numeric reference")
        return value

    @model_validator(mode="after")
    def exact_frozen_version_binding(self) -> "AuthorityReference":
        approved_version = FROZEN_AUTHORITY_VERSIONS[self.document]
        if self.frozen_version != approved_version:
            raise ValueError(
                "authority-version binding mismatch: "
                f"{self.document} requires frozen_version={approved_version!r}"
            )
        return self


class ExecutionSpec(StrictModel):
    mode: ExecutionMode
    adapter_id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,63}$")
    required_capability: str = Field(min_length=1)
    required_capability_version: str = Field(min_length=1)

    @field_validator("required_capability", "required_capability_version")
    @classmethod
    def metadata_only_not_execution_location(cls, value: str) -> str:
        if not value.strip() or re.match(r"^[a-z][a-z0-9+.-]*://", value, flags=re.IGNORECASE):
            raise ValueError("execution capability metadata must be nonblank and cannot be a URL")
        return value


class InputArtifactSpec(StrictModel):
    path: str = Field(min_length=1)
    role: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("path")
    @classmethod
    def relative_safe_path(cls, value: str) -> str:
        candidate = Path(value)
        if candidate.is_absolute() or not candidate.parts or any(part in {"", ".", ".."} for part in candidate.parts):
            raise ValueError("input path must be a normalized relative path without traversal")
        return value


class PeriodContext(StrictModel):
    period_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    start_date: str = Field(min_length=1)
    end_date: str = Field(min_length=1)
    date_convention_ref: str = Field(min_length=1)


class FixtureContext(StrictModel):
    question_or_proposition: str | None = None
    execution_context: str = Field(min_length=1)
    intended_use: str = Field(min_length=1)
    scope: dict[str, Any] | None = None
    population: dict[str, Any] | None = None
    periods: tuple[PeriodContext, ...] = ()
    currency: str | None = None


class VersionBindings(StrictModel):
    metric_version: str | None = None
    r3_profile_version: str | None = None
    r4_method_version: str | None = None
    policy_version: str | None = None
    validator_version: str | None = None
    precision_version: str | None = None


class StageProjection(StrictModel):
    stage: StageName
    chain_id: str = Field(default="main", pattern=r"^[a-z][a-z0-9_]{0,63}$")
    reachability: Reachability
    outcome: Any = None
    controlling_reason: str | None = None
    authority_ref: str | None = None
    not_reached_due_to: StageName | None = None

    @model_validator(mode="after")
    def validate_reachability(self) -> "StageProjection":
        if self.reachability is Reachability.BLOCKED:
            if not self.controlling_reason or not self.authority_ref:
                raise ValueError("blocked stage requires controlling_reason and authority_ref")
            if self.not_reached_due_to is not None:
                raise ValueError("blocked stage cannot use not_reached_due_to")
        elif self.reachability is Reachability.NOT_REACHED:
            if self.outcome is not None:
                raise ValueError("not_reached stage cannot contain fabricated outcome")
            if self.controlling_reason is not None or self.authority_ref is not None:
                raise ValueError("not_reached stage cannot contain blocker result fields")
            if self.not_reached_due_to is None:
                raise ValueError("not_reached stage requires not_reached_due_to")
        else:
            if (
                self.controlling_reason is not None
                or self.authority_ref is not None
                or self.not_reached_due_to is not None
            ):
                raise ValueError("reached stage cannot contain blocked/not-reached fields")
        _reject_float(self.outcome)
        return self


class FirstBlocker(StrictModel):
    blocker_id: str = Field(min_length=1)
    stage: StageName
    chain_id: str = Field(default="main", pattern=r"^[a-z][a-z0-9_]{0,63}$")
    reason: str = Field(min_length=1)
    authority_ref: str = Field(min_length=1)


class ExpectedProjection(StrictModel):
    expectation_kind: ExpectationKind
    material_path: tuple[StageProjection, ...] = Field(min_length=1)
    chain_dispositions: dict[str, str] = Field(default_factory=dict)
    first_controlling_blocker: Literal["NONE"] | FirstBlocker
    final_disposition: str = Field(min_length=1)
    permitted_meaning: tuple[str, ...] = Field(min_length=1)
    prohibited_meaning: tuple[str, ...] = ()
    trace_integrity_expectation: dict[str, Any] | str | None = None
    unique_outcome_rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_expected_path(self) -> "ExpectedProjection":
        if self.expectation_kind is ExpectationKind.POSITIVE:
            if self.first_controlling_blocker != "NONE":
                raise ValueError("positive fixture requires first_controlling_blocker=NONE")
        elif self.first_controlling_blocker == "NONE":
            raise ValueError("negative/precedence fixture requires an explicit first blocker")
        _validate_projection_uniqueness(self.material_path)
        _validate_projection_flow(self.material_path)
        _validate_blocker_consistency(self.material_path, self.first_controlling_blocker)
        _validate_chain_dispositions(self.material_path, self.chain_dispositions)
        return self


class R5FixtureManifest(StrictModel):
    fixture_schema_version: Literal["r5_pf0_v1"]
    fixture_id: str
    fixture_version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: Literal["ACTIVE"]
    family: R5Family
    layer: R5Layer
    purpose: str = Field(min_length=1)
    primary_authority: AuthorityReference
    supporting_authorities: tuple[AuthorityReference, ...] = ()
    execution: ExecutionSpec
    inputs: tuple[InputArtifactSpec, ...] = ()
    context: FixtureContext
    bindings: VersionBindings = Field(default_factory=VersionBindings)
    expected: ExpectedProjection

    @model_validator(mode="after")
    def validate_identity(self) -> "R5FixtureManifest":
        match = R5_ACTIVE_ID_PATTERN.fullmatch(self.fixture_id)
        if match is None:
            raise ValueError("fixture_id is not a canonical ACTIVE R5 ID")
        if match.group(1) != self.family.value:
            raise ValueError("fixture_id family does not match family field")
        if FAMILY_LAYER[self.family] is not self.layer:
            raise ValueError("fixture family does not match frozen layer metadata")
        return self


class ActualProjection(StrictModel):
    material_path: tuple[StageProjection, ...] = Field(min_length=1)
    chain_dispositions: dict[str, str] = Field(default_factory=dict)
    first_controlling_blocker: Literal["NONE"] | FirstBlocker
    final_disposition: str = Field(min_length=1)
    trace_integrity_state: dict[str, Any] | str | None = None
    artifact_evidence_refs: tuple[str, ...] = ()
    actual_output_producer: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_actual_path(self) -> "ActualProjection":
        _validate_projection_uniqueness(self.material_path)
        _validate_projection_flow(self.material_path)
        _validate_blocker_consistency(self.material_path, self.first_controlling_blocker)
        _validate_chain_dispositions(self.material_path, self.chain_dispositions)
        return self


class LoadedR5Fixture(StrictModel):
    case_dir: Path
    manifest: R5FixtureManifest
    input_paths: tuple[Path, ...]


def safe_load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    """Load bounded YAML without tags, aliases, anchors, merges, or object construction."""
    yaml_path = Path(path)
    if not yaml_path.is_file():
        raise R5ManifestError(f"YAML file does not exist: {yaml_path}")
    if yaml_path.is_symlink():
        raise R5ManifestError(f"YAML file must not be a symlink: {yaml_path}")
    raw = yaml_path.read_bytes()
    if len(raw) > MAX_YAML_BYTES:
        raise R5ManifestError(f"YAML file exceeds {MAX_YAML_BYTES} bytes: {yaml_path}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise R5ManifestError(f"YAML file must be UTF-8: {yaml_path}") from exc
    try:
        for token in yaml.scan(text):
            if isinstance(token, (AliasToken, AnchorToken, TagToken)):
                raise R5ManifestError(f"YAML aliases, anchors, and explicit tags are forbidden: {yaml_path}")
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise R5ManifestError(f"YAML is not safely loadable: {yaml_path}") from exc
    if not isinstance(payload, dict):
        raise R5ManifestError(f"YAML root must be a mapping: {yaml_path}")
    nodes, depth = _shape(payload)
    if nodes > MAX_YAML_NODES or depth > MAX_YAML_DEPTH:
        raise R5ManifestError(f"YAML structure exceeds safety limits: {yaml_path}")
    return payload


def load_r5_manifest(case_dir: str | Path) -> LoadedR5Fixture:
    case_path = Path(case_dir)
    if not case_path.is_dir() or case_path.is_symlink():
        raise R5ManifestError(f"R5 fixture directory is missing or unsafe: {case_path}")
    manifest_path = case_path / "manifest.yaml"
    try:
        manifest = R5FixtureManifest.model_validate(safe_load_yaml_mapping(manifest_path))
    except R5ManifestError:
        raise
    except Exception as exc:
        raise R5ManifestError(f"R5 manifest schema invalid for {manifest_path}: {exc}") from exc
    if manifest.fixture_id != case_path.name:
        raise R5ManifestError("fixture directory name must exactly match manifest fixture_id")
    input_paths = tuple(_verified_input(case_path, item) for item in manifest.inputs)
    return LoadedR5Fixture(case_dir=case_path.resolve(), manifest=manifest, input_paths=input_paths)


def _verified_input(case_dir: Path, spec: InputArtifactSpec) -> Path:
    root = case_dir.resolve()
    candidate = case_dir.joinpath(*Path(spec.path).parts)
    for component in (case_dir, *candidate.parents):
        if component == case_dir.parent:
            break
        if component.exists() and component.is_symlink():
            raise R5ManifestError(f"input path contains symlink: {spec.path}")
    if candidate.is_symlink():
        raise R5ManifestError(f"input artifact must not be a symlink: {spec.path}")
    resolved = candidate.resolve(strict=False)
    if root not in resolved.parents:
        raise R5ManifestError(f"input path escapes fixture directory: {spec.path}")
    if not resolved.is_file():
        raise R5ManifestError(f"input artifact is missing: {spec.path}")
    if sha256_file(resolved) != spec.sha256:
        raise R5ManifestError(f"input artifact hash mismatch: {spec.path}")
    return resolved


def _shape(value: Any, depth: int = 1) -> tuple[int, int]:
    if isinstance(value, dict):
        if "<<" in value:
            raise R5ManifestError("YAML merge keys are forbidden")
        sizes = [_shape(item, depth + 1) for pair in value.items() for item in pair]
    elif isinstance(value, (list, tuple)):
        sizes = [_shape(item, depth + 1) for item in value]
    else:
        return 1, depth
    return 1 + sum(size for size, _ in sizes), max([depth, *(item_depth for _, item_depth in sizes)])


def _reject_float(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("binary floating-point is forbidden in material outcomes; use quoted Decimal text")
    if isinstance(value, dict):
        for item in value.values():
            _reject_float(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_float(item)


def _validate_projection_uniqueness(path: tuple[StageProjection, ...]) -> None:
    keys = [(item.chain_id, item.stage.value) for item in path]
    if len(keys) != len(set(keys)):
        raise ValueError("material_path cannot repeat a stage within one chain")


def _validate_projection_flow(path: tuple[StageProjection, ...]) -> None:
    blocked_by_chain: dict[str, set[StageName]] = {}
    for item in path:
        earlier_blocked = blocked_by_chain.setdefault(item.chain_id, set())
        if item.reachability is Reachability.NOT_REACHED and item.not_reached_due_to not in earlier_blocked:
            raise ValueError(
                "not_reached_due_to must reference an earlier BLOCKED stage in the same material chain"
            )
        if earlier_blocked and item.reachability is not Reachability.NOT_REACHED:
            raise ValueError("a chain cannot fabricate a reached or blocked result after it is blocked")
        if item.reachability is Reachability.BLOCKED:
            earlier_blocked.add(item.stage)


def _validate_blocker_consistency(
    path: tuple[StageProjection, ...], blocker: Literal["NONE"] | FirstBlocker
) -> None:
    blocked = [item for item in path if item.reachability is Reachability.BLOCKED]
    if blocker == "NONE":
        if blocked:
            raise ValueError("first_controlling_blocker=NONE is inconsistent with a blocked material stage")
        return
    if not any(
        item.stage is blocker.stage
        and item.chain_id == blocker.chain_id
        and item.controlling_reason == blocker.reason
        and item.authority_ref == blocker.authority_ref
        for item in blocked
    ):
        raise ValueError("first controlling blocker must exactly match a blocked material stage")


def _validate_chain_dispositions(path: tuple[StageProjection, ...], dispositions: dict[str, str]) -> None:
    chain_ids = {item.chain_id for item in path}
    if dispositions and set(dispositions) != chain_ids:
        raise ValueError("chain_dispositions must name every and only material_path chain")
    if any(not value for value in dispositions.values()):
        raise ValueError("chain disposition values must be non-empty")
