# CommerceLens AI Skill Scope Specification

**Document:** SKILL_SCOPE_SPECIFICATION.md  
**Version:** v1.0  
**Status:** Approved  
**State:** Frozen  
**Date:** 2026-08-20

## 1. Document Purpose

This specification defines the behavioral and product contract of the CommerceLens Skill. It establishes what the Skill accepts, what it is responsible for, what it must delegate, when it may proceed, when it must clarify or stop, and what constitutes a completed analytical workflow.

This specification occupies the following position in the project hierarchy:

`PRD`  
↓  
`Skill Scope Specification`  
↓  
`Evidence Contract Specification`  
↓  
`Canonical Dataset + Metric Dictionary`  
↓  
`Evaluation Fixtures`  
↓  
`Architecture`

It defines behavioral responsibilities only. It does not define implementation mechanisms.

## 2. Authority and Constitutional Inheritance

This specification inherits all governing principles and approved decisions from:

- `PROJECT_MASTER_INSTRUCTIONS.md` v1.1 — Approved / Frozen
- `PRD.md` v1.1 — Approved / Frozen
- `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md` — Approved / Frozen; Migration Decision: GO

It does not redefine, replace, or reopen those documents. Where a conflict exists, the higher governing document prevails.

The CommerceLens Skill must preserve, at minimum:

- Evidence First
- No material claim without traceable evidence
- Analytical Correctness
- Evidence Traceability
- Reproducibility
- Deterministic Validation
- Data Sufficiency
- Transparent Limitations
- Human Decision Ownership
- Reuse Before Rebuild
- MVP Depth Over Feature Breadth

The Skill must follow the approved analytical workflow without alteration:

Business Question  
↓  
Metric Definition  
↓  
Hypothesis Generation  
↓  
Required Evidence  
↓  
Data Sufficiency Check  
↓  
Analysis Plan  
↓  
Deterministic Execution  
↓  
Deterministic Validation  
↓  
Findings  
↓  
Alternative Explanations  
↓  
Recommendation  
↓  
Limitations  
↓  
Evidence Contract

## 3. Purpose of the CommerceLens Skill

The CommerceLens Skill is the user-facing analytical reasoning and orchestration layer of CommerceLens AI.

Its purpose is to transform an eligible e-commerce Business Question and a supported structured dataset into a disciplined analytical workflow in which:

- the question is bounded before analysis;
- Metrics are defined before use;
- required Evidence is identified;
- Data Sufficiency is treated as a mandatory gate;
- material numerical outputs originate from deterministic execution;
- material Findings rely on appropriately validated results;
- claim strength remains within the Evidence;
- uncertainty, Alternative Explanations, and Limitations are disclosed; and
- Recommendations remain evidence-bounded decision support.

The Skill reasons about what must be analyzed, coordinates the analytical workflow, interprets validated Evidence, and communicates the result. It does not replace the Reusable Deterministic Analytics Engine, and it does not own the final business decision.

## 4. Specification Boundary

This document is not:

- a `SKILL.md` implementation;
- prompt engineering or a system prompt;
- a tool definition or tool schema;
- an API specification;
- Architecture;
- code, class, function, module, or directory design;
- a framework or model selection decision;
- host-specific Skill configuration; or
- a detailed Evidence Contract schema.

It defines what behavior is required, not how that behavior is technically implemented.

## 5. Canonical MVP Scope

### 5.1 Canonical Business Question

The canonical MVP Business Question is:

> How did revenue performance change between two comparable periods, and which products or categories contributed most to that change?

### 5.2 Supported Analytical Capabilities

The first Skill MVP supports only the capabilities required to answer that question:

- Revenue
- Orders
- Average Order Value (AOV)
- Product Performance
- Category Performance
- period-over-period comparison
- Contribution Analysis
- bounded Descriptive Analysis
- bounded Diagnostic Analysis

The Skill must keep each workflow bounded by the user’s eligible Business Question. The presence of additional fields does not authorize unrelated exploration or analytical expansion.

### 5.3 Supported Data-Source Types

The only supported MVP source types are:

- CSV
- Excel
- SQLite

Support means the source can be presented as a structured dataset or supported data reference suitable for the approved workflow. This specification does not define technical ingestion behavior.

## 6. Explicit Non-MVP Analytical Scope

The first Skill MVP does not require general support for:

- Gross Margin
- Discounts
- Refunds
- Inventory
- Stockouts
- Repeat Purchase
- Customer Retention
- Cohort Analysis
- Confidence Intervals
- Hypothesis Testing
- general Correlation Analysis
- A/B Testing
- Predictive Analysis
- Causal Analysis

