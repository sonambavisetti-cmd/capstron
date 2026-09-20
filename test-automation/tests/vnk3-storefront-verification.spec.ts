import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(__dirname, '..', '..');

function getSeededProductId(products: any[]) {
  const product = products.find((item) => item.sku === 'VFW-1001');
  expect(product, 'seeded product catalog should include VFW-1001').toBeTruthy();
  return product.id;
}

test.describe('VNK-3 storefront smoke + E2E verification', () => {
  test('homepage and site settings expose storefront identity', async ({ request }) => {
    const home = await request.get('/');
    expect(home.status()).toBe(200);
    const homeBody = await home.json();
    expect(homeBody.company).toBe('Vinayaka File Works');
    expect(homeBody.status).toBe('ok');

    const settings = await request.get('/api/site-settings');
    expect(settings.status()).toBe(200);
    const settingsBody = await settings.json();
    expect(settingsBody.company_name).toBe('Vinayaka File Works');
    expect(settingsBody.phone).toContain('+91');
    expect(settingsBody.address).toBeTruthy();
  });

  test('catalogue lists products with required fields', async ({ request }) => {
    const response = await request.get('/api/products');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();
    expect(body.length).toBeGreaterThanOrEqual(1);

    const product = body[0];
    expect(product).toHaveProperty('sku');
    expect(product).toHaveProperty('name');
    expect(product).toHaveProperty('unit_price');
    expect(product).toHaveProperty('quantity_available');
    expect(typeof product.quantity_available).toBe('number');
  });

  test('checkout accepts a valid COD order and returns an order reference', async ({ request }) => {
    const productList = await (await request.get('/api/products')).json();
    const productId = getSeededProductId(productList);

    const payload = {
      customer: {
        full_name: 'Verification Buyer',
        email: `verification-${Date.now()}@example.com`,
        phone: '+919876543210',
        address_line1: '12 Market Road',
        city: 'Bengaluru',
        state: 'Karnataka',
        postal_code: '560001',
        country: 'IN',
      },
      items: [{ product_id: productId, quantity: 1 }],
      payment_method: 'COD',
      notes: 'Verification order',
    };

    const response = await request.post('/api/orders', { data: payload });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.order_id).toBeTruthy();
    expect(body.order_status).toBe('PENDING');
    expect(body.payment_status).toBe('PENDING');

    const orderResponse = await request.get(`/api/orders/${body.order_id}`);
    expect(orderResponse.status()).toBe(200);
    const orderBody = await orderResponse.json();
    expect(orderBody.order_id).toBe(body.order_id);
    expect(orderBody.total_amount).toBeGreaterThan(0);
  });

  test('invalid checkout data is rejected with actionable validation errors', async ({ request }) => {
    const response = await request.post('/api/orders', {
      data: {
        customer: { full_name: '' },
        items: [],
        payment_method: 'COD',
      },
    });

    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.detail || body.error || body.message).toBeTruthy();
  });

  test('invoice generation succeeds and exposes a PDF download link', async ({ request }) => {
    const productList = await (await request.get('/api/products')).json();
    const productId = getSeededProductId(productList);
    const orderResponse = await request.post('/api/orders', {
      data: {
        customer: {
          full_name: 'Invoice Buyer',
          email: `invoice-${Date.now()}@example.com`,
          phone: '+919999999999',
          address_line1: '999 Sample Street',
          city: 'Bengaluru',
          state: 'Karnataka',
          postal_code: '560010',
          country: 'IN',
        },
        items: [{ product_id: productId, quantity: 2 }],
        payment_method: 'COD',
      },
    });

    expect(orderResponse.status()).toBe(200);
    const orderBody = await orderResponse.json();
    const invoiceResponse = await request.get(`/api/orders/${orderBody.order_id}/invoice`);
    expect(invoiceResponse.status()).toBe(200);
    const invoiceBody = await invoiceResponse.json();
    expect(invoiceBody.status).toBe('READY');
    expect(invoiceBody.download_url).toContain('pdf');
  });

  test('admin can authenticate and mark an order as processed', async ({ request }) => {
    const productList = await (await request.get('/api/products')).json();
    const productId = getSeededProductId(productList);
    const orderResponse = await request.post('/api/orders', {
      data: {
        customer: {
          full_name: 'Admin Buyer',
          email: `admin-${Date.now()}@example.com`,
          phone: '+918888888888',
          address_line1: '1 Admin Lane',
          city: 'Bengaluru',
          state: 'Karnataka',
          postal_code: '560020',
          country: 'IN',
        },
        items: [{ product_id: productId, quantity: 1 }],
        payment_method: 'ONLINE',
      },
    });
    const orderBody = await orderResponse.json();

    const loginResponse = await request.post('/api/admin/login', {
      data: { username: 'admin', password: 'adminpass' },
    });
    expect(loginResponse.status()).toBe(200);
    const loginBody = await loginResponse.json();
    expect(loginBody.status).toBe('ok');

    const statusResponse = await request.patch(`/api/admin/orders/${orderBody.order_id}/status`, {
      data: { status: 'PROCESSED' },
    });
    expect(statusResponse.status()).toBe(200);
    const statusBody = await statusResponse.json();
    expect(statusBody.order_status).toBe('PROCESSED');
  });

  test('no hardcoded secrets are present in repository config', async () => {
    const suspiciousPatterns = [
      /sk_(live|test)_[A-Za-z0-9]+/i,
      /(?:AKIA|ASIA)[A-Z0-9]{12,}/,
      /AIza[0-9A-Za-z\-_]{35}/,
      /(?:SECRET|API[_-]?KEY|PASSWORD)\s*[:=]\s*["'][^"']{8,}["']/i,
      /BEGIN (?:RSA |OPENSSH |PGP )?PRIVATE KEY/i,
    ];

    const candidateFiles = [
      path.join(repoRoot, 'dev', 'app', 'main.py'),
      path.join(repoRoot, 'dev', 'config.py'),
      path.join(repoRoot, 'dev', 'app', 'auth.py'),
      path.join(repoRoot, 'dev', 'app.py'),
      path.join(repoRoot, 'requirements.txt'),
      path.join(repoRoot, 'README.md'),
    ];

    const hits: string[] = [];
    for (const filePath of candidateFiles) {
      if (!fs.existsSync(filePath)) continue;
      const content = fs.readFileSync(filePath, 'utf8');
      for (const pattern of suspiciousPatterns) {
        if (pattern.test(content)) {
          hits.push(`${path.relative(repoRoot, filePath)} matches ${pattern}`);
        }
      }
    }

    expect(hits, `suspicious secrets found: ${hits.join('; ')}`).toEqual([]);
  });
});
