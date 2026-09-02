# PUBLIC V0.1 INTEGRATION GATE

## Status

APPROVED / FROZEN

Implementation:
COMPLETE

Freeze status:
FROZEN

Main Project Review:
COMPLETE

Approval record:

- task contract was approved for implementation;
- all prior Main Project corrections were satisfied;
- implementation is complete;
- Independent Source Review approved the implementation;
- Independent Runtime / Acceptance Verification accepted the implementation;
  and
- Final Main Project Review approved the gate for freeze.

Final governance record:

- Final Main Project decision:
  `PUBLIC V0.1 INTEGRATION GATE — APPROVED / FROZEN`
- Approved implementation HEAD:
  `72d4e094463134ed9efa7bb2ffd406a41d69c635`
- Authorization baseline:
  `fef87d3d5b08581ebdc1fc25105b41726355da3f`
- Implementation branch:
  `implementation/public-v0.1-integration-gate`
- Implementation decision:
  `COMPLETE`
- Independent Source Review:
  `APPROVE`
- Independent Acceptance:
  `ACCEPT`
- Final Main Project Review:
  `APPROVED FOR FREEZE`
- Acceptance Criteria:
  `40 / 40 applicable criteria satisfied`
- Acceptance-criteria discrepancy resolution:
  `ACCEPTANCE-CRITERIA DISCREPANCY RESOLVED — VERIFIER COUNTING ERROR`

Verification evidence:

- Implementation execution reported:
  - focused Skill tests: 14 passed;
  - Public v0.1 end-to-end: 1 passed;
  - P9 regression: 35 passed;
  - application regression: 21 passed;
  - full repository: 526 passed;
  - `git diff --check`: clean.
- Independent Source Review executed:
  - focused Public v0.1 combined suite: 15 passed;
  - P9 regression: 35 passed;
  - application regression: 21 passed;
  - full repository: 526 passed;
  - `git diff --check`: clean.
- Independent Runtime / Acceptance Verification executed:
  - focused Public v0.1 combined suite: 15 passed;
  - P9 regression: 35 passed;
  - application regression: 21 passed;
  - full repository: 526 passed;
  - `git diff --check`: clean;
  - hostile runtime verification: ACCEPT.
- Final Main Project Review freshly executed:
  - focused Public v0.1 suite: 15 passed.

Full-suite freeze authority comes from independently executed Source Review and
Acceptance evidence over unchanged implementation HEAD
`72d4e094463134ed9efa7bb2ffd406a41d69c635`.

Frozen acceptance summary:

- Revenue controlled runtime path: PASS;
- Orders governed distinct-order behavior: PASS;
- numeric AOV: PASS;
- AOV Orders=0:
  - `MetricState.UNDEFINED`
  - `value=None`
  - `orders_equals_zero`
  - not numeric zero;
- Revenue Change: PASS;
- Killer Demo 1: PASS;
- Killer Demo 2: PASS;
- unsupported Diagnostic Claim:
  - `INADMISSIBLE`
  - `unsupported_claim_type`;
- cross-request/equal-value substitution:
  - fail closed
  - `cross_request_substitution`;
- wrong Revenue Change value:
  - `value_mismatch`
  - no ValidatedResult / Evidence / supported Claim;
- Evidence Summary traceability: PASS;
- source input immutability: PASS;
- no network requirement: PASS.

Frozen analytical authority:

- MetadataStore schema: `v6`
- Supported Metrics: `revenue`, `orders`, `aov`, `revenue_change`
- Current positive Claim permission: `ClaimType.DESCRIPTIVE only`
- Positive Qualified Admissible path: `NONE`
- Public source headline: CSV and XLSX
- SQLite: existing kernel capability retained, not Public v0.1 headline workflow
- Normal analysis operation: `run_analysis(...)`
- Claim evaluation operation: `evaluate_claim(...)`

This freeze does not authorize support for Revenue Change Percentage, Product,
Category, Contribution, ranking, Findings, Alternative Explanations,
Recommendations, positive Diagnostic Claims, causal Claims, predictive Claims,
or prescriptive Claims.