These capabilities may be classified for later phases by the PRD, but they are not part of the behavioral success criteria for this MVP. The Skill must not reintroduce them indirectly through examples, Recommendations, or unsupported interpretations.

## 7. Accepted Inputs

### 7.1 Required Inputs

An analytical workflow requires:

1. **Business Question** — a question that can be assessed for MVP eligibility.
2. **Dataset or supported data reference** — a CSV, Excel, or SQLite source containing structured data relevant to the question.
3. **Comparison periods or sufficient information to determine them** — two periods that can be evaluated for comparability.
4. **Analytical context required to resolve material meaning** — only where the supplied question and validated data do not safely determine that meaning.

### 7.2 Optional Contextual Inputs

Optional context may include:

- the intended product or category scope;
- business calendar conventions;
- known exclusions;
- relevant population boundaries;
- an authoritative Metric definition or reference;
- known dataset limitations; and
- the intended decision context.

Optional context must not override validated dataset facts or an authoritative Metric Dictionary without explicit resolution.

### 7.3 Invalid Inputs

An input is invalid for the requested workflow when, for example:

- it is unreadable or structurally unusable for the required analysis;
- it is not one of the supported source types;
- no Business Question is supplied or recoverable from context;
- the requested periods cannot be represented by the available data;
- the input requires fabrication of fields, records, results, or business meaning; or
- its use would violate applicable data-handling constraints.

Invalid input must not be silently repaired through invented assumptions.

### 7.4 Ambiguous Inputs

An input is materially ambiguous when more than one reasonable interpretation would change a Metric, period, population, product/category scope, claim type, required Evidence, or resulting interpretation.

Material ambiguity triggers clarification unless validated data or existing context resolves it safely.

### 7.5 Unsupported Inputs

Unsupported inputs include:

- non-CSV, non-Excel, and non-SQLite source types for the MVP;
- live marketplace accounts or external database-server connections;
- requests that depend on unsupported KPIs or claim types; and
- inputs that require autonomous external business action.

The Skill must identify the unsupported boundary and must not simulate support.

## 8. Business Question Eligibility

An MVP Business Question is eligible only when it:

- falls within the approved e-commerce domain;
- can be answered through the supported MVP capabilities;
- is compatible with an available supported structured dataset;
- does not inherently require predictive or causal inference;
- can be bounded sufficiently to define Metrics, periods, population, and analytical scope; and
- can be evaluated under the approved evidence-first workflow.

The Skill must handle question states as follows:

| Question state | Required behavior |
| --- | --- |
| Fully supported | Proceed after required inputs, scope, and Data Sufficiency are established. |
| Partially supported | Identify the supported and unsupported portions. Proceed only with an independently valid supported portion and label the result as partial. |
| Ambiguous | Ask only the clarification necessary to prevent a material change in analysis or interpretation. |
| Outside MVP | State that the request exceeds approved MVP scope. Do not simulate the requested capability. |
| Unsupported by available Evidence | State **“Insufficient evidence to conclude.”** for the unsupported conclusion; a weaker supported analysis may be offered if clearly distinguished. |

## 9. Clarification Contract

Clarification is a controlled behavioral gate, not a default conversational step.

### 9.1 Proceed Without Clarification

The Skill should proceed without clarification when:

- the Business Question is eligible and sufficiently specific;
- Metrics can be referenced or resolved without inventing definitions;
- comparison periods and analytical population can be determined safely from validated data and supplied context;
- any remaining ambiguity is immaterial to the output; and
- the required Evidence and intended claim type are clear.

The Skill must not ask questions whose answers can be safely determined from validated data or context already supplied.

### 9.2 Clarification Required

The Skill must request clarification when unresolved ambiguity could materially change:

- Metric definition;
- comparison period;
- analytical population;
- product or category scope;
- interpretation;
- claim type; or
- required Evidence.

Clarification must be limited to what is necessary to resolve the material ambiguity. While clarification remains unresolved, the Skill must not present the affected workflow as ready for execution or completed.

## 10. Metric Definition Responsibility

The Skill must ensure that every Metric used in an Analysis Plan, Finding, or Recommendation is defined before use.

MVP Metric concepts include:

- Revenue
- Orders
- AOV
- Product Performance
- Category Performance
- Contribution

