# PUBLIC V0.1 RELEASE READINESS GATE

## 1. Status

Status:

APPROVED FOR IMPLEMENTATION / NOT FROZEN

Implementation:

NOT STARTED

Freeze status:

NOT FROZEN

Main Project Review:

COMPLETE

Release Decision:

NOT STARTED

This task specification authorizes future Release Readiness implementation only
within the exact approved future implementation file scope. It does not
authorize packaging edits, source changes, tests, GitHub release creation, Git
tags, pushes, public release actions, or P10 work.

## 2. Purpose

This task defines the governance and verification requirements that must be
satisfied before CommerceLens Public v0.1 may be considered eligible for a
public GitHub release decision.

Governing principle:

```text
No material claim without traceable evidence.
```

For Release Readiness, this principle applies to software release claims. The
project must not claim easy installation, reproducibility, public safety,
supported environment, GitHub readiness, data safety, documented functionality,
or license readiness without repository evidence and deterministic verification.

Release Readiness answers this question:

```text
Can a clean user obtain CommerceLens from the public repository, establish the
supported environment, run the approved Public v0.1 workflow, reproduce the
governed examples, understand the supported/unsupported boundary, inspect
Evidence behavior, and avoid relying on undocumented developer-machine
assumptions?
```

Release Readiness is a delivery and governance layer above the frozen
analytical kernel and the frozen Public v0.1 Skill integration. It must not
change analytical truth authority.

## 3. Authoritative Baseline

Repository inspected:

```text
/Users/linruixin/Desktop/commercelens skills/project 1
```

Required branch:

```text
main
```

Observed branch:

```text
main
```

Expected current main HEAD:

```text
e1e3db95be190fa8d4980afabee64909b04f5987
```

Observed current HEAD:

```text
e1e3db95be190fa8d4980afabee64909b04f5987
```

Observed recent log:

```text
e1e3db9 (HEAD -> main, implementation/public-v0.1-integration-gate) Freeze Public v0.1 integration gate
72d4e09 Implement Public v0.1 integration gate
fef87d3 Authorize Public v0.1 integration gate implementation
5ae8d63 Record P9 minimum physical fixture runner approval and freeze
ba72e2b (implementation/p9-001-minimum-physical-fixture-runner) Seal P9 hostile fixture authority
52a0a55 Close P9 fixture authority gaps
9671b60 Implement P9 minimum physical fixture runner
0355a06 Authorize P9 minimum physical fixture runner implementation
d940ed2 Align P9 fixture runner with frozen application service
6688e82 Record P9 public application service approval and freeze
2ac5d1c (implementation/p9-pre-001-application-service) Close P9 application service authority gaps
fc0de54 Implement P9 public application service foundation
38ce8a5 Authorize P9 public application service implementation
235df3a Correct P9 application service contract boundaries
e6cde33 Define P9 public application service prerequisite
```

Observed working tree before task-spec creation:

```text
## main
```

No tracked changes were present before this task-specification file was
created.

## 4. Current Frozen Product State

The current authoritative state recorded in `PROJECT_STATE.md` and
`tasks/PUBLIC-V0.1-INTEGRATION-GATE.md` is:

- P1-P9: APPROVED / FROZEN.
- Public v0.1 Integration Gate: APPROVED / FROZEN.
- Public v0.1 Integration implementation: COMPLETE.
- Public v0.1 Integration approved implementation HEAD:
  `72d4e094463134ed9efa7bb2ffd406a41d69c635`.
- Public v0.1 Integration governance freeze commit:
  `e1e3db95be190fa8d4980afabee64909b04f5987`.
- Independent Source Review: APPROVE.
- Independent Runtime / Acceptance Verification: ACCEPT.
- Final Main Project Review: APPROVED FOR FREEZE.
- Public v0.1 Integration Acceptance Criteria: 40 / 40 satisfied.
- MetadataStore: v6.
- Current supported Metrics:
  `revenue`, `orders`, `aov`, `revenue_change`.
- Positive Claim permission:
  `ClaimType.DESCRIPTIVE` only.
- Positive Qualified path: NONE.
- Post-freeze full suite: 526 passed.
- Public v0.1 Release Readiness: NOT STARTED.
- P10: Revenue Change Percentage, NOT STARTED.

The Public v0.1 Integration Gate is complete and must not be reopened by this
Release Readiness task unless a specific implementation defect or governing
conflict is discovered and escalated through Main Project Review.

## 5. Release Readiness Definition

Public v0.1 Release Readiness means:

```text
Frozen analytical kernel
+ Frozen Public v0.1 Skill integration
+ verified clean-user setup
+ public documentation
+ public-safe examples
+ reproducibility proof
+ license/data-safety review
+ repository hygiene
= eligible for Public GitHub v0.1 release decision
```

Release Readiness does not mean:

- publicly released;
- GitHub Release created;
- tag created;
- PyPI-ready;
- marketplace-ready;
- production SaaS-ready;
- solution validated;
- product-market fit proven.

Implementation complete, Integration frozen, Release ready, Publicly released,
and Solution validated are separate governance states.

Recommended future terminal state before actual release action:

```text
READY FOR PUBLIC RELEASE / NOT YET RELEASED
```

This terminology is now approved by Main Project Review as the successful
pre-release readiness state.

## 6. Clean User Definition

A clean user is a user who:

- starts from a fresh checkout or clean clone-like state at an approved commit;
- does not have or use the developer's existing `.venv`;
- does not rely on `/Users/linruixin/...` or any other local absolute path;
- does not rely on hidden environment variables;
- does not rely on runtime artifacts from previous executions;
- does not rely on shell aliases;
- does not rely on undeclared packages;
- follows only public documented setup and usage instructions;
- uses a supported Python interpreter documented by Release Readiness;
- uses only files included in the repository or files generated by documented
  steps;
- starts from explicitly controlled runtime directories and metadata state.

This definition is testable. Clean-checkout verification must use it directly.

## 7. Release Scope

Public v0.1 release readiness is scoped to public GitHub repository release
readiness only.

Supported public source headlines:

- CSV.
- XLSX.

Supported analytical scope:

- single governed-period Revenue;
- single governed-period Orders;
- single governed-period AOV;
- Revenue Change between two explicitly governed comparable periods.

Supported Metrics:

- `revenue`;
- `orders`;
- `aov`;
- `revenue_change`.

Supported grouping:

- `GroupingDimension.NONE` only.

Positive material Claim permission:

- `ClaimType.DESCRIPTIVE` only.

The current Public v0.1 Integration intentionally does not implement a general
natural-language parser. Public documentation must not imply arbitrary
free-form natural language analytics beyond actual Skill/host behavior.

Minimum public user journey:

```text
GitHub repository
-> verified setup
-> CommerceLens Skill/integration available
-> user provides supported CSV/XLSX
-> user provides bounded question or governed structured intent
-> frozen application service
-> ClaimDecision
-> evidence-governed response
```

## 8. Analytical Freeze Boundary

This task must not authorize or perform analytical expansion.

The following remain frozen:

- Metric semantics;
- canonical semantics;
- Data Sufficiency semantics;
- validation semantics;
- Evidence Contract semantics;
- Claim policy;
- application service analytical behavior;
- Public Response analytical semantics;
- MetadataStore schema v6;
- positive Claim permission limited to `ClaimType.DESCRIPTIVE`;
- supported Public v0.1 Metrics limited to `revenue`, `orders`, `aov`,
  `revenue_change`.

This task does not authorize:

- Revenue Change Percentage;
- Product;
- Category;
- Contribution;
- ranking;
- Findings;
- Alternative Explanations;
- Recommendations;
- positive Diagnostic Claims;
- causal Claims;
- predictive Claims;
- prescriptive Claims;
- new Evidence semantics;
- new canonical semantics;
- new MetadataStore schema.

## 9. Environment / Python Boundary

Observed environment evidence:

- System `python --version`: `Python 3.8.8`.
- Existing project `.venv/bin/python --version`: `Python 3.11.9`.
- `pyproject.toml` declares `requires-python = ">=3.11"`.
- Existing `.venv/pyvenv.cfg` records:
  `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m venv /Users/linruixin/Documents/project 1/.venv`.
- Existing editable install metadata in the current `.venv` points at
  `file:///Users/linruixin/Documents/project%201`.
- Direct import using the existing `.venv` from the authoritative repository
  failed without `PYTHONPATH=src`:
  `ModuleNotFoundError: No module named 'commerce_lens'`.
- Import with `PYTHONPATH=src` and the existing `.venv` succeeded and reported
  `commerce_lens.__version__ == "0.1.0"`.

Release Readiness must distinguish developer-machine environment from
documented clean-user installation requirements.

The existing `.venv` is not public release authority. Public users must not be
instructed to rely on it, copy it, or infer setup from it.

Release Readiness must document and verify an explicit supported Python
version or supported Python version range. It must not claim cross-platform
support unless cross-platform setup and workflow verification are actually
executed.

