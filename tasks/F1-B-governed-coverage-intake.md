# CommerceLens F1-B — Governed Coverage Authority Intake

Verification report, 2026-09-19. No commit, push, tag, release or deployment.

1. **Starting commit / baseline.** `92eea1b887df0560231d31131459aed52f0ca36b`
   on `main`, with the pre-existing uncommitted F1-A/F2-B authority remediation,
   fixture harness, regression tests and documentation changes preserved. The
   task began with 15 modified tracked files and three untracked test files.
   This is not a clean-HEAD-only baseline. A reconstructed copy of that baseline
   rejected `--coverage-declaration` with exit 2; see
   [before evidence](evidence/f1-b/before-intake.json).
2. **Branch.** `codex/f1-b-governed-coverage-intake`.
3. **Specification amendment.**
   [F1-B Public coverage authority amendment v1](../docs/amendments/F1-B-coverage-authority-v1.md)
   was written before production implementation under the supplied owner approval.
   It distinguishes independence from the question from external verification.
   It is an additive versioned amendment to the Public reading of Metric
   Dictionary §15 and Evidence Contract §§13–14. Historical Frozen files and their
   version history are unchanged. It authorizes no additional Metric/Claim scope.
4. **Files changed by F1-B.**
   - `docs/amendments/F1-B-coverage-authority-v1.md`: additive approved policy.
   - `src/commerce_lens/skill/coverage_intake.py`: model, confirmation record,
     bounded parser, context binding, deterministic validation and source projection.
   - `src/commerce_lens/skill/integration.py`: additive external boundary, preview,
     separate mapping input gate, artifact linkage and disclosure.
   - `src/commerce_lens/skill/public_response.py`: additive provenance output.
   - `src/commerce_lens/canonical/service.py`: skip an empty DuckDB insert batch;
     preserve the empty canonical table and downstream authority gates.
   - `skills/commerce-lens/scripts/run_public_analysis.py`: structured intake/preview.
   - `skills/commerce-lens/SKILL.md`: separate schema/coverage confirmation workflow.
   - `tests/skill/test_coverage_intake.py`: focused deterministic acceptance suite.
   - `README.md`, `docs/USAGE.md`, `docs/DEVELOPMENT.md`, `PROJECT_STATE.md`: policy,
     usage, boundary and retention documentation.
   - This report and `tasks/evidence/f1-b/`: synthetic before/after QA evidence.
   Other existing modified roadmap/test files belong to the starting worktree;
   F1-B does not claim them as new work.
5. **Declaration model.** Immutable extra-forbidden Pydantic `CoverageDeclaration`:
   ID, policy, aware recorded time, USER_DECLARED, dataset ID/content SHA-256,
   source type/sheet/table, human filename, covered dates, UTC convention,
   ScopeDefinition and explicit filter status, canonicalization context hash,
   availability cutoff, known-or-null extraction time, exact completeness and
   reviewed-export-basis assertions, optional local actor/session reference.
   No real name, email, signer or account credentials.
6. **Policy version.** `public_user_declared_coverage_v1`; this also versions the
   bounded declaration schema. Unknown versions are rejected.
7. **Validator architecture.** One external parser/validator serves Skill JSON and
   standalone manifests. JSON is bounded to 64 KiB and 1–16 declarations; duplicate
   keys, extra fields and invalid models fail closed. Exact confirmation/basis
   assertions avoid treating arbitrary prose as deterministically understood.
   Validation precedes trusted evidence projection. Current-input conflicts and
   conflicting prior accepted records in the same retained store block. No
   timestamp/latest-wins, implicit supersession or combining partial declarations.
8. **Dataset binding.** Reuses DatasetRegistry/DatasetReference and the actual
   immutable source snapshot. Dataset ID includes source bytes, source type and
   selected sheet/table. Both ID and full content hash must match. External runs
   use that validated DatasetReference for analysis, not a second source read.
   Filename is not authority; renaming identical bytes does not invalidate it.
9. **Scope/filter binding.** Exact existing ScopeDefinition equality; empty filters
   require `no_additional_filters`, otherwise `explicit_filters`. Population and
   filters cannot silently narrow the requested target. The full actual
   CanonicalizationRequest fingerprint binds mapping, eligibility value mappings,
   schema/date policy and currency context. Changed contexts cannot reuse authority.
10. **Cutoff behavior.** Inclusive UTC calendar dates; exclusive availability cutoff
    must be at/after midnight following the declared coverage end, at/before
    recorded confirmation, and at/before the internal runtime clock. Known
    extraction must fall between cutoff and recording. No CLI clock override.
    Every requested period must be contained; date conventions must match. Q4
    2026 is still open at this task's actual date and is blocked in production.