This specification does not finalize their formulas. The authoritative formulas, field requirements, aggregation rules, exclusions, and edge-case treatment belong to the future Canonical Dataset + Metric Dictionary.

Once the authoritative Metric Dictionary exists, the Skill must use it. The Skill must not silently invent, substitute, or vary KPI definitions. If a required definition is absent or materially ambiguous, the Skill must request clarification or identify the dependency as unresolved rather than manufacturing a definition.

Before the Canonical Dataset + Metric Dictionary is approved, this specification defines the requirement for authoritative Metric definitions but does not authorize the Skill to invent provisional production definitions.

MVP implementation and evaluation must not begin without the approved Metric Dictionary required by the project hierarchy.

## 11. Hypothesis Contract

The Skill may generate candidate hypotheses to guide the Analysis Plan and determine what Evidence or computation is needed. A hypothesis is a testable candidate explanation, not a result.

Hypotheses:

- are not Findings;
- are not Evidence;
- must not be presented as proven explanations;
- may guide Evidence requirements and bounded analysis; and
- must be evaluated against deterministic results where applicable.

The following concepts must remain distinct:

| Concept | Meaning |
| --- | --- |
| Hypothesis | A candidate explanation proposed before sufficient supporting Evidence is established. |
| Finding | A statement answering part of the Business Question and supported by validated Evidence. |
| Alternative Explanation | A plausible, clearly labeled interpretation that may account for an observed pattern but has not necessarily been tested. |
| Recommendation | Evidence-bounded decision support derived from supported Findings, not an autonomous decision or action. |

## 12. Required Evidence Contract

Before attempting a material conclusion, the Skill must identify the Evidence required to support the intended claim.

At a conceptual level, required Evidence may include:

- fields needed by the relevant Metric;
- valid and comparable periods;
- sufficient transaction records for the bounded analysis;
- stable product and category identifiers;
- Metric inputs and authoritative definitions;
- deterministic calculation results;
- data-quality findings;
- execution status; and
- validation status.

The Skill must not lower Evidence requirements merely to produce a report-shaped response. This section defines the obligation to identify and assemble Evidence, not the detailed Evidence Contract schema.

## 13. Data Sufficiency Contract

Data Sufficiency is a mandatory gate between Required Evidence and the Analysis Plan. The Skill must determine whether the available Evidence is adequate for the requested analysis and claim type.

Conceptual outcomes are:

- **Sufficient** — required data and context are adequate to proceed with the bounded plan.
- **Clarification Required** — a material ambiguity must be resolved before sufficiency can be determined or analysis can proceed.
- **Insufficient Evidence** — required Evidence is missing, unusable, or inadequate for the requested conclusion.
- **Unsupported Claim Type** — the requested strength of claim exceeds MVP capability or available Evidence.
- **Execution Required** — sufficiency may be established, but material results do not yet exist.
- **Validation Required** — execution exists, but results are not yet qualified to support material Findings.

These are behavioral meanings, not technical status codes.

When Evidence cannot support the requested conclusion, the Skill must state:

> Insufficient evidence to conclude.

Where appropriate, the Skill may provide a weaker supported analysis, but it must explicitly separate that analysis from the stronger requested conclusion and explain the downgrade.

## 14. Analysis Planning Contract

An acceptable product-level Analysis Plan must identify, as relevant:

- the bounded Business Question;
- Metrics and their authoritative definitions or references;
- comparison periods and their intended comparability;
- analytical population and exclusions;
- product and/or category segmentation;
- required deterministic calculations;
- Contribution Analysis;
- required validation; and
- intended claim type.

The plan must be proportionate to and bounded by the Business Question. It must not include unrelated exploratory analysis merely because additional data is available.

An Analysis Plan authorizes neither a Finding nor a numerical claim. It states what must be executed and validated.

## 15. Deterministic Execution Boundary

Material numerical outputs must originate from the Reusable Deterministic Analytics Engine. The Skill may determine what should be computed and why, but it must not calculate or assert material numerical results through language reasoning alone.

This boundary applies to, at minimum:

- Revenue totals;
- order counts;
- AOV;
- period-over-period change;
- product contribution;
- category contribution;
- ranked product or category results;
- material aggregations; and
- material comparisons.

Generated code is not execution Evidence. Planned execution is not completed execution. A plausible number, manually inferred number, or language-generated estimate must not be represented as an executed result.

The deterministic engine performs the computation. The Skill orchestrates the need for that computation and interprets only appropriately validated outputs.

## 16. Execution State Contract

The Skill must handle deterministic execution behaviorally as follows:

| Execution condition | Required Skill behavior |
| --- | --- |
| Successful | Record that required execution completed, then require applicable validation before using the result in a material Finding. |
| Unavailable | Explain what could not be completed; do not fabricate or estimate the missing output; do not declare full success. |
| Failed | Identify the failure as blocking the affected analysis; preserve any independently valid completed portion; do not convert failure into a result. |
| Partially completed | Separate completed and incomplete calculations; permit only independently valid partial output; do not present partial completion as full success. |
| Invalid | Reject the affected result as support for Findings and identify what remains unresolved. |
| Inconsistent with validation | Do not select the preferred result or rationalize the inconsistency; treat the affected output as unvalidated and block material Findings that depend on it. |

No non-success execution condition may be converted into a successful analytical result through narrative framing.

## 17. Deterministic Validation Boundary

Computation alone does not make a result trustworthy enough to support a material Finding.

The Skill must distinguish:

- **Executed Result** — an output produced by deterministic execution; and
- **Validated Result** — an executed output that has satisfied the applicable deterministic validation requirements.

Only appropriately validated results may support material Findings. If validation is missing, failed, incomplete, or inconsistent, the Skill must not elevate the executed result into a Finding.

This specification does not define validation algorithms. Those belong to later specifications and Architecture.

## 18. Finding Contract

A material Finding must:

- answer part of the Business Question;
- be supported by validated Evidence;
- use defined Metrics;
- remain within the supported claim type;
- be traceable to its relevant data, execution, and validation basis; and
- avoid stronger interpretation than the Evidence permits.

The Skill must not convert any of the following into Findings:

- hypotheses;
- assumptions;
- unvalidated results;
- missing Evidence;
- external speculation; or
- unsupported contextual narratives.

If the traceability or validation basis is unavailable, the material statement must not be labeled or presented as a Finding.

## 19. Claim Classification Contract

The Skill must preserve the constitutional claim taxonomy:

- **Descriptive** — states what was observed in the data.
- **Diagnostic** — examines how observed segments, patterns, or contributions relate to an outcome without automatically establishing causation.
- **Predictive** — estimates an unknown future or unobserved outcome.
- **Causal** — asserts that one factor produced a change in another.
- **Prescriptive** — recommends an action based on supported Evidence and stated constraints.

The MVP primarily supports bounded Descriptive and Diagnostic claims. Predictive and Causal claims are outside MVP.

Prescriptive Recommendations may be produced only when directly justified by supported Findings. They must not imply causal certainty when the underlying Evidence is descriptive or diagnostic.

When a user asks for a stronger claim than the Evidence or MVP permits, the Skill must:

1. identify the unsupported claim type;
2. refuse to present that stronger claim as established;
3. state **“Insufficient evidence to conclude.”** where the requested conclusion lacks adequate Evidence; and
4. offer a clearly labeled weaker supported claim when one is available.

## 20. Diagnostic and Contribution Boundary

The canonical question asks which products or categories contributed most to an observed revenue change. Contribution is an accounting or analytical attribution of observed change within the defined analysis; it does not automatically establish causation.

Within MVP scope, the Skill may identify:

- concentration;
- contribution;
- association;
- segment differences; and
- observed changes.

The Skill must not automatically claim that a product or category caused the revenue change. For example, identifying a product as a leading negative contributor does not establish that the product caused the overall decline.

Causal conclusions require causal Evidence and methods, which are outside MVP scope. The Skill must use contribution language precisely and must disclose this boundary when it materially affects interpretation.

## 21. Alternative Explanation Contract

Material diagnostic Findings should include plausible Alternative Explanations where relevant to prevent overconfident interpretation.

Alternative Explanations must:

- remain explicitly labeled as alternatives;
- not be presented as validated Findings unless separately tested and supported;
- identify reasonable uncertainty in interpreting the observed pattern; and
- remain consistent with, but not claimed as proven by, the available Evidence.

The Skill must not invent external events, market conditions, operational causes, customer motives, or business actions unsupported by available Evidence. If external explanatory Evidence is unavailable, the Skill must say so.

## 22. Recommendation Contract

The Skill may produce a Recommendation only when it:

- follows from supported Findings;
- is proportional to the strength and scope of the Evidence;
- acknowledges material Limitations;
- avoids implying causal certainty when only Descriptive or Diagnostic Evidence exists; and
- remains decision support rather than autonomous action.

A Recommendation may suggest what a human decision-maker should review, investigate, validate, or consider. It must not be presented as uniquely correct when the Evidence does not establish that conclusion.

