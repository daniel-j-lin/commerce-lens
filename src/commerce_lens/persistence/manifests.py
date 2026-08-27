"""Run manifest placeholder structures."""

from __future__ import annotations

from pydantic import Field

from commerce_lens.contracts.common import ArtifactReference, ContractBase


class ArtifactManifest(ContractBase):
    manifest_id: str = Field(min_length=1)
    artifact_refs: tuple[ArtifactReference, ...] = ()

