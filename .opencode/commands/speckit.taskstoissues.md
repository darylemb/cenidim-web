---
description: Convert existing tasks into actionable, dependency-ordered GitHub issues for the feature based on available design artifacts.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

**PREREQUISITE**: This command requires the GitHub MCP server (`github/github-mcp-server/issue_write`) which is NOT configured in the current `opencode.json` (only `playwright` is). To use this command:
1. Add the GitHub MCP to `opencode.json` under `mcp`
2. OR install/configure the MCP manually
3. OR use a different issue-tracking tool

If the MCP is not available, abort with a clear error message instead of attempting the conversion.

## Pre-Execution Checks

<!-- include: .opencode/commands/_lib/hooks-preamble.md (HOOK_KEY=before_taskstoissues, HOOK_PHASE=Pre, HOOK_TRIGGER="before proceeding to the Outline") -->

## Outline

1. Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").
2. From the executed script, extract the path to **tasks**.
3. Get the Git remote by running:

```bash
git config --get remote.origin.url
```

> [!CAUTION]
> ONLY PROCEED TO NEXT STEPS IF THE REMOTE IS A GITHUB URL

4. For each task in the list, use the GitHub MCP server to create a new issue in the repository that is representative of the Git remote.

> [!CAUTION]
> UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT MATCH THE REMOTE URL

## Post-Execution Checks

<!-- include: .opencode/commands/_lib/hooks-preamble.md (HOOK_KEY=after_taskstoissues, HOOK_PHASE=Post, HOOK_TRIGGER=after reporting) -->
