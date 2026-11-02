---
name: git-github-workflow
description: Git and GitHub workflow conventions — branching, commit messages, pull requests, code review etiquette, and repository hygiene. Use when committing, creating branches or PRs, writing PR descriptions, resolving conflicts, or setting up branch protection. The commit-commands plugin provides /commit and /commit-push-pr shortcuts.
---

# Git & GitHub Workflows

## When to activate
- Before committing, branching, opening/updating a PR, or resolving conflicts.

## Branching
- `main` is always deployable. Work on short-lived branches: `feat/…`, `fix/…`, `refactor/…`, `docs/…`, `chore/…`.
- Rebase your own branch onto `main` before PR; never rewrite history on shared branches; never force-push `main`.

## Commits
- Atomic: one logical change; migrations committed with the model change that needs them.
- Message: imperative subject ≤ 72 chars (`Enforce POST on book approval`), blank line, body explaining *why* and any risk.
- Optional Conventional Commit prefix (`fix:`, `feat:`) — be consistent within a branch.
- Before committing: `git diff --staged` review, `python manage.py check`, tests for touched areas.
- Never commit: `.env`, credentials, `media/`, `staticfiles/`, `db.sqlite3`, large binaries. If a secret is committed, rotate it immediately.

## Pull requests
- Small (< ~400 lines changed where possible). Title = what; description = why, how, test evidence, screenshots for UI, migration notes, rollback notes.
- Checklist in description: tests added, `check` passes, migrations reviewed, security impact considered.
- Review tools: `/code-review` (built-in), `/code-review:code-review` (plugin), `/pr-review-toolkit:review-pr`.
- Respond to every review comment; resolve only after addressing.

## Repository hygiene (recommended)
- Branch protection on `main`: required PR review, required CI checks, no force push.
- `.github/pull_request_template.md`, `CODEOWNERS`, Dependabot for pip and GitHub Actions.

## Security considerations
- Review diffs for secrets before every push; consider GitHub secret scanning + push protection.

## Checklist
- [ ] Branch named by type
- [ ] Atomic commits with clear messages
- [ ] No secrets/generated files staged
- [ ] Checks/tests run and reported
- [ ] PR description complete
