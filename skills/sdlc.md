---
description: "Run the SDLC flow end-to-end with explicit approval gates."
argument-hint: "Optional data for this workflow"
---

# SDLC Orchestrator

Coordinate the full pipeline and hand off each phase to the matching agent. Require explicit approval before each transition and stop after the required gate output is ready.

## Guardrails
- Follow `CLAUDE.md` and the repo conventions.
- Do not assume approval without explicit user confirmation.
- Keep the work scoped to the current SDLC phase and the relevant artifacts.
- Produce a concise summary at the end.
