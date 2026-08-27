# CommerceLens AI Evidence Contract Specification

**Document:** `EVIDENCE_CONTRACT_SPECIFICATION.md`  
**Version:** v1.0  
**Status:** Approved  
**State:** Frozen  
**Date:** 2026-08-20

---

## 1. Document Purpose

This specification defines the product-level Evidence Contract governing how CommerceLens analytical claims become admissible outputs.

The governing rule is:

> No material claim without traceable evidence.

This is an enforceable product rule. A material claim must not be presented, treated, or relied upon as an admissible CommerceLens analytical output unless its required evidence chain exists, is traceable, and satisfies every applicable requirement in this specification.

The Evidence Contract defines:

- what evidence must exist;
- which relationships must remain traceable;
- what makes a claim admissible, qualified, or inadmissible;
- what execution and validation information is required;
- how Data Sufficiency, assumptions, limitations, contradictions, failures, and partial completion affect evidence validity;
- how Findings, Alternative Explanations, and Recommendations relate to evidence; and
- the minimum completeness required for a material output.

The contract is intended to make unsupported analytical claims detectable in principle by a reviewer, evaluator, or deterministic validator. It supports Analytical Correctness, Evidence Traceability, Reproducibility, Deterministic Validation, Data Sufficiency, Claim Discipline, Transparent Limitations, and Human Decision Ownership. It does not redefine the governing Constitution.

## 2. Authority and Governing Documents

This specification is subordinate to and must conform to the following approved and frozen documents:

1. `PROJECT_MASTER_INSTRUCTIONS.md` v1.1 — Approved / Frozen; Skill-first Strategy amendment.
2. `PRD.md` v1.1 — Approved / Frozen; Skill-first Strategy amendment.
3. `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md` — Approved / Frozen; migration decision: GO.
4. `SKILL_SCOPE_SPECIFICATION.md` v1.0 — Approved / Frozen.

If this specification conflicts with an authoritative governing document, the higher governing document prevails. This specification does not reopen any approved product, scope, claim-taxonomy, execution, or human-ownership decision.

## 3. Contract Boundary

The Evidence Contract is a logical and behavioral contract. It defines what must be established and traceable before an analytical output is admissible.

It is not Architecture, a database schema, a JSON schema, a Pydantic model, an API contract, a SQL schema, class design, code, a serialization format, storage design, logging or observability architecture, `SKILL.md`, prompt engineering, UI design, a report template, or benchmark implementation.

This specification does not prescribe how evidence is stored, serialized, identified, displayed, or transported. Later artifacts may choose implementation mechanisms only if they preserve the logical requirements defined here.

## 4. Evidence Contract Purpose and Logical Chain

The Evidence Contract connects the complete analytical reasoning path:

Business Question  
↓  
Analytical Scope  
↓  
Metric Definition  
↓  
Required Evidence  
↓  
Data Source  
↓  
Execution  
↓  
Validation  
↓  
Validated Result  
↓  
Finding  
↓  
Alternative Explanations  
↓  
Recommendation  
↓  
Limitations

The contract must allow a reviewer, evaluator, or deterministic validator to determine:

- what supports each material claim;
- whether required evidence exists;
- whether deterministic execution actually occurred;
- whether the relevant result was validated;
- which assumptions affect interpretation;
- which limitations constrain the claim;
- which claim type is being made; and
- whether a Recommendation is supported by admissible Findings.

Traceability is required across the logical relationships, not through any particular physical storage shape.

## 5. Scope of Application

The Evidence Contract applies to material analytical outputs. An output is material when it could meaningfully affect the answer to the Business Question, the interpretation of business performance, or a human business decision.

Material outputs include, at minimum:

- KPI values;
- period comparisons;
- contribution results;
- ranked analytical results;
- material Findings;
- material Diagnostic interpretations;
- Recommendations; and
- statements that could materially influence a business decision.

Not every conversational sentence requires a complete evidence chain. Workflow guidance, clarification questions, status messages, and accurately labeled context may be communicated without being misrepresented as analytical Findings.

### 5.1 Output Categories

**Material Claim**  
An assertion about the data, performance, relationship, interpretation, or recommended response that could materially influence the answer or a decision. It is subject to claim admissibility rules.

**Supporting Statement**  
A statement that explains an admissible Claim without adding a new material assertion. If it introduces a new material assertion, it becomes a Material Claim and requires its own support.

**Process Statement**  
A factual statement about workflow state, such as whether clarification, execution, or validation is pending, successful, partial, unavailable, or failed. It must accurately reflect the workflow state but does not serve as evidence for the intended analytical result.

**User-provided Context**  
Information supplied by the user and preserved as context. It must not be silently converted into a validated analytical Finding. When relied upon materially, its role and unvalidated status must remain explicit unless independently established by governed evidence.

**Hypothesis**  
A testable proposition that guides Required Evidence and the Analysis Plan. It is not a Finding and must not be phrased as an established result.

**Alternative Explanation**  
A candidate interpretation of an observed result. Its evidence status must be explicit. It is not automatically a Finding or validated cause.

**Recommendation**  
A decision-support statement proposing an action, review, or further investigation based on admissible Findings. It is subject to stronger traceability and proportionality requirements.

**Limitation**  
A known constraint on data, scope, execution, validation, interpretation, claim strength, or completeness. A Limitation qualifies or blocks the affected Claim depending on severity.

## 6. Canonical MVP Boundary

Evidence Contract v1.0 is designed around the approved canonical MVP Business Question:

> How did revenue performance change between two comparable periods, and which products or categories contributed most to that change?

The bounded MVP analytical concepts are:

- Revenue;
- Orders;
- AOV;
- Product Performance;
- Category Performance;
- period-over-period comparison;
- Contribution Analysis;
- bounded Descriptive Analysis; and
- bounded Diagnostic Analysis.

Supported source types are CSV, Excel, and SQLite.

This specification does not create a universal evidence system for every analytical domain. It may support later extension at the conceptual level, but MVP depth and correctness take priority. Predictive, Causal, A/B testing, cohort, inventory, and connector-specific evidence requirements are not designed here.

## 7. Core Evidence Entities

The following are conceptual evidence entities. They are not technical classes, schemas, records, or storage objects. Each may be represented differently by later Architecture, but its purpose and relationships must be preserved.

### 7.1 Business Question

**Purpose:** Establish the decision-relevant question the analysis is intended to answer.  
**Required when:** Any material analysis or Finding is produced.  
**Must establish:** The original question, any clarified question, supported and unsupported portions, and intended claim type.  
**Downstream dependencies:** Analytical Scope, Required Evidence, Analysis Plan, Findings, and Recommendations.

### 7.2 Analytical Scope

