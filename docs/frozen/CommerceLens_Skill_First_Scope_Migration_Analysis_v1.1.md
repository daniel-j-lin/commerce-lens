# CommerceLens AI — Skill-first Scope Migration Analysis

**Analysis Version:** 1.1  
**Status:** Approved  
**Migration Decision:** GO  
**Strategy:** Skill-first  
**Date:** 2026-08-20  
**Source Baseline:** `PROJECT_MASTER_INSTRUCTIONS.md` v1.0 and `PRD.md` v1.0 (Approved, 2026-07-30)  
**Record Role:** Approved migration record from Product-first to Skill-first  
**Purpose:** Determine how CommerceLens should migrate from Product-first to Skill-first without weakening its evidence-first analytical core.  
**Change Authority:** Analysis only. This document does not amend either approved source document and does not initiate Architecture, coding, or Skill creation.

## Executive Decision

### GO

CommerceLens officially adopts the Skill-first Strategy with the following product model:

> CommerceLens Skill  
> ↓  
> Reusable Deterministic Analytics Engine  
> ↓  
> Decision Reliability Benchmark

This is an approved product-direction decision. It changes the primary delivery mechanism from Product-first to Skill-first without weakening or replacing the evidence-first analytical core.

## Approved Skill-first Development Constraints

The following constraints are mandatory:

1. The Skill must be backed by executable deterministic systems and must not become a prompt-only or documentation-only wrapper.
2. The first MVP must prove one narrow end-to-end e-commerce analytical workflow before analytical breadth, connectors, or advanced statistical capabilities are added.
3. Every material numerical output must originate from the deterministic engine and remain traceable through execution records, validation, reproducibility information, and the Evidence Contract.
4. The public GitHub repository must contain executable implementation, tests, evaluation cases, and a reproducible example—not primarily documentation.

These constraints are release-governing requirements, not unresolved conditions on the GO decision.

## External Outcome Evidence Limits

The product-direction decision is **GO**. External outcome claims are **not yet proven**.

There is currently **Insufficient evidence to conclude** that Skill-first will automatically produce:

- More GitHub stars.
- Stronger recruiter response.
- Greater market adoption.
- Stronger user demand.

These remain empirical questions. The MVP must generate evidence through executable implementation, evaluation results, reviewer feedback, and user feedback where available. The GO decision must not be interpreted as evidence that these external outcomes will occur.

The direction is stronger than Product-first for implementation speed, scope control, maintainability, and evidence-first separation of responsibilities. It also creates a clearer path to a reusable engine. These project-direction findings do not convert external adoption or hiring outcomes into proven claims.

## Decision Basis

| Evaluation Dimension | Finding | Confidence |
| --- | --- | --- |
| Product differentiation | Positive if differentiation remains evidence governance, not “AI analyzes files.” Generic analysis remains commoditized. | Directional |
| Technical feasibility | High for a narrow file-based workflow using mature data and statistical libraries. | High |
| Development speed | Likely faster because a standalone web application, authentication, billing, tenancy, and frontend are not required for proof. | High |
| GitHub / portfolio value | Potentially higher if the repository is executable and visibly tests unsupported claims; unproven until reviewed. | Directional |
| Recruiter comprehensibility | Good only if README language explains “Skill + deterministic engine + evidence contract” in under one minute. | Directional |
| Maintainability | Improved by separating reasoning instructions from deterministic computation and evidence records. | High |
| Long-term extensibility | Improved if the engine remains reusable and the Skill is not coupled to one host. | Directional |
| Evidence-first alignment | Strong: the delivery change reinforces “AI reasons; deterministic systems compute; evidence justifies.” | High |

## Preserve the Core

The following are constitutional invariants. Skill-first may change where and how they are delivered, but not their meaning, order, or enforcement strength:

- Evidence-first philosophy and “No material claim without traceable evidence.”
- Analytical correctness, evidence traceability, reproducibility, deterministic validation, transparent limitations, business value, and human decision ownership.
- The complete analytical workflow: Business Question → Metric Definition → Hypothesis Generation → Required Evidence → Data Sufficiency Check → Analysis Plan → SQL/Python/Statistical Execution → Deterministic Validation → Findings → Alternative Explanations → Recommendation → Limitations → Evidence Contract.
- Evidence Contract requirements and the required response “Insufficient evidence to conclude” when the requested conclusion is unsupported.
- Claim taxonomy: descriptive, diagnostic, predictive, causal, and prescriptive.
- Correlation must never be presented as causation without appropriate causal evidence.
- AI reasoning is not execution evidence and may not invent data, fields, results, confidence levels, significance, or external explanations.
- Recommendations must remain proportional to evidence strength and must not transfer final decision ownership from the human user.
- Public examples must use synthetic or openly licensed data.
- MVP depth must outrank feature breadth and visual polish.

## New Three-Layer Product Model

### Layer 1 — CommerceLens Skill

The user-facing analytical interface. It understands the business question, clarifies only material ambiguity, selects and defines metrics, generates hypotheses, states required evidence, plans analysis, selects approved tools, requests deterministic execution, interprets validated results, applies claim controls, and produces the report.

The Skill must not calculate material results from language reasoning, treat unexecuted code as executed, or convert weak evidence into a stronger claim.

### Layer 2 — Reusable Deterministic Analytics Engine

The execution and validation authority. It handles file ingestion, schema inspection, data-quality checks, KPI computation, SQL and Python execution, approved statistical methods, deterministic validation, provenance capture, and evidence tracking.

The engine—not the AI narrative—is the system of record for execution results. Failure, missing data, ambiguous schema, or unavailable execution must produce an explicit blocked or insufficient state.

### Layer 3 — Decision Reliability Benchmark

The evaluation layer for analytical correctness, evidence grounding, claim classification, reproducibility, unsupported inference, statistical correctness, and recommendation support.

The benchmark remains part of the long-term product direction, but a benchmark framework is not an MVP implementation priority. A small set of deterministic acceptance fixtures is required for MVP testing; that is not yet the full benchmark product.

