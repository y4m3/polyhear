# Global Instructions

## Language
- Respond in Japanese unless otherwise specified
- Code comments in English
- Commit messages in English, Conventional Commits format

## Code Style
- Prefer explicit over implicit
- No abbreviations in variable names except well-known ones (e.g., idx, ctx)
- Error handling: fail fast, explicit error messages

## Workflow
- Before modifying files, briefly explain the change
- Run lint/format after code changes when available
- Commit granularly (one logical change per commit)
- Perform a self-review before committing

## Constraints
- Do not use `sudo` without explicit approval
- Do not modify files outside the project directory without asking
- Do not generate placeholder/dummy implementations without noting them

## Reasoning
- For complex tasks, outline approach before implementation
- When uncertain, ask clarifying questions rather than assuming

## Git Worktree
- Worktree location: `../<repo-name>-worktree/<branch-name>/`
- Replace `/` in branch names with `-` for directory names
