# Jira Issue: VNK-2 — Enable customers to search and filter products by category, material, size, and specifications for faster product discovery

**Direct Link**: [View in Jira](https://sonambavisetti.atlassian.net/browse/VNK-2)

## Metadata
| Field | Value |
|-------|-------|
| Issue Key | VNK-2 |
| Issue Type | Story |
| Status | To Do |
| Priority | Medium |
| Assignee | Not Available |
| Reporter | SONAM BAVISETTI |
| Labels | Not Available |
| Components | Not Available |
| Sprint | Not Available |
| Epic | Not Available |

## Description
Description:

As a business customer or dealer,I want to search for products by name, category, or specifications and filter results by material type (PVC/PP/Board), size, and customization options,so that I can quickly find the exact products I need without browsing the entire catalog.

Business Value

- Improves customer experience and product discovery
- Reduces time to find relevant products
- Increases enquiry conversions for targeted products
- Supports customers with large product catalogs
Technical Scope

- Frontend: Search input + filter dropdowns/checkboxes
- Backend: Search API endpoint with query parameters
- Database: Add indexes for product search optimization
- Testing: Unit tests + E2E tests with Playwright

## Acceptance Criteria
Acceptance Criteria:
 AC1 â€” Product Search Scenario: Customer searches for a product   Given the customer is on the Products page   When the customer enters "PVC File" in the search box   Then matching products should be displayed   And non-matching products should be hidden   And search results count should be displayed

 AC2 â€” Filter by Material Type Scenario: Customer filters products by material   Given the customer is on the Products page   When the customer selects "PVC" from the material filter   Then only PVC products should be displayed   And other material products should be hidden

 AC3 â€” Filter by Size Scenario: Customer filters products by size   Given the customer is viewing filtered products   When the customer selects size "A4" from the size filter   Then only products available in A4 size should be displayed

 AC4 â€” Combined Search and Filter Scenario: Customer uses search with filters   Given the customer has entered a search term   When the customer applies material and size filters   Then products matching both search term and filters should be displayed

 AC5 â€” Clear Filters Scenario: Customer clears all filters   Given the customer has applied multiple filters   When the customer clicks "Clear All Filters"   Then all products should be displayed   And all filter selections should be reset

 AC6 â€” No Results Handling Scenario: Search returns no results   Given the customer is on the Products page   When the customer searches for a product that doesn't exist   Then a "No products found" message should be displayed   And suggestions to clear filters should be shown

 AC7 â€” Mobile Responsive Search Scenario: Customer searches on mobile device   Given the customer is using a mobile device   When the customer uses search and filters   Then the search and filter controls should be easily accessible   And results should display properly on small screens

Labels: search, filters, product-discovery, frontend, backend

## Related Issues
Not Available

## Attachments & Links
Not Available

## Recent Comments
Not Available

---

## Notes
- Fetched read-only from Jira; no changes made to the issue.
- Assignee, components, sprint, epic, links, and comments were empty in Jira.
- Previous user-story.md (VNK-1) backed up under backups/.