Freeze boundary:

The approved implementation is frozen at
`72d4e094463134ed9efa7bb2ffd406a41d69c635` plus the governance-recording
commit created by this task. The governance commit may change only
`tasks/PUBLIC-V0.1-INTEGRATION-GATE.md` and `PROJECT_STATE.md`. The governance
commit does not alter analytical implementation.

This freeze does not authorize reopening P1-P9, changing the Skill
implementation, changing Metric semantics, changing Evidence semantics,
changing Claim policy, adding new Metrics, adding Product/Category, Revenue
Change Percentage, Findings, Recommendations, CLI work, README work, packaging
work, dependency changes, GitHub release, release documentation, connectors,
network services, MCP, Wren, RAG, Multi-Agent, Vector DB, or P10
implementation.

Release readiness remains separate:

`PUBLIC V0.1 INTEGRATION GATE APPROVED / FROZEN` does not mean
`PUBLIC GITHUB V0.1 RELEASED`.

The next product-delivery governance step is
`PUBLIC V0.1 RELEASE READINESS GATE`.

That future gate must address README, verified installation instructions,
clean-checkout reproducibility, Python/environment setup, public
synthetic/open examples, supported/unsupported question documentation,
limitations, Evidence behavior documentation, refusal behavior documentation,
license review, data-safety review, repository hygiene, and public release
preparation.

Environment limitation:

- System Python observed: `Python 3.8.8`
- Approved existing project `.venv` used for successful verification:
  `Python 3.11.9`
- Project requires Python: `>=3.11`
- Classification: `Release Readiness limitation / setup requirement`
- This is not an Integration Gate failure.

This task is a governance and task-specification gate only. It does not begin
P10 and must not be renamed to P10.

PUBLIC V0.1 INTEGRATION GATE is a milestone inserted between P9 and P10. It
does not renumber P10 or any downstream phase. P10 remains Revenue Change
Percentage unless a separate authorized governance decision changes the
roadmap.

Required repository baseline for this task-specification creation:

- branch: `main`
- starting HEAD: `5ae8d6396d49a0e0824976e0f99ad21a46bea2ff`
- HEAD message: `Record P9 minimum physical fixture runner approval and freeze`
- required working tree: clean

Current approved state:

- P1-P8: APPROVED / FROZEN
- P9-PRE-001: APPROVED / FROZEN
- P9-001: APPROVED / FROZEN
- P9 approved implementation HEAD:
  `ba72e2b658b854b0e45ba51a3273f9e4e5a593bd`
- current full-suite authority: 511 passed
- MetadataStore: v6
- supported Metrics: `revenue`, `orders`, `aov`, `revenue_change`
- current positive Claim permission: `ClaimType.DESCRIPTIVE` only

This task does not authorize changes to P1-P9, Frozen specifications, release
documentation, `README.md`, dependencies, CLI, or public release packaging.

Production integration changes are authorized only within the exact
implementation file scope defined in Section 24.

---

## 1. Purpose

PUBLIC V0.1 INTEGRATION GATE defines the minimum integration layer required for
a clean user to:

1. provide supported commerce/e-commerce structured data;
2. ask a currently supported analytical question;
3. have the Skill form governed structured intent;
4. invoke the frozen CommerceLens application service;
5. mechanically bind authentic `ClaimCandidate` authority;
6. obtain authoritative `ClaimDecision`; and
7. receive a controlled evidence-governed public response.

Central invariant:

```text
The Skill may decide what to ask.
It may not decide what is true.
```

Required conceptual chain:

```text
User natural language
-> Skill / host interpretation
-> governed typed intent
-> deterministic integration validation
-> AnalysisRequest
-> run_analysis(...)
-> AnalysisResult
-> exact authentic authority binding
-> ClaimCandidate
-> evaluate_claim(...)
-> ClaimDecision
-> Public Response Projection
-> Skill rendering
```

The integration layer may construct `AnalysisRequest`. It must not own or
reimplement analytical semantics.

---

## 2. Public Positioning