---

# A. Constitution v1.0 → v1.1 Change List

## Classification Summary

- **KEEP:** The evidence philosophy, analytical workflow, evidence standard, taxonomy, decision hierarchy, governance model, data safety, documentation discipline, and most responsibility boundaries.
- **MODIFY:** Product definition, primary delivery mechanism, MVP statement, three-layer sequence, Product Demo positioning, and a small number of delivery-assumption terms.
- **ADD:** Skill-first delivery principle, Reuse before rebuild, explicit human decision ownership, engine execution authority, and differentiated-layer guidance.
- **DEFER:** Full Decision Reliability Benchmark implementation and external connector commitments.
- **REMOVE:** Only standalone-product-first assumptions. No evidence-first principle should be removed.

## Constitution Change Table

| Current Concept | Decision | Required Change | Reason | Impact |
| --- | --- | --- | --- | --- |
| Document Hierarchy | MODIFY | Preserve the hierarchy but clarify that v1.1 governs a Skill, deterministic engine, benchmark, and later implementation specifications. Do not insert Architecture work here. | Lower-level artifacts now include a Skill specification and engine requirements. | Governance becomes delivery-mechanism aware without changing authority. |
| Intended Audience | KEEP | No substantive change. | Product managers, engineers, analysts, AI engineers, and contributors remain the correct audience. | None. |
| Terminology | MODIFY | Add definitions for **CommerceLens Skill**, **Deterministic Analytics Engine**, **Execution Record**, and optionally **Validated Result**. Preserve all existing analytical terms unchanged. | New layers need one authoritative vocabulary. | Prevents “Skill reasoning” from being confused with engine execution. |
| Vision & Mission | MODIFY | Change “evidence-first e-commerce decision intelligence system” to “evidence-first e-commerce analytics skill powered by a reusable deterministic analytics engine,” while preserving the mission and constitutional principle verbatim in meaning. | Product identity and delivery mechanism changed; purpose did not. | Makes Skill-first explicit without redesigning CommerceLens. |
| Evidence First | KEEP | No change. | It remains the primary differentiator. | None. |
| Analytical Correctness Over Fluency | KEEP | No change. | Skill delivery increases, rather than reduces, the need for this constraint. | None. |
| Deterministic Validation Over AI Confidence | KEEP | No change to principle; cross-reference the engine as execution authority. | The engine operationalizes the existing principle. | Stronger separation of responsibilities. |
| Reproducibility | KEEP | No change to standard. | Reproducibility is independent of UI form. | None. |
| Business Value | KEEP | No change. | Skill-first is a delivery decision, not a new product goal. | None. |
| Transparent Limitations | KEEP | No change. | Required for responsible analytical outputs. | None. |
| MVP Depth Over Feature Breadth | KEEP | No change. | This becomes more important because Skills can otherwise accumulate broad instructions quickly. | Stronger scope control. |
| Product Scope definition | MODIFY | Replace platform/system-first wording with the Skill + deterministic engine definition. Keep every “not a generic assistant / chat-with-CSV / Text-to-SQL / dashboard / autonomous decision maker” boundary. | Current definition assumes a product form that is no longer primary. | Clarifies product category while preserving differentiation. |
| Intended Users | KEEP | Retain all existing user groups. Optionally describe analysts/operators as users invoking the Skill through a supported AI environment. | User problems remain the same. | Minimal copy change only. |
| Product Boundaries | MODIFY | Add that CommerceLens is not a prompt-only Skill, a host-specific demo, or a substitute for deterministic execution. Preserve rejected technology categories. | Skill-first introduces a new failure mode: fluent instructions without executed evidence. | Protects credibility and portability. |
| Analytical Workflow | KEEP | Preserve all 13 stages and their order. Clarify that the Skill coordinates reasoning stages and the engine performs execution/validation stages. | Workflow is correct; ownership needs clarification. | Operational separation without analytical weakening. |
| Evidence Standard and Contract | KEEP | Preserve all requirements. Add engine execution identifiers or references only at lower-level specification unless the Constitution needs a generic “execution record” field. | Evidence standards remain correct. | No scope expansion. |
| Data Sufficiency | KEEP | No substantive change. | It is a core differentiated capability. | None. |
| Unsupported Claims | KEEP | Add an explicit prohibition against representing planned, generated, or failed code as successfully executed. | Skill hosts may generate code even when execution is unavailable or fails. | Closes a Skill-specific reliability gap. |
| Evidence Strength | KEEP | No change. | Claim strength rules are delivery-independent. | None. |
| Claim Taxonomy | KEEP | No change. | Taxonomy remains essential. | None. |
| MVP purpose | MODIFY | Define MVP proof as one complete Skill-orchestrated, engine-executed, evidence-backed e-commerce workflow. | Existing language proves a product workflow but does not name the new layers. | Establishes a narrower and testable proof. |
| MVP analytical domain list | MODIFY | Reclassify the current 12 “priority analytical areas” as an approved domain envelope, not an obligation to implement all in v1.1 MVP. The PRD chooses the first narrow subset. | The current list is too broad when interpreted as one-release implementation scope. | Reduces schedule and reliability risk. |
| MVP data sources | KEEP | Retain CSV, Excel, and SQLite. | These sources provide strong portfolio value with bounded connector complexity. | None. |
| MVP output | KEEP | Preserve all output requirements and add explicit engine execution/validation references through the Evidence Contract. | The output contract already fits Skill-first. | Better auditability. |
| Out of Scope for MVP | MODIFY | Preserve all exclusions; add standalone SaaS/web application infrastructure, host-specific plugin ecosystem, and real-time streaming as non-priorities. | These are unnecessary to prove the Skill workflow. | Prevents delivery-layer scope creep. |
| Three-Layer Product Direction | MODIFY | Replace **Product Demo → Engine → Benchmark** with **CommerceLens Skill → Reusable Deterministic Analytics Engine → Decision Reliability Benchmark**. Clarify that Layers 1 and 2 are both required for the MVP vertical slice; Layer 3 is deferred except for MVP acceptance fixtures. | A Skill cannot credibly function without the engine, so the engine cannot remain Phase 3. | This is the largest constitutional migration. |
| Technical Philosophy | KEEP | Preserve “AI reasons. Deterministic systems compute. Evidence justifies.” | It directly supports the new model. | None. |
| AI Responsibilities | MODIFY | Map existing responsibilities explicitly to the Skill; add that it may request execution but cannot declare unverified execution success. | Makes authority boundaries enforceable. | Reduces fabricated-result risk. |
| Deterministic Responsibilities | MODIFY | Map responsibilities explicitly to the reusable engine; add ingestion, schema inspection, execution records, and evidence tracking. | Existing list is correct but incomplete for the promoted engine layer. | Defines engine responsibility at product level, not architecture level. |
| Architecture Discipline | ADD | Insert the formal principle: **Reuse before rebuild.** Mature commodity infrastructure should be reused or adapted unless it cannot satisfy evidence-first requirements. | Prevents unnecessary reinvention and accelerates delivery. | Improves speed and maintainability. |
| Security and Data Safety | KEEP | Preserve sensitive-by-default handling. Later specifications should require local/read-only defaults where supported, but no architecture should be prescribed here. | Skill-first does not eliminate data risk. | None at Constitution level. |
| Documentation Standard | MODIFY | Add Skill specification and Evidence Contract examples to documentation layers; emphasize executable examples over documentation volume for public GitHub. | The artifact hierarchy changed and portfolio risk is document-heavy output without proof. | Better handoff and portfolio clarity. |
| Decision Framework | KEEP | No change to ordering. | It already governs this migration correctly. | None. |
| Governance Model | KEEP | Preserve Core/MVP/Phase 2/Phase 3/Research/Backlog/Rejected categories and adoption rules. | Still sufficient. | None. |
| Human decision ownership | ADD | Add an explicit constitutional requirement that the user retains final analytical and business decision ownership; the Skill may recommend but not decide or execute business actions. | Existing text implies this but the new autonomous-seeming interface makes explicit wording necessary. | Protects accountability and scope. |
| Benchmark implementation | DEFER | Keep Benchmark as Layer 3; do not require the full benchmark for MVP. Require only acceptance fixtures needed to validate the MVP. | A full benchmark would delay the first executable workflow. | Maintains long-term differentiation without blocking delivery. |
| Standalone product-first delivery assumption | REMOVE | Remove only statements that make a web/platform product the required first delivery. Do not remove analytical product concepts, users, workflows, or reports. | Primary delivery mechanism changed. | Reduces unnecessary product surface. |

