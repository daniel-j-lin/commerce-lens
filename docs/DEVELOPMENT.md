# CommerceLens Development Notes

This document keeps developer-oriented setup, invocation, and verification
details separate from the public landing page.

## Python Package Setup

The deterministic CommerceLens runtime requires Python `>=3.11`.

From a clean checkout:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e "."
```

For developer/test verification:

```bash
python -m pip install -e ".[dev]"
```

The repository's existing developer `.venv` is not public installation
authority.

## Public Integration Boundary

The deterministic public execution boundary is:

- `commerce_lens.skill.integration.PublicAnalysisIntent`
- `commerce_lens.skill.integration.PublicSourceSelection`
- `commerce_lens.skill.integration.run_public_analysis`

The native Skill/plugin path constructs this structured intent from supported
natural-language questions and invokes the same boundary through
`skills/commerce-lens/scripts/run_public_analysis.py`.

The current integration expects explicit governed periods, a supported metric,
`GroupingDimension.NONE`, a supported local source selection, and descriptive
claim intent. Unsupported metrics, unsupported grouping, ambiguous period or
mapping authority, and unsupported claim types fail closed.

Missing `available_evidence` or `period_coverage_evidence` is not synthesized
from an intent. The sufficiency gate blocks unsupported claims. The Python
API retains its explicit trusted authority parameters; external declarations use
`coverage_declarations` or CLI `--coverage-declaration` and deterministic validation. The example below demonstrates the API shape and now returns a
governed block without independently supplied evidence.

Positive fixture tests explicitly declare complete Q3/Q4 2026 synthetic exports
using `tests/public_fixture_authority.py`. Runner component tests opt into
`tests/fixture_authority_runner.py`, which supplies that test-only authority at
the existing Python API boundary and runs the real gates. Real CLI regressions
separately verify missing-authority blocking and both retention modes. These
helpers are not a production coverage policy or a supported user entry point.

## Developer Python API Example

This example uses the tracked synthetic CSV at
`examples/public_v0_1/orders.csv`.

```python
from datetime import date
from pathlib import Path

from commerce_lens.contracts.common import PeriodDefinition, SourceType
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.skill.integration import (
    PublicAnalysisIntent,
    PublicQuestionClass,
    PublicSourceSelection,
    run_public_analysis,
)


def q3_2026():
    return PeriodDefinition(
        period_id="baseline",
        label="Q3 2026",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 9, 30),
        date_convention_ref="order_date_utc",
    )


def q4_2026():
    return PeriodDefinition(
        period_id="comparison",
        label="Q4 2026",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 12, 31),
        date_convention_ref="order_date_utc",
    )


source = Path("examples/public_v0_1/orders.csv")
outcome = run_public_analysis(
    PublicAnalysisIntent(
        question_class=PublicQuestionClass.REVENUE_CHANGE,
        metric_id="revenue_change",
        baseline_period=q3_2026(),
        comparison_period=q4_2026(),
        source=PublicSourceSelection(source, SourceType.CSV),
        original_question_text="How did revenue change from Q3 2026 to Q4 2026?",
    ),
    artifact_store=ArtifactStore(Path("runtime/temporary/public_v0_1_demo")),
    metadata_store=MetadataStore(Path("runtime/temporary/public_v0_1_demo.sqlite")),
)

