# CommerceLens AI PRD v1.1

**Version:** v1.1  
**Status:** Approved  
**State:** Frozen  
**Amendment:** Skill-first Strategy  
**Owner:** CommerceLens AI Product  
**Last Updated:** 2026-08-20  
**Governing Document:** `PROJECT_MASTER_INSTRUCTIONS.md` v1.1  
**Approved Migration Record:** `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md`

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Product Vision Alignment](#2-product-vision-alignment)
3. [Constitution Reference](#3-constitution-reference)
4. [Problem Statement](#4-problem-statement)
5. [Goals](#5-goals)
6. [Non-goals](#6-non-goals)
7. [Target Users](#7-target-users)
8. [User Personas](#8-user-personas)
9. [User Stories](#9-user-stories)
10. [Jobs To Be Done](#10-jobs-to-be-done)
11. [Canonical MVP Business Question](#11-canonical-mvp-business-question)
12. [Core User Journey](#12-core-user-journey)
13. [Functional Requirements](#13-functional-requirements)
14. [Non-functional Requirements](#14-non-functional-requirements)
15. [MVP Scope](#15-mvp-scope)
16. [Out of Scope](#16-out-of-scope)
17. [User Workflow](#17-user-workflow)
18. [Product Success Definition](#18-product-success-definition)
19. [Success Metrics](#19-success-metrics)
20. [Acceptance Criteria](#20-acceptance-criteria)
21. [Risks](#21-risks)
22. [Assumptions](#22-assumptions)
23. [Future Roadmap](#23-future-roadmap)
24. [Open Questions](#24-open-questions)
25. [Version Notes](#25-version-notes)

## 1. Product Overview

CommerceLens AI is an evidence-first e-commerce analytics Skill powered by a reusable deterministic analytics engine.

The CommerceLens Skill is the primary user-facing analytical interface. It helps users state a business question, clarify material ambiguity, define metrics, identify required evidence, plan analysis, interpret validated results, and produce decision-support reports.

The Reusable Deterministic Analytics Engine is the execution and validation authority. Material numerical findings must originate from deterministic execution, validation, and traceable evidence rather than language reasoning alone.

CommerceLens continues to serve the broader purpose of evidence-driven e-commerce decision intelligence. It is not a generic data analyst agent, generic AI assistant, chat-with-CSV tool, Text-to-SQL demo, dashboard generator, autonomous decision maker, or prompt-only Skill.

## 2. Product Vision Alignment

This PRD is governed by `PROJECT_MASTER_INSTRUCTIONS.md` v1.1, the Product Constitution of CommerceLens AI.

CommerceLens AI must preserve the constitutional principle:

> No material claim without traceable evidence.

The product experience must enforce the required analytical workflow:

1. Business Question
2. Metric Definition
3. Hypothesis Generation
4. Required Evidence
5. Data Sufficiency Check
6. Analysis Plan
7. SQL, Python, or Statistical Execution
8. Deterministic Validation
9. Findings
10. Alternative Explanations
11. Recommendation
12. Limitations
13. Evidence Contract

The Skill-first strategy changes the delivery mechanism. It does not weaken analytical rigor.

The PRD defines what the product must provide. It does not define implementation architecture, database schema, API behavior, code structure, prompt design, Skill host mechanics, or evidence serialization.

## 3. Constitution Reference

This PRD inherits all governing principles defined in `PROJECT_MASTER_INSTRUCTIONS.md` v1.1.

It does not redefine those principles.

Where conflicts exist, the Constitution prevails.

## 4. Problem Statement

E-commerce teams often ask business questions from structured data but receive answers that are difficult to trust because metrics are undefined, source data is unclear, analysis periods are ambiguous, calculations are not reproducible, and limitations are omitted.

Generic AI analysis tools can make this problem worse by producing fluent summaries without proving that claims are supported by executed analysis. Traditional dashboards can show metrics, but they often do not explain whether a business conclusion is justified, what evidence was required, or what alternative explanations remain.

CommerceLens AI addresses this gap by making evidence traceability, deterministic execution, data sufficiency, and analytical discipline part of the product experience.

## 5. Goals

- Enable users to complete one narrow evidence-first e-commerce analytical workflow through the CommerceLens Skill.
- Support the canonical revenue-performance question using CSV, Excel, and SQLite inputs.
- Require every material analytical claim to include or reference traceable evidence.
- Define metrics before they are used in findings or recommendations.
- Check data sufficiency before presenting material conclusions.
- Require material numerical findings to originate from deterministic execution and validation.
- Distinguish descriptive, diagnostic, predictive, causal, and prescriptive claims.
- Produce reproducible analytical outputs suitable for public GitHub review using synthetic or openly licensed data.
- Prove the Skill-first model through a working CommerceLens Skill and Reusable Deterministic Analytics Engine vertical slice.
- Prioritize MVP depth, reliability, and correctness over breadth or technical novelty.

## 6. Non-goals

- Build a general-purpose AI assistant.
- Build a generic chat-with-CSV tool.
- Build a dashboard generator.
- Build a Text-to-SQL demo as the primary product.
- Build a prompt-only or documentation-only Skill.
- Build a fully autonomous decision maker.
- Build a standalone SaaS or dedicated web application as a required MVP delivery surface.
- Build enterprise integrations, streaming analytics, account-based SaaS administration, billing, or tenancy.
- Build Multi-Agent, RAG, vector database, complex agent framework, LLM router, memory framework, plugin ecosystem, or multiple-LLM architecture features in the MVP.
- Build a broad statistical workbench or general data science platform.
- Require external marketplace connectors for MVP.
- Provide predictive, causal, or prescriptive claims when available evidence only supports descriptive or bounded diagnostic analysis.
- Execute pricing, inventory, marketing, marketplace, transaction, or other external business actions.
- Replace analyst judgment or human business accountability.

## 7. Target Users

CommerceLens AI serves users who need credible e-commerce analysis from structured data:

- E-commerce founders and operators with structured performance data and concrete business questions.
- Data analysts and business analysts who need reproducible evidence-backed outputs.
- Product, category, merchandising, growth, and operations teams that need decision support.
- Portfolio reviewers evaluating evidence-first analytics work, executable implementation, tests, failure cases, and reproducibility.
- Future contributors extending the product after the MVP vertical slice is reliable.

MVP users may not want to manually write SQL or Python, but they still require evidence-backed outputs and must retain final decision ownership.

## 8. User Personas

### 8.1 E-commerce Operator

**Profile:** Runs or manages an online store and needs to understand business performance without building a full analytics stack.

**Primary needs:**

- Provide structured e-commerce data in an approved MVP format.
- Understand revenue, orders, AOV, and product or category contribution across comparable periods.
- Know which findings are supported by data and which are only hypotheses.
- Receive recommendations only when evidence justifies them.

**Success condition:** Can make a better-informed business decision with clear evidence, limitations, and human ownership of the final action.

### 8.2 Data Analyst

**Profile:** An analyst responsible for turning business questions into validated findings and stakeholder-ready reporting.

**Primary needs:**

- Define metrics consistently.
- Validate calculations and data quality.
- Inspect whether material results came from deterministic execution.
- Preserve reproducibility across analyses.
- Communicate limitations and alternative explanations clearly.

**Success condition:** Can produce an evidence-backed analytical output faster without weakening analytical standards.

### 8.3 Product or Category Manager

**Profile:** Owns product mix, category performance, pricing, inventory, or merchandising decisions.

**Primary needs:**

- Understand which products or categories contributed most to a revenue change.
- Compare comparable periods responsibly.
- Identify where data is insufficient for stronger recommendations.

**Success condition:** Can prioritize investigation or business action based on validated findings and explicit limitations.

### 8.4 Portfolio Reviewer

**Profile:** Reviews the project as evidence of product analytics, business analysis, AI-assisted workflow, and analytical rigor.

**Primary needs:**

- Understand the product purpose quickly.
- See clear MVP boundaries.
- Verify that the Skill is backed by deterministic execution rather than prompt-only reasoning.
- Review tests, failure cases, deterministic results, and Evidence Contract output.

**Success condition:** Can evaluate CommerceLens AI as a credible analytics product rather than a generic AI demo.

## 9. User Stories

- As an e-commerce operator, I want to provide structured e-commerce data so that I can answer a concrete business question using my own records.
- As an e-commerce operator, I want CommerceLens to clarify only material ambiguity so that metric definitions and comparison periods are correct before analysis.
- As an e-commerce operator, I want the system to define revenue, orders, and AOV before analysis so that I understand how performance change is measured.
- As a data analyst, I want every material numerical finding to reference deterministic execution and validation status so that I can audit the result.
- As a data analyst, I want the system to flag missing, ambiguous, or insufficient fields so that unsupported conclusions are not presented as findings.
- As a product manager, I want to compare product and category contribution across two comparable periods so that I can identify where performance changes are concentrated.
- As a category manager, I want alternative explanations and limitations so that I do not overinterpret descriptive or bounded diagnostic results.
- As a business user, I want recommendations to remain proportional to the evidence so that I do not act on unsupported claims.
- As a portfolio reviewer, I want the public demo to use synthetic or openly licensed data so that the project can be reviewed safely.
- As a portfolio reviewer, I want the repository to include executable implementation, tests, expected outputs, and an Evidence Contract so that the claimed workflow is reproducible.
- As a future contributor, I want requirements and scope boundaries to be explicit so that I can extend the product without violating the Constitution.

## 10. Jobs To Be Done

- When I have structured e-commerce performance data and a business performance question, I want CommerceLens to guide and execute a rigorous evidence-first analysis so that I can understand what changed, identify the strongest supported contributors, and make a better-informed decision without manually assembling the entire analytical workflow.
- When a metric is used in a finding, I want to see its definition so I can determine whether the conclusion is meaningful.
- When the Skill presents a number, I want to trace it to deterministic execution, validation, and reproducibility information so I can audit or rerun it.
- When the data is incomplete, ambiguous, or unsuitable, I want the product to say so clearly so I do not act on unsupported claims.
- When a recommendation is presented, I want to understand the evidence strength, assumptions, tradeoffs, alternative explanations, and limitations so I can decide whether to act.
- When I review or revisit an analysis, I want a traceable Evidence Contract so I can audit how the conclusion was produced.

## 11. Canonical MVP Business Question

The first MVP must prove one canonical analytical workflow:

> How did revenue performance change between two comparable periods, and which products or categories contributed most to that change?

This question is the reference workflow for MVP acceptance and evaluation.

The MVP analytical scope is limited to:

- Revenue
- Orders
- Average Order Value
- Product performance
- Category performance
- Period-over-period change
- Contribution analysis
- Bounded descriptive analysis
- Bounded diagnostic analysis

## 12. Core User Journey

The core Skill-first product journey is:

```text
Invoke CommerceLens Skill
↓
Provide Dataset
↓
State Business Question
↓
Clarify Material Ambiguity if Required
↓
Data Validation
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
Evidence Review
↓
Findings
↓
Alternative Explanations
↓
Recommendation if Justified
↓
Limitations
↓
Evidence Contract
↓
Report / Structured Output
```

This is a product journey. It does not specify UI screens, APIs, function calls, classes, tool schemas, prompts, or host-specific Skill mechanics.

## 13. Functional Requirements

### 13.1 Core Requirements

| Requirement ID | Description | Business Value | Priority | Dependencies | Related Constitution | Related Architecture | Acceptance Criteria |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CORE-001 | Enforce the evidence-first analytical workflow for every material analysis. | Prevents unsupported conclusions and preserves product trust. | Core | Constitution | v1.1 Product Principles; Analytical Workflow | TBD | Every material output follows the workflow from Business Question through Evidence Contract, or explicitly states why a step cannot be completed. |
| CORE-002 | Require metric definitions before metrics appear in findings. | Ensures users understand what each KPI means before acting on it. | Core | CORE-001 | v1.1 Terminology; Evidence Standard | TBD | Each material finding that uses a metric references a metric definition, calculation basis, and analysis period. |
| CORE-003 | Classify material claims as descriptive, diagnostic, predictive, causal, or prescriptive. | Prevents correlation from being overstated as causation or recommendation. | Core | CORE-001 | v1.1 Claim Taxonomy | TBD | Every material claim has a visible claim type or is grouped under a section with an explicit claim type. |
| CORE-004 | Perform data sufficiency checks before material conclusions. | Prevents findings from unsupported, incomplete, stale, ambiguous, or unsuitable data. | Core | CORE-001, CORE-002, CORE-003 | v1.1 Evidence Standard; Data Sufficiency | TBD | The output includes sufficiency status and blocks or downgrades conclusions when required evidence is missing. |
| CORE-005 | Produce or reference an Evidence Contract for each material analytical output. | Makes analysis traceable, reproducible, and auditable. | Core | CORE-001 to CORE-004 | v1.1 Evidence Contract Requirements | TBD | Evidence Contract references business question, claim type, metrics, source, analysis period, executed method, result, validation, assumptions, limitations, alternative explanations, and recommendation where applicable. |
| CORE-006 | State "Insufficient evidence to conclude" when evidence cannot support the requested conclusion. | Protects analytical correctness and user decision quality. | Core | CORE-004 | v1.1 Vision & Mission; Evidence Standard | TBD | Unsupported material conclusions are not presented as findings; insufficiency is stated clearly with missing evidence. |
| CORE-007 | Separate findings, hypotheses, recommendations, limitations, and alternative explanations. | Helps users distinguish what is proven, possible, actionable, and uncertain. | Core | CORE-003, CORE-005 | v1.1 Analytical Workflow; Transparent Limitations | TBD | Output sections do not mix unsupported hypotheses with validated findings or recommendations. |
| CORE-008 | Preserve human decision ownership. | Prevents CommerceLens from becoming an autonomous business-action system. | Core | CORE-003, CORE-007 | v1.1 Human Decision Ownership | TBD | Product language states that CommerceLens provides decision support and that the human user owns final analytical and business decisions. |
| CORE-009 | Require deterministic execution for material numerical findings. | Prevents fluent but unexecuted analysis from being treated as evidence. | Core | CORE-005 | v1.1 Deterministic Validation; Technical Philosophy | TBD | Material numerical findings originate from deterministic execution and include validation state; generated code or planned analysis alone is not accepted as evidence. |

### 13.2 MVP Requirements

| Requirement ID | Description | Business Value | Priority | Dependencies | Related Constitution | Related Architecture | Acceptance Criteria |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MVP-001 | Support structured e-commerce data from CSV files. | Enables the simplest public and user-owned data workflow. | MVP | CORE-001 | v1.1 MVP Data Sources | TBD | User can complete the canonical analysis with a valid CSV dataset. |
| MVP-002 | Support structured e-commerce data from Excel files. | Matches common analyst and operator workflows. | MVP | CORE-001 | v1.1 MVP Data Sources | TBD | User can complete the canonical analysis with a valid Excel dataset. |
| MVP-003 | Support structured e-commerce data from SQLite files. | Enables reproducible local analytical workflows. | MVP | CORE-001 | v1.1 MVP Data Sources | TBD | User can complete the canonical analysis with a valid SQLite dataset without requiring external database connectors. |
| MVP-004 | Support the canonical revenue-performance workflow across two comparable periods. | Proves one credible end-to-end analytical vertical slice. | MVP | MVP-001 to MVP-003, CORE-002 | v1.1 MVP Definition; MVP Depth Over Feature Breadth | TBD | Product analyzes revenue, orders, AOV, product contribution, and category contribution for the approved canonical question. |
| MVP-005 | Identify required fields and field semantics for the canonical analysis. | Helps users understand whether their data can answer the business question. | MVP | CORE-004, MVP-004 | v1.1 Data Sufficiency | TBD | Product lists required fields and marks missing, ambiguous, incompatible, or unusable fields before conclusions. |
| MVP-006 | Provide business-question understanding and material ambiguity handling. | Prevents incorrect metric scope, period comparison, or interpretation. | MVP | MVP-005 | v1.1 CommerceLens Skill Responsibilities | TBD | The Skill requests clarification when ambiguity would materially affect metrics, scope, comparison period, or interpretation. |
| MVP-007 | Define metrics before analysis. | Ensures KPI meaning is clear before execution and findings. | MVP | CORE-002, MVP-004 | v1.1 Evidence Standard | TBD | Revenue, orders, AOV, product contribution, and category contribution are defined before findings are presented. |
| MVP-008 | Generate hypotheses and identify required evidence without presenting hypotheses as findings. | Guides analysis while protecting claim discipline. | MVP | CORE-003, CORE-007 | v1.1 Analytical Workflow; Claim Taxonomy | TBD | Hypotheses are labeled as hypotheses and only converted to findings after sufficient deterministic evidence exists. |
| MVP-009 | Produce a bounded analysis plan before findings. | Makes analytical reasoning reviewable before conclusions are presented. | MVP | MVP-005 to MVP-008 | v1.1 Analytical Workflow | TBD | Output includes planned metrics, comparisons, segments, periods, required evidence, claim boundaries, and validation expectations at a product level. |
| MVP-010 | Require deterministic engine execution for approved material computations. | Establishes the engine as execution authority. | MVP | CORE-009, MVP-009 | v1.1 Reusable Deterministic Analytics Engine | TBD | Material revenue, order, AOV, and contribution outputs reference deterministic execution evidence and cannot be based on Skill reasoning alone. |
| MVP-011 | Require deterministic validation status for calculations and data quality checks. | Builds confidence that numbers are calculated and checked rather than inferred. | MVP | MVP-010 | v1.1 Deterministic Validation; Reproducibility | TBD | Material numerical outputs show validation status and do not appear as findings when validation fails or is unavailable. |
| MVP-012 | Support execution integrity behavior. | Prevents planned, failed, unavailable, or partial execution from being represented as completed analysis. | MVP | MVP-010, MVP-011 | v1.1 Unsupported Claims; Deterministic Validation | TBD | Generated code is not evidence of execution; planned analysis is not completed analysis; failed, unavailable, or partial execution is not represented as successful or complete. |
| MVP-013 | Fail closed when required evidence, execution, or validation is insufficient. | Protects users from acting on unsupported outputs. | MVP | CORE-004, CORE-006, MVP-012 | v1.1 Evidence Standard; Transparent Limitations | TBD | Product returns explicit states such as clarification required, insufficient evidence, execution failed, validation failed, or unsupported claim type when applicable. |
| MVP-014 | Interpret validated evidence within claim boundaries. | Converts deterministic results into useful but bounded decision support. | MVP | CORE-003, CORE-007, MVP-011 | v1.1 Claim Taxonomy | TBD | Findings are consistent with validated results and do not overstate descriptive or bounded diagnostic evidence as causal or predictive. |
| MVP-015 | Include alternative explanations for material diagnostic findings. | Prevents overconfident interpretation of performance drivers. | MVP | CORE-007, MVP-014 | v1.1 Transparent Limitations; Analytical Workflow | TBD | Diagnostic findings include plausible alternative explanations and indicate whether available data can test them. |
| MVP-016 | Provide recommendations only when justified by evidence. | Makes outputs decision-useful without transferring decision ownership. | MVP | CORE-008, MVP-014, MVP-015 | v1.1 Human Decision Ownership; Evidence Strength | TBD | Recommendations are linked to validated findings, assumptions, limitations, and evidence strength; unsupported recommendations are blocked or downgraded. |
| MVP-017 | Generate an evidence-backed report or structured output. | Converts analysis into decision-ready communication. | MVP | CORE-005, MVP-016 | v1.1 MVP Output; Evidence Contract Requirements | TBD | Output contains business question, metric definitions, data sufficiency, analysis plan, execution and validation status, findings, alternatives, limitations, recommendation if justified, and Evidence Contract reference. |
| MVP-018 | Support public demo datasets that are synthetic or openly licensed only. | Enables GitHub-ready portfolio publishing without exposing private data. | MVP | Data safety policy | v1.1 MVP Data Sources; Documentation Standard | TBD | Public demo materials contain no private company data, customer data, proprietary URLs, real scraping outputs, or confidential records. |
| MVP-019 | Provide explicit scope labels for features and analytical capabilities. | Keeps contributors aligned with MVP depth over breadth. | MVP | Governance model | v1.1 Governance Model | TBD | Features in PRD and future specs are classified as Core, MVP, Phase 2, Phase 3, Research, Backlog, or Rejected. |
| MVP-020 | Require bounded evaluation fixtures before MVP release. | Makes reliability testable without promoting the full benchmark into MVP. | MVP | MVP-004, MVP-013 | v1.1 Decision Reliability Benchmark; MVP Definition | TBD | PRD requires later fixtures for valid canonical data, missing required fields, ambiguous mapping, insufficient comparison data, calculation mismatch, execution failure, unsupported causal or predictive requests, excessive recommendation, and reproducibility checks. |
| MVP-021 | Require a demonstrable and reproducible public release. | Supports credible public review without claiming external success. | MVP | MVP-018, MVP-020 | v1.1 Documentation Standard; Reproducibility | TBD | Public repository can show executable implementation, canonical synthetic example, deterministic results, tests, bounded evaluation cases, Evidence Contract output, clear limitations, and reproducible workflow. |

### 13.3 Phase 2 Requirements

| Requirement ID | Description | Business Value | Priority | Dependencies | Related Constitution | Related Architecture | Acceptance Criteria |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P2-001 | Add guided business question templates for common e-commerce decisions. | Reduces user ambiguity while preserving analytical discipline. | Phase 2 | MVP workflow reliability | v1.1 Product Scope; Analytical Workflow | TBD | Templates are mapped to required metrics, evidence needs, and claim types. |
| P2-002 | Add saved analysis history for reproducible review. | Helps users revisit prior decisions and compare outputs over time. | Phase 2 | Evidence Contract reliability | v1.1 Reproducibility; Evidence Contract Requirements | TBD | Saved records preserve the Evidence Contract and analysis context. |
| P2-003 | Expand analytics to discounts, refunds, gross margin, inventory, stockouts, customer repeat purchase, cohort analysis, confidence intervals, hypothesis testing, and correlation only where evidence rules are defined. | Improves decision value after the first workflow is reliable. | Phase 2 | MVP credibility; metric definitions | v1.1 Claim Taxonomy; Transparent Limitations | TBD | Each expanded capability has explicit metric definitions, sufficiency rules, validation expectations, and claim boundaries. |
| P2-004 | Add PostgreSQL and MySQL as optional read-oriented data sources. | Supports more realistic business workflows after file-based reliability is proven. | Phase 2 | Stable engine boundary; data safety review | v1.1 MVP Depth Over Feature Breadth; Product Boundaries | TBD | Connectors do not block MVP and include provenance, read-only expectations, and evidence traceability requirements at product level. |
| P2-005 | Add richer diagnostic workflows for product and category performance. | Increases decision value while preserving bounded interpretation. | Phase 2 | MVP-014, MVP-015 | v1.1 Claim Taxonomy; Evidence Strength | TBD | Diagnostic outputs include segmentation, comparisons, alternative explanations, and causal limitations. |

### 13.4 Phase 3 Requirements

| Requirement ID | Description | Business Value | Priority | Dependencies | Related Constitution | Related Architecture | Acceptance Criteria |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P3-001 | Evaluate Shopify connector support. | May reduce user setup friction after local workflow reliability is proven. | Phase 3 | Phase 2 stability; connector review | v1.1 Product Boundaries; Data Safety | TBD | Connector has a documented evidence-first use case and does not introduce autonomous business execution. |
| P3-002 | Evaluate Amazon Seller / SP-API connector support. | May support advanced seller analytics after core reliability is proven. | Phase 3 | Phase 2 stability; official access review | v1.1 Product Boundaries; Data Safety | TBD | Connector scope, authorization, reproducibility snapshot strategy, and metric mapping are reviewed before approval. |
| P3-003 | Explore full Decision Reliability Benchmark expansion after core workflows are stable. | Measures analytical correctness and evidence reliability at broader scale. | Phase 3 | MVP fixtures; evaluated workflow stability | v1.1 Decision Reliability Benchmark | TBD | Benchmark scope is documented separately and does not redefine PRD requirements. |
| P3-004 | Evaluate limited visual interface or dashboard support only after Skill plus engine reliability is proven. | May improve comprehension without becoming the MVP success criterion. | Phase 3 | MVP credibility | v1.1 MVP Depth Over Feature Breadth | TBD | Visual work supports evidence comprehension and does not replace execution, validation, or Evidence Contract requirements. |

### 13.5 Research Requirements

| Requirement ID | Description | Business Value | Priority | Dependencies | Related Constitution | Related Architecture | Acceptance Criteria |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RES-001 | Research Shopee, Taobao, and broader marketplace connector feasibility. | May identify future regional e-commerce data sources. | Research | Official API access; use-case validation | v1.1 Product Boundaries; Data Safety | TBD | No connector is approved until official access, data semantics, permissions, and evidence value are documented. |
| RES-002 | Research cross-host Skill portability and execution availability. | Determines whether the Skill can remain delivery-mechanism portable. | Research | MVP implementation evidence | v1.1 CommerceLens Skill; Reuse Before Rebuild | TBD | Compatibility claims are not made until tested in supported environments. |
| RES-003 | Research whether heavier data quality or profiling libraries reduce product risk. | May reduce implementation burden if provenance remains clear. | Research | MVP check inventory | v1.1 Reuse Before Rebuild; Evidence Traceability | TBD | Adoption requires documented fit, dependency cost, provenance behavior, and evidence-first alignment. |

### 13.6 Backlog Requirements

| Requirement ID | Description | Business Value | Priority | Dependencies | Related Constitution | Related Architecture | Acceptance Criteria |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BACKLOG-001 | Explore broader predictive analysis. | Potential future value for planning workflows. | Backlog | Stable descriptive and diagnostic workflows | v1.1 Claim Taxonomy; Evidence Strength | TBD | Not started until forecasting evidence requirements and validation rules are approved. |
| BACKLOG-002 | Explore causal analysis workflows. | Potential future value for experiment and intervention analysis. | Backlog | Approved causal design requirements | v1.1 Claim Taxonomy | TBD | Not started from ordinary transaction data without appropriate causal evidence standards. |
| BACKLOG-003 | Explore A/B testing workflows. | Potential future value for controlled experiment analysis. | Backlog | Experiment design specification | v1.1 Claim Taxonomy; Evidence Standard | TBD | Not started until assignment, power, interference, metric, and interpretation requirements are defined. |

### 13.7 Rejected Requirements

| Requirement ID | Description | Business Value | Priority | Dependencies | Related Constitution | Related Architecture | Acceptance Criteria |
| --- | --- | --- | --- | --- | --- | --- | --- |
| REJ-001 | Multi-Agent system for the MVP. | Not aligned with MVP depth or necessary for evidence-first validation. | Rejected | None | v1.1 Product Boundaries; MVP Depth Over Feature Breadth | TBD | Not included unless the Constitution is revised or a future approved requirement justifies it. |
| REJ-002 | RAG or vector database for the MVP. | Not required for structured CSV, Excel, or SQLite e-commerce analytics. | Rejected | None | v1.1 Product Boundaries; MVP Definition | TBD | Not included in MVP scope. |
| REJ-003 | Plugin ecosystem for the MVP. | Adds breadth before core analytical reliability is proven. | Rejected | None | v1.1 Product Boundaries; Governance Model | TBD | Not included in MVP scope. |
| REJ-004 | Enterprise SaaS administration, permissions, billing, and tenant management for the MVP. | Distracts from proving the evidence workflow. | Rejected | None | v1.1 Product Scope; MVP Definition | TBD | Not included in MVP scope. |
| REJ-005 | Streaming analytics or real-time monitoring for the MVP. | Outside structured file-based MVP scope. | Rejected | None | v1.1 MVP Definition; Product Boundaries | TBD | Not included in MVP scope. |
| REJ-006 | Autonomous decision execution. | Conflicts with human decision ownership. | Rejected | None | v1.1 Human Decision Ownership | TBD | Product does not execute pricing, inventory, marketing, marketplace, transaction, or other external business actions on behalf of users. |
| REJ-007 | General chatbot experience. | Dilutes the evidence-first analytical workflow. | Rejected | None | v1.1 Product Scope; Analytical Workflow | TBD | Product is not positioned or designed as a general chatbot. |
| REJ-008 | Enterprise BI platform. | Expands the product beyond focused decision intelligence. | Rejected | None | v1.1 Product Scope; MVP Depth Over Feature Breadth | TBD | Product does not become a broad BI platform in the MVP. |
| REJ-009 | Complex agent framework, LLM router, or memory framework for MVP. | Adds infrastructure before evidence workflow reliability is proven. | Rejected | None | v1.1 Product Boundaries; Reuse Before Rebuild | TBD | Not included unless later evidence demonstrates a necessary product gap. |
| REJ-010 | Prompt-only CommerceLens Skill. | Violates deterministic execution and evidence-first requirements. | Rejected | None | v1.1 Product Scope; Deterministic Validation | TBD | Skill cannot pass MVP without engine-backed execution, validation, and evidence traceability. |

## 14. Non-functional Requirements

| Requirement ID | Description | Priority | Acceptance Criteria |
| --- | --- | --- | --- |
| NFR-001 | Analytical correctness must take priority over completeness, speed, or presentation polish. | Core | Unsupported answers are blocked, downgraded, or labeled as insufficient evidence. |
| NFR-002 | Outputs must be reproducible from declared data sources, metric definitions, analysis period, and deterministic procedures. | Core | Material outputs include enough evidence metadata for review and rerun planning. |
| NFR-003 | Product language must preserve uncertainty. | Core | Reports distinguish confirmed findings, directional findings, hypotheses, insufficient evidence, and recommendations. |
| NFR-004 | Evidence traceability must be preserved for material outputs. | Core | Material claims can be traced to metric definitions, source data, analysis period, executed method, validation state, assumptions, limitations, and Evidence Contract. |
| NFR-005 | Failure behavior must be safe and explicit. | Core | Missing fields, material ambiguity, insufficient data, execution failure, validation failure, unavailable evidence, and unsupported claim types produce blocked, downgraded, or explicit failure outcomes. |
| NFR-006 | Public artifacts must be safe for GitHub review. | MVP | Public examples use synthetic or openly licensed data and avoid private, proprietary, or personally identifiable data. |
| NFR-007 | Product requirements must describe capabilities rather than demand custom implementations of commodity infrastructure. | Core | PRD does not require custom spreadsheet parsing, SQL engines, DataFrame systems, statistics libraries, or chart rendering unless justified by evidence-first requirements. |
| NFR-008 | MVP maintainability and testability must support a complete first analytical workflow. | MVP | The canonical workflow can be evaluated against bounded positive and negative fixtures. |
| NFR-009 | Visual presentation must not outrank analytical reliability. | Core | UI, dashboard, or report polish work is deprioritized when it conflicts with correctness, traceability, or reproducibility. |
| NFR-010 | Data safety must remain compatible with public demonstration and user-owned analysis. | Core | Public examples are synthetic or openly licensed, and future data-source expansion requires data-safety review. |

## 15. MVP Scope

The MVP must prove one complete Skill-orchestrated, deterministic-engine-executed, evidence-backed, reproducible e-commerce analytical workflow.

### 15.1 Included

- CommerceLens Skill as the primary user-facing analytical interface.
- Reusable Deterministic Analytics Engine as the execution and validation authority.
- CSV, Excel, and SQLite structured data sources.
- Canonical business question: "How did revenue performance change between two comparable periods, and which products or categories contributed most to that change?"
- Revenue, orders, AOV, product performance, category performance, period-over-period change, and contribution analysis.
- Bounded descriptive analysis and bounded diagnostic analysis.
- Business question understanding and material ambiguity clarification.
- Metric definition before analysis.
- Hypothesis generation as analysis guidance, not findings.
- Required evidence identification.
- Data sufficiency check.
- Analysis plan.
- Deterministic execution and validation status.
- Execution integrity and fail-closed behavior.
- Evidence-backed findings.
- Alternative explanations.
- Limitations.
- Recommendations only when justified.
- Evidence Contract.
- Bounded evaluation-fixture requirement for MVP release.
- Synthetic or openly licensed demo data for public review.
- Reproducible public demonstration with executable implementation, tests, expected outputs, and limitations.

### 15.2 Excluded From MVP

- Full analytical breadth across all e-commerce KPI areas.
- Gross margin, discounts, refunds, inventory, stockouts, customer retention, repeat purchase, cohort analysis, confidence intervals, hypothesis testing, general correlation analysis, A/B testing, predictive analysis, and causal analysis as required MVP capabilities.
- PostgreSQL, MySQL, Shopify, Amazon Seller / SP-API, Shopee, Taobao, or other external connectors.
- Full Decision Reliability Benchmark implementation.
- Standalone SaaS infrastructure or dedicated dashboard as a required delivery surface.
- Enterprise administration, billing, permissions, tenancy, and account management.
- Real-time or streaming analytics.
- Multi-Agent systems.
- RAG.
- Vector databases.
- Complex agent frameworks.
- LLM routers.
- Memory frameworks.
- Plugin ecosystems.
- Autonomous business action execution.
- Broad non-e-commerce domains.
- Visual polish that delays analytical reliability.

## 16. Out of Scope

The following are out of scope until formally reclassified:

- General business intelligence across unrelated domains.
- Automated scraping from real retailers.
- Private customer data exposure in public demos.
- Production data warehouse design.
- API contract design.
- Database schema design.
- Prompt engineering specifications.
- Skill host mechanics.
- Model orchestration strategy.
- Evidence serialization design.
- Module or directory structure.
- Forecasting or causal inference as default behavior.
- Legal, financial, or compliance advice.
- Claims that Skill-first will automatically produce GitHub stars, recruiter interest, market adoption, user demand, or commercial success.

## 17. User Workflow

### 17.1 Standard Skill-first Workflow

| Stage | Product Responsibility |
| --- | --- |
| Invoke CommerceLens Skill | Start the evidence-first analytical workflow through the Skill interface. |
| Provide Dataset | Accept only approved MVP data source types: CSV, Excel, and SQLite. |
| State Business Question | Capture the business decision need and requested analytical objective. |
| Clarify Material Ambiguity | Request clarification only when ambiguity materially affects metrics, scope, comparison periods, or interpretation. |
| Data Validation | Inspect whether available data can support the requested canonical analysis. |
| Metric Definition | Define revenue, orders, AOV, product contribution, and category contribution before findings. |
| Hypothesis / Required Evidence | Generate candidate explanations as hypotheses and identify evidence required for supported claims. |
| Data Sufficiency Check | Determine whether available data can support descriptive or bounded diagnostic conclusions. |
| Analysis Plan | Specify the bounded analytical plan at product level before execution. |
| Deterministic Execution | Require material numerical computation through the deterministic engine. |
| Deterministic Validation | Validate calculations and data-quality checks before material findings are presented. |
| Evidence Review | Review sufficiency, validation, assumptions, limitations, alternative explanations, and claim boundaries. |
| Findings | Present only evidence-supported conclusions with clear claim type. |
| Alternative Explanations | Identify plausible alternative explanations and whether available data can test them. |
| Recommendation if Justified | Provide action guidance only when proportional to the evidence. |
| Limitations | Communicate material data, metric, execution, and interpretation limitations. |
| Evidence Contract | Produce or reference traceability sufficient for audit and reproduction. |
| Report / Structured Output | Produce decision-ready output without replacing human decision ownership. |

### 17.2 Insufficient Evidence and Failure Workflow

1. User asks a question that available data, execution, or validation cannot support.
2. Product identifies the requested claim type and required evidence.
3. Product checks required evidence against available data and execution state.
4. Product returns an explicit outcome such as clarification required, insufficient evidence, execution failed, validation failed, or unsupported claim type.
5. Product explains what evidence, clarification, execution, or validation is missing.
6. Product may offer a weaker supported claim type, such as descriptive or directional analysis, when appropriate.
7. Product does not present unsupported findings, fabricated calculations, or unsupported recommendations.

## 18. Product Success Definition

A successful CommerceLens MVP enables a user to complete one narrow evidence-first e-commerce analytical workflow through the CommerceLens Skill and receive validated, reproducible, evidence-backed decision support.

Success requires understandable business-question interaction, sufficient data validation, correct metric definitions, deterministic execution, deterministic validation, evidence-backed findings, bounded diagnostic interpretation, alternative explanations, explicit limitations, justified recommendations when supported, an Evidence Contract, and reproducible output.

A fluent answer without deterministic execution does not constitute product success.

## 19. Success Metrics

Targets below are product acceptance targets for the approved MVP evaluation set. They are not achieved results until evaluated.

| Metric Category | Metric | Definition | MVP Acceptance Target |
| --- | --- | --- | --- |
| Workflow Completion | Canonical Workflow Completion Rate | Percentage of valid canonical fixtures that complete from Skill invocation through report and Evidence Contract. | 100% of approved valid fixtures |
| Analytical Correctness | KPI Calculation Correctness | Percentage of approved revenue, order, AOV, product contribution, and category contribution calculations matching deterministic expected results. | 100% of approved calculation fixtures |
| Evidence Traceability | Evidence Contract Coverage | Percentage of material analytical outputs that include or reference an Evidence Contract. | 100% |
| Evidence Traceability | Execution Evidence Coverage | Percentage of material numerical findings that reference deterministic execution and validation status. | 100% |
| Reproducibility | Deterministic Rerun Consistency | Percentage of approved rerun checks that reproduce material deterministic outputs from the same input and analytical definition. | 100% of approved rerun fixtures |
| Claim Discipline | Unsupported Claim Block Rate | Percentage of unsupported causal, predictive, or excessive recommendation requests that are blocked, downgraded, or labeled insufficient. | 100% of approved negative fixtures |
| Failure Integrity | Fail-Closed Coverage | Percentage of missing-field, ambiguous-field, insufficient-data, execution-failure, and validation-failure fixtures that produce explicit non-success outcomes. | 100% of approved failure fixtures |
| User Value | Decision-Useful Output Rate | Percentage of valid canonical outputs that answer the business question with findings, alternatives, limitations, and justified recommendation or next-evidence request. | 100% of approved valid fixtures |
| Data Safety | Public Data Safety Compliance | Percentage of public demo data and examples using synthetic or openly licensed data only. | 100% |
| Scope Control | MVP Domain Compliance | Percentage of MVP workflows limited to approved sources and canonical analytical scope unless explicitly classified outside MVP. | 100% |

## 20. Acceptance Criteria

PRD v1.1 is accepted when:

- It conforms to `PROJECT_MASTER_INSTRUCTIONS.md` v1.1.
- It conforms to `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md`.
- Skill-first is the primary MVP delivery model.
- CommerceLens Skill and Reusable Deterministic Analytics Engine are both MVP requirements.
- The Skill cannot pass MVP as a prompt-only wrapper.
- The canonical business question defines the first vertical slice.
- Revenue, orders, AOV, product performance, category performance, and contribution analysis form the primary MVP analytical scope.
- Broader analytics are not accidentally required for MVP.
- CSV, Excel, and SQLite remain MVP data sources.
- Material numerical findings require deterministic execution and validation.
- Failure behavior is fail-closed.
- Evidence Contract remains mandatory.
- Human decision ownership remains explicit.
- Full Decision Reliability Benchmark remains deferred.
- Bounded MVP evaluation fixtures are required before release.
- External marketplace connectors do not block MVP.
- The PRD does not introduce unnecessary Architecture or implementation details.
- The PRD does not claim GitHub stars, recruiter response, market adoption, user demand, or commercial success as proven outcomes.

The MVP product is accepted only when:

1. Valid CSV, Excel, or SQLite input can be accepted.
2. Required schema can be inspected.
3. The canonical Business Question can be processed.
4. Metrics are explicitly defined.
5. Data Sufficiency is evaluated.
6. An Analysis Plan is produced.
7. Required material computations are deterministically executed.
8. Execution success is evidenced.
9. Results are deterministically validated.
10. Findings are consistent with validated results.
11. Alternative Explanations are included where appropriate.
12. Limitations are explicit.
13. Recommendations do not exceed Evidence.
14. Evidence Contract is produced or referenced.
15. Material deterministic results are reproducible.
16. Failure cases fail closed rather than hallucinate completion.

The MVP is not accepted merely because the Skill responds, code is generated, a report is produced, or charts are displayed.

## 21. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Product becomes a generic AI data assistant. | Weakens differentiation and violates scope. | Enforce e-commerce domain, canonical workflow, Evidence Contract, and requirement classification. |
| Skill becomes prompt-only. | Violates deterministic execution and evidence-first requirements. | Require engine-backed execution, validation, and Evidence Contract traceability for MVP acceptance. |
| Product produces fluent but unsupported conclusions. | Damages trust and violates the Constitution. | Require data sufficiency checks, claim classification, deterministic validation, and insufficiency language. |
| MVP expands into too many analytical domains. | Delays proof of analytical reliability. | Narrow MVP to the canonical revenue-performance workflow and reclassify broader analytics. |
| Engine is incorrectly deferred. | Makes Skill-first MVP non-credible. | Treat the Reusable Deterministic Analytics Engine as required in the MVP vertical slice. |
| Full benchmark is promoted too early. | Delays MVP and creates unnecessary scope. | Require bounded evaluation fixtures for MVP and defer full Decision Reliability Benchmark. |
| Metrics are interpreted inconsistently. | Causes incorrect business decisions. | Require metric definitions before findings. |
| Users expect causal or predictive answers from non-causal data. | Creates overstated recommendations. | Classify claim type and downgrade unsupported causal or predictive claims. |
| Execution fails or is unavailable but appears successful. | Creates false evidence. | Require fail-closed execution integrity behavior. |
| Skill and engine outputs diverge. | Reduces traceability and user trust. | Require material findings to reference engine-produced results and validation state. |
| Reused libraries obscure provenance. | Weakens evidence traceability. | Apply reuse before rebuild while requiring source, method, result, and validation traceability. |
| Public repository becomes documentation-heavy without execution. | Weakens portfolio credibility. | Require executable implementation, tests, deterministic results, failure cases, and reproducible example. |
| Public demo accidentally uses sensitive data. | Creates privacy and portfolio risk. | Use synthetic or openly licensed data only. |
| Evidence Contract becomes too heavy for users. | Reduces usability. | Keep user-facing evidence concise while preserving traceability for audit. |

## 22. Assumptions

- MVP users can provide structured e-commerce data in CSV, Excel, or SQLite format.
- The first product proof can focus on file-based analysis without external integrations.
- The CommerceLens Skill can access or coordinate deterministic execution in at least one supported environment.
- Cross-host Skill portability is not proven and remains Research until tested.
- Synthetic or openly licensed data is sufficient for public portfolio demonstration.
- Users value correctness, traceability, and reproducibility over instant unsupported answers.
- The canonical revenue-performance workflow provides enough business value to prove the MVP.
- Broader analytics remain valuable but should not block the first vertical slice.
- Architecture and implementation documents will later define how requirements are fulfilled without changing product scope.

## 23. Future Roadmap

### 23.1 Phase 2

- Add guided business question templates.
- Add saved analysis history.
- Expand local analytics to discounts, refunds, gross margin, inventory, stockouts, customer repeat purchase, cohort analysis, confidence intervals, hypothesis testing, and correlation where metric definitions and evidence rules are approved.
- Add richer diagnostic workflows for product and category performance.
- Evaluate PostgreSQL and MySQL as read-oriented data sources after file-based reliability is proven.
- Expand evaluation fixtures beyond the canonical MVP cases without creating the full benchmark product.

### 23.2 Phase 3

- Evaluate Shopify connector support.
- Evaluate Amazon Seller / SP-API connector support.
- Explore full Decision Reliability Benchmark expansion after core workflows are stable.
- Evaluate a limited visual interface or dashboard only if it improves evidence comprehension.

### 23.3 Research

- Research Shopee, Taobao, and broader marketplace connector feasibility.
- Research cross-host Skill portability and execution availability.
- Research heavier data quality or profiling library fit.
- Research broader predictive, causal, and experiment-analysis workflows only after required evidence standards are defined.

### 23.4 Rejected Ideas

- Multi-Agent.
- General Chatbot.
- Enterprise BI Platform.
- Real-time Streaming.
- Vector Database.
- RAG.
- Complex Agent Framework.
- LLM Router.
- Memory Framework.
- Plugin Framework.
- Prompt-only Skill.
- Autonomous decision execution.
- Enterprise SaaS infrastructure for MVP.

## 24. Open Questions

- Which synthetic e-commerce dataset should be used as the canonical MVP demo dataset?
- Which metric definitions should be locked first for revenue, orders, AOV, product contribution, and category contribution?
- What level of Evidence Contract detail should be visible in the main report versus supporting detail?
- Which bounded evaluation fixtures should be approved before Architecture begins?
- Which host or execution environment should be targeted first for the CommerceLens Skill MVP?
- What product-level format should identify engine-produced results in user-facing reports without defining the technical schema?
- How should the Skill handle ambiguous business questions without creating excessive user friction?
- What minimum public repository evidence is required before the project is presented as portfolio-ready?

## 25. Version Notes

### v1.1 — Skill-first Strategy Amendment

- Adopted Skill-first delivery model.
- Promoted Reusable Deterministic Analytics Engine into the MVP vertical slice.
- Narrowed MVP to the canonical revenue-performance workflow.
- Reclassified broader analytics to Phase 2, Phase 3, Research, or Backlog.
- Strengthened execution integrity and fail-closed behavior.
- Added bounded evaluation-fixture requirement.
- Deferred connector expansion.
- Preserved evidence-first principles, analytical correctness, reproducibility, Evidence Contract, claim discipline, transparent limitations, and human decision ownership.

### v1.0 — Approved PRD Baseline

- Established the original CommerceLens AI PRD.
- Defined the evidence-first product requirements, users, functional requirements, success metrics, and MVP boundaries before Skill-first migration.
