---
description: "Fetch Jira issue details, display them clearly, and create/update `user-story.md` in the repo root."
argument-hint: "Optional data for this workflow"
---

# Jira Requirements Fetcher

Read the Jira issue details, extract summary, description, acceptance criteria, and metadata, then write the final markdown to `user-story.md` and summarize the result.

## Guardrails
- Follow `CLAUDE.md` and the repo conventions.
- Do not assume approval without explicit user confirmation.
- Keep the work scoped to the current SDLC phase and the relevant artifacts.
- Produce a concise summary at the end.