**Purpose:** Define the bounded population and comparison basis to which evidence and claims apply.  
**Required when:** A material Claim depends on periods, populations, products, categories, filters, segments, or exclusions.  
**Must establish:** Comparison periods, analytical population, product/category scope, exclusions, segmentation, relevant filters, and comparison basis.  
**Downstream dependencies:** Data Sufficiency, Execution, Validation, Validated Results, Findings, and Recommendations.

### 7.3 Metric Definition or Metric Reference

**Purpose:** Establish the authoritative meaning governing a KPI or calculation.  
**Required when:** A material output uses a Metric, aggregate, comparison, contribution, or ranking.  
**Must establish:** Which authoritative definition applies, including its required inputs, aggregation rule, relevant exclusions, and applicable period basis.  
**Downstream dependencies:** Required Evidence, Analysis Plan, Execution, Validation, numerical Claims, and Findings.

### 7.4 Data Source

**Purpose:** Establish the origin and source type of data used for analysis.  
**Required when:** Data supports deterministic execution or a material Claim.  
**Must establish:** The relevant origin, supported source type, and relationship to the governed dataset.  
**Downstream dependencies:** Dataset Identity, Provenance, Data Sufficiency, Execution, and Reproducibility.

### 7.5 Dataset Identity

**Purpose:** Distinguish the governed dataset that supported a result from any other dataset or plausible generated value.  
**Required when:** A material output relies on data.  
**Must establish:** A stable identity basis, relevant version or equivalent basis, material subset, analysis period, known exclusions, and material transformation context.  
**Downstream dependencies:** Data Sufficiency, Execution, Validation, Provenance, Findings, and Reproducibility.

### 7.6 Analysis Period

**Purpose:** Establish the time boundaries and comparison basis of the analysis.  
**Required when:** A Claim describes a period, change, comparison, or period-dependent Metric.  
**Must establish:** The relevant periods and their relationship to the supported comparison scope.  
**Downstream dependencies:** Data Sufficiency, Execution, Validation, Findings, assumptions about comparability, and Limitations.

### 7.7 Required Evidence

**Purpose:** Define what evidence must exist before the intended claim can be supported.  
**Required when:** A material claim type is intended.  
**Must establish:** Required fields, Metric inputs, coverage, identifiers, deterministic calculations, validation requirements, and claim-specific conditions, as applicable.  
**Downstream dependencies:** Data Sufficiency, Analysis Plan, admissibility, and failure behavior.

### 7.8 Data Sufficiency Assessment

**Purpose:** Determine whether available evidence can support the requested scope and claim type.  
**Required when:** Any material analysis is proposed.  
**Must establish:** Required Evidence, Available Evidence, material gaps, clarification needs, supported claim type, and permission to proceed.  
**Downstream dependencies:** Analysis Plan, Execution, admissibility, scope downgrades, and Insufficient Evidence conclusions.

### 7.9 Analysis Plan

**Purpose:** Connect the Business Question and Required Evidence to bounded deterministic work.  
**Required when:** Material execution is needed.  
**Must establish:** Intended computation, relevance, Metrics, scope, periods, population, required validation, and intended claim type.  
**Downstream dependencies:** Execution Records, Validation Records, Findings, and auditability.

### 7.10 Execution Record

**Purpose:** Establish that deterministic execution was attempted and state what actually occurred.  
**Required when:** A material result depends on computation.  
**Must establish:** The analytical operation, governed data basis, Metric or calculation served, execution outcome, relationship to results, and reproducibility relevance.  
**Downstream dependencies:** Executed Results, Validation, Provenance, numerical Claims, and Reproducibility.

### 7.11 Executed Result

**Purpose:** Represent a deterministic output produced by actual execution.  
**Required when:** Execution produces an output relevant to a material Claim.  
**Must establish:** The output's relationship to the execution, governed scope, and Metric or calculation.  
**Downstream dependencies:** Validation Record and, only after successful applicable validation, Validated Result and Finding.

### 7.12 Validation Record

**Purpose:** Establish whether an Executed Result satisfied applicable deterministic validation requirements.  
**Required when:** A material Claim depends on an Executed Result.  
**Must establish:** The result validated, requirement applied, outcome, unresolved inconsistencies, and whether the result may support a Finding.  
**Downstream dependencies:** Validated Result, claim admissibility, failures, and Reproducibility.

### 7.13 Validated Result

**Purpose:** Identify an Executed Result that satisfied all applicable validation requirements for its intended use.  
**Required when:** A material Finding relies on deterministic output.  
**Must establish:** That the relevant result, scope, and intended use reached the required validation state without unresolved blocking conflict.  
**Downstream dependencies:** Material numerical Claims, Findings, Recommendations, and auditability.

### 7.14 Claim

**Purpose:** Represent an assertion whose admissibility can be evaluated.  
**Required when:** A statement is material.  
**Must establish:** Content, claim type, materiality, supported scope, supporting evidence relationships, validation dependency, material assumptions, and material Limitations.  
**Downstream dependencies:** Finding classification, Recommendation support, review, and auditability.

### 7.15 Finding

**Purpose:** Represent an admissible material analytical Claim answering the Business Question or a supported sub-question.  
**Required when:** CommerceLens reports an analytical conclusion.  
**Must establish:** Relevance, correct claim classification, complete or appropriately qualified evidence chain, and supported scope.  
**Downstream dependencies:** Alternative Explanations, Recommendations, and human review.

### 7.16 Alternative Explanation

**Purpose:** Represent another possible interpretation of an observed result without silently treating it as established.  
**Required when:** A material interpretation would otherwise appear more certain or complete than the evidence allows, or when relevant alternatives are identified.  
**Must establish:** The proposed explanation, its evidence status, and whether it is supported, partially supported, untested but plausible, or unsupported.  
**Downstream dependencies:** Interpretation boundaries, Limitations, investigation Recommendations, and claim strength.

### 7.17 Recommendation

**Purpose:** Provide evidence-proportional decision support grounded in admissible Findings.  
**Required when:** CommerceLens proposes an action, review, or investigation.  
**Must establish:** Supporting Findings, applicable scope, material assumptions, material Limitations, proportional claim strength, and human decision ownership.  
**Downstream dependencies:** Human review and final human decision.

### 7.18 Assumption

**Purpose:** Represent a condition accepted for analysis but not established as a validated Finding.  
**Required when:** The condition materially affects execution, interpretation, or claim scope.  
**Must establish:** The accepted condition, why it matters, and which Claims or Recommendations it affects.  
**Downstream dependencies:** Qualification, Limitations, admissibility, and Reproducibility.

### 7.19 Limitation