## Constitution Migration Conclusion

Constitution v1.1 should be a narrow amendment, not a rewrite. Approximately four-fifths of the existing constitutional substance remains correct. The critical amendment is the promotion of the deterministic engine from a later reusable layer to a co-required MVP layer beneath the Skill.

---

# B. PRD v1.0 → v1.1 Change List

## Classification Summary

- **KEEP:** Problem, goals around evidence, most users/personas/JTBD, core analytical requirements, insufficiency workflow, evidence metrics, risk controls, and scope guardrails.
- **MODIFY:** Product overview, journey language, functional requirement ownership, analytical breadth, MVP scope, acceptance criteria, roadmap, success metrics, risks, and assumptions.
- **ADD:** Skill invocation behavior, engine execution authority, execution/evidence linkage, narrow canonical workflow, reuse policy, host portability, and “prompt-wrapper” risk.
- **DEFER:** Advanced diagnostics, inventory/retention/statistics, full benchmark, connectors, and standalone UI.
- **REMOVE:** Platform-first assumptions and the requirement to implement all listed KPI areas in the first MVP.

## PRD Change Table

| Current Concept | Decision | Required Change | Reason | Impact |
| --- | --- | --- | --- | --- |
| Product Overview | MODIFY | Replace “decision intelligence platform” with the Skill + deterministic engine product model. State that the Skill is the primary interface and the engine is execution authority. | Current overview communicates the old delivery mechanism. | Recruiters and contributors understand the product in one paragraph. |
| Product Vision Alignment | MODIFY | Update governing document reference to v1.1 after approval and map workflow responsibilities to Skill vs engine. | PRD must inherit the amended Constitution. | Maintains hierarchy. |
| Constitution Reference | KEEP | Only update version reference after v1.1 approval. | The section is already correct. | None. |
| Problem Statement | KEEP | No substantive change. | Undefined metrics, irreproducible calculations, and fluent unsupported AI answers remain the exact problem. | None. |
| Goals | MODIFY | Preserve evidence goals; add “prove a reusable deterministic engine through one Skill workflow” and “provide an executable GitHub demonstration.” | New product model and portfolio goal must be measurable. | More focused implementation outcome. |
| Non-goals | MODIFY | Preserve all current non-goals; add standalone SaaS/web app, prompt-only Skill, broad statistical workbench, and host-specific plugin ecosystem for MVP. | Prevents the migration from becoming either UI work or a generic Skill wrapper. | Stronger guardrails. |
| Target Users | KEEP | Retain current users. Clarify that the Portfolio Reviewer is an evaluation stakeholder, not necessarily a daily end user. | Current list remains valid, but product-user vs reviewer roles should not be conflated. | Cleaner product logic. |
| E-commerce Operator persona | KEEP | Rephrase “upload” as “provide or attach an approved data source” where host behavior differs. | Skill hosts may not use a dedicated upload UI. | Delivery-neutral language. |
| Data Analyst persona | KEEP | Add need to inspect execution logic and rerun the result. | Reusable engine makes this a first-class benefit. | Stronger analyst value. |
| Product/Category Manager persona | KEEP | No substantive change. | Needs remain valid. | None. |
| Portfolio Reviewer persona | MODIFY | Add the need to see a working Skill, engine-owned calculations, tests, and failure cases quickly. | Documentation alone is insufficient portfolio proof. | Directly guides repository quality. |
| User Stories | MODIFY | Preserve evidence stories; change file-upload wording to source provision; add stories for execution trace, rerun, and explicit failure when execution is unavailable. | Skill-first changes interaction and introduces execution-state risk. | Better acceptance coverage. |
| JTBD | KEEP | Add one JTBD: when the Skill presents a number, the user can trace it to an executed method and rerun it. | Existing jobs remain correct. | Small expansion tied to core evidence value. |
| Core User Journey | MODIFY | Use: Business Question → Data Source Provision → Schema & Data Validation → Metric/Evidence Definition → Analysis Plan → Deterministic Execution → Evidence Review → Findings → Recommendation if justified → Report + Evidence Contract. | “Upload” and generic “execution” obscure the new responsibility split. | Clearer product behavior without specifying architecture. |
| CORE-001 to CORE-007 | KEEP / MODIFY | Preserve requirements. Add ownership labels or wording that the Skill coordinates and the engine executes/validates. | Requirements remain correct but authority must be explicit. | Traceable responsibility boundaries. |
| MVP-001 CSV | KEEP | No change except Skill invocation wording. | Low complexity, high accessibility. | None. |
| MVP-002 Excel | KEEP | No change except Skill invocation wording. | Common operator/analyst format and useful parsing edge cases. | None. |
| MVP-003 SQLite | KEEP | No change except read-only behavior requirement at product level. | Demonstrates SQL capability without external credentials. | Strong portfolio value. |
| MVP-004 all analytical areas | MODIFY | Replace the single broad requirement with a narrow first workflow: revenue, orders, AOV, and product/category contribution across comparable periods. Optional discounts/refunds may be analyzed only when fields and definitions are sufficient. | Twelve domains create excessive metric, schema, and test combinations. | Major scope reduction and faster credible proof. |
| MVP-005 required fields | KEEP | Add field-semantic ambiguity, not only missing fields. | A column can exist but mean the wrong thing. | Stronger sufficiency behavior. |
| MVP-006 analysis plan | KEEP | Require plan status before engine execution and record changes if the plan is revised. | Supports reproducibility. | More auditable workflow. |
| MVP-007 validation status | MODIFY | Require every material result to reference an engine execution record and validation checks; generated-but-unexecuted code is a failure state. | Prevents the Skill from claiming execution it did not perform. | Critical reliability control. |
| MVP-008 report | KEEP / MODIFY | Keep report sections; require an attached or referenced structured Evidence Contract and reproducibility instructions. | Makes Skill output auditable. | Better GitHub demonstration. |
| MVP-009 public data | KEEP | No change. | Still required. | None. |
| MVP-010 scope labels | KEEP | Add Research and Backlog categories to match Constitution. | Current requirement omits two approved categories. | Governance consistency. |
| New Skill invocation requirement | ADD | The Skill accepts a business question plus an approved data source, clarifies only material ambiguity, and cannot proceed to findings until engine execution/validation status is available. | Defines the user-facing delivery mechanism. | Establishes Layer 1 MVP behavior. |
| New engine authority requirement | ADD | Material computations, SQL results, tests, and validation statuses must originate from Layer 2 and be recorded. | Prevents fabricated execution. | Establishes Layer 2 MVP behavior. |
| Phase 2 requirements | MODIFY | Move the reusable engine out of Phase 3; keep guided questions, richer diagnostics, retained analysis history, inventory/retention, and statistical methods in Phase 2 after the first workflow is stable. | Engine is now required for MVP; other breadth is not. | Corrects roadmap ordering. |
| Phase 3 requirements | MODIFY | Reserve Phase 3 for selected commerce connectors, broader domain coverage, and the full benchmark after reliability is established. | Aligns sequencing with the new model. | More maintainable expansion. |
| Rejected requirements | KEEP / ADD | Preserve Multi-Agent, RAG/vector DB, plugin ecosystem, enterprise SaaS, streaming, autonomous execution, generic chatbot, and enterprise BI exclusions. Add LLM router, memory framework, and complex agent framework explicitly. | User guardrails require explicit confirmation. | No ambiguity about MVP. |
| Non-functional requirements | ADD | Add execution integrity, host portability, deterministic rerun consistency, bounded failure behavior, and read-only handling for database inputs. | Skill-first introduces portability and tool-availability risks. | Improves reliability without selecting architecture. |
| MVP Scope | MODIFY | Replace broad KPI suite with one canonical revenue-performance diagnostic workflow plus required evidence-governance behavior. Retain CSV, Excel, SQLite. | Reliability and speed require narrower scope. | Defines a buildable first release. |
| Out of Scope | MODIFY | Add standalone web UI/SaaS, external marketplace connectors, default predictive/causal analysis, full cohort analysis, A/B testing, and full benchmark implementation. | Prevents implicit scope expansion. | Clear implementation boundary. |
| User Workflow | MODIFY | Rename product responsibilities by layer while preserving the evidence-first order and insufficiency path. | Required for Skill/engine clarity. | Improved traceability. |
| Product Success Definition | MODIFY | Success becomes completion of one Skill-orchestrated and engine-validated workflow producing reproducible findings and Evidence Contract. | Current statement is correct but delivery-neutral. | Testable success definition. |
| Success Metrics | MODIFY | Retain 100% governance targets for the defined test corpus. Add deterministic rerun consistency, execution-record coverage, and canonical workflow completion. State denominators and fixture sets. | Percentages without a defined evaluation set are not meaningful. | Metrics become reproducible. |
| Acceptance Criteria | MODIFY | Reference Constitution v1.1; require executable Skill behavior, engine-backed results, three input formats, canonical analysis, tests, and reproducible example. | Current criteria accept a product definition but not the new executable proof. | Stronger release gate. |
| Risks | MODIFY | Keep existing risks. Add: Skill becomes prompt-only, host lacks execution tools, Skill and engine outputs diverge, reused libraries obscure provenance, and repo becomes documentation-heavy. | These are new primary risks. | More realistic mitigation planning. |
| Assumptions | MODIFY | Add assumptions that at least one supported host can invoke local deterministic tools and that the Skill format can remain sufficiently portable. Mark cross-host behavior as Research Required until tested. | Portability and execution availability are not yet proven. | Prevents unsupported compatibility claims. |
| Future Roadmap | MODIFY | Phase 2: richer local analytics and database connectors. Phase 3: selected commerce APIs and broader evaluation. Benchmark remains deferred until core workflow stability. | Aligns with new layer sequence. | Cleaner roadmap. |
| Open Questions | MODIFY | Retain canonical dataset, first question, metric definitions, Evidence Contract visibility, and insufficiency cases. Add supported host(s), execution availability, portability target, and engine result-reference format. | These decisions materially affect the Skill PRD. | Defines the next review agenda without starting Architecture. |
| Standalone platform-first requirements | REMOVE | Remove only assumptions that require a dedicated platform/UI for MVP. Report output and product experience remain. | The delivery mechanism changed. | Lower build cost without loss of analytical scope. |