## 10. Installation Authority

Observed packaging configuration in `pyproject.toml`:

- build backend: `hatchling.build`;
- build requirement: `hatchling>=1.25`;
- project name: `commerce-lens`;
- project version: `0.1.0`;
- readme: `README.md`;
- Python requirement: `>=3.11`;
- runtime dependencies:
  - `duckdb>=1.0,<2`;
  - `openpyxl>=3.1,<4`;
  - `pydantic>=2.7,<3`;
  - `PyYAML>=6,<7`;
- dev dependency:
  - `pytest>=8,<9`.

Clean-copy packaging probe:

- Source used: `git archive HEAD` at
  `e1e3db95be190fa8d4980afabee64909b04f5987`.
- Probe location: `/tmp/commercelens-clean-audit.3o6BqT`.
- Python used:
  `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11`.
- Command shape verified:
  `python -m venv`, `python -m pip install --upgrade pip`,
  `python -m pip install -e "<clean-copy>[dev]"`.
- Result: editable install succeeded.
- Result: `import commerce_lens` succeeded.
- Result: installed/imported version reported `0.1.0`.

Installation authority decision for this proposed task:

```text
Current packaging appears sufficient for a Python 3.11 clean-copy editable
install path, but README documentation is stale and the checked-out developer
.venv is not authoritative.
```

README setup commands may only use commands that are verified against the
repository packaging. Invented commands are prohibited.

Possible future outcomes:

1. Current packaging sufficient:
   - documentation and verification only;
   - `pyproject.toml` remains protected.
2. Packaging documentation only required:
   - README may document the verified clean install path.
3. Narrow packaging correction required:
   - STOP for Main Project Review before authorizing `pyproject.toml`.
4. Packaging blocker requiring Main Project Review:
   - Release Readiness implementation may not silently fix or bypass it.

## 11. Packaging Decision Boundary

`pyproject.toml` is protected for the future Release Readiness implementation
unless a clean-checkout install blocker is reproduced and recorded with exact
evidence.

Evidence threshold required before `pyproject.toml` may be authorized:

- a clean checkout or archive of the approved baseline;
- supported Python interpreter;
- documented install command;
- exact error output;
- proof the failure is caused by project packaging rather than user
  environment, network outage, stale venv, or command typo;
- Main Project Review approval of the exact proposed packaging edit.

No arbitrary dependency additions are authorized by this task. No new
analytical dependency or framework may be introduced without governance
approval.

## 12. README Requirements

Observed current README state:

- `README.md` exists.
- It is stale relative to the frozen current state.
- It states the repository is governed through P7-001 APPROVED / FROZEN.
- It states the post-P7 state includes MetadataStore schema v5 and 398 passed
  tests.
- It states ClaimDecision, Evaluation Fixtures runner, `SKILL.md`, and related
  features do not yet exist.
- These statements conflict with the current `PROJECT_STATE.md` and frozen
  Public v0.1 Integration Gate state.

Minimum README requirements for Public v0.1:

- what CommerceLens is;
- what CommerceLens is not;
- evidence-first positioning;
- supported Python version or version range;
- verified setup commands;
- verified invocation/use path;
- supported input formats;
- supported Metrics;
- supported question examples;
- unsupported question examples;
- expected Evidence/refusal behavior;
- AOV Undefined behavior;
- limitations;
- currently unsupported features;
- example workflow;
- reproducibility/testing instructions;
- data-safety statement;
- license status;
- no public claims beyond verified functionality.

README truthfulness rule:

Every README/public claim must correspond to one of:

- current frozen product behavior;
- actual verified installation behavior;
- actual executed test result;
- clearly labeled limitation;
- clearly labeled future roadmap item.

README must not claim:

- production readiness;
- enterprise readiness;
- arbitrary AI analytics;
- causal analysis;
- broad e-commerce platform integrations;
- benchmark superiority;
- proven user trust improvement;
- market validation;
- commercial reliability;

unless separately supported by evidence.

README must not become marketing overclaim.

## 13. Public Example Requirements

Observed current examples:

- `examples/public_v0_1/orders.csv` exists.
- The file is a small synthetic-looking CSV with two rows:
  - Q3 2026 revenue 120.00 USD;
  - Q4 2026 revenue 100.00 USD.
- This CSV can support Revenue Change decline demonstrations in principle.
- No tracked XLSX public example was observed.
- No tracked public AOV Undefined example file was observed.
- Most current Public v0.1 demo data is generated inside tests with `tmp_path`,
  not provided as public user-facing examples.