Public v0.1 must be positioned as bounded commerce/e-commerce structured-data
analysis.

Public v0.1 must not be positioned as generic arbitrary-tabular analytics.

The underlying source is structured business data, but advertised analytical
scope must remain the currently approved commerce/e-commerce Metric and
question set. The frozen kernel must not be reopened to make the product
generic.

---

## 3. Public Source Boundary

Publicly supported source types:

- CSV
- XLSX

Kernel-supported but not advertised as a Public v0.1 workflow:

- SQLite

Deferred source types:

- live databases
- Shopify
- Amazon
- Shopee
- marketplace connectors
- PostgreSQL
- MySQL
- external APIs
- web Evidence

Existing SQLite capability must not be removed.

No network requirement is authorized for Public v0.1.

---

## 4. Metric and Question Boundary

Public v0.1 supports only these Metrics:

- `revenue`
- `orders`
- `aov`
- `revenue_change`

Supported analytical classes:

- single governed-period Revenue
- single governed-period Orders
- single governed-period AOV
- Revenue Change between two explicitly governed comparable periods

Grouping:

- NONE

No new Metric is authorized.

Revenue Change percentage is not authorized.

Product, Category, contribution, ranking, diagnostic positive Claims, causal
Claims, predictive Claims, and prescriptive Claims are out of scope.

---

## 5. Natural-Language Boundary

This task must not authorize:

- a Python natural-language parser;
- keyword or regex heuristics that attempt to infer arbitrary business intent;
- generic natural-language-to-SQL;
- arbitrary Python execution; or
- LLM-generated authority.

The host Skill / LLM owns interpretation of user language.

The deterministic integration layer receives typed governed intent and validates
it fail-closed.

`governed typed intent` is an integration-local transient representation only.
It may carry only the minimum structured interpretation needed to construct or
validate the existing governed request, such as:

- supported question class;
- approved Metric reference;
- period intent;
- approved scope;
- grouping;
- Claim intent;
- source selection; and
- mapping selection.

It is not:

- a new analytical authority;
- a new Metric authority;
- a replacement for `AnalysisRequest`;
- a persistence authority;
- an Evidence entity;
- a numerical result authority;
- a Claim permission authority; or
- a second hand-maintained contract equivalent to existing Pydantic contracts.

The authoritative deterministic execution input remains the existing
`AnalysisRequest`.

The typed-intent representation must not contain:

- Metric formulas;
- calculated values;
- Evidence;
- `ValidatedResult` authority;
- `ClaimDecision` permission; or
- invented business semantics.

The deterministic layer must validate at minimum:

- supported question class;
- approved Metric ID;
- required period authority;
- scope;
- grouping;
- Claim type;
- source authority; and
- mapping authority.

If material ambiguity remains, the integration layer must return clarification
required. It must not invent missing periods, Metrics, scope, grouping, causal
intent, or diagnostic intent.

---

## 6. Period Authority

Periods must be either:

- explicitly supplied by the user; or
- unambiguously established by governed conversational context.

The system must never silently infer a missing comparison period.

Public killer demos must be independently reproducible and therefore use
explicit period/year authority.

Canonical demo wording:

```text
How did revenue change from Q3 2026 to Q4 2026?
```

```text
Why did revenue drop from Q3 2026 to Q4 2026?
```

A demo question whose comparison baseline must be guessed is not authorized.

---

## 7. AnalysisRequest Construction

The integration layer may construct `AnalysisRequest` only from validated typed
intent and authentic current authority.

Metric IDs:

- allowlist from current governed authority.

Metric formulas:

- must never be duplicated.

Periods:

- from validated typed intent.

Public v0.1 single-period requests must reuse the exact already-implemented and
P9-proven single-period `AnalysisRequest` construction semantics.

Future implementation must inspect the current repository read-only before
constructing single-period requests, including the existing P9 single-period
fixture/harness construction and relevant application tests/helpers.

If current approved implementation already establishes an exact single-period
encoding, future implementation must reuse it without semantic modification.

Future implementation must not invent:

- a dummy comparison period;
- a synthetic baseline period;
- silent duplicate-period semantics;
- placeholder comparison semantics;
- a new `AnalysisRequest` field;
- a new period state;
- a new period convention; or
- any alternate single-period encoding not already established by current
  approved implementation.

If the exact current single-period request construction cannot be established
safely from existing production/test authority, implementation must stop and
return to Main Project Review.

`AnalysisRequest` must not be modified merely to make Public v0.1 integration
easier.

Scope:

- approved current scope only.

Grouping:

- NONE.

Dataset ref:

- actual governed registration authority.

Schema version:

- runtime/current authority, never invented by an LLM.

Metric registry version:

- runtime/current authority.

Required Evidence:

- current governed authority.

Original question text:

- context/provenance only, not executable analytical authority.

Automatic arbitrary alias inference is not authorized. If mapping is materially
ambiguous, the integration layer must clarify or fail closed.

---

## 8. Frozen Application Service Requirement

Normal analytical execution must use:

- `run_analysis(...)`

Claim evaluation must use:

- `evaluate_claim(...)`

The Public v0.1 integration layer must not reconstruct these steps as an
alternate pipeline:

- intake
- canonicalization
- sufficiency
- planning
- execution
- validation
- Evidence

P9-PRE remains frozen.

If integration requires changing the frozen application service, implementation
must stop and return to Main Project Review.

---

## 9. ClaimCandidate Ownership

The Skill may propose:

- Claim type;
- Metric target;
- intended proposition; and
- supported semantic meaning.

Authoritative `ClaimCandidate` facts must not be generated by the LLM.

Future implementation must provide a deterministic AUTHORITY BINDER.

Authoritative fields include, as applicable:

- `claimed_value`
- `claimed_metric_state`
- `undefined_reason`
- Evidence refs
- `ValidatedResult` refs
- request ID
- dataset ID
- canonical dataset ID/fingerprint
- population refs/fingerprints
- period refs/roles
- currency
- unit
- execution-derived facts

These fields must be mechanically bound from authentic current kernel
authority.

The AUTHORITY BINDER may mechanically populate only existing schema-valid
`ClaimCandidate` fields from authentic current authority.

It must not:

- calculate Metrics;
- reconstruct values from prose;
- create Evidence;
- create new provenance semantics;
- create new Claim fields;
- create hidden authority inside generic metadata;
- decide Claim admissibility;
- replace `evaluate_claim(...)`; or
- weaken exact-ref provenance.

The Skill still owns the semantic intent of the candidate.

The binder owns only exact authority binding.

The existing P8 evaluator still owns Claim permission.

```text
Skill semantic intent
+
authentic kernel authority
-> complete schema-valid ClaimCandidate
-> evaluate_claim(...)
-> authoritative ClaimDecision
```

`ClaimCandidate != ClaimDecision`

### Capability Classification

| Capability | Formal Classification | Public v0.1 Decision |
| --- | --- | --- |
| Governed Skill orchestration / question boundary | Core | Required Public v0.1 orchestration boundary |
| Integration-local typed intent validation | MVP | Required for Public v0.1; transient and non-authoritative |
| Exact-ref Authority Binder | Core | Required integration control for authentic `ClaimCandidate` authority binding |
| Public Response Projection | MVP | Required Public v0.1 presentation boundary |
| Evidence Summary projection | MVP | Required bounded user-facing Evidence presentation |
| CSV / XLSX public workflow | MVP | Publicly supported in v0.1 |
| SQLite public headline workflow | MVP | Existing MVP source capability remains; not advertised as a primary Public v0.1 workflow |
| automatic arbitrary alias inference | Backlog | Not authorized for Public v0.1; materially ambiguous mappings must clarify or fail closed |
| CLI | MVP | Existing Frozen Architecture capability; deferred as a Public v0.1 prerequisite |
| Product / Category | MVP | Existing broader MVP authority; implementation deferred to current downstream roadmap / P11 and not authorized here |
| positive Diagnostic Claims | Phase 2 | Not authorized for Public v0.1; requires separate future governance and implementation authority |
| RAG / Multi-Agent / Vector DB | Rejected | Rejected for MVP implementation; any separate Research treatment requires its own governance authority |