---

# C. Skill-first MVP Scope

## MVP Product Statement

The CommerceLens Skill MVP is a user-facing e-commerce analytical workflow that accepts a business question and CSV, Excel, or SQLite data; determines whether the data can support the question; coordinates a deterministic revenue-performance analysis; and returns validated findings, limitations, alternative explanations, and an Evidence Contract.

It is not a general analytics agent, statistical workbench, standalone SaaS, marketplace connector, or autonomous decision system.

## Canonical MVP Business Workflow

**Primary business question:**

> How did revenue performance change between two comparable periods, and which products or categories contributed most to that change?

**Supported analytical outputs:**

- Revenue, order count, and AOV with explicit metric definitions.
- Period-over-period absolute and percentage change.
- Product and category contribution to the observed change.
- Data-quality and sufficiency findings relevant to those metrics.
- Descriptive findings and bounded diagnostic statements only.
- Alternative explanations, including product mix, incomplete periods, missing/duplicated orders, refunds/discount treatment, and stock availability when the data does not resolve them.
- Recommendations only when supported; otherwise a next-evidence request or “Insufficient evidence to conclude.”

This workflow is narrow enough to validate deeply and broad enough to demonstrate SQL, DataFrame operations, business metrics, evidence governance, failure handling, and decision-ready communication.

