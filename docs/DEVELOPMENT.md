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

The supported answer is absolute Revenue Change. Public v0.1.3 does not add a
percentage, causal explanation, or recommendation.

## Verification

Current v0.1.3 verification evidence recorded in the README describes a
specific 2026-09-04 Python 3.11.9 run, including a full repository suite result
of `601 passed`. Test counts are evidence from that verification run, not a
permanent contract.

Useful focused checks:

```bash
python -m pytest tests/p14
python -m pytest tests/skill/test_native_plugin_packaging.py tests/skill/test_integration.py tests/skill/test_public_response.py tests/end_to_end/test_public_v0_1.py
python -m pytest tests/fixture_runner
python -m pytest tests/application
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