The Skill must not produce a material Recommendation merely because the user expects one. If Evidence is inadequate, no material Recommendation may be presented as justified.

## 23. Human Decision Ownership

CommerceLens supports decisions. The user owns the final decision.

The Skill must not autonomously:

- change prices;
- alter inventory;
- modify campaigns;
- change marketplace settings;
- execute transactions; or
- take external business actions.

This boundary applies even when the Skill produces a Recommendation. The Skill’s role ends at evidence-backed decision support and explicit communication of uncertainty and Limitations.

## 24. Limitation Contract

The Skill must disclose each material limitation that affects the interpretation, reliability, scope, or completeness of the output.

Relevant limitations may include:

- missing fields;
- incomplete or non-comparable periods;
- limited historical coverage;
- ambiguous category mapping;
- unsupported causal interpretation;
- data-quality issues;
- incomplete deterministic execution; and
- validation limitations.

Limitations must be specific to the workflow and sufficiently concrete to affect interpretation. Generic boilerplate does not satisfy this contract.

## 25. Evidence Contract Dependency

The Skill must produce or assemble an evidence-backed analytical output whose material claims can be represented in the future `EVIDENCE_CONTRACT_SPECIFICATION.md`.

For each material claim, the Skill must be capable of providing the relevant conceptual information, including:

- the Business Question and bounded scope;
- the Metric definition or authoritative reference;
- the supporting dataset and analysis period;
- the required deterministic execution basis;
- the validation status;
- applicable assumptions and Limitations;
- the supported claim type; and
- the linkage between Evidence and the Finding or Recommendation.

This document does not define the Evidence Contract’s schema, identifiers, serialization, or technical representation.

## 26. Output Contract

A successful CommerceLens analytical output must logically contain:

1. **Business Question** — the eligible question being answered.
2. **Scope and comparison periods** — the bounded population, product/category scope, exclusions, and periods.
3. **Metric definitions or references** — the definitions governing the analysis.
4. **Data Sufficiency status** — whether the analysis passed the mandatory sufficiency gate and any relevant qualification.
5. **Analysis Plan** — the bounded plan that governed execution.
6. **Execution status** — whether required deterministic calculations completed.
7. **Validation status** — whether the relevant executed results passed required validation.
8. **Findings** — only claims supported by validated Evidence.
9. **Alternative Explanations** — where relevant, clearly separated from Findings.
10. **Recommendation** — only if justified and bounded by Evidence.
11. **Limitations** — specific constraints affecting interpretation.
12. **Evidence Contract reference or representation** — the Evidence linkage required by the future contract.

This is a logical content contract. It does not prescribe JSON, Markdown syntax, UI, file format, serialization, or rendering.

## 27. Successful Completion Definition

A workflow is successfully completed only when all critical requirements applicable to the canonical analysis have been satisfied:

- the Business Question is eligible;
- analytical context is sufficient or material ambiguity has been resolved;
- Metrics are defined;
- the Data Sufficiency gate has passed;
- the Analysis Plan is bounded by the Business Question;
- required deterministic execution has completed;
- required validation has passed;
- Findings are supported by validated results;
- claim boundaries are respected;
- Alternative Explanations are included where appropriate;
- material Limitations are disclosed;
- any Recommendation is bounded by Evidence; and
- Evidence Contract requirements are satisfied at the product level.

A workflow is not complete merely because:

- the Skill responded;
- an Analysis Plan exists;
- code was generated;
- calculations were proposed;
- deterministic execution was requested but not completed; or
- a report-shaped answer was generated.

## 28. Fail-Closed Behavior

The Skill must fail closed. It must not manufacture completion or substitute narrative confidence when a critical analytical dependency fails.

Conceptual blocking or terminal outcomes include:

| Outcome | Behavioral meaning |
| --- | --- |
| Clarification Required | A material ambiguity prevents safe progression. The affected workflow pauses until resolved. |
| Insufficient Evidence | Available Evidence cannot support the requested analysis or conclusion. The Skill states **“Insufficient evidence to conclude.”** |
| Unsupported Scope | The request is outside approved MVP domain, capability, KPI, or source boundaries. |
| Unsupported Claim Type | The requested claim is stronger than MVP capability or available Evidence permits. |
| Execution Unavailable | Required deterministic computation cannot be performed; missing results are not estimated or fabricated. |
| Execution Failed | Required computation did not produce a valid result; dependent Findings are blocked. |
| Validation Failed | Executed results did not satisfy required validation; dependent Findings are blocked. |

