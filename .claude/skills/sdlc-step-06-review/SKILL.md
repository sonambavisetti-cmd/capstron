---

name: code-review
description: Review implemented Python code for plan and architecture conformance, security, quality, and maintainability, then apply only safe targeted fixes.
---------------------------------------------------------------------------------------------------------------------------------------------------------------

# Code Review Skill

## Purpose

Review the implemented production code under `dev/` against the approved `impl-plan.md` and `architecture.md`.

Identify defects, security vulnerabilities, plan or architecture deviations, and code-quality issues. Apply only safe, targeted fixes that do not change the intended business behavior.

## Review Process

### 1. Load Review Context

Read:

* `impl-plan.md`
* `architecture.md`
* All production code under `dev/`

If the user specifies files or TASK IDs, prioritize those areas but still check for critical issues that could affect the overall implementation.

### 2. Review Implementation Against the Plan

For each implementation task:

* Confirm the task has been implemented.
* Verify the implementation matches the task description.
* Verify the Definition of Done is satisfied.
* Check that required files and components exist.
* Identify missing, incomplete, or unrelated implementation.
* Check that task dependencies and execution order were respected.

Do not modify `impl-plan.md` to make the implementation appear compliant.

### 3. Review Architecture Conformance

Verify that the implementation follows `architecture.md`, including:

* Component responsibilities
* Component boundaries
* Data flow
* API design
* Data model
* Technology choices
* Security boundaries
* Configuration approach
* Error-handling approach

If the implementation conflicts with the architecture, report the conflict rather than redesigning the application.

### 4. Perform Security Review

Review every production file for relevant OWASP Top 10 risks, including:

* Injection vulnerabilities
* Broken authentication or authorization
* Sensitive data exposure
* Security misconfiguration
* Missing or inadequate input validation
* Unsafe handling of external data
* Path traversal
* Insecure file operations
* Hardcoded credentials, tokens, passwords, or API keys
* Unsafe error messages or logging of sensitive information
* Missing security controls required by the architecture

Use `validate_cves` when applicable to identify known dependency vulnerabilities.

### 5. Review Code Quality

Check for:

* PEP 8 violations
* Missing or inappropriate type hints
* Poor naming
* Unnecessary duplication
* Dead or unreachable code
* Unnecessary complexity
* Incorrect exception handling
* Missing boundary validation
* Inconsistent patterns
* Missing docstrings on public functions
* Unused imports or variables
* Obvious runtime errors

Focus on defects that materially affect correctness, security, maintainability, or compliance with the approved design.

### 6. Classify Findings

Classify each finding as:

* **BLOCKER** — Critical security vulnerability, broken functionality, data-loss risk, or defect that prevents the implementation from safely proceeding.
* **MAJOR** — Significant correctness, security, maintainability, or plan/architecture issue.
* **MINOR** — Low-impact style, readability, or maintainability issue.

Assign a unique finding ID such as `R-01`, `R-02`, etc.

### 7. Apply Safe Fixes

Apply targeted fixes directly in `dev/` only when the fix is:

* Clearly correct
* Localized
* Low risk
* Consistent with the approved architecture
* Not expected to change intended business behavior

Examples of appropriate fixes:

* Remove a hardcoded secret.
* Replace unsafe SQL construction with parameterized queries.
* Add missing input validation.
* Fix an obvious null/exception handling defect.
* Remove an unused import.
* Correct a clear PEP 8 issue.
* Add a missing type annotation.
* Correct an obvious security configuration issue.

Do not:

* Rewrite entire files.
* Refactor unrelated code.
* Add new business functionality.
* Change APIs or architecture.
* Modify requirements.
* Modify `architecture.md`.
* Modify `impl-plan.md`.
* Create test files.
* Change behavior merely to satisfy a style preference.

### 8. Verify Fixes

After applying fixes:

* Re-read the modified code.
* Check for syntax or static errors where possible.
* Run lightweight validation when appropriate.
* Confirm the fix did not introduce an obvious regression.
* Record exactly what was changed.

If a finding cannot be safely fixed without changing behavior or architecture, leave the code unchanged and report it under **Manual Action Required**.

## Review Output

Return a report using this structure:

```text
## Code Review Report

### Summary
<Overall assessment in 2–3 sentences>

### Findings

| ID | File | Line | Severity | Issue | Fix Applied? |
|----|------|------|----------|-------|-------------|
| R-01 | dev/... | 42 | BLOCKER | <issue> | Yes |
| R-02 | dev/... | 58 | MAJOR | <issue> | No |

### Auto-Fixed Items
- R-01: <what was fixed and why>
- R-03: <what was fixed and why>

### Manual Action Required
- R-02: <what must be addressed manually and why>

### Plan Conformance

| TASK | Implemented? | Notes |
|------|--------------|-------|
| TASK-01 | Yes | <notes> |
| TASK-02 | No | <missing implementation> |

### Architecture Conformance
- <Finding or confirmation>
- <Finding or confirmation>

### Security Checklist
- [x] No hardcoded secrets
- [x] External inputs validated
- [x] Injection risks reviewed
- [x] Authentication/authorization reviewed where applicable
- [x] Sensitive data handling reviewed
- [x] Error handling reviewed
- [x] Dependency vulnerabilities checked where applicable
- [x] OWASP Top 10 risks reviewed

### Review Status
<APPROVED / CHANGES REQUIRED>
```

## Gate Rule

Use:

* **APPROVED** when there are no unresolved BLOCKER or MAJOR findings.
* **CHANGES REQUIRED** when any BLOCKER or MAJOR finding remains unresolved.

The review status must reflect the actual findings and must not be changed merely because a fix was attempted.

Return the completed review report to the orchestrator for the Phase 6 gate.
