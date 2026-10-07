# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: vnk3-storefront-verification.spec.ts >> VNK-3 storefront smoke + E2E verification >> admin can authenticate and mark an order as processed
- Location: tests\vnk3-storefront-verification.spec.ts:121:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 200
Received: 401
```

# Test source

```ts
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
  118 |     expect(invoiceBody.download_url).toContain('pdf');
  119 |   });
  120 | 
  121 |   test('admin can authenticate and mark an order as processed', async ({ request }) => {
  122 |     const productList = await (await request.get('/api/products')).json();
  123 |     const productId = getSeededProductId(productList);
  124 |     const orderResponse = await request.post('/api/orders', {
  125 |       data: {
  126 |         customer: {
  127 |           full_name: 'Admin Buyer',
  128 |           email: `admin-${Date.now()}@example.com`,
  129 |           phone: '+918888888888',
  130 |           address_line1: '1 Admin Lane',
  131 |           city: 'Bengaluru',
  132 |           state: 'Karnataka',
  133 |           postal_code: '560020',
  134 |           country: 'IN',
  135 |         },
  136 |         items: [{ product_id: productId, quantity: 1 }],
  137 |         payment_method: 'ONLINE',
  138 |       },
  139 |     });
  140 |     const orderBody = await orderResponse.json();
  141 | 
  142 |     const loginResponse = await request.post('/api/admin/login', {
  143 |       data: { username: 'admin', password: 'adminpass' },
  144 |     });
> 145 |     expect(loginResponse.status()).toBe(200);
      |                                    ^ Error: expect(received).toBe(expected) // Object.is equality
  146 |     const loginBody = await loginResponse.json();
  147 |     expect(loginBody.status).toBe('ok');
  148 | 
  149 |     const statusResponse = await request.patch(`/api/admin/orders/${orderBody.order_id}/status`, {
  150 |       data: { status: 'PROCESSED' },
  151 |     });
  152 |     expect(statusResponse.status()).toBe(200);
  153 |     const statusBody = await statusResponse.json();
  154 |     expect(statusBody.order_status).toBe('PROCESSED');
  155 |   });
  156 | 
  157 |   test('no hardcoded secrets are present in repository config', async () => {
  158 |     const suspiciousPatterns = [
  159 |       /sk_(live|test)_[A-Za-z0-9]+/i,
  160 |       /(?:AKIA|ASIA)[A-Z0-9]{12,}/,
  161 |       /AIza[0-9A-Za-z\-_]{35}/,
  162 |       /(?:SECRET|API[_-]?KEY|PASSWORD)\s*[:=]\s*["'][^"']{8,}["']/i,
  163 |       /BEGIN (?:RSA |OPENSSH |PGP )?PRIVATE KEY/i,
  164 |     ];
  165 | 
  166 |     const candidateFiles = [
  167 |       path.join(repoRoot, 'dev', 'app', 'main.py'),
  168 |       path.join(repoRoot, 'dev', 'config.py'),
  169 |       path.join(repoRoot, 'dev', 'app', 'auth.py'),
  170 |       path.join(repoRoot, 'dev', 'app.py'),
  171 |       path.join(repoRoot, 'requirements.txt'),
  172 |       path.join(repoRoot, 'README.md'),
  173 |     ];
  174 | 
  175 |     const hits: string[] = [];
  176 |     for (const filePath of candidateFiles) {
  177 |       if (!fs.existsSync(filePath)) continue;
  178 |       const content = fs.readFileSync(filePath, 'utf8');
  179 |       for (const pattern of suspiciousPatterns) {
  180 |         if (pattern.test(content)) {
  181 |           hits.push(`${path.relative(repoRoot, filePath)} matches ${pattern}`);
  182 |         }
  183 |       }
  184 |     }
  185 | 
  186 |     expect(hits, `suspicious secrets found: ${hits.join('; ')}`).toEqual([]);
  187 |   });
  188 | });
  189 | 
```