---

name: requirements-analysis
description: Transform a user story into structured functional and non-functional requirements.
-----------------------------------------------------------------------------------------------

# Requirements Analysis Skill

## Purpose

Analyze the provided user story and create a structured `requirements.md` artifact for the next SDLC phase.

## Instructions

1. Read `user-story.md` from the repository root.
2. Identify the business goal and problem being addressed.
3. Identify the relevant actors and stakeholders.
4. Extract functional requirements and assign IDs using `FR-01`, `FR-02`, etc.
5. Extract non-functional requirements and assign IDs using `NFR-01`, `NFR-02`, etc.
6. Map the available acceptance criteria to the relevant functional requirements using Given/When/Then format.
7. Identify explicitly stated out-of-scope items.
8. Identify assumptions and open questions without inventing requirements.
9. Preserve the intent of the original user story.
10. Do not add requirements that are not supported by the user story.
11. Create or overwrite `requirements.md` in the repository root.
12. Ensure the generated document is clear and structured for downstream SDLC agents.

## Expected Result

Create `requirements.md` containing:

* Problem Statement
* Stakeholders
* Functional Requirements
* Non-Functional Requirements
* Acceptance Criteria
* Out of Scope
* Open Questions / Assumptions

## Quality Rules

* Use unique and sequential requirement IDs.
* Keep each requirement specific and testable where possible.
* Keep acceptance criteria traceable to the corresponding functional requirement.
* Mark information as `Not Specified` when it is not available.
* Do not make architecture, technology, or implementation decisions.
* Do not generate code or test cases.
