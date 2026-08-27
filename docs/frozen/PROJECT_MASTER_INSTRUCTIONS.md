# CommerceLens AI Product Constitution

**Version:** v1.1  
**Status:** Approved  
**State:** Frozen  
**Amendment:** Skill-first Strategy  
**Owner:** CommerceLens AI Product & Architecture  
**Last Updated:** 2026-08-20

## Table of Contents

1. [Document Hierarchy](#document-hierarchy)
2. [Intended Audience](#intended-audience)
3. [Terminology](#terminology)
4. [Vision & Mission](#1-vision--mission)
5. [Product Principles](#2-product-principles)
6. [Product Scope](#3-product-scope)
7. [Analytical Workflow](#4-analytical-workflow)
8. [Evidence Standard](#5-evidence-standard)
9. [Claim Taxonomy](#6-claim-taxonomy)
10. [MVP Definition](#7-mvp-definition)
11. [Technical Philosophy](#8-technical-philosophy)
12. [Documentation Standard](#9-documentation-standard)
13. [Decision Framework](#10-decision-framework)
14. [Governance Model](#11-governance-model)
15. [Constitutional Requirements](#12-constitutional-requirements)
16. [Version Notes](#version-notes)

## Document Hierarchy

PROJECT_MASTER_INSTRUCTIONS.md is the Product Constitution of CommerceLens AI and serves as the highest governing document of the project.

All lower-level artifacts shall conform to this constitution.

Document hierarchy:

PROJECT_MASTER_INSTRUCTIONS.md
↓
PRD.md
↓
Skill Scope Specification
↓
Evidence Contract Specification
↓
ARCHITECTURE.md
↓
Implementation
↓
Supporting Specifications, including Canonical Dataset / Metric Dictionary and Evaluation Fixtures

If conflicts exist, lower-level documents shall be revised unless this constitution is intentionally amended.

## Intended Audience

This constitution is intended for:

- Product Managers
- Software Engineers
- Data Analysts
- AI Engineers
- Future Contributors

It defines the governing principles of CommerceLens AI rather than implementation details.

## Terminology

The following terms are the single source of truth for CommerceLens AI. Other documents and sections must reference these definitions rather than redefine them.

| Term | Definition |
| --- | --- |
| Business Question | The business decision, performance issue, or analytical question that an analysis is intended to answer. |
| Metric | A defined quantitative measure used to evaluate performance, behavior, or business outcomes. |
| Evidence | Traceable support for a material claim, including relevant data sources, metric definitions, analysis period, executed methods, validated results, assumptions, limitations, and alternative explanations. |
| Finding | An evidence-supported analytical statement produced after data sufficiency, execution, and validation. |
| Recommendation | A proposed business action or next step that is proportional to the strength, type, and limitations of the supporting evidence. |
| Claim | Any analytical statement that describes, explains, predicts, attributes, or recommends something about business performance or action. |
| Material Claim | A claim that could influence a business decision, analytical conclusion, product judgment, operational action, or performance interpretation. |
| Evidence Contract | The required evidence record that makes a material claim traceable, reproducible, limited, and auditable. |
| Deterministic Validation | Verification performed by reproducible systems or procedures for calculations, SQL results, statistical tests, KPI logic, data quality checks, and numerical outputs. |
| Data Sufficiency Check | The required evaluation of whether available data can responsibly support the requested claim type. |
| Analytical Workflow | The required conceptual sequence that moves from Business Question to Evidence Contract before presenting material conclusions. |
| Reproducibility | The ability to regenerate a material analytical output from declared data sources, metric definitions, analysis period, and execution logic. |
| CommerceLens Skill | The user-facing analytical reasoning and orchestration layer of CommerceLens AI. |
| Reusable Deterministic Analytics Engine | The execution and validation authority for deterministic computation, provenance, validation, and evidence tracking. |
| Decision Reliability Benchmark | The evaluation layer for analytical correctness and evidence reliability. |
| Execution Record | A traceable record that deterministic execution occurred and produced a specific output, failure, or blocked state. |
| Validated Result | A deterministic output that has passed the required validation state for its intended analytical use. |

## 1. Vision & Mission

CommerceLens AI is an evidence-first e-commerce analytics skill powered by a reusable deterministic analytics engine.

It is designed from the workflow of a rigorous professional data analyst. AI may help understand business questions, generate hypotheses, plan analyses, select appropriate methods, interpret validated results, and draft reports. It must not create material conclusions from language fluency, intuition, pattern completion, or unsupported assumptions.

The mission of CommerceLens AI is to help e-commerce operators turn business questions into reproducible findings, clearly documented limitations, and evidence-backed recommendations while preserving the broader purpose of reliable decision intelligence.

The constitutional principle is:

> No material claim without traceable evidence.

If the available evidence is insufficient, the system must explicitly state:

> Insufficient evidence to conclude.

CommerceLens AI exists to make analytical reasoning more reliable, not to make unsupported answers sound more confident.

## 2. Product Principles

### 2.1 Evidence First

Every material conclusion must be linked to evidence as defined in [Terminology](#terminology).

### 2.2 Analytical Correctness Over Fluency

A response that is incomplete but correct is preferable to a fluent response that overstates the evidence. The system must preserve uncertainty when uncertainty exists.

### 2.3 Deterministic Validation Over AI Confidence

AI reasoning is not evidence by itself. Material numerical, statistical, and data quality claims must be validated through Deterministic Validation.

### 2.4 Reproducibility

Material analytical outputs must be reproducible.

### 2.5 Business Value

The product must prioritize e-commerce decisions that matter to operators, analysts, product teams, and business stakeholders. Technical sophistication is only valuable when it improves decision quality.

### 2.6 Transparent Limitations

Limitations, assumptions, data gaps, and alternative explanations are required parts of the product experience. The system must not hide weak evidence behind confident language.

### 2.7 MVP Depth Over Feature Breadth

CommerceLens AI must become credible in a narrow scope before expanding. A smaller product with strong evidence discipline is preferable to a broad product with shallow reliability.

### 2.8 Human Decision Ownership

CommerceLens AI provides analytical decision support. The human user retains final analytical and business decision ownership.

## 3. Product Scope

CommerceLens AI is:

> An evidence-driven e-commerce decision intelligence system that follows a structured analyst workflow and requires every material conclusion to be supported by reproducible evidence.

CommerceLens AI is not:

- A generic AI assistant
- A generic "chat with CSV" tool
- A simple Text-to-SQL demo
- A dashboard generator
- A prompt-only Skill
- A documentation-only Skill
- A host-specific demo
- An AI engineering research project
- A fully autonomous decision maker
- A substitute for deterministic execution
- A standalone SaaS requirement for MVP
- A replacement for analyst judgment
- An autonomous business-action system

The product may use AI, SQL, Python, statistics, BI concepts, and reporting workflows. These are means to support evidence-based decision intelligence, not independent product goals.

The CommerceLens Skill may recommend actions when justified by Evidence. It does not own the final business decision and must not execute business actions on behalf of the user within the approved MVP direction.

### 3.1 Intended Users

CommerceLens AI is intended for users who need to analyze e-commerce performance and make business decisions from structured data, including:

- E-commerce founders and operators
- Data analysts and business analysts
- Product and category managers
- Growth, merchandising, and operations teams
- Portfolio reviewers evaluating evidence-first analytics work

### 3.2 Product Boundaries

CommerceLens AI must focus on structured analytical decision support. It must not expand into broad automation, multi-agent research, generalized data science, or unrelated business domains until the core e-commerce evidence workflow is credible.

Any feature outside the approved MVP requires documented business justification before implementation.

Unapproved additions include, but are not limited to:

- Multi-Agent systems
- RAG
- Vector databases
- Agent frameworks
- Memory frameworks
- Plugin frameworks
- LLM routers
- Enterprise SaaS infrastructure
- Real-time streaming
- Other unapproved capabilities unrelated to the MVP evidence workflow

## 4. Analytical Workflow

Every CommerceLens AI analysis must follow the same conceptual workflow:

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

The system must not jump directly from a user question to a conclusion.

The workflow defines the required analytical order. PRD, architecture, and implementation documents may define how the workflow is presented, executed, and stored.

## 5. Evidence Standard

The Evidence Standard defines what must be true before CommerceLens AI may present a material claim.

### 5.1 Evidence Contract Requirements

Every material analytical output must include or reference an Evidence Contract.

An Evidence Contract must identify:

- Business Question
- Claim type
- Metric definitions
- Data source or sources
- Analysis period
- Required evidence
- Data sufficiency status
- Executed SQL, Python, statistical method, or reproducible procedure
- Deterministic Validation
- Calculated result or validated output
- Assumptions
- Limitations
- Alternative explanations
- Recommendation, if any

The Evidence Contract does not need to prove that a claim is strong. It must make the strength, weakness, and traceability of the claim clear.

### 5.2 Data Sufficiency

The system must evaluate whether available data is sufficient for the requested conclusion and claim type.

When evidence is incomplete, stale, ambiguous, biased, missing required fields, too small, or inappropriate for the requested claim type, the system must state the limitation and avoid overclaiming.

### 5.3 Unsupported Claims

The system must not invent:

- Data sources
- Columns or fields
- Query results
- Statistical significance
- Confidence levels
- Business context
- Causal mechanisms
- External explanations
- User intent

If the required evidence is unavailable, the correct output is uncertainty, not speculation.

### 5.4 Evidence Strength

Claims must be expressed with strength proportional to their evidence.

The system may present:

- Confirmed findings when evidence is sufficient and validated
- Directional findings when evidence is partial but informative
- Hypotheses when evidence suggests a possibility but does not establish a finding
- Insufficient evidence when the available data cannot support the requested claim

## 6. Claim Taxonomy

CommerceLens AI must classify material claims before presenting them.

| Claim Type | Meaning | Evidence Requirement |
| --- | --- | --- |
| Descriptive | States what happened. | Valid metrics, source data, analysis period, and reproducible calculations. |
| Diagnostic | Explains why something may have happened. | Descriptive evidence plus comparison, segmentation, driver analysis, and alternative explanations. |
| Predictive | Estimates what may happen. | Historical data, modeling or forecasting method, validation logic, assumptions, and uncertainty. |
| Causal | Claims that one factor caused an outcome. | Appropriate causal design or clearly stated causal limitations. Correlation alone is insufficient. |
| Prescriptive | Recommends what action to take. | Evidence linked to business goals, expected tradeoffs, limitations, and proportional confidence. |

The system must never present correlation as causation without appropriate causal evidence.

When a user asks a causal or prescriptive question but the available data only supports descriptive or diagnostic analysis, the system must downgrade the claim and explain why.

## 7. MVP Definition

The MVP must prove one complete Skill-orchestrated, deterministic-engine-executed, evidence-backed, reproducible e-commerce analytical workflow.

The MVP must include both the CommerceLens Skill and the Reusable Deterministic Analytics Engine in the first vertical slice. The full Decision Reliability Benchmark is not required for MVP.

### 7.1 MVP Domain

The MVP focuses on a narrow subset of structured e-commerce performance analysis. The PRD determines the approved MVP subset.

The approved CommerceLens analytical domain envelope includes:

- Revenue
- Orders
- Average Order Value
- Gross Margin
- Discounts
- Refunds
- Product Mix
- Inventory
- Stockouts
- Customer Retention
- Product Performance
- Category Performance

### 7.2 MVP Data Sources

The MVP may support:

- CSV
- Excel
- SQLite

Public versions must use synthetic or openly licensed data only. The product must not expose private company data, customer data, proprietary URLs, real retailer scraping outputs, or confidential operational records.

### 7.3 MVP Output

The MVP must produce analytical outputs that include:

- A clear Business Question
- Defined Metrics
- Evidence-backed Findings
- Deterministic Validation
- Alternative explanations
- Limitations
- Evidence Contract
- Recommendation only when justified

### 7.4 Out of Scope for MVP

The MVP must not prioritize:

- Multi-Agent systems
- RAG
- Vector databases
- Complex agent frameworks
- LLM routers
- Memory frameworks
- Plugin ecosystems
- Enterprise SaaS infrastructure
- Real-time streaming
- Multiple LLM architectures
- Fully autonomous decision execution
- Broad enterprise integration
- Unrelated business domains
- Visual polish ahead of analytical reliability

These capabilities may only be reconsidered if they directly serve a documented business requirement and are classified under [Section 11](#11-governance-model).

Any feature outside the approved MVP requires documented business justification before implementation.

### 7.5 Three-Layer Product Direction

CommerceLens AI follows the approved Skill-first product model:

1. CommerceLens Skill
2. Reusable Deterministic Analytics Engine
3. Decision Reliability Benchmark

Layer 1, the CommerceLens Skill, is the user-facing analytical reasoning and orchestration layer.

Layer 2, the Reusable Deterministic Analytics Engine, is the execution, computation, validation, provenance, and evidence-tracking authority.

Layer 3, the Decision Reliability Benchmark, is the evaluation layer for analytical correctness and evidence reliability.

Layers 1 and 2 are both required for the MVP vertical slice. Layer 3 remains part of the long-term product direction, while bounded MVP evaluation fixtures are required before Architecture and implementation.

## 8. Technical Philosophy

CommerceLens AI separates AI reasoning from deterministic execution.

The core design philosophy is:

> AI reasons.
>
> Deterministic systems compute.
>
> Evidence justifies.

### 8.1 CommerceLens Skill Responsibilities

The CommerceLens Skill may be responsible for:

- Understanding Business Questions
- Clarifying material ambiguity
- Selecting and defining Metrics
- Generating hypotheses
- Identifying required Evidence
- Planning analysis
- Selecting approved analytical actions
- Requesting deterministic execution
- Interpreting validated results
- Enforcing Claim boundaries
- Presenting Findings
- Presenting alternative explanations
- Producing Recommendations when justified
- Communicating limitations
- Explaining uncertainty
- Producing or assembling evidence-backed reports

The CommerceLens Skill must not treat its own reasoning as evidence. It may request deterministic execution but may not declare execution successful without returned execution evidence.

The CommerceLens Skill must not:

- Fabricate execution results
- Calculate material results through language reasoning alone
- Represent generated code as executed code
- Represent planned analysis as completed analysis
- Treat failed execution as successful execution
- Strengthen Claims beyond available Evidence
- Bypass Deterministic Validation

### 8.2 Reusable Deterministic Analytics Engine Responsibilities

The Reusable Deterministic Analytics Engine must be responsible for:

- Data ingestion
- Schema inspection
- Data quality checks
- KPI computation
- SQL execution
- Python execution
- Approved statistical execution
- KPI validation
- Deterministic Validation
- Execution Records
- Provenance capture
- Evidence tracking
- Result Reproducibility

Material numerical outputs used in Findings must originate from deterministic execution. AI-generated narrative is not execution evidence.

Failure, missing data, ambiguous schema, unavailable execution, or invalid execution must produce an explicit blocked, failed, or insufficient state.

### 8.3 Execution Integrity

Generated code is not evidence of execution.

Planned analysis is not evidence of execution.

A material numerical result may be used only when the Reusable Deterministic Analytics Engine has produced the result and the required validation state is available.

The system must not represent unexecuted code, failed code, unavailable execution, or partial execution as successful analytical evidence.

### 8.4 Responsibility Boundary

The CommerceLens Skill understands, reasons, plans, selects, interprets, and communicates.

The Reusable Deterministic Analytics Engine executes, computes, validates, records, and returns execution evidence.

The Evidence layer links Claims to data, Metrics, methods, results, validation, assumptions, and limitations.

### 8.5 Reuse Before Rebuild

> Reuse before rebuild.

CommerceLens AI should reuse or adapt mature commodity-level analytical infrastructure unless doing so would materially weaken:

- Analytical correctness
- Evidence traceability
- Reproducibility
- Deterministic Validation
- Data safety
- Benchmark validity
- Maintainability

CommerceLens AI should prioritize original development for differentiated reliability capabilities such as:

- KPI semantic governance
- Data Sufficiency reasoning
- Evidence tracking
- Evidence Contract
- Claim classification and control
- Alternative explanation requirements
- Deterministic Validation orchestration
- Decision reliability evaluation

### 8.6 Architecture Discipline

Architecture must serve analytical correctness, evidence traceability, Reproducibility, business value, data safety, and maintainability.

The system must not adopt technologies because they are fashionable. Technical additions must be justified by a product requirement and classified under [Section 11](#11-governance-model).

### 8.7 Security and Data Safety

The product must treat uploaded files and analytical outputs as sensitive by default. Public demos must avoid private, proprietary, or personally identifiable data.

## 9. Documentation Standard

CommerceLens AI documentation must make decisions traceable.

### 9.1 Required Documentation Qualities

Documentation must be:

- Clear
- Concise
- Versioned
- Consistent in terminology
- Connected to evidence standards
- Explicit about scope and limitations
- Suitable for public GitHub review when intended for portfolio use

### 9.2 Documentation Layers

The Product Constitution defines why the product exists, what it is, and what it must preserve.

The PRD defines product requirements, user workflows, acceptance criteria, and MVP behavior.

Skill Scope Specification defines Skill responsibilities, boundaries, and approved orchestration behavior.

Evidence Contract Specification defines detailed evidence records, validation references, and traceability structures.

Canonical Dataset / Metric Dictionary documentation defines approved datasets, metric meanings, and metric governance.

Evaluation Fixtures define bounded MVP evaluation cases for analytical correctness and evidence reliability.

Architecture documentation defines system design, components, interfaces, and implementation boundaries.

Implementation documentation defines setup, execution, code usage, testing, and developer workflows.

This document must not become a detailed implementation guide.

### 9.3 Terminology Governance

Core terms must follow [Terminology](#terminology). Lower-level documents may add implementation-specific terms, but they must not redefine constitutional terms.

## 10. Decision Framework

When priorities conflict, CommerceLens AI must use the following order:

1. Analytical correctness
2. Evidence traceability
3. Reproducibility
4. Business value
5. Data safety
6. Transparent limitations
7. MVP depth
8. Maintainable architecture
9. Documentation
10. Visual polish

This priority order is binding for product, architecture, documentation, and implementation decisions.

The system must choose a less impressive answer that is supported over a more impressive answer that is unsupported.

## 11. Governance Model

All new product ideas, features, architectural changes, and analytical capabilities must be classified before adoption.

### 11.1 Classification Categories

| Category | Definition |
| --- | --- |
| Core | Required to preserve the Product Constitution. |
| MVP | Required to prove the first Skill-orchestrated, deterministic-engine-executed, evidence-backed e-commerce analytics workflow. |
| Phase 2 | Valuable after MVP credibility is established. |
| Phase 3 | Long-term expansion after the core product is stable. |
| Research | Worth investigating, but not committed to product scope. |
| Backlog | Potentially useful, but not currently prioritized. |
| Rejected | Not aligned with the product direction or evidence standard. |

### 11.2 Adoption Rule

No feature may be added only because it is technically interesting, popular, or easy to demonstrate.

Each adopted feature must support at least one of:

- Analytical correctness
- Evidence traceability
- Reproducibility
- Business value
- Data safety
- Maintainability

### 11.3 Change Discipline

Changes that weaken evidence traceability, blur claim types, reduce Reproducibility, or encourage unsupported conclusions must be rejected unless the Product Constitution is formally revised.

If any future decision conflicts with this document, preserve the following in order:

1. Evidence First
2. Analytical correctness
3. Deterministic Validation
4. Explicit uncertainty
5. Business value
6. MVP depth
7. Maintainability

## 12. Constitutional Requirements

The following requirements are binding across all CommerceLens AI work:

1. No material claim may be presented without traceable evidence.
2. Every material analytical output must include or reference an Evidence Contract.
3. AI reasoning must not replace deterministic execution for calculations, SQL results, statistical tests, KPI validation, or data quality checks.
4. Generated code, planned analysis, failed execution, unavailable execution, and partial execution must not be represented as successful analytical evidence.
5. A material numerical result may be used only when deterministic execution has produced the result and the required validation state is available.
6. Metrics must be defined before they are used in Findings.
7. Data sufficiency must be checked before material conclusions are stated.
8. Claim types must be distinguished as descriptive, diagnostic, predictive, causal, or prescriptive.
9. Correlation must not be presented as causation without appropriate causal evidence.
10. Unsupported, unavailable, or insufficient evidence must be stated explicitly.
11. Recommendations must be proportional to the strength and type of evidence.
12. The human user retains final analytical and business decision ownership.
13. The system must not convert analytical Recommendations into autonomous business actions unless a future constitutional amendment explicitly authorizes such behavior.
14. Alternative explanations and limitations must be included for material Findings.
15. Public demos must use synthetic or openly licensed data only.
16. MVP development must prioritize depth and reliability over breadth and novelty.
17. The CommerceLens Skill and Reusable Deterministic Analytics Engine are both required for the MVP vertical slice.
18. The full Decision Reliability Benchmark is not required for MVP, but bounded MVP evaluation fixtures are required before Architecture and implementation.
19. New features must be classified before adoption.
20. Technical architecture must support analytical correctness, traceability, Reproducibility, and maintainability.
21. This Product Constitution answers why CommerceLens AI exists, what it is, and what it must preserve. Detailed execution decisions belong in PRD, architecture, and implementation documents.

CommerceLens AI v1.1 is approved only while these constitutional requirements remain intact.

## Version Notes

Version 1.0

Initial release of the CommerceLens AI Product Constitution.

Version 1.1

Skill-first Strategy amendment.

- Primary delivery mechanism changed from Product-first to Skill-first.
- Reusable Deterministic Analytics Engine promoted to a co-required MVP layer.
- Decision Reliability Benchmark retained as the third long-term layer.
- Reuse before rebuild added.
- Core evidence-first analytical principles remain unchanged.
