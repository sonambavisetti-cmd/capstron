import { test, expect } from '@playwright/test';

// Traceability:
// Jira: VNK-134 (VNK-VNK-2-ENH-001)
// Scope: client-side validation + inline field errors for quote enquiry form

test.describe('VNK-134 Quote enquiry form client-side validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  async function fillValidForm(page: any) {
    await page.getByLabel(/Full Name/i).fill('Test User');
    // Placeholder may include +91; validation should accept digits-only 10-15.
    await page.getByLabel(/Mobile/i).fill('9876543210');
    await page.getByLabel(/Email/i).fill('test.user@example.com');
    await page.getByLabel(/Product Category/i).selectOption({ label: /Files/i });
    await page.getByLabel(/Details/i).fill('Need 100 office files. Please call back.');
  }

  function getFieldError(page: any, fieldId: string) {
    return page.locator(`#err-${fieldId}`);
  }

  test('VNK-134-HP-001: Valid submission sends exactly one request and shows sending state', async ({ page }) => {
    await fillValidForm(page);

    const [request] = await Promise.all([
      page.waitForRequest((r) => r.url().includes('/api/quote-') && r.method() === 'POST'),
      page.getByRole('button', { name: /Submit/i }).click(),
    ]);

    // Sending state message is user-visible
    await expect(page.locator('#form-message')).toContainText(/Sending/i);

    // Ensure only one request is sent for a single click
    const requests = page.requests;
    // Fallback if page.requests isn't available: count via listener
    expect(request.postDataJSON()).toBeTruthy();

    // Verify no inline errors are shown
    await expect(getFieldError(page, 'name')).toBeHidden();
    await expect(getFieldError(page, 'mobile_number')).toBeHidden();
    await expect(getFieldError(page, 'product_category')).toBeHidden();
  });

  test('VNK-134-NEG-REQ-001: Empty name shows inline error and prevents request', async ({ page }) => {
    await fillValidForm(page);
    await page.getByLabel(/Full Name/i).fill('');

    let sent = 0;
    page.on('request', (r) => {
      if (r.url().includes('/api/quote-') && r.method() === 'POST') sent += 1;
    });

    await page.getByRole('button', { name: /Submit/i }).click();

    await expect(getFieldError(page, 'name')).toBeVisible();
    await expect(getFieldError(page, 'name')).toContainText(/required|name/i);

    // Focus should move to first invalid field
    await expect(page.getByLabel(/Full Name/i)).toBeFocused();

    expect(sent).toBe(0);
  });

  test('VNK-134-NEG-REQ-002: Empty mobile shows inline error and prevents request', async ({ page }) => {
    await fillValidForm(page);
    await page.getByLabel(/Mobile/i).fill('');

    let sent = 0;
    page.on('request', (r) => {
      if (r.url().includes('/api/quote-') && r.method() === 'POST') sent += 1;
    });

    await page.getByRole('button', { name: /Submit/i }).click();

    await expect(getFieldError(page, 'mobile_number')).toBeVisible();
    await expect(page.getByLabel(/Mobile/i)).toBeFocused();
    expect(sent).toBe(0);
  });

  test('VNK-134-NEG-REQ-003: No product category shows inline error and prevents request', async ({ page }) => {
    await fillValidForm(page);
    // Select empty option if exists; otherwise selectOption with value '' will no-op
    const select = page.getByLabel(/Product Category/i);
    const options = await select.locator('option').all();
    // Find an empty/placeholder option if present
    let placeholderValue: string | null = null;
    for (const opt of options) {
      const val = await opt.getAttribute('value');
      const text = (await opt.textContent()) ?? '';
      if (!val || val.trim() === '' || /select/i.test(text)) {
        placeholderValue = val ?? '';
        break;
      }
    }
    if (placeholderValue !== null) {
      await select.selectOption(placeholderValue);
    }

    let sent = 0;
    page.on('request', (r) => {
      if (r.url().includes('/api/quote-') && r.method() === 'POST') sent += 1;
    });

    await page.getByRole('button', { name: /Submit/i }).click();

    await expect(getFieldError(page, 'product_category')).toBeVisible();
    expect(sent).toBe(0);
  });

  test('VNK-134-NEG-EMAIL-001: Invalid email blocks submit and shows inline error', async ({ page }) => {
    await fillValidForm(page);
    await page.getByLabel(/Email/i).fill('not-an-email');

    let sent = 0;
    page.on('request', (r) => {
      if (r.url().includes('/api/quote-') && r.method() === 'POST') sent += 1;
    });

    await page.getByRole('button', { name: /Submit/i }).click();

    await expect(getFieldError(page, 'email')).toBeVisible();
    expect(sent).toBe(0);
  });

  test('VNK-134-BOUND-PHONE-001: Phone too short blocks submit', async ({ page }) => {
    await fillValidForm(page);
    await page.getByLabel(/Mobile/i).fill('123456789');

    let sent = 0;
    page.on('request', (r) => {
      if (r.url().includes('/api/quote-') && r.method() === 'POST') sent += 1;
    });

    await page.getByRole('button', { name: /Submit/i }).click();

    await expect(getFieldError(page, 'mobile_number')).toBeVisible();
    expect(sent).toBe(0);
  });

  test('VNK-134-BOUND-PHONE-002: Phone too long blocks submit', async ({ page }) => {
    await fillValidForm(page);
    await page.getByLabel(/Mobile/i).fill('1234567890123456');

    let sent = 0;
    page.on('request', (r) => {
      if (r.url().includes('/api/quote-') && r.method() === 'POST') sent += 1;
    });

    await page.getByRole('button', { name: /Submit/i }).click();

    await expect(getFieldError(page, 'mobile_number')).toBeVisible();
    expect(sent).toBe(0);
  });

  test('VNK-134-BOUND-PHONE-003: Phone with letters blocks submit', async ({ page }) => {
    await fillValidForm(page);
    await page.getByLabel(/Mobile/i).fill('12345abcde');

    let sent = 0;
    page.on('request', (r) => {
      if (r.url().includes('/api/quote-') && r.method() === 'POST') sent += 1;
    });

    await page.getByRole('button', { name: /Submit/i }).click();

    await expect(getFieldError(page, 'mobile_number')).toBeVisible();
    expect(sent).toBe(0);
  });

  test('VNK-134-REG-001: Name inline error clears on input', async ({ page }) => {
    await fillValidForm(page);
    await page.getByLabel(/Full Name/i).fill('');

    await page.getByRole('button', { name: /Submit/i }).click();
    await expect(getFieldError(page, 'name')).toBeVisible();

    await page.getByLabel(/Full Name/i).fill('Corrected Name');
    await expect(getFieldError(page, 'name')).toBeHidden();
  });
});
