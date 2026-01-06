---
description: Conventional Commits workflow with self-review
allowed-tools: Bash(git:*)
---

# Commit Command

Create well-structured commits following Conventional Commits format.
Automatically handles both single and multiple commit scenarios.

## Workflow

### Step 0: Check Preconditions

1. Run `git status` to check for changes
2. If no changes: Report "No changes to commit." and **stop**
3. Note if this is a new repo (no commits yet) for Step 1

### Step 1: Analyze Changes

1. Unstage everything: `git reset HEAD` (skip if new repo with no commits)
2. Run `git status` to see all changed and untracked files
3. Run `git diff` to review modifications (tracked files only)
4. Check recent commits for style: `git log --oneline -5` (skip if new repo)
   - If no commits or inconsistent style, follow Conventional Commits format

**Handle untracked files:**
If untracked files exist, list them and ask:
```
Untracked files found:
- path/to/file1
- path/to/file2

[A]ll include / [I]nclude each / [G]itignore / [S]kip all
```

**On [I]nclude each:**
For each file: `[filename] - [I]nclude / [G]itignore / [S]kip?`
After all files: add [G]itignore selections to .gitignore, include .gitignore in commit.

**On [G]itignore:**
1. Ask which files/patterns to add
2. Append to .gitignore (create if needed)
3. Include .gitignore changes in commit
4. For remaining untracked files: re-prompt with [A]ll / [I]nclude each / [S]kip all

**After handling untracked files:**
If no files remain to commit (all skipped and no tracked changes): Report "No files to commit." and stop.

### Step 2: Self-review (Recommended)

Before proposing commits, offer self-review:

```
Found [N] changed files. Run self-review first? (yes/no)
```

- **yes**: Follow the criteria in `self-review.md`
  - If file not found: Basic review (security, correctness, no debug code)
  - If P0/P1 issues found: **STOP**, report issues, ask user to fix first
  - If P2/P3 or clean: Proceed to Step 3
- **no**: Warn "Proceeding without self-review. Issues may require amending later." and proceed

### Step 3: Determine Commit Strategy

Evaluate these split criteria:

**Consider splitting when ANY apply:**
1. Different commit types are mixed (feat + fix, refactor + feat, etc.)
2. Multiple independent features/fixes that don't depend on each other
3. Tests for pre-existing code (not for the new feature being added)
4. Documentation files (README, docs/) mixed with code changes

**Keep together:**
- feat + test for the SAME feature (common practice)
- Inline code comments with their related code changes

**Result:** If no split criteria apply → single commit

### Step 4: Present Commit Plan & Get Approval

**Format for Single Commit:**
```
=== Commit Plan: Single Commit ===

Rationale: [Why one commit is appropriate]

Proposed:
  type(scope): subject (max 50 chars)

  Body: [Why this change, if non-obvious]

Files ([N]):
- path/to/file1
- path/to/file2

[Y]es, commit / [M]odify / [C]ancel
```

**On [M]odify (Single Commit):**
Ask for new commit message, update plan, re-show for approval.

**On [C]ancel:**
Report "Commit cancelled. All changes remain unstaged." and stop.

**Format for Multiple Commits:**
```
=== Commit Plan: [N] Commits ===

Rationale: [Why splitting improves clarity]

Sequence:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. type(scope): subject
   Why: [Rationale for this commit]
   Files: [list]

2. type(scope): subject
   Why: [Rationale for this commit]
   Files: [list]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[A]ll at once / [O]ne by one / [M]odify / [C]ancel
```

**On [O]ne by one:**
For each commit, show "Commit [N]/[Total]: message" then:
- [Y]es: Execute and continue
- [S]kip: Skip this commit (files remain unstaged), continue to next
- [A]bort: Stop, show summary of completed commits. Remaining changes stay unstaged.

**On [M]odify (Multiple Commits):**
```
What would you like to change?
1. Commit message(s)
2. File grouping
3. Commit order
4. Merge commits
5. Split a commit
```

