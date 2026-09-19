# F2-A Evidence Persistence / Retention amendment v1

Status: owner-approved implementation amendment; additive to the frozen
CommerceLens contracts and the F1-B amendment.

Scope: local evidence persistence for an explicitly retained analysis run.
This amendment does not change Metric definitions, Evidence authority,
sufficiency, admissibility, ClaimDecision, or public-response semantics.

## Retention policy

- The default is `temporary`. Temporary stores are isolated for the invocation
  and are removed when the runner exits.
- Retention is opt-in before execution with `--retention-root ROOT`, or with
  `RetainedRunSession` / `run_retained_public_analysis` in the Python API.
- A retained run is self-contained at `ROOT/<run_id>/` and has a manifest,
  local artifacts, and a paired `metadata.sqlite` registry. There is no TTL,
  automatic garbage collection, shared reference counting, or automatic replay.
- Retained data is local plaintext storage. F2-A does not add encryption,
  cloud storage, secure erase, access control, or external connectors.
  `delete-run` removes only the selected retained-run directory and reports
  `secure_erase: false`; it never deletes the original external source file.

## Persisted evidence and status

The retained package records the source snapshot, canonical Parquet, structured
intent/request, canonicalization context and record, F1-B declaration and
disclosure, sufficiency, execution, validation, admissibility, ClaimCandidate,
ClaimDecision, AnalysisResult, PublicResponse, rendered response, versions,
fingerprints, and cross-record linkage available to that run.

The manifest lifecycle is fail-closed:

- `temporary`: no persistent audit package is promised;
- `retained_incomplete`: a retained directory exists but finalization is not complete;
- `retained_complete`: the manifest, metadata, artifacts, hashes, linkage, and
  complete marker verify successfully;
- `retention_failed`: persistence or post-write verification failed.

Finalization failure is an analysis/delivery failure: the CLI exits nonzero and
the API raises an explicit retention error. A failed or incomplete package is
never upgraded to `retained_complete`. Persistence records preserve the
existing `USER_DECLARED` authority and do not upgrade it to independently
verified evidence.

## Metadata and operations

The metadata schema is v7. Migration is additive: legacy v6 component stores
gain the v7 retained-run registry but remain legacy/incomplete until a new
self-contained retained run is finalized. No run ID is fabricated for legacy
stores.

The runner supports:

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py \
  --retention-root ./runtime/retained \
  --source ./orders.csv --source-type csv \
  --question-class revenue_change --metric revenue_change \
  --baseline-label "Q3 2026" --baseline-start 2026-07-01 --baseline-end 2026-09-30 \
  --comparison-label "Q4 2026" --comparison-start 2026-10-01 --comparison-end 2026-12-31

python3.11 skills/commerce-lens/scripts/run_public_analysis.py \
  --retention-root ./runtime/retained --list-retained
python3.11 skills/commerce-lens/scripts/run_public_analysis.py \
  --retention-root ./runtime/retained --inspect-run RUN_ID
python3.11 skills/commerce-lens/scripts/run_public_analysis.py \
  --retention-root ./runtime/retained --verify-run RUN_ID
python3.11 skills/commerce-lens/scripts/run_public_analysis.py \
  --retention-root ./runtime/retained --delete-run RUN_ID
```

Inspection and verification do not replay, rerun, or re-render the analysis.
Verification checks the stored manifest, complete marker, artifact hashes,
SQLite integrity/schema, record presence, request/result/response linkage, and
F1-B `USER_DECLARED` linkage.
