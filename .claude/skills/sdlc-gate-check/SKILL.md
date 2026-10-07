---
name: sdlc-gate-check
description: >
  Use when: checking the current gate status of the SDLC pipeline — which phase
  artifacts exist, which are empty, and what the next step should be.
  Triggers: "sdlc status", "what phase am I in", "check gate", "sdlc resume check",
  "which artifacts exist", "pipeline state".
---

# SDLC Gate Check Skill

Inspects the workspace to determine the current SDLC pipeline state and the next required action.

## Steps

1. Check which artifact files exist and are non-empty:
   - `user-story.md`
   - `requirements.md`
   - `architecture.md`
   - `design-review.md`
   - `impl-plan.md`
   - `dev/` (any Python files)
   - `test-automation/` (any test files)
   - `CHANGELOG.md`

2. Map findings to pipeline phase:

| Condition | Last Completed Phase | Next Action |
|-----------|---------------------|-------------|
| No artifacts found | None | Start Phase 1: `@sdlc-step-01-requirements` |
| `requirements.md` exists | Phase 1 | Start Phase 2: `@sdlc-step-02-architecture` |
| `architecture.md` exists | Phase 2 | Start Phase 3: `@sdlc-step-03-design-review` |
| `design-review.md` exists with APPROVE verdict | Phase 3 | Start Phase 4: `@sdlc-step-04-impl-plan` |
| `design-review.md` exists with REJECT verdict | Phase 3 (rejected) | Re-run Phase 2: `@sdlc-step-02-architecture` |
| `impl-plan.md` exists | Phase 4 | Start Phase 5: `@sdlc-step-05-implementation` |
| `dev/` has Python files | Phase 5 | Start Phase 6: `@sdlc-step-06-review` |
| Review complete (confirmed in chat) | Phase 6 | Start Phase 7: `@sdlc-step-07-verify` |
| `test-automation/` has test files | Phase 7 | Start Phase 8: `@sdlc-step-08-pr` |
| `CHANGELOG.md` updated | Phase 8 | Pipeline complete ✅ |

3. Output a gate status table and the recommended next command.

## Skill Invocation

- When determining the next step, invoke supporting skills (for example `sdlc-step-01-requirements` and `clarifying-scenarios`) as needed to enrich the pipeline context and help resolve ambiguous or incomplete artifacts before recommending a phase.
## Output Format

```
## SDLC Pipeline Status

| Phase | Name | Artifact | Status |
|-------|------|----------|--------|
| 1 | Requirements | requirements.md | ✅ Complete |
| 2 | Architecture | architecture.md | ✅ Complete |
| 3 | Design Review | design-review.md | ✅ APPROVED |
| 4 | Impl Plan | impl-plan.md | ⏳ Missing |
| 5 | Implementation | dev/ | ⏳ Waiting |
| 6 | Review | (chat) | ⏳ Waiting |
| 7 | Verify | test-automation/ | ⏳ Waiting |
| 8 | PR | CHANGELOG.md | ⏳ Waiting |

**Current gate**: Phase 3 approved
**Next action**: `@sdlc-step-04-impl-plan` or `@sdlc from=impl-plan`
```
