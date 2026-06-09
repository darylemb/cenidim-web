---
description: Generate a custom checklist for the current feature based on user requirements.
---

## Checklist Purpose: "Unit Tests for English"

**CRITICAL CONCEPT**: Checklists are **UNIT TESTS FOR REQUIREMENTS WRITING** - they validate the quality, clarity, and completeness of requirements in a given domain.

**NOT for verification/testing**:
- Verify button clicks correctly
- Test error handling works
- Confirm the API returns 200
- Check that code/implementation matches the spec

**FOR requirements quality validation**:
- "Are visual hierarchy requirements defined for all card types?" (completeness)
- "Is 'prominent display' quantified with specific sizing/positioning?" (clarity)
- "Are hover state requirements consistent across all interactive elements?" (consistency)
- "Are accessibility requirements defined for keyboard navigation?" (coverage)
- "Does the spec define what happens when logo image fails to load?" (edge cases)

**Metaphor**: If your spec is code written in English, the checklist is its unit test suite. You're testing whether the requirements are well-written, complete, unambiguous, and ready for implementation - NOT whether the implementation works.

**Ejemplos detallados por dimension** (UX, API, Performance, Security + anti-examples): ver
`.opencode/commands/_examples/checklist-examples.md`. Cargar solo si necesitas ejemplos.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

<!-- include: .opencode/commands/_lib/hooks-preamble.md (HOOK_KEY=before_checklist, HOOK_PHASE=Pre, HOOK_TRIGGER="before proceeding to the Execution Steps") -->

## Execution Steps

1. **Setup**: Run `.specify/scripts/bash/check-prerequisites.sh --json` from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS list. All file paths must be absolute.

2. **Clarify intent (dynamic)**: Derive up to THREE initial contextual clarifying questions (no pre-baked catalog). They MUST:
   - Be generated from the user's phrasing + extracted signals from spec/plan/tasks
   - Only ask about information that materially changes checklist content
   - Be skipped individually if already unambiguous in `$ARGUMENTS`
   - Prefer precision over breadth

   Generation algorithm:
   1. Extract signals: feature domain keywords, risk indicators, stakeholder hints, explicit deliverables
   2. Cluster signals into candidate focus areas (max 4) ranked by relevance
   3. Identify probable audience & timing if not explicit
   4. Detect missing dimensions: scope breadth, depth/rigor, risk emphasis, exclusion boundaries, measurable acceptance criteria
   5. Formulate questions from archetypes: Scope refinement, Risk prioritization, Depth calibration, Audience framing, Boundary exclusion, Scenario class gap

   Question formatting rules: A–E options max, compact table, never restate what user said, no speculation.

   Defaults when interaction impossible: Depth=Standard, Audience=Reviewer (PR) si code-related, Focus=Top 2 clusters.

   Output Q1/Q2/Q3. After answers: if >=2 scenario classes remain unclear, MAY ask Q4/Q5 with one-line justification each. Max 5 total.

3. **Understand user request**: Combine `$ARGUMENTS` + clarifying answers:
   - Derive checklist theme (security, review, deploy, ux)
   - Consolidate explicit must-have items
   - Map focus selections to category scaffolding
   - Infer missing context from spec/plan/tasks (no hallucination)

4. **Load feature context**: Read from FEATURE_DIR: spec.md, plan.md (if exists), tasks.md (if exists).
   - Load only necessary portions relevant to active focus areas (avoid full-file dumping)
   - Progressive disclosure: add follow-on retrieval only if gaps detected

5. **Generate checklist** - Create "Unit Tests for Requirements":
   - Create `FEATURE_DIR/checklists/` directory if missing
   - Use short descriptive name based on domain (e.g., `ux.md`, `api.md`, `security.md`)
   - If file does NOT exist: create new with CHK001 start
   - If file exists: append, continuing from last CHK ID
   - Never delete or replace existing content - always preserve and append

   **CORE PRINCIPLE - Test the Requirements, Not the Implementation**:
   Every item MUST evaluate requirements themselves for: Completeness, Clarity, Consistency, Measurability, Coverage.

   **Category Structure**:
   - Requirement Completeness, Clarity, Consistency
   - Acceptance Criteria Quality
   - Scenario Coverage, Edge Case Coverage
   - Non-Functional Requirements
   - Dependencies & Assumptions
   - Ambiguities & Conflicts

   **ITEM STRUCTURE**:
   - Question format asking about requirement quality
   - Focus on what's WRITTEN (or not written) in the spec/plan
   - Quality dimension in brackets [Completeness/Clarity/etc.]
   - Reference spec section `[Spec §X.Y]` when checking existing requirements
   - Use `[Gap]` marker for missing requirements

   **PROHIBITED** (these make it an implementation test):
   - "Verify", "Test", "Confirm", "Check" + implementation behavior
   - Code execution, user actions, system behavior references
   - "Displays correctly", "works properly"
   - "Click", "navigate", "render", "load", "execute"

   **REQUIRED PATTERNS**:
   - "Are [requirement type] defined/specified/documented for [scenario]?"
   - "Is [vague term] quantified/clarified with specific criteria?"
   - "Are requirements consistent between [section A] and [section B]?"
   - "Can [requirement] be objectively measured/verified?"

   **Traceability**: MIN 80% of items MUST include `[Spec §X.Y]`, `[Gap]`, `[Ambiguity]`, `[Conflict]`, or `[Assumption]`.

   **Content Consolidation**: Soft cap 40 items; merge near-duplicates; if >5 low-impact edge cases, group as one item.

6. **Structure Reference**: Generate the checklist following the canonical template in `.specify/templates/checklist-template.md`. If template is unavailable, use: H1 title, meta lines, `##` category sections containing `- [ ] CHK### <item>` lines with globally incrementing IDs starting at CHK001.

7. **Report**: Output full path to checklist file, item count, and summarize:
   - File created vs appended
   - Focus areas selected
   - Depth level
   - Actor/timing
   - Any explicit must-have items incorporated

**Important**: Each `/speckit.checklist` invocation uses a short descriptive filename. To avoid clutter, use descriptive types and clean up obsolete checklists when done.

## Post-Execution Checks

<!-- include: .opencode/commands/_lib/hooks-preamble.md (HOOK_KEY=after_checklist, HOOK_PHASE=Post, HOOK_TRIGGER=after reporting) -->
