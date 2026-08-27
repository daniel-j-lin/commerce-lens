"""Claim admissibility policy boundary."""

from __future__ import annotations

from typing import Protocol

from commerce_lens.contracts.evidence import ClaimCandidate, ClaimDecision


class ClaimAdmissibilityEvaluator(Protocol):
    """Future deterministic evaluator interface.

    Phase 1 intentionally defines only the boundary. Implementations must not
    approve claims until governed policy is implemented.
    """

    def evaluate(self, candidate: ClaimCandidate) -> ClaimDecision:
        raise NotImplementedError("Claim admissibility policy is not implemented in Phase 1")

