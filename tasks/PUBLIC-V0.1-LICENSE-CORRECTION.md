# PUBLIC V0.1 LICENSE CORRECTION

## 1. Status

Status:

APPROVED / FROZEN

Implementation:

COMPLETE

Freeze status:

FROZEN

Main Project Review:

COMPLETE

Independent Review:

APPROVE

Release Decision:

NOT CHANGED

License governance:

RESOLVED

Approved Public v0.1 license:

MIT License / MIT

SPDX identifier:

MIT

Approved copyright line:

Copyright (c) 2026 Jui-Hsin (Daniel) Lin

This task specification authorized a narrowly scoped pre-release license
governance correction for CommerceLens Public v0.1. Implementation is complete,
independent focused review approved the correction, and this task is now
approved and frozen.

## 2. Purpose

CommerceLens Public v0.1 is currently recorded as:

```text
APPROVED / FROZEN
READY FOR PUBLIC RELEASE / NOT YET RELEASED
```

Before actual public release, Main Project governance has made an explicit
licensing decision change:

FROM:

```text
Apache License 2.0 / Apache-2.0
```

TO:

```text
MIT License / MIT
```

The purpose of this task is only to govern that license correction before the
first public release.

The rationale is that CommerceLens Public v0.1 is intended to maximize
low-friction open-source inspection, reuse, forking, and portfolio adoption, and
MIT is a simpler permissive license for the current project objective.
Commercial use, modification, redistribution, and downstream closed-source use
remain permitted.

This is a licensing and presentation decision. It is not an analytical product
change, not P10, and not a product-quality claim.

This MIT licensing decision supersedes the prior Apache-2.0 Public v0.1
licensing decision for the upcoming first public release. Prior Apache-2.0
governance remains valid historical evidence and must not be erased merely
because the active license authority is changing.

The current active release license authority becomes MIT only after the
governed correction lifecycle completes.

The governed correction lifecycle is now complete. The active Public v0.1
release license authority is MIT License / MIT.

## 3. Repository Authority

Repository:

```text
/Users/linruixin/Desktop/commercelens skills/project 1
```

Observed branch at task-specification creation:

```text
implementation/public-v0.1-release-readiness
```

Observed HEAD at task-specification creation:

```text
c72473593952a9f3bf2874243ca8de9194d6035b
```

Public v0.1 implementation commit:

```text
15d81279f243d66366fc4279b4f87a00beede042
```

Current package version:

```text
0.1.0
```

Future Git tag:

```text
v0.1.0
```

Future GitHub Release:

```text
CommerceLens v0.1.0
```

No tag, GitHub Release, push, PyPI publication, hosted service, or public
release action is authorized by this task.

MIT license implementation commit:

```text
216601de809cdc5fe6e744492f985822cb522d27
```

MIT task provenance commit:

```text
87bb49862cd74fff59258208d6b8eb89cf2fb42a
```

## 4. Current License Evidence

Observed license state at task-specification creation:

- `LICENSE` contains the canonical Apache License 2.0 text.
- `README.md` states: `CommerceLens AI is licensed under the Apache License
  2.0. See LICENSE.`
- `README.md` records SPDX identifier `Apache-2.0`.
- `PROJECT_STATE.md` records license `Apache-2.0` and approved license
  `Apache License 2.0`.
- `tasks/PUBLIC-V0.1-RELEASE-READINESS-GATE.md` records Apache License 2.0
  release-readiness authority and verification.

Observed packaging metadata:

- `pyproject.toml` declares package version `0.1.0`.
- `pyproject.toml` does not declare a license field.
- `pyproject.toml` does not declare Apache-specific license metadata.

No unresolved implementation file-scope decision is raised for `pyproject.toml`
by current repository evidence. `pyproject.toml` remains protected unless a
separate Main Project authorization changes that scope.

## 5. Proposed Future Implementation Scope

Main Project Review approves future implementation to modify only:

- `LICENSE`
- `README.md`

No other ordinary implementation file is authorized.

Future `LICENSE` change:

- replace the canonical Apache License 2.0 text with the standard MIT License
  text;
- use exactly `Copyright (c) 2026 Jui-Hsin (Daniel) Lin` as the copyright
  line;
- use no custom restrictions;
- prohibit no commercial use;
- create no dual-license arrangement;
- combine no MIT and Apache terms;
- add no non-standard clauses.

Future `README.md` change:

- replace only required Public v0.1 license references from `Apache License
  2.0` to `MIT License`;
- replace only required SPDX references from `Apache-2.0` to `MIT`.
- do not perform a broader README redesign.

The future implementation must not modify:

- this governing task specification;
- package version;
- dependencies;
- source;
- tests;
- examples;
- analytical behavior;
- Metric definitions;
- Evidence semantics;
- ClaimDecision policy;
- runtime semantics;
- P10 status.

## 6. MIT License Authority

License governance:

```text
RESOLVED
```

Approved Public v0.1 license:

```text
MIT License / MIT
```

SPDX identifier:

```text
MIT
```

The implementation must use the standard MIT License text.

Approved copyright line:

```text
Copyright (c) 2026 Jui-Hsin (Daniel) Lin
```

The future `LICENSE` implementation must use that exact copyright line.

The future implementer must not invent a legal entity, company, organization,
username, additional copyright holder, alternative spelling, or shortened name.

## 7. Release Readiness Impact

The existing Apache-based Release Readiness evidence cannot be silently reused
as if the license state were unchanged.

After implementation, focused verification must cover:

- standard MIT License text;
- exact approved copyright line;
- `README.md` MIT license references;
- absence of active Apache release-license ambiguity;
- absence of source, test, example, dependency, `pyproject.toml`,
  package-version, and packaging changes;