Minimum public examples required:

- single-period Revenue;
- single-period Orders;
- numeric single-period AOV;
- Revenue Change;
- Killer Demo 1;
- Killer Demo 2 with diagnostic refusal;
- AOV Undefined with Orders = 0;
- refusal behavior for unsupported analytical conclusions.

Preferred minimum public assets:

- keep or update `examples/public_v0_1/orders.csv` for Revenue, Orders,
  numeric AOV, Revenue Change, Killer Demo 1, and Killer Demo 2;
- add a minimal AOV Undefined CSV only if the existing CSV cannot demonstrate
  Orders = 0 without confusing the primary demo;
- add a minimal XLSX example or deterministic documented generation step for
  XLSX only if release verification proves the XLSX public path from the
  repository;
- document exact questions/intents and expected bounded outputs.

Do not create a large public example corpus. Do not expose internal fixture
complexity unnecessarily.

## 14. Public Data Safety

Release Readiness must prove that public examples and public documentation use
only:

- synthetic data; or
- properly licensed public data with explicit license authority.

The release must not include:

- customer data;
- employer/company confidential data;
- private URLs;
- proprietary scraping outputs;
- API keys;
- secrets;
- personally identifying data unless explicitly licensed and required,
  preferably none;
- local machine paths in public documentation or artifacts;
- hidden runtime artifacts.

Before release, the repository must be scanned and manually reviewed for public
data safety.

## 15. License Boundary

Observed license state:

- No `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `COPYING`, or `NOTICE` file was
  found at repository depth inspected.
- `pyproject.toml` does not declare a license field.
- README does not resolve license terms.

LICENSE GOVERNANCE DECISION:

```text
License governance: RESOLVED
Approved license: Apache License 2.0
```

Future Release Readiness implementation may create exactly `LICENSE` using the
standard, unmodified Apache License 2.0 license text.

Do not create custom license terms. Do not dual-license. Do not add
commercial-use restrictions. The `LICENSE` file is authorized only because this
Main Project governance decision explicitly resolves the license choice.

## 16. Repository Hygiene

Observed hygiene state:

- `.gitignore` exists.
- It ignores `.venv/`, `venv/`, `env/`, `__pycache__/`, `*.py[cod]`,
  `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, runtime generated
  directories, `.env`, `.env.*`, `*.secret`, `*.key`, `.DS_Store`, IDE/editor
  directories, build artifacts, dist artifacts, egg-info, and
  `CommerceLens_*_Main_Project_Review*.zip`.
- Tracked runtime directories contain `.gitkeep` files only.
- Ignored local artifacts currently observed include `.venv/`, `.pytest_cache/`,
  `.DS_Store`, many `__pycache__/` directories, local review ZIP files, and
  `.DS_Store` files under docs/runtime/src/tests.
- No `.github/` directory was observed.

Release Readiness must verify:

- no tracked local runtime artifacts;
- no untracked public-release-relevant files accidentally omitted or included;
- `.venv` is not relied on or committed;
- caches are ignored and not required;
- SQLite runtime files are ignored and not required;
- generated artifacts are excluded unless explicitly public assets;
- temporary files are absent from tracked release state;
- IDE/editor files are absent from tracked release state;
- OS metadata is absent from tracked release state;
- stale task drafts or review ZIPs are not part of public release artifacts;
- private data and large accidental files are absent from tracked release
  state.

Do not automatically delete files during Release Readiness task-spec creation
or implementation. Hygiene findings must be recorded and resolved through the
authorized file scope or escalated.

## 17. Secrets / Local-Path Safety

Observed tracked scan:

- A tracked-content scan for `/Users/linruixin`, `/private/tmp`,
  `Documents/project`, `Desktop/commercelens`, `API key`, `token`, `password`,
  `secret`, `PRIVATE KEY`, `BEGIN RSA`, and `connection string` found no
  obvious secret material in tracked release files.
- Matches for "secret" were limited to `.gitignore` patterns and frozen
  architecture guidance about excluding secrets.

Release Readiness must perform a narrow deterministic release check for:

- API keys;
- tokens;
- passwords;
- connection strings;
- private keys;
- credentials;
- secrets;
- private endpoints;
- personal data;
- absolute local filesystem paths.

The check should combine simple deterministic repository scans with manual
review. Do not add an elaborate security framework unless Main Project Review
finds it necessary.

## 18. Supported / Unsupported Public Contract