## Layer 1 — Skill MVP Responsibilities

- Accept the business question and approved data source.
- Detect material ambiguity in periods, currency, revenue field semantics, order granularity, refunds, discounts, and category/product identifiers.
- Ask a clarification only when the answer would materially change the metric or claim.
- Classify the requested claim.
- Define metrics before use.
- Generate hypotheses and alternative explanations as hypotheses, not findings.
- State required evidence and perform a sufficiency decision using engine-provided schema/profile results.
- Produce an analysis plan before requesting execution.
- Request only approved deterministic operations.
- Interpret only returned, validated results.
- Generate a concise analytical report and structured Evidence Contract.
- Fail closed when execution is unavailable, unsuccessful, inconsistent, or insufficiently traceable.

## Layer 2 — Engine MVP Responsibilities

- Ingest CSV, Excel, and SQLite inputs using read-only behavior where applicable.
- Inspect tables/sheets, columns, types, row counts, nulls, duplicates, date ranges, candidate keys, and basic cardinality.
- Preserve source identity and analysis period.
- Execute approved SQL/Python transformations and KPI calculations.
- Validate metric invariants, aggregations, denominators, join cardinality, period completeness, and result consistency.
- Return structured results, warnings, errors, and validation status.
- Record the executed procedure, parameters, source references, and calculated outputs needed by the Evidence Contract.
- Never return synthetic success when an operation failed.

## MVP Analytical Capability Prioritization

Scoring uses a relative 1–5 scale. Higher is better except Implementation Cost, where 5 is most costly. The classification is a product decision, not proof of future value.

| Capability | Business Value | Reliability | Cost | Portfolio Value | Decision | Rationale |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Revenue | 5 | 5 | 2 | 5 | MVP | Core commercial KPI and ideal surface for metric-governance proof. |
| Orders | 5 | 5 | 1 | 4 | MVP | Required denominator and trend driver. |
| AOV | 5 | 5 | 1 | 4 | MVP | Simple but exposes denominator and cancellation/refund definitions. |
| Product performance | 5 | 4 | 2 | 5 | MVP | High decision value and clear segmentation. |
| Category performance | 5 | 4 | 2 | 5 | MVP | Demonstrates aggregation and mix contribution. |
| Descriptive statistics | 4 | 5 | 1 | 3 | MVP (bounded) | Needed for profiles and comparisons; not a generic stats module. |
| Diagnostic analysis | 5 | 3 | 3 | 5 | MVP (bounded) | Allow contribution, segmentation, and comparisons; prohibit causal wording. |
| Discounts | 4 | 3 | 3 | 4 | Phase 2 | Gross/net and allocation semantics vary materially. |
| Refunds | 5 | 3 | 3 | 4 | Phase 2 | Timing, partial refunds, returns, and order status need stronger models. |
| Gross margin | 5 | 3 | 4 | 5 | Phase 2 | COGS, shipping, tax, refunds, and allocation definitions create high ambiguity. |
| Inventory | 5 | 3 | 4 | 5 | Phase 2 | Requires snapshots or movement logic beyond basic order tables. |
| Stockouts | 5 | 2 | 4 | 5 | Phase 2 | Stockout inference is unsafe without time-grained inventory evidence. |
| Customer repeat purchase | 4 | 3 | 3 | 4 | Phase 2 | Requires stable customer identity, time windows, and privacy controls. |
| Cohort analysis | 4 | 3 | 4 | 5 | Phase 2 | Valuable but adds cohort definitions and censoring/window issues. |
| Confidence intervals | 3 | 4 | 3 | 4 | Phase 2 | Useful once sampling assumptions and eligible metrics are defined. |
| Hypothesis testing | 3 | 3 | 4 | 5 | Phase 2 | Requires assumption checks, multiple-testing controls, and careful interpretation. |
| Correlation | 3 | 2 | 2 | 3 | Phase 2 | Easy to compute but commonly overinterpreted; add only with strong claim controls. |
| A/B testing | 5 | 3 | 5 | 5 | Phase 3 / Research | High value and portfolio impact, but experiment design, power, assignment, interference, and metric definitions materially expand scope. |
| Predictive analysis | 4 | 2 | 5 | 5 | Deferred | Not needed to prove evidence-first descriptive/diagnostic workflow. |
| Causal analysis | 5 | 1 | 5 | 5 | Deferred | Requires appropriate designs and must not be simulated from ordinary transaction data. |

