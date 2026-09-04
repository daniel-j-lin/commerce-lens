# CommerceLens

## Evidence-Governed Analytics Agent Skill

Turn commerce data into validated, traceable analytical claims, and refuse conclusions the evidence cannot support.

Core principle:

```text
No material claim without traceable evidence.
```

CommerceLens is an evidence-governed commerce analytics Agent Skill. Material
analytical claims must pass governed, deterministic Evidence and ClaimDecision
authority before they can be presented as supported.

## What Makes CommerceLens Different?

CommerceLens focuses on evidence-governed analytical judgment rather than
treating generated answers or executed queries as sufficient authority.

| Typical AI analytics behavior | CommerceLens |
| --- | --- |
| Produces an answer from available data | Defines required Evidence before supporting a Claim |
| Executed query may be treated as sufficient | Separates executed results from validated results |
| Plausible explanations may be generated | Refuses unsupported diagnostic or causal explanations |
| Metrics may be interpreted ad hoc | Uses governed metric definitions |
| Correlation may leak into causal language | Makes Claim type and admissibility explicit |
| Answer is primary output | Returns Claim, Evidence, status, and limitations |

## Public v0.1 Capabilities

Public v0.1 supports a native Codex Skill/plugin workflow over local
structured data files. The Skill interprets supported natural-language business
questions into structured intent, then invokes the deterministic CommerceLens
runtime. The deterministic runtime remains the sole authority for material KPI
values, Evidence, and ClaimDecision outcomes.

Supported inputs:

- CSV with canonical columns or an explicitly confirmed source-to-canonical mapping
- XLSX with canonical columns or an explicitly confirmed source-to-canonical mapping

Supported Metrics:

- Revenue
- Orders
- AOV
- Revenue Change

Supported positive material Claim scope:

- descriptive claims only

Governed behaviors:

- AOV remains Undefined when Orders equals zero;
- unsupported why or diagnostic questions are refused;
- Revenue Change is absolute change only;
- Revenue Change Percentage is not supported in Public v0.1;
- non-canonical column mappings are proposed for user confirmation and are
  validated deterministically before analysis.

The host or caller is responsible for interpreting a user question into a
structured `PublicAnalysisIntent`. The current Public v0.1 integration validates
that intent, constructs the governed request, executes the frozen application
service, evaluates ClaimDecision authority, and projects a public response.

## Governed Refusal Example

Question:

```text
Why did revenue drop from Q3 2026 to Q4 2026?
```

Expected Public v0.1 behavior:

- the supported descriptive decline/change may be shown;
- the unsupported diagnostic explanation is refused.

The required bounded refusal is:

```text
Insufficient evidence to conclude why Revenue declined.
```

## Quick Start

### Requirements

- Python >=3.11

Public v0.1 has been verified with environment-independent Python behavior on a
local Python 3.11 environment. This README does not claim operating-system
certification for Windows, macOS, or Linux.

### Install as a Codex plugin

CommerceLens includes a minimal native Codex skills-only plugin package:

- `.agents/plugins/marketplace.json`
- `.codex-plugin/plugin.json`
- `skills/commerce-lens/SKILL.md`
- `skills/commerce-lens/scripts/run_public_analysis.py`

The repository marketplace exposes the existing plugin root, and the plugin
manifest exposes the local Skill directory with:

```json
"skills": "./skills/"
```

Add this repository as a Codex marketplace source, install the `commerce-lens`
plugin from that marketplace, then start a fresh Codex session:

```bash
codex plugin marketplace add daniel-j-lin/commerce-lens
codex plugin marketplace list
codex plugin add commerce-lens --marketplace commerce-lens
```

If you are testing a local checkout instead of GitHub distribution, add the
local repository root as the marketplace source:

```bash
codex plugin marketplace add .
codex plugin add commerce-lens --marketplace commerce-lens
```

After installation, restart or reload Codex if your surface requires it. Once
the bundled Skill is discovered in a fresh session, ask CommerceLens a supported
Public v0.1 question and provide a CSV or XLSX file.

Supported first-run questions include:

```text
How did revenue change from Q3 2026 to Q4 2026?
Why did revenue drop from Q3 2026 to Q4 2026?
What was AOV in Q4 2026?
```

On first use, the bundled Skill may verify Python >=3.11, create an isolated
local environment, install this local package, and invoke the deterministic
runner. Do not treat manual construction of `PublicAnalysisIntent` as the
end-user Skill workflow for v0.1.2.

### Standalone Skill fallback for local development

During local development, a developer may expose only the Skill folder through a
user-level Skill location. That fallback is not the public plugin distribution
path and should not be used as acceptance evidence for repository marketplace
packaging.

### Deterministic runner surface

The deterministic runner command surface is:

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py \
  --source examples/public_v0_1/orders.csv \
  --source-type csv \
  --question-class revenue_change \
  --metric revenue_change \
  --baseline-label "Q3 2026" \
  --baseline-start 2026-07-01 \
  --baseline-end 2026-09-30 \
  --comparison-label "Q4 2026" \
  --comparison-start 2026-10-01 \
  --comparison-end 2026-12-31 \
  --original-question "How did revenue change from Q3 2026 to Q4 2026?"
```

This command is intended for the Skill/agent orchestration layer. It translates
already-interpreted structured arguments into the existing governed
`run_public_analysis(...)` integration. It does not calculate Revenue, Orders,
AOV, or Revenue Change itself. The runner automatically creates temporary
`ArtifactStore` and `MetadataStore` locations for the governed run and returns
the public response plus a `validated_results_summary` derived from CommerceLens
validation records.

When source headers differ from the CommerceLens canonical schema, the Skill may
propose a source-to-canonical mapping and must ask the user to confirm or
correct it. Confirmed mappings can be handed to the deterministic runner as JSON
without renaming or editing the source file:

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py \
  --source path/to/orders.csv \
  --source-type csv \
  --question-class revenue_change \
  --metric revenue_change \
  --baseline-label "Q3 2026" \
  --baseline-start 2026-07-01 \
  --baseline-end 2026-09-30 \
  --comparison-label "Q4 2026" \
  --comparison-start 2026-10-01 \
  --comparison-end 2026-12-31 \
  --mapping-json '{"Order ID":"order_id","Order Line ID":"order_line_id","Order Date":"order_date","Product ID":"product_id","Quantity":"quantity","Revenue":"line_revenue","Currency":"currency","Order Status":"eligibility_status"}'
```

The JSON object maps source field names to canonical field names. The runner
constructs the existing `CanonicalMapping`, and the deterministic
`validate_mapping(...)` authority must pass before governed analysis proceeds.

### Install Python package for development

From a clean checkout, create an isolated environment and install the package:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e "."
```

For developer/test verification, install the test extra:

```bash
python -m pip install -e ".[dev]"
```

The repository's existing developer `.venv` is not required and is not public
installation authority.

### Developer Python API Example

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

for evidence in outcome.response.evidence_summary:
    print(evidence)
```

The supported answer is the absolute Revenue Change. Public v0.1 does not add a
percentage, causal explanation, or Recommendation. This Python API remains
available for development and tests; it is not the primary end-user Skill UX.

## Evidence Model

Conceptually, the Public v0.1 path is:

```text
Business Question
-> Metric Definition
-> Required Evidence
-> Data Sufficiency
-> Analysis Plan
-> Deterministic Execution
-> Deterministic Validation
-> Evidence
-> ClaimDecision
-> Controlled Response
```

The deterministic public execution boundary is:

- `commerce_lens.skill.integration.PublicAnalysisIntent`
- `commerce_lens.skill.integration.PublicSourceSelection`
- `commerce_lens.skill.integration.run_public_analysis`

The native Skill/plugin path constructs this structured intent from supported
natural-language questions and invokes the same boundary through
`skills/commerce-lens/scripts/run_public_analysis.py`.

The current integration expects explicit governed periods, a supported Metric,
`GroupingDimension.NONE`, a supported local source selection, and descriptive
Claim intent. It validates unsupported Metrics, unsupported grouping, ambiguous
period or mapping authority, and unsupported Claim types fail-closed.