Public v0.1 must communicate this supported contract:

- CSV;
- XLSX;
- `revenue`;
- `orders`;
- `aov`;
- `revenue_change`;
- descriptive material Claims only;
- explicit governed periods;
- grouping `NONE`;
- evidence-governed response projection.

Public v0.1 must communicate these unsupported boundaries:

- generic arbitrary-tabular analysis;
- Revenue Change Percentage;
- Product / Category analysis;
- contribution/ranking;
- forecasts;
- positive diagnostic explanations;
- causal inference;
- Recommendations;
- marketplace connectors;
- network services;
- hosted SaaS;
- Docker;
- PyPI publication;
- REST API;
- cloud hosting;
- marketplace packaging.

GitHub-ready does not mean marketplace-ready.

## 19. Evidence Traceability Demo

Release Readiness must require a minimum public demonstration of:

```text
Question
-> governed request or structured intent
-> result
-> Evidence status
-> Claim status
-> safe response
```

The public demo must make traceability visible without dumping raw internal
UUIDs by default.

Minimum public Evidence Summary fields:

- Metric name and metric id;
- governed period label and role;
- MetricState;
- Evidence status;
- ClaimState;
- source filename;
- source type;
- validation status or equivalent public-readable confirmation;
- limitation/refusal text where applicable.

The demo must not invent Evidence, reformat unsupported conclusions as
supported, or expose raw internal storage details as a substitute for a
public-readable explanation.

## 20. Refusal Demo

Release Readiness must preserve Killer Demo 2:

Question:

```text
Why did revenue drop from Q3 2026 to Q4 2026?
```

Required behavior:

- supported descriptive Revenue Change portion may proceed;
- diagnostic conclusion must be refused;
- `ClaimType.DIAGNOSTIC` remains unsupported for positive permission;
- no speculative cause leakage.

Required bounded message:

```text
Insufficient evidence to conclude why Revenue declined.
```

Prohibited candidate-cause leakage includes examples such as promotions,
seasonality, competition, traffic, inventory, demand, advertising, pricing, or
assortment unless a future governed diagnostic workflow is separately approved.

## 21. AOV Undefined Demo

Release Readiness must require a public demonstration of:

```text
Orders = 0
-> AOV Undefined
-> value None
-> undefined_reason orders_equals_zero
```

Required behavior:

- MetricState is `UNDEFINED`;
- public disposition is a supported descriptive state, not a numeric value;
- ClaimState may be admissible for the state proposition;
- AOV is never represented as `0` when Orders equals zero.

## 22. Clean-Checkout Reproducibility

Clean-checkout verification must prove, from a fresh checkout or clean
clone-like state:

- approved commit identity;
- clean repository state;
- supported OS assumptions, if any;
- supported Python version;
- virtual environment creation;
- dependency installation from documented authority;
- package/module import;
- Skill/integration invocation;
- CSV public example;
- XLSX public example or explicitly governed XLSX generation step;
- Killer Demo 1;
- Killer Demo 2;
- AOV Undefined;
- focused Public v0.1 tests;
- P9 regression;
- application regression;
- full repository regression or explicitly approved release verification suite;
- `git diff --check`;
- clean final git status except explicitly expected ignored runtime artifacts.

Do not claim cross-platform support unless verified. Do not require CI
expansion unless Main Project Review finds local reproducibility insufficient
for Public v0.1.

Clean-checkout verification must start from explicitly controlled state and
must block reliance on:

- `/Users/linruixin/...`;
- developer-specific paths;
- existing local `.venv`;
- cached artifacts;
- previously registered runtime metadata;
- untracked files;
- shell aliases;
- undeclared packages;
- local environment variables;
- pre-existing databases;
- manually prepared state not documented for users.

## 23. Version / Tag / Release Identity

Observed version configuration:

- `pyproject.toml` declares `version = "0.1.0"`.
- `src/commerce_lens/__init__.py` declares `__version__ = "0.1.0"`.
- No Git tag was created by this task.
- No GitHub Release was created by this task.

RELEASE IDENTITY GOVERNANCE DECISION:

```text
Package version: 0.1.0
Future Git tag: v0.1.0
Future GitHub Release title: CommerceLens v0.1.0
Approved successful pre-release state: READY FOR PUBLIC RELEASE / NOT YET RELEASED
```

The package version already exists in current packaging and must not be
changed. Package version `0.1.0` is not evidence that a Git tag already exists.
Future tag `v0.1.0` is not evidence that a GitHub Release already exists.
`READY FOR PUBLIC RELEASE / NOT YET RELEASED` is not `PUBLICLY RELEASED`.

