# R4-IMP implementation allocation

R4 is implemented as a bounded internal analytical method, not as a scalar Metric.

- `contracts/r4.py` owns the R4 v1.0 method, request, authority, trace, executed-result, validation, and validated-result shapes.
- `engine/r4_execution.py` owns deterministic Product-Level Revenue Decomposition execution and complete trace production.
- `validation/r4_validator.py` independently re-reads canonical authority and checks the frozen R4 invariants.
- `persistence/r4_repository.py` stores and re-authenticates immutable R4 artifacts through the existing `ArtifactStore` and `MetadataStore`.
- `application/r4_service.py` is the only new internal orchestration entry point. Before execution it authenticates the exact Baseline Revenue, Comparison Revenue, and Revenue Change `ValidatedResult` authorities and their existing P6/P7 descriptive `AdmissibleEvidence` authorities. It blocks missing, copied, tampered, stale, or cross-lineage Evidence and blocks diagnostic execution without exact R3 authority.

R4 reuses the central precision authority without defining an R4-local substitute: `PRECISION_POLICY_REF` identifies Section 34 of the approved Canonical Dataset and Metric Dictionary, and `PRECISION_POLICY_VERSION` binds its frozen document version `v1.0`. Request, execution authority, trace, validation, and validated output all retain that exact pair and fail closed on an absent or stale version.

The public `run_analysis(...)` surface, Metric allowlist, response projection, README feature list, and Claim policy remain unchanged.