Core distinctions:

```text
Executed Result != Validated Result
Validated Result != Admissible Evidence
Admissible Evidence != ClaimDecision
```

A public Evidence Summary makes traceability readable without requiring users
to inspect raw runtime identifiers. It includes the Metric, governed period,
MetricState, Evidence status, ClaimState, source filename, source type, and
validation status.

## Supported / Unsupported Scope

Public v0.1 is not primarily:

- generic Chat with CSV
- generic Text-to-SQL
- dashboard generation
- arbitrary natural-language analytics
- causal analysis
- forecasting
- recommendations
- SaaS
- enterprise production platform
- a full e-commerce analytics platform

Public v0.1 does not currently support:

- Revenue Change Percentage
- Product / Category analysis
- contribution / ranking
- positive diagnostic explanation
- causal inference
- forecasting
- Recommendations
- arbitrary generic tabular analytics
- marketplace connectors
- hosted SaaS
- REST API
- production cloud service

SQLite exists in the lower-level kernel, but it is not the primary Public v0.1
workflow.

## Supported Examples

The public examples are in `examples/public_v0_1/`:

- `orders.csv` demonstrates Revenue, Orders, numeric AOV, Revenue Change, the
  supported descriptive answer, and the diagnostic refusal demo.
- `aov_undefined.csv` demonstrates AOV Undefined when Orders equals zero.
- `orders.xlsx` demonstrates the XLSX source path with the same synthetic order
  shape as `orders.csv`.

The examples use identity canonical columns with explicit eligibility status:
`paid` rows are eligible and `cancelled` rows are excluded.

### Revenue Change

Question:

```text
How did revenue change from Q3 2026 to Q4 2026?
```

Expected Public v0.1 behavior:

- absolute Revenue Change can be supported when the source and governed periods
  provide sufficient evidence;
- Revenue Change Percentage is not produced;
- no causal explanation is produced;
- no Recommendation is produced.

With `examples/public_v0_1/orders.csv`, Q3 2026 Revenue is 120.00 USD and Q4
2026 Revenue is 100.00 USD, so the supported absolute Revenue Change is -20.00
USD.

### AOV Undefined

When Orders equals zero, AOV is not zero. It is governed as:

```text
Undefined
```

The public state includes `MetricState=Undefined`, value `None`, and
`undefined_reason=orders_equals_zero`.

## Reproducibility / Tests

Current v0.1.2 release verification was run on 2026-09-04 with Python 3.11.9
in a fresh local venv and produced:

- P12 explicit schema mapping UX tests: 10 passed
- P11 input robustness characterization tests: 34 passed
- native Skill packaging and integration tests: 26 passed
- full repository tests: 582 passed

To run the verification suite from an environment installed with `.[dev]`:

```bash
python -m pytest tests/skill/test_native_plugin_packaging.py tests/skill/test_integration.py tests/skill/test_public_response.py tests/end_to_end/test_public_v0_1.py
python -m pytest tests/fixture_runner
python -m pytest tests/application
python -m pytest
git diff --check
```

Test counts are evidence from a specific verification run, not a permanent
contract.

## Data Safety

The public example files are synthetic. Do not commit secrets, private customer
data, confidential employer data, API keys, credentials, private URLs, or local
runtime artifacts.

CommerceLens Public v0.1 does not claim enterprise security certification.

## License / Release Status

CommerceLens is licensed under the MIT License. See `LICENSE`.

Copyright:

```text
Copyright (c) 2026 Jui-Hsin (Daniel) Lin
```

SPDX identifier:

```text
MIT
```

Package version:

```text
0.1.2
```

Public release:

```text
CommerceLens v0.1.2
```

Git tag:

```text
v0.1.2
```

CommerceLens v0.1.2 adds explicit source-to-canonical schema mapping
confirmation to the existing Public v0.1 governed analytics workflow.

CommerceLens is not currently published to PyPI and does not provide a hosted
SaaS product, REST API, or production cloud service.