Release Readiness implementation must not create the Git tag, create the GitHub
Release, push, publish the repository, or publish to PyPI. Actual release
remains a later explicit release action.

## 24. CI Decision

Observed CI state:

- No `.github/` directory was observed.
- No GitHub Actions workflow was observed.

CI classification for this proposed task:

```text
Useful but optional unless Main Project Review determines that local
clean-checkout reproducibility is insufficient for Public v0.1 release
confidence.
```

Do not add GitHub Actions automatically. If CI becomes required, a separate
exact file-scope authorization is required before implementation.

## 25. Capability Classification

Formal Classification uses exactly one project taxonomy value per row. Release
Readiness Decision is separate from Formal Classification.

| Capability | Formal Classification | Release Readiness Decision |
| --- | --- | --- |
| README public documentation | MVP | Required before release |
| Clean-checkout reproducibility | MVP | Required before release |
| Verified install instructions | MVP | Required before release |
| Python environment documentation | MVP | Required before release |
| Public synthetic examples | MVP | Required before release |
| Evidence traceability demo | MVP | Required before release |
| Refusal demo | MVP | Required before release |
| AOV Undefined demo | MVP | Required before release |
| License resolution | MVP | Resolved as Apache License 2.0; `LICENSE` required before readiness passes |
| Public-data safety review | MVP | Required before release |
| Repository hygiene | MVP | Required before release |
| Secret/path scan | MVP | Required before release |
| Git tag | MVP | Future tag `v0.1.0`, final release action only |
| GitHub Release | MVP | Future title `CommerceLens v0.1.0`, separately authorized |
| CI | Backlog | Useful but optional unless Main Project Review requires it |
| Docker | Backlog | Not required for Public v0.1 |
| PyPI | Backlog | Out of scope unless separately approved |
| Hosted API | Backlog | Out of scope |
| Marketplace packaging | Backlog | Out of scope |
| Revenue Change Percentage | Phase 2 | P10, not part of Release Readiness |
| Product / Category analysis | Phase 2 | Out of scope for Public v0.1 |
| Forecasting | Phase 3 | Out of scope |
| Causal/diagnostic analytics expansion | Phase 3 | Out of scope |
| Solution Validation experiment | Research | Out of scope |

## 26. Future Implementation File Scope

This section proposes the exact future file scope for a later authorized
Release Readiness implementation. This task-specification creation authorizes
none of these edits now.

### A. Ordinary Release Readiness implementation files

Authorized ordinary future Release Readiness implementation files after
implementation authorization:

- `README.md`
- `examples/public_v0_1/README.md`
- `examples/public_v0_1/orders.csv`
- `examples/public_v0_1/aov_undefined.csv`
- `examples/public_v0_1/orders.xlsx`

These are the complete ordinary implementation file scope for Release
Readiness. The implementation agent must not modify its own governing contract.

### B. Governance-resolved Release Readiness license file

- `LICENSE`

`LICENSE` is authorized only under the now-approved Apache License 2.0
governance decision. Future Release Readiness implementation may create exactly
`LICENSE` using the standard, unmodified Apache License 2.0 license text.

### C. Later governance-recording files — NOT ordinary implementation scope

- `tasks/PUBLIC-V0.1-RELEASE-READINESS-GATE.md`
- `PROJECT_STATE.md`

These files may be modified only during a later separately authorized
governance recording / final Release Readiness decision step. They must not be
modified during ordinary Release Readiness implementation.

The later governance step may use these files only to record items such as:

- implementation status;
- source review result;
- clean-checkout verification result;
- final Release Readiness decision;
- approved release identity;
- resolved license status;
- acceptance evidence;
- READY FOR PUBLIC RELEASE state;
- subsequent release status.

### D. Protected Files Unless Separately Authorized

Protected files unless a STOP condition triggers Main Project Review and exact
new authorization:

- `pyproject.toml`
- `.gitignore`
- `.github/`
- `src/**`
- `tests/**`
- `docs/frozen/**`
- `tasks/PUBLIC-V0.1-INTEGRATION-GATE.md`
- `tasks/P3-001-metric-registry-population-plan.md`
- `tasks/P4-001-revenue-orders-aov-reference-execution.md`
- `tasks/P5-001-revenue-orders-aov-deterministic-validation.md`
- `tasks/P6-001-narrow-evidence-admissibility.md`
- `tasks/P7-001-revenue-change-vertical-slice.md`
- `tasks/P8-001-claim-decision-foundation.md`
- `tasks/P9-PRE-001-public-application-service-foundation.md`
- `tasks/P9-001-minimum-physical-fixture-runner.md`
- `COMMERCE_LENS_PROJECT_GOALS_AND_ROADMAP_P7_2026-09-01.md`
- `decisions/**`
- `runtime/**`

