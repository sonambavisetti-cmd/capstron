---

name: implementation-planning
description: Break down an approved architecture into ordered, traceable implementation tasks.
----------------------------------------------------------------------------------------------

# Implementation Planning Skill

## Purpose

Create a concrete implementation plan from the approved architecture and documented requirements.

## Instructions

1. Read `architecture.md` from the repository root.
2. Read `requirements.md` from the repository root.
3. Use the architecture as the source of truth for implementation planning.
4. Identify the components, layers, modules, APIs, data models, and integrations that need to be implemented.
5. Break the architecture into small, actionable implementation tasks.
6. Assign each task a unique sequential ID such as `TASK-01`, `TASK-02`, etc.
7. Group tasks logically by component or layer.
8. Order tasks based on dependencies, placing foundational tasks before dependent tasks.
9. For every task, define:

    * Task description
    * Target files
    * Dependencies
    * Related FR/NFR
    * Definition of Done
10. Ensure every task is traceable to at least one FR or NFR whenever applicable.
11. Identify implementation risks and provide a mitigation for each significant risk.
12. Respect the project boundaries:

    * Python implementation files must be under `dev/`.
    * Playwright/TypeScript automation files must be under `test-automation/`.
13. Do not write or modify implementation code.
14. Do not introduce functionality that is not supported by the requirements or architecture.
15. Do not redesign or change the approved architecture.
16. Create or overwrite `impl-plan.md` in the repository root.

## Planning Rules

* Keep tasks specific enough for a developer to execute.
* Avoid combining unrelated implementation activities into one task.
* Ensure task dependencies are valid and logically ordered.
* Reference the exact expected file paths where possible.
* Use the FR/NFR IDs from `requirements.md`; do not invent requirement IDs.
* If a target file cannot be determined from the architecture, mark it as `To Be Determined` rather than inventing a structure.
* Include testing-related implementation tasks only when they are defined or implied by the approved architecture and requirements.
* Do not create tasks for architecture decisions that have already been finalized.

## Expected Result

Create `impl-plan.md` containing:

* Implementation summary
* Ordered task breakdown
* Task dependencies
* FR/NFR traceability
* Definition of Done for each task
* Execution order
* Risk register

The resulting plan must be detailed enough for the development phase to execute without requiring an architecture redesign.