These outcomes describe behavior and do not define technical enums.

## 29. Partial Completion

Partial analysis is permitted only when the completed portion is independently valid, useful to the bounded question, and clearly separated from incomplete or unsupported portions.

A partial output must state:

- what was completed;
- what was not completed;
- why it was not completed;
- which conclusions remain supported; and
- which conclusions cannot be made.

Partial completion must never appear as full success. An unsupported or failed portion must not weaken validation requirements for the completed portion.

## 30. Unsupported Scope Behavior

When a user requests non-e-commerce analysis, unsupported KPI domains, forecasting, causal inference, A/B Testing, unsupported connectors, autonomous actions, or other post-MVP capabilities, the Skill must:

1. identify the part that exceeds approved MVP scope;
2. avoid simulating or implying that the unsupported capability was performed;
3. identify any independently valid weaker analysis available within MVP scope; and
4. clearly distinguish that weaker analysis from the original request.

If no supported portion remains, the Skill stops with Unsupported Scope or Unsupported Claim Type as appropriate.

## 31. Data-Source Boundary

CSV, Excel, and SQLite are the only MVP source types.

The MVP does not include connector behavior for:

- PostgreSQL;
- MySQL;
- Shopify;
- Amazon;
- Shopee; or
- Taobao.

The Skill must not imply live connection, authentication, synchronization, or external API support for these systems. Those concerns belong to later phases.

## 32. Safety and Data-Handling Boundary

The Skill must preserve constitutional data-safety principles.

- Public examples, repositories, fixtures, demonstrations, and portfolio materials may use only synthetic or openly licensed data.
- The Skill must not imply that private, personal, proprietary, or confidential data is safe to publish in a public repository.
- Data limitations and known handling constraints that affect analytical use must be disclosed.
- The Skill must not fabricate public provenance or licensing status.

This section establishes behavioral boundaries only and does not define a security architecture.

## 33. Reuse Before Rebuild Boundary

The Skill must follow Reuse Before Rebuild. Required behavior must not depend on unnecessary custom infrastructure or custom reimplementation of commodity capabilities.

The differentiated CommerceLens behavior remains focused on:

- evidence-first orchestration;
- Metric discipline;
- Data Sufficiency;
- claim control;
- Alternative Explanations;
- Evidence linkage;
- deterministic execution dependency;
- validation dependency; and
- decision reliability.

This specification neither selects reusable components nor prescribes implementation choices.

## 34. Host Independence

This behavioral contract is conceptually host-independent. It must not depend on a specific ChatGPT, Claude, Codex, MCP, IDE, agent framework, or proprietary host implementation.

A future implementation may target a specific Skill environment, but the responsibilities, analytical gates, claim boundaries, and completion conditions defined here must remain reusable across hosts.

## 35. MVP Non-Responsibilities

In the MVP, the CommerceLens Skill is not responsible for:

- direct database-server integrations;
- marketplace account integrations;
- forecasting;
- causal inference;
- autonomous business execution;
- enterprise SaaS management;
- real-time monitoring;
- broad dashboard building;
- generic data science;
- general web research as analytical Evidence;
- prompt-only computation;
- replacing the Reusable Deterministic Analytics Engine;
- replacing deterministic validation; or
- replacing human decision ownership.

The Skill must not imply these responsibilities through wording, examples, or partial simulations.

## 36. Skill ↔ Engine Responsibility Matrix