If future implementation discovers that a protected file must change for
Release Readiness, implementation must stop and seek Main Project Review with
the exact file path, exact reason, and exact evidence. Do not silently broaden
the file scope.

If clean-user installation cannot be reproduced using current packaging:

`STOP -> Main Project Review`

Do not automatically modify `pyproject.toml`.

## 27. Implementation Acceptance Criteria

1. Public v0.1 Integration Gate remains APPROVED / FROZEN.
2. No analytical semantics are changed.
3. Supported Public v0.1 Metrics remain exactly `revenue`, `orders`, `aov`,
   and `revenue_change`.
4. Positive material Claim permission remains `ClaimType.DESCRIPTIVE` only.
5. Clean-checkout setup succeeds from an approved commit.
6. Supported Python version is documented and verified.
7. No workflow relies on the developer `.venv`.
8. Dependency installation succeeds from documented authority.
9. Package/module import succeeds without `PYTHONPATH` hacks unless such path
   setup is explicitly documented as the verified installation mode.
10. Public invocation path is reproducible.
11. CSV supported example succeeds.
12. XLSX supported example succeeds.
13. Revenue example succeeds.
14. Orders example succeeds.
15. Numeric AOV example succeeds.
16. AOV Undefined example succeeds.
17. Revenue Change example succeeds.
18. Killer Demo 1 succeeds.
19. Killer Demo 2 succeeds.
20. Diagnostic refusal is preserved.
21. No unsupported causal or diagnostic leakage appears in public responses.
22. Evidence Summary is public-readable and traceable.
23. README setup commands execute successfully.
24. README supported-question statements are accurate.
25. README unsupported-question statements are accurate.
26. README limitations are accurate.
27. No private, proprietary, employer, customer, or confidential data exists in
   public assets.
28. No secrets are present.
29. No developer absolute paths remain in public-facing files.
30. Standard unmodified Apache License 2.0 `LICENSE` exists before Release
   Readiness can pass.
31. Repository hygiene passes.
32. `.gitignore` behavior is appropriate for release-readiness artifacts.
33. Runtime/generated files are excluded appropriately.
34. No new analytical dependency or framework is introduced without authority.
35. No network requirement is introduced.
36. P9 regression passes.
37. Application regression passes.
38. Public v0.1 focused tests pass.
39. Complete repository regression passes.
40. `git diff --check` passes.
41. Clean checkout remains clean after documented setup/test workflow except
   explicitly expected ignored runtime artifacts.
42. Package version remains `0.1.0`; future release identity is Git tag
   `v0.1.0`, GitHub Release title `CommerceLens v0.1.0`, and successful
   readiness state `READY FOR PUBLIC RELEASE / NOT YET RELEASED`.
43. Release documentation does not overclaim solution validation.
44. Implementation does not create Git tag `v0.1.0`, create GitHub Release
   `CommerceLens v0.1.0`, push, publish the repository, or publish to PyPI.
45. Only authorized Release Readiness implementation files are changed; the task
   specification and `PROJECT_STATE.md` are not ordinary implementation files,
   and `pyproject.toml` remains unchanged.
46. Current README stale P7/P8/P9/Public v0.1 statements are corrected without
   marketing overclaim.
47. Existing public examples are either verified as synthetic/public-safe or
   replaced with verified synthetic public examples.
48. Public examples avoid exposing internal fixture complexity unless needed for
   reproducibility.
49. The Apache License 2.0 governance decision is recorded as resolved before
   any public release action; no custom, dual, restricted, or other license
   terms are used.
50. Existing local `.venv` editable metadata pointing outside the authoritative
   repository is not used as release evidence.
51. Public documentation distinguishes Skill/host structured intent from a
   nonexistent general Python natural-language parser.
52. P10 remains Revenue Change Percentage and is not started.

All claimed test counts must be actual execution results from the future
implementation or verification, not inherited assumptions.

## 28. Verification Requirements

Future Release Readiness verification must include:

- documentation-command verification;
- clean environment/bootstrap verification;
- clean-checkout or clean-archive workflow;
- supported Python verification;
- dependency installation verification;
- package import verification;
- synthetic CSV execution;
- synthetic XLSX execution;
- Killer Demo 1;
- Killer Demo 2;
- AOV Undefined;
- Evidence Summary inspection;
- refusal behavior inspection;
- input immutability where applicable;
- secret/path scan;
- public-data safety review;
- license status review;
- file-scope review;
- P9 regression;
- application regression;
- Public v0.1 focused tests;
- full repository regression;
- `git diff --check`;
- final `git status --short --branch`.

Suggested minimum command families, to be made exact during future
implementation:

- `git status --short --branch`;
- `git rev-parse HEAD`;
- supported Python `--version`;
- `python -m venv`;
- `python -m pip install -e ".[dev]"`;
- package import/version check;
- public example execution commands or documented Python snippets;
- focused Public v0.1 pytest selection;
- P9 regression pytest selection;
- application regression pytest selection;
- full `python -m pytest`;
- deterministic `rg` scans for secrets and local absolute paths;
- `git diff --check`.

Do not create tests now. Future test additions are not authorized by this
proposed scope unless Main Project Review expands the exact file scope.

## 29. Release Decision Boundary

Release Readiness implementation completion is not public release
authorization.

Required lifecycle:

```text
Release Readiness task specification
-> Main Project Review
-> corrections
-> APPROVED FOR IMPLEMENTATION / NOT FROZEN
-> Release Readiness implementation
-> Source Review
-> Independent clean-checkout/runtime verification
-> Final Release Readiness Review
-> READY FOR PUBLIC RELEASE / NOT YET RELEASED
-> separate explicit Public Release action
```

The implementation task must not create a Git tag, create a GitHub Release,
publish to PyPI, publish to any marketplace, push, or otherwise release the
project unless a separate explicit final Release Decision authorizes the exact
action.

## 30. Out of Scope

The following are out of scope:

- P10 Revenue Change Percentage;
- Product/Category;
- Contribution;
- ranking;
- Findings;
- Alternative Explanations;
- Recommendations;
- diagnostic analytics expansion;
- causal inference;
- forecasting;
- new data connectors;
- Shopify/Amazon/Shopee integration;
- PostgreSQL/MySQL integration;
- REST API;
- frontend;
- dashboard;
- hosted service;
- PyPI unless separately approved;
- Docker unless justified and approved;
- cloud deployment;
- marketplace submission;
- MCP;
- external executor;
- Wren production;
- RAG;
- Multi-Agent;
- Vector DB;
- Benchmark scoring;
- Solution Validation experiment.

This Release Readiness Gate is between frozen Public v0.1 Integration and
public release. It is not P10. P10 remains Revenue Change Percentage and must
not be renumbered or begun by this task.

## 31. Stop Conditions

STOP for Main Project Review if Release Readiness requires or discovers:

- Metric change;
- canonical change;
- Data Sufficiency change;
- validation change;
- Evidence Contract change;
- Claim policy change;
- application-service redesign;
- Public Response semantic redesign;
- new supported Metric;
- positive new Claim type;
- MetadataStore v7;
- new major runtime dependency;
- new network requirement;
- arbitrary alias inference;
- packaging architecture redesign;
- production source modification;
- security-sensitive credential handling;
- license choice inconsistent with Apache License 2.0 governance authority;
- unsupported public claim;
- inability to reproduce from clean checkout;
- inability to establish a legitimate installation path;
- need to edit `pyproject.toml`;
- need to edit `.gitignore`;
- need to add `.github/`;
- need to edit `src/**`;
- need to edit `tests/**`;
- need to modify frozen specs or prior frozen task records;
- any repository-state discrepancy that makes release evidence unreliable.

Do not silently solve governance blockers.

## 32. Governance Lifecycle

This task may proceed only through explicit governance authorization.

Current state:

```text
PUBLIC V0.1 RELEASE READINESS GATE
Status: APPROVED FOR IMPLEMENTATION / NOT FROZEN
Implementation: NOT STARTED
Freeze status: NOT FROZEN
Main Project Review: COMPLETE
```

The Public v0.1 Integration Gate remains approved and frozen. This task must
not reopen P1-P9, alter analytical truth authority, or begin P10.

Before any public GitHub release, the project must complete:

- Main Project Review of this task specification;
- authorized Release Readiness implementation;
- source review;
- independent clean-checkout/runtime verification;
- final Release Readiness review;
- explicit separate release decision.

Only after that separate release decision may release actions such as tagging,
GitHub Release creation, or publishing be performed.
