# CommerceLens AI Required Evidence Matrix Specification

**Document:** `REQUIRED_EVIDENCE_MATRIX_SPECIFICATION.md`  
**Milestone:** R3 — Required Evidence Matrix  
**Version:** R3 v1.0  
**Status:** Approved  
**State:** Frozen  
**Date:** 2026-09-22  
**Project:** CommerceLens AI  
**Product compatibility:** CommerceLens AI v0.2.0 behavior unchanged

---

## 1. Purpose

This specification defines the minimum governed, proposition-specific Required Evidence model needed to determine whether a future diagnostic test is legitimately eligible to run.

For one exact Diagnostic Proposition, R3 answers:

> What evidence must exist, what function must each evidence item serve, and what semantic, structural, alignment, coverage, measurement, provenance, and validation requirements must be satisfied before diagnostic execution is allowed?

R3 governs evidence qualification requirements. It does not establish a diagnostic conclusion, test result, support criterion, Finding, or Claim permission.

The controlling relationship is:

```text
Diagnostic Proposition
→ Resolved Required Evidence Profile
→ Available Evidence
→ existing Data Sufficiency / Evidence Admissibility authorities
→ diagnostic test eligible or blocked
```

It is not:

```text
Required Evidence Profile
→ Supported Diagnostic Finding
```

This specification operationalizes the frozen rule:

> No material claim without traceable evidence.

---

## 2. Scope

R3 defines governance semantics for:

- the Layered Required Evidence Architecture;
- the Required Evidence Profile and its resolved proposition-specific authority;
- reusable Proposition-Family Requirement Templates;
- Exact Proposition Binding;
- Method-Specific Requirement References without method definition;
- evidence roles and evidence-dimension applicability;
- semantic validity, source authority, completeness, alignment, measurement validity, missingness, provenance, and validation requirements;
- conditional Metric, unit, currency, grain, join, denominator, external-admission, and method-prerequisite requirements;
- dependency source classification;
- blocking, qualification, and material narrowing rules;
- deterministic pre-test requirement evaluation;
- integration with existing Data Sufficiency and Evidence Admissibility authorities;
- profile identity, versioning, and immutable historical binding;
- human-reviewable matrix views;
- the R2 integration and R4/R5 handoff boundaries; and
- evaluator-conformance requirements.

R3 applies to future diagnostic test eligibility. It does not authorize the implementation or public use of such tests.

---

## 3. Non-Scope

R3 does not:

- redesign or amend frozen R1 or R2 semantics;
- define a diagnostic formula, estimator, weighting rule, interaction allocation, threshold, effect size, support criterion, or contradiction criterion;
- define or implement a diagnostic method registry;
- generate hypotheses or Alternative Explanations;
- determine `CRITERION_MET`, `CRITERION_NOT_MET`, or `PROPOSITION_CONTRADICTED`;
- authorize a Finding or material Claim;
- replace, extend, or bypass `ClaimDecision`;
- create new R2 states or a lifecycle state machine;
- create a second Data Sufficiency or Evidence Admissibility authority;
- prescribe a database schema, runtime contract, class, enum, persistence layout, API, or serialization format;
- expand the canonical dataset, supported Metrics, or public product scope;
- acquire, browse for, or automatically admit external evidence;
- implement fixtures, tests, SQL, Python, statistical code, migrations, or runtime policy;
- change v0.2.0 behavior or its descriptive-only positive Claim permission; or
- begin R4, R5, or R6.

---

## 4. Frozen Authorities and Terminology

### 4.1 Governing authorities

R3 extends but does not redefine:

- `PROJECT_MASTER_INSTRUCTIONS.md`;
- `DIAGNOSTIC_REASONING_SPECIFICATION.md` (R1);
- `HYPOTHESIS_FINDING_STATE_MODEL_SPECIFICATION.md` (R2);
- `EVIDENCE_CONTRACT_SPECIFICATION.md`;
- `ARCHITECTURE_SPECIFICATION.md`;
- `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md`;
- `EVALUATION_FIXTURES_SPECIFICATION.md`; and
- the current approved implementation authorities documented by the repository.

If this draft conflicts with a frozen authority, the frozen authority controls and the conflicting R3 text is non-conforming.

### 4.2 Existing runtime authorities preserved

R3 preserves the current authority boundaries represented by:

- `AnalysisRequest.required_evidence`;
- `EvidenceRequirement`;
- `AvailableEvidence`;
- `DataSufficiencyResult`;
- canonical schema and canonicalization records;
- Data Quality results;
- the Metric Registry;
- `ExecutionRecord` and `ExecutedResult`;
- `ValidationRecord` and `ValidatedResult`;
- `EvidenceAdmissibilityRecord` and `AdmissibleEvidence`;
- dataset, canonical dataset, population, period, artifact, and fingerprint references;
- retained-run manifests and immutable evidence artifacts; and
- `ClaimCandidate` and `ClaimDecision`.

The current physical `EvidenceRequirement` and `AvailableEvidence` contracts are narrower than the R3 semantic model. This specification does not modify them or prescribe their future replacement.

Current result-centered descriptive `AdmissibleEvidence` remains authoritative only for its governed descriptive role and intended use. A validated and descriptively admissible result MAY be an authenticated candidate input for a future diagnostic proposition, but its descriptive admissibility is not inherited as diagnostic-input admissibility. R3 does not modify the current descriptive Evidence Admissibility implementation or prescribe a new physical diagnostic evidence contract.

### 4.3 Preserved distinctions

The following are binding:

```text
Field exists != Required Evidence satisfied
Available Evidence != Admissible Evidence
Required Evidence for Proposition A != Required Evidence for Proposition B
Test eligible != Test supports proposition
Test supports proposition != Claim authorized
Qualification != evidence waiver
Family Template != Resolved Required Evidence authority
Descriptive AdmissibleEvidence != diagnostic-input admissibility
Conditionally substantive != optional to resolve
Exact Proposition Binding != Diagnostic Evaluation
Required Evidence Profile != evaluation authority
```

### 4.4 Normative language