After user selects:
1. → Ask for new message, update plan
2. → Show files, ask how to regroup
3. → Show order, ask new sequence
4. → Ask which commits to merge
5. → Ask which commit and how to split

Then re-show updated plan for approval.

**On [C]ancel:**
Report "Commit cancelled. All changes remain unstaged." and stop.

### Step 5: Execute Commits

**For each commit:**
1. Stage files: `git add [files]`
2. Create commit:
   - Subject only: `git commit -m "type(scope): subject"`
     - If subject contains `"`, `$`, or backticks: use HEREDOC instead
   - With body/footer: Use HEREDOC (no leading spaces in message):

```bash
git commit -m "$(cat <<'EOF'
type(scope): subject

Body explaining WHY (if needed).

BREAKING CHANGE: description (if applicable)
Refs: #123 (if applicable)
EOF
)"
```

3. Confirm: `✓ [hash] type(scope): subject`

**After all commits:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary: Created [N] commit(s)

✓ [hash] commit message
✓ [hash] commit message
⊘ [skipped] commit message (files unstaged)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next steps:
- Review: git log --oneline -[N]
- Push: git push origin [branch]
- Undo: git reset --soft HEAD~[N] (before push only)
```

## Error Handling

- **Pre-commit hook fails**: Report error verbatim. Options:
  - [R]etry: User fixes the issue, then re-run `git commit` (files stay staged)
  - [S]kip hook: Use `--no-verify` (skips ALL hooks - use with caution)
  - [A]bort: Stop, show summary of completed commits. Remaining changes stay unstaged.
- **Staging fails**: Report which files failed. Options:
  - [S]kip file: Exclude from this commit (file stays unstaged), continue staging other files in this commit
  - [A]bort: Stop, show summary. Remaining changes stay unstaged.
  - If all files in a commit are skipped: treat as skipped commit, continue to next.
- **Any git error**: Stop immediately, show error, ask user how to proceed.

## Commit Message Guidelines

### Format
```
type(scope): subject (max 50 chars, imperative mood)

Optional body explaining WHY (wrap at 72 chars).
Focus on motivation and context, not what changed.

Optional footer for breaking changes or issue refs.
```

### Types
| Type | Use for |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code restructuring (no behavior change) |
| `test` | Adding or modifying tests |
| `chore` | Maintenance (deps, config, build) |
| `perf` | Performance improvement |

**Breaking changes**: Add "!" before ":" — e.g., `feat!:`, `feat(scope)!:`

### Scope
- Use component/module name: `auth`, `api`, `cli`
- Use directory name if no clear component: `utils`, `config`
- Omit for global changes: `chore: update dependencies`

### Checklist
- ✓ Imperative mood: "add" not "added" or "adds"
- ✓ No period at end of subject
- ✓ Body explains WHY when non-obvious
- ✓ `BREAKING CHANGE:` footer for breaking changes
- ✓ `Refs: #123` when applicable

## Examples

### Single Commit (Feature with Tests)
```
feat(api): add user search endpoint

Enables frontend to search users by name or email.
Required for the new admin dashboard.

Refs: #456
```

### Multiple Commits (Refactor then Feature)
```
Commit 1:
refactor(auth): extract token validation logic

Commit 2:
feat(auth): add session refresh endpoint
Uses the extracted validation logic.
```

### Multiple Commits (Feature + Docs)
```
Commit 1:
feat(export): add data export API endpoint
Includes implementation and tests.

Commit 2:
docs(export): document export API usage
```

### Breaking Change
```
feat(api)!: change response format to camelCase

Previous snake_case caused client-side confusion.
Aligns with JavaScript conventions.

BREAKING CHANGE: API responses now use camelCase.
Clients must update parsing logic.

Refs: #789
```

## Notes

- **AI Attribution**: Do NOT mention AI in commit messages. Focus on WHAT and WHY.
- **Atomic Commits**: Each commit should leave code working. If unavoidable, warn user.
- **Commit Size**: Prefer smaller, focused commits over large mixed changes.
