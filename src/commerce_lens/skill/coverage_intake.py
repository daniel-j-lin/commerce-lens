"""F1-B external USER_DECLARED boundary; never a trusted evidence deserializer.

Owner authority: docs/amendments/F1-B-coverage-authority-v1.md.
The validator projects source coverage only. Other analytical gates remain intact.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from commerce_lens.canonical.models import CanonicalizationRequest, PeriodCoverageEvidence
from commerce_lens.contracts.common import (
    AvailableEvidence, ContractBase, PeriodDefinition, ScopeDefinition, SourceType, utc_now,
)
from commerce_lens.contracts.evidence import DatasetReference
from commerce_lens.evidence.identifiers import canonical_json_fingerprint
from commerce_lens.persistence.artifact_store import ArtifactStore

POLICY_VERSION = "public_user_declared_coverage_v1"
COMPLETENESS_ASSERTION = "I confirm this export is complete for the declared period, population and filters through the declared data-availability cutoff."
DISCLOSURE = "Coverage is based on a user-provided declaration and has not been independently verified by CommerceLens."
SOURCE_BASIS_ASSERTION = "I reviewed the export date range, population/status filters, all pages and export completion status against this declaration."
CONFIRMED_INTENT = "confirmed"
MAX_DECLARATION_BYTES = 65536


class CoverageDeclaration(ContractBase):
    declaration_id: str = Field(min_length=1, max_length=160)
    policy_version: Literal["public_user_declared_coverage_v1"]
    recorded_at: datetime
    authority_type: Literal["USER_DECLARED"]
    dataset_id: str = Field(min_length=1)
    content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_type: Literal[SourceType.CSV, SourceType.EXCEL_XLSX]
    selected_sheet: str | None
    selected_table: None
    source_filename: str = Field(min_length=1, max_length=255)
    covered_start: date
    covered_end: date
    date_convention_ref: Literal["order_date_utc"]
    scope: ScopeDefinition
    filters_status: Literal["no_additional_filters", "explicit_filters"]
    context_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    data_availability_cutoff: datetime
    extracted_at: datetime | None
    completeness_assertion: Literal[COMPLETENESS_ASSERTION]
    source_basis: Literal["reviewed_export_controls"]
    source_basis_detail: Literal[SOURCE_BASIS_ASSERTION]
    actor_session_ref: str | None = Field(default=None, max_length=160)

    @field_validator("recorded_at", "data_availability_cutoff", "extracted_at")
    @classmethod
    def aware_instant(cls, value):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("coverage timestamps require an explicit timezone")
        return value.astimezone(UTC) if value is not None else None

    @model_validator(mode="after")
    def coherent(self):
        if self.covered_end < self.covered_start or self.covered_end == date.max:
            raise ValueError("invalid coverage interval")
        expected = "explicit_filters" if self.scope.filters else "no_additional_filters"
        if self.filters_status != expected:
            raise ValueError("filters must be explicitly enumerated, including no additional filters")
        if self.source_type == SourceType.EXCEL_XLSX and not self.selected_sheet:
            raise ValueError("XLSX declaration requires explicit selected sheet")
        if self.source_type == SourceType.CSV and self.selected_sheet is not None:
            raise ValueError("CSV declaration cannot select a sheet")
        return self


def context_fingerprint(request: CanonicalizationRequest) -> str:
    """Bind the actual mapping, eligibility, schema, normalization and currency context."""
    return canonical_json_fingerprint(request.model_dump(mode="json"))


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate coverage JSON key: {key}")
        result[key] = value
    return result


def load_declarations(path: str | Path) -> tuple[CoverageDeclaration, ...]:
    # Bounded read, including when file size changes between stat/read.
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_DECLARATION_BYTES + 1)
    if len(raw) > MAX_DECLARATION_BYTES:
        raise ValueError("coverage declaration exceeds 64 KiB")
    return parse_declarations(json.loads(raw, object_pairs_hook=_unique_keys))


def parse_declarations(payload) -> tuple[CoverageDeclaration, ...]:
    values = payload if isinstance(payload, (list, tuple)) else [payload]
    if not 1 <= len(values) <= 16:
        raise ValueError("supply 1–16 coverage declarations; unresolved conflicts fail closed")
    # Revalidate even Pydantic instances: model_copy/model_construct are trusted APIs.
    return tuple(CoverageDeclaration.model_validate(
        item.model_dump(mode="json") if isinstance(item, CoverageDeclaration) else item
    ) for item in values)


def declaration_template(dataset: DatasetReference, context: CanonicalizationRequest,
                         scope: ScopeDefinition, periods: tuple[PeriodDefinition, ...]) -> dict:
    """A non-authoritative confirmation proposal. Null fields intentionally cannot validate."""
    return {
        "declaration_id": None, "policy_version": POLICY_VERSION, "recorded_at": None,
        "authority_type": "USER_DECLARED", "dataset_id": dataset.dataset_id,
        "content_fingerprint": dataset.content_fingerprint, "source_type": dataset.source_type.value,
        "selected_sheet": dataset.selected_sheet, "selected_table": dataset.selected_table,
        "source_filename": dataset.original_name,
        "covered_start": min(p.start_date for p in periods).isoformat(),
        "covered_end": max(p.end_date for p in periods).isoformat(),
        "date_convention_ref": periods[0].date_convention_ref,
        "scope": scope.model_dump(mode="json"),
        "filters_status": "explicit_filters" if scope.filters else "no_additional_filters",
        "context_fingerprint": context_fingerprint(context),
        "data_availability_cutoff": None, "extracted_at": None,
        "completeness_assertion": None, "source_basis": None, "source_basis_detail": None,
        "actor_session_ref": None,
    }


def _utc_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("coverage timestamps require an explicit timezone")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def complete_coverage_proposal(template: dict, *, data_availability_cutoff: datetime,
                               source_basis_detail: str = SOURCE_BASIS_ASSERTION,
                               extracted_at: datetime | None = None) -> dict:
    """Build the exact structured facts that may be shown and confirmed.

    The result is still a proposal, not evidence. Required authority fields are
    deliberately populated only from explicit host-provided coverage facts.
    """
    if not data_availability_cutoff:
        raise ValueError("a complete coverage proposal requires a data-availability cutoff")
    if source_basis_detail != SOURCE_BASIS_ASSERTION:
        raise ValueError("coverage source basis must use the governed reviewed-export-controls assertion")
    return {
        **template,
        "data_availability_cutoff": _utc_iso(data_availability_cutoff),
        "extracted_at": _utc_iso(extracted_at),
        "source_basis": "reviewed_export_controls",
        "source_basis_detail": source_basis_detail,
        "completeness_assertion": COMPLETENESS_ASSERTION,
    }


def _proposal_binding(proposal: dict, requested_periods: tuple[PeriodDefinition, ...]) -> dict:
    """Return all displayed semantic facts, excluding run-local identity fields."""
    binding = {
        key: value for key, value in proposal.items()
        if key not in {"declaration_id", "recorded_at", "actor_session_ref"}
    }
    binding["requested_periods"] = [period.model_dump(mode="json") for period in requested_periods]
    return binding


def coverage_proposal_fingerprint(template: dict, *, requested_periods: tuple[PeriodDefinition, ...],
                                  data_availability_cutoff: datetime,
                                  source_basis_detail: str = SOURCE_BASIS_ASSERTION,
                                  extracted_at: datetime | None = None) -> str:
    """Fingerprint the complete proposal before any USER_DECLARED authority exists."""
    proposal = complete_coverage_proposal(
        template,
        data_availability_cutoff=data_availability_cutoff,
        source_basis_detail=source_basis_detail,
        extracted_at=extracted_at,
    )
    return canonical_json_fingerprint(_proposal_binding(proposal, requested_periods))


def confirm_declaration(template: dict, *, response: str | None = None,
                        confirmation_intent: str | None = None,
                        proposal_fingerprint: str | None = None,
                        requested_periods: tuple[PeriodDefinition, ...],
                        recorded_at: datetime,
                        declaration_id: str, data_availability_cutoff: datetime,
                        source_basis_detail: str = SOURCE_BASIS_ASSERTION,
                        extracted_at: datetime | None = None,
                        actor_session_ref: str | None = None) -> CoverageDeclaration:
    """Record only a canonical confirmation of one complete displayed proposal.

    This creates an untrusted declaration, NOT coverage evidence. Intake must still
    validate it against the current bytes/context/period and clock before use.
    """
    if confirmation_intent is not None and confirmation_intent != CONFIRMED_INTENT:
        raise ValueError("coverage is unconfirmed; correction or uncertainty requires clarification")
    if confirmation_intent is None and response != "Confirm":
        raise ValueError("coverage is unconfirmed; affirmative language must be normalized to confirmed")
    if confirmation_intent is not None and response not in (None, "Confirm"):
        raise ValueError("free-form confirmation text must be normalized by the host")
    if not proposal_fingerprint:
        raise ValueError("complete displayed coverage proposal fingerprint is required")

    proposal = complete_coverage_proposal(
        template,
        data_availability_cutoff=data_availability_cutoff,
        source_basis_detail=source_basis_detail,
        extracted_at=extracted_at,
    )
    expected_fingerprint = canonical_json_fingerprint(_proposal_binding(proposal, requested_periods))
    if proposal_fingerprint != expected_fingerprint:
        raise ValueError("coverage confirmation proposal fingerprint does not match the displayed proposal")
    return CoverageDeclaration.model_validate({
        **proposal, "declaration_id": declaration_id, "recorded_at": recorded_at,
        "actor_session_ref": actor_session_ref,
    })


def _semantic_binding(declaration: CoverageDeclaration) -> dict:
    return declaration.model_dump(mode="json", exclude={
        "declaration_id", "recorded_at", "source_filename", "source_basis_detail", "actor_session_ref",
    })


def validate_declarations(payload, *, dataset: DatasetReference,
                          context: CanonicalizationRequest, scope: ScopeDefinition,
                          periods: tuple[PeriodDefinition, ...],
                          artifact_store: ArtifactStore) -> CoverageDeclaration:
    declarations = parse_declarations(payload)
    now = utc_now()
    for item in declarations:
        actual = (dataset.dataset_id, dataset.content_fingerprint, dataset.source_type,
                  dataset.selected_sheet, dataset.selected_table)
        declared = (item.dataset_id, item.content_fingerprint, item.source_type,
                    item.selected_sheet, item.selected_table)
        if declared != actual:
            raise ValueError("coverage dataset/content/sheet/table/source binding differs")
        if item.context_fingerprint != context_fingerprint(context):
            raise ValueError("coverage mapping/eligibility context changed")
        if item.scope != scope:
            raise ValueError("coverage population/filters differ from requested scope")
        closed_at = datetime.combine(item.covered_end + timedelta(days=1), time.min, UTC)
        if not closed_at <= item.data_availability_cutoff <= item.recorded_at <= now:
            raise ValueError("coverage period is open or cutoff/recorded time is insufficient or future")
        if item.extracted_at is not None and not item.data_availability_cutoff <= item.extracted_at <= item.recorded_at:
            raise ValueError("coverage extraction time conflicts with availability cutoff")
        for period in periods:
            if period.date_convention_ref != item.date_convention_ref:
                raise ValueError("coverage date convention differs")
            if not item.covered_start <= period.start_date <= period.end_date <= item.covered_end:
                raise ValueError("requested period exceeds declared coverage")
    # No implicit latest-wins rule. Include prior accepted records in this retained
    # store; temporary runs cannot discover declarations from deleted/other stores.
    known = list(declarations)
    root = artifact_store.safe_path("runs", "coverage_declarations", dataset.dataset_id)
    if root.exists():
        for path in sorted(root.glob("*.json")):
            known.extend(load_declarations(path))
    bindings = {canonical_json_fingerprint(_semantic_binding(item)) for item in known}
    identities = {}
    for item in known:
        content = canonical_json_fingerprint(item.model_dump(mode="json"))
        if item.declaration_id in identities and identities[item.declaration_id] != content:
            raise ValueError("conflicting reuse of declaration ID")
        identities[item.declaration_id] = content
    if len(bindings) != 1:
        raise ValueError("conflicting coverage declarations; v1 has no supersession rule")
    return sorted(declarations, key=lambda item: item.declaration_id)[0]


def project_coverage(declaration: CoverageDeclaration, artifact_ref: str):
    """Called only after validate_declarations; supports source coverage alone."""
    return (
        AvailableEvidence(
            evidence_id=declaration.declaration_id, description=DISCLOSURE,
            source_ref=artifact_ref, satisfies_requirement_ids=("req_global",),
        ),
        PeriodCoverageEvidence(
            coverage_ref_id=declaration.declaration_id, dataset_ref_id=declaration.dataset_id,
            observed_start_date=declaration.covered_start, observed_end_date=declaration.covered_end,
            date_convention_ref=declaration.date_convention_ref, governing_note_ref=artifact_ref,
        ),
    )
