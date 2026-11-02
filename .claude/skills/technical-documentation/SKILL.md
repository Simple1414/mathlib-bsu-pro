---
name: technical-documentation
description: Technical documentation standards for README, docs/ (TECHNICAL_SPEC, ROADMAP, SECURITY_CHECKLIST), architecture decision records, runbooks, docstrings, and changelogs. Use when writing or updating any documentation, documenting a feature, or after changing setup, configuration, roles, or deployment.
---

# Technical Documentation

## When to activate
- A change alters setup steps, env vars, roles/permissions, deployment, or user-visible behavior.
- Writing ADRs, runbooks, API docs, docstrings.

## Language
- Existing docs (`README.md`, `docs/*`) are in **Tajik**; keep them in Tajik. Developer-facing additions (ADRs, CLAUDE.md, code comments) may be English. Do not mix languages within one document.

## What goes where
| Doc | Content |
|-----|---------|
| `README.md` | what it is, quick start, commands, project structure |
| `docs/TECHNICAL_SPEC.md` | roles, features, data model, business rules |
| `docs/SECURITY_CHECKLIST.md` | pre-production security gates |
| `docs/ROADMAP.md` | planned work |
| `docs/adr/NNNN-title.md` | architecture decisions: context, decision, consequences |
| `docs/runbooks/*.md` | deploy, backup/restore, incident steps |
| `.env.example` | every env var with safe placeholder and comment |

## Writing rules
- Lead with the task the reader wants to do; numbered steps; copy-pasteable commands that were actually run.
- State prerequisites and versions. Show expected output for verification steps.
- Keep docs next to the code change in the same PR.
- Docstrings: public functions/classes explain *why* and contract (args, returns, raises), not a restatement of code. Comments only for non-obvious reasoning.
- Diagrams: Mermaid in Markdown for flows (book submission → approval → publication).

## Security considerations
- Never include real passwords, keys, hostnames of internal systems, or personal data. Use `strong_password_here`-style placeholders and say so.

## Testing requirements
- Execute every documented command in a clean environment (or state that it was not verified).

## Checklist
- [ ] Correct doc updated in same change
- [ ] Commands verified
- [ ] `.env.example` updated for new env vars
- [ ] No secrets or personal data
- [ ] Consistent language per document