**Purpose:** Represent a known constraint on evidence or interpretation.  
**Required when:** A constraint materially affects a Claim or Recommendation.  
**Must establish:** The constraint, affected outputs, and whether it qualifies or blocks them.  
**Downstream dependencies:** Claim wording, admissibility, Recommendation scope, and human review.

### 7.20 Provenance

**Purpose:** Preserve the traceable origin and analytical lineage of evidence.  
**Required when:** Evidence supports a material output.  
**Must establish:** Data origin, governed dataset, Metric definition, execution, validation, and material Claim relationships.  
**Downstream dependencies:** Auditability, admissibility, and Reproducibility.

### 7.21 Reproducibility Information

**Purpose:** Preserve enough governed analytical context to reproduce material deterministic results under equivalent conditions.  
**Required when:** A material deterministic Finding is produced.  
**Must establish:** Dataset basis, Metric definition, scope, periods, required computation, and relevant assumptions.  
**Downstream dependencies:** Review, evaluation, future reproduction, and reliability assessment.

## 8. Business Question Evidence

The Business Question anchors the Evidence Contract. Every material Finding must ultimately answer the bounded Business Question or an explicitly supported sub-question that is relevant to it.

The contract must preserve conceptually:

- the original user question;
- the clarified question, where clarification changes ambiguity into a supported analytical request;
- the portion of the request supported by available evidence and MVP scope;
- any unsupported portion; and
- the intended claim type.

An analysis does not become decision-relevant evidence merely because it was computed. A result unrelated to the Business Question or supported sub-question is inadmissible as an answer to that question. It may be reported only as clearly separate non-answer context if doing so does not create an unsupported material implication.

Clarification must not silently broaden the user's request. Material changes to the question must be visible and traceable.

## 9. Analytical Scope Evidence

The Analytical Scope bounds every execution, result, Finding, and Recommendation. It must establish, as applicable:

- comparison periods;
- analytical population;
- product and category scope;
- exclusions;
- segmentation;
- relevant filters; and
- comparison basis.

A Finding must not silently use a materially different scope from the scope represented in its evidence chain. Any material scope change requires traceable disclosure and a renewed Data Sufficiency determination for the changed scope.

If only a narrower scope is supported, the Claim must be narrowed explicitly. A valid result for one subset does not support a Claim about the full population. Scope ambiguity that could materially change the result requires clarification or blocks the affected Claim.

## 10. Metric Definition Evidence

A calculation alone does not make a Metric value admissible. Every material KPI, comparison, contribution result, ranking, or aggregate must trace to an authoritative Metric definition or reference.

The required logical relationship is:

Metric  
→ Definition  
→ Required Fields  
→ Aggregation Rule  
→ Relevant Exclusions  
→ Analysis Period  
→ Executed Result

This specification defines the traceability requirement only. It does not define formulas or provisional semantics for Revenue, Orders, AOV, Contribution, Product Performance, or Category Performance.

### 10.1 Metric Dictionary Dependency

The Evidence Contract Specification defines the requirement for Metric-definition traceability. It does not authorize provisional production Metric definitions.

The future Canonical Dataset + Metric Dictionary is the authoritative source for MVP Metric semantics.

MVP implementation and evaluation must not begin until the Canonical Dataset + Metric Dictionary is approved, consistent with the approved `SKILL_SCOPE_SPECIFICATION.md` v1.0.

Before that approval, metric names may be referenced only as governed MVP concepts. Their formulas, required fields, aggregation rules, and exclusions must not be invented or treated as authoritative.

## 11. Data Source and Dataset Identity

For every material Claim based on data, it must be possible to distinguish:

> This result came from this governed dataset under this scope.

from:

> The system generated a plausible number.

The evidence basis must conceptually preserve:

- source type;
- dataset identity;
- dataset version or equivalent identity basis;
- relevant data subset;
- analysis period;
- provenance;
- known exclusions; and
- known transformation context where material.

No particular identity mechanism is prescribed. Hashes, object identifiers, filenames, database identifiers, and storage mechanisms are Architecture decisions. Whatever mechanism is later selected must reliably establish the governed dataset basis and distinguish it from other data or fabricated output.

## 12. Provenance Contract

Provenance is the traceable origin and analytical lineage of Evidence. At product level, provenance must make it possible to understand:

- where the relevant data originated;
- which governed dataset supported execution;
- which Metric definition governed computation;
- which execution produced the result;
- which validation qualified the result; and
- which material Claim uses that result.

Provenance must be specific enough to prevent unrelated evidence, stale results, or outputs from different scopes from being silently substituted into a Claim's chain.

This contract does not define technical lineage infrastructure.

## 13. Required Evidence, Available Evidence, Validated Result, and Admissible Evidence

The following concepts must remain distinct:

**Required Evidence**  
Evidence that must exist for the intended claim type, Metric, scope, and analytical purpose.

**Available Evidence**  
Evidence currently present and accessible for assessment or analysis. Availability alone does not establish admissibility.

**Validated Result**  
An Executed Result that has satisfied all applicable deterministic validation requirements for its intended material use.

**Admissible Evidence**  
Evidence that has satisfied all applicable requirements governing its intended role in a material Claim evidence chain, including provenance, authoritative definition, sufficiency, execution, validation, scope, or other applicable requirements.

Not every Evidence entity undergoes the same deterministic validation process. Deterministic validation applies where required by the Evidence type and intended analytical use.

Before material analysis proceeds, Required Evidence must be derived from the Business Question, intended claim type, scope, Metric references, and validation needs. It may include required fields, Metric inputs, period coverage, product/category identifiers, deterministic calculations, validation requirements, and other claim-specific conditions.

Missing Required Evidence must affect Data Sufficiency and admissibility. Available Evidence must not be treated as Admissible Evidence merely because it appears plausible or is internally convenient. This terminology does not weaken the requirement that material numerical Findings must trace to appropriately Validated Results.

## 14. Data Sufficiency Contract

Every material Claim must pass the Data Sufficiency gate. The assessment must make it possible to determine:

- what Evidence was required;
- what Evidence was available;
- whether material gaps existed;
- whether clarification was required;
- whether the requested claim type was supported; and
- whether the workflow was allowed to proceed.

Data Sufficiency is claim- and scope-dependent. Data may be sufficient for a bounded Descriptive Claim but insufficient for a Diagnostic, Causal, broader-scope, or Recommendation claim.

If the relevant state is Insufficient Evidence, the unsupported material Claim is inadmissible. The required user-facing conclusion is:

> Insufficient evidence to conclude.

The system may still report what is missing, which weaker scope or claim type is supportable, and which independent evidence chains are complete. It must not infer missing evidence through language or manufacture values to pass the gate.

## 15. Analysis Plan Traceability

Material execution must trace to a bounded analytical purpose established before results are interpreted as Findings. The relationship to the Analysis Plan must make it possible to determine:

- what was intended to be computed;
- why it was relevant to the Business Question;
- which Metrics were involved;
- which periods, populations, filters, and exclusions applied;
- what validation was required; and
- what claim type the analysis intended to support.

The contract does not require every minor computational step to become a separate material evidence entity. It requires enough planning traceability to distinguish purposeful, governed analysis from unrelated computation or post hoc narrative selection.

## 16. Execution Record Contract

An Execution Record establishes that deterministic execution was attempted and states the actual outcome. It must distinguish:

- planned execution;
- generated code;
- attempted execution;
- successful execution;
- failed execution;
- unavailable execution; and
- partial execution.

Generated code alone is not proof of execution. A plan, a query draft, or executable-looking text does not establish that a numerical result was produced.

An Execution Record must conceptually establish:

- the analytical operation executed;
- the governed data and scope on which it operated;
- the Metric or calculation it served;
- the execution outcome;
- its relationship to any produced result; and
- information material to later analytical reproduction.

Runtime logs, command syntax, code storage, technical identifiers, and infrastructure are outside this specification.

## 17. Executed Result and Validated Result

An Executed Result is a deterministic output produced by actual execution. It is not automatically admissible evidence for a material Finding.

The contract preserves the non-equivalence:

> Executed Result ≠ Validated Result

An Executed Result may exist while validation is pending, validation has failed, execution was partial, or conflicting results remain unresolved. In each case its status must remain visible and it must not be represented as validated support.

A Validated Result is an Executed Result that has satisfied all applicable deterministic validation requirements for the intended claim, scope, and use. Only appropriately Validated Results may support material Findings.

Executed-but-unvalidated, failed-validation, and conflicting-validation results are not Validated Results.

## 18. Validation Record Contract

A Validation Record establishes whether an Executed Result satisfies the applicable deterministic validation requirements. It must conceptually capture:

- which Executed Result was assessed;
- which validation requirement applied;
- the validation outcome;
- any unresolved inconsistency; and
- whether the result may support a material Finding.

Validation must apply to the relevant result and use. Validation of one calculation, period, subset, or Metric does not automatically validate another.

This specification does not define validation algorithms. Those belong to later approved specifications and Architecture.

## 19. Reproducibility Contract

For material deterministic outputs, the evidence chain must preserve enough governed information to reproduce the analytical result under the same or equivalent governed conditions, including:

- dataset basis;
- authoritative Metric definition;
- Analytical Scope;
- comparison periods;
- required computation; and
- relevant material assumptions.

The requirement is reproducibility of the analytical definition and material deterministic result. It does not require identical narrative wording, nor does this specification promise bit-for-bit reproduction.

An inability to reconstruct the governed evidence basis weakens auditability and may make the affected Claim inadmissible when reproduction is required to establish what was actually computed.

## 20. Claim Contract

Claim is a first-class conceptual object for evidence evaluation. Every Claim must be classifiable and, when material, must expose enough information to evaluate admissibility.

A material Claim must conceptually carry:

- claim content;
- claim type;
- materiality;
- supported scope;
- supporting Evidence relationships;
- validation dependency;
- material assumptions; and
- material Limitations.

A sentence may contain more than one Claim. Support for one Claim does not automatically support another embedded assertion.

## 21. Claim Type Contract

CommerceLens preserves the following claim taxonomy:

- **Descriptive:** States what was observed or calculated within governed data and scope.
- **Diagnostic:** Interprets observed patterns, contributions, concentrations, associations, or segment differences without claiming causation.
- **Predictive:** States an expectation about an unobserved or future outcome.
- **Causal:** States that one factor caused or changed another outcome.
- **Prescriptive:** Recommends a decision or action based on supported Findings.

The MVP primarily admits Descriptive Claims and bounded Diagnostic Claims. Predictive and Causal Claims are outside MVP. Prescriptive Recommendations are governed by separate Recommendation admissibility rules.

A Descriptive or Diagnostic evidence chain must never be relabeled or narrated as Causal. Claim wording must not exceed the strength of its evidence.

## 22. Claim Admissibility States

### 22.1 Admissible

A material Claim is Admissible only when all applicable requirements are satisfied:

- it is relevant to the Business Question or a supported sub-question;
- its scope is explicit and supported;
- every applicable Metric traces to an authoritative definition;
- Data Sufficiency supports the claim type and scope;
- successful deterministic execution occurred where numerical evidence is required;
- applicable validation succeeded;
- the Claim traces to the relevant Validated Result;
- the Claim is correctly classified;
- material assumptions are disclosed;
- material Limitations are disclosed; and
- no unresolved blocking contradiction remains.

### 22.2 Qualified Admissibility

A material Claim may remain admissible with explicit qualification when its core evidence chain is complete and validated, but a non-blocking assumption, limitation, or non-material gap constrains interpretation or generalization.

Qualification is permitted only when:

- the evidence directly supports the narrowed Claim;
- the qualification is attached to the affected Claim rather than hidden in generic boilerplate;
- the limitation does not invalidate the underlying result;
- the wording and scope are reduced to match the evidence; and
- a reasonable reviewer can distinguish what is established from what remains uncertain.

Qualified admissibility must not be used to rescue a Claim with missing Metric authority, insufficient data for the Claim, absent execution, failed validation, or unresolved blocking contradiction.

### 22.3 Inadmissible

A material Claim is Inadmissible when any blocking requirement is absent or failed. An Inadmissible Claim must not be presented as a CommerceLens Finding or used to justify a Recommendation.

The system may state that the Claim could not be established, identify the blocker, report the appropriate fail-closed state, or provide a weaker independently supported Claim.

## 23. Material Numerical Claim Rule

> A material numerical claim is inadmissible unless the relevant numerical value originates from deterministic execution and the applicable result has reached the required validation state.

This rule includes Revenue, Orders, AOV, period change, Contribution, rankings, material aggregates, and material comparisons.

Language-model arithmetic, narrative inference, generated code without execution, copied plausible values, or reconstruction from unsupported text are not acceptable substitutes for deterministic execution and validation.

## 24. Finding Contract

A Finding is a material analytical Claim that answers part of the Business Question and has satisfied the applicable Evidence Contract.

The required logical traceability is:

Finding  
↓  
Claim Type  
↓  
Validated Result or Results  
↓  
Validation Record or Records  
↓  
Execution Record or Records  
↓  
Metric Definition or Definitions  
↓  
Dataset and Scope  
↓  
Business Question

Where material, Assumptions and Limitations must also trace to the Finding. This is a logical relationship, not a required storage shape.

No Finding may be created solely from a hypothesis, raw data observation not governed by the analysis, unvalidated output, Alternative Explanation, user expectation, or generic business knowledge.