---

## 10. Exact-Ref Binding Rule

This is a critical requirement.

Authority binding must begin from exact authoritative references returned by
`AnalysisResult` and current persisted authority.

Heuristic authority selection is not authorized, including:

```text
list all records
-> search by Metric name
-> search by matching period
-> choose a plausible record
```

Future implementation must use exact refs whenever current APIs/contracts
provide them.

Cross-request or equal-value substitution must not be permitted.

If current frozen interfaces do not provide enough exact-ref retrieval to build
a `ClaimCandidate` safely, implementation must stop and return to Main Project
Review. Future implementation must not weaken provenance semantics or modify
frozen persistence/application authority without approval.

---

## 11. Proposition Types

For current numeric Valid Metrics:

- `ClaimType.DESCRIPTIVE`
- `ClaimPropositionType.METRIC_VALUE_EQUALS`
- `claimed_value` mechanically bound from authentic governed value

For AOV Undefined:

- `ClaimType.DESCRIPTIVE`
- `ClaimPropositionType.METRIC_STATE_IS`
- `claimed_metric_state`: `UNDEFINED`
- `claimed_value`: NONE
- `undefined_reason`: `orders_equals_zero`

Undefined AOV must not be converted to zero.

---

## 12. ClaimDecision Authority

All material public supported Claims require:

- `evaluate_claim(...)`
- authoritative `ClaimDecision`

Invariant:

```text
NO MATERIAL USER-FACING SUPPORTED CLAIM
WITHOUT AUTHORITATIVE CLAIMDECISION PERMISSION.
```

Current positive permission remains:

- `ClaimType.DESCRIPTIVE` only

Positive Qualified Admissible is not authorized.

`INADMISSIBLE` Claims must never be rendered as supported facts.

No `ClaimDecision` means no supported material Claim.

---

## 13. Public Response Projection

The LLM must not freely transform `AnalysisResult` into an unrestricted answer.

Future implementation may add only a narrow structured Public Response
Projection above the frozen kernel.

The projection must separate at least:

- Metric State
- Claim State
- Public response/support disposition

These are not interchangeable.

Example:

```text
MetricState:
Undefined

ClaimState:
Admissible

Public disposition:
Supported descriptive state

value:
None

undefined_reason:
orders_equals_zero
```

`Undefined` must not be labeled as a ClaimState.

The response projection is not a replacement for kernel authority.

---

## 14. Minimum Public Response Surface

The structured response should support:

- Supported Claims / Answer
- Evidence Summary
- Metric State
- Claim Status
- Limitations
- Unsupported Conclusions
- Additional Evidence Needed, only where it does not imply unsupported causes
- Clarification Required
- Blocked / Insufficient Evidence state

This task must not authorize formal:

- `Finding`
- `AlternativeExplanation`
- `Recommendation`

artifacts.

---

## 15. Evidence Presentation

User-facing Evidence Summary may expose bounded useful information such as:

- Metric;
- definition/version where useful;
- period;
- scope;
- governed value/state;
- validation status;
- Evidence status;
- Claim status;
- source filename/type; and
- material limitations.

Raw internal UUIDs/fingerprints must not be dumped by default.

Full provenance remains internally preserved.

---

## 16. Insufficient Evidence

Preserve this exact phrase where governed failure requires it:

```text
Insufficient evidence to conclude.
```

Data Quality failure:

- no speculative answer.

Data Sufficiency failure:

- no speculative answer.

Validation failure:

- no material Claim.

Evidence inadmissible:

- no material supported Claim.

Claim inadmissible:

- explicitly refuse the stronger conclusion.

Failure must not be softened into unsupported analytical explanation with terms
such as:

- likely
- probably
- seems
- could be because

---

## 17. Partial Completion

Independent Metric states must not be collapsed.

Example:

```text
Orders:
Valid = 0

AOV:
Undefined
value None
orders_equals_zero
```

