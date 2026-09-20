# P15 Execution Protocol

## 1. Objective

Determine whether a first-time external participant can use CommerceLens in a
fresh Codex conversation to complete a governed descriptive comparison and
correctly understand mapping, coverage authority, provenance, retention, and
diagnostic refusal.

P15 reports observed evidence only. It does not establish market demand,
willingness to pay, benchmark superiority, causal-analysis quality, or general
usability beyond the tested participants.

## 2. Approved decisions

- Primary surface: fresh Codex conversation.
- CLI is allowed only for public installation steps or product-exposed
  retained-run operations.
- Observer may not install the product for the participant.
- Run one independent pilot participant first.
- If P01 has no reliability blocker and the protocol is executable, continue
  toward three independent participants total.
- Dataset A and Dataset B are new closed-period synthetic fixtures.
- Retained mode is secondary; at least one of the final three participants must
  exercise it.
- Temporary mode must be exercised by at least one participant.
- F3 does not block P15; single-period KPI is excluded from the pass gate.
- Recording is optional and requires explicit consent.
- Synthetic retained bundles may be retained as validation evidence.
- Existing retention UX gaps are observed, not pre-fixed.

## 3. Frozen datasets

### Dataset A

`data/P15-A-governed-marketplace.csv` is a fully synthetic order-line export
with 100 rows, 48 eligible baseline orders, 45 eligible comparison orders, four
multi-line eligible orders, and three cancelled control rows.

Periods:

- Baseline: 2025-01-01 through 2025-03-31 inclusive
- Comparison: 2026-01-01 through 2026-03-31 inclusive

The source uses non-canonical headers, USD only, `paid` as eligible, and
`cancelled` as excluded. The source is intentionally not accompanied by an
oracle or implementation explanation in participant material.

### Dataset B

`data/P15-B-coverage-unknown.csv` is a fully synthetic 80-row export with the
same public source shape. The participant-facing context truthfully states
that they do not know whether all pages, relevant status filters, and complete
records are present. No accepted coverage declaration is supplied.

The expected authority outcome is blocked or clarification-required, with no
material Revenue, Orders, AOV, or Revenue Change claim.

## 4. Participant sequence

P01 performs S1, S2, S3, and one assigned retention condition: S4 or S5. The
assigned condition is recorded before the session and is not explained as a
test hypothesis.

For the final three-person sample:

- at least one participant performs S4 retained mode;
- at least one participant performs S5 temporary mode;
- S1 and S2 are performed by every participant;
- S3 is performed in a fresh conversation.

Each scenario starts in a fresh Codex conversation. The product is not
reinstalled between scenarios unless installation itself is the scenario.

## 5. Observer rules

Level 0: no intervention.

Level 1: participant may reread product-visible instructions.

Level 2: use only: “Please continue using only what the product tells you.”

Level 3: use only the minimum rescue language in
`observer/intervention-script.md` for installation, invocation, or file-location
blocks. No rescue wording may teach mapping semantics, coverage authority,
USER_DECLARED, expected values, or which coverage choice to select.

Every intervention records timestamp, level, exact wording, trigger, and
outcome impact. Any Level 2 or Level 3 intervention disqualifies that task from
unaided-success counting.

## 6. Objective measures

Record installation success, time to first valid invocation, file loading,
mapping completion and correctness, coverage response correctness, refusal to
falsely confirm unknown coverage, descriptive-result completion, numerical
correctness, diagnostic refusal, provenance comprehension, retention
comprehension, retained list/inspect/verify success, interventions,
unrecoverable errors, task time, and unsupported material claims.

Do not collapse these into an arbitrary confidence score.

## 7. Reliability gate

The following counts must all be zero:

- unsupported material claims;
- false coverage authority;
- false external-verification representation;
- silent retained-evidence corruption.

One violation is sufficient to stop P15 for remediation.

## 8. Formal three-person target

After three participants, the bounded target is:

- at least 2/3 S1 unaided completion;
- at least 2/3 core comprehension success;
- zero reliability-gate violations;
- comprehension score at least 7/8 per participant, with no material
  misunderstanding on Q1, Q3, Q4, Q5, or Q8.

One participant is a pilot and cannot be called “P15 PASS”.

## 9. Pilot outcome

### PROCEED TO P02/P03

P01 has no correctness, authority, or retained-evidence blocker and the
protocol itself is executable.

### PAUSE FOR BOUNDED REMEDIATION

Reliability remains correct, but installation, UX, or documentation produces a
repeatable HIGH issue. Remediate only the bounded issue, then repeat affected
scenarios.

### STOP P15

Any unsupported material claim, false authority, USER_DECLARED
misrepresentation, retained-evidence misrepresentation/corruption, or protocol
contamination that invalidates the observation.

## 10. Evidence and privacy

Use anonymous participant IDs. Capture exact prompts, outputs, timestamps,
coverage responses, retention choice, interventions, objective results,
comprehension answers, interview answers, and retained run metadata where
applicable. Separate raw observation, observer interpretation, and product
inference. Do not collect names, email addresses, credentials, or private
business/customer data.

## 11. Pre-P01 validation

The package is not execution-ready until all of the following are recorded in
the final report:

- deterministic regeneration and hash identity;
- independent oracle validation;
- current-product Dataset A governed dry run;
- current-product Dataset B blocked dry run;
- historical-period closure check;
- participant-material oracle leakage check;
- observer-material review;
- `git diff --check`.

No human participant may be run as part of this preparation goal.