`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative. Conceptual labels in uppercase or code formatting define required meaning only; they do not prescribe runtime enums or physical fields.

---

## 5. Governing Principles

1. **Exact proposition first.** Required Evidence is defined for one exact Diagnostic Proposition, not for a topic label or free-form hypothesis name.
2. **Evidence function and evidence fitness are separate.** Evidence roles state what evidence does; evidence dimensions state whether it is fit to do it.
3. **Field presence is never sufficient authority.** Names, plausible values, and schema availability cannot replace governed semantics.
4. **Availability and admissibility remain separate and intended-use-specific.** Evidence may exist and still be invalid for the proposition, role, or intended use. Descriptive admissibility does not automatically establish diagnostic-input admissibility.
5. **All frozen R1 minimum dimensions are mandatory to resolve, explicitly and non-Cartesianly.** Every resolved profile must make an applicability determination for relevance, semantic validity, source authority, completeness, temporal alignment, population alignment, Metric compatibility, unit and currency compatibility, measurement validity, missingness, provenance, and validation status at the proper proposition, role, cross-role, shared-authority, or method-specific level. A dimension that is not materially applicable requires an explicit governed reason; no dimension may silently disappear.
6. **The earliest material blocker controls eligibility.** Later evidence, qualification, or prose cannot repair an earlier required failure.
7. **Material narrowing changes governed meaning and follows R2 authority.** If evidence supports only a narrower object, a new exact R2 Diagnostic Proposition, narrower Exact Proposition Binding, resolved profile, and new R2 Diagnostic Evaluation must be used. R3 defines evidence requirements; it does not create evaluation authority.
8. **Reuse does not confer authority.** Family templates and shared lineage reduce duplication but do not authorize evidence or tests.
9. **Existing deterministic authorities are reused.** R3 supplies proposition-specific requirements; it does not recompute sufficiency, validation, admission, or Claim permission.
10. **Independent chains remain independent.** A defect in one evidence chain does not invalidate a separately complete chain.
11. **No confidence score.** Requirement satisfaction is not an LLM confidence, probability, evidence-strength percentage, or quality score.
12. **Fail closed.** Undefined, missing, failed, ambiguous, inadmissible, or unresolved material requirements block the affected test.

---

## 6. Layered Required Evidence Architecture

The approved architecture is:

```text
Global Evidence Governance
+ Proposition-Family Requirement Template
+ Exact Proposition Binding
+ Method-Specific Requirement References
→ Resolved Required Evidence Profile
```

The resolved profile is the proposition-specific evidence contract used for eligibility evaluation.

### 6.1 Global Evidence Governance

Global Evidence Governance defines universal frozen principles, dimensions, and fail-closed invariants. Every frozen R1 minimum evidence dimension requires explicit applicability resolution in every Resolved Required Evidence Profile. A dimension may be explicitly non-applicable when it is not materially substantive to the exact proposition, but it may never be silently omitted. Additional conditional dimensions apply when their triggers are present.

Global rules MAY add protection. They MUST NOT weaken a family requirement, exact binding, frozen authority, or stricter method prerequisite.

### 6.2 Proposition-Family Requirement Template

A Proposition-Family Requirement Template defines stable reusable evidence patterns for one bounded diagnostic family. It MAY identify:

- typical evidence roles;
- typical measurement requirements;
- expected grain;
- identity and join patterns;
- population relationships;
- common coverage concerns;
- prohibited proxy types; and
- unresolved method-owned requirement slots.

A family template MUST NOT define or establish:

- exact proposition authority;
- evidence satisfaction;
- sufficiency or admissibility;
- a formula, estimator, threshold, support criterion, or contradiction criterion;
- test eligibility by itself; or
- Claim permission.

Family membership is organizational and reusable metadata. It is not material authority.

### 6.3 Exact Proposition Binding

Exact Proposition Binding is the controlling proposition-specific evidence authority. It resolves global and family requirements against the exact:

- Diagnostic Proposition;
- intended claim class and material use;
- analytical scope;
- outcome and evidence-role populations;
- periods and comparison basis;
- variables and governed semantics;
- Metric references and definition versions;
- required evidence roles;
- dependency source classes;
- grains, identities, and joins;
- units and currencies;
- measurement classifications;
- completeness, coverage, and missingness rules;
- provenance and validation requirements;
- blocking conditions;
- qualification and narrowing constraints; and
- method-prerequisite references.

Only this resolved binding may serve as the proposition-specific Required Evidence authority.

Exact Proposition Binding defines evidence requirements only. It does not create, finalize, or replace the R2 Diagnostic Proposition or Diagnostic Evaluation authority.

### 6.4 Method-Specific Requirement References

R3 permits references to future governed method prerequisites. Such prerequisites MAY add or tighten evidence conditions. They MUST NOT:

- waive a frozen evidence dimension;
- weaken global, family, or exact requirements;
- redefine R1 or R2;
- define a formula or implementation inside R3; or
- define support or contradiction criteria inside R3.

An unresolved material method prerequisite prevents test eligibility. It does not permit a best-effort method substitute.

### 6.5 Layer resolution rules

Layer resolution is cumulative and fail-closed:

1. Global rules always apply unless a dimension is explicitly and validly non-applicable.
2. Family templates add reusable requirements but do not remove global requirements.
3. Exact bindings resolve and may tighten family requirements.
4. Method references may add or tighten evidence requirements.
5. No lower layer may weaken a stricter applicable requirement from another authoritative layer.
6. Conflicting layer requirements remain unresolved until governed authority resolves them; an evaluator MUST NOT select the more permissive rule.

---

## 7. Required Evidence Profile

### 7.1 Definition

A Required Evidence Profile is the governed specification of evidence conditions for a bounded proposition or family. A **Resolved Required Evidence Profile** is the immutable-by-reference result of applying the four architecture layers to one exact Diagnostic Proposition.

### 7.2 Minimum conceptual content

A resolved profile must conceptually identify or bind:

- profile identity and version;
- exact Diagnostic Proposition reference;
- intended claim class;
- intended material use;
- family template identity and version, if used;
- required evidence roles;
- role-specific semantic requirements;
- dimension-applicability decisions;
- dependency source classification;
- scope, populations, periods, and comparison basis;
- variables and governed definitions;
- grain, identity, and join requirements;
- completeness, coverage, and missingness requirements;
- measurement classification and fitness conditions;
- Metric, unit, and currency compatibility;
- provenance requirements;
- pre-execution, method-prerequisite, and post-execution validation obligations;
- blocking conditions;
- qualification and material-narrowing rules;
- method-prerequisite references; and
- governing authority references.

This list defines governance semantics. It is not a database, JSON, Pydantic, or API schema.

### 7.3 Profile completeness

A profile is defined only when every material requirement and every applicable dimension can be resolved without material ambiguity. A profile containing an undefined material rule, an unbounded proxy, an unresolved layer conflict, or a required but unspecified materiality rule is incomplete and blocks the affected test.

### 7.4 Profile authority

A resolved profile establishes what evidence qualification must be demonstrated. It does not establish that evidence is available, sufficient, admissible, supportive, or Claim-authorizing.

A Required Evidence Profile is requirement authority only. It is not a Diagnostic Evaluation, does not create evaluation identity or history, and does not finalize a material judgment. Those authorities remain with R2.

---

## 8. Profile Identity and Versioning

### 8.1 Identity

Profile identity must preserve the material meaning of its requirement set. It must be reviewable through human-readable content and references; an opaque hash alone is insufficient.

### 8.2 Material changes requiring a new version

A new profile version is required when any material governance changes, including:

- evidence roles;
- semantic requirements;
- measurement classification or permitted use;
- source-authority rules;
- dependency source class;
- completeness, coverage, or missingness rule;
- population, period, grain, identity, or join rule;
- Metric, unit, or currency compatibility;
- blocking consequence;
- validation requirement; or
- method-prerequisite reference.

Pure formatting, translation, or non-material wording MAY retain the same semantic version when existing project governance permits.

### 8.3 Historical binding

A finalized R2 Diagnostic Evaluation remains bound to the exact profile version originally used. A later profile version MUST NOT mutate, reinterpret, or silently replace historical authority. R3 supplies the versioned requirement authority; R2 owns evaluation identity, finalization, immutability, and historical authority. Re-evaluation under a new material profile version requires a new Diagnostic Evaluation under R2.

---

## 9. Proposition-Family Requirement Templates

### 9.1 Purpose

Family templates reduce repeated governance for propositions with materially similar evidence patterns. They support discovery and consistent authoring without becoming test or evidence authority.

### 9.2 Permitted contents

A family template SHOULD identify:

- the bounded family meaning;
- typical roles and relationships;
- typical source classes;
- expected grain and identity basis;
- usual population and temporal relationships;
- measurement types that may or may not be acceptable;
- coverage and missingness concerns;
- common blocking conditions;
- applicable existing authorities; and
- unresolved method-owned slots.

### 9.3 Prohibited use

An evaluator MUST NOT infer that evidence is sufficient or admissible because it resembles a family template. No family default may weaken an exact requirement. If exact material meaning cannot be resolved, the proposition is not test eligible.

---

## 10. Exact Proposition Binding

### 10.1 Binding rule

The exact binding must materially match the R2 Diagnostic Proposition. It must not substitute a broader, narrower, stronger, differently timed, differently populated, or differently measured proposition merely because the display text appears similar.

### 10.2 Material identity dimensions

The binding must preserve, as applicable:

- relationship or pattern and direction;
- observed outcome;
- intended claim class;
- scope;
- populations;
- periods and comparison basis;
- variables and semantic meaning;
- authoritative Metrics and versions;
- units and currencies;
- intended material use; and
- constraints bounding interpretation or strength.

### 10.3 Narrowing

If available evidence supports only a narrower population, period, scope, or material meaning, the broad proposition MUST NOT remain the evaluated object with a cautionary disclaimer. Instead:

```text
materially narrower supported meaning
→ new exact R2 Diagnostic Proposition
→ narrower Exact Proposition Binding
→ new Resolved Required Evidence Profile for that proposition
→ new R2 Diagnostic Evaluation bound to that proposition and profile
```

A qualification MAY communicate the narrowing after it is structurally represented. It MUST NOT substitute for that representation.

The Exact Proposition Binding and Resolved Required Evidence Profile define proposition-specific evidence requirements. They do not themselves create Diagnostic Evaluation authority.

---

## 11. Evidence Roles

Evidence Role answers: **What function does this evidence serve in this proposition?**

Evidence Dimension answers: **Is this evidence fit for that function and intended use?**

Roles and dimensions are orthogonal.

### 11.1 Core roles

| Role | Governed function |
|---|---|
| Observed Outcome Evidence | Establishes the governed outcome being examined, without by itself establishing a diagnostic explanation |
| Explanatory-Variable Evidence | Measures or represents the variable, pattern, or construct proposed for diagnostic testing |
| Population / Eligibility Evidence | Establishes which records, entities, events, or cohorts belong to the governed analysis population |
| Completeness / Coverage Evidence | Establishes whether the intended periods, populations, entities, transactions, events, and material segments were observed sufficiently |
| Source-Authority / Provenance Evidence | Establishes authorized origin, lineage, transformations, versions, integrity, and intended-use traceability |

### 11.2 Conditional roles

| Role | Trigger |
|---|---|
| Normalization / Denominator Evidence | Required when a rate, average, share, per-unit value, index, or normalized comparison materially depends on a denominator or normalization basis |
| Identity / Join Evidence | Required when roles, sources, grains, periods, or entities must be linked or reconciled |
| Unit / Currency Evidence | Required when units or currencies materially affect comparison, aggregation, transformation, or interpretation |

### 11.3 Roles not created by default

R3 does not create default roles for temporal alignment, semantic validity, measurement validity, validation evidence, or Alternative Explanation evidence. These are dimensions, authority requirements, cross-role relationships, or R2-owned considerations.

### 11.4 Multi-role evidence

One authenticated evidence source MAY serve multiple roles only when:

- each role is explicitly mapped;
- its semantics are valid for each role;
- shared lineage genuinely covers each intended use;
- reuse does not conceal a missing independent authority; and
- proposition-specific admissibility permits the reuse.

The fact that one dataset contains several fields is not sufficient to establish multi-role fitness.

---

## 12. Dimension Applicability

### 12.1 Non-Cartesian rule

Universal evidence dimensions are proposition-level obligations. They do not create a Cartesian product in which every role independently instantiates every dimension.

R3 explicitly rejects a model equivalent to:

```text
8 roles × 12 dimensions = 96 mandatory independent checks
```

### 12.2 Applicability levels

A dimension must be resolved at the level where its material meaning exists:

| Applicability level | Use |
|---|---|
| Proposition-level | Concerns the exact proposition as a whole, such as relevance or overall representability |
| Role-level | Concerns the fitness of evidence serving one role, such as explanatory measurement validity |
| Cross-role relationship-level | Concerns compatibility between roles, such as population or temporal alignment |
| Shared authority-level | One authenticated authority legitimately satisfies multiple roles, such as shared dataset provenance |
| Method-specific level | A future governed method imposes an additional evidence prerequisite |

### 12.3 Applicability resolution

Every frozen R1 minimum evidence dimension MUST receive an explicit applicability resolution in every Resolved Required Evidence Profile. For each minimum dimension, the resolved profile must state:

- the applicable level;
- the requirement or relationship to be evaluated;
- the controlling authority;
- the failure consequence; or
- an explicit governed reason why the dimension is genuinely not applicable.

Silent omission is non-conforming. `Not applicable` cannot be used merely because evidence is unavailable or evaluation is inconvenient.

A dimension may be conditionally substantive while remaining mandatory to resolve. For example, Metric compatibility may be explicitly non-applicable when no governed Metric or Metric-derived construct materially participates; unit and currency compatibility may be explicitly non-applicable when no material unit-bearing or monetary evidence participates. Each such determination requires a governed, reviewable reason.

### 12.4 Examples

- Population alignment commonly applies across Observed Outcome and Explanatory-Variable roles rather than as duplicate checks on each field.
- Provenance may be satisfied by one authenticated canonical dataset lineage across several roles when the same lineage genuinely supports those roles and uses.
- Metric compatibility is mandatory to resolve; it becomes substantively applicable where a governed Metric or Metric-derived value participates and otherwise requires explicit governed non-applicability.
- Unit and currency compatibility is mandatory to resolve; it becomes substantively applicable where material unit-bearing or monetary evidence participates and otherwise requires explicit governed non-applicability.
- Join governance applies when roles or sources require linkage; it is not duplicated for a single already-governed canonical table with no additional join.

---

## 13. Normative Dimension Catalog

### 13.1 Frozen R1 minimum dimensions — mandatory to resolve

| Dimension | Meaning | Normal applicability level | Controlling authority or evidence | Fail-closed consequence |
|---|---|---|---|---|
| Relevance | Evidence bears directly on the exact proposition and intended material use | Proposition and role | Diagnostic Proposition, Business Question, role mapping | Irrelevant evidence cannot satisfy the requirement |
| Semantic validity | Fields, values, statuses, transformations, and relationships mean what the proposition assumes | Role or shared authority | Canonical mapping, governed definitions, transformation records | Ambiguous or invalid semantics block |
| Source authority | The source is authorized for the role and intended use | Role or shared authority | Dataset/source registration and admission policy | Unauthorized source blocks |
| Completeness | Material periods, populations, entities, records, events, and values are sufficiently covered | Proposition, role, or cross-role | Coverage evidence and materiality rule | Material unresolved incompleteness blocks |
| Temporal alignment | Evidence covers the governed time relationship required by the proposition | Cross-role or proposition | Period definitions, coverage, timezone, temporal semantics | Material mismatch or unresolved alignment blocks |
| Population alignment | Evidence roles refer to the same population or an explicitly governed relationship | Cross-role or proposition | Scope, population references, eligibility authority | Material mismatch blocks |
| Metric compatibility | Authoritative Metric definitions, exclusions, aggregation rules, populations, periods, and intended uses are compatible | Proposition, role, or cross-role | Metric Dictionary, Metric Registry, Metric/version references | Incompatibility or unresolved applicability blocks; genuinely absent Metric use requires explicit governed non-applicability |
| Unit and currency compatibility | Material units and currencies are known, governed, and comparable | Proposition, role, or cross-role | Canonical and Metric authority, unit/currency and conversion references | Unknown or incompatible material basis blocks; genuinely absent unit/currency use requires explicit governed non-applicability |
| Measurement validity | Evidence measures the intended concept under an allowed measurement classification | Role | Measurement definition, transformation/method authority | Invalid or unsupported measurement blocks |
| Missingness | Missing, unknown, excluded, zero, absent, and not-applicable conditions are measured and interpreted correctly | Role, cross-role, or proposition | Data Quality, coverage and materiality rules | Material unresolved missingness blocks |
| Provenance | Evidence is traceable through source, transformation, use, and applicable execution/validation | Shared authority or role | IDs, references, versions, fingerprints, retained artifacts | Insufficient traceability blocks |
| Validation status | All applicable deterministic checks for the evidence type and use have passed | Shared authority, role, or stage | Data Quality, method prerequisite authority, ValidationRecord/ValidatedResult | Failed or unresolved required validation blocks |

All twelve frozen R1 minimum dimensions are mandatory to resolve. Some are conditionally substantive, but none is optional to resolve. Explicit governed non-applicability is permitted where materially correct; silent omission is not. Mandatory resolution does not mean duplicate per-role checks.

### 13.2 Additional conditional dimensions beyond the frozen R1 minimum

| Dimension | Trigger | Required resolution |
|---|---|---|
| Granularity | Grain affects meaning, aggregation, identity, linkage, or admissibility | Required grain, permitted transformation, grain-loss behavior |
| Join requirements | Multiple sources, grains, identities, or temporal records must be linked | Key authority, cardinality, temporal validity, unmatched records, join loss |
| Normalization / denominator | A rate, average, share, index, or per-unit construct is material | Authoritative denominator, population, period, unit, zero/undefined behavior |
| External admission | A material dependency is `EXTERNAL`, or an `EITHER` dependency uses an external source | Separate governed source admission and intended-use authority |
| Method-specific prerequisite | A future governed method requires additional evidence conditions | Exact method/version reference and prerequisite resolution |

When a trigger is present, the additional dimension is required. These additions do not replace or reduce the mandatory applicability resolution of any frozen R1 minimum dimension.

---

## 14. Source Dependency Classification

Every material dependency must be classified with semantics equivalent to:

| Class | Meaning |
|---|---|
| `INTERNAL` | Expected from the current governed evidence package or an internal governed source class |
| `EXTERNAL` | Requires evidence outside the current governed package and separate governed admission |
| `EITHER` | May be satisfied by an authorized internal source or separately governed admitted external source |

Rules:

1. Classification belongs to the resolved requirement, not merely the dataset label.
2. An unmet material `INTERNAL` dependency is an internal evidence gap under existing sufficiency/admissibility authority.
3. An unmet material `EXTERNAL` dependency is preserved for R2's External Evidence Required derivation when no earlier blocker controls.
4. `EITHER` does not authorize web search, automatic acquisition, arbitrary source substitution, or relaxed admission.
5. Finding external information is not governed external evidence admission.
6. A change of dependency class is material and requires a new profile version.

---

## 15. Granularity Governance

Where grain affects material meaning, a resolved profile must identify:

- required grain;
- the evidence roles affected;
- permissible aggregation or transformation;
- transformation authority and lineage;
- whether finer grain may validly satisfy the role;
- whether aggregation changes proposition meaning;
- identity retained or lost through transformation; and
- grain-loss blockers.

Potential grains include order-line, order, product, category, customer/cohort, period, event, snapshot, and external observation. This list does not expand the canonical dataset or authorize new product capabilities.

A coarser dataset does not satisfy a finer-grain requirement merely because it includes similarly named fields. A finer-grain dataset does not automatically satisfy the requirement if the needed identity, completeness, or transformation authority is absent.

---

## 16. Identity and Join Governance

When evidence sources or grains must be linked, the resolved profile must govern:

- authoritative entity identity;
- key semantics and source authority;
- expected cardinality;
- duplicate amplification risk;
- temporal validity of the relationship;
- cross-period identity consistency;
- unmatched records;
- material join loss; and
- mapping/transformation provenance.

Binding rules:

```text
same column name != same identity authority
same displayed label != same entity
similar values != duplicate proof
```

An unresolved many-to-many relationship fails closed unless explicit governed semantics permit it. R3 defines no join algorithm and no universal join-loss threshold. If materiality depends on a threshold or sensitivity rule that is not frozen, the profile or future governed method must provide it; otherwise eligibility remains unresolved.

---

## 17. Completeness and Coverage

A resolved profile must distinguish, where material:

- period coverage;
- population coverage;
- entity coverage;
- field and value completeness;
- transaction or event completeness;
- material segment coverage;
- known exclusions; and
- unknown exclusions.

```text
some relevant records exist != sufficient coverage
```

The applicable materiality rule must be governed and reviewable. R3 MUST NOT invent a universal numeric threshold. A claim-sensitive rule MAY be used where frozen authority supports it, such as whether missing or unclassified evidence could change a claimed ranking or completeness conclusion.

If no applicable materiality rule exists, coverage eligibility is unresolved and the affected test is blocked. Unknown coverage cannot be converted into zero activity or proven absence.

---

## 18. Temporal Alignment

The resolved profile must define, where applicable:

- outcome period;
- explanatory-evidence period;
- comparison basis;
- timezone and date-boundary convention;
- comparable-window requirements;
- event-time and snapshot-time relationship;
- missing-period behavior;
- semantic stability across time; and
- a method-owned lag prerequisite reference, if required.

No period may be silently extended, shortened, shifted, imputed, or normalized. Current canonical comparable-period rules remain authoritative where they apply. R3 defines no lag model, seasonal adjustment, or time-series method.

---

## 19. Population Alignment

The resolved profile must define:

- outcome population;
- each evidence-role population;
- the governed relationship between populations;
- eligibility rules;
- cancellation and refund treatment;
- applicable channel, store, product, customer, or other filters;
- population authority, version, and fingerprint where available; and
- permitted narrowing.

Governed population relationships may include same population, explicit subset, explicit superset, cohort linkage, or another specifically governed relationship. The label alone is insufficient; the material relationship and its validity for the proposition must be stated.

Unresolved material population mismatch blocks the affected test. A disclaimer cannot repair it.

---

## 20. Measurement Classification

Every material outcome or explanatory measurement must use one of the following specification-level meanings:

| Classification | Governance meaning | Eligibility consequence |
|---|---|---|
| Direct Measurement | Directly measures the intended governed concept | May satisfy measurement validity only if all other applicable dimensions pass |
| Governed Transformed Measurement | Derived through an authorized transformation with full lineage | Eligible only within the governed transformation meaning and intended use |
| Governed Proxy | Indirect evidence explicitly permitted for a bounded proposition and use | Eligible only within its defined maximum Claim boundary and method/admission constraints |
| Inferred Construct | Requires future governed method and admission before material use | Not eligible until that authority exists and applies |
| Unsupported Proxy | Does not validly measure the required concept | Cannot satisfy the requirement |

These labels define semantics, not runtime enum names.

Measurement classification is role- and intended-use-specific. A measure may be direct for one proposition and an unsupported proxy for another.

Explicitly:

```text
lower AOV != direct evidence of discounting
```

---

## 21. Metric, Unit, Currency, and Denominator Compatibility

### 21.1 Metric compatibility

Where a Metric participates, the profile must bind or reference:

- Metric ID and definition version;
- governed definition and intended use;
- aggregation and additivity;
- exclusions and eligibility rules;
- denominator, if applicable;
- population and period basis;
- undefined conditions; and
- applicable validation references.

The frozen Metric Dictionary and Metric Registry remain authoritative. R3 does not restate or redefine formulas.

### 21.2 Unit compatibility

Where units are material, the profile must establish their meaning, comparability, and any authorized transformation. Unknown or incompatible material units block eligibility.

### 21.3 Currency compatibility

Where monetary evidence is material, the profile must establish the currency and common governed basis. Mixed unnormalized or unknown currency blocks eligibility. R3 does not authorize FX lookup or conversion.

### 21.4 Normalization and denominator

Where a rate, average, share, index, or per-unit comparison is material, the authoritative denominator must match the governed population, period, exclusions, unit, and intended use. Missing or incompatible denominator authority blocks eligibility; zero or undefined behavior follows the applicable governed Metric or future method authority.

Equal numeric values under different Metrics, versions, units, currencies, populations, periods, or denominators do not establish equivalence.

---

## 22. Missingness

The resolved profile must distinguish at least:

- field absent;
- null or unknown value;
- unobserved population;
- missing period;
- known exclusion;
- structural non-applicability;
- genuine zero; and
- proven absence.

For each material missingness condition, the profile must define or bind:

- how it is observed or measured;
- its semantic interpretation;
- the applicable materiality rule;
- blocking or qualifying consequence; and
- affected proposition scope.

R3 defines no universal missingness percentage. Missing is not zero, and uncertain absence is not proven absence.

---

## 23. Provenance

Required Evidence must remain traceable through semantics equivalent to:

```text
source
→ dataset identity
→ canonicalization / transformation
→ scope / population / period
→ evidence role
→ execution where applicable
→ validation where applicable
→ admissibility
→ proposition / intended use
```

R3 reuses existing artifact references, fingerprints, record IDs, policy and definition versions, and retained-run patterns. It does not require a graph database or new evidence graph.

Shared provenance MAY satisfy multiple roles only when its authenticated lineage genuinely covers each role and use. Conversational memory, equivalent values, copied prose, or a dynamic “latest” record cannot substitute for authority.

---

## 24. Validation Requirements

### 24.1 Pre-execution evidence validation

Pre-execution validation determines whether available evidence satisfies applicable schema, semantic, coverage, identity, join, period, population, Metric, unit, currency, missingness, and provenance requirements.

Existing canonicalization, Data Quality, sufficiency, and admissibility authorities own their actual judgments.

### 24.2 Method-prerequisite validation

Future governed method authority may require additional validations. R3 provides only requirement/reference semantics. An undefined or failed material method prerequisite blocks eligibility.

### 24.3 Post-execution result validation

Existing `ValidationRecord` and `ValidatedResult` authorities govern executed-result validation. Test eligibility before execution does not imply post-execution validation success.

### 24.4 No substitution

Qualification, statistical plausibility, LLM judgment, or a successful unrelated validation cannot repair a failed required validation.

---

## 25. Data Sufficiency Boundary

The Required Evidence Profile defines what must be checked. Existing `DataSufficiencyResult` or its canonical successor remains authoritative for applicable availability and structural sufficiency outcomes.

Data Sufficiency evaluates or references, as applicable:

- whether required data exists;
- request, dataset, canonicalization, and schema linkage;
- required period coverage and basic comparability;
- governed population and eligible records;
- grain and canonical identity;
- missingness and basic completeness;
- currency basis;
- Data Quality blockers;
- clarification requirements; and
- per-chain execution eligibility.

R3 MUST NOT duplicate those outcomes into a second sufficiency status. A resolved profile supplies proposition-specific requirements and references; the sufficiency authority supplies the actual governed evaluation record and reasons.

A declaration that Available Evidence satisfies a requirement is not proof. The applicable authority must establish satisfaction.

---

## 26. Evidence Admissibility Boundary

R3 defines proposition-specific admission requirements. Existing Evidence Admissibility authority or its canonical successor remains responsible for actual admission judgment.

The following intended-use boundary is mandatory:

```text
Descriptive AdmissibleEvidence != diagnostic-input admissibility
```

A validated descriptive result together with descriptive admissibility MAY provide authenticated candidate evidence for a future diagnostic use. It does not automatically become admissible for that diagnostic use:

```text
validated descriptive result
+ descriptive admissibility
→ authenticated candidate evidence for diagnostic use