print(outcome.response.render_text())
```

The paired `ArtifactStore`/`MetadataStore` example above is component-store
persistence only. It is not an F2-A finalized Evidence Bundle: a retained
bundle is complete only when its self-contained run manifest, persisted
artifact/record linkages, integrity checks, and final `complete.marker` all
agree. Runs without that finalization state remain visible as incomplete or
failed and must not be treated as retained evidence.

The supported descriptive answer is absolute Revenue Change. CommerceLens v0.3.1
still does not add Revenue Change Percentage, causal conclusions, or
recommendations. It adds one bounded public diagnostic path for the approved
product-composition association only.

## Verification

CommerceLens v0.3.1 release verification records the exact focused and full
suite results from the release verification run. Test counts are evidence from
a specific run, not a permanent contract. Test counts are evidence from a
specific run, not a permanent contract.

Useful focused checks:

```bash
python -m pytest tests/p14
python -m pytest tests/skill/test_native_plugin_packaging.py tests/skill/test_integration.py tests/skill/test_public_response.py tests/end_to_end/test_public_v0_1.py
python -m pytest tests/fixture_runner
python -m pytest tests/application
python -m pytest -p no:cacheprovider tests/docs/test_readme_bilingual_parity.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python validation/p15/scripts/run_p15_preflight.py
python -m pytest
git diff --check
```

## Development Skill Fallback

During local development, a developer may expose only the Skill folder through a
user-level Skill location. That fallback is not the public plugin distribution
path and should not be used as release or marketplace acceptance evidence.

For first use, the bundled Skill may verify Python `>=3.11`, create an isolated
local environment, install this local package, and invoke the deterministic
runner. Do not hide bootstrap failures. If Python or package dependencies cannot
be installed, report the installation/runtime failure. Never respond by having
the LLM calculate material metrics itself.


## F1-B external intake boundary

The owner-approved additive specification is
`docs/amendments/F1-B-coverage-authority-v1.md`. The external versioned model and
validator live in `skill/coverage_intake.py`, with Skill/API/runner integration in
`skill/integration.py`. External fields never select requirement IDs. Projection
supplies only req_global plus PeriodCoverageEvidence; the separate confirmed
canonical mapping/registry input gate supplies only the requested req_metric.
Canonicalization, currency, eligibility, execution and validation remain the
existing gates. Trusted Python callers are unchanged; mixing external and trusted
inputs fails closed.

The availability cutoff is exclusive UTC and the runtime clock is internal. There
is no user-controlled now/as-of flag. Q3/Q4 2026 positive tests explicitly patch
the test clock to 2027-01-03; actual September 2026 execution must block Q4.
The tests execute the actual runner and engine, without fixture authority injection.
Run `.venv/bin/python -m pytest tests/skill/test_coverage_intake.py`.

Confirmation uses the exact `COMPLETENESS_ASSERTION` and
`SOURCE_BASIS_ASSERTION` constants. V1 accepts only the reviewed-export-controls
basis. The host shows that basis inside one complete proposal and normalizes
affirmative language to the canonical confirmation intent; it does not require a
second audit-wording response. Do not convert arbitrary prose or uncertainty
into this assertion. Unsupported basis or uncertainty remains blocked. These
assertions record user-declared coverage, not independent verification. Full
mappings (including IDs) are conservatively bound; even equivalent remapping can
require a new declaration/store. Retained unresolved conflicts block; temporary
runs cannot discover declarations in deleted stores.

## Coverage authority and renderer contract

Mapping authority answers what a source field means. Coverage authority answers
whether the governed periods, population, and filters are complete. Neither
authority substitutes for the other. `PublicCoverageContext` carries reviewed
host facts only into proposal rendering; it is not Evidence. The user-confirmed
proposal creates `USER_DECLARED` authority only after deterministic validation.

`coverage_proposal_fingerprint(...)` binds the complete displayed proposal to
the current source, mapping/eligibility context, scope, periods, cutoff, and
governed assertions. A stale or mismatched fingerprint fails closed. Explicit
timezone offsets canonicalize to UTC; naive timestamps are rejected. The
renderer displays complete known facts once and lists only genuinely missing
facts. It must never manufacture completeness from request dates or observed
dataset dates.

## Canonical, runtime, and installed Skill roles

- `skills/commerce-lens/SKILL.md` is the canonical public plugin instruction.
- `src/commerce_lens/skill/SKILL.md` is the runtime/source distribution copy
  with a more compact role-specific presentation.
- An installed user or isolated Skill is derived distribution state, never the
  place to fix release behavior.

The two repository Skills require behavioral parity for mapping/coverage
separation, consolidated confirmation, `USER_DECLARED` disclosure, cutoff and
missing-fact behavior, proposal binding, temporary/retained routing,
`list`/`inspect`/`verify`,diagnostic routing, execution/refusal behavior, bounded diagnostic rendering, and fail-closed behavior. They do
not need byte-for-byte identity. The deterministic parity test is
`tests/skill/test_skill_distribution_parity.py`.

## Retention lifecycle

The host selects temporary or retained mode before execution. Retained mode
creates the run, persists source and canonical artifacts, writes metadata and
public/result artifacts, validates linkage and hashes from disk, writes the
`retained_complete` manifest, and writes `complete.marker` last. A completion
marker must never precede verified persistence. Failure records a failed state
and returns nonzero; it cannot silently become complete.

`list`, `inspect`, and `verify` operate across processes. Verification checks
persistence integrity and does not replay analysis. Retention does not alter
`ClaimDecision`, source authority, or Metric semantics. Temporary mode creates
no retained run.

## P15 and release verification

P00 is a completed internal protocol rehearsal with zero external participants.
P01 has not been run, and P15 remains NOT PASS. Run preflight with:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  .venv/bin/python validation/p15/scripts/run_p15_preflight.py
```

The release gate also requires focused coverage and retention tests, packaging
and diagnostic execution and refusal regressions, README parity, the complete suite,
`git diff --check`, data-safety review, and an isolated install from the exact
candidate commit.

For the isolated gate, use a clean clone or worktree and a separate
`AUDIT_CODEX_HOME`; never overwrite the developer's configured Codex home or
patch an installed cache directly. Verify plugin version, canonical/installed
Skill and runner hashes, Dataset A temporary and retained behavior, Dataset B
blocking, diagnostic refusal, and absence of a retained run in temporary mode.
Any divergence is fixed in canonical repository source, committed, and retested.
# R7 repository capability and public boundary

# R7 public diagnostic capability

CommerceLens v0.3.1 exposes the approved R7 diagnostic vertical through the
installed public plugin for `product_composition_association` using
`weekly_product_presence_revenue_association@1.0.0`.

The public path is:

`diagnostic_revenue_drop`
→ governed descriptive Revenue Change
→ production R6 hypothesis, evidence, and eligibility checks
→ authenticated `ELIGIBLE_NOT_EXECUTED` handoff
→ approved R7 execution
→ independent validation
→ recursive lineage authentication
→ bounded public explanation.

R6 remains responsible for hypothesis governance, evidence sufficiency,
diagnostic admission, fitness, and pre-test eligibility.

R7 remains responsible for the diagnostic method, execution, independent
validation, and post-test evaluation.

`CRITERION_MET` means only that the predefined diagnostic criterion was met.
It is not causality, a sole or primary cause, statistical significance,
a `ClaimDecision`, a `Finding`, or a recommendation.

If R6 is not eligible, required evidence is missing, or R7 authentication fails,
the public path fails closed and does not produce an authoritative diagnostic
explanation.