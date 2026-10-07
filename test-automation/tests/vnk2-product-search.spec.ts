import { test, expect, Page } from '@playwright/test';
import { execFileSync } from 'child_process';
import * as path from 'path';

// Traceability: Jira VNK-2 product search and filter (AC1-AC7, FR-01..FR-09, NFR-01).
//
// Setup: the seed script is run EXPLICITLY (never on app start). It uses the DATABASE_URL of this
// process, which MUST be the same database the Flask server under test uses. The spec refuses to run
// without DATABASE_URL so it can never seed the tracked dev.db by accident.
//
// Seed facts used below (dev/scripts/seed_products.py), active products = 8:
//  PVC: Clear File Folder (A4,A3; LOGO PRINT,COLOR), Document File Premium (A4,FS; LOGO PRINT),
//       Expanding File Organizer (FS)           -> 'PVC' only appears in material for Clear File Folder (F-01)
//  PP : Poly Ring File (A4), Project Folder (A3,A5)
//  BOARD: Archive Box File (A4,FS; LOGO PRINT,EMBOSSING), Printed Register (A5), Writing Pad (A4,A5)
//  Inactive: Discontinued PVC File (must never show)

const REPO_ROOT = path.resolve(__dirname, '..', '..');

test.beforeAll(() => {
  if (!process.env.DATABASE_URL) {
    throw new Error('DATABASE_URL must be set to the DB used by the server under test (refusing to seed the default dev.db).');
  }
  execFileSync('python', ['-m', 'dev.scripts.seed_products'], {
    cwd: REPO_ROOT,
    env: { ...process.env, SECRET_KEY: process.env.SECRET_KEY || 'dev-secret' },
    stdio: 'pipe',
  });
});

const cards = (page: Page) => page.locator('#product-grid .card');
const skus = async (page: Page) =>
  (await cards(page).evaluateAll((els) => els.map((e) => e.getAttribute('data-sku')))).sort();

// Returns the number of active products in the DB under test (seeded 8 plus any rows other specs left behind).
async function openPage(page: Page): Promise<number> {
  const api = await page.request.get('/api/products/search?limit=100');
  const total: number = (await api.json()).total;
  expect(total).toBeGreaterThanOrEqual(8);
  await page.goto('/');
  await expect(cards(page)).toHaveCount(total);
  // Filter options are populated from /api/products/filters.
  await expect(page.locator('#filter-material option')).not.toHaveCount(1);
  return total;
}

async function ensureFiltersOpen(page: Page) {
  const open = await page.locator('#filters-panel').evaluate((d: HTMLDetailsElement) => d.open);
  if (!open) await page.locator('#filters-panel > summary').click();
  await expect(page.locator('#filter-material')).toBeVisible();
}

