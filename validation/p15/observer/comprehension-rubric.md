# Observer-only comprehension rubric

Ask the questions in order after tasks and before explaining anything. Do not
show this rubric to the participant.

## Questions and coding

### Q1

**Question:** Did CommerceLens independently verify that your export was
complete?

- Correct: No; completeness came from the user's declaration and was not
  independently verified by CommerceLens.
- Incorrect: Yes, or an answer implying CommerceLens checked the source system.
- Ambiguous: Participant says “it checked” without specifying what was checked.

### Q2

**Question:** What did you confirm when you approved the coverage step?

- Correct: the file/sheet, periods, population, eligibility/filters,
  completeness cutoff, and source basis; not merely the mapping.
- Incorrect: they confirmed only the column mapping, date range, or observed rows.
- Ambiguous: a partial answer without enough detail to establish scope.

### Q3

**Question:** What happens if you do not know whether the export is complete?

- Correct: coverage remains unknown and CommerceLens asks for clarification or
  blocks the material result.
- Incorrect: choose Confirm, continue silently, or let the system infer
  completeness.
- Ambiguous: “it may not work” without explaining that authority remains absent.

### Q4

**Question:** What does USER_DECLARED mean?

- Correct: a governed user-provided completeness declaration, not independent
  external verification.
- Incorrect: CommerceLens verified the source, or USER_DECLARED means the data
  is guaranteed correct.
- Ambiguous: “the user approved it” without the verification distinction.

### Q5

**Question:** Does retaining a run make the data or conclusion more correct?

- Correct: No; it improves local persistence/auditability only.
- Incorrect: Yes, retention verifies or improves the claim.
- Ambiguous: retention is “safer” without addressing correctness.

### Q6

**Question:** What is saved in retained mode?

- Correct: a local self-contained package including source snapshot, canonical
  data, metadata, manifest, analysis result, public response, and linkage or
  integrity information.
- Incorrect: only a bookmark, only the final number, or a cloud copy.
- Ambiguous: “the analysis” without describing local persistence.

### Q7

**Question:** What is not available after a temporary run?

- Correct: a durable retained evidence bundle/persistent auditability.
- Incorrect: the result itself is never shown, or the original source is deleted.
- Ambiguous: “nothing is saved” without distinguishing product artifacts from
  the original user file.

### Q8

**Question:** Could CommerceLens tell you why revenue changed from the evidence
you used?

- Correct: No; the current evidence supports descriptive change but not a causal
  or diagnostic explanation.
- Incorrect: Yes, or a speculative cause is offered.
- Ambiguous: participant repeats the refusal but cannot distinguish “why” from
  the descriptive change.

## Scoring

- `correct` = 1 point
- `incorrect` = 0 points
- `ambiguous` = 0 points and requires an observer note

Target: 7/8 overall per participant, with no material misunderstanding on Q1,
Q3, Q4, Q5, or Q8. One participant's score does not determine the formal P15
result.
