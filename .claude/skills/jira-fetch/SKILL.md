---

name: jira-fetch
description: Fetch and format requirements from a Jira issue.
-------------------------------------------------------------

# Jira Fetch Skill

## Purpose

Retrieve the requirement details from a Jira issue and create the requirement artifact for downstream agents.

## Instructions

1. Get the Jira issue key or URL from the user.
2. Use the available Jira/MCP tools to retrieve the issue.
3. Extract the requirement information, including:

    * Summary
    * Description
    * Acceptance criteria
    * Status
    * Priority
    * Assignee
    * Labels
    * Components
    * Related issues, if available
4. Preserve the requirement meaning without adding or changing business requirements.
5. Format the information as Markdown.
6. Save the formatted requirement to `user-story.md` in the repository root.
7. Overwrite the existing `user-story.md` when it already exists.
8. If information is unavailable, mark it as `Not Available`.
9. Do not modify the Jira issue.
10. Do not create code, test cases, or implementation decisions.

## Expected Result

A `user-story.md` file containing the latest Jira requirement in a clear, structured Markdown format.