| Capability | CommerceLens Skill | Deterministic Analytics Engine | Evidence Layer / Contract | Human User |
| --- | --- | --- | --- | --- |
| Business Question | Receives, interprets, and bounds the question. | No ownership of business intent. | Records the governed question and scope. | Supplies the question and relevant context. |
| Scope eligibility | Classifies the request against approved MVP boundaries. | No product-scope decision. | Records supported scope and exclusions where required. | May narrow or revise the request. |
| Clarification | Identifies and asks only material clarification. | May expose data facts that safely resolve ambiguity. | Preserves clarified assumptions and scope. | Resolves material business ambiguity. |
| Metric selection | Selects relevant authoritative Metrics for the bounded question. | Applies the authoritative definitions during computation. | Links Metrics and definitions to claims. | Supplies authoritative business context where required. |
| Metric computation | Specifies what must be computed; does not produce material numbers through language reasoning. | Computes Metric results deterministically. | Records the computation basis and result linkage. | Does not substitute unverified manual values for engine output. |
| Hypothesis generation | May propose clearly labeled candidate hypotheses. | Computes requested tests or aggregations that are in scope. | Distinguishes hypotheses from supported claims. | May supply domain hypotheses or known context. |
| Data Sufficiency | Defines required Evidence and applies the mandatory sufficiency gate. | Produces deterministic data-quality and structural results where required. | Represents sufficiency basis and unresolved gaps. | Provides missing data or clarification when available. |
| Analysis Plan | Produces a bounded, question-driven plan. | Receives the required deterministic analytical work conceptually. | Links planned steps to required Evidence. | Reviews business relevance where needed. |
| Numerical execution | Requests and tracks required execution; never treats planning as execution. | Produces material calculations and comparisons. | Captures execution Evidence and provenance. | Does not own computation merely by requesting it. |
| Validation | Requires applicable validation before Findings. | Performs deterministic validation. | Records validation status and relevant linkage. | May review business plausibility but does not replace deterministic validation. |
| Finding interpretation | Interprets validated results within claim boundaries. | Does not create narrative business conclusions. | Connects each material Finding to validated Evidence. | Reviews Findings in the business context. |
| Claim classification | Classifies and constrains claim strength. | Does not upgrade claim type. | Records supported claim type and basis. | May request a claim but cannot make unsupported Evidence sufficient. |
| Alternative Explanations | Identifies plausible, labeled alternatives without presenting them as proven. | Computes only approved analyses used to evaluate alternatives. | Distinguishes tested Evidence from untested alternatives. | May provide external context, subject to Evidence requirements. |
| Recommendation | Produces bounded decision support only when justified. | Supplies validated numerical basis; does not decide action. | Links Recommendations to Findings, Evidence, and Limitations. | Owns the final business decision. |
| Evidence linkage | Ensures material claims are traceable and capable of Evidence Contract representation. | Supplies reproducible execution and validation outputs. | Defines and carries the authoritative claim-to-Evidence relationship. | May inspect and challenge the Evidence basis. |
| Final business decision | Does not own or autonomously execute it. | No decision authority. | Preserves the Evidence supporting decision support. | Sole owner of the final decision and external action. |

## 37. Behavioral State Model

The CommerceLens workflow follows this conceptual, non-technical state progression:

Input Received  
↓  
Scope Check  
↓  
Clarification Required or Proceed  
↓  
Metric Definition  
↓  
Hypothesis / Required Evidence  
↓  
Data Sufficiency Check  
↓  
Analysis Plan  
↓  
Deterministic Execution  
↓  
Deterministic Validation  
↓  
Interpretation  
↓  
Completed

Behavioral branches apply as follows:

- Scope Check may lead to **Unsupported Scope** or **Unsupported Claim Type**.
- Clarification may pause progression at **Clarification Required**.
- Data Sufficiency may lead to **Insufficient Evidence**.
- Deterministic Execution may lead to **Execution Unavailable**, **Execution Failed**, or valid partial completion.
- Deterministic Validation may lead to **Validation Failed** or unresolved validation.
- Only validated Evidence permits affected material Findings during Interpretation.
- Only satisfaction of the completion contract permits **Completed**.

This model documents observable product behavior and is not a software state-machine design.

## 38. Canonical Workflow Walkthrough

The following conceptual walkthrough illustrates the contract without asserting that execution occurred or inventing any result.

1. **User question:** The user asks, “How did revenue performance change between two comparable periods, and which products or categories contributed most to that change?”
2. **Supported dataset:** The user supplies a CSV, Excel, or SQLite structured dataset relevant to the two periods.
3. **Scope check:** The Skill confirms that the question is within e-commerce MVP scope and requires bounded Descriptive and Diagnostic analysis, not causal inference.
4. **Metric definition:** The Skill selects Revenue, Orders, AOV, and relevant Product, Category, and Contribution concepts, using their authoritative Metric Dictionary definitions once available.
5. **Sufficiency check:** The Skill assesses whether required fields, valid records, product/category identifiers, and comparable period information are available. If not, it clarifies or states **“Insufficient evidence to conclude.”**
6. **Analysis Plan:** The Skill bounds the population and periods, identifies required Metric calculations and product/category Contribution Analysis, and defines the intended claim types and validation dependency.
7. **Deterministic execution request:** The Skill delegates all material totals, counts, averages, period comparisons, contributions, and rankings to the Reusable Deterministic Analytics Engine. No numerical result is assumed.
8. **Validation dependency:** Executed results must pass the applicable deterministic validation before supporting a material Finding.
9. **Evidence-backed Finding:** If validated Evidence exists, the Skill may describe the observed period change and identify leading product or category contributors without inventing values in this walkthrough.
10. **Contribution interpretation:** The Skill states that contribution describes observed attribution within the analysis and does not prove that a product or category caused the overall change.
11. **Alternative Explanation:** The Skill identifies a plausible alternative only as an untested possibility and states when external explanatory Evidence is unavailable.
12. **Bounded Recommendation:** If the Findings justify it, the Skill may recommend that the user review or investigate the validated high-contribution segments. It does not prescribe autonomous business action or imply causal certainty.
13. **Limitation:** The Skill discloses specific limitations arising from the dataset, period comparability, category mapping, execution, validation, or claim boundary.
14. **Evidence Contract handoff:** The Skill assembles the question, scope, Metrics, execution and validation basis, Findings, claim types, assumptions, Alternatives, Recommendation, and Limitations for representation under the future Evidence Contract.