One supported Metric may be rendered even if another independent Metric is
blocked, where current frozen application authority allows it.

---

## 18. Diagnostic Partial-Support Behavior

For this question:

```text
Why did revenue drop from Q3 2026 to Q4 2026?
```

The system must separate:

SUPPORTED:

- whether Revenue declined and by how much.

UNSUPPORTED:

- why it declined.

Expected logical behavior:

```text
descriptive Revenue Change Claim
-> authoritative ADMISSIBLE

diagnostic explanation Claim
-> INADMISSIBLE
-> unsupported_claim_type
```

Public response must preserve:

```text
Insufficient evidence to conclude why Revenue declined.
```

Future implementation must not invent or leak unsupported causes including:

- promotion
- seasonality
- competition
- traffic
- inventory
- demand
- customer behavior
- market causes
- other possible causes

`Additional Evidence Needed` may state only that an approved diagnostic workflow
and relevant diagnostic Evidence would be required. It must not present possible
causes as candidate explanations.

---

## 19. Skill Boundary

Future `SKILL.md` owns:

- workflow;
- question-boundary instructions;
- clarification behavior;
- structured intent production;
- application invocation guidance;
- Claim intent formulation;
- refusal behavior; and
- response rendering behavior.

Future `SKILL.md` must not duplicate:

- Revenue formula;
- Orders formula;
- AOV formula;
- Revenue Change formula;
- validation rules;
- Evidence rules; or
- Claim permission logic.

Skill orchestrates.

Kernel determines.

---

## 20. CLI and Installation Boundary

CLI remains permitted by broader Frozen Architecture.

CLI is not a Public v0.1 Integration Gate prerequisite.

This task must not implement CLI and must not remove CLI from broader roadmap
authority.

This task may establish the Skill/package integration boundary required for
local use.

This task must not perform GitHub release packaging or documentation work.

This task must not modify `README.md`.

This task must not invent an install command unless current packaging authority
has been separately inspected and authorized.

GitHub release work remains a later gate.

---

## 21. Public Source Mapping

Future implementation must not assume automatic arbitrary column-alias
inference.

Initial public examples should use either:

- governed canonical-compatible columns; or
- explicitly authorized mapping.

Materially ambiguous mapping must clarify or fail closed.

Hidden semantic repair is not authorized.

---

## 22. Exact Killer Demo 1 Acceptance

Question:

```text
How did revenue change from Q3 2026 to Q4 2026?
```

Future implementation must prove:

- supported source accepted;
- explicit periods preserved;
- Metric = `revenue_change` only;
- grouping = NONE;
- `run_analysis(...)` called;
- governed deterministic result returned;
- validation passes;
- `AdmissibleEvidence` exists;
- `ClaimCandidate` mechanically bound from exact authentic authority;
- `evaluate_claim(...)` called;
- ClaimState = ADMISSIBLE;
- public response renders governed Revenue Change;
- Evidence Summary corresponds to authentic authority;
- no Revenue Change percentage;
- no diagnostic explanation; and
- no Recommendation.

---

## 23. Exact Killer Demo 2 Acceptance

Question:

```text
Why did revenue drop from Q3 2026 to Q4 2026?
```

Future implementation must prove both:

DESCRIPTIVE PORTION:

- Revenue decline/change is established through the governed chain where
  Evidence supports it.

DIAGNOSTIC PORTION:

- `ClaimType.DIAGNOSTIC`
- `ClaimState.INADMISSIBLE`
- failure: `unsupported_claim_type`

Public response must communicate:

- supported descriptive Revenue change; and
- `Insufficient evidence to conclude why Revenue declined.`

No unsupported cause may leak into the public response.

---

## 24. Future Implementation File Scope

This approved task specification locks the exact implementation scope authorized
by Main Project Review.

Implementation is authorized only within the production, test, and example
scope defined below.

Only this minimum production file scope may be created or modified during this
approved implementation:

- `src/commerce_lens/skill/__init__.py`
- `src/commerce_lens/skill/SKILL.md`
- `src/commerce_lens/skill/integration.py`
- `src/commerce_lens/skill/public_response.py`

