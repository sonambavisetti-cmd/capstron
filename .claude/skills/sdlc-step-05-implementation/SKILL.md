---

name: implementation
description: Execute the approved implementation plan and create production-ready Python code.
----------------------------------------------------------------------------------------------

# Implementation Skill

## Purpose

Execute the approved `impl-plan.md` and implement the planned functionality using the architecture as the source of truth.

## Instructions

1. Read `impl-plan.md` from the repository root.
2. Read `architecture.md` to understand the approved design.
3. Execute tasks in the defined execution order.
4. For each task:

    * Read the existing target files, if any.
    * Implement the functionality described by the task.
    * Create or modify only the files specified by the implementation plan where possible.
    * Verify the task's Definition of Done.
5. Keep implementation aligned with the approved architecture.
6. Implement only functionality supported by the requirements and implementation plan.
7. Keep all production Python code under `dev/`.
8. Do not create or modify test files; test automation is handled by Phase 7.
9. Use environment variables for credentials and secrets.
10. Never hardcode passwords, API tokens, keys, or other secrets.
11. Validate external inputs and handle errors appropriately.
12. Follow Python best practices and PEP 8.
13. Use type hints for Python code.
14. Do not modify `requirements.md`, `architecture.md`, `design-review.md`, or `impl-plan.md`.
15. Do not redesign the architecture during implementation.
16. If a task cannot be implemented because of a missing dependency, unclear requirement, or architecture issue, stop that task and clearly report the blocker.
17. After implementation, report completed and blocked tasks.

## Implementation Rules

* Follow the task dependencies defined in `impl-plan.md`.
* Do not silently skip tasks.
* Do not introduce unrelated features or refactoring.
* Reuse existing project structure and components when appropriate.
* Keep changes focused on the current task.
* Verify that the implementation satisfies the task's Definition of Done.
* If implementation requires a decision that conflicts with `architecture.md`, report the conflict instead of changing the architecture.

## Expected Result

Production-ready Python implementation under `dev/` that satisfies the approved implementation plan.

Provide a completion report containing:

* Completed tasks
* Blocked or skipped tasks
* Files created or modified
* Any blockers
* Any deviations or required architecture clarification