- absence of analytical behavior changes;
- `git diff --check`;
- Public v0.1 focused regression;
- full regression if required by existing Release Readiness governance;
- clean public-facing license consistency.

Redundant clean-checkout analytical verification is not required unless the
license correction changes executable behavior or packaging.

If implementation unexpectedly affects packaging or runtime behavior, stop for
Main Project Review.

After approval, implementation, Source Review, verification, and governance
recording, Public v0.1 Release Readiness may be restored as:

```text
READY FOR PUBLIC RELEASE / NOT YET RELEASED
```

Actual public release remains a separate action.

## 8. Analytical Freeze

This task preserves exactly:

Supported Metrics:

- `revenue`
- `orders`
- `aov`
- `revenue_change`

Positive Claim permission:

```text
ClaimType.DESCRIPTIVE only
```

Positive Qualified path:

```text
NONE
```

MetadataStore:

```text
v6
```

No Metric, Evidence, ClaimDecision, validation, source, test, or runtime
semantics may change.

## 9. P10 Boundary

P10 remains:

```text
Revenue Change Percentage
```

P10 status remains:

```text
NOT STARTED
```

This task is not P10 and does not authorize Revenue Change Percentage work.

## 10. Governance Lifecycle

Required lifecycle:

```text
License Correction Task Spec
-> Main Project Review
-> APPROVED FOR IMPLEMENTATION / NOT FROZEN
-> focused LICENSE / README implementation
-> focused Source Review / verification
-> governance recording
-> Public v0.1 Release Readiness restored as:
   READY FOR PUBLIC RELEASE / NOT YET RELEASED
-> separate Public Release action
```

## 11. Acceptance Criteria

1. PASS — Approved future license is recorded as `MIT License / MIT`.
2. PASS — Apache License 2.0 is removed from the active Public v0.1 release surface
   after authorized implementation.
3. PASS — Standard MIT License text is used in `LICENSE`.
4. PASS — `LICENSE` uses exactly `Copyright (c) 2026 Jui-Hsin (Daniel) Lin`.
5. PASS — `README.md` identifies the license as MIT License.
6. PASS — `README.md` records SPDX identifier `MIT`.
7. PASS — No custom restrictions are added.
8. PASS — No commercial-use prohibition is added.
9. PASS — No dual licensing is introduced.
10. PASS — MIT and Apache terms are not combined.
11. PASS — Package version remains `0.1.0`.
12. PASS — No analytical source files are changed.
13. PASS — No tests are changed.
14. PASS — No examples are changed.
15. PASS — No dependencies are changed.
16. PASS — `pyproject.toml` remains unchanged unless separately authorized by Main
    Project Review.
17. PASS — Public v0.1 focused regression remains passing.
18. PASS — Full regression is run if required by existing Release Readiness
   governance.
19. PASS — `git diff --check` passes.
20. PASS — No Git tag, GitHub Release, push, PyPI publication, hosted service, public
    release action, or P10 work occurs; P10 remains `Revenue Change Percentage
    — NOT STARTED`.

## 12. Implementation Result

Implementation:

```text
COMPLETE
```

Implementation commit:

```text
216601de809cdc5fe6e744492f985822cb522d27
```

Implementation changed exactly:

- `LICENSE`
- `README.md`

Implementation result:

- standard MIT License installed;
- exact copyright line used:
  `Copyright (c) 2026 Jui-Hsin (Daniel) Lin`;
- README active license changed to MIT License;
- README SPDX changed to MIT;
- `pyproject.toml` unchanged;
- package version remains `0.1.0`;
- no source, test, example, dependency, packaging, or analytical behavior
  change.

## 13. Governance Provenance Limitation

The MIT License Correction task was created and Main Project reviewed before
implementation, but its task specification remained untracked until after the
implementation commit.

Task-spec provenance commit:

```text
87bb49862cd74fff59258208d6b8eb89cf2fb42a
```

Disposition:

```text
GOVERNANCE PROVENANCE LIMITATION — NON-ANALYTICAL
```

No pre-implementation Git authorization commit existed. No history rewrite was
performed. The implementation commit was not amended. The provenance commit
must not be represented as a pre-implementation authorization baseline.

## 14. Independent Focused Source Review / Verification

Decision:

```text
APPROVE
```

Reviewed MIT implementation commit:

```text
216601de809cdc5fe6e744492f985822cb522d27
```

Reviewed provenance commit:

```text
87bb49862cd74fff59258208d6b8eb89cf2fb42a
```

Verified:

- implementation scope exact;
- `LICENSE` standard MIT text;
- exact copyright line correct;
- README MIT references correct;
- no active Apache ambiguity;
- `pyproject.toml` protected and unchanged;
- package version `0.1.0`;
- analytical freeze preserved;
- focused regression: `15 passed`;
- full regression: `526 passed`;
- `git diff --check` passed;
- P10 remained NOT STARTED.

Findings:

- BLOCKER: NONE
- MATERIAL: NONE
- MINOR: Governance chronology/provenance limitation only — transparent,
  non-analytical, non-blocking.

## 15. Final Governance Recording

Final MIT License Correction status:

```text
APPROVED / FROZEN
```

Implementation:

```text
COMPLETE
```

Freeze:

```text
FROZEN
```

Main Project Review:

```text
COMPLETE
```

Independent Review:

```text
APPROVE
```

License governance:

```text
RESOLVED
```

Approved active license:

```text
MIT License / MIT
```

Approved copyright line:

```text
Copyright (c) 2026 Jui-Hsin (Daniel) Lin
```

## 16. Historical Stop Condition

The Main Project Review step for task-specification creation modified only this
file:

```text
tasks/PUBLIC-V0.1-LICENSE-CORRECTION.md
```

That earlier step did not implement the license change.
