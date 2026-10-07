# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: vinayaka-checkout.spec.ts >> Vinayaka checkout & invoice flows >> checkout (COD) creates an order and returns confirmation
- Location: tests\vinayaka-checkout.spec.ts:74:7

# Error details

```
Error: expect(received).toContain(expected) // indexOf

Expected substring: "Invoice for order 908f716c-f283-4955-92d7-375129ae1d11"
Received string:    "%PDF-1.3
%���� ReportLab Generated PDF document (opensource)
1 0 obj
<<
/F1 2 0 R /F2 3 0 R
>>
endobj
2 0 obj
<<
/BaseFont /Helvetica /Encoding /WinAnsiEncoding /Name /F1 /Subtype /Type1 /Type /Font
>>
endobj
3 0 obj
<<
/BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding /Name /F2 /Subtype /Type1 /Type /Font
>>
endobj
4 0 obj
<<
/Contents 8 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 7 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<·
>>·
  /Type /Page
>>
endobj
5 0 obj
<<
/PageMode /UseNone /Pages 7 0 R /Type /Catalog
>>
endobj
6 0 obj
<<
/Author (anonymous) /CreationDate (D:20261007150249+05'00') /Creator (anonymous) /Keywords () /ModDate (D:20261007150249+05'00') /Producer (ReportLab PDF Library - \\(opensource\\))·
  /Subject (unspecified) /Title (Vinayaka File Works Invoice d3680f1a-0f78-463c-ac91-d8385889056e) /Trapped /False
>>
endobj
7 0 obj
<<
/Count 1 /Kids [ 4 0 R ] /Type /Pages
>>
endobj
8 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 522
>>
stream
Gat%`6#Y7,&;BTO'm\"1W%N[]Tm$pnGPq&J*M?T>Qgr,mp2_jka5lNo<[N[0SX;47I@J&]ORJ3Eud,Dh*>r2PJ#2WT0+9POCVF_-W\"'h8#WQkLo=D+#B\\W5!lP_,VD9EXHblIPZPA)Y#U3r&!XAp4:<4.'*!=i1Z<B(1HoA7^WmXIJp]Y6tU(D0.clas98FB_E(KCm=3Rj/pY$jAOA4/YQ1A81JmNCnZuUMCYBbVF%k:TL^Hga&'>IpTDY);cRBW$W8^u8ZIIeR[\"cLR6[XO_\\-s[QgS.*fBo;N>faak?%gD(G@A1Aaf4O)Z1U#1a&2aQ1Q>WH+a(fR\\*g_BIV`:fpgtP!m!3a[XtBJiDJnqCc%[7_ImFsrgfkcSas\\lSeYh''m'@8ZKe]W`o3n2FMo0SOB\"@HZD@aodppQuoMa[#c0=rF2*$T%k>,5Vn%/U%R3hc2e%4>o27G2#D\\U0:q`CHTfF=:F>G_AWfK=D.MfldJ2n\"B4Pr+L!(IY2!MI\"LCn\"??8\\>?VX%~>endstream
endobj
xref
0 9
0000000000 65535 f·
0000000061 00000 n·
0000000102 00000 n·
0000000209 00000 n·
0000000321 00000 n·
0000000524 00000 n·
0000000592 00000 n·
0000000909 00000 n·
0000000968 00000 n·
trailer
<<
/ID·
[<c2b1b25427e80a877513c1241cf49152><c2b1b25427e80a877513c1241cf49152>]
% ReportLab generated PDF document -- digest (opensource)·
/Info 6 0 R
/Root 5 0 R
/Size 9
>>
startxref
1580
%%EOF
"
```

# Test source

```ts
  19  |     `name = '${name}'`,
  20  |     `price = '${price}'`,
  21  |     `qty = ${quantity}`,
  22  |     "with SessionLocal() as session:",
  23  |     "    product = session.query(Product).filter_by(sku=sku).first()",
  24  |     "    if product is None:",
  25  |     "        session.add(Product(sku=sku, name=name, description='Seeded for tests', unit_price=price, quantity_available=qty, image_url=''))",
  26  |     "    else:",
  27  |     "        product.name = name",
  28  |     "        product.unit_price = price",
  29  |     "        product.quantity_available = qty",
  30  |     "    session.commit()",
  31  |   ].join('\n');
  32  | 
  33  |   execFileSync('python', ['-c', script], {
  34  |     cwd: repoRoot,
  35  |     env: { ...process.env, SECRET_KEY: 'dev-secret' },
  36  |   });
  37  | }
  38  | 
  39  | async function findProductBySku(request: any, sku: string) {
  40  |   const res = await request.get('/api/products');
  41  |   const body = await res.json();
  42  |   const prod = body.find((p: any) => p.sku === sku);
  43  |   return prod;
  44  | }
  45  | 
  46  | test.describe('Vinayaka checkout & invoice flows', () => {
  47  |   test.beforeAll(() => {
  48  |     initDatabase();
  49  |   });
  50  | 
  51  |   test('can add items to cart via API', async ({ request }) => {
  52  |     const sku = `CART-${Date.now()}`;
  53  |     seedProduct(sku, 'Cart Product', '199.00', 5);
  54  | 
  55  |     const prod = await findProductBySku(request, sku);
  56  |     expect(prod, 'seeded product exists').toBeTruthy();
  57  | 
  58  |     const customerId = 'test-customer-1';
  59  |     const addRes = await request.post(`/api/cart/${customerId}/add`, {
  60  |       data: { item: { product_id: prod.id, sku: prod.sku, quantity: 2, unit_price: prod.price } },
  61  |     });
  62  |     expect(addRes.status()).toBe(200);
  63  |     const addBody = await addRes.json();
  64  |     expect(addBody.status).toBe('ok');
  65  |     expect(addBody.cart).toBeTruthy();
  66  |     expect(addBody.cart.items && addBody.cart.items.length).toBeGreaterThan(0);
  67  | 
  68  |     const getRes = await request.get(`/api/cart/${customerId}`);
  69  |     expect(getRes.status()).toBe(200);
  70  |     const cart = await getRes.json();
  71  |     expect(cart.items && cart.items[0].product_id).toBe(prod.id);
  72  |   });
  73  | 
  74  |   test('checkout (COD) creates an order and returns confirmation', async ({ request }) => {
  75  |     const sku = `ORDER-${Date.now()}`;
  76  |     seedProduct(sku, 'Order Product', '299.00', 3);
  77  | 
  78  |     const prod = await findProductBySku(request, sku);
  79  |     expect(prod, 'seeded product exists').toBeTruthy();
  80  | 
  81  |     const payload = {
  82  |       customer: {
  83  |         full_name: 'Test Buyer',
  84  |         email: `buyer+${Date.now()}@example.com`,
  85  |         phone: '+919876543210',
  86  |         address_line1: '12 Test Street',
  87  |         city: 'Bengaluru',
  88  |       },
  89  |       items: [
  90  |         { product_id: prod.id, quantity: 1 }
  91  |       ],
  92  |       payment: { method: 'COD' }
  93  |     };
  94  | 
  95  |     const res = await request.post('/api/orders', { data: payload });
  96  |     expect(res.status()).toBe(201);
  97  |     const body = await res.json();
  98  |     expect(body.order_id).toBeTruthy();
  99  | 
  100 |     const orderId = body.order_id;
  101 |     const getOrder = await request.get(`/api/orders/${orderId}`);
  102 |     expect(getOrder.status()).toBe(200);
  103 |     const ord = await getOrder.json();
  104 |     expect(ord.id).toBe(orderId);
  105 |     // after creation, order_status should be PROCESSING per create_order implementation
  106 |     expect(ord.status).toBeTruthy();
  107 | 
  108 |     // Invoice should be generated (generate_invoice runs synchronously in test env)
  109 |     const invRes = await request.get(`/api/orders/${orderId}/invoice`);
  110 |     expect(invRes.status()).toBe(200);
  111 |     const inv = await invRes.json();
  112 |     expect(inv.status).toBe('READY');
  113 |     expect(inv.download_url).toBeTruthy();
  114 | 
  115 |     // Download the invoice file and assert content
  116 |     const dl = await request.get(inv.download_url);
  117 |     expect([200, 201].includes(dl.status())).toBeTruthy();
  118 |     const text = await dl.text();
> 119 |     expect(text).toContain(`Invoice for order ${orderId}`);
      |                  ^ Error: expect(received).toContain(expected) // indexOf
  120 |   });
  121 | });
  122 | 
```