import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import path from 'node:path';

const repoRoot = path.resolve(__dirname, '..', '..');

function initDatabase() {
  execFileSync('python', ['-c', 'from dev.db import init_db; init_db(); print("db ok")'], {
    cwd: repoRoot,
    env: { ...process.env, SECRET_KEY: 'dev-secret' },
  });
}

function seedAdmin(username = 'admin', password = 'admin') {
  const script = [
    "from dev.scripts.seed_admin import seed",
    `seed('${username}', '${password}')`,
  ].join('\n');
  execFileSync('python', ['-c', script], { cwd: repoRoot, env: { ...process.env, SECRET_KEY: 'dev-secret' } });
}

function seedProduct(sku: string, name: string, price: string, quantity: number) {
  const script = [
    "from dev.db import SessionLocal",
    "from dev.models import Product",
    `sku = '${sku}'`,
    `name = '${name}'`,
    `price = '${price}'`,
    `qty = ${quantity}`,
    "with SessionLocal() as session:",
    "    product = session.query(Product).filter_by(sku=sku).first()",
    "    if product is None:",
    "        session.add(Product(sku=sku, name=name, description='Seeded for tests', unit_price=price, quantity_available=qty, image_url=''))",
    "    else:",
    "        product.name = name",
    "        product.unit_price = price",
    "        product.quantity_available = qty",
    "    session.commit()",
  ].join('\n');

  execFileSync('python', ['-c', script], {
    cwd: repoRoot,
    env: { ...process.env, SECRET_KEY: 'dev-secret' },
  });
}

test.describe('Vinayaka store verification', () => {
  test.beforeAll(() => {
    initDatabase();
    seedAdmin();
  });

  test('homepage shows company branding', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('body')).toContainText('Vinayaka File Works');
    await expect(page.locator('body')).toContainText('Paper & printing solutions');
    await expect(page.locator('body')).toContainText('Get a quote');
  });

  test('homepage includes company address and phone details', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('body')).toContainText('No. 42, Market Road');
    await expect(page.locator('body')).toContainText('+91 98765 43210');
  });

  test('product API returns product details', async ({ request }) => {
    const sku = `TEST-${Date.now()}`;
    seedProduct(sku, 'Test Product', '799.00', 12);

    const response = await request.get('/api/products');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();
    expect(body.some((item: any) => item.sku === sku)).toBeTruthy();
  });

  test('invalid order payload is rejected with a clear error', async ({ request }) => {
    const response = await request.post('/api/orders', {
      data: {
        customer: {},
        items: [],
      },
    });

    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.error || body.message).toBeTruthy();
  });

  test('admin login succeeds with seeded credentials', async ({ request }) => {
    const response = await request.post('/api/admin/login', {
      data: {
        username: 'admin',
        password: 'admin',
      },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe('ok');
  });
});