## 25. Diagnostic Finding Contract

Bounded Diagnostic Findings in the canonical MVP may identify contribution, concentration, association, segment differences, and observed change patterns.

Additional rules apply:

- the underlying Descriptive evidence must be admissible;
- the diagnostic interpretation must remain within the observed scope;
- the analytical method must be appropriate to the intended bounded interpretation;
- material Alternative Explanations and Limitations must not be concealed; and
- causal language is prohibited unless causal Evidence exists.

The contract preserves:

> Contribution ≠ Causation.

Admissible under the MVP:

> Category A was a leading negative contributor to the observed revenue change.

Inadmissible under the MVP evidence boundary:

> Category A caused the revenue decline.

The example illustrates claim-type discipline only and does not assert any actual product, category, value, or result.

## 26. Alternative Explanation Contract

An Alternative Explanation is a candidate interpretation, not automatically a Finding. Its evidence status must be explicit as one of the following conceptual conditions:

- **Evidence-supported:** governed evidence directly supports presenting it as a bounded Finding of the correct claim type;
- **Partially supported:** some relevant evidence exists, but material components remain unestablished;
- **Untested but plausible:** it is a hypothesis for further investigation, not a conclusion; or
- **Unsupported:** no adequate evidence basis exists, so it must not be presented as an analytical explanation.

CommerceLens must not fabricate competitor activity, market events, customer motives, promotions, pricing decisions, supply problems, or external macroeconomic causes without Evidence.

When external Evidence is unavailable, that absence must remain explicit. An untested but plausible explanation may inform an investigation Recommendation only if clearly labeled and not represented as a validated cause.

## 27. Assumption Contract

An Assumption is a condition accepted for analysis that is not itself established as a Validated Finding. Material assumptions may concern period comparability, mappings, exclusions, or interpretation boundaries, but this specification does not define canonical assumptions before the Canonical Dataset + Metric Dictionary exists.

Each material Assumption must be traceable to the Claims, calculations, or Recommendations it affects. Its effect must be evaluated:

- if the Claim remains directly supported under the disclosed Assumption, the Claim may be qualified;
- if the Assumption materially changes the calculation or cannot be accepted without evidence, the affected Claim may require clarification or become inadmissible;
- an Assumption must never be narrated as observed fact; and
- an Assumption cannot replace Required Evidence.

## 28. Limitation Contract

A Limitation is a known constraint on data, scope, execution, validation, interpretation, claim strength, or completeness.

Material Limitations must be linked conceptually to the Claims or Recommendations they affect. They must not be hidden in generic boilerplate or separated so far from the affected output that their effect becomes unclear.

A Limitation is non-blocking when the underlying evidence still directly and reliably supports a narrower or qualified Claim. It is blocking when it prevents the Claim from meeting a required element, such as authoritative Metric meaning, sufficient evidence, successful execution, applicable validation, supported scope, or resolution of a material contradiction.

The output must therefore distinguish:

- an admissible Claim with an explicit qualification; and
- an inadmissible Claim whose evidence chain is blocked.

## 29. Recommendation Evidence Chain

Recommendations require stronger traceability than ordinary narrative. A material Recommendation must trace to:

Recommendation  
↓  
Admissible Finding or Findings

The Recommendation must also trace, where applicable, to:

- Supported Scope;
- Relevant Assumptions; and
- Applicable Limitations.

Each supporting Finding continues to trace through its own evidence chain:

Finding  
↓  
Validated Result or Results  
↓  
Validation Record or Records  
↓  
Execution Record or Records  
↓  
Metric Definition or Definitions  
↓  
Dataset and Scope  
↓  
Business Question

A Recommendation must not be justified directly by raw data alone, a hypothesis alone, unvalidated execution, an Alternative Explanation alone, user expectation, generic best practice, or external speculation unless governed Evidence explicitly supports that basis and the resulting statement remains within scope.

## 30. Recommendation Admissibility

A material Recommendation is admissible only when:

- every supporting Finding is admissible;
- the Recommendation traces clearly to those Findings;
- its scope does not exceed the scope of the Findings;
- its strength is proportional to the Evidence;
- material Limitations and Assumptions are disclosed;
- causal certainty is not implied from Descriptive or Diagnostic evidence;
- reasonable Alternative Explanations are not converted into facts;
- it remains decision support rather than an autonomous decision; and
- final decision ownership remains with the human user.

If Findings support only further investigation, the Recommendation must be framed as investigation, review, data collection, or validation rather than as a guaranteed business action or outcome.

An admissible Recommendation does not establish that the action will produce a particular result unless separately admissible evidence supports that claim type. Under the MVP, such causal or predictive certainty is outside scope.

## 31. Unsupported Stronger Claim Behavior

When Evidence supports a weaker Claim than the user requested, CommerceLens must not silently upgrade evidence strength.

Conceptual pattern:

- **Requested:** Causal explanation.
- **Available Evidence:** Diagnostic contribution analysis.
- **Required behavior:** The causal Claim is inadmissible; the supported Diagnostic Claim may remain admissible; the downgrade must be explicit; and the unsupported conclusion receives “Insufficient evidence to conclude.”

The same rule applies to scope, certainty, completeness, and Recommendation strength. A valid narrow Claim does not justify a broader Claim.

## 32. Evidence Completeness

A material Claim's evidence chain is complete only when every component required for its claim type, Metric, scope, and intended use is present and satisfies the applicable state.

**Complete Evidence Chain**  
All required relationships and states are present, applicable validation has succeeded, and no blocking contradiction remains.

**Qualified Evidence Chain**  
The core chain is complete and validated, but disclosed non-blocking assumptions or Limitations constrain the Claim's interpretation or scope.

**Incomplete Evidence Chain**  
One or more required components are absent, unresolved, unvalidated, or not traceable.

**Blocked Evidence Chain**  
A required gate has failed or a blocking contradiction, unsupported scope, unsupported claim type, failed execution, failed validation, or insufficient evidence prevents admissibility.

Evidence Completeness is not a numerical score. This specification does not authorize completeness percentages, confidence percentages, or invented thresholds.

## 33. Missing Evidence Behavior

Missing Evidence has different consequences depending on materiality:

**Non-material missing Evidence**  
Does not change the calculation, claim type, supported scope, interpretation, or decision relevance. It may be disclosed where useful but does not necessarily block the Claim.

**Material but qualifying missing Evidence**  
Constrains interpretation or generalization while leaving a narrower validated Claim intact. The affected Claim must be narrowed and explicitly qualified.

**Blocking missing Evidence**  
Prevents an applicable requirement from being satisfied. The affected material Claim is inadmissible.

