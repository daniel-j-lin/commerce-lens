"""Pydantic contracts for CommerceLens cross-boundary records."""

from commerce_lens.contracts.common import ClaimState, ClaimType, MetricState, RunStatus, SourceType
from commerce_lens.contracts.diagnostic import DiagnosticProposition, PreTestDiagnosticEvaluation
from commerce_lens.contracts.hypotheses import (
    CandidateProposal,
    CandidateProposalBatch,
    GenerationProvenance,
    GovernedHypothesis,
    R6ToR7Handoff,
)
from commerce_lens.contracts.required_evidence import (
    HypothesisFamilyRequirementTemplate,
    RequirementJudgment,
    ResolvedRequiredEvidenceProfile,
)

__all__ = [
    "CandidateProposal",
    "CandidateProposalBatch",
    "ClaimState",
    "ClaimType",
    "DiagnosticProposition",
    "GenerationProvenance",
    "GovernedHypothesis",
    "HypothesisFamilyRequirementTemplate",
    "MetricState",
    "PreTestDiagnosticEvaluation",
    "R6ToR7Handoff",
    "RequirementJudgment",
    "ResolvedRequiredEvidenceProfile",
    "RunStatus",
    "SourceType",
]
