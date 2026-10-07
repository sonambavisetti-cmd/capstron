# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: vnk3-storefront-verification.spec.ts >> VNK-3 storefront smoke + E2E verification >> homepage and site settings expose storefront identity
- Location: tests\vnk3-storefront-verification.spec.ts:14:7

# Error details

```
SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | import fs from 'node:fs';
  3   | import path from 'node:path';
  4   | 
  5   | const repoRoot = path.resolve(__dirname, '..', '..');
  6   | 
  7   | function getSeededProductId(products: any[]) {
  8   |   const product = products.find((item) => item.sku === 'VFW-1001');
  9   |   expect(product, 'seeded product catalog should include VFW-1001').toBeTruthy();
  10  |   return product.id;
  11  | }
  12  | 
  13  | test.describe('VNK-3 storefront smoke + E2E verification', () => {
  14  |   test('homepage and site settings expose storefront identity', async ({ request }) => {
  15  |     const home = await request.get('/');
  16  |     expect(home.status()).toBe(200);
> 17  |     const homeBody = await home.json();
      |                      ^ SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
  18  |     expect(homeBody.company).toBe('Vinayaka File Works');
  19  |     expect(homeBody.status).toBe('ok');
  20  | 
  21  |     const settings = await request.get('/api/site-settings');
  22  |     expect(settings.status()).toBe(200);
  23  |     const settingsBody = await settings.json();
  24  |     expect(settingsBody.company_name).toBe('Vinayaka File Works');
  25  |     expect(settingsBody.phone).toContain('+91');
  26  |     expect(settingsBody.address).toBeTruthy();
  27  |   });
  28  | 
  29  |   test('catalogue lists products with required fields', async ({ request }) => {
  30  |     const response = await request.get('/api/products');
  31  |     expect(response.status()).toBe(200);
  32  |     const body = await response.json();
  33  |     expect(Array.isArray(body)).toBeTruthy();
  34  |     expect(body.length).toBeGreaterThanOrEqual(1);
  35  | 
  36  |     const product = body[0];
  37  |     expect(product).toHaveProperty('sku');
  38  |     expect(product).toHaveProperty('name');
  39  |     expect(product).toHaveProperty('unit_price');
  40  |     expect(product).toHaveProperty('quantity_available');
  41  |     expect(typeof product.quantity_available).toBe('number');
  42  |   });
  43  | 
  44  |   test('checkout accepts a valid COD order and returns an order reference', async ({ request }) => {
  45  |     const productList = await (await request.get('/api/products')).json();
  46  |     const productId = getSeededProductId(productList);
  47  | 
  48  |     const payload = {
  49  |       customer: {
  50  |         full_name: 'Verification Buyer',
  51  |         email: `verification-${Date.now()}@example.com`,
  52  |         phone: '+919876543210',
  53  |         address_line1: '12 Market Road',
  54  |         city: 'Bengaluru',
  55  |         state: 'Karnataka',
  56  |         postal_code: '560001',
  57  |         country: 'IN',
  58  |       },
  59  |       items: [{ product_id: productId, quantity: 1 }],
  60  |       payment_method: 'COD',
  61  |       notes: 'Verification order',
  62  |     };
  63  | 
  64  |     const response = await request.post('/api/orders', { data: payload });
  65  |     expect(response.status()).toBe(200);
  66  |     const body = await response.json();
  67  |     expect(body.order_id).toBeTruthy();
  68  |     expect(body.order_status).toBe('PENDING');
  69  |     expect(body.payment_status).toBe('PENDING');
  70  | 
  71  |     const orderResponse = await request.get(`/api/orders/${body.order_id}`);
  72  |     expect(orderResponse.status()).toBe(200);
  73  |     const orderBody = await orderResponse.json();
  74  |     expect(orderBody.order_id).toBe(body.order_id);
  75  |     expect(orderBody.total_amount).toBeGreaterThan(0);
  76  |   });
  77  | 
  78  |   test('invalid checkout data is rejected with actionable validation errors', async ({ request }) => {
  79  |     const response = await request.post('/api/orders', {
  80  |       data: {
  81  |         customer: { full_name: '' },
  82  |         items: [],
  83  |         payment_method: 'COD',
  84  |       },
  85  |     });
  86  | 
  87  |     expect(response.status()).toBe(400);
  88  |     const body = await response.json();
  89  |     expect(body.detail || body.error || body.message).toBeTruthy();
  90  |   });
  91  | 
  92  |   test('invoice generation succeeds and exposes a PDF download link', async ({ request }) => {
  93  |     const productList = await (await request.get('/api/products')).json();
  94  |     const productId = getSeededProductId(productList);
  95  |     const orderResponse = await request.post('/api/orders', {
  96  |       data: {
  97  |         customer: {
  98  |           full_name: 'Invoice Buyer',
  99  |           email: `invoice-${Date.now()}@example.com`,
  100 |           phone: '+919999999999',
  101 |           address_line1: '999 Sample Street',
  102 |           city: 'Bengaluru',
  103 |           state: 'Karnataka',
  104 |           postal_code: '560010',
  105 |           country: 'IN',
  106 |         },
  107 |         items: [{ product_id: productId, quantity: 2 }],
  108 |         payment_method: 'COD',
  109 |       },
  110 |     });
  111 | 
  112 |     expect(orderResponse.status()).toBe(200);
  113 |     const orderBody = await orderResponse.json();
  114 |     const invoiceResponse = await request.get(`/api/orders/${orderBody.order_id}/invoice`);
  115 |     expect(invoiceResponse.status()).toBe(200);
  116 |     const invoiceBody = await invoiceResponse.json();
  117 |     expect(invoiceBody.status).toBe('READY');
```