11. **Provenance behavior.** Always USER_DECLARED on this external path. Existing
    ClaimDecision states/policies remain untouched; disclosure does not pretend
    to be independent verification or add a trust score. The declaration is
    written through ArtifactStore and referenced by source evidence/sufficiency
    and the response's structured provenance.
12. **Skill confirmation UX.** Mapping confirmation happens first. Coverage has a
    distinct file/sheet, requested dates/time boundary, population, eligibility,
    filters, cutoff and source-basis summary. Choices: Confirm / Correct / I don't
    know. Corrections require reconfirmation. Only explicit confirmation of the
    complete summary/basis produces a declaration; silence/vague replies do not.
13. **Runner/intake interface.** Add `--prepare-coverage` to normal arguments for
    an unconfirmed summary/template with null confirmation/time/basis fields and
    no analysis. Add `--coverage-declaration FILE` for validated external JSON.
    The Python keyword is `coverage_declarations`; existing trusted evidence
    keywords remain unchanged. Mixing external and trusted evidence fails closed.
    There is no `--complete` or provenance-promotion flag.
14. **Sufficiency integration.** Coverage projects only `req_global` source authority
    and PeriodCoverageEvidence. The independently checked canonical mapping and
    known registry Metric provide only the requested `req_<metric>` input-context
    authority. Arbitrary requirements remain missing. Existing canonicalization,
    currency, eligibility, sufficiency, planning, execution, validation and exact
    ClaimDecision binding remain the same chain. Coverage cannot repair invalid
    mapping, unknown currency/eligibility or invalid money inputs.
15. **Complete-zero result.** Accepted coverage plus the valid scoped population
    yields Revenue 0, Orders 0 and AOV Undefined (`orders_equals_zero`) both for
    the empty comparison period and for an all-excluded source with known currency.
    There is no zero shortcut. A header-only file with no authority now reaches
    the governed blocked result instead of throwing on `executemany([])`.
16. **Ambiguous/unknown result.** No supported material claim. Non-confirmation
    cannot construct an attestation; invalid manifests are rejected or produce
    clarification/blocked. Missing declarations retain the original sufficiency
    block, including when observed source min/max span both requested periods.
17. **Spoofing protections.** SOURCE_DECLARED, EXTERNALLY_VERIFIED, TEST_FIXTURE,
    missing provenance, arbitrary requirement IDs, bypass fields and mutated
    model instances are rejected at the external boundary. Existing trusted
    Python callers remain trusted; this is not identity or signature verification.
18. **Output disclosure.** “Coverage is based on a user-provided declaration and
    has not been independently verified by CommerceLens.”
    `response.coverage_provenance` preserves the declaration, scope/filters,
    period/cutoff/policy/dataset and ArtifactReference, alongside the request/run
    IDs and normal validated-result/ClaimDecision output.
19. **Retention limitation.** Uses existing temporary or explicitly paired retained
    stores. Temporary cleanup deletes local coverage artifacts. Returned JSON can
    carry provenance but is not persistent auditability; conflicts in deleted or
    other stores cannot be detected. Skill temporary declaration inputs must also
    be cleaned up. QA files here are explicitly retained synthetic test evidence,
    not a new product retention policy or F2-A implementation.
20. **Natural-language E2E result.** The requested question, “How did revenue change
    from Q3 2026 to Q4 2026?”, exercises non-canonical CSV mapping proposals,
    separately confirmed mapping, no-coverage blocking, separate coverage preview,
    scripted explicit Confirm, structured USER_DECLARED input, the actual runner,
    full kernel/ClaimDecision and visible disclosure. Result: +60.00 USD on the
    synthetic 120.00 / 180.00 fixture, under an explicitly patched test clock of
    2027-01-03. I don't know cannot create the declaration; no-coverage remains
    blocked. This is an automated Skill-path/runner scenario with scripted host
    interpretation/confirmation, not an observed real user's live host dialogue.
    The actual clock separately blocks future Q4 2026. A closed Q3/Q4 2025
    scenario also exercises real CLI processes and both retention modes without
    clock patching. See [captured runner sequence](evidence/f1-b/after-skill-path.json).
21. **Focused tests.** Final F1-B plus canonical selection: **105 passed in
    217.40s** (70 F1-B cases and 35 existing canonical tests). All 20 owner
    acceptance cases have deterministic coverage.
22. **Relevant regressions.** Initial F1-A/F2-B regression invocation: 29 passed.
    The targeted existing sufficiency/application/Skill/end-to-end/P11/P12/P13/P14
    selection: 131 passed in 504.16s, before the final empty-batch guard. The final
    full suite re-executes these against that guard. Exact commands below.
23. **Full suite.** **700 passed in 461.25s** (exit 0), including all final
    F1-B, F1-A/F2-B, P11–P14, canonical, sufficiency, integration and runner tests. An earlier run was deliberately
    interrupted after 360 passing tests to incorporate the empty-batch correction;
    it is not counted as a completed suite.
