# Requirements: VNK-2 - Product Search and Filter

Source: user-story.md (Jira VNK-2, Story, Priority Medium, Status To Do)

## Problem Statement
Business customers and dealers must currently browse the whole product catalog to find products. They need to search by name, category, or specifications and filter by material type (PVC/PP/Board), size, and customization options so they can find the exact products quickly. Stated business value: better product discovery, less time to find products, more enquiry conversions for targeted products, support for large catalogs.

## Stakeholders
- Business customers (end users) - primary
- Dealers (end users) - primary
- Reporter: SONAM BAVISETTI
- Assignee: Not Specified
- Development / QA (frontend, backend, database, testing) - implied by Technical Scope

## Functional Requirements
- FR-01: The Products page shall provide a search input that searches products by name, category, or specifications. (AC1)
- FR-02: Matching products shall be displayed and non-matching products hidden; a search results count shall be displayed. (AC1)
- FR-03: The Products page shall provide a material type filter with options PVC, PP, and Board; selecting a value shows only products of that material and hides others. (AC2)
- FR-04: The Products page shall provide a size filter (e.g., "A4"); selecting a size shows only products available in that size, including when other filters are already applied. (AC3)
- FR-05: The Products page shall provide a filter for customization options. (Story text; no acceptance criterion; options Not Specified)
- FR-06: Search term and filters shall be combinable; results shall match the search term AND all applied filters. (AC4)
- FR-07: A "Clear All Filters" control shall reset all filter selections and display all products. (AC5)
- FR-08: When no products match, a "No products found" message shall be shown along with suggestions to clear filters. (AC6)
- FR-09: Search and filter controls shall be easily accessible on mobile devices, and results shall display properly on small screens. (AC7)
- FR-10: The backend shall expose a search API endpoint accepting query parameters for search and filters. (Technical Scope)
- FR-11: Database indexes shall be added to optimize product search. (Technical Scope)

## Non-Functional Requirements
- NFR-01: Responsiveness - the UI shall be usable on mobile and small screens (AC7).
- NFR-02: Performance - search shall be optimized via database indexes; numeric targets (response time, catalog size) Not Specified.
- NFR-03: Testability - unit tests and Playwright E2E tests shall be delivered (Technical Scope).
- NFR-04: Usability - users shall find products without browsing the full catalog; measurable criteria Not Specified.
- NFR-05: Security, accessibility, browser support, and rate limiting: Not Specified.

## Acceptance Criteria
- AC1 Search: On the Products page, entering "PVC File" displays matching products, hides non-matching ones, and shows a results count.
- AC2 Material filter: Selecting "PVC" shows only PVC products and hides other materials.
- AC3 Size filter: While viewing filtered products, selecting size "A4" shows only products available in A4.
- AC4 Combined: With a search term entered, applying material and size filters shows products matching both the term and filters.
- AC5 Clear: With multiple filters applied, clicking "Clear All Filters" shows all products and resets all filter selections.
- AC6 No results: Searching for a nonexistent product shows a "No products found" message and suggestions to clear filters.
- AC7 Mobile: On a mobile device, search and filter controls are easily accessible and results display properly on small screens.

Traceability: AC1 -> FR-01, FR-02; AC2 -> FR-03; AC3 -> FR-04; AC4 -> FR-06; AC5 -> FR-07; AC6 -> FR-08; AC7 -> FR-09, NFR-01.

## Out of Scope
Not explicitly stated in the story. Items not mentioned and therefore not captured: sorting, pagination, autocomplete/suggestions while typing, saved searches, search analytics, and changes to the enquiry/quote flow.

## Open Questions / Assumptions
1. Customization options (FR-05): which options exist, and what are the filter values? No acceptance criterion covers it.
2. Search matching: is it case-insensitive, partial/substring, multi-term, or fuzzy? Which fields count as "specifications"?
3. Does search/filter run instantly on input or on submit? Is debouncing expected? Not Specified.
4. Size filter: which sizes are available (only A4 given)? Single-select or multi-select? Can the material filter be multi-select?
5. Do filter options come from catalog data or a fixed list? Category filter: the title mentions category, but the filter list in the story names only material, size, and customization; is a category filter required?
6. "Suggestions to clear filters" (AC6): exact wording and form Not Specified.
7. Should filter/search state persist in the URL (shareable/back button)? Not Specified.
8. Mobile breakpoint and layout (e.g., collapsible filter panel) Not Specified.
9. Performance targets and catalog size Not Specified.
10. Assumption: the existing Products page is the place for these features; the story refers to "the Products page" as existing.
11. Assumption: the Jira label list (search, filters, product-discovery, frontend, backend) is informational only; the metadata table shows Labels as Not Available.
