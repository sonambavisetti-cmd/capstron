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

async function findProductBySku(request: any, sku: string) {
  const res = await request.get('/api/products');
  const body = await res.json();
  const prod = body.find((p: any) => p.sku === sku);
  return prod;
}

test.describe('Vinayaka checkout & invoice flows', () => {
  test.beforeAll(() => {
    initDatabase();
  });

  test('can add items to cart via API', async ({ request }) => {
    const sku = `CART-${Date.now()}`;
    seedProduct(sku, 'Cart Product', '199.00', 5);

    const prod = await findProductBySku(request, sku);
    expect(prod, 'seeded product exists').toBeTruthy();

    const customerId = 'test-customer-1';
    const addRes = await request.post(`/api/cart/${customerId}/add`, {
      data: { item: { product_id: prod.id, sku: prod.sku, quantity: 2, unit_price: prod.price } },
    });
    expect(addRes.status()).toBe(200);
    const addBody = await addRes.json();
    expect(addBody.status).toBe('ok');
    expect(addBody.cart).toBeTruthy();
    expect(addBody.cart.items && addBody.cart.items.length).toBeGreaterThan(0);

    const getRes = await request.get(`/api/cart/${customerId}`);
    expect(getRes.status()).toBe(200);
    const cart = await getRes.json();
    expect(cart.items && cart.items[0].product_id).toBe(prod.id);
  });

  test('checkout (COD) creates an order and returns confirmation', async ({ request }) => {
    const sku = `ORDER-${Date.now()}`;
    seedProduct(sku, 'Order Product', '299.00', 3);

    const prod = await findProductBySku(request, sku);
    expect(prod, 'seeded product exists').toBeTruthy();

    const payload = {
      customer: {
        full_name: 'Test Buyer',
        email: `buyer+${Date.now()}@example.com`,
        phone: '+919876543210',
        address_line1: '12 Test Street',
        city: 'Bengaluru',
      },
      items: [
        { product_id: prod.id, quantity: 1 }
      ],
      payment: { method: 'COD' }
    };

    const res = await request.post('/api/orders', { data: payload });
    expect(res.status()).toBe(201);
    const body = await res.json();
    expect(body.order_id).toBeTruthy();

    const orderId = body.order_id;
    const getOrder = await request.get(`/api/orders/${orderId}`);
    expect(getOrder.status()).toBe(200);
    const ord = await getOrder.json();
    expect(ord.id).toBe(orderId);
    // after creation, order_status should be PROCESSING per create_order implementation
    expect(ord.status).toBeTruthy();

    // Invoice should be generated (generate_invoice runs synchronously in test env)
    const invRes = await request.get(`/api/orders/${orderId}/invoice`);
    expect(invRes.status()).toBe(200);
    const inv = await invRes.json();
    expect(inv.status).toBe('READY');
    expect(inv.download_url).toBeTruthy();

    // Download the invoice file and assert content
    const dl = await request.get(inv.download_url);
    expect([200, 201].includes(dl.status())).toBeTruthy();
    const text = await dl.text();
    expect(text).toContain(`Invoice for order ${orderId}`);
  });
});