24. **git diff --check.** Passed (exit 0). Frozen files, dependencies and
    plugin version have no diff. No configured lint or
    typecheck tool was found in pyproject.toml or repository configuration.
25. **Compatibility impact.** Additive keyword and response field; old trusted
    callers and fixture harness remain supported. Bare-file commands retain their
    missing-evidence blocks. The empty-batch fix permits normal empty-table
    processing without changing any Metric formula or currency authority. No new
    dependency, migration, public breaking API, ClaimDecision state, identity
    infrastructure or vendor semantics.
26. **Remaining limitations.** V1 supports only UTC date convention, exact scopes,
    the explicit reviewed-export-controls source basis, and the existing Public
    paid/cancelled eligibility context. It conservatively binds full mapping IDs;
    it does not infer equivalent/subset filter semantics. Conflicting retained
    declarations have no supersession mechanism. The CLI retains its existing
    all-eligible scope; filtered target scopes are supported through the existing
    Python intent rather than new scope flags. Currency cannot be invented for
    a completely empty source. No separate fresh-host/live-user interaction was
    observed; automated confirmations are explicitly labeled as QA input. None of
    F2-A/F3/F4-B, new Metrics, diagnostics, connectors, vendor manifests,
    benchmarks, external participant validation or deployment was implemented.
27. **F1-B verdict.** **PASS for deterministic implementation and automated
    Skill-path acceptance.** This does not assert that a separate live-user/host
    dialogue was observed; the exact E2E boundary is stated in items 20 and 26.
28. **READY FOR HUMAN REVIEW. YES.** Review the additive policy, external intake
    boundary and separate confirmation wording. All work remains uncommitted;
    no push, tag, release or deployment occurred.

## Exact validation commands

Run from the CommerceLens repository:

```sh
.venv/bin/python -m pytest tests/skill/test_public_authority_regression.py
.venv/bin/python -m pytest tests/skill/test_coverage_intake.py
.venv/bin/python -m pytest tests/skill/test_public_authority_regression.py tests/sufficiency tests/application tests/skill tests/end_to_end tests/p11 tests/p12 tests/p13 tests/p14 --ignore=tests/skill/test_coverage_intake.py
.venv/bin/python -m pytest tests/skill/test_coverage_intake.py tests/canonical
.venv/bin/python -m pytest
git diff --check
git diff --name-only -- docs/frozen pyproject.toml .codex-plugin/plugin.json
```

Before/after defect evidence: expanded focused tests initially reported
`1 failed, 69 passed`; the header-only source raised DuckDB
`Invalid Input Error: executemany requires a non-empty list of parameter sets to be provided`.
The guarded insertion fixes only that failure path; no default coverage or zeros
were introduced. A separate earlier assertion compared numeric zero to a
specific decimal string format; it was corrected to compare numerical values.

## Owner acceptance-case mapping

| Case | Focused regression coverage |
| --- | --- |
| 1 | `test_valid_user_declared_chain_and_traceability` |
| 2 | `test_missing_declaration_cannot_turn_absent_rows_into_zero` |
| 3 | `test_invalid_external_declarations_fail_closed`, `test_only_explicit_confirmation_records_attestation` |
| 4 | `test_changed_bytes` and dataset/hash mutations |
| 5 | sheet/source/table mutations and `test_xlsx_binding_and_execution` |
| 6 | covered-start/end mutations |
| 7 | date-convention mutation |
| 8 | cutoff/recording/extraction mutations and `test_open_period_actual_clock` |
| 9 | `test_explicit_scope_and_filters` |
| 10 | unknown/mismatched filters_status mutations |
| 11 | `test_filters_omit_required_population`, `test_population_differs` |
| 12 | `test_mapping_change_cannot_reuse_declaration`, `test_changed_eligibility_semantics_invalidates_declaration` |
| 13 | `test_complete_zero`, `test_complete_zero_with_only_excluded_rows` |
| 14 | no-declaration empty period and `test_empty_source_without_authority_is_blocked` |
| 15 | SOURCE_DECLARED / EXTERNALLY_VERIFIED mutations |
| 16 | TEST_FIXTURE mutation and `test_reconstructed_model_cannot_spoof_provenance` |
| 17 | `test_conflicts_in_one_intake`, `test_conflicts_with_retained_declaration` |
| 18 | `test_min_max_never_establish_coverage` |
| 19 | `test_request_expanded_one_day` |
| 20 | Existing `test_public_authority_regression.py` plus full suite |

Additional regressions cover missing/duplicate/extra JSON fields, bounded input,
renaming, same-content duplicate declarations, mixed trust boundaries, arbitrary
requirements, mapping/currency/eligibility/money gates, actual runner E2E, XLSX,
and fresh-process temporary/retained provenance behavior.
