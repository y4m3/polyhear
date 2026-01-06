---
description: PR review response workflow
allowed-tools: mcp__github__*, Bash(gh:*)
---

# PR Review Response Workflow

## Target PR

- If PR number is provided as argument, use PR #$ARGUMENTS
- If no argument, use the PR associated with the current branch

## Process

1. First, check if there are any unresolved or new review comments
   - Use `gh pr view` to get basic PR status
   - If no pending reviews or new comments, report "No new review comments" and stop

2. If new comments exist, fetch full review details and for each comment:
   - Reviewer name
   - Comment content (quote briefly)
   - File and line location
   - Whether it's a thread or standalone comment

3. Assess each comment:
   - Action needed: yes / no / needs discussion
   - Priority: high (blocking) / medium (should fix) / low (suggestion)
   - Proposed response or code change

4. Present the prioritized summary and wait for my confirmation before making any changes