NOT

validated descriptive result
+ descriptive admissibility
→ diagnostic-input admissibility
```

Future diagnostic admission must be capable of binding or evaluating:

- exact proposition;
- diagnostic evidence role;
- intended diagnostic use;
- source authority;
- semantic and measurement validity;
- scope, population, and period;
- profile and other material versions and fingerprints;
- Required Evidence references; and
- applicable validation authority.

Every applicable Required Evidence condition must still be satisfied for the diagnostic proposition and intended use. R3 does not create a new physical evidence contract, admissibility enum, engine, or positive diagnostic policy, and it does not change current descriptive Evidence Admissibility behavior.

Evidence that is present but inadmissible must remain distinguishable from absent evidence through an authoritative admission record and specific reason.

---

## 27. Blocking, Qualification, and Narrowing

### 27.1 Blocking conditions

The affected test is blocked when any material condition is undefined, missing, failed, invalid, ambiguous, inadmissible, incompatible, or unresolved, including:

- Required Evidence definition;
- semantics;
- material evidence availability;
- source authority;
- population or period alignment;
- Metric, unit, currency, grain, identity, join, or denominator compatibility;
- measurement validity;
- material completeness, coverage, or missingness;
- provenance;
- required validation; or
- governed admission of required external evidence.

### 27.2 Qualification

Qualification is permitted only when:

- the core evidence chain remains independently complete and valid;
- no required evidence failure is waived;
- no failed validation is repaired;
- the supported material meaning is explicit;
- any material narrowing is represented in the exact proposition and binding; and
- rendering attaches the qualification to the affected object.

### 27.3 Qualification is not a waiver

The following is prohibited:

```text
broad unsupported proposition
+ cautionary prose
→ treated as eligible
```

The conforming sequence is:

```text
evidence supports only narrower meaning
→ create new exact R2 Diagnostic Proposition
→ create narrower Exact Proposition Binding
→ resolve a new Required Evidence Profile for that proposition
→ create new R2 Diagnostic Evaluation bound to that proposition and profile
→ communicate any remaining non-blocking qualification
```

R3 defines and supplies the narrowed evidence requirements, binding, blockers, and profile version. R2 owns the new proposition identity, Diagnostic Evaluation identity, finalization, immutability, and historical evaluation authority.

### 27.4 Independent chains

An independently complete narrower or separate chain MAY proceed only when its scope genuinely excludes the defect and its own exact binding is complete. It does not inherit authority from the failed chain.

---

## 28. Deterministic Requirement Evaluation

### 28.1 Requirement-level meanings

Future systems must preserve meanings equivalent to:

Every frozen R1 minimum dimension must receive one of these governed outcomes at its applicable level. A dimension that is not materially substantive still requires `Explicitly Not Applicable` or equivalent meaning with a governed reason.

| Meaning | Definition |
|---|---|
| Satisfied | Applicable requirement is proven by the required authentic authority |
| Failed | Evidence or authority affirmatively violates the requirement |
| Missing | Required evidence or authority is absent |
| Unresolved | Material ambiguity, undefined rule, or incomplete determination prevents judgment |
| Explicitly Not Applicable | The resolved profile gives a governed reason the dimension does not apply |
| External Dependency Unmet | Material external requirement lacks governed admitted evidence |
| Present but Inadmissible | Evidence exists but fails admission for the exact role, proposition, or use |

These are semantic outcomes, not approved runtime enum members.

### 28.2 Required judgment content

Every material requirement judgment must preserve:

- requirement and applicable dimension;
- outcome;
- reason;
- evidence and authority references;
- role or relationship affected;
- scope, population, and period;
- profile, definition, policy, and other material versions; and
- blocking or qualifying consequence.

These requirement judgments are R3 inputs to the R2 evaluation path. They do not constitute, create, or finalize a Diagnostic Evaluation.

### 28.3 Evidence mapping

Evidence mapping must identify which authentic evidence item is proposed for which requirement and role. Mapping by identifier or declaration is necessary for traceability but not sufficient for satisfaction. The evidence must pass every applicable qualification condition.

### 28.4 Controlling blocker

The first material blocker under Section 29 controls test eligibility. Later outcomes may be retained for audit but cannot repair or displace it.

---

## 29. Deterministic Pre-Test Evaluation Order

Evaluators must apply this order:

1. **Exact proposition representability.** Materially ambiguous or unrepresentable meaning blocks.
2. **Profile identity and version resolution.** Missing, conflicting, or mismatched profile authority blocks.
3. **Applicable evidence roles.** Required roles and role relationships must be resolved.
4. **Dimension applicability.** All twelve frozen R1 minimum dimensions must receive explicit applicability resolution, and every triggered additional conditional dimension must be resolved; silent omissions block. A materially non-applicable minimum dimension requires a governed reason.
5. **Dependency source classification.** Material dependencies must be classified.
6. **Available Evidence mapping.** Candidate evidence must be authentically mapped to requirements and roles.
7. **Data Sufficiency.** Existing authority evaluates applicable availability and structural conditions.
8. **Evidence fitness.** Semantic, source, alignment, measurement, completeness, missingness, provenance, and conditional compatibility requirements are evaluated by their owning authorities.
9. **Evidence Admissibility.** Existing admission authority evaluates exact proposition, role, and intended-use fitness. Descriptive admissibility may authenticate candidate evidence but is not inherited as diagnostic-input admissibility.
10. **Blocking versus qualification.** Material defects and valid narrower chains are distinguished without waiver.
11. **Controlling blocker.** The earliest blocker is retained with reason and authority.
12. **Test eligibility.** Eligibility is true only when every applicable pre-test blocking requirement and required method prerequisite has passed.

If an external dependency is unmet after proposition/profile definition, its source classification must be preserved so R2 can derive External Evidence Required rather than ordinary internal Missing Evidence, subject to frozen R1/R2 precedence.

---

## 30. Test Eligibility

### 30.1 Eligibility predicate

A future diagnostic test is eligible only when all of the following are true for the exact proposition and resolved profile:

- proposition is representable;
- profile and version are defined and materially matched;
- all required roles, all twelve frozen R1 minimum dimension applicability decisions, and all triggered additional conditional dimensions are resolved;
- every material internal dependency is satisfied;
- every material external dependency used by the test is governed and admitted;
- Data Sufficiency authorizes the affected execution chain;
- evidence semantics, source authority, measurement, alignment, completeness, missingness, and provenance are valid;
- all substantively applicable Metric and unit/currency conditions, plus all triggered grain, join, denominator, and external-admission requirements, pass;
- all required pre-execution validations pass;
- applicable method prerequisites and references are defined and satisfied; and
- no blocking or unresolved material defect remains.

### 30.2 Eligibility boundaries

```text
test eligible != test executed
test executed != result validated
result validated != proposition supported
proposition supported != Claim authorized
```

R3 determines only evidence-based eligibility. R4 will later define method behavior. R2 and existing authorities preserve execution, validation, analytical outcome, Alternative Explanation Check, and Claim-permission boundaries.

---

## 31. Product Mix Family Profile — Full Example

This example demonstrates R3 governance. It does not approve a product-mix method, formula, threshold, support criterion, or diagnostic Claim.

### 31.1 Bounded family meaning

The Product Mix family concerns a proposed diagnostic pattern involving the composition of governed product identities within an eligible merchandise-sales population across governed periods and its relationship to an observed outcome.

It does not mean that product mix caused, drove, or contributed to the outcome. Mechanical product contribution under the frozen Metric Dictionary is not automatically diagnostic product-mix support.

### 31.2 Family Profile Sheet

| Evidence role | Required concept | Semantic condition | Source class | Grain / identity | Population / period | Coverage / missingness | Validation authority | Blocking condition | Method dependency |
|---|---|---|---|---|---|---|---|---|---|
| Observed Outcome | Governed outcome such as Revenue Change | Exact Metric definition/version; no diagnostic meaning inferred from value alone | Internal | Governed target Metric grain/result | Exact scope and comparison periods | Complete periods and eligible population | Existing descriptive Metric execution/validation authority may authenticate candidate input; diagnostic proposition/intended-use admission remains separately required | Missing, invalid, unvalidated, mismatched, or not admitted for diagnostic use | Future method may reference outcome shape, not redefine Metric |
| Explanatory Variable | Governed product composition evidence | Stable product identity; governed value/quantity semantics; no name-based identity substitution | Internal by default | Canonical order-line evidence grouped through authoritative `product_id`; any transformation traceable | Same or explicitly governed related population and periods | Material product/entity/value coverage established | Canonical/Data Quality plus future method prerequisites | Unstable identity, ambiguous value semantics, or material uncovered products | Exact composition representation and support criterion remain method-owned |
| Population / Eligibility | Eligible merchandise lines and filters | Same eligibility, cancellation/refund treatment, date basis, and scope across roles | Internal | Order-line population authority | Same governed population or explicit valid relationship | Unknown exclusions block | Existing population/sufficiency authority | Population mismatch or ambiguous eligibility | None beyond future method additions |
| Completeness / Coverage | Period, population, product, and transaction coverage | Absence distinguished from unknown; entry/exit requires complete period evidence | Internal or Either only if separately governed | Coverage may be dataset/period/entity level | Both governed periods and exact scope | Material unknown product or period coverage blocks | Coverage and sufficiency authority | Incomplete or undefined materiality rule | Future method may add sensitivity rule |
| Source Authority / Provenance | Authenticated lineage for all above roles | Source, canonicalization, transformations, versions, and intended diagnostic use traceable | Internal by default | Shared canonical lineage may cover several roles | Exact dataset/scope/population/period | Missing lineage cannot be qualified away | Existing artifact/fingerprint/retention authority plus proposition- and intended-use-specific diagnostic admission | Insufficient provenance or diagnostic-use admission | Method reference retained if used |
| Identity / Join | Product and any cross-source mapping identity | `product_id` meaning stable; key/cardinality/temporal validity governed | Internal or Either depending source | Order-line-to-product; no unresolved many-to-many | Valid across both periods | Unmatched/material join loss governed | Canonical identity/Data Quality or future admitted mapping authority | Unresolved identity or material join loss | Only if future method uses additional source |
| Unit / Currency | Comparable monetary/unit basis where material | One governed currency; quantity is positive whole-number line semantics; optional unit price has no authority until declared | Internal | Order-line | Same basis across periods/population | Unknown unit/currency blocks | Canonical and Metric authority | Mixed currency, invalid quantity, ambiguous optional price semantics | Future method must state if unit-price evidence is actually required |

### 31.3 Exact Proposition Binding Sheet

Illustrative proposition:

> Within governed scope S and the common eligible merchandise population, between Baseline Period B and Comparison Period C, the distribution of governed product identities is proposed for a future diagnostic test as a pattern associated with the observed governed Revenue Change.

This is a hypothesis for eligibility illustration, not a Finding.

| Binding element | Resolved requirement |
|---|---|
| Proposition | Exact bounded wording above; no causal or “contributed to” meaning |
| Intended claim class/use | Future bounded diagnostic test only; no current positive Claim permission |
| Outcome | Governed Revenue Change reference/version for S, B, and C; existing validated descriptive authority may serve as authenticated candidate evidence, but descriptive admissibility does not establish diagnostic-input admissibility |
| Scope | Explicit filters defining S; no silent broadening |
| Population | Same governed eligible order-line population across outcome and explanatory evidence unless an explicitly valid relationship is defined |
| Periods | Explicit B and C with canonical comparability, coverage, timezone, and stable semantics |
| Explanatory evidence | Stable `product_id`, governed `line_revenue` value semantics, valid quantity and eligibility semantics; product names display-only |
| Grain | Canonical order-line as current source authority; any aggregation is future method-owned and traceable |
| Identity | `product_id` authoritative across periods; entry/exit distinguished from incomplete coverage; no name fallback |
| Join | No additional join if all roles use the same canonical lineage; otherwise the exact mapping, cardinality, unmatched records, and temporal validity become required |
| Completeness | Complete periods, eligible transactions, product identity, and material entity/value coverage; no invented universal threshold |
| Missingness | Missing product/value/date/quantity/currency handled under canonical blocking rules; genuine absence requires complete coverage |
| Measurement | Product identity and governed line value are direct for their stated concepts; optional `unit_price` is not evidence of a price concept until semantics are governed |
| Metric compatibility | Frozen Revenue/Revenue Change definitions and versions; no redefinition |
| Unit/currency | One governed currency; quantity semantics preserved; any price/unit transformation requires authority |
| Provenance | Dataset, canonicalization, scope/population/period, execution/validation where applicable, descriptive authority, diagnostic intended-use admission, and proposition use traceable |
| Validation | Applicable canonical/Data Quality, sufficiency, Metric/result, proposition- and intended-use-specific diagnostic admission, and future method-prerequisite validations |
| Blockers | Any unresolved semantic, identity, coverage, alignment, currency, provenance, admission, or method-prerequisite defect |
| Qualification/narrowing | A product subset may proceed only through a new exact R2 Diagnostic Proposition, narrower binding, new resolved profile, and new R2 Diagnostic Evaluation; prose cannot preserve a broader proposition |
| Method reference | Required before actual test eligibility; formula and support criterion remain outside R3 |
| Profile version | Exact profile version must be retained by the future Diagnostic Evaluation |

### 31.4 Dimension applicability illustration

- Relevance is proposition-level and role-mapping-specific.
- Product identity semantics and measurement validity are role-level.
- Population and temporal alignment are cross-role.
- One authenticated canonical lineage may satisfy shared provenance for several roles.
- Metric compatibility applies to outcome/value roles using governed Metrics.
- Currency applies to monetary roles, not independently to the identity role.
- Join requirements are explicitly not applicable when no join beyond the authenticated canonical dataset occurs; the reason must be recorded.

### 31.5 Non-authorization

This example does not determine whether product mix changed, whether any criterion is met, whether the proposition is supported, or whether a diagnostic Claim may be rendered.

Existing descriptive validation or admissibility in this example authenticates only candidate input authority. It does not satisfy diagnostic-input admissibility without evaluation of the exact proposition, diagnostic role, intended use, scope, population, period, measurement, source, profile/version, validation authority, and all applicable Required Evidence conditions.

---

## 32. Discounting Semantic-Invalidity Counterexample

A source field named `discount` is Available Evidence only. It does not establish Required Evidence satisfaction.

Before it can satisfy a discount-related explanatory role, governed authority must establish, as applicable:

- percentage versus absolute amount;
- the baseline, gross, or list price referenced;
- line versus order grain;
- whether the value is allocated across multiple items;
- cancellation and refund treatment;
- eligibility population;
- period consistency and semantic stability;
- currency and unit;
- missingness meaning;
- source authority and transformation lineage; and
- whether it directly measures discounting or is a proxy.

Current `line_revenue` is authoritative post-discount eligible merchandise value, but it does not by itself reveal the amount or rate of discount. Current optional `unit_price` has no discount authority until its pre/post-discount semantic and validation relationship are declared.

Likewise:

```text
lower AOV != direct evidence of discounting
```

Without the required semantics, the evidence is ambiguous or an unsupported proxy and the affected diagnostic test is blocked. R3 does not create a discount model or capability.

---

## 33. Refund-Impact Boundary Example

Refund impact may require refund-event evidence with governed event identity, event time, order/line linkage, amount/currency, partial-versus-full treatment, eligibility effects, completeness, and provenance.

The current canonical dataset is an order-line model, not a refund-event ledger. It supports governed final eligible `line_revenue` and the existing cancellation/full-refund boundary; it does not authorize reconstruction of unsupported partial refunds or refund events.

Therefore, where an exact refund-impact proposition requires a refund-event ledger or equivalent evidence not present in current authority:

```text
required event-grain evidence unavailable or outside current governed authority
→ Required Evidence unresolved/missing or external as correctly classified
→ diagnostic test blocked or deferred
```

CommerceLens MUST NOT invent negative lines, infer event timing, reconstruct refund amounts, or treat current post-discount Revenue as a complete refund ledger. This example does not add refund analysis to MVP scope.

---

## 34. Human-Reviewable Specification Views

### 34.1 Normative Dimension Catalog

Section 13 is the normative catalog. It defines each dimension, applicability rule, authority expectation, and fail-closed consequence.

### 34.2 Family Profile Sheet

Section 31.2 demonstrates the required review form for a bounded family:

| Evidence role | Required concept | Semantic condition | Source class | Grain / identity | Population / period | Coverage / missingness | Validation authority | Blocking condition | Method dependency |
|---|---|---|---|---|---|---|---|---|---|

This is a specification view, not an implementation schema.

### 34.3 Exact Proposition Binding Sheet

Section 31.3 demonstrates how a family template becomes proposition-specific Required Evidence authority. It binds material identity, roles, applicable dimensions, source dependencies, blockers, narrowing, method references, and profile version; it does not become R2 Diagnostic Evaluation authority.

### 34.4 Cross-Family Review Matrix

The following matrix is a non-authoritative omission-detection tool:

| Review concern | Product Mix | Discounting | Refund Impact |
|---|---|---|---|
| Primary example use | Full family/profile and exact binding | Semantic-invalidity counterexample | Grain/canonical-scope boundary |
| Observed outcome | Governed Metric outcome | Would require exact governed outcome | Would require exact governed outcome |
| Explanatory evidence | Product composition with governed identity/value semantics | Governed direct discount measure or admitted bounded proxy | Governed refund event/ledger evidence |
| Material grain | Order-line/product relationship | Line or order must be explicitly governed | Refund event plus order/line linkage |
| Identity/join | Stable product identity; joins conditional | Price/discount allocation identity may be required | Event-to-order/line identity required |
| Primary semantic trap | Product name or incomplete product set | Field named `discount` without definition | Final Revenue treated as event ledger |
| Measurement boundary | Direct product/value concepts; method still future | Lower AOV is not direct discount evidence | Post-discount Revenue is not complete refund-event evidence |
| Current scope consequence | Evidence model can be specified; method remains future | No full capability authorized | Required event authority absent; blocked/deferred |

This matrix MUST NOT be used as Required Evidence authority. Deferred families—quantity/volume shift, AOV shift, category mix, channel mix, stockout, and customer repeat/cohort—remain outside substantive R3 specification.

---

## 35. R2 Integration

R3 supplies or makes traceable to R2:

- Required Evidence Profile identity and version;
- exact proposition binding;
- requirement-resolution judgments;
- dependency source classification;
- sufficiency authority references;
- admissibility authority references;
- admitted evidence references;
- specific blocking reasons;
- method and validation prerequisite references; and
- qualification and narrowing constraints.

These are evidence-requirement authorities and inputs only. They do not create Diagnostic Proposition or Diagnostic Evaluation authority. When material narrowing is required, R3 supplies the narrower binding and resolved profile for a new exact R2 Diagnostic Proposition; R2 creates and owns the corresponding new Diagnostic Evaluation and its history.

R2 retains authority for:

- Diagnostic Proposition and Diagnostic Evaluation;
- evaluation identity, finalization, immutability, and history;
- Evidence Conflict Assessment;
- Analytical Outcome;
- Alternative Explanation Check;
- `ClaimCandidate` and `ClaimDecision`; and
- Derived Material Disposition.

R3 creates no R2 state or evaluation object. R2 binds R3 requirement authority rather than copying it into a competing source of truth. Descriptive `AdmissibleEvidence` may be referenced as authenticated candidate input but must not be treated as inherited diagnostic-input admission.

---

## 36. Alternative Explanation Evidence Boundary

R3 does not create an Alternative Explanation input role. R1/R2 retain the mandatory Alternative Explanation Check and its authority.

A resolved profile MAY identify **material competing evidence considerations** when known competing interpretations make particular proposition-specific evidence material. Such considerations:

- do not generate alternatives;
- do not create an alternative ontology;
- do not treat the absence of imagined alternatives as a fabricated evidence requirement;
- do not decide the R2 Alternative Explanation Check; and
- do not silently convert conflicting admitted evidence into ordinary missing evidence.

The producer and physical representation of conflict-related inputs remain a later implementation-allocation question.

---

## 37. R4 Handoff Boundary

R3 hands future R4 work:

- resolved profile identity/version;
- exact proposition and material use;
- required evidence roles and semantics;
- scope, populations, periods, and comparison basis;
- grain, identity, and join constraints;
- Metric, unit, currency, and denominator constraints;
- completeness, coverage, and missingness obligations;
- measurement classifications;
- provenance and validation categories;
- eligibility blockers; and
- method-specific prerequisite slots.

R3 does not hand off or define:

- decomposition formula;
- estimator;
- weighting;
- interaction allocation;
- thresholds;
- effect sizes;
- support criteria;
- contradiction criteria; or
- execution logic.

R4 must not infer that R3 eligibility establishes proposition support.

---

## 38. Future R5 Fixture Requirements

R5 should later create local deterministic cases covering at least:

1. field present but semantically invalid;
2. correct field and wrong population;
3. correct field and wrong period;
4. correct value and wrong Metric version;
5. mixed currency;
6. unknown currency;
7. wrong grain;
8. invalid join cardinality;
9. material unmatched join records;
10. incomplete population coverage;
11. unknown population coverage;
12. Direct Measurement;
13. Governed Transformed Measurement;
14. Governed Proxy within its bounded use;
15. Inferred Construct without required future authority;
16. Unsupported Proxy;
17. external dependency not admitted;
18. evidence available but inadmissible;
19. missing provenance;
20. failed required validation;
21. non-material bounded gap with a valid narrower proposition;
22. invalid qualification used to repair a blocking failure;
23. fully aligned and admissible evidence;
24. material profile-version change requiring a new evaluation; and
25. family template used without Exact Proposition Binding.

R3 defines case obligations only. It creates no fixture, expected runtime enum, test, or benchmark score.

---

## 39. Fail-Closed Invariants

1. Missing or unresolved Required Evidence Profile blocks diagnostic test eligibility.
2. Profile-version mismatch blocks the affected evaluation.
3. Family template without Exact Proposition Binding has no final authority.
4. Field presence alone cannot satisfy Required Evidence.
5. Same field name does not establish the same semantics.
6. Same entity-key text does not establish identity authority.
7. Every frozen R1 minimum evidence dimension must receive explicit applicability resolution; Metric compatibility and unit/currency compatibility cannot silently disappear.
8. A materially non-applicable frozen R1 minimum dimension requires an explicit governed, reviewable reason.
9. Evidence cannot be reused across roles without explicit compatibility and admission.
10. Internal missing evidence remains distinct from an external dependency.
11. Present-but-inadmissible evidence remains distinct from absent evidence.
12. Unresolved join cardinality, duplication, or material join loss blocks the affected test.
13. Unresolved material population mismatch blocks.
14. Unresolved material period mismatch blocks.
15. Unsupported Proxy blocks.
16. Unknown or incompatible material unit or currency blocks.
17. Material unresolved missingness or coverage blocks.
18. Required validation failure blocks.
19. Qualification cannot waive a Required Evidence condition.
20. Material narrowing must route through a new exact R2 Diagnostic Proposition, narrower Exact Proposition Binding, new Resolved Required Evidence Profile, and new R2 Diagnostic Evaluation.
21. A profile default cannot weaken a stricter exact requirement.
22. A method reference cannot waive frozen evidence dimensions.
23. A profile-version change cannot rewrite finalized R2 evaluation history.
24. LLM judgment, confidence, user insistence, or disclaimer cannot waive Required Evidence.
25. Failure in one evidence chain must not invalidate unrelated independently complete chains.
26. A declaration that evidence satisfies a requirement is not proof of satisfaction.
27. Equal values, similar prose, or shared family membership cannot substitute authenticated authority.
28. Unknown coverage cannot be treated as zero activity or proven absence.
29. A successful descriptive result does not by itself authorize diagnostic test eligibility.
30. Test eligibility cannot be represented as proposition support or Claim permission.
31. Descriptive `AdmissibleEvidence` does not automatically establish diagnostic-input admissibility.
32. Diagnostic-input admission must be proposition-, role-, intended-use-, scope-, population-, period-, measurement-, source-, profile/version-, validation-, and Required-Evidence-specific.
33. Exact Proposition Binding and Required Evidence Profile remain requirement authority only; they do not create Diagnostic Evaluation authority.
34. R2 remains the authority for Diagnostic Proposition identity, Diagnostic Evaluation identity, finalization, immutability, and history.

Any unresolved invariant violation produces a non-eligible fail-closed outcome for the affected test chain.

---

## 40. Risks and Mitigations

| Risk | Governance mitigation | Residual limitation |
|---|---|---|
| R3 degrades into a column checklist | Roles, dimensions, exact binding, and authority requirements; explicit field-presence prohibition | Future physical contracts could still over-compress semantics |
| Universal dimensions become a Cartesian product | Explicit applicability levels and shared/cross-role resolution | Poor authoring may still duplicate checks unnecessarily |
| Family ontology expands without bound | Families are bounded reusable templates and non-authoritative | Future governance must resist speculative family creation |
| R3 defines R4 methods indirectly | Method-owned slots and references only; formulas/criteria prohibited | Some evidence prerequisites cannot be finalized until a method exists |
| Data Sufficiency is duplicated | Profile defines requirements; existing authority records actual sufficiency | Future allocation must map new semantics cleanly |
| Evidence Admissibility is duplicated | R3 defines admission conditions; existing authority owns judgment | Current implementation is descriptive/result-focused only |
| Qualification becomes a waiver | Mandatory structural narrowing and exact re-binding | Renderers must later preserve the narrowed meaning |
| Proxy evidence is overstated | Five-class measurement model and maximum bounded use | Future methods must define admissible proxy conditions |
| Arbitrary thresholds are introduced | Frozen rule, claim-sensitive rule, or future method authority required | Some cases remain blocked until such authority exists |
| Product Mix overfits R3 | Discount semantic counterexample and refund boundary test generality | Only one full family is intentionally specified |
| MVP scope expands | Examples expressly non-authorizing; canonical model unchanged | Later work requires separate approval |
| Evidence conditions are too abstract | Each judgment requires outcome, reason, authority, context, version, and consequence | Physical representation remains deferred |

---

## 41. Open Implementation-Allocation Questions

No unresolved semantic question blocks R3 completion. The following matters are intentionally deferred and do not reopen the approved architecture.

### 41.1 Physical contract placement

**Question:** Which future physical contract or contracts should represent family templates, exact bindings, resolved profiles, and requirement judgments?

**Why it matters:** The current `EvidenceRequirement` is intentionally narrow, while duplicating authority across request, sufficiency, and diagnostic contracts would create conflicting sources of truth.

**Downstream milestone:** A separately approved implementation-planning milestone after method governance is sufficiently defined.

### 41.2 Profile authoring and approval authority

**Question:** Which component may propose a profile, and which deterministic or human governance process approves it for material use?

**Why it matters:** The Skill may propose evidence requirements, but LLM proposal cannot become authority by self-approval.

**Downstream milestone:** Future governance/implementation allocation; not R4 formula design itself.

### 41.3 Explicit non-applicability representation

**Question:** What minimum physical form records `Explicitly Not Applicable`, its reason, authority, and reviewer trace?

**Why it matters:** Silent omission is prohibited, but R3 does not prescribe a runtime enum or schema.

**Downstream milestone:** Future contract design and R5 conformance fixtures.

### 41.4 Additive layer mechanics

**Question:** How should a future physical representation merge global, family, exact, and method requirements while preventing weakening overrides?

**Why it matters:** Deterministic resolution requires conflict detection and version binding without copying all authority into every profile.

**Downstream milestone:** Future contract/evaluator implementation planning.

### 41.5 Evidence-conflict-related inputs

**Question:** Which future component produces requirement inputs relevant to R2 Evidence Conflict Assessment?

**Why it matters:** R3 may identify material competing evidence considerations, but R2 owns conflict assessment and no silent evidence selection is permitted.

**Downstream milestone:** Future R2 implementation allocation and R5 cases.

### 41.6 Source-authority policy integration

**Question:** How will future internal source classes and separately governed external-admission policy be referenced physically?

**Why it matters:** `INTERNAL`, `EXTERNAL`, and `EITHER` require deterministic policy references; source location alone does not establish authority.

**Downstream milestone:** Future evidence-admission governance, not automatic acquisition.

### 41.7 Diagnostic input evidence versus result-based Admissible Evidence

**Question:** Should future physical authority distinguish diagnostic input evidence from the current result-centered `AdmissibleEvidence`, or extend a common contract without collapsing their different validation paths?

**Why it matters:** Not every input evidence type undergoes executed-result validation, availability and admissibility must remain separate, and descriptive admissibility must never be inherited as diagnostic-input admissibility. This physical-allocation question does not reopen the semantic non-inheritance rule.

**Downstream milestone:** Future evidence contract implementation planning after R3 review.

---

## 42. Evaluator Conformance

Two conforming evaluators receiving the same:

- exact Diagnostic Proposition;
- resolved profile and version;
- evidence package;
- authority references; and
- scope, populations, and periods

must agree materially on:

- applicable evidence roles;
- explicit applicability resolution and applicability levels for all twelve frozen R1 minimum dimensions, plus every triggered additional conditional dimension;
- evidence-to-requirement mapping;
- whether each requirement is satisfied, failed, missing, externally unmet, present-but-inadmissible, unresolved, or explicitly not applicable;
- whether descriptive authority is only authenticated candidate input or has separately passed diagnostic-input admission;
- whether a defect is blocking or qualifying;
- whether material narrowing requires a new exact R2 Diagnostic Proposition, narrower binding/profile, and new R2 Diagnostic Evaluation;
- the first controlling blocker; and
- diagnostic test eligibility.

Conformance does not require identical prose, identifier syntax, internal object layout, or storage representation.

### 42.1 Minimum conformance cases

A future evaluator suite must cover at least:

1. undefined profile;
2. profile-version mismatch;
3. family template without exact binding;
4. silent omission of Metric compatibility or unit/currency compatibility;
5. valid explicit governed non-applicability for a frozen R1 minimum dimension at the appropriate applicability level;
6. shared provenance legitimately satisfying multiple roles;
7. invalid cross-role evidence reuse;
8. internal missing evidence;
9. external dependency not admitted;
10. evidence present but inadmissible;
11. descriptive `AdmissibleEvidence` offered as diagnostic input without proposition- and intended-use-specific admission;
12. qualification incorrectly used as waiver;
13. valid narrowing through a new exact R2 proposition, binding/profile, and R2 Diagnostic Evaluation;
14. product identity mismatch across periods;
15. unresolved many-to-many join;
16. unknown coverage;
17. unsupported proxy;
18. mixed currency;
19. failed required validation;
20. fully satisfied profile with a governed method reference; and
21. independently complete chain surviving an unrelated blocked chain.

### 42.2 Judgment review

For every conformance case, a reviewer must be able to identify the R2 proposition, R3 profile/version, applicable role and all mandatory dimension-applicability decisions, evidence and authority references, descriptive-versus-diagnostic admission status where relevant, controlling reason, required narrowing and R2 evaluation path, and eligibility outcome.

---

## 43. Success Criteria

R3 conforms only when all statements below are true:

- [x] Proposition-specific Required Evidence is defined.
- [x] Field-presence logic is explicitly rejected.
- [x] Layered Required Evidence Architecture is formalized.
- [x] Family templates are reusable but non-authoritative without exact binding.
- [x] Exact Proposition Binding is the controlling requirement authority.
- [x] Method references cannot waive evidence governance.
- [x] Evidence roles and dimensions remain orthogonal.
- [x] Universal dimensions do not become a role-by-dimension Cartesian product.
- [x] Every frozen R1 minimum evidence dimension is mandatory to resolve at the correct applicability level.
- [x] Metric compatibility and unit/currency compatibility cannot be silently omitted; governed non-applicability is explicit and reviewable.
- [x] Additional conditional dimensions remain distinct from the frozen R1 minimum set.
- [x] Semantic validity and source authority are preserved.
- [x] Completeness and coverage are governed without invented universal thresholds.
- [x] Temporal and population alignment are governed.
- [x] Granularity, identity, and join requirements are governed.
- [x] The five-class measurement model is defined.
- [x] Unsupported proxies fail closed.
- [x] Metric, unit, currency, and denominator compatibility are preserved.
- [x] Missingness is governed without a universal percentage.
- [x] Provenance remains traceable through existing patterns.
- [x] Required validation categories are explicit.
- [x] Internal missing evidence and external dependency remain distinct.
- [x] Availability and admissibility remain distinct.
- [x] Descriptive `AdmissibleEvidence` does not imply diagnostic-input admissibility.
- [x] Product Mix treats descriptive validated/admissible authority only as authenticated candidate input pending diagnostic intended-use admission.
- [x] Existing Data Sufficiency and Evidence Admissibility authorities are reused.
- [x] Blocking and qualifying defects are distinct.
- [x] Qualification cannot repair failed Required Evidence.
- [x] Material narrowing requires a new exact R2 Diagnostic Proposition, narrower binding/profile, and new R2 Diagnostic Evaluation.
- [x] Deterministic pre-test eligibility semantics are defined.
- [x] Test eligibility is distinct from support and Claim authorization.
- [x] R2 semantics and authority are not redefined.
- [x] Exact Proposition Binding and Required Evidence Profile remain separate from R2 Diagnostic Evaluation authority.
- [x] R4 methods are not defined.
- [x] R5 fixtures are specified only as future cases and not implemented.
- [x] Current canonical scope and v0.2.0 behavior remain unchanged.
- [x] R4–R6 are not started.

---

## 44. Dependencies and Next Milestone

R3 depends on the frozen authorities listed in Section 4 and on the current canonical sufficiency, validation, admissibility, provenance, persistence, and ClaimDecision boundaries.

This specification is Approved / Frozen and is the authoritative R3 baseline for downstream milestones. Approval and freeze do not authorize runtime implementation, diagnostic Claim-permission expansion, Product Mix execution, public diagnostic behavior, R4 execution, R5 fixture implementation, or R6 hypothesis generation.

R4 may begin only through a separate authorized `/plan`. Any R3 implementation plan, diagnostic Claim-policy expansion, public behavior change, or downstream execution requires separate explicit owner authorization.

---

**End of R3 Required Evidence Matrix Specification**