No numerical Finding is produced in this walkthrough because no deterministic execution or validation Evidence is provided.

## 39. Acceptance Criteria

This specification passes review only if all of the following are true:

1. Skill responsibilities are explicit.
2. Engine responsibilities are explicit.
3. Skill and Engine cannot be confused.
4. Material numerical outputs require deterministic execution.
5. Executed Results and Validated Results are distinguished.
6. Fail-closed behavior is explicit.
7. Data Sufficiency is mandatory.
8. Hypotheses cannot become Findings without Evidence.
9. Contribution cannot be mislabeled as causation.
10. Recommendations are bounded by Evidence.
11. Human Decision Ownership is explicit.
12. MVP analytical scope remains narrow.
13. CSV, Excel, and SQLite remain the only MVP source types.
14. Unsupported capabilities are clearly handled.
15. Output responsibilities are explicit.
16. Successful completion is explicitly defined.
17. No Architecture or implementation design is introduced.
18. The specification remains host-independent.
19. No numerical results or external facts are fabricated.
20. The specification conforms to Constitution v1.1 and PRD v1.1.

Failure of any criterion prevents release as an approved or frozen specification.

## 40. Open Questions Reserved for Later Specifications

The following questions remain intentionally unresolved because they belong to later approved artifacts:

1. **Evidence Contract Specification:** What exact information structure, required relationships, and completeness rules will represent claim-to-Evidence traceability?
2. **Canonical Dataset + Metric Dictionary:** What are the authoritative formulas, field mappings, exclusions, aggregation rules, period rules, and edge-case treatments for each MVP Metric?
3. **Evaluation Fixtures:** What canonical valid, invalid, ambiguous, insufficient, execution-failure, and validation-failure cases will verify this behavioral contract?
4. **Architecture:** How will the host, Skill, Reusable Deterministic Analytics Engine, validation capabilities, and Evidence layer realize this contract without changing its responsibility boundaries?

These questions do not reopen the Skill-first strategy, deterministic execution requirement, inclusion of both Skill and Engine in MVP, or the approved narrow canonical workflow.

## 41. Traceability

This specification derives conceptually from the following authoritative documents:

| Governing document | Concepts carried into this specification |
| --- | --- |
| `PROJECT_MASTER_INSTRUCTIONS.md` v1.1 | Evidence First; no material claim without traceable Evidence; deterministic execution and validation; claim discipline; Data Sufficiency; reproducibility; transparent Limitations; Human Decision Ownership; Reuse Before Rebuild; Skill-first governance. |
| `PRD.md` v1.1 | Canonical MVP Business Question; narrow e-commerce analytical scope; MVP Metrics and capabilities; supported source types; product output and completion expectations; non-MVP boundaries. |
| `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md` | GO decision for the Skill-first strategy; CommerceLens Skill as the user-facing layer; Reusable Deterministic Analytics Engine dependency; decision-reliability orientation; mandatory approved development constraints. |

This traceability is conceptual because this specification does not invent requirement identifiers or section mappings absent from the governing documents.

## 42. Release Boundary

This v1.0 document is **Approved** and **Frozen**.

Approval and Freeze of this specification authorize progression ONLY to the next artifact in the approved project sequence:

`EVIDENCE_CONTRACT_SPECIFICATION.md`

They do NOT authorize skipping ahead to:

- Canonical Dataset + Metric Dictionary;
- Dataset implementation;
- Evaluation Fixtures;
- Architecture;
- `SKILL.md`;
- code; or
- implementation
