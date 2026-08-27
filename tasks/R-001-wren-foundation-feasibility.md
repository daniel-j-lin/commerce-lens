# R-001 — Wren Foundation Feasibility

## Status

COMPLETED / CLOSED

Main Project Decision:

KEEP DUCKDB

Independent Review:

REVIEW CONFIRMED

Production Adoption:

NO

Architecture Amendment:

NOT REQUIRED

The remaining sections preserve the original research specification.

---

## 1. Decision Question

Determine whether Wren Core provides sufficient technical and architectural value to justify:

1. continuing with the current DuckDB execution foundation;
2. partially adapting selected Wren capabilities; or
3. proposing Wren as a candidate replacement/wrapper for selected CommerceLens deterministic execution responsibilities.

This task produces evidence for a later Main Project architecture decision.

It does not authorize adoption.

---

## 2. Background

CommerceLens Phase 1 and Phase 2 are:

APPROVED / FROZEN.

The current Frozen Architecture defines DuckDB as the primary tabular execution engine.

Recent external research identified Wren Core as a potential reusable deterministic semantic/execution foundation.

Wren is currently classified as:

FOUNDATION CANDIDATE

NOT ADOPTED.

The purpose of R-001 is to test this candidate before CommerceLens begins production Metric Registry and Metric execution implementation.

---

## 3. Primary Research Questions

R-001 must answer:

### Q1 — Core Isolation

Can the required Wren semantic / execution capability be used without adopting the complete GenBI, LLM, RAG, UI, or agent platform?

Determine:

- minimum components required;
- required runtime services;
- required processes;
- required dependencies;
- whether an in-process or thin adapter integration is practical;
- whether full Wren platform infrastructure is unavoidable.

### Q2 — Metric Authority

Can CommerceLens remain the sole authority for Metric semantics?

The spike must prove or disprove whether:

CommerceLens Metric Definition
→ adapter
→ Wren compilation/execution

can operate without Wren becoming a second independent Metric authority.

Wren must not be allowed to:

- invent Revenue semantics;
- alter eligibility population;
- infer missing fields;
- infer currency;
- repair duplicate identity;
- change canonical semantics.

### Q3 — Deterministic Numerical Fidelity

For equivalent governed inputs, compare deterministic results for:

- Revenue;
- Orders;
- AOV.

Compare, where technically possible:

CommerceLens reference calculation
vs
current DuckDB execution
vs
Wren execution.

Test:

- numerical equality;
- Decimal fidelity;
- Null vs Zero;
- aggregation behavior;
- distinct-order behavior;
- repeat-run reproducibility;
- result ordering where relevant.

### Q4 — Relationship / Semantic Compilation

Determine whether Wren materially reduces implementation complexity for:

- semantic model compilation;
- product/category relationship handling;
- join-path resolution;
- execution-plan generation;
- SQL compilation.

The spike must use only the minimum relationship model required to test this capability.

Do not build a broad semantic layer.

### Q5 — Execution Provenance

Determine whether Wren execution can expose enough deterministic information for CommerceLens to preserve:

- source identity;
- Metric definition reference;
- execution request;
- generated/compiled query or equivalent operation;
- execution result;
- execution version/context;
- reproducibility.

CommerceLens Evidence Contract remains authoritative.

### Q6 — Decimal / Monetary Fidelity

Evaluate whether Wren preserves exact monetary semantics for CommerceLens-compatible Decimal values.

At minimum evaluate:

- ordinary currency values;
- scale greater than 9;
- large precision values within supported limits;
- multiple-row monetary aggregation;
- source → execution → result fidelity;
- explicit behavior when a value cannot be represented exactly.

Silent precision loss is unacceptable.

Do not invent a CommerceLens requirement for arbitrary 76-digit business values.

Extreme precision tests are engine-conformance tests, not new business requirements.

### Q7 — Dependency / Operational Cost

Measure the minimum dependency and runtime surface required to use Wren.

Record:

- runtime dependencies;
- required services;
- process count;
- installation complexity;
- build complexity;
- native/runtime requirements;
- startup requirements;
- maintenance implications;
- expected repository complexity.