## Required MVP Outputs

Each completed analysis must provide:

1. Business Question and clarified scope.
2. Claim type and permitted claim strength.
3. Metric definitions.
4. Source summary and analysis period.
5. Required evidence and data sufficiency status.
6. Analysis plan.
7. Engine execution and validation status.
8. Findings linked to calculated results.
9. Alternative explanations.
10. Limitations and assumptions.
11. Recommendation only when justified.
12. Structured Evidence Contract with reproducibility references.

## MVP Acceptance Gates

The Skill-first MVP is complete only when all gates pass:

- The canonical synthetic dataset can be represented and analyzed through CSV, Excel, and SQLite inputs.
- The same declared metrics and analysis period produce numerically consistent results across the three representations, subject to documented format differences.
- Every material numerical claim references an engine-produced result and validation status.
- Every material claim is classified and included in or linked to an Evidence Contract.
- Required negative cases pass: missing revenue field, ambiguous date field, duplicated orders, incomplete period, unsupported causal prompt, unavailable execution, and unjustified recommendation.
- A failed or unavailable execution never appears as a completed finding.
- A fresh user can reproduce the canonical example from documented inputs and commands/instructions.
- GitHub visibly includes executable implementation, tests, expected outputs, and evaluation results.
- No external connector, standalone SaaS infrastructure, Multi-Agent, RAG, vector database, complex agent framework, LLM router, memory framework, plugin ecosystem, enterprise infrastructure, or streaming system is required.

## Reuse Before Rebuild

### Formal Engineering Principle

> **Reuse before rebuild.** Reuse or adapt mature commodity-level analytics infrastructure unless it cannot meet CommerceLens requirements for analytical correctness, evidence traceability, reproducibility, data safety, or benchmark validity. Build the governance and reliability layer that differentiates CommerceLens.

### BUILD / REUSE / ADAPT / DEFER Matrix

| Capability | Decision | Recommended Boundary | Rationale / Research Status |
| --- | --- | --- | --- |
| CSV ingestion | REUSE | Use a mature DataFrame/SQL reader; add CommerceLens source metadata and error handling. | Commodity capability. pandas provides standard CSV I/O; DuckDB can query file formats directly. |
| Excel parsing | REUSE | Use pandas-compatible Excel engines; preserve workbook/sheet selection and parsing warnings. | Commodity capability; do not write a new parser. |
| SQLite access | REUSE | Use a mature SQLite/DuckDB access layer in read-only mode; record selected tables and queries. | Commodity capability; DuckDB documents direct SQLite access. |
| SQL execution | REUSE | Use an embedded analytical SQL engine and capture exact query/parameters/results. | DuckDB provides in-process SQL and broad file/database access. Final choice belongs to Architecture. |
| DataFrames | REUSE | Use pandas initially unless performance evidence justifies another library. | Mature, comprehensible, and portfolio-friendly. No current evidence requires Polars. |
| Statistical tests | REUSE + DEFER | When Phase 2 begins, use SciPy/statsmodels and wrap with assumption/claim controls. | SciPy already supplies tests and confidence intervals; CommerceLens should govern usage, not reimplement formulas. |
| Visualization | ADAPT | Reuse a mature plotting library and build only a small approved chart-selection/report layer. | Chart rendering is commodity; evidence-linked chart captions and source references are differentiated. |
| Schema inspection | ADAPT | Reuse library metadata/type inspection; build commerce-semantic checks and ambiguity reporting. | Generic inspection is commodity; semantic sufficiency is differentiated. |
| Basic data profiling | ADAPT | Start with targeted deterministic checks. Evaluate a profiling library only if it reduces code without obscuring provenance. | **Research Required** before adopting a heavy profiling dependency. Automated profiling tools exist, but their output does not replace CommerceLens sufficiency reasoning. |
| Data quality validation | ADAPT | Implement the minimum explicit checks first; evaluate Great Expectations after MVP if rule volume grows. | Great Expectations has mature checkpoint/validation concepts, but may be excessive for the first vertical slice. **Research Required** for fit and dependency cost. |
| Report rendering | ADAPT | Reuse Markdown/template rendering; build the CommerceLens report schema, evidence links, and insufficiency presentation. | Rendering is commodity; analytical structure is differentiated. |
| Skill structure | ADAPT | Follow the open Agent Skills structure: concise Skill instructions with scripts/references loaded as needed. Avoid host-specific assumptions where possible. | The Agent Skills specification defines a lightweight portable package shape; cross-host execution compatibility remains **Research Required**. |
| KPI definitions | BUILD | Create versioned CommerceLens metric definitions, eligibility rules, and ambiguity handling. | KPI semantics are central to analytical correctness and business value. |
| Data sufficiency reasoning | BUILD | Map claim type and metric to required fields, conditions, and downgrade/block outcomes. | Core differentiated capability. |
| Evidence tracking | BUILD | Produce structured links from claims to source, metric, method, result, validation, assumptions, and limitations. | Core differentiated capability; generic lineage alone is insufficient. |
| Evidence Contract | BUILD | Own the schema, completeness rules, and user-facing representation. | Primary CommerceLens differentiator. |
| Claim classification/control | BUILD | Enforce descriptive/diagnostic/predictive/causal/prescriptive limits and correlation safeguards. | Core differentiated capability. |
| Alternative explanation requirements | BUILD | Require plausible alternatives and mark whether data can test them. | Differentiated analyst workflow. |
| Deterministic validation orchestration | BUILD | Define which validations must pass before each material result can be used. | Libraries compute checks; CommerceLens governs their required relationship to claims. |
| Decision reliability evaluation | BUILD + DEFER | Define MVP acceptance fixtures now; build the full Benchmark only after workflow stability. | Differentiated long-term layer, but not a first-release product. |

