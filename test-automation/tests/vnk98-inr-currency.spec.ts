import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { inflateSync } from 'node:zlib';
import path from 'node:path';

// VNK-98 (AC-2, AC-3): order -> invoice flow reports INR, never USD.
// SAFETY: this spec shells out to python (init_db drops/creates tables), so it refuses to run
// unless DATABASE_URL points at a non-default (temp) database. It never touches dev.db.
const repoRoot = path.resolve(__dirname, '..', '..');

function requireTempDb() {
  const url = process.env.DATABASE_URL || '';
  if (!url || /dev\.db$/i.test(url)) {
    throw new Error('Refusing to run: set DATABASE_URL to a temp sqlite file (not dev.db).');
  }
}

function py(script: string) {
  return execFileSync('python', ['-c', script], {
    cwd: repoRoot,
    env: { ...process.env, SECRET_KEY: 'dev-secret' },
  }).toString();
}

function seedProduct(sku: string, price: string, qty: number) {
  py([
    'from dev.db import init_db, SessionLocal',
    'from dev.models import Product',
    'init_db()',
    'with SessionLocal() as s:',
    `    s.add(Product(sku='${sku}', name='INR Spec Product', description='', unit_price='${price}', quantity_available=${qty}, image_url=''))`,
    '    s.commit()',
  ].join('\n'));
}

// ASCII85 decode (ReportLab default filter chain is ASCII85 + Flate).
function a85decode(input: string): Buffer {
  const s = input.replace(/\s+/g, '').replace(/^<~/, '').replace(/~>$/, '');
  const out: number[] = [];
  let group: number[] = [];
  for (const ch of s) {
    if (ch === 'z' && group.length === 0) { out.push(0, 0, 0, 0); continue; }
    group.push(ch.charCodeAt(0) - 33);
    if (group.length === 5) {
      let v = 0;
      for (const g of group) v = v * 85 + g;
      out.push((v >>> 24) & 255, (v >>> 16) & 255, (v >>> 8) & 255, v & 255);
      group = [];
    }
  }
  if (group.length > 1) {
    const n = group.length;
    while (group.length < 5) group.push(84);
    let v = 0;
    for (const g of group) v = v * 85 + g;
    const bytes = [(v >>> 24) & 255, (v >>> 16) & 255, (v >>> 8) & 255, v & 255];
    out.push(...bytes.slice(0, n - 1));
  }
  return Buffer.from(out);
}

// Return the text operands of every content stream in a ReportLab PDF.
function pdfText(pdf: Buffer): string {
  const raw = pdf.toString('latin1');
  const pieces: string[] = [raw];
  const re = /stream\r?\n([\s\S]*?)endstream/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(raw)) !== null) {
    const body = m[1];
    try { pieces.push(inflateSync(a85decode(body)).toString('latin1')); continue; } catch { /* next */ }
    try { pieces.push(inflateSync(Buffer.from(body, 'latin1')).toString('latin1')); } catch { /* not flate */ }
  }
  const all = pieces.join('\n');
  const ops = [...all.matchAll(/\(((?:\\.|[^\\)])*)\)\s*Tj/g)].map((x) => x[1].replace(/\\(.)/g, '$1'));
  return ops.join('\n');
}

test.describe('VNK-98 INR currency: order -> invoice', () => {
  test.beforeAll(() => {
    requireTempDb();
  });

  test('order is PROCESSING and the invoice PDF is labelled INR, not USD', async ({ request }) => {
    const sku = `INR-${Date.now()}`;
    seedProduct(sku, '250.00', 5);

    const list = await request.get('/api/products');
    expect(list.status()).toBe(200);
    const products = await list.json();
    const prod = products.find((p: any) => p.sku === sku);
    expect(prod, 'seeded product visible via API').toBeTruthy();

    const res = await request.post('/api/orders', {
      data: {
        customer: { full_name: 'INR Buyer', email: `inr+${Date.now()}@example.com` },
        items: [{ product_id: prod.id, quantity: 2 }],
        payment: { method: 'COD' },
        currency: 'USD', // must be ignored by the server (FR-07)
      },
    });
    expect(res.status()).toBe(201);
    const { order_id } = await res.json();
    expect(order_id).toBeTruthy();

    const ord = await (await request.get(`/api/orders/${order_id}`)).json();
    expect(ord.status).toBe('PROCESSING');
    expect(ord.status).not.toBe('PAID');

    const invRes = await request.get(`/api/orders/${order_id}/invoice`);
    expect(invRes.status()).toBe(200);
    const inv = await invRes.json();
    expect(inv.status).toBe('READY');

    const dl = await request.get(inv.download_url);
    expect(dl.status()).toBe(200);
    const text = pdfText(await dl.body());
    expect(text).toContain('Vinayaka File Works'); // extractor sanity
    expect(text).toContain('INR');
    expect(text).toContain('Currency: INR');
    expect(text).toContain('INR 500.00'); // 2 x 250.00
    expect(text).not.toContain('USD');
  });
});
