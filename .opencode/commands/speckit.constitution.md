---
description: Create or update the project constitution from interactive or provided principle inputs, ensuring all dependent templates stay in sync.
handoffs:
  - label: Build Specification
    agent: speckit.specify
    prompt: Implement the feature specification based on the updated constitution. I want to build...
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

<!-- include: .opencode/commands/_lib/hooks-preamble.md (HOOK_KEY=before_constitution, HOOK_PHASE=Pre, HOOK_TRIGGER="before proceeding to the Outline") -->

## Outline

You are updating the project constitution at `.specify/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, (b) fill the template precisely, and (c) propagate any amendments across dependent artifacts.

**Note**: If `.specify/memory/constitution.md` does not exist yet, it should have been initialized from `.specify/templates/constitution-template.md` during project setup. If it's missing, copy the template first.

Follow this execution flow:

1. Load the existing constitution at `.specify/memory/constitution.md`.
   - Identify every placeholder token of the form `[ALL_CAPS_IDENTIFIER]`.
   **IMPORTANT**: The user might require less or more principles than the ones used in the template. If a number is specified, respect that - follow the general template.

2. Collect/derive values for placeholders:
   - If user input supplies a value, use it
   - Otherwise infer from existing repo context (README, docs, prior constitution versions)
   - For governance dates: `RATIFICATION_DATE` is the original adoption date, `LAST_AMENDED_DATE` is today if changes are made
   - `CONSTITUTION_VERSION` must increment according to semantic versioning:
     - MAJOR: Backward incompatible governance/principle removals or redefinitions
     - MINOR: New principle/section added or materially expanded guidance
     - PATCH: Clarifications, wording, typo fixes, non-semantic refinements
   - If version bump type ambiguous, propose reasoning before finalizing

3. Draft the updated constitution content:
   - Replace every placeholder with concrete text (no bracketed tokens left except intentionally retained)
   - Preserve heading hierarchy
   - Each Principle section: succinct name line, paragraph capturing non-negotiable rules, explicit rationale
   - Governance section lists amendment procedure, versioning policy, compliance review expectations

4. Consistency propagation checklist:
   - Read `.specify/templates/plan-template.md` and ensure "Constitution Check" aligns
   - Read `.specify/templates/spec-template.md` for scope/requirements alignment
   - Read `.specify/templates/tasks-template.md` and ensure task categorization reflects principle changes
   - Read each command file in `.specify/templates/commands/*.md` to verify no outdated references
   - Read any runtime guidance docs (README.md, etc.). Update references to principles changed.

5. Produce Sync Impact Report (prepend as HTML comment at top of constitution file):
   - Version change: old → new
   - List of modified principles
   - Added/removed sections
   - Templates requiring updates with file paths
   - Follow-up TODOs

6. Validation before final output:
   - No remaining unexplained bracket tokens
   - Version line matches report
   - Dates ISO format YYYY-MM-DD
   - Principles are declarative, testable, free of vague language

7. Write the completed constitution back to `.specify/memory/constitution.md` (overwrite).

8. Output final summary to the user with:
   - New version and bump rationale
   - Files flagged for manual follow-up
   - Suggested commit message

Formatting & Style Requirements:
- Use Markdown headings exactly as in the template
- Wrap long rationale lines to keep readability (<100 chars ideally)
- Single blank line between sections
- No trailing whitespace

If the user supplies partial updates, still perform validation and version decision steps.

If critical info missing, insert `TODO(<FIELD_NAME>): explanation` and include in Sync Impact Report.

Do not create a new template; always operate on the existing constitution file.

## Post-Execution Checks

<!-- include: .opencode/commands/_lib/hooks-preamble.md (HOOK_KEY=after_constitution, HOOK_PHASE=Post, HOOK_TRIGGER=after reporting) -->
