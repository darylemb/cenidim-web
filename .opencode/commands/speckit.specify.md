---
description: Create or update the feature specification from a natural language feature description.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

<!-- include: .opencode/commands/_lib/hooks-preamble.md (HOOK_KEY=before_specify, HOOK_PHASE=Pre, HOOK_TRIGGER=none) -->

## Outline

The text the user typed after `/speckit.specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

1. **Generate a concise short name** (2-4 words) for the feature:
   - Analyze the feature description and extract the most meaningful keywords
   - Create a 2-4 word short name that captures the essence of the feature
   - Use action-noun format when possible (e.g., "add-user-auth", "fix-payment-bug")
   - Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)
   - Keep it concise but descriptive enough to understand at a glance

2. **Branch creation** (optional, via hook):
   - If a `before_specify` hook ran successfully, it will have created/switched to a git branch and output JSON containing `BRANCH_NAME` and `FEATURE_NUM`. Note these for reference.
   - If user explicitly provided `GIT_BRANCH_NAME`, pass it through to the hook

3. **Create the spec feature directory**:
   - Specs live under the default `specs/` directory unless user explicitly provides `SPECIFY_FEATURE_DIRECTORY`
   - **Resolution order for `SPECIFY_FEATURE_DIRECTORY`**:
     1. If user explicitly provided it (env var, arg, config), use as-is
     2. Otherwise auto-generate under `specs/`:
        - Check `.specify/init-options.json` for `branch_numbering`
        - If `"timestamp"`: prefix is `YYYYMMDD-HHMMSS`
        - If `"sequential"` or absent: prefix is `NNN` (next 3-digit number)
        - Construct: `<prefix>-<short-name>` (e.g., `003-user-auth`)
        - Set `SPECIFY_FEATURE_DIRECTORY` to `specs/<directory-name>`
   - Create the directory and copy `.specify/templates/spec-template.md` to `SPECIFY_FEATURE_DIRECTORY/spec.md`
   - Persist path to `.specify/feature.json`
   - You must only create one feature per invocation
   - Spec directory and file are always created by this command, never by the hook

4. Load `.specify/templates/spec-template.md` to understand required sections.

5. Follow this execution flow:
   1. Parse user description from arguments. If empty: ERROR "No feature description provided"
   2. Extract key concepts: actors, actions, data, constraints
   3. For unclear aspects:
      - Make informed guesses based on context and industry standards
      - Only mark with [NEEDS CLARIFICATION: specific question] if choice significantly impacts scope/UX, multiple reasonable interpretations exist, or no reasonable default
      - **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
      - Prioritize: scope > security/privacy > UX > technical details
   4. Fill User Scenarios & Testing section. If no clear user flow: ERROR "Cannot determine user scenarios"
   5. Generate Functional Requirements (each must be testable)
   6. Define Success Criteria (measurable, technology-agnostic outcomes)
   7. Identify Key Entities (if data involved)
   8. Return: SUCCESS (spec ready for planning)

6. Write the specification to SPEC_FILE using the template structure, replacing placeholders while preserving section order and headings.

7. **Specification Quality Validation**: After writing the initial spec, validate against quality criteria:
   a. **Create Spec Quality Checklist** at `SPECIFY_FEATURE_DIRECTORY/checklists/requirements.md` with validation items (Content Quality, Requirement Completeness, Feature Readiness sections)
   b. **Run Validation Check** against each checklist item
   c. **Handle Validation Results**:
      - **If all items pass**: Mark complete and proceed
      - **If items fail**: list, update spec, re-run validation (max 3 iterations)
      - **If [NEEDS CLARIFICATION] remain**: extract max 3 markers, present Q1/Q2/Q3 in table format with options, wait for user response
   d. **Update Checklist** with current pass/fail status

8. **Report completion** to the user with: SPECIFY_FEATURE_DIRECTORY, SPEC_FILE, Checklist results summary, Readiness for next phase

9. **Check for extension hooks**

**NOTE:** Branch creation is handled by the `before_specify` hook (git extension). Spec directory and file creation are always handled by this core command.

## Quick Guidelines

- Focus on **WHAT** users need and **WHY**.
- Avoid HOW to implement (no tech stack, APIs, code structure).
- Written for business stakeholders, not developers.
- DO NOT create any checklists that are embedded in the spec. That will be a separate command.

### Section Requirements

- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation

When creating this spec from a user prompt:

1. **Make informed guesses**: Use context, industry standards, common patterns
2. **Document assumptions**: Record reasonable defaults in the Assumptions section
3. **Limit clarifications**: Maximum 3 [NEEDS CLARIFICATION] markers - only for critical decisions
4. **Prioritize clarifications**: scope > security/privacy > UX > technical details
5. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist
6. **Common areas needing clarification** (only if no reasonable default exists):
   - Feature scope and boundaries
   - User types and permissions
   - Security/compliance requirements

**Examples of reasonable defaults** (don't ask about these):
- Data retention: Industry-standard practices
- Performance targets: Standard web/mobile app expectations
- Error handling: User-friendly messages with appropriate fallbacks
- Authentication method: Standard session-based or OAuth2 for web apps
- Integration patterns: REST/GraphQL for web services

### Success Criteria Guidelines

Success criteria must be:
1. **Measurable**: Include specific metrics (time, percentage, count, rate)
2. **Technology-agnostic**: No mention of frameworks, languages, databases, tools
3. **User-focused**: Describe outcomes from user/business perspective
4. **Verifiable**: Can be tested/validated without knowing implementation details

**Good examples**:
- "Users can complete checkout in under 3 minutes"
- "System supports 10,000 concurrent users"
- "95% of searches return results in under 1 second"

**Bad examples** (implementation-focused):
- "API response time is under 200ms" (too technical)
- "Database can handle 1000 TPS" (implementation detail)
- "React components render efficiently" (framework-specific)
- "Redis cache hit rate above 80%" (technology-specific)

## Post-Execution Checks

<!-- include: .opencode/commands/_lib/hooks-preamble.md (HOOK_KEY=after_specify, HOOK_PHASE=Post, HOOK_TRIGGER=after reporting) -->