Only this focused test scope may be created or modified during this approved
implementation:

- `tests/skill/test_integration.py`
- `tests/skill/test_public_response.py`
- `tests/end_to_end/test_public_v0_1.py`

Only this public integration example / synthetic asset location may be created
or modified:

- `examples/public_v0_1/`

Only minimal synthetic/public-safe files required to demonstrate or test the
approved Public v0.1 behavior may be created there. Unrelated examples and
benchmark corpus expansion are not authorized.

Protected by default:

- `src/commerce_lens/application/`
- `src/commerce_lens/contracts/`
- `src/commerce_lens/metrics/`
- `src/commerce_lens/engine/`
- `src/commerce_lens/validation/`
- `src/commerce_lens/evidence/`
- `src/commerce_lens/persistence/`
- `docs/frozen/`
- `pyproject.toml`
- `README.md`

Any production or contract file outside the authorized implementation scope
requires stop and Main Project Review before modification.

Future implementation must not expand file scope merely because a change
appears convenient.

If current package installation is materially impossible without packaging
changes, future implementation must stop and request Main Project Review rather
than pre-authorizing packaging changes.

---

## 25. Implementation Acceptance Criteria

Future implementation may be considered complete only if all applicable
requirements pass:

1. P1-P9 remain unchanged except where a separately approved governance update
   explicitly records later status.
2. Frozen specifications remain unchanged.
3. Public v0.1 supports only `revenue`, `orders`, `aov`, and
   `revenue_change`.
4. Positive Claim permission remains `ClaimType.DESCRIPTIVE` only.
5. Positive Qualified Admissible behavior is not introduced.
6. CSV supported path passes.
7. XLSX supported path passes.
8. Existing SQLite kernel capability remains intact but is not required as a
   headline Public v0.1 workflow.
9. No new Metric semantics are introduced.
10. No new canonical semantics are introduced.
11. Single-period request construction reuses exact existing approved/P9-proven
    semantics.
12. No dummy or invented period encoding is introduced.
13. `run_analysis(...)` remains the only normal analytical application
    boundary.
14. `evaluate_claim(...)` remains the Claim evaluation authority.
15. Integration performs no Metric arithmetic.
16. Integration does not duplicate Data Sufficiency, validation, Evidence
    admissibility, or Claim admissibility.
17. Typed governed intent remains transient integration-local state and does
    not become a second analytical contract authority.
18. AUTHORITY BINDER mechanically populates only existing schema-valid
    `ClaimCandidate` fields.
19. Exact-ref binding uses authentic current authority.
20. Heuristic selection of plausible records is not used where exact references
    exist.
21. Cross-request and equal-value substitution remain fail-closed.
22. No material supported user-facing Claim appears without authoritative
    `ClaimDecision`.
23. `INADMISSIBLE` Claims cannot leak into Supported Claims / Answer.
24. AOV Orders=0 remains `MetricState.UNDEFINED`, value `None`, and not numeric
    zero.
25. Independent Metric states remain independently renderable.
26. Public response performs no new material arithmetic.
27. Public Evidence Summary corresponds to authentic kernel authority.
28. Killer Demo 1 passes.
29. Killer Demo 2 passes.
30. Unsupported Diagnostic / Predictive / Causal / Prescriptive conclusions
    remain visibly refused or bounded.
31. No unsupported cause leaks through speculative wording.
32. No network requirement is introduced.
33. No new runtime/framework dependency is added.
34. MetadataStore remains v6.
35. P9 regression remains passing.
36. Full repository regression remains passing.
37. `git diff --check` is clean.
38. Only explicitly authorized implementation files are created or modified.
39. Input source immutability remains preserved.
40. No GitHub release is performed by this implementation task.

Implementation completion is not the same as Public GitHub v0.1 release
authorization.

`Undefined != failure != numeric zero`

---

## 26. Future Test Requirements

Future implementation must require tests for at least:

- CSV Revenue supported;
- CSV Orders supported;
- CSV numeric AOV supported;
- Revenue Change supported;
- XLSX equivalent supported path;
- AOV Orders=0 remains Undefined / None;
- Demo 1;
- Demo 2 descriptive-support + diagnostic-refusal;
- forecast rejected;
- recommendation rejected;
- Product/Category rejected;
- Revenue Change percentage rejected;
- ambiguous period requires clarification;
- ambiguous mapping clarifies/fails closed;
- missing governed data produces no supported Claim;
- validation failure produces no supported Claim;
- inadmissible Evidence produces no supported Claim;
- inadmissible ClaimDecision cannot leak as supported response;
- `ClaimCandidate` exact-ref binding;
- cross-request/equal-value authority substitution still rejected;
- partial Metric states render independently;
- public response performs no Metric arithmetic;
- Evidence Summary corresponds to authentic authority;
- no network requirement;
- input source immutable;
- P9 regression remains passing; and
- complete repository regression remains passing.

This task does not require actual GitHub release documentation.

---

## 27. Public v0.1 Release Readiness Gate

Completion of the Public v0.1 integration implementation does not authorize
Public GitHub release.

Before Public v0.1 may be released, a separate release-readiness review must
confirm at minimum:

- fresh complete repository regression pass;
- P9 regression pass;
- Public v0.1 integration test pass;
- clean-checkout reproducibility;
- supported CSV example;
- supported XLSX example;
- synthetic or appropriately licensed public-safe data only;
- verified installation instructions against actual packaging authority;
- README setup instructions;
- README supported question list;
- README unsupported question list;
- known limitations;
- Evidence behavior explanation;
- refusal behavior explanation;
- public Evidence traceability demonstration;
- license review;
- public-data safety review;
- no private/proprietary/customer data;
- clean repository state; and
- GitHub-ready repository hygiene.

`README.md` and release-documentation changes remain outside the current
integration implementation authorization. They require a later explicit
release-readiness / release task authorization.

Do not invent a new P-number for this release gate.

PUBLIC V0.1 INTEGRATION GATE is a milestone inserted between P9 and P10 and
does not renumber P10 or later phases.

---

## 28. Out of Scope

This task must not implement or authorize:

- Revenue Change percentage;
- Product;
- Category;
- Contribution;
- ranking;
- diagnostic positive Claims;
- causal Claims;
- predictive Claims;
- prescriptive Claims;
- Findings;
- AlternativeExplanation;
- Recommendation;
- generic NL-to-SQL;
- arbitrary Python;
- external Evidence;
- connectors;
- REST API;
- server;
- frontend;
- dashboard;
- CLI;
- RAG;
- LangChain;
- LangGraph;
- MCP;
- Multi-Agent;
- Vector DB;
- Wren;
- Decision Reliability Benchmark scoring; or
- generic arbitrary-tabular analytics.

---

## 29. Stop Conditions

Future implementation must stop for Main Project Review if it requires:

- Frozen specification change;
- Metric semantic change;
- canonical semantic change;
- Data Sufficiency change;
- validation change;
- Evidence admissibility change;
- ClaimDecision policy change;
- new Metric;
- MetadataStore v7;
- new runtime/framework dependency;
- application-service redesign;
- material `AnalysisRequest` / `AnalysisResult` redesign;
- new automatic mapping semantics;
- LLM-generated Evidence refs/fingerprints;
- heuristic authority selection where exact authority is required;
- unsupported Claims leaking despite Inadmissible decision;
- P9 regression failure;
- full regression failure; or
- generic arbitrary-tabular expansion.

---

## 30. Governance Lifecycle

Required lifecycle:

```text
Task specification created
-> Main Project Review
-> corrections if required
-> APPROVED FOR IMPLEMENTATION / NOT FROZEN
-> implementation
-> source review
-> independent verification
-> APPROVED / FROZEN
```

Initial task status:

PROPOSED / NOT AUTHORIZED

Final lifecycle record:

Implementation:

COMPLETE

Final task status:

APPROVED / FROZEN

Freeze status:

FROZEN