Do not use vague labels such as "lightweight" or "heavy" without evidence.

### Q8 — Adapter Complexity

Determine how much CommerceLens-specific code would be required between:

CanonicalDataset
→ Wren
→ ExecutedResult.

Record:

- files/modules;
- approximate adapter responsibilities;
- transformations;
- semantic translations;
- provenance capture;
- error translation.

The purpose is to determine whether reuse actually reduces implementation complexity.

---

## 4. Narrow Analytical Scope

The spike may test only:

- Revenue;
- Orders;
- AOV;
- one small canonical synthetic dataset;
- one minimal product/category relationship model;
- deterministic execution;
- Decimal semantics;
- provenance;
- reproducibility.

The synthetic data must conform to the Frozen CommerceLens canonical semantics.

The spike may implement temporary reference calculations solely for engine comparison.

These reference calculations are research artifacts.

They are NOT production Metric implementations.

---

## 5. Required Comparison

Where technically possible, produce an explicit comparison:

| Capability | CommerceLens Reference | Current DuckDB | Wren |
| --- | --- | --- | --- |
| Revenue result | | | |
| Orders result | | | |
| AOV result | | | |
| Decimal fidelity | | | |
| Null / Zero behavior | | | |
| Repeatability | | | |
| Provenance accessibility | | | |
| Relationship handling | N/A / baseline | | |
| Dependency surface | | | |
| Adapter complexity | | | |

Do not fill cells without executed evidence.

If a comparison cannot be performed, state:

NOT TESTED

and explain why.

---

## 6. Research Isolation

All R-001 implementation must remain isolated from production CommerceLens code.

Preferred research boundary:

research/wren_foundation/

or an isolated Codex/git worktree.

Do NOT modify production:

- `src/commerce_lens/engine/`
- `src/commerce_lens/metrics/`
- `src/commerce_lens/validation/`
- `src/commerce_lens/evidence/`
- production persistence behavior
- production canonicalization
- production Data Sufficiency

unless a later Main Project-approved task explicitly authorizes adoption.

The main implementation must remain valid without Wren installed.

---

## 7. Explicitly Out of Scope

Do NOT implement or evaluate:

- Wren GenBI product behavior;
- LLM Text-to-SQL;
- RAG;
- vector databases;
- Multi-Agent runtime architecture;
- UI;
- dashboards;
- broad connector support;
- marketplace connectors;
- full database-dialect coverage;
- forecasting;
- causal analysis;
- Recommendation generation;
- Claim admissibility implementation;
- Benchmark scoring;
- production Wren integration.

Do not turn the spike into a Wren tutorial or Wren product demo.

---

## 8. Production Dependency Rule

Do NOT add Wren or spike-specific dependencies to the production `pyproject.toml` during research.

Research dependencies must remain isolated.

If Wren requires environment setup, dependency files may exist only within the research boundary unless Main Project later approves adoption.

---

## 9. Frozen Specification Protection

R-001 must not modify any file under:

docs/frozen/

The spike does not amend Architecture.

If Wren appears superior, the correct result is:

Architecture Amendment Recommended

not:

production architecture silently changed.

---

## 10. Required Evidence

Every material R-001 conclusion must identify its evidence.

Evidence may include:

- exact dependency installation commands;
- inspected Wren component/version;
- source repository/version/commit where available;
- executed test code;
- exact test input;
- exact output;
- generated query / execution representation where available;
- execution timing only when actually measured;
- repeat-run comparison;
- dependency inventory;
- error output;
- adapter code;
- deterministic comparison result.

Do not conclude from README claims alone when executable verification is practical.

---

## 11. Required Research Artifacts

The research implementation should produce, at minimum:

research/wren_foundation/
├── README.md
├── RESULTS.md
├── adapter/
├── tests/
└── fixtures/

Exact internal structure may remain minimal.

### README.md

Must explain:

- environment setup;
- what is being tested;
- how to reproduce the spike;
- what is intentionally excluded.

### RESULTS.md

Must contain factual results only.

It must separate:

- executed evidence;
- observations;
- limitations;
- untested items;
- interpretation.

---

## 12. Required Tests

At minimum evaluate:

### Core usability

- Wren component initializes successfully or the failure is captured.
- minimum required runtime surface is identified.

### Revenue

- deterministic total using governed `line_revenue`.

### Orders

- distinct eligible `order_id`.
- multi-line order counts once.

### AOV

- Revenue / Orders using identical governed population.

### Null / Zero

- zero monetary value remains zero.
- missing monetary value is not silently converted to zero.

### Decimal fidelity

- standard two-decimal values;
- more than 9 fractional digits;
- large supported precision;
- repeated aggregation;
- unsupported precision fails explicitly if applicable.

### Reproducibility

Execute the same test multiple times.

Equivalent governed inputs must produce equivalent material outputs.

### Relationship

Use one minimal product/category relationship only if required to evaluate semantic compilation or relationship resolution.

Do not broaden the model.

---

## 13. No Fake Success

If Wren cannot:

- install;
- isolate;
- execute;
- preserve required semantics;
- expose sufficient provenance;
- maintain reproducibility;

record the failure.

Do not weaken the acceptance criteria to make the candidate pass.

---

## 14. Decision Criteria

R-001 must end in exactly one recommendation:

### KEEP DUCKDB

Recommend when evidence shows that Wren:

- adds excessive dependency/runtime complexity;
- cannot be isolated sufficiently;
- does not improve implementation materially;
- weakens deterministic semantics;
- weakens provenance;
- creates duplicate Metric authority;
- or provides insufficient value relative to current DuckDB architecture.

### PARTIAL ADAPT

Recommend when one or more isolated Wren capabilities provide clear value but full execution-foundation adoption is not justified.

The exact reusable capability must be named.

### ARCHITECTURE AMENDMENT CANDIDATE

Recommend when evidence shows that Wren can materially replace or wrap selected DuckDB execution responsibilities while preserving:

- CommerceLens Metric authority;
- canonical semantics;
- numerical fidelity;
- deterministic validation boundaries;
- provenance;
- reproducibility;
- maintainability.

This outcome does NOT authorize adoption.

It authorizes preparation of an Architecture Amendment proposal only.

---

## 15. Conditions Requiring Main Project Confirmation

Stop and request Main Project review if:

- production source code must be modified to continue;
- Frozen semantics conflict with Wren requirements;
- Wren requires a major platform component outside the research boundary;
- CommerceLens Metric semantics would need to change;
- canonical semantics would need to change;
- production `pyproject.toml` would need to change;
- Docker/server infrastructure appears mandatory for the proposed production architecture;
- a Wren licensing issue affects intended reuse;
- a major unplanned dependency or security concern appears;
- the spike cannot isolate the relevant Wren capability.

Ordinary research debugging does NOT require confirmation.

---

## 16. Definition of Done

R-001 is complete only when:

- Wren Core isolation has been tested;
- minimum dependency/runtime surface is documented;
- Revenue has an executed comparison result;
- Orders has an executed comparison result;
- AOV has an executed comparison result;
- Decimal fidelity has executed evidence;
- reproducibility has been tested;
- execution provenance has been assessed;
- adapter complexity has been assessed;
- limitations and untested items are explicit;
- production code remains unchanged;
- Frozen documents remain unchanged;
- RESULTS.md exists;
- one of the three authorized recommendations is produced.

---

## 17. Required Final Report

The implementation task must report:

A. Wren component/version tested

B. Environment/runtime required

C. Files created

D. Dependencies installed inside the research boundary

E. Core isolation result

F. Revenue comparison

G. Orders comparison

H. AOV comparison

I. Decimal fidelity results

J. Relationship/semantic compilation findings

K. Provenance findings

L. Reproducibility findings

M. Adapter complexity

N. Runtime/dependency cost

O. Test commands and exact results

P. Failures / limitations / untested items

Q. Production files changed, expected:

NONE

R. Frozen files changed, expected:

NONE

S. Final recommendation:

KEEP DUCKDB

or

PARTIAL ADAPT

or

ARCHITECTURE AMENDMENT CANDIDATE

T. Evidence supporting that recommendation

After reporting:

STOP.

Do not begin production integration.

Do not begin Phase 3.
