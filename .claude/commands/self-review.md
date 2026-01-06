---
description: Pre-commit self-review
allowed-tools: Bash(git diff:*), Bash(git status:*)
---

# Self Review

Pre-commit self-review. Evaluate changes from an objective perspective.

## Goal

Find issues that I would want to fix if I noticed them.

## Instructions

### Step 1: Gather Changes

Run these commands to understand the changes:
- `git status` - see changed files
- `git diff --cached` - see staged changes (if empty, use `git diff`)

Identify the purpose and scope of the changes.

### Step 2: Review Against Criteria

Review the changes. Only report issues that meet ALL of these criteria:

**Must report if:**
- Introduced in THIS change (not pre-existing)
- Has meaningful impact on correctness, performance, security, or maintainability
- Is specific and actionable
- Does NOT demand rigor absent elsewhere in the codebase
- I would want to fix it if I knew about it

**Review for:**

**1. Correctness & Safety** (Critical - P0/P1):
- **Security**: secrets, vulnerabilities, input validation
- **Correctness**: logic errors, edge cases, unintended behavior
- **Resource Management**: file/connection leaks, proper cleanup

**2. Impact & Verification** (High - P1):
- **Breaking Changes**: API changes, backward compatibility, caller impact
- **Testing**: adequate test coverage, edge cases tested, existing tests pass

**3. Code Quality** (Medium - P2/P3):
- **Quality**: debug code, error handling
- **Documentation**: comments/docs match implementation
- **Reviewability**: naming clarity, complex logic explained, magic numbers
- **Performance**: obvious inefficiencies, N+1 queries

**4. Commit Quality** (Low - P2/P3):
- **Commit Scope**: focused changes, no unrelated modifications
- **Language**: no Japanese in code/comments unless intentional

**Ignore:**
- Trivial style issues that don't obscure meaning
- Pre-existing problems unrelated to this change
- Speculative "might be a problem" issues

### Step 3: Report Findings

If issues are found, report each with:

**Priority levels:**
| Priority | Meaning | Examples |
|----------|---------|----------|
| [P0] Critical | Blocker | Exposed secrets, security vulnerability, data loss risk |
| [P1] High | Must fix before commit | Obvious bugs, broken functionality |
| [P2] Medium | Should fix | Quality issues, missing error handling |
| [P3] Low | Consider | Nice-to-have improvements |

**For each issue, provide:**
- **Location**: file:line
- **Issue**: What is wrong (1 paragraph max, be specific)
- **Condition**: Under what conditions does this problem occur

### Step 4: Verdict

Provide final verdict:

- 🛑 **Blocked**: P0 found → Cannot commit, fix immediately
- ⚠️ **Fix Required**: P1 found → Fix before committing
- ✅ **Ready**: P2/P3 only or no issues → OK to commit

If issues exist, list them and suggest fixes.
