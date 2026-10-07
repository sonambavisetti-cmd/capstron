# Requirements

## Short summary
Build a customer-facing website for "Vinayaka File Works" that presents company information and branding, shows a product catalog, supports adding items to a cart and placing orders (Cash on Delivery or Online payment), and generates downloadable PDF invoices matching the provided sample bill layout. Source: user-story.md in repository (VNK-1). Attempted live Jira REST API returned 404; content used is the local user-story.md export.

## Problem Statement
Customers of Vinayaka File Works need a simple, trustworthy storefront where they can browse available products, view prices and availability, place orders using Cash on Delivery or an online payment option, and download a PDF invoice that matches the supplied bill layout. The business needs to receive, view, and mark orders as processed without exposing secrets in the repository.

## Stakeholders
| Role | Responsibility |
|------|---------------|
| Customer | Browse products, add items to cart, place orders, and download invoices |
| Business owner / staff | Provide product data, review incoming orders, and fulfil customer orders |
| Admin user | Review and update order status (mark processed) and access order records |
| Developer | Implement storefront, checkout flow, invoice generation, and admin capabilities |
| Payment provider (if used) | Process online payments in a secure and testable manner |

## Functional Requirements
| ID | Description | Priority |
|----|-------------|----------|
| FR-01 | Homepage displays the company name "Vinayaka File Works", logo, full postal address, and contact number. | High |
| FR-02 | Product listing page shows products with name, SKU, image (if available), unit price, and available quantity. | High |
| FR-03 | Customer can add products to a cart and review items (quantities and pricing) before checkout. | High |
| FR-04 | Checkout captures customer contact and delivery information and allows selection of Cash on Delivery or Online payment. | High |
| FR-05 | System validates required inputs (customer details, delivery address, payment selection) and surfaces clear error messages for invalid or missing fields. | High |
| FR-06 | On successful order submission the system persists the order and shows a confirmation to the customer including an order reference. | High |
| FR-07 | System generates a downloadable PDF invoice matching the supplied sample bill fields: invoice number, date, customer details, itemized list, totals, and company details. | High |
| FR-08 | Admin interface or a protected admin endpoint allows viewing submitted orders and marking them as processed. | Medium |
| FR-09 | Repository and codebase do not contain secrets (API keys); configuration is provided through environment variables. | High |

## Non-Functional Requirements (Success Metrics)
| ID | Description | Metric |
|----|-------------|--------|
| NFR-01 | Responsive user interface for desktop and mobile use. | Pages render and remain usable at common mobile/desktop breakpoints (manual UAT). |
| NFR-02 | PDF invoice layout consistency with the provided sample. | Invoice contains required fields and visually follows sample layout (manual verification). |
| NFR-03 | Basic input validation and access control for admin functions. | Validation prevents common injection/invalid input; admin pages require authentication. |
| NFR-04 | Product listing performance under typical load. | Typical product listing requests respond in under 500 ms (measured in dev/staging). |
| NFR-05 | No credentials stored in repository. | CI or local runs must succeed using environment variables; scans show no secrets. |

## Acceptance Criteria
### FR-01: Homepage displays company information
- Given a customer opens the website homepage
- When the page loads
- Then the company name "Vinayaka File Works", logo, full postal address, and contact number are visible.

### FR-02: Product catalog is shown to customers
- Given a customer visits the product listing page
- When the page loads
- Then each product displays: name, SKU, image (or placeholder), unit price, and available quantity.

### FR-03: Customer can add items to cart
- Given a customer is viewing products
- When they add one or more products to the cart and view the cart
- Then the cart shows the selected products with correct quantities, unit prices, and a subtotal.

### FR-04: Customer can checkout and choose payment method
- Given a customer has items in the cart
- When they submit contact and delivery details and choose either Cash on Delivery or Online payment
- Then the system accepts the order if inputs are valid and returns an order reference; if payment is selected and succeeds, the order is completed.

### FR-05: Invalid inputs are handled gracefully
- Given a customer submits incomplete or invalid order details
- When required fields are missing or invalid
- Then the system shows clear, actionable validation messages and does not create an order.

### FR-06: Order confirmation is shown after successful purchase
- Given a valid order is submitted
- When the order is persisted
- Then the customer sees an order confirmation page or message including the order reference and next steps.

### FR-07: PDF invoice is generated for the order
- Given an order is successfully placed
- When the user requests or the system generates the invoice
- Then a downloadable PDF invoice is produced containing invoice number, date, customer details, itemized line items, totals, and company details matching the sample bill fields.

### FR-08: Admin can process orders
- Given an admin user accesses the admin/orders view
- When they view an order
- Then they can mark the order as processed and see the updated status.

### FR-09: Secrets are not committed to the repository
- Given the repository is prepared for development or deployment
- When configuration is required
- Then credentials are supplied via environment variables and no secrets are present in source control.

## Out of Scope
- Native mobile applications (this ticket covers a web storefront only)
- Advanced inventory forecasting, warehouse management, or ERP integrations
- Email-based order notifications (not required by the current user story)
- Detailed payment provider selection and deep payment customization (payment provider choice is out-of-scope; integration can be isolated to a sandbox/mock for initial delivery)

## Open Questions / Assumptions
- Payment provider: Which online payment gateway should be used in production? (open)
- Confirm the final, authoritative company postal address and contact phone number to display on the site and invoice. (open)
- Invoice PDF exact styling: the sample bill is provided but final font/spacing decisions need confirmation. (assumption: match fields and general layout; exact styling may be iterated)
- Admin authentication: method and user management are not specified; assume a protected admin interface or simple endpoint with basic auth until requirements are provided. (assumption)
- Provided assets: repository indicates a company logo and a sample bill screenshot are available; confirm high-resolution logo and source for invoice template if precise matching is required. (open)


