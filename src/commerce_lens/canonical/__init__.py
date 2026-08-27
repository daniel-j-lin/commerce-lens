"""Canonicalization boundary."""

from commerce_lens.canonical.mapping import CanonicalFieldMapping, CanonicalMapping, identity_mapping
from commerce_lens.canonical.models import (
    CanonicalLineRecord,
    CanonicalizationRequest,
    CanonicalizationResult,
    EligibilityMode,
    EligibilityState,
    EligibilityValueMapping,
    PeriodCoverageEvidence,
)
from commerce_lens.canonical.schema import (
    CANONICAL_SCHEMA_VERSION,
    UNCLASSIFIED_CATEGORY_ID,
    UNCLASSIFIED_CATEGORY_NAME,
)
from commerce_lens.canonical.service import canonicalize_dataset

__all__ = [
    "CANONICAL_SCHEMA_VERSION",
    "UNCLASSIFIED_CATEGORY_ID",
    "UNCLASSIFIED_CATEGORY_NAME",
    "CanonicalFieldMapping",
    "CanonicalLineRecord",
    "CanonicalMapping",
    "CanonicalizationRequest",
    "CanonicalizationResult",
    "EligibilityMode",
    "EligibilityState",
    "EligibilityValueMapping",
    "PeriodCoverageEvidence",
    "canonicalize_dataset",
    "identity_mapping",
]