### Reference Findings

- The [Agent Skills specification](https://agentskills.io/specification) supports a lightweight Skill package with metadata and progressively disclosed instructions/resources; CommerceLens should adapt the structure, not treat the format itself as differentiation.
- [DuckDB](https://duckdb.org/docs/current/guides/overview.html) documents embedded SQL workflows across CSV/Excel and direct querying of SQLite, PostgreSQL, and MySQL; this supports reuse for commodity execution, subject to Architecture validation.
- [pandas I/O documentation](https://pandas.pydata.org/docs/reference/io.html) covers CSV and Excel ingestion, supporting a reuse decision rather than custom parsing.
- [SciPy statistics documentation](https://docs.scipy.org/doc/scipy/reference/stats.html) provides hypothesis tests and confidence-interval capabilities; CommerceLens should build governance around test selection and interpretation, not new statistical implementations.
- [Great Expectations](https://docs.greatexpectations.io/docs/reference/api/checkpoint_class/) offers validation/checkpoint abstractions. It is a candidate for later adaptation, not an automatic MVP dependency.

## Existing Skills / Open-source Reference Strategy

Research should be question-led. Every external project must be evaluated against a specific CommerceLens gap and classified before adoption.

| Reference Category | What to Learn | What Not to Copy | Decision Rule |
| --- | --- | --- | --- |
| AI analytics Skills | Skill organization, trigger descriptions, progressive disclosure, safe execution handoff. | Broad “analyze anything” positioning or unverified narrative outputs. | Adapt structure only if it remains concise and testable. |
| Data analyst agents | Planning/execution separation, error handling, structured outputs. | Autonomous conclusions, hidden prompts, or framework-heavy orchestration. | Reuse patterns only when execution provenance is inspectable. |
| Text-to-SQL systems | Schema context, query review, execution/error loops, SQL safety. | Treating valid SQL as sufficient evidence or making Text-to-SQL the product. | Adapt execution safety; build CommerceLens evidence governance. |
| Statistical tools | Tested implementations, assumption diagnostics, result objects. | Automatic significance claims or causal language. | Reuse calculations; build eligibility and interpretation controls. |
| Analytics assistants | User onboarding, question clarification, report readability. | Generic chatbot/UI breadth. | Borrow interaction patterns only when they reduce friction without weakening workflow. |

Required research record for every candidate:

- Exact capability gap.
- License and maintenance status.
- Supported execution environment.
- Determinism and error behavior.
- Provenance/auditability.
- Security and data-handling implications.
- Dependency weight and lock-in.
- Evidence-first fit.
- Decision: REUSE, ADAPT, DEFER, REJECT, or **Research Required**.

No named open-source project should be described as “integrated” or “suitable” until this record is complete and a small technical spike is reviewed in a later phase.

## Future Connector Strategy

| Connector / Source | Classification | Reason | Entry Condition |
| --- | --- | --- | --- |
| CSV | MVP | Lowest setup cost and strongest reproducibility for a public example. | Canonical schema mapping and validation. |
| Excel | MVP | Common business format and valuable parsing/data-quality surface. | Sheet selection, type/date ambiguity, and formula/value behavior documented. |
| SQLite | MVP | Local SQL demonstration without network credentials. | Read-only access and table selection validation. |
| PostgreSQL | Phase 2 | High reuse potential and lower semantic complexity than commerce APIs. | Stable engine interface, read-only credentials, query limits, provenance, and security review. |
| MySQL | Phase 2 | Same rationale as PostgreSQL. | Same as PostgreSQL. |
| Shopify | Phase 3 | Valuable structured commerce source, but authentication, scopes, pagination, versioning, and commerce semantic mapping add complexity. Shopify documents quarterly API versions and restricted access for older order data. | Stable local workflow; connector-specific metric mapping; authorization/data-safety review; reproducibility snapshot strategy. |
| Amazon Seller / SP-API | Phase 3 / Research | Strong value but onboarding, authorization, reports, marketplaces, and data semantics are materially complex. | Approved use case, test account/data, report mapping, rate-limit/retry strategy, and evidence snapshot design. |
| Amazon Marketplace (broader) | Research | Scope is ambiguous beyond SP-API seller analytics. | Define exact user, API, region, dataset, and decision use case. |
| 蝦皮 | Research | Regional availability, partner access, permissions, and schema stability require verification. | Official API access and a specific evidence-first use case. |
| 淘寶 | Research | Platform access, regional constraints, permissions, and semantic mapping require verification. | Official API access and a specific evidence-first use case. |
| Other marketplaces | Research | “Marketplace connector” is not a product requirement by itself. | Business demand plus accessible official API and mapped evidence value. |
| Write-back/action connectors | Rejected for current roadmap | CommerceLens supports human decisions and must not execute business actions in MVP/near-term connector phases. | Requires a future constitutional/product review. |

The connector classifications for Shopify and Amazon are supported by current official documentation: Shopify exposes commerce data through its [GraphQL Admin API](https://shopify.dev/docs/api/admin-graphql/latest) and applies access/version constraints; Amazon SP-API requires registration and authorization and spans orders, reports, payments, and other seller data in its [official documentation](https://developer-docs.amazon.com/sp-api). These are useful future sources, but not necessary to validate CommerceLens’ core evidence workflow.

## GitHub / Portfolio Strategy

The repository must answer the following in under one minute:

1. What decision problem does CommerceLens solve?
2. Why can generic AI file analysis produce unsafe or unsupported conclusions?
3. What does the CommerceLens Skill do?
4. What does the deterministic engine do?
5. How is every material claim traced and validated?
6. What happens when evidence is insufficient?

The repository must then prove the answer through:

- One runnable canonical e-commerce example.
- The same example in CSV, Excel, and SQLite representations.
- A visible analysis plan, executed procedure, validation output, analytical report, and Evidence Contract.
- Tests for calculations, metric definitions, data-quality rules, evidence linkage, claim downgrade/blocking, and failed execution.
- At least one “generic AI might overclaim” negative example showing CommerceLens refusing or downgrading the claim.
- Reproduction instructions with declared environment and expected outputs.
- A short design explanation of Skill responsibility vs engine responsibility.
- Measured evaluation results for the defined test corpus.

Documentation is necessary but not sufficient. A repository with extensive Constitution/PRD text and no executable vertical slice fails the portfolio objective.

## Scope Guardrails

| Capability | MVP Status | Reconsideration Rule |
| --- | --- | --- |
| Multi-Agent | Rejected | Only if one agent cannot satisfy a documented analytical control that cannot be handled deterministically. |
| RAG | Rejected | Only if an approved workflow requires retrieval from an external knowledge corpus; structured input analysis does not. |
| Vector Database | Rejected | Only if a validated retrieval requirement exists. |
| Complex Agent Framework | Rejected | Only if required orchestration cannot be implemented and tested with a simpler Skill/tool pattern. |
| LLM Router | Rejected | Only if measured model-specific failures justify routing. |
| Memory Framework | Rejected | Saved analytical history may be Phase 2, but a general memory framework is not required. |
| Plugin Ecosystem | Rejected | Individual connectors may be approved later; an ecosystem is not a product goal. |
| Enterprise SaaS Infrastructure | Rejected | Not required for a portfolio-quality local/file MVP. |
| Real-time Streaming | Rejected | Current business questions are batch analytical workflows. |
| Standalone Web Application | Deferred | A thin demo interface may be considered only after the Skill + engine vertical slice is credible. |

---

# Recommended Migration Sequence

The following is the approved program sequence. Listing later stages does not initiate Architecture, implementation, or Skill creation in this document.

1. **Approve Skill-first Scope Migration.** Record the GO decision and mandatory development constraints.
2. **Amend `PROJECT_MASTER_INSTRUCTIONS.md` v1.0 → v1.1.** Apply only the approved constitutional migration changes and re-freeze the Constitution.
3. **Amend `PRD.md` v1.0 → v1.1.** Apply only the approved product-requirement migration changes and re-freeze the PRD.
4. **Define Skill Scope Specification.** Establish the behavioral contract of the CommerceLens Skill before Architecture begins.
5. **Define Evidence Contract Specification.** Lock required fields, claim-to-evidence links, execution references, insufficiency states, and visible versus supporting detail.
6. **Define Canonical Synthetic Dataset + Metric Dictionary.** Fix grain, periods, product/category fields, order-status rules, revenue, order count, and AOV definitions.
7. **Define MVP Evaluation Fixtures.** Include positive, ambiguous, insufficient, causal-overclaim, and failed-execution cases.
8. **Architecture.** Begin only after all required migration artifacts are completed and approved.
9. **Implementation.** Implement only the approved architecture and MVP scope.
10. **CommerceLens Skill MVP.** Complete the narrow Skill + deterministic engine vertical slice.
11. **Evaluation.** Execute the approved fixtures and document results and limitations.
12. **GitHub Release.** Release executable implementation, tests, evaluation cases, and the reproducible canonical example.
13. **Decision Reliability Benchmark expansion.** Expand the benchmark only after the MVP workflow is stable and evaluated.

## Purpose of the Skill Scope Specification

The Skill Scope Specification is a pre-Architecture behavioral contract. It is **not**:

- Architecture.
- `SKILL.md` implementation.
- Prompt engineering.
- Tool implementation.

Its purpose is to define how the CommerceLens Skill must behave before technical design begins. It should eventually specify:

- Accepted inputs.
- User and Business Question interaction.
- Skill responsibilities.
- Skill non-responsibilities.
- Allowed analytical actions.
- Deterministic execution dependency.
- Skill ↔ Engine responsibility boundary.
- Output contract.
- Evidence Contract dependency.
- Insufficiency behavior.
- Fail-closed behavior.
- Execution-unavailable behavior.
- Unsupported-claim behavior.

This migration record does not create the Skill Scope Specification.

# Final Recommendation

### GO

CommerceLens will migrate from Product-first to Skill-first because the new delivery mechanism better focuses effort on the actual differentiated value: evidence governance, data sufficiency, claim control, deterministic validation orchestration, and reproducibility. It avoids spending the first release on web-product infrastructure that does not prove analytical reliability.

The four Approved Skill-first Development Constraints remain mandatory. In particular, Layer 2 is required in the MVP, the analytical scope remains limited to the canonical workflow, and the repository must prove execution and failure behavior through tests. These are approved development constraints, not conditions on the migration decision.

There is **Insufficient evidence to conclude** that Skill-first will by itself create more GitHub stars, stronger recruiter response, greater market adoption, or stronger user demand. The MVP must generate evidence through executable implementation, evaluation results, reviewer feedback, and user feedback where available.

**Stop condition:** The Skill-first Scope Migration is approved.

No Architecture or implementation should begin until the following migration artifacts are completed and approved:

- `PROJECT_MASTER_INSTRUCTIONS.md` v1.1.
- `PRD.md` v1.1.
- Skill Scope Specification.
- Evidence Contract Specification.
- Canonical Synthetic Dataset + Metric Dictionary.
- MVP Evaluation Fixtures.