test.describe('VNK-2 product search and filter', () => {
  test('initial load shows all active products, hides inactive, count shown', async ({ page }) => {
    const total = await openPage(page);
    await expect(page.locator('#results-count')).toHaveText(`${total} products`);
    expect(await skus(page)).not.toContain('SMP-FILE-A4-OLD');
    await expect(page.locator('#no-results')).toBeHidden();
    await expect(page.locator('#search-error')).toBeHidden();
  });

  test('AC1: searching "PVC File" shows matches, hides non-matches, shows count (incl. F-01 fixture)', async ({ page }) => {
    await openPage(page);
    await page.locator('#product-search-input').fill('PVC File');
    await expect(cards(page)).toHaveCount(3);
    expect(await skus(page)).toEqual(['SMP-FILE-A4-CLR', 'SMP-FILE-A4-DOC', 'SMP-FILE-FS-EXP']);
    // F-01: 'Clear File Folder' has PVC only as material
    await expect(page.locator('#product-grid')).toContainText('Clear File Folder');
    await expect(page.locator('#product-grid')).not.toContainText('Poly Ring File');
    await expect(page.locator('#product-grid')).not.toContainText('Archive Box File');
    await expect(page.locator('#results-count')).toHaveText('3 products');
  });

  test('AC2: material filter PVC shows only PVC products', async ({ page }) => {
    await openPage(page);
    await ensureFiltersOpen(page);
    await page.locator('#filter-material').selectOption('PVC');
    await expect(cards(page)).toHaveCount(3);
    const text = await page.locator('#product-grid').innerText();
    expect(text).toContain('Material: PVC');
    expect(text).not.toContain('Material: PP');
    expect(text).not.toContain('Material: BOARD');
    await expect(page.locator('#results-count')).toHaveText('3 products');
  });

  test('AC3: size A4 on an already filtered view shows only A4 products', async ({ page }) => {
    await openPage(page);
    await ensureFiltersOpen(page);
    await page.locator('#filter-material').selectOption('PVC');
    await expect(cards(page)).toHaveCount(3);
    await page.locator('#filter-size').selectOption('A4');
    await expect(cards(page)).toHaveCount(2);
    expect(await skus(page)).toEqual(['SMP-FILE-A4-CLR', 'SMP-FILE-A4-DOC']);
    const cardTexts = await cards(page).allInnerTexts();
    for (const t of cardTexts) expect(t).toMatch(/Sizes:.*\bA4\b/);
  });

  test('AC4: search term + material + size combine (AND)', async ({ page }) => {
    await openPage(page);
    await ensureFiltersOpen(page);
    await page.locator('#product-search-input').fill('Document');
    await expect(cards(page)).toHaveCount(1);
    await page.locator('#filter-material').selectOption('PVC');
    await page.locator('#filter-size').selectOption('A4');
    await expect(cards(page)).toHaveCount(1);
    expect(await skus(page)).toEqual(['SMP-FILE-A4-DOC']);

    // Term that matches PVC/A4 products only partially: "File" + BOARD + A4 -> Archive Box File only
    await page.locator('#product-search-input').fill('File');
    await page.locator('#filter-material').selectOption('BOARD');
    // wait for the re-render (the previous result also had exactly one card)
    await expect(page.locator('#product-grid .card[data-sku="SMP-BOX-A4-BRD"]')).toHaveCount(1);
    await expect(cards(page)).toHaveCount(1);
    expect(await skus(page)).toEqual(['SMP-BOX-A4-BRD']);
  });

  test('FR-05/F-10: customization filter', async ({ page }) => {
    await openPage(page);
    await ensureFiltersOpen(page);
    await page.locator('#filter-customization').selectOption('LOGO PRINT');
    await expect(cards(page)).toHaveCount(3);
    expect(await skus(page)).toEqual(['SMP-BOX-A4-BRD', 'SMP-FILE-A4-CLR', 'SMP-FILE-A4-DOC']);
  });

  test('AC5: Clear All Filters resets controls and shows all products', async ({ page }) => {
    const total = await openPage(page);
    await ensureFiltersOpen(page);
    await page.locator('#product-search-input').fill('File');
    await page.locator('#filter-material').selectOption('PVC');
    await page.locator('#filter-size').selectOption('A4');
    await page.locator('#filter-customization').selectOption('LOGO PRINT');
    await expect(cards(page)).toHaveCount(2);
    await page.locator('#clear-filters').click();
    await expect(page.locator('#product-search-input')).toHaveValue('');
    await expect(page.locator('#filter-material')).toHaveValue('');
    await expect(page.locator('#filter-size')).toHaveValue('');
    await expect(page.locator('#filter-customization')).toHaveValue('');
    await expect(cards(page)).toHaveCount(total);
    await expect(page.locator('#results-count')).toHaveText(`${total} products`);
  });

  test('AC6: nonexistent product shows "No products found" with suggestion and clear action', async ({ page }) => {
    const total = await openPage(page);
    await page.locator('#product-search-input').fill('zzqx-no-such-product-vnk2');
    await expect(page.locator('#no-results')).toBeVisible();
    await expect(page.locator('#no-results')).toContainText('No products found');
    await expect(page.locator('#no-results')).toContainText('clear your filters');
    await expect(cards(page)).toHaveCount(0);
    await expect(page.locator('#search-error')).toBeHidden();
    await page.locator('#no-results-clear').click();
    await expect(cards(page)).toHaveCount(total);
    await expect(page.locator('#no-results')).toBeHidden();
    await expect(page.locator('#product-search-input')).toHaveValue('');
  });

  test('desktop: filters panel is open by default', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await openPage(page);
    expect(await page.locator('#filters-panel').evaluate((d: HTMLDetailsElement) => d.open)).toBe(true);
    await expect(page.locator('#filter-material')).toBeVisible();
  });

  test('AC7: mobile 390px - controls reachable, usable, results fit without horizontal overflow', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openPage(page);
    // F-08: collapsed by default on narrow screens, summary reachable
    expect(await page.locator('#filters-panel').evaluate((d: HTMLDetailsElement) => d.open)).toBe(false);
    await expect(page.locator('#product-search-input')).toBeVisible();
    const summary = page.locator('#filters-panel > summary');
    await expect(summary).toBeVisible();
    const sbox = await summary.boundingBox();
    expect(sbox!.height).toBeGreaterThanOrEqual(44);
    await summary.click();
    await expect(page.locator('#filter-material')).toBeVisible();
    await expect(page.locator('#filter-size')).toBeVisible();
    await expect(page.locator('#filter-customization')).toBeVisible();
    await expect(page.locator('#clear-filters')).toBeVisible();
    for (const id of ['#product-search-input', '#filter-material', '#filter-size', '#filter-customization', '#clear-filters']) {
      const b = await page.locator(id).boundingBox();
      expect(b!.height, `${id} touch height`).toBeGreaterThanOrEqual(44);
      expect(b!.x + b!.width, `${id} within viewport`).toBeLessThanOrEqual(390 + 1);
    }
    await page.locator('#filter-material').selectOption('PVC');
    await expect(cards(page)).toHaveCount(3);
    // single-column grid and no horizontal overflow
    const overflow = await page.evaluate(() => ({
      doc: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      grid: (document.getElementById('product-grid') as HTMLElement).scrollWidth -
        (document.getElementById('product-grid') as HTMLElement).clientWidth,
    }));
    expect(overflow.doc).toBeLessThanOrEqual(0);
    expect(overflow.grid).toBeLessThanOrEqual(0);
    const xs = await cards(page).evaluateAll((els) => els.map((e) => Math.round(e.getBoundingClientRect().left)));
    expect(new Set(xs).size).toBe(1);
  });

  test('error state: failed search shows error message, not "No products found"', async ({ page }) => {
    await page.route('**/api/products/search*', (route) => route.fulfill({ status: 500, contentType: 'application/json', body: '{"error":"x"}' }));
    await page.goto('/');
    await expect(page.locator('#search-error')).toBeVisible();
    await expect(page.locator('#search-error')).toContainText('Unable to load products');
    await expect(page.locator('#no-results')).toBeHidden();
    await expect(cards(page)).toHaveCount(0);
  });

  test('security: markup typed in search is not rendered as HTML', async ({ page }) => {
    await openPage(page);
    await page.locator('#product-search-input').fill('<img src=x id=vnk2-injected>');
    await expect(page.locator('#no-results')).toBeVisible();
    await expect(page.locator('#vnk2-injected')).toHaveCount(0);
  });

  test('regression: quote form and marketing cards still render', async ({ page }) => {
    await openPage(page);
    await expect(page.locator('#name')).toBeVisible();
    await expect(page.locator('#mobile_number')).toBeVisible();
    await expect(page.getByText('Durable file folders, project tags')).toBeVisible();
  });
});
