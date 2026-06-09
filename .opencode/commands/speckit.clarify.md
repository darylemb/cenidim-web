---
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

<!-- include: .opencode/commands/_lib/hooks-preamble.md (HOOK_KEY=before_clarify, HOOK_PHASE=Pre, HOOK_TRIGGER="before proceeding to the Outline") -->

## Outline

Goal: Detect and reduce ambiguity or missing decision points in the active feature specification and record the clarifications directly in the spec file.

Note: This clarification workflow is expected to run (and be completed) BEFORE invoking `/speckit.plan`. If the user explicitly states they are skipping clarification (e.g., exploratory spike), you may proceed, but must warn that downstream rework risk increases.

Execution steps:

1. Run `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` from repo root **once** (combined `--json --paths-only` mode / `-Json -PathsOnly`). Parse minimal JSON payload fields: `FEATURE_DIR`, `FEATURE_SPEC`, (optionally `IMPL_PLAN`, `TASKS`). If JSON parsing fails, abort and instruct user to re-run `/speckit.specify`. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. Load the current spec file. Perform a structured ambiguity & coverage scan using this taxonomy. For each category, mark status: Clear / Partial / Missing. Produce an internal coverage map used for prioritization (do not output raw map unless no questions will be asked).

   **Functional Scope & Behavior**: Core user goals & success criteria, Explicit out-of-scope declarations, User roles / personas differentiation

   **Domain & Data Model**: Entities, attributes, relationships; Identity & uniqueness rules; Lifecycle/state transitions; Data volume / scale assumptions

   **Interaction & UX Flow**: Critical user journeys / sequences; Error/empty/loading states; Accessibility or localization notes

   **Non-Functional Quality Attributes**: Performance, Scalability, Reliability & availability, Observability, Security & privacy, Compliance

   **Integration & External Dependencies**: External services/APIs and failure modes; Data import/export formats; Protocol/versioning assumptions

   **Edge Cases & Failure Handling**: Negative scenarios; Rate limiting / throttling; Conflict resolution

   **Constraints & Tradeoffs**: Technical constraints; Explicit tradeoffs or rejected alternatives

   **Terminology & Consistency**: Canonical glossary terms; Avoided synonyms / deprecated terms

   **Completion Signals**: Acceptance criteria testability; Measurable Definition of Done style indicators

   **Misc / Placeholders**: TODO markers / unresolved decisions; Ambiguous adjectives lacking quantification

   For each category with Partial or Missing status, add a candidate question opportunity unless clarification would not materially change implementation.

3. Generate (internally) a prioritized queue of candidate clarification questions (maximum 5). Do NOT output them all at once. Constraints:
   - Maximum 5 total questions across the whole session
   - Each answerable with EITHER multiple-choice (2-5 options) OR short-phrase answer (<=5 words)
   - Only include questions whose answers materially impact architecture, data modeling, task decomposition, test design, UX behavior, operational readiness, or compliance validation
   - Ensure category coverage balance
   - Exclude questions already answered
   - Favor clarifications that reduce downstream rework risk
   - If more than 5 categories remain unresolved, select top 5 by (Impact * Uncertainty)

4. Sequential questioning loop (interactive):
   - Present EXACTLY ONE question at a time
   - For multiple-choice: analyze all options, present recommended option prominently with reasoning, format as table A-E, allow short alternative
   - For short-answer: provide suggested answer with reasoning
   - After user answers: validate mapping, record in working memory, move to next
   - Stop when: all critical ambiguities resolved, user signals completion, or 5 questions reached
   - Never reveal future queued questions in advance

5. Integration after EACH accepted answer (incremental update approach):
   - Maintain in-memory representation of spec plus raw file contents
   - For first integrated answer: ensure `## Clarifications` section exists, create `### Session YYYY-MM-DD` subheading
   - Append bullet: `- Q: <question> → A: <final answer>`
   - Apply clarification to most appropriate section (Functional, User Stories, Data Model, Success Criteria, Edge Cases, Terminology)
   - Replace earlier ambiguous statements instead of duplicating
   - Save spec file AFTER each integration (atomic overwrite)
   - Preserve formatting: keep heading hierarchy

6. Validation (performed after EACH write plus final pass):
   - Exactly one bullet per accepted answer
   - Total asked questions ≤ 5
   - Updated sections contain no lingering vague placeholders
   - No contradictory earlier statement remains
   - Markdown structure valid
   - Terminology consistency

7. Write the updated spec back to `FEATURE_SPEC`.

8. Report completion:
   - Number of questions asked & answered
   - Path to updated spec
   - Sections touched
   - Coverage summary table (Resolved / Deferred / Clear / Outstanding per category)
   - If Outstanding or Deferred remain, recommend next step
   - Suggested next command

Behavior rules:
- If no meaningful ambiguities found: "No critical ambiguities detected worth formal clarification."
- If spec file missing: instruct user to run `/speckit.specify` first
- Never exceed 5 total asked questions
- Avoid speculative tech stack questions
- Respect user early termination signals ("stop", "done", "proceed")
- If no questions asked due to full coverage, output compact coverage summary

Context for prioritization: $ARGUMENTS

## Post-Execution Checks

<!-- include: .opencode/commands/_lib/hooks-preamble.md (HOOK_KEY=after_clarify, HOOK_PHASE=Post, HOOK_TRIGGER=after reporting) -->
