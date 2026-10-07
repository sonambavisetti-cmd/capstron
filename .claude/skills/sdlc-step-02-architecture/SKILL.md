---

name: architecture-design
description: Design a system architecture from structured requirements and document major architecture decisions.
-----------------------------------------------------------------------------------------------------------------

# Architecture Design Skill

## Purpose

Analyze `requirements.md` and create a clear, traceable system architecture that satisfies the documented requirements.

## Instructions

1. Read `requirements.md` from the repository root.
2. If `design-review.md` is available, read it and address every rejection or review comment.
3. Map the functional and non-functional requirements to the proposed architecture.
4. Define the major system components, modules, services, and layers.
5. Define the responsibility of each component and how components interact.
6. Define the data model, entities, relationships, and storage approach.
7. Define the required API endpoints, events, or external integrations.
8. Select the technology stack based on the requirements and document the rationale for each major choice.
9. Identify authentication, authorization, data protection, and other relevant security considerations.
10. Identify scalability, availability, reliability, and failure-handling considerations where applicable.
11. Record every significant architecture decision as an ADR.
12. Ensure the architecture does not introduce functionality outside the documented requirements.
13. Respect the project boundaries:

    * Python application code belongs in `dev/`.
    * Playwright/TypeScript test automation belongs in `test-automation/`.
14. Do not generate implementation code.
15. Do not create `impl-plan.md`.
16. Create or overwrite `architecture.md` in the repository root.
17. Ensure the architecture is understandable and actionable for downstream development and QA agents.

## Traceability Rules

* Every major functional requirement should be addressed by at least one architecture component or interaction.
* Non-functional requirements should be reflected in the relevant architecture decisions.
* Major technology or design choices must have a corresponding ADR.
* Do not invent requirements to justify an architecture decision.
* Clearly identify assumptions where the requirements do not provide enough information.

## ADR Rules

For each significant architecture decision, document:

* **Status**
* **Context**
* **Decision**
* **Consequences**

Use sequential IDs such as `ADR-01`, `ADR-02`, etc.

## Expected Result

Create `architecture.md` containing:

* Architecture Overview
* Component Diagram
* Components and Responsibilities
* Data Model
* API / Integration Surface
* Technology Stack and Rationale
* Security Considerations
* Scalability and Reliability
* Architecture Decision Records
