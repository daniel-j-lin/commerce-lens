# F1-B Public coverage authority amendment v1

Status: owner-approved policy; implementation verified by the F1-B regression
suite and full repository suite (see `tasks/F1-B-governed-coverage-intake.md`).
Authority: the F1-B owner instruction supplied on 2026-09-18.
Policy identifier: `public_user_declared_coverage_v1`.

This additive, versioned amendment governs only Public descriptive Revenue,
Orders, AOV, and Revenue Change. It supplements Canonical Dataset and Metric
Dictionary §15 (comparable periods and independent source coverage) and Evidence
Contract §§13–14 (required evidence and insufficiency). Historical Approved /
Frozen files remain unchanged. No other Frozen semantic is replaced.

For this boundary, **independent of the analytical request** means an explicit
export completeness attestation separate from the question and its requested
dates. It does not mean **independently verified by CommerceLens or an external
verifier**. An accepted user attestation is always `USER_DECLARED`, never
`EXTERNALLY_VERIFIED`, `SOURCE_DECLARED`, or `TEST_FIXTURE`.

An attestation can satisfy source coverage only after deterministic checks bind
it to the actual DatasetReference/content fingerprint, source type and selected
sheet/table, mapping/eligibility context, population, explicit applicable filters,
compatible date convention, containing coverage dates, and a sufficient
availability cutoff for a closed period. Unknown, ambiguous, uncertain,
contradictory, incomplete or implicit declarations fail closed. Neither request
dates nor observed source date extrema establish or extend completeness.

The bounded v1 implementation accepts `order_date_utc` inclusive calendar dates.
The declared availability cutoff is an exclusive UTC instant at or after
midnight following the covered end date; it must be no later than the recorded
confirmation time and the runtime clock. If extraction time is supplied, cutoff
must be no later than extraction, and extraction no later than confirmation.
Unknown extraction time is allowed only with an explicit reviewed-export basis
and declared availability cutoff. V1 records an explicit fixed assertion that the
declarant reviewed export dates, population/status filters, all pages and export
completion; arbitrary free text is not parsed into completeness authority. All requested periods must lie within the
closed declared interval. Unsupported date conventions fail closed.

Population/filter compatibility is conservative exact equality with the existing
ScopeDefinition. An empty filter set requires explicit `no_additional_filters`;
otherwise the exact canonical filters require `explicit_filters`. The fixed
Public paid/Eligible and cancelled/Excluded mapping is bound through the full
canonicalization context fingerprint. No vendor semantics or identity proof is
introduced. Distinct unresolved declarations for the same dataset fail closed;
v1 does not implement supersession or merge coverage from separate declarations.

Acceptance projects only source coverage into existing PeriodCoverageEvidence and
`req_global` source authority. Metric inputs/mapping, currency, eligibility,
canonicalization, sufficiency, execution, validation and ClaimDecision remain
separate gates. In particular, acceptance alone cannot satisfy `req_<metric>` or
arbitrary requirement IDs. The existing canonical identity mapping or separately
confirmed explicit mapping supplies the Public input-context authority for the
requested governed registry Metric; canonicalization and existing downstream
checks still determine its validity. No ClaimDecision state or qualification
policy changes. A complete empty eligible population retains Revenue/Orders = 0
and AOV = Undefined only when the remaining gates are valid.

Every dependent public result discloses: “Coverage is based on a user-provided
declaration and has not been independently verified by CommerceLens.” Structured
provenance links declaration, dataset, period, scope/filters, cutoff, policy and
artifact. Trusted Python evidence inputs remain a distinct caller boundary.
External JSON must pass this validator before creating trusted evidence objects.

Coverage confirmation is separate from schema confirmation and uses one
consolidated proposal containing the governed coverage facts. The proposal may
represent the reviewed-export-controls completeness basis directly; the user
does not need to repeat the same audit wording in a second interaction. Only an
explicit confirmation bound to that exact complete proposal may record an
attestation. Corrections, silence, and uncertain replies never confirm. This is
a UX clarification only: the required facts, deterministic bindings,
`USER_DECLARED` semantics, independent-verification disclosure, and existing
temporary/explicitly retained storage remain unchanged. Persistent auditability,
F2-A and all non-descriptive or additional Metrics remain out of scope.
