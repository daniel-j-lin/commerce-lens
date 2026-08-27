# CommerceLens AI — Codex Repository Instructions

## 1. Authority

CommerceLens AI is governed by the Approved / Frozen specifications under:

`docs/frozen/`

The governing principle is:

> No material claim without traceable evidence.

The Frozen specifications are authoritative.

Implementation must conform to them.

If implementation convenience conflicts with a Frozen semantic:

- preserve the Frozen semantic;
- stop the affected change;
- report the conflict;
- do not silently reinterpret the requirement.

Files under `docs/frozen/` are read-only governing artifacts.

Never modify them unless the user explicitly provides a Main Project-approved replacement.

---

## 2. Task Execution Contract

Every implementation task must answer six questions before completion.

### 2.1 What is being done?

Determine the exact requested implementation slice from the current task prompt.

Implement only that slice.

Do not infer authorization for the next project phase.

A task prompt authorizes only the work explicitly included in that task.

---

### 2.2 Where may changes occur?

Before editing:

1. inspect the relevant existing modules;
2. identify the minimum files required;
3. prefer existing approved module boundaries;
4. create new modules only when the current architecture clearly requires them.

Changes should remain inside the smallest relevant implementation boundary.

Do not perform unrelated repository cleanup.

---

### 2.3 What must not be changed?

Unless the current task explicitly authorizes it, do not modify:

- `docs/frozen/`;
- approved Metric semantics;
- Evidence Contract semantics;
- fixture expected outcomes;
- Architecture decisions;
- unrelated implementation phases;
- public APIs unrelated to the task;
- dependencies;
- package structure;
- repository-wide formatting.

Never introduce:

- Multi-Agent product architecture;
- RAG;
- vector databases;
- generic plugin frameworks;
- microservices;
- network APIs;
- cloud infrastructure;
- autonomous business actions;
- unsupported Metrics;
- predictive or causal analysis.

Do not add a technology because it is fashionable or convenient.

---

## 3. Implementation Discipline

Use this priority order:

1. Analytical correctness
2. Evidence traceability
3. Reproducibility
4. Business value
5. Data safety
6. Transparent limitations
7. MVP depth
8. Maintainability
9. Documentation
10. Visual polish

Prefer:

- explicit deterministic code over clever abstraction;
- typed contracts over unstructured dictionaries;
- fail-closed behavior over guessing;
- one governed implementation over duplicated logic;
- small changes over speculative framework construction.

Do not duplicate governed KPI formulas in prompts, README files, or unrelated modules.

The authoritative Metric semantics belong to the Frozen Metric Dictionary and later governed runtime Metric Registry.

---

## 4. Scope Protection

Never automatically continue into the next implementation phase.

Examples:

finishing Canonicalization does not authorize Metric execution;

finishing Metric execution does not authorize Claim policy;

finishing the engine does not authorize UI;

finishing MVP implementation does not authorize Benchmark scoring.

When the current task is complete:

STOP.

Wait for Main Project Review or a new explicit task.

---

## 5. Evidence and Deterministic Boundaries

The following boundaries are non-negotiable:

- LLM reasoning is not numerical execution evidence.
- Generated code is not execution evidence.
- Executed Result is not Validated Result.
- Failed validation cannot be repaired by qualification.
- Missing is not zero.
- Unknown currency must not be inferred.
- Duplicate ambiguity must not be silently resolved.
- Contribution is not causation.
- The Skill cannot self-authorize material Claim admissibility.
- Independent valid analytical chains must survive unrelated failures.

Do not introduce bypass flags such as:

- `force_valid`
- `ignore_validation`
- `override_failure`
- `assume_success`

---

## 6. Before Editing

Before making material changes:

1. read the applicable `AGENTS.md`;
2. read the current task prompt;
3. inspect the relevant Frozen specification sections;
4. inspect the current implementation and tests;
5. run the relevant baseline tests when practical.

Do not rewrite working code before understanding the existing behavior.

---

## 7. Testing Requirements

Every implemented behavior requires deterministic tests where practical.

Tests must:

- exercise observable behavior;
- cover positive and negative cases;
- include failure paths when the contract is fail-closed;
- use synthetic/local data only;
- avoid network dependencies;
- avoid nondeterministic timing;
- preserve source immutability where applicable.

When fixing a defect:

add or update a test that would fail without the correction whenever practical.

Do not create fake passing validation or placeholder success behavior.

---

## 8. Verification Before Completion

Before declaring a task complete:

1. run targeted tests for changed behavior;
2. run the complete relevant project test suite;
3. inspect the final git diff;
4. verify no protected/Frozen files changed;
5. verify no unauthorized dependency was added;
6. verify no later-phase functionality was introduced;
7. verify error/failure paths remain fail-closed;
8. verify the final implementation matches the current task scope.

Do not claim tests passed unless they were actually executed.

Do not fabricate:

- test counts;
- coverage;
- benchmark scores;
- execution results;
- confidence values.

---

## 9. When to Ask the User / Stop

Do not repeatedly ask for confirmation for ordinary implementation details.

Continue autonomously when the choice:

- does not change analytical semantics;
- does not change Architecture;
- does not add scope;
- is reversible;
- has one clearly simplest implementation.

STOP and ask/report when:

- Frozen specifications materially conflict;
- a required semantic is genuinely undefined;
- the choice would alter Metric meaning;
- the choice would alter Evidence admissibility;
- the choice would change fixture expected outcomes;
- the choice requires an Architecture change;
- a new major dependency appears necessary;
- destructive repository/data operations are required;
- tests expose a governing-spec contradiction.

Do not resolve these cases by guessing.

---

## 10. Definition of Done

A task is complete only when:

- every requested deliverable exists;
- required behavior is implemented;
- required failure behavior is implemented;
- tests covering the implementation exist;
- the complete relevant test suite passes;
- no Frozen specification was modified;
- no unauthorized scope was added;
- no known blocking defect remains;
- actual verification results are recorded.

Completion of one task does not authorize the next task.

---

## 11. Final Task Report

Every implementation task must end with a concise factual report containing:

- files created or modified;
- behavior implemented;
- tests added or modified;
- exact test command;
- exact test result;
- dependencies added or changed;
- known limitations;
- Frozen-spec conflicts or ambiguities discovered;
- explicitly unimplemented next-phase items.

Do not report a result that was not verified.

---

## 12. Git and External Actions

Do not:

- push;
- merge;
- open a PR;
- publish a package;
- deploy;
- modify external systems;

unless explicitly requested.

Repository implementation work may proceed autonomously inside the authorized task scope.