The Skill must not fill missing Evidence through language inference, invented fields, assumed values, or plausible narrative. If no independently supported weaker Claim exists, the output must state “Insufficient evidence to conclude.”

## 34. Contradictory Evidence

When material Evidence conflicts, CommerceLens must not silently choose the result that best supports a preferred narrative.

If a material contradiction cannot be deterministically resolved, the system must:

- disclose the conflict;
- preserve the relationship to the conflicting Evidence;
- prevent unsupported certainty;
- qualify or block the affected Findings; and
- avoid using the conflicted Claim to support a stronger Recommendation.

A contradiction is blocking when it prevents determination of which result is valid for the relevant scope or Metric. It may be qualifying only when the unaffected core Claim remains independently complete, validated, and accurately narrowed.

This specification does not define conflict-resolution algorithms.

## 35. Failed Execution Evidence

Failed execution is evidence that execution failed. It is not evidence for the intended numerical result.

Failure must remain traceable to the attempted analytical purpose. All dependent material Claims are blocked unless a separate, independently valid Execution Record, Executed Result, Validation Record, and Validated Result support them.

Narrative recovery must not fabricate, approximate, infer, or reconstruct the missing result.

## 36. Partial Execution Evidence

Partial execution means that only part of the planned analytical work completed successfully, or that some intended operations or scopes did not complete.

A partial workflow may produce admissible Claims only for independently complete and validated portions. It must make clear:

- what completed;
- what did not complete;
- which evidence chains are complete;
- which Claims remain admissible; and
- which Claims are blocked.

Partial execution must not be labeled or presented as complete workflow success. Completion of one Metric, period, segment, or contribution analysis does not validate unrelated incomplete portions.

## 37. Validation Failure Evidence

Validation failure is evidence about the reliability state of an Executed Result. It is not validated support for the intended Finding.

Dependent Findings must be blocked unless another independently valid evidence chain supports them. The Skill must not rationalize the validation failure, select a preferred unvalidated output, or soften the failure into apparent success.

An explanation of the failure may be reported as a Process Statement, provided it does not assert an unsupported analytical result.

## 38. Evidence-to-Claim Traceability Matrix

The matrix below states minimum conceptual relationships. “Required” means the relationship must exist for admissibility. “Conditional” means it is required when applicable to the claim's scope, interpretation, or evidence state. “Not applicable” means the output does not inherently require that relationship.

| Output type | Business Question | Scope | Metric Definition | Dataset | Data Sufficiency | Execution | Validation | Validated Result | Assumption | Limitation | Supporting Finding | Claim Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Material KPI Value | Required | Required | Required | Required | Required | Required | Required | Required | Conditional | Conditional | Not applicable | Required |
| Period Comparison | Required | Required | Required | Required | Required | Required | Required | Required | Conditional | Conditional | Not applicable | Required |
| Contribution Result | Required | Required | Required | Required | Required | Required | Required | Required | Conditional | Conditional | Not applicable | Required |
| Descriptive Finding | Required | Required | Required when Metric-based | Required | Required | Required when computation-based | Required when result-based | Required when result-based | Conditional | Conditional | Not applicable | Required |
| Diagnostic Finding | Required | Required | Required when Metric-based | Required | Required | Required | Required | Required | Conditional | Required when interpretation is constrained | Not applicable | Required |
| Alternative Explanation | Required for decision relevance | Required | Conditional | Conditional | Required to establish evidence status | Conditional | Conditional | Conditional | Conditional | Required when untested or partial | Conditional | Required |
| Recommendation | Required | Required | Through supporting Findings | Through supporting Findings | Through supporting Findings | Through supporting Findings | Through supporting Findings | Through supporting Findings | Conditional | Required when material | Required | Required |
| Limitation Statement | Conditional | Required for affected output | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Not applicable | Conditional | Required as limitation |
| Insufficient Evidence conclusion | Required | Required | Conditional | Conditional | Required | Conditional | Conditional | Not applicable | Conditional | Required when relevant | Not applicable | Required as insufficiency conclusion |

This matrix does not replace claim-specific evaluation. A “Conditional” element becomes required whenever omitting it would materially change interpretation, scope, reliability, or decision relevance.

## 39. Evidence Admissibility Matrix by Claim Type

| Claim type | MVP status | Minimum evidence expectation | Deterministic execution | Validation | Additional restrictions | MVP admissibility |
|---|---|---|---|---|---|---|
| Descriptive | In scope | Governed dataset and scope; authoritative Metrics where applicable; sufficient evidence; complete traceability | Required for material numerical or computed Claims | Required for material Executed Results | Must describe only observed or calculated evidence within scope | Admissible when contract is satisfied |
| Diagnostic | Bounded in scope | Admissible descriptive basis plus evidence supporting contribution, concentration, association, segment difference, or observed pattern | Required | Required | No causal language; Alternative Explanations and material Limitations remain explicit | Admissible only within bounded MVP interpretation |
| Predictive | Outside MVP | Would require a stronger future contract not defined here | Not defined here | Not defined here | Must not be simulated through descriptive evidence or language inference | Inadmissible under MVP |
| Causal | Outside MVP | Would require causal Evidence and a stronger future contract not defined here | Not defined here | Not defined here | Contribution, correlation, association, and sequence do not establish causation | Inadmissible under MVP |
| Prescriptive | Recommendations only | Admissible supporting Findings, proportional scope and strength, traceable assumptions and Limitations | Through supporting Findings | Through supporting Findings | Must remain decision support; no unsupported causal or predictive certainty | Admissible only under Recommendation rules |

## 40. Canonical Evidence Chain Walkthrough

The following walkthrough is conceptual and contains no dataset values, product names, category names, formulas, execution identifiers, or assumed outcomes.

### Business Question

The governed question asks how revenue performance changed between two comparable periods and which products or categories contributed most to that change.

### Scope

The analysis establishes the comparison periods, population, applicable product/category boundaries, exclusions, filters, and comparison basis. Unsupported portions are identified rather than silently included.

### Metric References

The intended Revenue, Orders, AOV, performance, comparison, and Contribution concepts reference their future approved authoritative definitions. No calculation proceeds under invented semantics.

### Required Evidence

The analysis identifies the fields, period coverage, product/category identifiers, Metric inputs, deterministic calculations, and validation requirements necessary for the intended Descriptive and bounded Diagnostic Claims.

### Data Sufficiency

Available Evidence is compared with Required Evidence. The system determines which requested Claims and scopes are supported, which require clarification, and which are blocked.

### Analysis Plan

The plan identifies the relevant period comparison, Metric computations, contribution analysis, populations, and required validations, all tied to the Business Question.

### Execution Record

The record establishes whether the governed computations actually ran on the governed dataset and scope, and whether execution succeeded, failed, was unavailable, or was partial.

