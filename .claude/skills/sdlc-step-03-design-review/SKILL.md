---

name: design-review
description: Review system architecture for requirements alignment, security, reliability, maintainability, and design risks.
-----------------------------------------------------------------------------------------------------------------------------

# Design Review Skill

## Purpose

Review `architecture.md` against `requirements.md` and identify design gaps, risks, and issues that must be addressed before implementation.

## Instructions

1. Read `requirements.md` from the repository root.
2. Read `architecture.md` from the repository root.
3. Compare the architecture against all documented functional and non-functional requirements.
4. Review the architecture using these areas:

    * Requirements coverage
    * Security and data protection
    * Authentication and authorization
    * Secrets management
    * Input validation
    * Scalability
    * Reliability and failure handling
    * Maintainability
    * Testability
    * API and integration design
    * Data model and storage
    * Technology choices
    * ADR completeness
    * Project folder and language boundaries
5. Identify every significant issue or risk.
6. Assign a severity to every finding:

    * **P0** — Security vulnerability or significant data-loss risk. Blocks approval.
    * **P1** — Critical requirements, scalability, reliability, or architecture gap. Blocks approval.
    * **P2** — Design or maintainability concern. Does not block approval.
    * **P3** — Minor improvement or style suggestion. Does not block approval.
7. Provide a clear recommendation for every finding.
8. Do not rewrite or modify `architecture.md`.
9. Do not create implementation code or other artifacts.
10. Approve the architecture only when there are no unresolved P0 or P1 findings.
11. Reject the architecture when one or more unresolved P0 or P1 findings exist.
12. Create or overwrite `design-review.md` in the repository root.

## Review Rules

* Every FR and NFR should be checked for architectural coverage.
* Do not invent requirements during the review.
* Distinguish actual architecture gaps from optional improvements.
* P0/P1 findings must contain enough detail for the architecture agent to understand what needs to be corrected.
* P2/P3 findings should not cause rejection.
* Verify that every major architecture decision has an ADR where appropriate.
* Verify that the architecture respects:

    * `dev/` for Python application code
    * `test-automation/` for Playwright/TypeScript automation

## Verdict Rules

Use:

`APPROVE` when there are no unresolved P0 or P1 findings.

`REJECT` when one or more unresolved P0 or P1 findings exist.

## Expected Result

Create `design-review.md` containing:

* Verdict
* Review summary
* Findings with severity
* Requirements coverage
* Security checklist
* Approval conditions for rejected designs

The review must provide actionable feedback that can be consumed by the Phase 2 Architecture Agent during a re-loop.
