# CommerceLens AI

CommerceLens AI is an evidence-driven commerce and e-commerce analytical
decision-support system. Material analytical claims must pass governed,
deterministic Evidence and ClaimDecision authority before they can be presented
as supported.

Its core principle is:

```text
No material claim without traceable evidence.
```

In practice, CommerceLens can refuse unsupported conclusions instead of filling
evidence gaps with plausible language.

## Current Public v0.1 Scope

Public v0.1 supports structured Python invocation of the CommerceLens Skill
integration over local structured data files.

Supported sources:

- CSV
- XLSX

Supported Metrics:

- Revenue
- Orders
- AOV
- Revenue Change

Supported positive material Claim type:

- Descriptive only

The host or caller is responsible for interpreting a user question into a
structured `PublicAnalysisIntent`. The current Public v0.1 integration validates
that intent, constructs the governed request, executes the frozen application
service, evaluates ClaimDecision authority, and projects a public response. It
does not provide a CLI, GUI, REST endpoint, hosted chatbot, or general Python
natural-language parser.

## Current Limitations

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

## Requirements

- Python >=3.11

Public v0.1 has been verified with environment-independent Python behavior on a
local Python 3.11 environment. This README does not claim operating-system
certification for Windows, macOS, or Linux.

## Installation

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

## Quick Start

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
percentage, causal explanation, or Recommendation.

## Public v0.1 Invocation

The supported public boundary is structured Python invocation through:

- `commerce_lens.skill.integration.PublicAnalysisIntent`
- `commerce_lens.skill.integration.PublicSourceSelection`
- `commerce_lens.skill.integration.run_public_analysis`

The current integration expects explicit governed periods, a supported Metric,
`GroupingDimension.NONE`, a supported local source selection, and descriptive
Claim intent. It validates unsupported Metrics, unsupported grouping, ambiguous
period or mapping authority, and unsupported Claim types fail-closed.

## Supported Examples

The public examples are in `examples/public_v0_1/`:

- `orders.csv` demonstrates Revenue, Orders, numeric AOV, Revenue Change, the
  supported descriptive answer, and the diagnostic refusal demo.
- `aov_undefined.csv` demonstrates AOV Undefined when Orders equals zero.
- `orders.xlsx` demonstrates the XLSX source path with the same synthetic order
  shape as `orders.csv`.

The examples use identity canonical columns with explicit eligibility status:
`paid` rows are eligible and `cancelled` rows are excluded.

## Evidence-Governed Behavior

Conceptually, the Public v0.1 path is:

```text
Question / governed intent
-> deterministic execution
-> validation
-> Evidence
-> ClaimDecision
-> public response
```

A public Evidence Summary makes traceability readable without requiring users
to inspect raw runtime identifiers. It includes the Metric, governed period,
MetricState, Evidence status, ClaimState, source filename, source type, and
validation status.

## Killer Demo 1

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

## Killer Demo 2

Question:

```text
Why did revenue drop from Q3 2026 to Q4 2026?
```

Expected Public v0.1 behavior:

- the supported descriptive decline/change may be shown;
- the diagnostic explanation is refused.

The required bounded refusal is:

```text
Insufficient evidence to conclude why Revenue declined.
```

## AOV Undefined

When Orders equals zero, AOV is not zero. It is governed as:

```text
Undefined
```

The public state includes `MetricState=Undefined`, value `None`, and
`undefined_reason=orders_equals_zero`.

## Reproducibility / Tests

Current release-candidate verification on this implementation branch was run on
2026-09-02 with Python 3.11.9 and produced:

- Public v0.1 focused tests: 15 passed
- P9 fixture runner: 35 passed
- application tests: 21 passed
- full repository tests: 526 passed

To run the verification suite from an environment installed with `.[dev]`:

```bash
python -m pytest tests/skill/test_integration.py tests/skill/test_public_response.py tests/end_to_end/test_public_v0_1.py
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

## License

CommerceLens AI is licensed under the Apache License 2.0. See `LICENSE`.

SPDX identifier:

```text
Apache-2.0
```

## Release Status

Package version:

```text
0.1.0
```

Current implementation/release-readiness state on this branch:

```text
NOT YET PUBLICLY RELEASED
```

Future approved tag identity:

```text
v0.1.0
```

No Git tag, GitHub Release, PyPI publication, hosted service, or public release
action is created by this release-readiness implementation.
