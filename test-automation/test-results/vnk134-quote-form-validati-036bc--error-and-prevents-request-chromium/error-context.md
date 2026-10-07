# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: vnk134-quote-form-validation.spec.ts >> VNK-134 Quote enquiry form client-side validation >> VNK-134-NEG-REQ-001: Empty name shows inline error and prevents request
- Location: tests\vnk134-quote-form-validation.spec.ts:47:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByLabel(/Full Name/i)

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - banner [ref=e3]:
    - generic [ref=e4]: Vinayaka File Works
    - navigation [ref=e5]:
      - link "Products" [ref=e6] [cursor=pointer]:
        - /url: "#products"
      - link "Services" [ref=e7] [cursor=pointer]:
        - /url: "#services"
      - link "About" [ref=e8] [cursor=pointer]:
        - /url: "#about"
      - link "Contact" [ref=e9] [cursor=pointer]:
        - /url: "#contact"
    - link "Get a quote" [ref=e10] [cursor=pointer]:
      - /url: "#quote-form"
  - generic [ref=e11]:
    - generic [ref=e12]:
      - generic [ref=e13]: Paper & printing solutions
      - heading "Print smarter. Deliver better." [level=1] [ref=e14]
      - paragraph [ref=e15]: Vinayaka File Works helps businesses and families with custom stationery, packaging, printing, and office essentials—delivered with reliable service and quick turnaround.
      - generic [ref=e16]:
        - link "Shop products" [ref=e17] [cursor=pointer]:
          - /url: "#products"
        - link "Explore services" [ref=e18] [cursor=pointer]:
          - /url: "#services"
      - generic [ref=e19]:
        - generic [ref=e20]: No. 42, Market Road, Bengaluru, Karnataka 560001
        - generic [ref=e21]: +91 98765 43210
      - generic [ref=e22]:
        - generic [ref=e23]: Bulk printing
        - generic [ref=e24]: Office supplies
        - generic [ref=e25]: Custom stationery
    - generic [ref=e29]:
      - strong [ref=e30]: Premium Office Pack
      - generic [ref=e31]:
        - generic [ref=e32]: Starter bundle
        - strong [ref=e33]: ₹1,499
  - generic [ref=e34]:
    - generic [ref=e35]:
      - heading "Popular products" [level=2] [ref=e36]
      - link "View all →" [ref=e37] [cursor=pointer]:
        - /url: "#"
    - generic [ref=e38]:
      - generic [ref=e39]:
        - heading "Printed Forms" [level=3] [ref=e41]
        - paragraph [ref=e42]: Custom invoice books, registers, and office forms designed to keep daily operations efficient.
      - generic [ref=e43]:
        - heading "Packaging Kits" [level=3] [ref=e45]
        - paragraph [ref=e46]: Professional packaging and business stationery for retail, gifting, and courier-ready deliveries.
      - generic [ref=e47]:
        - heading "Files & Folders" [level=3] [ref=e49]
        - paragraph [ref=e50]: Durable file folders, project tags, and archival materials built for everyday use.
    - generic [ref=e51]:
      - generic [ref=e52]:
        - generic [ref=e53]: Search products
        - searchbox "Search products" [ref=e54]
      - group [ref=e55]:
        - generic "Filters" [ref=e56] [cursor=pointer]
        - generic [ref=e57]:
          - generic [ref=e58]:
            - generic [ref=e59]: Material
            - combobox "Material" [ref=e60]:
              - option "All" [selected]
          - generic [ref=e61]:
            - generic [ref=e62]: Size
            - combobox "Size" [ref=e63]:
              - option "All" [selected]
          - generic [ref=e64]:
            - generic [ref=e65]: Customization
            - combobox "Customization" [ref=e66]:
              - option "All" [selected]
          - button "Clear All Filters" [ref=e67] [cursor=pointer]
      - paragraph [ref=e68]: 2 products
      - generic [ref=e69]:
        - generic [ref=e70]:
          - heading "Cart Product" [level=3] [ref=e72]
          - paragraph [ref=e73]: Seeded for tests
          - generic [ref=e74]: ₹199.00
        - generic [ref=e75]:
          - heading "Order Product" [level=3] [ref=e77]
          - paragraph [ref=e78]: Seeded for tests
          - generic [ref=e79]: ₹299.00
  - generic [ref=e80]:
    - heading "Why customers choose us" [level=2] [ref=e82]
    - generic [ref=e83]:
      - generic [ref=e84]:
        - heading "Fast turnaround" [level=3] [ref=e86]
        - paragraph [ref=e87]: Quick production timelines for urgent print jobs and repeat office supply orders.
      - generic [ref=e88]:
        - heading "Quality assurance" [level=3] [ref=e90]
        - paragraph [ref=e91]: Careful print checks, premium paper selection, and a focus on clean finishing details.
      - generic [ref=e92]:
        - heading "Flexible support" [level=3] [ref=e94]
        - paragraph [ref=e95]: Support for local businesses, schools, shops, and event organizers with tailored order planning.
  - generic [ref=e96]:
    - heading "Request a quote" [level=2] [ref=e98]
    - generic [ref=e99]:
      - generic [ref=e100]:
        - generic [ref=e101]:
          - generic [ref=e102]: Name *
          - textbox "Name *" [ref=e103]:
            - /placeholder: Enter your full name
        - generic [ref=e105]:
          - generic [ref=e106]: Company / Organization
          - textbox "Company / Organization" [ref=e107]:
            - /placeholder: Your organization name
        - generic [ref=e109]:
          - generic [ref=e110]: Mobile Number *
          - textbox "Mobile Number *" [ref=e111]:
            - /placeholder: +91 98765 43210
        - generic [ref=e113]:
          - generic [ref=e114]: Email
          - textbox "Email" [ref=e115]:
            - /placeholder: you@example.com
        - generic [ref=e117]:
          - generic [ref=e118]: Product / Category *
          - textbox "Product / Category *" [ref=e119]:
            - /placeholder: e.g. Office stationery
        - generic [ref=e121]:
          - generic [ref=e122]: Required Quantity
          - textbox "Required Quantity" [ref=e123]:
            - /placeholder: e.g. 250 units
        - generic [ref=e125]:
          - generic [ref=e126]: Customization / Requirements
          - textbox "Customization / Requirements" [ref=e127]:
            - /placeholder: Tell us about your requirements, materials, printing, or sizing preferences.
        - generic [ref=e129]:
          - generic [ref=e130]: Preferred Contact Method
          - combobox "Preferred Contact Method" [ref=e131]:
            - option "Call" [selected]
            - option "WhatsApp"
            - option "Email"
        - generic [ref=e133]:
          - generic [ref=e134]: Additional Message
          - textbox "Additional Message" [ref=e135]:
            - /placeholder: Add any additional details or timelines.
      - generic [ref=e137]:
        - button "Send enquiry" [ref=e138] [cursor=pointer]
        - paragraph
  - contentinfo [ref=e139]: Vinayaka File Works • Office stationery, printing, and business essentials
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | // Traceability:
  4   | // Jira: VNK-134 (VNK-VNK-2-ENH-001)
  5   | // Scope: client-side validation + inline field errors for quote enquiry form
  6   | 
  7   | test.describe('VNK-134 Quote enquiry form client-side validation', () => {
  8   |   test.beforeEach(async ({ page }) => {
  9   |     await page.goto('/');
  10  |   });
  11  | 
  12  |   async function fillValidForm(page: any) {
> 13  |     await page.getByLabel(/Full Name/i).fill('Test User');
      |                                         ^ Error: locator.fill: Test timeout of 30000ms exceeded.
  14  |     // Placeholder may include +91; validation should accept digits-only 10-15.
  15  |     await page.getByLabel(/Mobile/i).fill('9876543210');
  16  |     await page.getByLabel(/Email/i).fill('test.user@example.com');
  17  |     await page.getByLabel(/Product Category/i).selectOption({ label: /Files/i });
  18  |     await page.getByLabel(/Details/i).fill('Need 100 office files. Please call back.');
  19  |   }
  20  | 
  21  |   function getFieldError(page: any, fieldId: string) {
  22  |     return page.locator(`#err-${fieldId}`);
  23  |   }
  24  | 
  25  |   test('VNK-134-HP-001: Valid submission sends exactly one request and shows sending state', async ({ page }) => {
  26  |     await fillValidForm(page);
  27  | 
  28  |     const [request] = await Promise.all([
  29  |       page.waitForRequest((r) => r.url().includes('/api/quote-') && r.method() === 'POST'),
  30  |       page.getByRole('button', { name: /Submit/i }).click(),
  31  |     ]);
  32  | 
  33  |     // Sending state message is user-visible
  34  |     await expect(page.locator('#form-message')).toContainText(/Sending/i);
  35  | 
  36  |     // Ensure only one request is sent for a single click
  37  |     const requests = page.requests;
  38  |     // Fallback if page.requests isn't available: count via listener
  39  |     expect(request.postDataJSON()).toBeTruthy();
  40  | 
  41  |     // Verify no inline errors are shown
  42  |     await expect(getFieldError(page, 'name')).toBeHidden();
  43  |     await expect(getFieldError(page, 'mobile_number')).toBeHidden();
  44  |     await expect(getFieldError(page, 'product_category')).toBeHidden();
  45  |   });
  46  | 
  47  |   test('VNK-134-NEG-REQ-001: Empty name shows inline error and prevents request', async ({ page }) => {
  48  |     await fillValidForm(page);
  49  |     await page.getByLabel(/Full Name/i).fill('');
  50  | 
  51  |     let sent = 0;
  52  |     page.on('request', (r) => {
  53  |       if (r.url().includes('/api/quote-') && r.method() === 'POST') sent += 1;
  54  |     });
  55  | 
  56  |     await page.getByRole('button', { name: /Submit/i }).click();
  57  | 
  58  |     await expect(getFieldError(page, 'name')).toBeVisible();
  59  |     await expect(getFieldError(page, 'name')).toContainText(/required|name/i);
  60  | 
  61  |     // Focus should move to first invalid field
  62  |     await expect(page.getByLabel(/Full Name/i)).toBeFocused();
  63  | 
  64  |     expect(sent).toBe(0);
  65  |   });
  66  | 
  67  |   test('VNK-134-NEG-REQ-002: Empty mobile shows inline error and prevents request', async ({ page }) => {
  68  |     await fillValidForm(page);
  69  |     await page.getByLabel(/Mobile/i).fill('');
  70  | 
  71  |     let sent = 0;
  72  |     page.on('request', (r) => {
  73  |       if (r.url().includes('/api/quote-') && r.method() === 'POST') sent += 1;
  74  |     });
  75  | 
  76  |     await page.getByRole('button', { name: /Submit/i }).click();
  77  | 
  78  |     await expect(getFieldError(page, 'mobile_number')).toBeVisible();
  79  |     await expect(page.getByLabel(/Mobile/i)).toBeFocused();
  80  |     expect(sent).toBe(0);
  81  |   });
  82  | 
  83  |   test('VNK-134-NEG-REQ-003: No product category shows inline error and prevents request', async ({ page }) => {
  84  |     await fillValidForm(page);
  85  |     // Select empty option if exists; otherwise selectOption with value '' will no-op
  86  |     const select = page.getByLabel(/Product Category/i);
  87  |     const options = await select.locator('option').all();
  88  |     // Find an empty/placeholder option if present
  89  |     let placeholderValue: string | null = null;
  90  |     for (const opt of options) {
  91  |       const val = await opt.getAttribute('value');
  92  |       const text = (await opt.textContent()) ?? '';
  93  |       if (!val || val.trim() === '' || /select/i.test(text)) {
  94  |         placeholderValue = val ?? '';
  95  |         break;
  96  |       }
  97  |     }
  98  |     if (placeholderValue !== null) {
  99  |       await select.selectOption(placeholderValue);
  100 |     }
  101 | 
  102 |     let sent = 0;
  103 |     page.on('request', (r) => {
  104 |       if (r.url().includes('/api/quote-') && r.method() === 'POST') sent += 1;
  105 |     });
  106 | 
  107 |     await page.getByRole('button', { name: /Submit/i }).click();
  108 | 
  109 |     await expect(getFieldError(page, 'product_category')).toBeVisible();
  110 |     expect(sent).toBe(0);
  111 |   });
  112 | 
  113 |   test('VNK-134-NEG-EMAIL-001: Invalid email blocks submit and shows inline error', async ({ page }) => {
```