### Executed Result

Any deterministic outputs produced by successful execution remain Executed Results and are not yet Findings.

### Validation Record

Applicable validation assesses each Executed Result and records whether it satisfies its requirements or contains unresolved inconsistency.

### Validated Result

Only results satisfying applicable validation become Validated Results eligible to support material Claims.

### Finding

The system may state the supported period-performance change and leading product/category contributions only within the validated scope and correct Descriptive or bounded Diagnostic classification.

### Alternative Explanation

Possible interpretations not established by governed Evidence are labeled according to evidence status. They are not presented as causes.

### Recommendation

Any Recommendation traces to admissible Findings, stays proportional to their scope and strength, and is framed as decision support. If evidence supports only further investigation, the Recommendation requests investigation or review.

### Limitations

Material data, scope, execution, validation, and interpretation constraints are attached to the affected Findings and Recommendations. Blocking Limitations prevent the dependent output from becoming admissible.

## 41. Negative Evidence Examples

### A. Generated Code but No Execution

The code demonstrates only a proposed method. Without actual deterministic execution, no Executed Result exists. Any dependent numerical Claim is inadmissible.

### B. Executed Result but No Required Validation

Execution produced an output, but the result has not reached the required validation state. It remains an Executed Result, not a Validated Result, and cannot support a material Finding.

### C. KPI Number with No Authoritative Metric Definition

The number has no governed semantic basis. A plausible calculation cannot establish what the KPI means. The material KPI Claim is inadmissible.

### D. Diagnostic Contribution Rewritten as Causal Explanation

Contribution evidence supports a bounded Diagnostic Claim, not causation. Rewriting it as a cause exceeds the evidence and makes the causal Claim inadmissible.

### E. Recommendation Based Only on an Untested Hypothesis

A Hypothesis is not a Finding. Without admissible supporting Findings, the Recommendation lacks the required evidence chain and is inadmissible. At most, the hypothesis may justify a clearly labeled investigation proposal.

### F. Failed Execution Followed by a Fabricated Narrative Result

Execution failure proves only that execution failed. A narrative value or conclusion created afterward has no deterministic result or validation and is inadmissible.

### G. Missing Required Field but Full Finding Still Produced

The missing field creates a blocking Required Evidence gap for the intended Claim. Unless an independently valid narrower Claim avoids that dependency, the full Finding is inadmissible.

### H. Alternative Explanation Presented as a Validated Cause

An untested or partially supported explanation is not causal Evidence. Presenting it as a validated cause violates evidence-status labeling and the MVP claim boundary.

## 42. Fail-Closed Behavior

The Evidence Contract connects directly to the approved Skill fail-closed states.

| Fail-closed state | Evidence meaning | Admissibility consequence |
|---|---|---|
| Clarification Required | Material ambiguity prevents a governed Business Question, scope, Metric interpretation, or Required Evidence determination | Affected material Claims cannot become admissible until clarified; independent unambiguous Claims may proceed only if separately complete |
| Insufficient Evidence | Required Evidence is materially absent for the intended Claim or scope | Affected Claim is blocked; output “Insufficient evidence to conclude.” |
| Unsupported Scope | Requested analysis exceeds approved source, domain, Metric, or MVP boundaries | Claims requiring unsupported scope are blocked; a supported narrower scope must be explicit |
| Unsupported Claim Type | Requested Claim exceeds the admitted taxonomy or evidence strength, including Predictive or Causal Claims under MVP | Unsupported Claim is blocked; an independently supported weaker Claim may be provided with explicit downgrade |
| Execution Unavailable | Required deterministic execution could not be performed | Dependent numerical or computed Claims are blocked |
| Execution Failed | Attempted execution did not successfully produce the intended result | Failure remains traceable; dependent Claims are blocked absent an independent valid chain |
| Validation Failed | Executed Result did not satisfy applicable validation | Result cannot become a Validated Result or Admissible Evidence for the intended Finding; dependent Findings are blocked absent an independent valid chain |

These states prevent affected material Claims from becoming admissible. They do not prevent accurate Process Statements about the failure state, nor do they invalidate unrelated independently complete evidence chains.

## 43. Partial Completion Contract

When CommerceLens returns a partial analysis, the output must distinguish:

- **Completed Evidence Chains:** independently complete, sufficiently supported, successfully executed where required, validated, and admissible; and
- **Blocked or Incomplete Evidence Chains:** missing, failed, unavailable, contradictory, unsupported, or unvalidated portions.

Only Completed Evidence Chains may support material Claims. The existence of one valid Finding must not make unrelated failed Findings admissible. The overall workflow must not be labeled complete if required portions remain blocked.

Recommendations may use only the admissible Findings from completed chains and must disclose when the requested analysis was only partially completed.

## 44. Human Decision Ownership

The Evidence Contract supports human review and decision-making. It does not transfer decision ownership to CommerceLens.

The human user must be able conceptually to inspect:

- what was found;
- what Evidence supports it;
- what remains uncertain;
- what Limitations and Assumptions apply; and
- why a Recommendation was made.

CommerceLens provides evidence-based decision support. It does not autonomously execute the resulting business decision, and an admissible Recommendation does not remove the need for human judgment.

## 45. Auditability Requirement

For every material output, a reviewer must be able to answer:

1. What Claim was made?
2. What type of Claim is it?
3. What Business Question or supported sub-question does it answer?
4. What authoritative Metric definition applies?
5. What dataset, period, and scope support it?
6. Was the data sufficient for this Claim type and scope?
7. What deterministic execution produced the result?
8. Was the relevant result validated?
9. What assumptions affect it?
10. What Limitations affect it?
11. What Alternative Explanations remain and what is their evidence status?
12. If it is a Recommendation, which admissible Findings justify it?

If these questions cannot be answered for a material Claim, the evidence chain is incomplete or blocked unless the missing item is demonstrably not applicable.

Auditability here is a product-level requirement. No audit UI, storage mechanism, technical lineage system, or report rendering is prescribed.

## 46. Reproducibility Requirement

For each material deterministic Finding, a future implementation must be capable of reproducing the material analytical result from the governed evidence basis.

The following information must remain available conceptually:

- bounded Business Question and supported sub-question;
- Analytical Scope and comparison basis;
- governed dataset basis and material transformation context;
- authoritative Metric definition or reference;
- relevant analysis periods;
- Required Evidence and Data Sufficiency determination;
- intended computation;
- actual execution relationship;
- applicable validation relationship; and
- material assumptions and Limitations.

This specification does not define how reproduction is executed and does not require identical AI narrative wording.

## 47. Evidence Contract Non-Responsibilities

This specification does not define:

- Metric formulas;
- canonical dataset schema;
- field names;
- SQL;
- Python;
- statistical algorithms;
- validation algorithms;
- execution runtime;
- storage;
- database design;
- object identifiers;
- hashing;
- serialization;
- APIs;
- UI;
- report rendering; or
- benchmark scoring.

These belong to later approved artifacts. Nothing in this specification authorizes their implementation.

## 48. Reuse Before Rebuild

The constitutional principle is:

> Reuse before rebuild.

The Evidence Contract defines differentiated evidence-governance behavior. It does not require CommerceLens to invent custom storage, lineage, validation, or execution infrastructure for novelty.

Later Architecture may reuse mature components when they satisfy this contract's traceability, admissibility, reproducibility, validation, scope, safety, and host-independence requirements.

## 49. Host Independence

The Evidence Contract is host-independent. Its rules must remain valid if the implementation environment changes.

It is not bound to ChatGPT, Claude, Codex, MCP, a particular LLM, a particular Skill host, or a specific agent framework.

Any future host or execution environment must preserve the same logical evidence relationships and fail-closed behavior.

## 50. Future Extensibility Without Scope Expansion

Later analytical capabilities may require stronger or additional evidence contracts. This specification allows that conceptual possibility but does not design those systems.

It does not add detailed requirements for Predictive, Causal, A/B testing, cohort, inventory, or connector-specific analysis. It does not authorize Phase 2, Phase 3, Research, or Backlog functionality.

MVP depth, correctness, traceability, and admissibility remain the priority.

## 51. Acceptance Criteria

This specification passes Main Project Review only if all of the following are true:

1. “No material claim without traceable evidence” is operationalized as an enforceable admissibility rule.
2. Material Claim is clearly defined.
3. Required evidence entities are conceptually defined without technical schemas.
4. The Business Question anchors material Findings.
5. Analytical Scope and material scope changes are traceable.
6. Material Metrics require authoritative definitions.
7. The Canonical Dataset + Metric Dictionary dependency is explicit.
8. Dataset identity and Provenance requirements are conceptually defined.
9. Required Evidence, Available Evidence, Validated Results, and Admissible Evidence are distinguished.
10. Data Sufficiency governs permission to proceed and Claim admissibility.
11. An Execution Record proves actual execution state rather than planned execution or generated code.
12. Executed Result and Validated Result remain distinct.
13. Validation failure blocks dependent Findings.
14. Reproducibility requirements are explicit.
15. Descriptive, Diagnostic, Predictive, Causal, and Prescriptive classifications are preserved.
16. Admissible, Qualified, and Inadmissible Claim behavior is explicit.
17. Material numerical Claims require deterministic execution and applicable validation.
18. Material Findings require Admissible Evidence, and material numerical Findings require appropriately Validated Results.
19. Contribution cannot become causation.
20. Alternative Explanations carry explicit evidence status.
21. Material Assumptions and Limitations affect qualification or admissibility.
22. Recommendations trace to admissible Findings and remain proportional to Evidence.
23. Missing Evidence behavior distinguishes non-material, qualifying, and blocking gaps.
24. Contradictory Evidence behavior prevents narrative selection and unsupported certainty.
25. Failed and partial execution behavior is defined.
26. Approved fail-closed states connect explicitly to evidence admissibility.
27. Partial completion is not represented as full success.
28. Product-level auditability is defined.
29. Human Decision Ownership remains explicit.
30. No technical Architecture, implementation schema, or storage design is introduced.
31. No numerical result, formula, dataset value, external fact, or evidence identifier is fabricated.
32. The contract remains host-independent.
33. The contract remains bounded to the canonical MVP.
34. The specification conforms to the Constitution v1.1, PRD v1.1, Skill-first migration decision, and `SKILL_SCOPE_SPECIFICATION.md` v1.0.

## 52. Open Questions for Later Artifacts

The following questions remain intentionally unresolved because they belong to later approved artifacts:

### Canonical Dataset + Metric Dictionary

- What are the authoritative formulas, required fields, aggregation rules, exclusions, and comparison semantics for each MVP Metric?
- What governed dataset semantics establish the canonical analytical population and period comparability?
- Which transformation assumptions are authoritative and which require disclosure?

### Evaluation Fixtures

- Which positive, negative, partial, contradictory, failure, and insufficiency cases will test conformance to this contract?
- Which expected claim-admissibility outcomes must each fixture verify?
- How will fixtures test that unsupported Claims are detectable without converting the Evidence Contract into a scoring implementation?

### Architecture

- How will the logical evidence relationships be represented, preserved, and retrieved?
- How will execution, validation, provenance, reproducibility, and partial completion states be implemented?
- Which mature components can be reused while satisfying the contract?
- How will host independence and governed identity be preserved?

These questions do not reopen the Skill-first strategy, deterministic execution requirement, claim taxonomy, canonical MVP question, CSV/Excel/SQLite scope, Human Decision Ownership, or the necessity of the Evidence Contract.

## 53. Conceptual Traceability to Governing Documents

| Governing source | Conceptual derivation preserved in this specification |
|---|---|
| `PROJECT_MASTER_INSTRUCTIONS.md` v1.1 | Evidence-first governance; no material claim without traceable evidence; analytical correctness; deterministic execution and validation; reproducibility; transparent limitations; Reuse before rebuild; Human Decision Ownership; host-independent Skill-first direction |
| `PRD.md` v1.1 | Product-level analytical workflow; business-question orientation; actionable but bounded decision support; canonical MVP outcomes; evidence and limitation visibility |
| `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md` | Approved Skill-first migration; executable deterministic backing; narrow end-to-end MVP depth; reusable engine direction without expanding this specification into implementation |
| `SKILL_SCOPE_SPECIFICATION.md` v1.0 | Approved canonical MVP question and source types; claim taxonomy; fail-closed states; Data Sufficiency gate; Metric Dictionary dependency; execution and validation boundaries; partial-workflow behavior |

No requirement identifiers are asserted because precise governing requirement IDs are not available in this specification.

## 54. Release Boundary

This approved and frozen specification defines only the logical and behavioral Evidence Contract.

Main Project approval and Freeze of this specification authorize progression only to the next approved artifact:

- Canonical Dataset + Metric Dictionary.

This approval does not authorize progression beyond that artifact to:

- dataset implementation;
- Evaluation Fixtures;
- Architecture;
- `SKILL.md`;
- code; or
- implementation.

The Canonical Dataset + Metric Dictionary is not created or begun by this specification.

## 55. Document Status

**Document:** `EVIDENCE_CONTRACT_SPECIFICATION.md`  
**Version:** v1.0  
**Status:** Approved  
**State:** Frozen  
**Date:** 2026-08-20

---

**End of Document**
